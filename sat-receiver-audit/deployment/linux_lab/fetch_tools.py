#!/usr/bin/env python3
"""Rebuild isolated, hash-locked x86_64 QEMU/ISO tools without host installation.

The destination must be a new directory outside this project. Requires Python3,
curl, dpkg-deb, tar, gpgv and an existing trusted Ubuntu archive keyring.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, lzma
from pathlib import Path
import platform, shutil, subprocess, sys, urllib.parse

PROJECT=Path(__file__).resolve().parents[2]
LOCK=Path(__file__).with_name('host-packages.lock.json')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire(item,path,cache=None):
    if cache is not None:
        candidate=cache/item['filename']
        if candidate.is_file() and candidate.stat().st_size==item['bytes'] and digest(candidate)==item['sha256']:
            shutil.copyfile(candidate,path)
            if digest(path)!=item['sha256']:raise RuntimeError('Copied cache hash mismatch')
            return
    subprocess.run(['curl','--fail','--location','--retry','2','--connect-timeout','20','--max-time','300','--silent','--show-error',item['url'],'--output',str(path)],check=True)
    if ('bytes' in item and path.stat().st_size!=item['bytes']) or digest(path)!=item['sha256']:
        raise RuntimeError('Hash/size mismatch for '+item['url'])


def signed_records(raw):
    records={}
    for block in raw.decode('utf-8').split('\n\n'):
        fields={}
        for line in block.splitlines():
            if not line.startswith(' ') and ': ' in line:
                key,value=line.split(': ',1);fields[key]=value
        if 'Filename' in fields:records[fields['Filename']]=fields
    return records


LIBPATH=('usr/lib/x86_64-linux-gnu','lib/x86_64-linux-gnu')


def wrapper_texts():
    # --inhibit-cache: never resolve a missing locked library via host ld.so.cache.
    template='''#!/bin/sh
set -eu
tools_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export QEMU_MODULE_DIR="$tools_root/root/usr/lib/x86_64-linux-gnu/qemu"
exec "$tools_root/root/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" --inhibit-cache --library-path "$tools_root/root/usr/lib/x86_64-linux-gnu:$tools_root/root/lib/x86_64-linux-gnu" "$tools_root/root/usr/bin/PROGRAM" EXTRA "$@"
'''
    return {program:template.replace('PROGRAM',program).replace('EXTRA',extra) for program,extra in
            [('qemu-system-aarch64','-L "$tools_root/root/usr/share/qemu"'),('qemu-img',''),('genisoimage','')]}


def unpack(debs,packages,root):
    # Only unpack filesystem payloads, in lock order; no dpkg installation or scripts.
    for item in packages:
        producer=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(debs/item['filename'])],stdout=subprocess.PIPE)
        try:
            subprocess.run(['tar','--extract','--no-same-owner','--no-same-permissions','--directory',str(root)],stdin=producer.stdout,check=True)
        finally:producer.stdout.close()
        if producer.wait():raise RuntimeError('Cannot unpack '+item['name'])


def wrappers(dest):
    for program,text in wrapper_texts().items():
        path=dest/'bin'/program;path.write_text(text);path.chmod(0o755)


def host_library_leaks(listing,root):
    """ld.so --list lines resolving outside root (or not at all). The loader
    still searches default host directories after --library-path."""
    leaks=[]
    for line in listing.splitlines():
        if ' => ' not in line:continue
        name,target=(x.strip() for x in line.split(' => ',1))
        target=target.rsplit(' (0x',1)[0].strip()
        # The PT_INTERP entry names the host path; the wrapper runs the locked ld.so.
        if name.startswith('/') and Path(name).name.startswith('ld-linux'):continue
        if target=='not found' or not Path(target).resolve().is_relative_to(Path(root).resolve()):leaks.append(name+' => '+target)
    return leaks


def resolved_libraries(dest,program):
    ldso=dest/'root/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2'
    listing=subprocess.run([str(ldso),'--inhibit-cache','--library-path',':'.join(str(dest/'root'/x) for x in LIBPATH),
                            '--list',str(dest/'root/usr/bin'/program)],capture_output=True,text=True,check=True).stdout
    leaks=host_library_leaks(listing,dest/'root')
    if leaks:raise RuntimeError('Tool resolves a library outside the locked runtime: '+program+': '+'; '.join(leaks[:10]))
    return sorted(line.split(' => ',1)[0].strip() for line in listing.splitlines() if ' => ' in line)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest',type=Path,required=True,help='New tools directory outside project; existing paths are rejected')
    parser.add_argument('--package-cache',type=Path,help='Optional read-only cache directory containing locked .deb filenames')
    parser.add_argument('--keyring',type=Path,default=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg'))
    parser.add_argument('--jobs',type=int,default=6)
    args=parser.parse_args();dest=args.dest.expanduser().resolve()
    if dest==PROJECT or dest.is_relative_to(PROJECT):parser.error('--dest must be outside the project')
    if dest.exists() or args.dest.is_symlink():parser.error('--dest must not already exist')
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','amd64'):parser.error('This lock targets Linux x86_64 hosts')
    if not args.keyring.is_file():parser.error('An existing trusted Ubuntu archive keyring is required; use --keyring')
    for command in ('curl','dpkg-deb','tar','gpgv'):
        if not shutil.which(command):parser.error('Required host utility is missing: '+command)
    lock=json.loads(LOCK.read_text())
    if lock['schema_version']!=1 or len(lock['packages'])!=87:parser.error('Unexpected lock schema or package count')
    if not 1<=args.jobs<=16:parser.error('--jobs must be between 1 and 16')
    dest.mkdir(parents=True,exist_ok=False)
    for part in ('debs','metadata','metadata/gpg-home','root','bin'):(dest/part).mkdir()
    (dest/'metadata/gpg-home').chmod(0o700)
    shutil.copyfile(LOCK,dest/'host-packages.lock.json')
    release=dest/'metadata/InRelease';acquire(lock['inrelease'],release)
    verify=subprocess.run(['gpgv','--homedir',str(dest/'metadata/gpg-home'),'--keyring',str(args.keyring.resolve()),'--status-fd','1',str(release)],capture_output=True,text=True)
    (dest/'metadata/gpg-verification.txt').write_text(verify.stdout+verify.stderr)
    if verify.returncode or ('[GNUPG:] VALIDSIG '+lock['inrelease']['signing_fingerprint']+' ') not in verify.stdout:
        raise RuntimeError('Ubuntu InRelease signature verification failed')
    rows=[line.split() for line in release.read_text().splitlines()]
    for fields in ([lock['index']['sha256'],str(lock['index']['bytes']),'main/binary-amd64/Packages.xz'],[lock['index']['uncompressed_sha256'],str(lock['index']['uncompressed_bytes']),'main/binary-amd64/Packages']):
        if fields not in rows:raise RuntimeError('Index hash is absent from signed InRelease')
    index=dest/'metadata/Packages.xz';acquire(lock['index'],index)
    raw=lzma.decompress(index.read_bytes())
    if len(raw)!=lock['index']['uncompressed_bytes'] or hashlib.sha256(raw).hexdigest()!=lock['index']['uncompressed_sha256']:
        raise RuntimeError('Uncompressed signed index hash mismatch')
    records=signed_records(raw)
    for item in lock['packages']:
        if Path(item['filename']).name!=item['filename']:raise RuntimeError('Unsafe locked package filename')
        key=urllib.parse.unquote(urllib.parse.urlsplit(item['url']).path).split('/ubuntu/',1)[1]
        signed=records[key]
        for key1,key2 in [('name','Package'),('version','Version'),('architecture','Architecture'),('sha256','SHA256')]:
            if item[key1]!=signed[key2]:raise RuntimeError('Lock/index mismatch: '+item['name']+' '+key1)
        if item['bytes']!=int(signed['Size']):raise RuntimeError('Lock/index size mismatch: '+item['name'])
    cache=args.package_cache.resolve() if args.package_cache else None
    def fetch(item):acquire(item,dest/'debs'/item['filename'],cache);return item['name']
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as workers:
        for name in workers.map(fetch,lock['packages']):print('Verified '+name,flush=True)
    unpack(dest/'debs',lock['packages'],dest/'root')
    wrappers(dest)
    versions,libraries={},{}
    for name in lock['tools']:
        libraries[name]=resolved_libraries(dest,name)
        result=subprocess.run([str(dest/'bin'/name),'--version'],capture_output=True,text=True,check=True)
        versions[name]=result.stdout.strip().splitlines()[0]
    report={'status':'PASS','platform':lock['platform'],'package_count':len(lock['packages']),'download_bytes':lock['download_bytes'],'lock_sha256':digest(LOCK),'versions':versions,'libraries_resolved_inside_root':libraries,'host_installation':False,'scope':'Tool versions and program DT_NEEDED closure (ld.so --inhibit-cache --list) tested; dlopen()ed QEMU modules are not listed; no guest Linux boot, physical-board or security-update qualification claim.'}
    (dest/'tools-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    try:main()
    except (RuntimeError,subprocess.CalledProcessError,OSError,KeyError) as error:
        print('Tool rebuild failed: '+str(error),file=sys.stderr);raise SystemExit(1)
