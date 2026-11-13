#!/usr/bin/env python3
"""Export lists of the LimeSuiteNG +lab build (TX-AUDIT.md section L), stdlib only, no network.

  check DEB...   compare exports.json with the .deb files sr-rx-packages built (liblimesuiteng and
                 limesuiteng-soapysdr, artifact lab-out-light)
  write DEB...   replace the symbol lists of exports.json with the ones those .deb files hold

The lists are the defined dynamic symbols (the names `nm -D --defined-only` prints: every named .dynsym
entry whose section index is not SHN_UNDEF) of the library and of the SoapySDR module, and the module's
undefined dynamic symbols that the library defines. `write` keeps every other key of exports.json; after it
the caller updates "source" (run, job, commit), sets the recipe's export_count values to the new counts
(deployment/tests/test_lime_tx_audit.py checks that they follow the lists) and names every new lime
class in TX-AUDIT.md section L. The lists stay an agent audit draft (AUDIT_DRAFT_CI_CHECKED), not a
review. Exit status: 0 equal (check) or written (write), 1 different, 2 bad input.
"""
import io
import json
import struct
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORTS = HERE / "exports.json"
LIB_FILE = "usr/lib/aarch64-linux-gnu/liblimesuiteng.so.0.3-1"
SOAPY_FILE = "usr/lib/aarch64-linux-gnu/SoapySDR/modules0.8/liblimesuitengSupport.so"
SHT_DYNSYM = 11
SHN_UNDEF = 0


def deb_file(deb, path):
    """The bytes of one regular file of a .deb (ar archive with data.tar.gz/.xz/.bz2), or None."""
    if deb[:8] != b"!<arch>\n":
        raise ValueError("not an ar archive")
    pos = 8
    while pos + 60 <= len(deb):
        header = deb[pos:pos + 60]
        name = header[:16].decode("ascii").strip().rstrip("/")
        size = int(header[48:58].decode("ascii").strip())
        body = deb[pos + 60:pos + 60 + size]
        if len(body) != size:
            raise ValueError("truncated ar member " + name)
        if name.startswith("data.tar"):
            if name.endswith(".zst"):
                raise ValueError("data.tar.zst needs zstd; the builder packs with dpkg-deb -Zxz")
            with tarfile.open(fileobj=io.BytesIO(body), mode="r:*") as tar:
                for member in tar.getmembers():
                    if member.name.removeprefix("./").lstrip("/") == path:
                        if not member.isfile():
                            raise ValueError(path + " is not a regular file")
                        return tar.extractfile(member).read()
            return None
        pos += 60 + size + (size & 1)
    raise ValueError("no data.tar member")


def dynamic_symbols(elf):
    """(defined, undefined) names of the .dynsym of a little-endian ELF64 file."""
    if elf[:4] != b"\x7fELF" or elf[4] != 2 or elf[5] != 1:
        raise ValueError("not a little-endian ELF64 file")
    shoff, = struct.unpack_from("<Q", elf, 0x28)
    shentsize, shnum = struct.unpack_from("<HH", elf, 0x3A)
    sections = [struct.unpack_from("<IIQQQQIIQQ", elf, shoff + i * shentsize) for i in range(shnum)]
    defined, undefined, tables = set(), set(), 0
    for _name, kind, _flags, _addr, offset, size, link, _info, _align, entsize in sections:
        if kind != SHT_DYNSYM:
            continue
        tables += 1
        if entsize != 24 or link >= shnum or offset + size > len(elf):
            raise ValueError("malformed .dynsym")
        strings = sections[link][4]
        for index in range(1, size // entsize):
            st_name, _st_info, _st_other, st_shndx, _value, _size = struct.unpack_from("<IBBHQQ", elf, offset + index * entsize)
            end = elf.index(b"\0", strings + st_name)
            name = elf[strings + st_name:end].decode("ascii")
            if name:
                (undefined if st_shndx == SHN_UNDEF else defined).add(name)
    if tables != 1:
        raise ValueError("expected one .dynsym, found %d" % tables)
    return defined, undefined


def lists(debs):
    """The exports.json symbol lists of the two files, read from the given .deb bytes."""
    found = {}
    for path in (LIB_FILE, SOAPY_FILE):
        hits = [data for data in (deb_file(deb, path) for deb in debs) if data is not None]
        if len(hits) != 1:
            raise ValueError("%s is in %d of the given .deb files, not 1" % (path, len(hits)))
        found[path] = dynamic_symbols(hits[0])
    library = found[LIB_FILE][0]
    return {LIB_FILE: {"defined": sorted(library)},
            SOAPY_FILE: {"defined": sorted(found[SOAPY_FILE][0]),
                         "imports_from_liblimesuiteng": sorted(found[SOAPY_FILE][1] & library)}}


def differences(data, new):
    """One line per symbol that is in exactly one of exports.json and the .deb lists."""
    out = []
    for path, keys in new.items():
        entry = data["files"].get(path, {})
        for key, symbols in keys.items():
            old = set(entry.get(key, []))
            out += ["+ %s %s %s" % (path, key, s) for s in sorted(set(symbols) - old)]
            out += ["- %s %s %s" % (path, key, s) for s in sorted(old - set(symbols))]
    return out


def main(argv):
    if len(argv) < 2 or argv[0] not in ("check", "write"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        new = lists([Path(p).read_bytes() for p in argv[1:]])
    except (OSError, ValueError, tarfile.TarError, struct.error) as error:
        print("export_lists: " + str(error), file=sys.stderr)
        return 2
    data = json.loads(EXPORTS.read_text(encoding="utf-8"))
    if set(data["files"]) != set(new):
        print("export_lists: exports.json lists other files", file=sys.stderr)
        return 2
    diff = differences(data, new)
    counts = ", ".join("%s %d" % (p.rsplit("/", 1)[-1], len(k["defined"])) for p, k in new.items())
    if argv[0] == "check":
        print("\n".join(diff + ["%s: %s defined, %d imports" % ("DIFFERENT" if diff else "EQUAL", counts,
                                                               len(new[SOAPY_FILE]["imports_from_liblimesuiteng"]))]))
        return 1 if diff else 0
    for path, keys in new.items():
        data["files"][path].update(keys)
    EXPORTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("written: %s defined; update source, the recipe export_count values and TX-AUDIT.md section L" % counts)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
