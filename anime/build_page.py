"""Builds a ViteC stream-record tracker page (same layout and logic as sao_vitecp.html).

usage: python3 build_page.py CONFIG.json OUT.html [--fragment]

CONFIG: title, h1, storage_key, note (HTML), sections[{title, rows[{uuid, ep, tc, hint?}]}], seed{row_id: 1|2}.
Row id = first 8 chars of the record uuid + episode + first 4 hex of md5(section title), exactly as in the SAO page.
--fragment drops <!DOCTYPE>/<html>/<head>/<body> for publishing as an Artifact (the host adds its own skeleton).
"""
import hashlib, html, json, sys

DOC_OPEN = '''<!DOCTYPE html>
<html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
'''

STYLE = '''<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--bg:#faf9f7;--card:#fff;--tx:#1c1a17;--dim:#6b665e;--line:#e6e2db;--acc:#b4531f;--ok:#3f7d3f;--warn:#8a6d1f}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#171512;--card:#201d19;--tx:#ece8e1;--dim:#9c958a;--line:#34302a;--acc:#e8853f;--ok:#7bb37b;--warn:#d9b45c;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#171512;--card:#201d19;--tx:#ece8e1;--dim:#9c958a;--line:#34302a;--acc:#e8853f;--ok:#7bb37b;--warn:#d9b45c;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;padding-block:28px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.wrap{{max-width:900px;margin:0 auto}}
h1{{font-size:25px;margin:0 0 6px;text-wrap:balance}}
.sub{{color:var(--dim);font-size:14px;margin-bottom:16px}}
.sub a{{color:var(--acc)}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin-bottom:18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.track{{flex:1;min-width:140px;height:8px;background:var(--bg);border:1px solid var(--line);border-radius:99px;overflow:hidden}}
.fill{{height:100%;width:0;background:var(--ok);transition:width .25s}}
.stat{{font-size:14px;font-variant-numeric:tabular-nums;white-space:nowrap}}
button.reset{{background:none;border:1px solid var(--line);color:var(--dim);border-radius:7px;padding:5px 11px;font-size:13px;cursor:pointer}}
button.reset:hover{{color:var(--tx);border-color:var(--acc)}}
button.reset.arm{{color:var(--acc);border-color:var(--acc)}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:12px 14px;font-size:14px;color:var(--dim);margin-bottom:20px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:16px}}
h2{{font-size:17px;margin:0 0 3px}}
.cnt{{color:var(--dim);font-size:13px;margin-bottom:11px}}
.row{{display:flex;align-items:center;gap:4px;border-radius:8px;border:1px solid transparent}}
.row:hover{{background:var(--bg);border-color:var(--line)}}
.mark{{flex:none;width:30px;height:30px;margin-left:6px;border:none;background:none;cursor:pointer;color:var(--dim);font-size:15px;line-height:1;border-radius:6px}}
.mark:hover{{color:var(--ok)}}
a.ep{{flex:1;display:flex;gap:14px;align-items:baseline;padding:9px 10px;text-decoration:none;color:var(--tx)}}
.mark:focus-visible,a.ep:focus-visible,button.reset:focus-visible{{outline:2px solid var(--acc);outline-offset:1px}}
.num{{font-weight:600;color:var(--acc);min-width:78px;font-size:14px}}
.tc{{font-size:13px;font-variant-numeric:tabular-nums}}
.hint{{color:var(--dim);font-size:12.5px;padding:0 10px 9px 58px;margin-top:-5px}}
.row.seen .num,.row.seen .tc{{color:var(--dim)}}
.row.seen a.ep{{text-decoration:line-through;text-decoration-color:var(--dim);opacity:.62}}
.row.seen .mark{{color:var(--ok)}}
.row.now{{background:color-mix(in srgb,var(--acc) 11%,transparent);border-color:var(--acc)}}
.row.now .mark{{color:var(--acc)}}
.row.now .num{{color:var(--acc)}}
#now{{background:var(--card);border:1px solid var(--acc);border-left:3px solid var(--acc);border-radius:8px;padding:10px 14px;font-size:14px;margin-bottom:18px}}
#now a{{color:var(--acc)}}
footer{{color:var(--dim);font-size:13px;text-align:center;margin-top:22px}}
@media (prefers-reduced-motion:reduce){{.fill{{transition:none}}}}
</style>'''

BODY_OPEN = '''<div class="wrap">
<h1>{h1}</h1>
<div class="sub">Записи стрімів · <a href="https://bit.ly/anime-table" target="_blank" rel="noopener">таблиця-джерело</a> · <a href="https://live.vkvideo.ru/vitecp" target="_blank" rel="noopener">канал</a></div>
<div class="bar"><span class="stat">Переглянуто <b id="stat">0 / 0</b></span><span class="track"><span class="fill" id="fill"></span></span><button class="reset" id="reset" type="button">Скинути</button></div>
<div id="now" hidden></div>
<div class="note">{note}</div>
'''

