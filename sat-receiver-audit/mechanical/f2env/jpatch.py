"""Format-preserving number patch of a JSON text: same structure, changed numbers rewritten in place."""
import json
import re

_num = re.compile(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?')
_ws = re.compile(r'[ \t\n\r]*')


def numbers(text):
    """[(start, end, path)] for every number literal."""
    out = []
    i = 0

    def ws(i):
        return _ws.match(text, i).end()

    def value(i, path):
        i = ws(i)
        c = text[i]
        if c == '{':
            i = ws(i + 1)
            if text[i] == '}':
                return i + 1
            while True:
                i = ws(i)
                s = json.decoder.scanstring(text, i + 1)
                key, i = s
                i = ws(i)
                assert text[i] == ':'
                i = value(i + 1, path + (key,))
                i = ws(i)
                if text[i] == ',':
                    i += 1
                    continue
                assert text[i] == '}'
                return i + 1
        if c == '[':
            i = ws(i + 1)
            if text[i] == ']':
                return i + 1
            k = 0
            while True:
                i = value(i, path + (k,))
                k += 1
                i = ws(i)
                if text[i] == ',':
                    i += 1
                    continue
                assert text[i] == ']', text[i - 20:i + 20]
                return i + 1
        if c == '"':
            return json.decoder.scanstring(text, i + 1)[1]
        mm = _num.match(text, i)
        if mm:
            out.append((mm.start(), mm.end(), path))
            return mm.end()
        for lit in ('true', 'false', 'null'):
            if text.startswith(lit, i):
                return i + len(lit)
        raise ValueError(i)
    value(0, ())
    return out


def get(o, path):
    for p in path:
        o = o[p]
    return o


def fmt(v):
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return f'{v:.1f}'
    return json.dumps(v)


def patch(text, new):
    old = json.loads(text)
    parts, last = [], 0
    n = 0
    for s, e, path in numbers(text):
        ov, nv = get(old, path), get(new, path)
        if ov != nv or type(ov) != type(nv):
            lit = text[s:e]
            if isinstance(nv, float) and '.' not in lit and nv.is_integer():
                rep = str(int(nv))       # keep an integer literal style
            else:
                rep = fmt(nv)
            parts.append(text[last:s])
            parts.append(rep)
            last = e
            n += 1
    parts.append(text[last:])
    out = ''.join(parts)
    assert json.loads(out) == new or _eq(json.loads(out), new)
    return out, n


def _eq(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def remove_key(text, key, after=0):
    """Remove the member "key": <value> (first occurrence at or after offset `after`) with its separating comma."""
    import re as _re
    i = text.index(json.dumps(key) + ':', after)
    j = i + len(json.dumps(key)) + 1
    j = _ws.match(text, j).end()
    # scan the value
    depth, k, ins = 0, j, False
    while True:
        c = text[k]
        if ins:
            if c == chr(92):
                k += 2
                continue
            if c == '"':
                ins = False
                if depth == 0:
                    k += 1
                    break
        elif c == '"':
            ins = True
        elif c in '{[':
            depth += 1
        elif c in '}]':
            depth -= 1
            if depth == 0:
                k += 1
                break
        elif depth == 0 and c in ',}]':
            break
        k += 1
    # remove the preceding comma + whitespace (or the following comma)
    a = i
    b = k
    m2 = _re.compile(r',[ \t\r\n]*$').search(text[:a])
    if m2:
        a = m2.start()
    else:
        m3 = _re.compile(r'[ \t\r\n]*,').match(text, b)
        if m3:
            b = m3.end()
    out = text[:a] + text[b:]
    json.loads(out)
    return out