SCRIPT = '''<footer>Усього записів: {total}</footer></div><script>
(function(){{
 var KEY='{key}', st={{}};
 try{{ st=JSON.parse(localStorage.getItem(KEY)||'null'); }}catch(e){{ st=null; }}
 if(!st||typeof st!=='object'){{ st=JSON.parse(document.getElementById('seed').textContent); }}
 function save(){{ try{{ localStorage.setItem(KEY,JSON.stringify(st)); }}catch(e){{}} }}
 var rows=[].slice.call(document.querySelectorAll('.row'));
 var MARK={{0:'○',1:'▶',2:'✔'}};
 var TIP={{0:'не переглянуто — клік: зараз дивлюся',1:'зараз дивлюся — клік: переглянуто',2:'переглянуто — клік: зняти'}};
 function paint(){{
  var done=0,cur=null;
  rows.forEach(function(r){{
   var v=st[r.dataset.id]||0;
   r.classList.toggle('seen',v===2);
   r.classList.toggle('now',v===1);
   var m=r.querySelector('.mark');
   m.textContent=MARK[v]; m.title=TIP[v]; m.setAttribute('aria-label',TIP[v]);
   if(v===2)done++;
   if(v===1&&!cur)cur=r;
  }});
  document.querySelectorAll('section').forEach(function(s2){{
   var all=s2.querySelectorAll('.row').length,d=s2.querySelectorAll('.row.seen').length;
   s2.querySelector('.cnt').textContent='записів: '+all+' · переглянуто '+d;
  }});
  document.getElementById('stat').textContent=done+' / '+rows.length;
  document.getElementById('fill').style.width=(rows.length?done/rows.length*100:0)+'%';
  var box=document.getElementById('now');
  if(cur){{
   box.hidden=false;
   box.innerHTML='▶ Зараз дивитесь: <b>'+cur.dataset.title+'</b>, '+cur.dataset.ep+
     ' · <a href="#'+cur.dataset.id+'">перейти</a>';
  }} else {{ box.hidden=true; }}
 }}
 rows.forEach(function(r){{
  r.querySelector('.mark').addEventListener('click',function(){{
   var id=r.dataset.id,v=st[id]||0,n=(v+1)%3;
   if(n===1){{ rows.forEach(function(o){{ if(st[o.dataset.id]===1) st[o.dataset.id]=0; }}); }}
   if(n===0){{ delete st[id]; }} else {{ st[id]=n; }}
   save();paint();
  }});
  r.querySelector('a.ep').addEventListener('click',function(){{
   rows.forEach(function(o){{ if(st[o.dataset.id]===1) st[o.dataset.id]=0; }});
   st[r.dataset.id]=1;save();setTimeout(paint,40);
  }});
 }});
 // confirm() is blocked inside the Artifact viewer, so the reset asks for a second click instead
 var rb=document.getElementById('reset'),armed=0;
 function disarm(){{ clearTimeout(armed); armed=0; rb.textContent='Скинути'; rb.classList.remove('arm'); }}
 rb.addEventListener('click',function(){{
  if(!armed){{ rb.textContent='Точно скинути? Ще раз'; rb.classList.add('arm'); armed=setTimeout(disarm,4000); return; }}
  disarm(); st={{}}; save(); paint();
 }});
 paint();
}})();
</script>'''

DOC_CLOSE = '</body></html>'


def hms(t):
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def row_id(uuid, ep, title):
    return f"{uuid[:8]}-{ep}-{hashlib.md5(title.encode()).hexdigest()[:4]}"


def build(cfg, fragment=False):
    out = []
    if not fragment:
        out.append(DOC_OPEN)
    out.append(STYLE.format(title=html.escape(cfg["title"])))
    out.append("\n" if fragment else "</head><body>")
    out.append(BODY_OPEN.format(h1=html.escape(cfg["h1"]), note=cfg["note"]))
    total = 0
    for sec in cfg["sections"]:
        t = sec["title"]; et = html.escape(t)
        lines = [f'<section><h2>{et}</h2><div class="cnt"></div>']
        for r in sec["rows"]:
            rid = row_id(r["uuid"], r["ep"], t); ep = f"серія {r['ep']}"
            href = f"https://live.vkvideo.ru/vitecp/record/{r['uuid']}?tab=video&amp;tc={r['tc']}"
            lines.append(f'<div class="row" id="{rid}" data-id="{rid}" data-title="{et}" data-ep="{ep}"><button class="mark" type="button">○</button>'
                         f'<a class="ep" href="{href}" target="_blank" rel="noopener"><span class="num">{ep}</span><span class="tc">{hms(r["tc"])}</span></a></div>')
            if r.get("hint"):
                lines.append(f'<div class="hint">{html.escape(r["hint"])}</div>')
            total += 1
        lines.append('</section>')
        out.append("\n".join(lines) + "\n")
    out.append(f'<script type="application/json" id="seed">{json.dumps(cfg.get("seed", {}), ensure_ascii=False)}</script>\n')
    out.append(SCRIPT.format(total=total, key=cfg["storage_key"]))
    if not fragment:
        out.append(DOC_CLOSE)
    return "".join(out)


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(build(cfg, fragment="--fragment" in sys.argv[3:]))
