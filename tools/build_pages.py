#!/usr/bin/env python3
"""KidsTrip の個別ページを作る（毎日の更新で、commit の前に実行する）。

  python3 tools/build_pages.py

- index.html をブラウザで開いてデータ（js/data.js の EVENTS・BABY など）を読み、
  event/<ID>/index.html（イベントごと）と spot/<ID>/index.html（赤ちゃん設備のある施設ごと）を作る。
- 一覧から外れたイベント・施設のページは消さずに「掲載終了」のページにする（送られたリンクが切れないように）。
- sitemap.xml を全ページぶん作り直す。lastmod は中身が変わった日だけ新しくする（記録は tools/pages.json）。
- index.html の目印（<!--PAGES:START--> 〜 <!--PAGES:END-->、<!--LD:START--> 〜 <!--LD:END-->）の間を書き直す。
"""
import datetime, hashlib, html, json, os, re, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://kidstrip.jp/"
TODAY = datetime.date.today()
MANIFEST = os.path.join(ROOT, "tools", "pages.json")
TRACK_URL_RE = re.compile(r'const TRACK_URL = "([^"]*)"')
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def hash_id(t):  # index.html の hashId と同じ（FNV-1a 32bit → 36進数）
    h = 0x811c9dc5
    for ch in t:
        h ^= ord(ch)
        h = (h * 16777619) & 0xffffffff
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        h, r = divmod(h, 36)
        out = digits[r] + out
        if h == 0:
            return out


def load_data():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page()
        pg.goto("file://" + os.path.join(ROOT, "index.html"))
        pg.wait_for_timeout(800)
        d = pg.evaluate("""() => ({
          events: EVENTS.map(e => Object.assign({}, e, { area: FOOD_OF[e.t] || "" })),
          baby: BABY,
          areas: Object.fromEntries(FOOD_AREAS.map(a => [a.k, (FOOD[a.k] && FOOD[a.k].name) || a.name || ""])),
          rain: RAIN_LABEL,
          weekends: WEEKENDS,
          // 個別ページを厚くするための、データから出せる周りの情報（推測はしない）
          extra: (() => {
            const strip = h => (h || "").split(/<[^>]+>/).map(x => x.trim()).filter(Boolean);
            const mins = (a, b) => Math.max(1, Math.round(distM(a, b) * 1.3 / 70));
            const ev = {}, sp = {};
            // 施設の位置：SPOT_GEO にないものは、会場の位置（VENUE_GEO）の名前で引く
            const SPOT_GEO_ALL = {};
            Object.values(BABY).forEach(list => list.forEach(b => { const g = SPOT_GEO[b.n] || (VENUE_GEO.find(([re]) => re.test(b.n)) || [])[1]; if (g) SPOT_GEO_ALL[b.n] = g; }));
            EVENTS.forEach(e => {
              const k = accessKey(e), a = k ? ACCESS[k] : null, g = venueGeo(e);
              ev[e.id] = {
                geo: g || null,
                acc: strip(accPoints(e, k, a)),
                food: kidsFoodNear(e).slice(0, 8).map(x => ({ n: x.sh.n, gen: x.sh.gen || "", min: x.min, tags: x.sh.tags.slice(0, 3) })),
                courts: foodCourtNear(e).slice(0, 3).map(x => ({ n: x.c.n, min: x.min })),
                clothes: g ? CLOTHES.filter(c => c.g).map(c => ({ n: c.n, url: c.url, hours: c.hours, kinds: c.kinds || [], min: mins(g, c.g) })).filter(x => x.min <= 15).sort((p, q) => p.min - q.min).slice(0, 5) : [],
                spots: g ? Object.entries(SPOT_GEO_ALL).map(([n, sg]) => ({ n, min: mins(g, sg) })).filter(x => x.min <= 10).sort((p, q) => p.min - q.min).slice(0, 6) : [],
              };
            });
            const seen = new Set();
            Object.values(BABY).forEach(list => list.forEach(b => {
              if (seen.has(b.n)) return; seen.add(b.n);
              const g = SPOT_GEO[b.n] || (VENUE_GEO.find(([re]) => re.test(b.n)) || [])[1]; const p = PAPA[b.n];
              sp[b.n] = {
                geo: g || null,
                // 座標の出どころ：own＝施設の名前で登録（未確認）、borrowed＝会場の名前のパターンで借りた、official＝公式で確かめた
                geoSrc: !g ? "" : (typeof GEO_SRC !== "undefined" && GEO_SRC[b.n] === "official") ? "official" : SPOT_GEO[b.n] ? "own" : "borrowed",
                addr: (typeof SPOT_ADDR !== "undefined" && SPOT_ADDR[b.n]) || null,
                papa: p ? { label: PAPA_LABEL[p.v] || "", t: p.t || "" } : null,
                food: g ? KIDS_SHOPS.filter(sh => sh.g).map(sh => ({ n: sh.n, gen: sh.gen || "", min: mins(g, sh.g), tags: sh.tags.slice().sort((p, q) => (/離乳食|温め/.test(q) ? 1 : 0) - (/離乳食|温め/.test(p) ? 1 : 0)).slice(0, 3) })).filter(x => x.min <= 10).sort((p, q) => p.min - q.min).slice(0, 8) : [],
                courts: g ? FOOD_COURTS.map(c => ({ n: c.n, min: mins(g, c.g) })).filter(x => x.min <= 10).sort((p, q) => p.min - q.min).slice(0, 3) : [],
                clothes: g ? CLOTHES.filter(c => c.g).map(c => ({ n: c.n, url: c.url, hours: c.hours, kinds: c.kinds || [], min: mins(g, c.g) })).filter(x => x.min <= 15).sort((p, q) => p.min - q.min).slice(0, 5) : [],
                events: g ? EVENTS.map(e => ({ e, g2: venueGeo(e) })).filter(x => x.g2 && mins(g, x.g2) <= 15).map(x => ({ id: x.e.id, min: mins(g, x.g2) })).sort((p, q) => p.min - q.min).slice(0, 10) : [],
              };
            }));
            return { ev, sp };
          })(),
        })""")
        b.close()
    return d


def year_of(m):
    return TODAY.year if m >= TODAY.month - 1 else TODAY.year + 1


def iso(k):
    m, d = map(int, k.split("/"))
    return datetime.date(year_of(m), m, d)


def jp_date(k):
    dt = iso(k)
    return f"{dt.month}月{dt.day}日({'月火水木金土日'[dt.weekday()]})"


def when_text(e):
    if e["kind"] == "ongoing":
        return (e["period"] if ("確認" in e["period"] or "いつでも" in e["period"]) else "会期 " + e["period"]) if e.get("period") else "開催中"
    st = e.get("stop") or {}
    return "・".join(jp_date(k) + (f"（{st[k]}）" if k in st else "") for k in e["days"])


CSS = """
.finder{margin:12px 0 6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.finder label{font-weight:700;font-size:.95em;width:100%}.finder input{flex:1;min-width:0;font-size:16px;padding:8px 10px;border:1px solid #c9d3dc;border-radius:8px}
.toc{margin:6px 0 12px;font-size:.9em;line-height:2}.toc a{display:inline-block;margin:0 8px 0 0;white-space:nowrap}
.gkcmp th[scope=row]{white-space:nowrap}.gkcmp td{font-size:.92em}
.fac li{padding:8px 10px;margin:6px 0}
.gk{list-style:none;padding:0}.gk li{border:1px solid #e5e5e5;border-radius:10px;padding:10px 12px;margin:8px 0;line-height:1.7}.gk h3{margin:0 0 2px;font-size:1.02em}
:root{--paper:#f8fafc;--card:#fff;--ink:#18222e;--muted:#5b6875;--line:#dde3e9;--accent:#0a6f95;--accent-soft:#e2f0f6;--ok:#2e7d4f;--bad:#b3372b}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN","Yu Gothic","Meiryo",sans-serif;line-height:1.7}
.wrap{max-width:760px;margin:0 auto;padding:16px}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.top img{width:min(200px,50vw);height:auto;display:block}
.crumb{font-size:12.5px;color:var(--muted);margin:4px 0 10px}.crumb a{color:var(--muted)}
h1{font-size:22px;line-height:1.4;margin:0 0 6px}h2{font-size:17px;margin:22px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.ended{background:#fbf0d9;color:#7a5200;border-radius:12px;padding:10px 12px;margin:0 0 12px;font-weight:700}
table.info{width:100%;border-collapse:collapse;font-size:14.5px}table.info th{width:6.5em;text-align:left;color:var(--muted);font-weight:700;vertical-align:top;padding:6px 8px 6px 0}table.info td{padding:6px 0;border-bottom:1px solid var(--line)}
.sum{margin:10px 0}.tip{background:var(--accent-soft);border-radius:10px;padding:8px 10px;font-size:14px}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px}.btn{display:inline-block;padding:7px 14px;border-radius:999px;border:1px solid var(--accent);color:var(--accent);background:var(--card);text-decoration:none;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit}
.btn.main{background:var(--accent);color:#fff}.btn.line{background:#06c755;border-color:#06c755;color:#fff}
table.bm{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--card)}table.bm th,table.bm td{border-bottom:1px solid var(--line);padding:6px 4px}table.bm thead th{font-size:12px;color:var(--muted);text-align:center}table.bm thead th:first-child,table.bm tbody th{text-align:left}
td.y{color:var(--ok);text-align:center;font-weight:700}td.n{color:var(--bad);text-align:center;font-weight:700}td.u{color:var(--muted);text-align:center}
.legend,.small{font-size:12px;color:var(--muted)}ul.food .tag{font-size:11.5px;margin-left:6px;padding:1px 7px;border-radius:999px;background:#f1f4f7;color:#3b5266}ul.links{padding-left:1.2em}ul.links li{margin:4px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0;margin:8px 0}.chips li{font-size:12.5px;padding:2px 10px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-weight:700}
footer{margin:28px 0 8px;font-size:12px;color:var(--muted)}
.mlead{margin:4px 0 8px}.mlead summary{cursor:pointer;color:var(--accent);font-weight:700;font-size:14px}.mlead[open] summary{margin-bottom:4px}
a{color:var(--link)}
:root{--link:#0b57b5;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#11171e;--card:#19212b;--ink:#e8edf2;--muted:#9aa8b5;--line:#2a3542;--accent:#5cb8dc;--accent-soft:#15303d;--ok:#6cc690;--bad:#f08a7e;--link:#8cc4ff;color-scheme:dark}
:root:not([data-theme="light"]) .ended{background:#382c14;color:#ffd9a8}:root:not([data-theme="light"]) ul.food .tag{background:#243140;color:#c5d3e0}:root:not([data-theme="light"]) .gk li{border-color:var(--line)}:root:not([data-theme="light"]) .finder input{background:var(--card);color:var(--ink);border-color:var(--line)}:root:not([data-theme="light"]) .btn.main{color:#0c1a22}}
:root[data-theme="dark"]{--paper:#11171e;--card:#19212b;--ink:#e8edf2;--muted:#9aa8b5;--line:#2a3542;--accent:#5cb8dc;--accent-soft:#15303d;--ok:#6cc690;--bad:#f08a7e;--link:#8cc4ff;color-scheme:dark}
:root[data-theme="dark"] .ended{background:#382c14;color:#ffd9a8}:root[data-theme="dark"] ul.food .tag{background:#243140;color:#c5d3e0}:root[data-theme="dark"] .gk li{border-color:var(--line)}:root[data-theme="dark"] .finder input{background:var(--card);color:var(--ink);border-color:var(--line)}:root[data-theme="dark"] .btn.main{color:#0c1a22}
"""

SHARE_JS = """document.addEventListener("click",async ev=>{const b=ev.target.closest("[data-share]");if(!b)return;const url=location.href.split("?")[0],title=document.title;
if(navigator.share){try{await navigator.share({title,url})}catch(_){}return}
try{await navigator.clipboard.writeText(url);b.textContent="コピーしました"}catch(_){b.textContent=url}});"""


def track_js(track_url, page):
    if not track_url:
        return ""
    return """(function(){var U=%s;if(!/(github\\.io|kidstrip\\.jp)$/.test(location.hostname))return;var v="";try{v=localStorage.getItem("vid")||"";if(!v){v=Math.random().toString(36).slice(2,10);localStorage.setItem("vid",v)}}catch(_){}try{if(localStorage.getItem("me")==="1")v="自分_"+v}catch(_){}
var ua=navigator.userAgent,dev=/iPhone|iPod/.test(ua)?"iPhone":/iPad/.test(ua)?"iPad":/Android/.test(ua)?(/Mobile/.test(ua)?"Androidスマホ":"Androidタブレット"):"PC",app=/\\bLine\\//i.test(ua)?"LINEアプリ内":/Instagram/.test(ua)?"Instagramアプリ内":/FBAN|FBAV/.test(ua)?"Facebookアプリ内":"ブラウザ",tz="";try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||""}catch(_){}
function t(type,value,target){var ref="";try{ref=document.referrer?new URL(document.referrer).hostname:""}catch(_){}var body=JSON.stringify({type:type,value:String(value||"").slice(0,200),target:String(target||"").slice(0,200),dev:dev,app:app,ref:ref.slice(0,100),vid:v,page:%s,lang:(navigator.language||"").slice(0,10),tz:tz.slice(0,40),jp:tz?(tz==="Asia/Tokyo"?"日本":"海外"):"",ua:ua.slice(0,160),bot:navigator.webdriver?"1":""});try{navigator.sendBeacon?navigator.sendBeacon(U,new Blob([body],{type:"text/plain"})):fetch(U,{method:"POST",body:body,mode:"no-cors",keepalive:true})}catch(_){}}
t("pageview",document.title);document.addEventListener("click",function(ev){var a=ev.target.closest("a,[data-share]");if(!a)return;var h=a.getAttribute("href")||"",n=document.querySelector("h1")?document.querySelector("h1").textContent:"";
if(a.hasAttribute("data-share"))return t("copy_link","個別ページ",n);if(a.dataset.act)return t(a.dataset.act,a.href,n);if(/line\\.me\\/R\\/share/.test(h))return t("line_share","個別ページ",n);if(/^matome\\//.test(%s)&&/^\\/(event|spot)\\/[^\\/]+\\/$/.test(h))return t("matome_item",h,n);if(/^https?:/.test(h)&&h.indexOf(location.hostname)<0)return t("outlink",a.href,n)})})();""" % (json.dumps(track_url), json.dumps(page), json.dumps(page))


FINDER_JS = r"""(function(){var q=document.getElementById('kf');if(!q)return;var art=q.closest('article');var hs=[].slice.call(art.querySelectorAll('h2[id^="s"]'));
function rows(b){var a=[],us=[];if(b.matches('ul,ol'))us.push(b);us=us.concat([].slice.call(b.querySelectorAll('ul,ol')));us.forEach(function(u){a=a.concat([].slice.call(u.children))});[].slice.call(b.querySelectorAll('tr')).forEach(function(r){if(r.querySelector('td'))a.push(r)});return a}
function blk(h){var a=[],el=h.nextElementSibling;while(el&&el.tagName!=='H2'){a.push(el);el=el.nextElementSibling}return a}
q.addEventListener('input',function(){var v=q.value.trim().toLowerCase(),tot=0;hs.forEach(function(h){var n=0,bs=blk(h);bs.forEach(function(b){rows(b).forEach(function(r){var ok=!v||r.textContent.toLowerCase().indexOf(v)>=0;r.style.display=ok?'':'none';if(ok)n++})});var sh=!v||n>0;h.style.display=sh?'':'none';bs.forEach(function(b){b.style.display=sh?'':'none'});tot+=n});
document.getElementById('kfn').textContent=v?(tot?tot+'件見つかりました':'見つかりませんでした（ことばを短くしてみてください）'):'';document.getElementById('ktoc').style.display=v?'none':''})})();"""


def add_finder(body, label, ph):
    """長い一覧ページ（区ごとの施設・/event/・/spot/）に、目次と「ことばで絞り込む」欄を入れる。JSが動かなくても一覧はそのまま読める"""
    heads = []
    def sub(m):
        txt = re.sub(r"<[^>]+>", "", m.group(1))
        if txt.startswith("ほかの区"): return m.group(0)
        heads.append(txt); return f'<h2 id="s{len(heads)}">{m.group(1)}</h2>'
    body = re.sub(r"<h2>(.*?)</h2>", sub, body)
    if len(heads) < 3: return body
    toc = '<nav class="toc" id="ktoc" aria-label="もくじ"><b>もくじ：</b>' + "".join(f'<a href="#s{i + 1}">{E(h)}</a>' for i, h in enumerate(heads)) + "</nav>"
    box = (f'<div class="finder"><label for="kf">{E(label)}</label><input id="kf" type="search" placeholder="{E(ph)}" autocomplete="off">'
           '<span id="kfn" class="small" aria-live="polite"></span></div>')
    i = body.find('<h2 id="s1">')
    return body[:i] + box + toc + body[i:] + f"<script>{FINDER_JS}</script>"


def page(title, desc, path, body, ld, noindex=False, track_url="", tpage="", og=None, og_alt=None):
    if path in ("event/", "spot/") or (path.startswith("area/") and path.count("/") == 2):
        body = add_finder(body, *{"event/": ("イベント名・会場・区で絞り込む", "例：クリスマス、動物園、中区"), "spot/": ("施設の名前・駅で絞り込む", "例：ららぽーと、横浜駅、そごう")}.get(path, ("施設の名前・種類・町名で絞り込む", "例：プレイルーム、公園、町の名前")))
    url = SITE + path
    up = "../" * path.strip("/").count("/") + "../"
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>try{{var t=localStorage.getItem("theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}}catch(_){{}}</script>
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{robots}<link rel="canonical" href="{url}">
<meta property="og:type" content="{"website" if path == "about/" else "article"}">
<meta property="og:site_name" content="KidsTrip">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og or "img/ogp.jpg"}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{E(og_alt) if og_alt else "KidsTrip（キッズトリップ）のロゴ。観覧車やお城を背景に、両手を広げて喜ぶ4人家族のイラスト"}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" sizes="192x192" href="{up}img/favicon-192.png">
<link rel="icon" type="image/png" sizes="48x48" href="{up}img/favicon-48.png">
<link rel="icon" href="{up}img/favicon.png">
<link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">
{lds}<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<div class="top"><a href="/"><img src="{up}img/logo.webp" width="640" height="191" alt="KidsTrip（キッズトリップ）トップへ"></a><a class="btn" href="/">イベント一覧へ</a></div>
{body}
<footer><p>KidsTrip（キッズトリップ）横浜の子連れおでかけ・イベント一覧。施設・主催者の公式情報などをもとに要約しています。内容は変わることがあるので、出かける前に必ず公式ページで確認してください。</p>
<p>サイトをよくするため、押されたボタン・リンクの回数を、名前などの個人情報なしで記録しています。</p>
<p class="small"><a href="/event/">イベント一覧</a>　<a href="/area/">区ごとの施設・遊び場</a>　<a href="/spot/">授乳室・おむつ替えのある施設</a>　<a href="/matome/">特集・まとめ</a><br><a href="/about/">このサイトについて</a>　<a href="/contact/">お問い合わせ</a>　<a href="/privacy/">プライバシーポリシー</a></p></footer>
</div>
<script>{SHARE_JS}{track_js(track_url, tpage)}</script>
</body>
</html>
"""


def line_url(text):
    from urllib.parse import quote
    return "https://line.me/R/share?text=" + quote(text)


def mark(v):
    return '<td class="y">○</td>' if v is True else '<td class="n">×</td>' if v is False else '<td class="u">？</td>'


def short(n):
    return re.sub(r"[（(].*$", "", n).strip()


def matrix(list_, spot_ids):
    if not list_:
        return ""
    rows = "".join(f'<tr><th scope="row"><a href="/spot/{spot_ids[b["n"]]}/">{E(short(b["n"]))}</a></th>{mark(b.get("d"))}{mark(b.get("f"))}{mark(b.get("w"))}{mark(b.get("mw"))}</tr>' for b in list_)
    return f'<table class="bm"><thead><tr><th>場所</th><th>おむつ替え</th><th>授乳室</th><th>お湯</th><th>レンジ</th></tr></thead><tbody>{rows}</tbody></table><p class="legend">○ あり　× なし　？ 調べた範囲で確認できず</p>'


def crumbs(items):
    html_ = " ＞ ".join(f'<a href="{u}">{E(n)}</a>' if u else E(n) for n, u in items)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE + u.lstrip("/")} if u else {})} for i, (n, u) in enumerate(items)]}
    return f'<p class="crumb">{html_}</p>', ld


def og_when(e):
    ds = sorted(iso(k) for k in (e.get("days") or []))
    if e.get("kind") == "ongoing" or not ds:
        return "いつでも行ける" if e.get("kind") == "ongoing" else "日にちは公式で確認"
    f = lambda x: f"{x.month}/{x.day}（{'月火水木金土日'[x.weekday()]}）"
    return f(ds[0]) if len(ds) == 1 else f"{f(ds[0])}〜{f(ds[-1])}"


OG_HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>
html,body{margin:0;width:1200px;height:630px;font-family:"Noto Sans CJK JP","Noto Sans JP",sans-serif}
.w{box-sizing:border-box;width:1200px;height:630px;padding:56px 64px;display:flex;flex-direction:column;justify-content:space-between;
background:linear-gradient(135deg,#e2f0f6 0%,#fff6e5 100%);border:18px solid #0a6f95}
.tag{display:inline-block;background:#0a6f95;color:#fff;font-size:30px;font-weight:700;padding:6px 18px;border-radius:999px}
.t{font-size:TSIZEpx;font-weight:900;line-height:1.25;color:#17324a;margin:18px 0 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.m{font-size:38px;font-weight:700;color:#0a6f95}
.v{font-size:28px;color:#3b5266;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.f{display:flex;align-items:center;justify-content:space-between}
.f img{height:84px}.f span{font-size:26px;color:#3b5266}
</style></head><body><div class="w"><div><span class="tag">TAG</span><div class="t">TITLE</div></div>
<div><div class="m">WHEN</div><div class="v">VENUE</div></div>
<div class="f"><img src="LOGO"><span>横浜の子連れおでかけ・イベント一覧</span></div></div></body></html>"""


def render_og(events, man_og):
    """イベントごとのOG画像（1200x630のJPEG）を og/ID.jpg に作る。中身が変わったものだけ作り直す。"""
    os.makedirs(os.path.join(ROOT, "og"), exist_ok=True)
    todo = []
    new = {}
    for e in events:
        w = (e.get("ward") or "").split("・")[0]
        tag = ("無料" if e["price"] == "free" else "") + ("　" if e["price"] == "free" else "") + (w or "横浜市")
        key = hashlib.sha1("|".join([e["t"], og_when(e), tag, e["venue"], "v2"]).encode()).hexdigest()[:12]
        new[e["id"]] = key
        if man_og.get(e["id"]) != key or not os.path.exists(os.path.join(ROOT, "og", e["id"] + ".jpg")):
            todo.append((e, tag))
    if todo:
        logo = "file://" + os.path.join(ROOT, "img", "logo.webp")
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            for e, tag in todo:
                n = len(e["t"])
                size = 72 if n <= 18 else 62 if n <= 28 else 54 if n <= 40 else 46
                html_s = (OG_HTML.replace("TSIZE", str(size)).replace("TAG", E(tag)).replace("TITLE", E(e["t"]))
                          .replace("WHEN", E(og_when(e) + ("　" + e["time"] if e.get("kind") == "limited" and len(e.get("time", "")) <= 14 else "")))
                          .replace("VENUE", E(e["venue"])).replace("LOGO", logo))
                tmp = os.path.join(ROOT, "og", "_tmp.html")
                open(tmp, "w", encoding="utf-8").write(html_s)
                pg.goto("file://" + tmp)
                pg.wait_for_timeout(50)
                pg.screenshot(path=os.path.join(ROOT, "og", e["id"] + ".jpg"), type="jpeg", quality=78)
            b.close()
        os.remove(os.path.join(ROOT, "og", "_tmp.html"))
    return new, len(todo)


def render_og_spots(spots, spot_ids, areas, man_og):
    """赤ちゃん設備のある施設ごとのOG画像（og/spot-ID.jpg）。名前・設備の○×？・エリアが変わったものだけ作り直す。"""
    sym = lambda v: "○" if v is True else "×" if v is False else "？"
    todo, new = [], {}
    for n, (b, area) in spots.items():
        sid = spot_ids[n]
        when = f"おむつ替え{sym(b.get('d'))}　授乳室{sym(b.get('f'))}　お湯{sym(b.get('w'))}"
        venue = areas.get(area, "") + ("・" + b["where"] if b.get("where") else "")
        key = hashlib.sha1("|".join([n, when, venue, "s1"]).encode()).hexdigest()[:12]
        new[sid] = key
        if man_og.get(sid) != key or not os.path.exists(os.path.join(ROOT, "og", f"spot-{sid}.jpg")):
            todo.append((sid, short(n) + "の授乳室・おむつ替え", when, venue))
    if todo:
        logo = "file://" + os.path.join(ROOT, "img", "logo.webp")
        tmp = os.path.join(ROOT, "og", "_tmp.html")
        with sync_playwright() as p:
            br = p.chromium.launch(executable_path="/usr/bin/google-chrome")
            pg = br.new_page(viewport={"width": 1200, "height": 630})
            for sid, t, when, venue in todo:
                size = 72 if len(t) <= 18 else 62 if len(t) <= 28 else 54
                open(tmp, "w", encoding="utf-8").write(OG_HTML.replace("TSIZE", str(size)).replace("TAG", "赤ちゃん設備").replace("TITLE", E(t))
                                                     .replace("WHEN", E(when)).replace("VENUE", E(venue)).replace("LOGO", logo))
                pg.goto("file://" + tmp); pg.wait_for_timeout(50)
                pg.screenshot(path=os.path.join(ROOT, "og", f"spot-{sid}.jpg"), type="jpeg", quality=78)
            br.close()
        os.remove(tmp)
    return new, len(todo)


WARD_ORDER_ALL = ["鶴見区","神奈川区","西区","中区","南区","港南区","保土ケ谷区","旭区","磯子区","金沢区","港北区","緑区","青葉区","都筑区","戸塚区","栄区","泉区","瀬谷区"]


def play_ok(x):
    return x.get("kind") == "ongoing" and x.get("price") == "free" and (x.get("freeplay") or x.get("animal") or x.get("ride"))


def food_list(food, courts):
    if not food and not courts:
        return ""
    li = "".join(f'<li><b>{E(f["n"])}</b>' + (f'（{E(f["gen"])}）' if f.get("gen") else "") + f'　ベビーカーで約{f["min"]}分' +
                 ("".join(f'<span class="tag">{E(t)}</span>' for t in f.get("tags") or [])) + "</li>" for f in food)
    li += "".join(f'<li><b>{E(c["n"])}</b>（フードコート）　ベビーカーで約{c["min"]}分</li>' for c in courts)
    return (f'<h2>歩いて10分以内の子連れで入りやすいごはん</h2><ul class="links food">{li}</ul>'
            '<p class="small">時間はベビーカーで歩いたときのめやす（直線距離から計算）。メニューや営業時間は行く前にお店で確かめてください。</p>')


def clothes_list(cl):
    if not cl:
        return ""
    li = "".join(f'<li><a href="{E(c["url"])}" target="_blank" rel="noopener">{E(c["n"])}</a>' + (f'<span class="tag">{E("・".join("子どもの靴" if x == "靴" else x for x in c["kinds"]))}</span>' if c.get("kinds") else '<span class="tag">取り扱いは公式で未確認</span>') + f'　{E(c["hours"])}　ベビーカーで約{c["min"]}分</li>' for c in cl)
    return (f'<h2>歩いて15分以内でベビー服・子ども服・靴が買えるお店</h2><ul class="links food">{li}</ul>'
            '<p class="small">急なおもらし・汚れの着替えや、靴を忘れたときに。時間は直線距離からのめやす。在庫・営業時間はお店で確かめてください（出典：各チェーン公式の店舗検索）。</p>')


def circles_html(x):
    cs = x.get("circles") or []
    if not cs:
        return ""
    li = "".join(f'<li><b>{E(c["n"])}</b>：{E(c["what"])}／{E(c["when"])}／対象：{E(c["age"])}</li>' for c in cs)
    link = f'<a href="{E(x["circlesUrl"])}" target="_blank" rel="noopener">サークル紹介</a>' if x.get("circlesUrl") else "サークル紹介"
    return (f'<h2>ここで活動している子ども向けサークル</h2><ul class="links">{li}</ul>'
            f'<p class="small">活動日は団体の登録時の情報で、変わっていることがあります。入会・見学は施設に問い合わせてください（{link}・{E(x.get("circlesAsof", ""))}）。</p>')


def split_venue(venue):
    """会場の文字列から、施設名と住所を分ける（例：「立場地区センター（泉区中田北1-9-14）」→ 名前・区・番地）。住所がなければ番地は空。"""
    m = re.search(r"（([^（）]*?・)?(?:横浜市)?([^（）・]{1,6}区)([^（）]*?\d[^（）]*)）", venue or "")
    if not m:
        return (venue or "").strip(), "", ""
    keep = f"（{m.group(1).rstrip('・')}）" if m.group(1) else ""
    name = re.sub(r"\s+", " ", (venue[:m.start()] + keep + venue[m.end():])).strip(" ・") or venue
    return name, m.group(2), m.group(3).strip()


def event_page(e, d, spot_ids, track_url):
    path = f"event/{e['id']}/"
    ward1 = e["ward"].split("・")[0]
    wsuf = "" if (e.get("ward") or "").split("・")[0] in e["t"] else f"（{e['ward']}）"  # 名前に区名が入っていれば二重に付けない
    if e["kind"] == "ongoing":  # 通年の施設・遊び場：検索結果に「会期」ではなく中身が出るように
        title = f"{e['t']}{wsuf}｜横浜の子連れおでかけ｜KidsTrip"
        desc = f"{e['sum']}（{e['venue']}・{re.sub(r'（.*?）', '', e.get('priceText', ''))[:30]}）"[:120]
    else:
        title = f"{e['t']}{wsuf}｜横浜の子連れイベント｜KidsTrip"
        desc = f"{when_text(e)[:60]}　{e['venue']}。{e['sum']}"[:120]
    area = e.get("area") or ""
    babies = d["baby"].get(area, [])
    if e["kind"] == "ongoing" and ward1 in WARD_SLUG:
        ch, cld = crumbs([("トップ", "/"), ("区ごとの施設・遊び場", "/area/"), (ward1, f"/area/{WARD_SLUG[ward1]}/"), (e["t"], "")])
    else:
        ch, cld = crumbs([("トップ", "/"), ("施設・遊び場" if e["kind"] == "ongoing" else "イベント一覧", "/area/" if e["kind"] == "ongoing" else "/event/"), (e["t"], "")])
    chips = "".join(f"<li>{E(x)}</li>" for x in [
        {"free": "無料", "admission": "入園料のみ", "paid": "有料"}.get(e["price"], "料金要確認"), e["ageText"], e["place"], d["rain"].get(e["rain"], "")] if x)
    resv = f'<a class="btn" data-act="resv" href="{E(e["resvUrl"])}" target="_blank" rel="noopener">予約ページへ</a>' if e.get("resvUrl") else ""
    url = SITE + path
    share_text = f"【{e['t']}】\n{when_text(e)}　{e['time']}\n場所：{e['ward']}・{e['venue']}\n{url}"
    others = [x for x in d["events"] if x.get("area") == area and area and x["id"] != e["id"]][:8]
    ex = d["extra"]["ev"].get(e["id"], {})
    spot_rows = [b for nm in [x["n"] for x in ex.get("spots", [])] for b in [d["_spot_by_name"].get(nm)] if b]
    near_spots_html = ('<h2>歩いて10分以内のおむつ替え・授乳室・お湯</h2>' + matrix(spot_rows, spot_ids)) if spot_rows else ""
    acc_html = ('<h2>行き方のめやす</h2><ul class="links">' + "".join(f"<li>{E(x)}</li>" for x in ex["acc"]) + "</ul>") if ex.get("acc") else ""
    food_html = food_list(ex.get("food", []), ex.get("courts", []))
    w1 = (e.get("ward") or "").split("・")[0]
    plays = [x for x in d["events"] if play_ok(x) and x["id"] != e["id"] and w1 and w1 in (x.get("ward") or "")]
    plays.sort(key=lambda x: (not str(x.get("place", "")).startswith("屋内"), x["t"]))
    play_html = (f'<h2>{E(w1)}の無料で遊べる場所（雨の日は屋内から）</h2><ul class="links">' + "".join(
        f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(str(x.get("place", "")).replace("（", "・").split("・")[0])}）</li>' for x in plays[:8]) + "</ul>") if plays else ""
    sn = d.get("_spot_of_ev", {}).get(e["id"])
    same_spot = (f'<p class="tip">👶 {E(short(sn))}の授乳室・おむつ替え・お湯の場所（何階のどこか・パパも使えるか）は、<a href="/spot/{spot_ids[sn]}/">{E(short(sn))}の授乳室・おむつ替えのページ</a>にまとめています。</p>') if sn else ""
    sameday_html = ""
    if e["kind"] == "limited" and e.get("days"):
        d0 = e["days"][0]
        same = [x for x in d["events"] if x["id"] != e["id"] and x["kind"] == "limited" and d0 in (x.get("days") or [])]
        same.sort(key=lambda x: (w1 not in (x.get("ward") or ""), x["t"]))
        if same:
            sameday_html = (f'<h2>{E(jp_date(d0))}に開かれるほかの親子イベント</h2><ul class="links">' + "".join(
                f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(x["ward"])}）</li>' for x in same[:8]) + "</ul>")
    body = f"""{ch}
<article class="card">
<h1>{E(e['t'])}</h1>
{('<p class="tip">主催から「公式の情報を見てほしい」とのお願いがあるため、くわしい行き方・交通規制・当日の開催などは主催の公式ページで確認してください。</p><div class="btns"><a class="btn main" data-act="official" href="' + E(e['url']) + '" target="_blank" rel="noopener">' + E(e.get('officialLabel') or '主催の公式ページを開く') + '</a></div>') if e.get('officialOnly') else ''}
<ul class="chips">{chips}</ul>
<table class="info">
<tr><th>日にち</th><td>{E(when_text(e))}</td></tr>
<tr><th>時間</th><td>{E(e['time'])}</td></tr>
<tr><th>場所</th><td>{E(e['ward'])}・{E(e['venue'])}</td></tr>
<tr><th>料金</th><td>{E(e['priceText'])}</td></tr>
<tr><th>対象</th><td>{E(e['ageText'])}</td></tr>
<tr><th>予約</th><td>{E(e['resvText'])}</td></tr>
<tr><th>雨の日</th><td>{E(d['rain'].get(e['rain'], ''))}{'' if (e.get('rainText') or '').strip() in ('', d['rain'].get(e['rain'], '')) else '（' + E(e['rainText']) + '）'}</td></tr>
</table>
<p class="sum">{E(e['sum'])}</p>
{f'<p class="tip">💡 {E(e["tip"])}</p>' if e.get('tip') else ''}
<p class="small">{("情報の時点：" + E(e["asof"]) + "　") if e.get("asof") else ""}出典：{E(e['src'])}</p>
<div class="btns"><a class="btn main" data-act="official" href="{E(e['url'])}" target="_blank" rel="noopener">公式ページで確認</a>{resv}
<a class="btn" href="/?e={E(e['id'])}">一覧で見る（行き方・近くのごはん）</a>
{'' if e.get('noShare') else '<button type="button" class="btn" data-share="1">🔗 リンクを送る・コピー</button>\n<a class="btn line" href="' + E(line_url(share_text)) + '" target="_blank" rel="noopener">LINEで送る</a>'}</div>
</article>
{same_spot}
{f'<h2>近くのおむつ替え・授乳室・お湯（{E(d["areas"].get(area, ""))}）</h2>' + matrix(babies, spot_ids) if babies else near_spots_html}
{acc_html}
{food_html}
{clothes_list(ex.get("clothes", []))}
{circles_html(e)}
{play_html}
{sameday_html}
{('<h2>近くのほかのイベント</h2><ul class="links">' + ''.join(f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(when_text(x)[:30])}）</li>' for x in others) + '</ul>') if others else ''}
"""
    ld = [cld]
    vname, vward, vstreet = split_venue(e["venue"])
    addr = {"@type": "PostalAddress", **({"streetAddress": vstreet} if vstreet else {}), "addressLocality": "横浜市" + (vward or ward1), "addressRegion": "神奈川県", "addressCountry": "JP"}
    g = (ex or {}).get("geo")
    geo = {"@type": "GeoCoordinates", "latitude": g[0], "longitude": g[1]} if g else None
    if e["kind"] == "limited" and e["days"]:
        days = sorted(iso(k) for k in e["days"])
        start = days[0].isoformat()
        if len(days) == 1 and isinstance(e.get("start"), int) and 0 < e["start"] < 1440 and re.search(r"\d", e["time"]):
            start += "T%02d:%02d:00+09:00" % divmod(e["start"], 60)
        ev = {"@context": "https://schema.org", "@type": "Event", "name": e["t"], "startDate": start, "endDate": days[-1].isoformat(),
              "eventStatus": "https://schema.org/EventCancelled" if e.get("cancelled") else "https://schema.org/EventScheduled",
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "location": {"@type": "Place", "name": vname, "address": addr, **({"geo": geo} if geo else {})},
              "description": e["sum"], "image": [SITE + "img/ogp.jpg"], "url": url, "isAccessibleForFree": e["price"] == "free", "inLanguage": "ja"}
        # 料金（offers）：無料は0円、有料は料金の欄にある「○円」のいちばん安い金額。分からないものは入れない
        yen = [int(x.replace(",", "")) for x in re.findall(r"(\d[\d,]*)\s*円", e.get("priceText", ""))]
        if e["price"] == "free" or yen:
            ev["offers"] = {"@type": "Offer", "price": 0 if e["price"] == "free" else min(yen), "priceCurrency": "JPY", "url": e.get("resvUrl") or e.get("url") or url,
                            "availability": "https://schema.org/InStock"}
        ld.append(ev)
    elif e["kind"] == "ongoing":
        # 通年の施設・遊び場・公園：Event ではなく場所として出す（公園は Park）
        typ = "Park" if re.search(r"公園|広場|ふるさと村", e["t"]) and e.get("place", "").startswith("屋外") else "TouristAttraction"
        pl = {"@context": "https://schema.org", "@type": typ, "name": e["t"], "description": e["sum"], "url": url, "image": [SITE + "img/ogp.jpg"],
              "address": addr, **({"geo": geo} if geo else {}),
              "isAccessibleForFree": e["price"] == "free", "publicAccess": True, "touristType": "子ども連れの家族", "inLanguage": "ja"}
        ld.append(pl)
    og = f"og/{e['id']}.jpg"
    for x in ld:
        if "image" in x: x["image"] = [SITE + og]
    return path, page(title, desc, path, body, ld, track_url=track_url, tpage=path, og=og,
                      og_alt=f"{e['t']}（{og_when(e)}・{ward1 or '横浜市'}）"), e["t"]


def spot_page(b, area, d, spot_ids, track_url):
    sid = spot_ids[b["n"]]
    path = f"spot/{sid}/"
    has = [n for n, v in (("おむつ替え", b.get("d")), ("授乳室", b.get("f")), ("調乳のお湯", b.get("w")), ("離乳食のレンジ", b.get("mw"))) if v is True]
    # 検索する人は「何階？」を知りたいので、場所（○F・○階）が分かる施設は題名でそれを伝える
    floor = re.search(r"\d\s*[FＦ階]", b.get("where") or "")
    extra = "・電子レンジ" if b.get("mw") else ""
    title = f"{short(b['n'])}の授乳室は何階？おむつ替え・お湯{extra}｜KidsTrip" if floor else f"{short(b['n'])}の授乳室・おむつ替え・お湯{extra}｜KidsTrip"
    ar = d['areas'].get(area, '')
    ar = "" if not ar or ar == short(b['n']) else f"（{ar}）"
    # 検索結果で答え（どこにあるか）が先に見えるように、場所を先に書く
    desc = (f"{short(b['n'])}{ar}の授乳室・おむつ替えの場所：{b['where']}。" if b.get("where") else f"{short(b['n'])}{ar}の赤ちゃん設備。") + ("・".join(has) + "あり。" if has else "")
    desc = desc[:150]
    ch, cld = crumbs([("トップ", "/"), ("授乳室・おむつ替えのある施設", "/spot/"), (short(b["n"]), "")])
    se = d.get("_ev_of_spot", {}).get(b["n"])
    same_ev = (f'<p class="tip">🎟 {E(short(b["n"]))}の料金・開いている時間・遊び方・行き方は、<a href="/event/{se["id"]}/">{E(se["t"])}のページ</a>にまとめています。</p>') if se else ""
    evs = [x for x in d["events"] if x.get("area") == area][:10]
    sx = d["extra"]["sp"].get(b["n"], {})
    pp = sx.get("papa")
    papa_html = f'<h2>パパも使える？</h2><p><b>{E(pp["label"])}</b>　{E(pp["t"])}</p>' if pp and pp.get("label") else ""
    ev_by_id = {x["id"]: x for x in d["events"]}
    geo_ev = [ev_by_id[x["id"]] for x in sx.get("events", []) if x["id"] in ev_by_id and ev_by_id[x["id"]] not in evs]
    near_ev_html = ('<h2>歩いて15分くらいで行けるイベント・遊び場</h2><ul class="links">' + "".join(
        f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(when_text(x)[:30])}）</li>' for x in geo_ev[:8]) + "</ul>") if geo_ev else ""
    near = [x for x in d["baby"].get(area, []) if x["n"] != b["n"]]
    ex = "".join(f"<li>{E(x)}</li>" for x in b.get("ex") or [])
    ad = sx.get("addr")
    from urllib.parse import quote
    if sx.get("geoSrc") == "official":
        map_url = f"https://www.google.com/maps/search/?api=1&query={sx['geo'][0]},{sx['geo'][1]}"
    else:  # 座標が確かめられていないときは名前（＋公式の住所）で探す
        map_url = "https://www.google.com/maps/search/?api=1&query=" + quote(short(b["n"]) + (f" 横浜市{ad['ward']}{ad['st']}" if ad else " 横浜"))
    addr_row = (f'<tr><th>住所</th><td>{("〒" + E(ad["zip"]) + " ") if ad.get("zip") else ""}神奈川県横浜市{E(ad["ward"])}{E(ad["st"])}{("（" + E(ad["sub"]) + "）") if ad.get("sub") else ""}'
                f'<div class="small">（<a href="{E(ad["src"])}" target="_blank" rel="noopener">公式ページ</a>{("・" + E(ad["via"])) if ad.get("via") else ""}・{E(ad["checked"])}確認）</div></td></tr>') if ad else ""
    body = f"""{ch}
<article class="card">
<h1>{E(b['n'])}の授乳室・おむつ替え・お湯</h1>
<table class="bm"><thead><tr><th>場所</th><th>おむつ替え</th><th>授乳室</th><th>お湯</th><th>レンジ</th></tr></thead><tbody><tr><th>{E(short(b['n']))}</th>{mark(b.get('d'))}{mark(b.get('f'))}{mark(b.get('w'))}{mark(b.get('mw'))}</tr></tbody></table>
<p class="legend">○ あり　× なし　？ 調べた範囲で確認できず</p>
<table class="info"><tr><th>場所</th><td>{E(b.get('where'))}</td></tr><tr><th>エリア</th><td>{E(d['areas'].get(area, ''))}</td></tr>{addr_row}{('<tr><th>電子レンジ</th><td>' + E(b.get('mwText')) + '</td></tr>') if b.get('mwText') else ''}</table>
{f'<ul class="chips">{ex}</ul>' if ex else ''}
<p class="sum">{E(b.get('note'))}</p>
<p class="small">出典：{E(b.get('src'))}</p>
<div class="btns"><a class="btn main" data-act="official" href="{E(b.get('url'))}" target="_blank" rel="noopener">公式ページで確認</a>
<a class="btn" href="{E(map_url)}" target="_blank" rel="noopener">地図で見る</a>
<button type="button" class="btn" data-share="1">🔗 リンクを送る・コピー</button></div>
</article>
{same_ev}
{papa_html}
{food_list(sx.get("food", []), sx.get("courts", []))}
{clothes_list(sx.get("clothes", []))}
{('<h2>同じエリアのほかの赤ちゃん設備</h2>' + matrix(near, spot_ids)) if near else ''}
{near_ev_html}
{('<h2>このあたりのイベント</h2><ul class="links">' + ''.join(f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(when_text(x)[:30])}）</li>' for x in evs) + '</ul>') if evs else ''}
"""
    feats = [{"@type": "LocationFeatureSpecification", "name": n, "value": v} for n, v in (("おむつ替え", b.get("d")), ("授乳室", b.get("f")), ("調乳のお湯", b.get("w")), ("離乳食用の電子レンジ", b.get("mw"))) if isinstance(v, bool)]
    og = f"og/spot-{sid}.jpg"
    place = {"@context": "https://schema.org", "@type": spot_type(b["n"]), "name": short(b["n"]), "description": desc, "url": SITE + path, "image": [SITE + og],
             "address": {"@type": "PostalAddress", **({"streetAddress": ad["st"]} if ad else {}), "addressLocality": "横浜市" + (ad["ward"] if ad else ""),
                         "addressRegion": "神奈川県", **({"postalCode": ad["zip"]} if ad and ad.get("zip") else {}), "addressCountry": "JP"},
             "amenityFeature": feats, "publicAccess": True}
    if b.get("url"): place["sameAs"] = b["url"]
    # 借りた座標（会場の名前のパターンから）は構造化データに出さない。地図リンクに座標を使うのは公式で確かめたものだけ
    if sx.get("geo") and sx.get("geoSrc") != "borrowed": place["geo"] = {"@type": "GeoCoordinates", "latitude": sx["geo"][0], "longitude": sx["geo"][1]}
    place["hasMap"] = map_url
    return path, page(title, desc, path, body, [cld, place], track_url=track_url, tpage=path, og=og,
                      og_alt=f"{short(b['n'])}の赤ちゃん設備（おむつ替え・授乳室・お湯）"), b["n"]


# 施設ページの構造化データの型（名前から。合わないものは Place のまま）。上から順に見る
SPOT_TYPES = [
    (r"セブン-イレブン|ローソン|デイリーヤマザキ|ファミリーマート", "ConvenienceStore"),
    (r"ホテル|宿|海員会館", "Hotel"), (r"映画館|シネマ", "MovieTheater"), (r"カラオケ|万葉倶楽部", "EntertainmentBusiness"),
    (r"薬局|クリエイトエス・ディー", "Pharmacy"), (r"クリニック", "MedicalClinic"), (r"デンタル|歯科", "Dentist"), (r"一時預かり", "ChildCare"),
    (r"美容室|美容院|ヘアサロン|理容", "HairSalon"), (r"ネイル", "NailSalon"),
    (r"POLA|ノエビア|整体|鍼灸|治療院|アロマ|Luce", "HealthAndBeautyBusiness"),
    (r"チャイナドレス", "Store"),
    (r"子育て支援拠点|とことこ|地区センター|コミュニティハウス|ケアプラザ|あーすぷらざ|防災センター", "CivicStructure"),
    (r"ベビーケアスペース", "TrainStation"), (r"YCAT|エア・ターミナル", "BusStation"), (r"客船ターミナル", "BoatTerminal"),
    (r"動物園|ズーラシア", "Zoo"), (r"シーパラダイス|アクアリウム|水族館", "Aquarium"), (r"図書館", "Library"),
    (r"象の鼻テラス|中華街|大世界|マリンタワー|レストラン船|キリンビール|ストロベリーパーク|フォレストアドベンチャー|ウォーターパーク", "TouristAttraction"),
    (r"コスモワールド", "AmusementPark"),
    (r"外交官の家|イギリス館|番館|エリスマン邸|開港記念会館|大倉山記念館", "LandmarksOrHistoricalBuildings"), (r"總持寺", "BuddhistTemple"),
    (r"博物館|美術館|資料館|記念館|資料室|ミュージアム|文学館|科学館|保存館|技術館|文化館|ギャラリー|ニュースパーク|プラネタリア|博覧館|人形の家|文庫|氷川丸|日本丸|ライブラリー|Mulabo|Beauty Park", "Museum"),
    (r"公園|三溪園|こどもの国", "Park"),
    (r"スタジアム|アリーナ|球技場", "StadiumOrArena"), (r"プール|武道館|スポーツセンター", "SportsActivityLocation"),
    (r"能楽堂|にぎわい座|ホール", "PerformingArtsTheater"), (r"パシフィコ", "EventVenue"),
    (r"区役所|市役所|県庁|赤十字", "GovernmentBuilding"),
    (r"百貨店|高島屋|そごう", "DepartmentStore"),
    (r"モール|ららぽーと|ワールドポーターズ|クイーンズスクエア|ランドマークプラザ|MARK IS|ルミネ|ジョイナス|モアーズ|ポルタ|シァル|CIAL|トレッサ|アウトレット|東急スクエア|ニュウマン|コレットマーレ|ベイクォーター|ソラトス|ミオカ|みなも|TOKYU S\.C|カエデウォーク|テラス|ビブレ|スカイビル|アソビル|BASEGATE|モディ|サクラス|トツカーナ|アベニュー|LICOPA|イオン|アピタ|S\.C\.|MARINE & WALK|赤レンガ倉庫|ハンマーヘッド|HOME'S|キュービックプラザ|プリンスペペ|港南台バース|ブランチ|ショッピングストリート|元町スカイビル", "ShoppingCenter"),
    (r"スーパー|パルケ", "GroceryStore"), (r"ドン・キホーテ|ヨドバシ|ノジマ|CeeU|眼鏡|文具|履物|自然食品|さゆり堂|杉本家|タッチまいはぁと|チャイナドレス", "Store"),
]


def spot_type(n):
    for rx, t in SPOT_TYPES:
        if re.search(rx, n):
            return t
    return "Place"


MIN_CHARS = 400  # 本文（タグ・スクリプトを除いた文字数）がこれより少ないページは noindex・sitemapから外す


def body_chars(htmltext):
    s = re.sub(r"(?s)<(script|style|head)[^>]*>.*?</\1>", "", htmltext)
    s = re.sub(r"(?s)<footer.*?</footer>", "", s)
    return len(re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", s))))


def _norm(x):
    return re.sub(r"[\s　（）()「」『』・〜~\-—:：、。,.!！?？'\"]", "", x or "").lower()


def en_links(d, spots, spot_ids):
    p = os.path.join(ROOT, "en", "index.html")
    if not os.path.exists(p):
        return
    src = open(p, encoding="utf-8").read()
    jas = []
    ev0 = src.find("const EVENTS")
    ev1 = src.find("];", ev0) if ev0 >= 0 else -1
    for m in re.finditer(r'\bn:\s*"((?:[^"\\]|\\.)*)",\s*ja:\s*"((?:[^"\\]|\\.)*)"(?:,\s*a:\s*"(\w+)")?', src):
        is_ev = ev0 <= m.start() <= ev1
        jas.append((m.group(1).replace('\\"', '"'), m.group(2), "event" if is_ev else "spot", "events" if is_ev else (m.group(3) or "other")))
    for m in re.finditer(r'"a": "(\w+)", "n": "((?:[^"\\]|\\.)*)", "ja": "((?:[^"\\]|\\.)*)"', src):
        jas.append((m.group(2).replace('\\"', '"'), m.group(3), "spot", m.group(1)))
    ev_keys = [(_norm(re.split(r"[（(]", e["t"])[0]), _norm(e["t"]), "event", e["id"], e["t"]) for e in d["events"]]
    sp_keys = [(_norm(re.split(r"[（(]", n)[0]), _norm(n), "spot", spot_ids[n], short(n)) for n in spots]
    found, seen = [], set()
    for en, ja, prefer, area in jas:
        j = _norm(ja)
        if len(j) < 3:
            continue
        best = None
        for core, full, kind, pid, name in sp_keys + ev_keys:
            if len(core) < 3:
                continue
            # かっこの中だけに名前が出てくるもの（例：「キッズガーデン（ヨルノヨ × …）」）には結びつけない
            if j == core or j == full or (len(j) >= 4 and (j in core or core in j)):
                score = (0 if kind == prefer else 1, abs(len(core) - len(j)))
                if best is None or score < best[0]:
                    best = (score, kind, pid, name)
        if best and (best[1], best[2]) not in seen:
            seen.add((best[1], best[2]))
            found.append((en, best[1], best[2], best[3], area))
    # 同じ場所が「案内ページ（/event/）」と「授乳室・おむつのページ（/spot/）」の両方に出るときは、/spot/ の方に印を付けて区別する
    def base(x): return re.split(r"\s+(?:&|—|-|\()", x)[0].strip().lower()
    ev_bases = {base(f[0]) for f in found if f[1] == "event"}
    AREA_ORDER = [("mm", "Minato Mirai & Yokohama Station"), ("kannai", "Chinatown, Yamashita & Kannai"), ("north", "North Yokohama (Shin-Yokohama)"),
                  ("zoo", "Zoos & aquariums"), ("park", "Big parks & suburbs"), ("south", "Big parks & suburbs"), ("other", "Big parks & suburbs"), ("events", "Seasonal events")]
    groups = {}
    for en, k, pid, name, area in found:
        label = dict(AREA_ORDER).get(area, "Big parks & suburbs")
        extra = ' <span class="ja">· nursing rooms &amp; diapers</span>' if k == "spot" and base(en) in ev_bases else ""
        groups.setdefault(label, []).append(f'<li><a href="/{k}/{pid}/" hreflang="ja">{E(en)}</a> <span class="jp">JP</span>{extra} <span class="ja" lang="ja">{E(name)}</span></li>')
    order = []
    for _, lab in AREA_ORDER:
        if lab not in order: order.append(lab)
    items = "".join(f'<details class="jagrp"><summary>{E(lab)} ({len(groups[lab])})</summary><ul class="jalinks">{"".join(groups[lab])}</ul></details>' for lab in order if lab in groups)
    block = ('<!--JA:START--><section id="ja-pages"><details class="fold"><summary><h2 class="fsum">More details (in Japanese)'
             f'<span class="sub">{len(found)} pages by area — tap to open</span></h2></summary>'
             '<p>Each page below (marked <span class="jp">JP</span>) is in Japanese, with the official link, access, nearby family restaurants, and nursing rooms / diaper changing within walking distance. Use your browser\'s translate feature.</p>'
             f'{items}</details></section><!--JA:END-->')
    if "<!--JA:START-->" in src:
        src = re.sub(r"(?s)<!--JA:START-->.*?<!--JA:END-->", lambda _: block, src)
    else:
        src = src.replace('  <section id="baby">', block + '\n  <section id="baby">', 1)
    open(p, "w", encoding="utf-8").write(src)


ENDED_DIR = os.path.join(ROOT, "tools", "ended")


def save_ended_body(kind, pid):
    """一覧から外れた日に、それまでのページの本文（カード）を tools/ended/ に残す（掲載終了ページで「開催時の情報」として見せる）"""
    out = os.path.join(ENDED_DIR, f"{pid}.html")
    src = os.path.join(ROOT, kind, pid, "index.html")
    if os.path.exists(out) or not os.path.exists(src):
        return
    s = open(src, encoding="utf-8").read()
    if "掲載終了" in s:
        return
    m = re.search(r'(?s)<article class="card">.*?</article>', s)
    if m:
        os.makedirs(ENDED_DIR, exist_ok=True)
        open(out, "w", encoding="utf-8").write(m.group(0))


def ended_page(kind, pid, name, d=None):
    path = f"{kind}/{pid}/"
    what = "イベント" if kind == "event" else "施設の情報"
    saved = ""
    fp = os.path.join(ENDED_DIR, f"{pid}.html")
    if os.path.exists(fp):
        saved = open(fp, encoding="utf-8").read()
    ward = ""
    past = ""
    if saved:
        mw = re.search(r"<th>場所</th><td>([^<・]+区)", saved)
        ward = mw.group(1) if mw else ""
        md = re.search(r"<th>日にち</th><td>([^<]*)</td>", saved)
        last = md.group(1) if md else ""
        # 開催時のカードから、共有ボタンや一覧へのリンクを外し、公式ページへのボタンだけ残す
        card = re.sub(r'(?s)^<article class="card">', "", saved)
        card = re.sub(r'(?s)</article>$', "", card)
        card = re.sub(r"(?s)<h1>.*?</h1>", "", card)
        card = re.sub(r'<a class="btn"[^>]*href="/\?e=[^"]*"[^>]*>.*?</a>', "", card)
        card = re.sub(r'(?s)<button[^>]*data-share[^>]*>.*?</button>', "", card)
        card = re.sub(r'(?s)<a class="btn line"[^>]*>.*?</a>', "", card)
        card = card.replace("公式ページで確認", "公式ページ（次の開催のお知らせもここで）")
        past = f'<h2>開催していたときの情報</h2><p class="small">ここから下は、掲載していたときの内容です（{E(last)}）。次の開催の日にちや料金は変わることがあるので、公式ページで確かめてください。</p>{card}'
    rel = ""
    if d is not None and kind == "event":
        evs = d["events"]
        same = [e for e in evs if ward and e.get("ward") == ward and e.get("kind") == "limited"][:8]
        play = [e for e in evs if ward and e.get("ward") == ward and e.get("kind") == "ongoing" and e.get("price") == "free" and (e.get("freeplay") or e.get("animal") or e.get("ride"))][:6]
        if not same:
            same = [e for e in evs if e.get("kind") == "limited"][:8]
        lab = f"{ward}で" if ward and any(e.get("ward") == ward for e in same) else "横浜で"
        rel += f'<h2>{E(lab)}これから開かれる親子イベント</h2><ul class="links">' + "".join(
            f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a>（{E(e.get("ward", ""))}）</li>' for e in same) + "</ul>"
        if play:
            rel += f'<h2>{E(ward)}の無料で遊べる場所</h2><ul class="links">' + "".join(
                f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a></li>' for e in play) + "</ul>"
    body = f"""<p class="crumb"><a href="/">トップ</a> ＞ <a href="/">イベント</a> ＞ {E(name)}（掲載終了）</p>
<article class="card"><p class="ended">この{what}は終わりました。いまは一覧に出していません</p><h1>{E(name)}</h1>
<p>開催が終わったか、情報を確かめられなくなったため、一覧から外しました。同じ{E(ward) if ward else "地域"}でこれから開かれるイベントや、無料で遊べる場所を下にまとめています。</p>
<div class="btns"><a class="btn main" href="/">いまのイベントを見る</a><a class="btn" href="/#foodall">ごはん・おむつを見る</a></div></article>
{rel}{past}"""
    og = f"og/{pid}.jpg" if kind == "event" and os.path.exists(os.path.join(ROOT, "og", f"{pid}.jpg")) else None
    return path, page(f"{name}（掲載終了）｜KidsTrip", f"{name}の掲載は終わりました。開催していたときの情報と、{ward or '横浜'}でこれから開かれる親子イベントをまとめています。", path, body, [], noindex=True, og=og)


ABOUT_BODY = """<p class="crumb"><a href="/">トップ</a> ＞ このサイトについて</p>
<article class="card">
<h1>このサイトについて</h1>
<p>KidsTrip（キッズトリップ）は、横浜で子どもと出かける家族のための、イベントとおでかけ情報の一覧です。週末・祝日を中心に、0歳から小学生くらいまでの親子が楽しめる催しと、近くのおむつ替え・授乳室・調乳のお湯、子連れで入りやすいごはんをまとめています。毎日情報を見直しています。</p>
<h2>情報の集め方</h2>
<ul>
<li>出典にするのは、①施設・お店・主催者の公式、②横浜市・区・神奈川県などの行政、③新聞・地域ニュース、④実際に行った人から直接聞いた情報（「利用者の情報」と書きます）です。</li>
<li>まとめサイトやブログ、SNSは見つけるきっかけにだけ使い、公式で確かめてから載せます。確かめられないものは載せません。</li>
<li>料金・時間・予約が分からないときは、推測で書かずに「公式ページに記載なし」とします。情報が食い違うときは「情報が分かれています」と書きます。</li>
<li>グルメサイトなどの機械的な収集はしていません。</li>
</ul>
<h2>内容について</h2>
<p>各ページの文章は、元のページをもとにこのサイトが短くまとめたものです。必ず元のページへのリンクを付けています。内容は予告なく変わったり、中止になったりすることがあります。出かける前に、必ず公式ページで最新の情報を確かめてください。免責については<a href="/privacy/">プライバシーポリシー</a>の「5. 免責」をご覧ください。</p>
<h2>運営者</h2>
<p>KidsTrip は個人で運営しています（会社や団体ではありません）。ご連絡はお問い合わせフォームか、メール（<a href="mailto:info@kidstrip.jp">info@kidstrip.jp</a>）でお願いします。</p>
<h2>文章と画像の扱い</h2>
<p>他のサイトの文章を長く写したり、写真を転載したりはしていません。このサイトの文章・イラストを使いたいときは、お問い合わせからご連絡ください。</p>
<h2>投稿の扱い</h2>
<p>いまは、このサイトで投稿を受け付けていません。設備の情報の追加・訂正は、お問い合わせフォームからお送りください。いただいた情報は、確かめたうえで「利用者の情報（○年○月）」として載せることがあります。送ってくださった方の名前などは載せません。事実と違うもの、ほかの人の権利を傷つけるもの、宣伝だけのものは載せません。</p>
<h2>使われ方の記録</h2>
<p>サイトをよくするため、表示されたページ、検索した言葉、押されたボタン・リンク、端末とブラウザの種類（スマホ・PCなど。機械による自動アクセスを分けるため）、どのサイトから来たか、日本からのアクセスかどうか（時間帯の設定から判定）を記録しています。名前・メールアドレス・正確な位置などの個人情報は記録しません。Cookieは使わず、同じ人の訪問をまとめて数えるために、ランダムな番号だけをブラウザに保存しています。「近くで探す」の現在地は、画面の中で距離を計算するためだけに使い、記録するのは「横浜市のあたり」などの大まかな区分だけです。広告とCookieの扱いを含め、くわしくは<a href="/privacy/">プライバシーポリシー</a>をご覧ください。</p>
<h2>お問い合わせ・掲載のご相談</h2>
<p>イベント情報の追加・訂正、掲載や協賛のご相談、サイトへのご質問は、お問い合わせフォーム（Googleアカウントでのログインが必要です）か、メール（<a href="mailto:info@kidstrip.jp">info@kidstrip.jp</a>）でどうぞ。</p>
<div class="btns"><a class="btn main" href="FORM_URL" target="_blank" rel="noopener">お問い合わせフォーム</a><a class="btn" href="/">イベント一覧へ</a><a class="btn" href="/en/">English</a></div>
</article>"""


PRIVACY_BODY = """<p class="crumb"><a href="/">トップ</a> ＞ プライバシーポリシー</p>
<article class="card">
<h1>プライバシーポリシー</h1>
<p>KidsTrip（キッズトリップ、以下「このサイト」）は、利用する方の情報を次のとおり扱います。</p>
<h2>1. 集める情報と使い道</h2>
<p>サイトをよくするために、次の情報を記録しています。名前・メールアドレス・電話番号・正確な位置など、個人を特定できる情報は記録しません。</p>
<ul>
<li>表示されたページ、検索した言葉、使った絞り込み、押されたボタン・リンク</li>
<li>端末の種類（スマホ・PCなど）と、ブラウザの種類（ユーザーエージェント。機械による自動アクセスと人のアクセスを分けるため）</li>
<li>どのサイトから来たか（参照元のドメイン）</li>
<li>端末の言語と時間帯の設定（日本からのアクセスかどうかのめやす）</li>
<li>「近くで探す」「出発駅」で選んだ駅、または「横浜市のあたり」などの大まかな区分（現在地の座標は送りません）</li>
</ul>
<p>記録は運営者のGoogleスプレッドシートにため、どのページや機能がよく使われているかを調べて、掲載内容や使いやすさを直すためだけに使います。法令にもとづく場合を除き、第三者に渡しません。</p>
<h2>2. ブラウザに保存する情報</h2>
<p>このサイトは、次の情報を利用する方のブラウザの中（ローカルストレージ）に保存します。運営者のサーバーには送られません（1の記録で使う番号を除く）。ブラウザの設定から、いつでも消せます。</p>
<ul>
<li>同じ人の訪問をまとめて数えるための、ランダムな番号</li>
<li>お気に入り（☆）に入れたイベント</li>
<li>前回の検索・絞り込みの条件（60日で消えます）</li>
</ul>
<h2>3. 広告について</h2>
<p>このサイトでは、第三者配信の広告サービス（Google アドセンスなど）を利用することがあります。広告配信事業者は、利用する方の興味に合わせた広告を表示するため、Cookie（クッキー）を使うことがあります。Cookieを使うことで、このサイトや他のサイトへの過去のアクセス情報にもとづいた広告が表示されます。Cookieには、名前・住所・メールアドレス・電話番号は含まれません。</p>
<ul>
<li>Google がCookieを使って広告を配信するしくみ：<a href="https://policies.google.com/technologies/ads?hl=ja" target="_blank" rel="noopener">広告 – ポリシーと規約 – Google</a></li>
<li>パーソナライズ広告は、<a href="https://adssettings.google.com/" target="_blank" rel="noopener">Google の広告設定</a>で無効にできます。また、<a href="https://www.aboutads.info/" target="_blank" rel="noopener">www.aboutads.info</a> で、第三者配信事業者のCookieを無効にできます。</li>
</ul>
<h2>4. 外部のサービスとリンク</h2>
<p>お問い合わせにはGoogleフォームを、地図・経路にはGoogleマップへのリンクを使っています。これらのサービスでの情報の扱いは、各サービスの方針に従います。このサイトから移動した先のサイトの内容や情報の扱いについて、このサイトは責任を負いません。</p>
<h2>5. 免責</h2>
<p>このサイトの情報は、施設・主催者の公式情報などをもとに、できるだけ正確になるよう確かめて載せていますが、正確さ・新しさを保証するものではありません。出かける前に、必ず公式ページで最新の情報を確かめてください。このサイトの情報を使って生じた損害について、運営者は責任を負いかねます。</p>
<h2>6. 著作権</h2>
<p>このサイトの文章・イラストの著作権は運営者にあります。引用の範囲をこえて使いたいときは、お問い合わせからご連絡ください。</p>
<h2>7. このポリシーの変更</h2>
<p>このポリシーは、必要に応じて予告なく変えることがあります。変えたときは、このページでお知らせします。</p>
<h2>8. お問い合わせ</h2>
<p>このポリシーについてのお問い合わせは、お問い合わせフォームか、メール（<a href="mailto:info@kidstrip.jp">info@kidstrip.jp</a>）でどうぞ。</p>
<p class="small">制定日：2026年11月16日</p>
<div class="btns"><a class="btn main" href="FORM_URL" target="_blank" rel="noopener">お問い合わせフォーム</a><a class="btn" href="/about/">このサイトについて</a><a class="btn" href="/">イベント一覧へ</a></div>
</article>"""


def privacy_page(track_url, form_url):
    path = "privacy/"
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "プライバシーポリシー｜KidsTrip", "url": SITE + path, "inLanguage": "ja",
          "publisher": {"@type": "Organization", "name": "KidsTrip", "url": SITE, "logo": SITE + "img/logo.webp"}}
    return path, page("プライバシーポリシー｜KidsTrip（キッズトリップ）", "KidsTrip（キッズトリップ）のプライバシーポリシー。集める情報と使い道、ブラウザに保存する情報、広告（Cookie）、外部サービス、免責について。",
                      path, PRIVACY_BODY.replace("FORM_URL", E(form_url)), [ld], track_url=track_url, tpage=path)


def about_page(track_url, form_url):
    path = "about/"
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": "KidsTrip について", "url": SITE + path, "inLanguage": "ja",
          "publisher": {"@type": "Organization", "name": "KidsTrip", "url": SITE, "logo": SITE + "img/logo.webp"}}
    return path, page("このサイトについて｜KidsTrip（キッズトリップ）", "KidsTrip（キッズトリップ）の運営方針。情報の集め方と出典、内容の扱い、使われ方の記録、お問い合わせについて。",
                      path, ABOUT_BODY.replace("FORM_URL", E(form_url)), [ld], track_url=track_url, tpage=path)

# ---- 学童・放課後（tools/gakudo.json から gakudo/ と gakudo/区/ のページを作る）----
GAKUDO_JSON = os.path.join(ROOT, "tools", "gakudo.json")
WARD_SLUG = {"鶴見区":"tsurumi","神奈川区":"kanagawa","西区":"nishi","中区":"naka","南区":"minami","港南区":"konan","保土ケ谷区":"hodogaya","旭区":"asahi","磯子区":"isogo","金沢区":"kanazawa","港北区":"kohoku","緑区":"midori","青葉区":"aoba","都筑区":"tsuzuki","戸塚区":"totsuka","栄区":"sakae","泉区":"izumi","瀬谷区":"seya"}
GTYPE = {"kids": "放課後キッズクラブ（小学校の中）", "club": "放課後児童クラブ（学童保育・学校の外）", "hamakko": "はまっ子ふれあいスクール（特別支援学校）"}
GAKUDO_SRC = "https://www.city.yokohama.lg.jp/kosodate-kyoiku/hokago/hokagokids/houkago-kids.html"
GAKUDO_FEES = f"""<h2>キッズクラブと学童のちがい</h2>
<table class="bm gkcmp"><thead><tr><th></th><th>放課後キッズクラブ</th><th>放課後児童クラブ（学童保育）</th></tr></thead><tbody>
<tr><th scope="row">場所</th><td>通っている小学校の中（市立小学校すべてにある）</td><td>学校の外（一軒家・マンションの一室など）</td></tr>
<tr><th scope="row">使える子</th><td>その小学校に通う1〜6年生ならだれでも（16時までの「わくわく」）。17時・19時までの「すくすく」は、仕事などで放課後に家に大人がいない家庭の子だけ</td><td>仕事などで放課後に家に大人がいない家庭の子だけ</td></tr>
<tr><th scope="row">学区</th><td>その小学校の子だけ（学区に住んで私立に通う子も）</td><td>決まりなし（どの学校からでも通える）</td></tr>
<tr><th scope="row">時間</th><td>市内どこでも同じ。平日は放課後〜19時まで</td><td>クラブごとに違う。20時・21時まで開いているところも</td></tr>
<tr><th scope="row">料金</th><td>市内どこでも同じ。無料・月2,000円・月5,000円の3つ</td><td>クラブごとに違う（キッズより高めのことが多い）</td></tr>
<tr><th scope="row">運営</th><td>市が選んだ法人（会社・NPOなど）</td><td>保護者会（運営委員会）・NPO・会社など。保護者がお手伝いするクラブもある</td></tr>
<tr><th scope="row">雰囲気</th><td>学校の中なので移動がなく安心。大勢で遊ぶ</td><td>少人数で家庭的なところが多い。送迎・お弁当があるクラブも</td></tr>
<tr><th scope="row">申し込み</th><td colspan="2">どちらも区役所ではなく、各クラブへ直接</td></tr>
</tbody></table>
<p class="small">ざっくり言うと、キッズクラブは「学校の中の、みんなが使える放課後の場所」、学童は「学校の外の、働く家庭のための第二の家」です。出典：<a href="https://www.city.yokohama.lg.jp/kosodate-kyoiku/hokago/hokagokenzen/houkago.html" target="_blank" rel="noopener">横浜市「初めての人へ（放課後の居場所の概要）」</a>・<a href="https://www.city.yokohama.lg.jp/kosodate-kyoiku/hokago/hokagokids/houkago-kids.html" target="_blank" rel="noopener">横浜市「放課後キッズクラブ」</a></p>
<h2>放課後キッズクラブの区分と料金（市内共通）</h2>
<table class="bm"><thead><tr><th>区分</th><th>使える人</th><th>時間</th><th>料金（月）</th></tr></thead><tbody>
<tr><th scope="row">わくわく（区分1）</th><td>その小学校に通う1〜6年生ならだれでも</td><td>平日 放課後〜16時（土曜なし・学校が休みの日は2時間ほど）</td><td>無料</td></tr>
<tr><th scope="row">すくすく ゆうやけ（区分2A）</th><td>仕事などで放課後に家に大人がいない家庭の子</td><td>平日 放課後〜17時／土曜 8時30分〜17時／休みの日 8時〜17時</td><td>2,000円（7・8月は2,500円）</td></tr>
<tr><th scope="row">すくすく ほしぞら（区分2B）</th><td>同上</td><td>平日 放課後〜19時／土曜 8時30分〜19時／休みの日 8時〜19時</td><td>5,000円（7・8月は5,500円）</td></tr>
</tbody></table>
<p class="small">ほかに、おやつ代（実費ほど）と保険料（年800円以下）がかかります。就学援助・市民税所得割の非課税・生活保護の世帯は、ゆうやけが無料、ほしぞらが2,500円（7・8月は3,000円）になります。わくわくの子が用事でたまに遅くなる日は、すくすくに空きがあれば「スポット利用」（1回800円＋おやつ代、19時まで）ができます。日曜・祝日・年末年始（12/29〜1/3）は休みです。すくすくに申し込むときは就労証明書などが要ります。申し込みは区役所ではなく、各クラブへ直接。出典：<a href="{GAKUDO_SRC}" target="_blank" rel="noopener">横浜市「放課後キッズクラブ」</a></p>
<h2>放課後児童クラブ（学童保育）とは</h2>
<p>一軒家やマンションの一室など学校の外にあり、保護者会・NPO・会社などが運営しています。仕事などで放課後に家に大人がいない家庭の小学生が対象で、学区の決まりはありません。時間・料金・送迎・お弁当などはクラブごとに違うので、各クラブに問い合わせてください（多くのクラブは平日の午後に電話がつながります）。</p>"""


def gakudo_card(r):
    from urllib.parse import quote
    where = r["addr"] or (r["schools"] + ("" if r["schools"].endswith(("学園", "学校")) else "小学校") + "の中" if r["schools"] else "")
    mq = quote(f'横浜市{r["ward"]}{r["addr"]}' if r["addr"] else f'横浜市{r["ward"]} {r["name"].split("放課後")[0]}')
    tel = r["tel"]
    bits = [f'<li><h3>{E(r["name"])}</h3><div class="small">{E(GTYPE[r["type"]])}</div>']
    if where: bits.append(f'<div>📍 {E(where)}　<a href="https://www.google.com/maps/search/?api=1&amp;query={mq}" target="_blank" rel="noopener">地図</a></div>')
    if tel: bits.append(f'<div>☎ <a href="tel:{E(tel)}">{E(tel)}</a></div>')
    if r["hours"]: bits.append(f'<div>🕘 {E(r["hours"])}</div>')
    if r["schools"] and r["type"] == "club": bits.append(f'<div>🏫 主な小学校：{E(r["schools"])}</div>')
    if r["operator"]: bits.append(f'<div>運営：{E(r["operator"])}</div>')
    if r.get("note"): bits.append(f'<div>📝 {E(r["note"])}</div>')
    bits.append(f'<div class="small">出典：<a href="{E(r["src"])}" target="_blank" rel="noopener">横浜市{E(r["ward"])}の案内</a>（{E(r["asof"])}）</div></li>')
    return "".join(bits)


def gakudo_pages(track_url):
    if not os.path.exists(GAKUDO_JSON):
        return []
    rows = json.load(open(GAKUDO_JSON, encoding="utf-8"))
    out = []
    wards = [w for w in WARD_SLUG if any(r["ward"] == w for r in rows)]
    def cnt(xs, t): return sum(1 for r in xs if r["type"] == t)
    links = "".join(f'<li><a href="/gakudo/{WARD_SLUG[w]}/">{w}</a>（キッズ{cnt(xs,"kids")}・学童{cnt(xs,"club")}）</li>' for w in wards for xs in [[r for r in rows if r["ward"] == w]])
    asof = rows[0]["asof"] if rows else ""
    body = f"""<article class="ev"><p class="crumb"><a href="/">トップ</a> ＞ 学童・放課後キッズクラブ</p>
<h1>横浜市の学童・放課後キッズクラブ一覧</h1>
<p>横浜市18区の放課後キッズクラブ（{cnt(rows,"kids")}か所）と放課後児童クラブ（学童保育・{cnt(rows,"club")}か所）を、各区役所の案内ページからまとめました。区を選ぶと、住所・電話・主な小学校が見られます。トップの「🎒 学童・放課後」では、小学校名で探したり、いくつかの質問に答えてどの区分が合いそうかの目安を見たりできます。</p>
<div class="btns"><a class="btn main" href="/#gakudo">小学校名で探す・区分の目安を見る</a></div>
<h2>区ごとの一覧</h2><ul>{links}</ul>
{GAKUDO_FEES}
<p class="small">情報の時点：{E(asof)}。空き状況・料金・時間は変わることがあるので、必ず各クラブ・区役所に確かめてください。</p></article>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "横浜市の学童・放課後キッズクラブ一覧", "url": SITE + "gakudo/", "inLanguage": "ja"}
    gitems = {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜市の区ごとの学童・放課後キッズクラブ一覧", "numberOfItems": len(wards),
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}gakudo/{WARD_SLUG[w]}/", "name": f"{w}の学童・放課後キッズクラブ一覧"} for i, w in enumerate(wards)]}
    out.append(("gakudo/", page(f"横浜市の学童・放課後キッズクラブ一覧（全{len(rows)}か所・区ごと）｜KidsTrip", f"横浜市18区の放課後キッズクラブ{cnt(rows,'kids')}か所と学童（放課後児童クラブ）{cnt(rows,'club')}か所の住所・電話・主な小学校。わくわく・ゆうやけ・ほしぞらの区分と料金も。", "gakudo/", body, [ld, crumbs([("トップ", "/"), ("学童・放課後キッズクラブ", "")])[1], gitems], track_url=track_url, tpage="gakudo/")))
    for w in wards:
        xs = [r for r in rows if r["ward"] == w]
        sec = "".join(f'<h2>{E(GTYPE[t])}（{n}）</h2><ul class="gk">' + "".join(gakudo_card(r) for r in xs if r["type"] == t) + "</ul>"
                      for t in ("kids", "club", "hamakko") for n in [cnt(xs, t)] if n)
        miss = ""
        body = f"""<article class="ev"><p class="crumb"><a href="/">トップ</a> ＞ <a href="/gakudo/">学童・放課後キッズクラブ</a> ＞ {w}</p>
<h1>{w}の学童・放課後キッズクラブ一覧</h1>
<p>{w}の放課後キッズクラブ{cnt(xs,"kids")}か所と放課後児童クラブ（学童保育）{cnt(xs,"club")}か所です。キッズクラブはその小学校に通う子（学区に住んで私立に通う子も）が使えます。学童は学区の決まりがなく、「主な小学校」はそのクラブに通っている子の多い学校です。</p>
<div class="btns"><a class="btn main" href="/#gakudo">区分の目安を見る</a><a class="btn" href="/gakudo/">ほかの区</a></div>
{sec}{miss}{GAKUDO_FEES}
<p class="small">情報の時点：{E(asof)}（{w}の案内ページから）。空き状況・料金・時間は変わることがあるので、必ず各クラブに確かめてください。</p></article>"""
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{w}の学童・放課後キッズクラブ一覧", "url": f"{SITE}gakudo/{WARD_SLUG[w]}/", "inLanguage": "ja"}
        out.append((f"gakudo/{WARD_SLUG[w]}/", page(f"{w}の学童・放課後キッズクラブ一覧（{len(xs)}か所）｜KidsTrip", f"{w}の放課後キッズクラブ{cnt(xs,'kids')}か所と学童（放課後児童クラブ）{cnt(xs,'club')}か所の住所・電話・主な小学校・開所時間。区分（わくわく・ゆうやけ・ほしぞら）と料金も。", f"gakudo/{WARD_SLUG[w]}/", body, [ld, crumbs([("トップ", "/"), ("学童・放課後キッズクラブ", "/gakudo/"), (w, "")])[1], {"@context": "https://schema.org", "@type": "ItemList", "name": f"{w}の放課後キッズクラブ・学童", "numberOfItems": len(xs), "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "ChildCare", "name": r["name"], **({"telephone": r["tel"]} if r.get("tel") else {}), "address": {"@type": "PostalAddress", **({"streetAddress": r["addr"]} if r.get("addr") else {}), "addressLocality": "横浜市" + w, "addressRegion": "神奈川県", "addressCountry": "JP"}}} for i, r in enumerate(xs)]}], track_url=track_url, tpage=f"gakudo/{WARD_SLUG[w]}/")))
    return out


def play_kind(x):
    t = x["t"]
    if "地区センター" in t: return "地区センターのプレイルーム"
    if "子育て支援拠点" in t or "つどいの広場" in t or "親子の広場" in t: return "子育て支援拠点・親子の広場"
    if "ログハウス" in t: return "こどもログハウス"
    if "プレイパーク" in t or "公園" in t or str(x.get("place", "")).startswith("屋外"): return "公園・屋外の遊び場"
    return "施設・モール・博物館など"


FAC_JSON = os.path.join(ROOT, "tools", "facilities.json")
FAC_TYPE = {"park": "公園", "library": "図書館", "community": "コミュニティハウス", "sports": "スポーツセンター", "pool": "屋内プール", "outdoor": "野外活動センター", "careplaza": "地域ケアプラザ", "pool_summer": "屋外プール（夏だけ）"}
FAC_ORDER = ["park", "library", "community", "sports", "pool", "outdoor", "careplaza", "pool_summer"]


def fac_rows():
    return json.load(open(FAC_JSON, encoding="utf-8")) if os.path.exists(FAC_JSON) else []


def fac_li(r, ev=None):
    from urllib.parse import quote
    mq = quote(f'横浜市{r["ward"]}{r["addr"]}' if r.get("addr") else f'横浜市{r["ward"]} {r["name"]}')
    bits = [f'<li><b>{E(r["name"])}</b>']
    if ev: bits.append(f'（<a href="/event/{ev["id"]}/">くわしいページ</a>）')
    if r["type"] == "park" and (r.get("kind") or r.get("area")): bits.append('<span class="small">（' + "・".join(x for x in [E(r.get("kind") or ""), f'{r["area"]:,}㎡' if r.get("area") else ""] if x) + '）</span>')
    sub = []
    if r.get("addr"): sub.append(f'📍 {E(r["addr"])} <a href="https://www.google.com/maps/search/?api=1&amp;query={mq}" target="_blank" rel="noopener">地図</a>')
    if r.get("tel"): sub.append(f'☎ <a href="tel:{E(r["tel"])}">{E(r["tel"])}</a>')
    if r.get("hours"): sub.append(f'🕘 {E(r["hours"])}')
    if r.get("closed"): sub.append(f'休み：{E(r["closed"])}')
    if r.get("kids"): sub.append(f'👶 {E(r["kids"])}')
    if r.get("note"): sub.append(f'📝 {E(r["note"])}')
    if sub: bits.append('<div class="small">' + "　".join(sub) + "</div>")
    bits.append("</li>")
    return "".join(bits)


def fac_sections(w, ong):
    """区のページに足す、市の施設の一覧（公園・図書館・コミュニティハウスなど）。tools/facilities.json から"""
    rows = [r for r in fac_rows() if r["ward"] == w]
    if not rows: return "", 0
    out, n = [], 0
    for t in FAC_ORDER:
        xs = [r for r in rows if r["type"] == t]
        if not xs: continue
        n += len(xs)
        lis = "".join(fac_li(r, next((e for e in ong if r["name"] in e["t"]), None)) for r in xs)
        note = {"park": "市の公園一覧表（令和8年3月31日現在）の大きな公園と、区役所の公園紹介ページに載っている公園。トイレ・遊具は区のページに書いてあるものだけ載せています（書いていない公園は空欄）。",
                "careplaza": "高齢の方の相談が中心の施設ですが、子育てサロンや親子の集まりを開いている館もあります。各館に確かめてください。",
                "community": "小・中学校の中などにある、図書コーナーや研修室のある施設。だれでも無料で使えます（開館日は館ごと）。"}.get(t, "")
        out.append(f'<h2>{FAC_TYPE[t]}（{len(xs)}）</h2>' + (f'<p class="small">{note}</p>' if note else "") + f'<ul class="gk fac">{lis}</ul>')
    src = '<p class="small">出典：横浜市の公園一覧表・図書館一覧・地域ケアプラザ紹介、各区役所の公園紹介・コミュニティハウスの案内、はまスポ（横浜市スポーツ施設案内）、横浜市の屋内プールの案内。2026年11月時点。住所・電話・時間が空いているものは、各施設のページで確かめてください。</p>'
    return "".join(out) + src, n


def area_pages(d, track_url):
    """区ごとの「子連れで行ける施設・遊び場」ページ（/area/区/）と、その入口（/area/）。通年の施設は /event/ のURLのまま、ここからつなぐ。"""
    out = []
    evs = d["events"]
    def wards_of(e): return str(e.get("ward") or "").split("・")
    ong = [e for e in evs if e.get("kind") == "ongoing" and not e["t"].startswith("各区")]
    lim = [e for e in evs if e.get("kind") == "limited" and e.get("days")]
    def li(e, extra=""):
        price = {"free": "無料", "admission": "入園料のみ", "paid": "有料"}.get(e.get("price"), "料金は要確認")
        return f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a>（{E(price)}{("・" + E(extra)) if extra else ""}）<div class="small">{E(e.get("sum", "")[:70])}</div></li>'
    rows = []
    for w, slug in WARD_SLUG.items():
        xs = [e for e in ong if w in wards_of(e)]
        ys = sorted([e for e in lim if w in wards_of(e)], key=lambda e: (iso(e["days"][0]), e.get("start") or 0))
        if not xs and not ys: continue
        rows.append((w, slug, len(xs), len(ys), len([e for e in xs if e.get("price") == "free"]), {k: sum(1 for e in xs if e.get("price") == "free" and play_kind(e) == k) for k in ["地区センターのプレイルーム", "子育て支援拠点・親子の広場", "こどもログハウス", "公園・屋外の遊び場", "施設・モール・博物館など"]},
                     ys[0] if ys else None))
        kinds = ["地区センターのプレイルーム", "子育て支援拠点・親子の広場", "こどもログハウス", "公園・屋外の遊び場", "施設・モール・博物館など"]
        free = [e for e in xs if e.get("price") == "free"]
        paid = [e for e in xs if e.get("price") != "free"]
        sec = "".join(f'<h2>{k}（{len(g)}）</h2><ul class="links">' + "".join(li(e, str(e.get("place", "")).split("（")[0]) for e in sorted(g, key=lambda e: e["t"])) + "</ul>"
                      for k in kinds for g in [[e for e in free if play_kind(e) == k]] if g)
        if paid:
            sec += f'<h2>有料・入園料のいる施設（料金要確認のものも）（{len(paid)}）</h2><ul class="links">' + "".join(li(e, str(e.get("place", "")).split("（")[0]) for e in sorted(paid, key=lambda e: e["t"])) + "</ul>"
        fsec, fn = fac_sections(w, xs)
        sec += fsec
        if ys:
            sec += f'<h2>{w}でこれから開かれる親子イベント（{len(ys)}）</h2><ul class="links">' + "".join(
                f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a>（{E(when_text(e)[:30])}）</li>' for e in ys[:20]) + "</ul>"
            if len(ys) > 20: sec += f'<p class="small">ほか{len(ys) - 20}件は<a href="/">トップの一覧</a>で日にち・区を選ぶと見られます。</p>'
        other = "".join(f'<a href="/area/{s2}/">{w2}</a> ' for w2, s2 in WARD_SLUG.items() if w2 != w)
        path = f"area/{slug}/"
        ch, cld = crumbs([("トップ", "/"), ("区ごとの施設・遊び場", "/area/"), (w, "")])
        body = f"""{ch}
<article class="card"><h1>{w}の子連れで行ける施設・遊び場</h1>
<p>{w}で、0歳から小学生の子どもと行ける施設・遊び場を{len(xs)}か所まとめました。無料のものは{len(free)}か所です。{f"そのほか、市の公園・図書館・コミュニティハウス・スポーツセンター・地域ケアプラザなど{fn}か所も下に並べています（タブ「🏛 施設をさがす」でも探せます）。" if fn else ""}雨の日は屋内のプレイルームや子育て支援拠点、晴れた日は公園やこどもログハウスへ。開館日・時間は施設ごとに違うので、名前を押して確かめてください。</p>
<div class="btns"><a class="btn main" href="/#play">無料の遊び場を区で絞り込む</a><a class="btn" href="/#shisetsu">施設を名前で探す</a>{f'<a class="btn" href="/gakudo/{slug}/">{w}の学童・キッズクラブ</a>' if os.path.exists(GAKUDO_JSON) else ''}</div>
{sec}
<h2>ほかの区</h2><p class="small">{other}</p></article>"""
        items = [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}event/{e['id']}/", "name": e["t"]} for i, e in enumerate(sorted(free, key=lambda e: (kinds.index(play_kind(e)), e["t"])) + sorted(paid, key=lambda e: e["t"]) + ys[:20])]
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{w}の子連れで行ける施設・遊び場", "url": SITE + path, "inLanguage": "ja"}, cld,
              {"@context": "https://schema.org", "@type": "ItemList", "name": f"{w}の子連れで行ける施設・遊び場", "numberOfItems": len(items), "itemListElement": items}]
        out.append((path, page(f"{w}の子連れで行ける施設・遊び場・公園（{len(xs) + fn}か所）｜KidsTrip",
                               f"{w}で0歳〜小学生と行ける施設・遊び場{len(xs)}か所（地区センターのプレイルーム・子育て支援拠点・こどもログハウス・公園など）と、これから開かれる親子イベント。",
                               path, body, ld, track_url=track_url, tpage=path)))
    ch, cld = crumbs([("トップ", "/"), ("区ごとの施設・遊び場", "")])
    tn = sum(r[2] for r in rows); tf = sum(r[4] for r in rows); te = len(lim)
    def wline(w, slug, n, m, nf, kc, ny):
        parts = "・".join(f"{k.replace('地区センターの', '').replace('・親子の広場', '').replace('・屋外の遊び場', '').replace('・モール・博物館など', '')}{c}" for k, c in kc.items() if c)
        nxt = f"いちばん近いイベントは{when_text(ny)[:20]}の「{ny['t'][:30]}」。" if ny else "いまはこの区で日にちの決まったイベントを載せていません。"
        return (f'<li><a href="/area/{slug}/"><b>{w}</b></a>：施設・遊び場{n}か所（うち無料{nf}か所{("：" + parts) if parts else ""}）、これからの親子イベント{m}件。{E(nxt)}</li>')
    body = f"""{ch}
<article class="card"><h1>横浜市の区ごとの子連れで行ける施設・遊び場</h1>
<p>横浜市18区の、子どもと行ける施設・遊び場（地区センターのプレイルーム・子育て支援拠点・こどもログハウス・公園・動物園など）を区ごとにまとめました。いま載せているのは施設・遊び場{tn}か所（うち無料{tf}か所）と、これから開かれる親子イベント{te}件です。区を選ぶと、種類ごとの一覧と、その区でこれから開かれるイベントが見られます。</p>
<p>雨の日は屋内の地区センターのプレイルームや子育て支援拠点、晴れた日は公園やこどもログハウスが便利です。開館日・時間は施設ごとに違うので、各施設のページから公式ページで確かめてください。</p>
<h2>区ごとの件数と特徴</h2>
<ul class="links">{"".join(wline(*r) for r in rows)}</ul>
<p class="small">情報の時点：{TODAY.year}年{TODAY.month}月{TODAY.day}日（毎日更新）。件数はこのサイトに載せているものだけで、区内のすべての施設ではありません。</p></article>"""
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}area/{r[1]}/", "name": f"{r[0]}の子連れで行ける施設・遊び場"} for i, r in enumerate(rows)]
    out.append(("area/", page(f"横浜市の区ごとの子連れで行ける施設・遊び場（{len(rows)}区・{tn}か所）｜KidsTrip", f"横浜市18区ごとに、子どもと行ける施設・遊び場{tn}か所（無料{tf}か所）と、これから開かれる親子イベントをまとめました。", "area/", body,
                              [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "横浜市の区ごとの子連れで行ける施設・遊び場", "url": SITE + "area/", "inLanguage": "ja"}, cld,
                               {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜市の区ごとの子連れで行ける施設・遊び場", "numberOfItems": len(items), "itemListElement": items}], track_url=track_url, tpage="area/")))
    return out


# ---- 特集・まとめ記事（/matome/）：毎日 EVENTS から自動で作り直す。文は決まった形で、データにないことは書かない（2026年11月）
MATOME_COUNT = {}  # path → 件数（トップの「📰 特集」に出す）
MATOME_LINKS = []  # (path, 題名)。matome_pages が埋め、index.html のページ一覧に使う
PRICE_JA = {"free": "無料", "admission": "入園料・入館料のみ", "paid": "有料", "unknown": "料金は要確認"}


def _up_days(e):
    return [k for k in (e.get("days") or []) if iso(k) >= TODAY]


def _hm(m):
    return f"{m // 60}:{m % 60:02d}" if isinstance(m, int) and m > 0 else ""


def matome_item(e, day=None):
    st = (e.get("stop") or {}).get(day) if day else None
    ds = _up_days(e)
    when = "" if day else (("・".join(jp_date(k) for k in ds[:4]) + ("ほか" if len(ds) > 4 else "")) if ds else when_text(e))
    bits = [x for x in [when, E(e.get("ward", "")), E(PRICE_JA.get(e.get("price"), "料金は要確認")), "雨でもOK" if e.get("rain") == "ok" else "", E(e.get("ageText", ""))] if x]
    venue = split_venue(e.get("venue", ""))[0] if e.get("venue") else ""
    return (f'<li><a href="/event/{e["id"]}/"><b>{E(e["t"])}</b></a>' + (f' <b style="color:var(--bad)">⛔ {E(st)}</b>' if st else "") +
            f'<div class="small">{" ・ ".join(bits)}{("　会場：" + E(venue)) if venue else ""}</div>'
            f'<div>{E(e.get("sum", ""))}</div></li>')


YE_PAT = re.compile(r"年末年始|年末|年始|元日|元旦|正月|三が日|大みそか|大晦日|12/2[6-9]|12/3[01]|(?<![\d/])1/[1-7](?![\d])")
YE_CORE = re.compile(r"年末|年始|元日|元旦|正月|三が日|大みそか|大晦日|12/2[6-9]|12/3[01]|(?<![\d/])1/[1-3](?![\d])")
YE_CLOSED = re.compile(r"休|閉館|閉園|以外は開館|以外は開園|営業しない")


def yearend_note(texts, closed=None, period=None):
    """年末年始の休み・営業時間の書いてある部分だけを、データの文からそのまま抜き出す（推測で足さない）。
    period（会期）は「○○以外は開館」のような休みの書き方のときだけ使う（会期の始まり・終わりの日は休みではないので）"""
    segs = []
    src = [(t, False) for t in texts] + ([(period, True)] if period else [])
    for t, is_period in src:
        for seg in re.split(r"[。\n]", str(t or "")):
            seg = seg.strip(" 　、")
            if not seg or not YE_CORE.search(seg):
                continue
            if is_period and not YE_CLOSED.search(seg):
                continue
            if not is_period and not (YE_CLOSED.search(seg) or re.search(r"\d+:\d+|確認", seg)):
                continue
            if len(seg) > 90:
                m = YE_CORE.search(seg); a = max(0, m.start() - 40); seg = ("…" if a else "") + seg[a:a + 90] + "…"
            if seg not in segs:
                segs.append(seg)
    cd = [k for k in (closed or []) if YE_CORE.search(k) and "/" in k]
    if cd and not any(YE_CLOSED.search(x) for x in segs):
        segs.insert(0, "休み：" + "・".join(cd))
    if not segs:
        return None, ""
    txt = "／".join(segs[:2])
    clauses = re.split(r"[、，／]", txt)
    kind = "closed" if any(YE_CORE.search(c) and YE_CLOSED.search(c) for c in clauses) else ("check" if "確認" in re.sub(r"（[^（）]*\d+年\d+月\d+日確認）", "", txt) else "open")
    return kind, txt

def yearend_days(txt):
    """「12/28〜1/4以外は開館」「12/26〜31休み」「1/1は休業」「12/31・1/1休み」「休み：1/1」から、年末年始（12/24〜1/7）に休む日を取り出す。
    日にちのすぐ後ろに「休」「以外は開」が続くものだけ（会期の「12/12〜1/17（年末年始の休館をのぞく）」などは数えない）。読めないときは空"""
    import datetime as _dt
    def od(m, d):
        try: return _dt.date(2026 if m == 12 else 2027, m, d)
        except ValueError: return None
    lo, hi = _dt.date(2026, 12, 24), _dt.date(2027, 1, 7)
    D = r"(?<![\d/])(1[12]|[1-9])/(\d{1,2})(?:\s*[〜~～\-]\s*(?:(1[12]|[1-9])/)?(\d{1,2}))?(?![\d/])"
    TAIL = re.compile(r"^(?:\s*[・、]\s*(?:1[12]|[1-9])/\d{1,2}(?:\s*[〜~～\-]\s*(?:(?:1[12]|[1-9])/)?\d{1,2})?)*\s*(?:は|が|も)?\s*(?:休|お休み|以外は開|閉)")
    out = set()
    for c in re.split(r"[、，／]", txt):
        if not YE_CLOSED.search(c):
            continue
        head = bool(re.match(r"\s*(?:休み|休館日?|休園日?)\s*[：:は]", c))
        for m in re.finditer(D, c):
            if not (head or TAIL.match(c[m.end():])):
                continue
            m1, d1 = int(m.group(1)), int(m.group(2))
            a, b = od(m1, d1), (od(int(m.group(3) or m.group(1)), int(m.group(4))) if m.group(4) else None)
            b = b or a
            if a and b and a <= b:
                x = a
                while x <= b:
                    if lo <= x <= hi: out.add(x)
                    x += _dt.timedelta(days=1)
    return sorted(out)


def yearend_label(days):
    if not days: return "年末年始に休み（日にちは各施設で確かめてください）"
    f = lambda x: f"{x.month}/{x.day}"
    if len(days) == 1: return f"{f(days[0])}だけ休み"
    if (days[-1] - days[0]).days == len(days) - 1: return f"{f(days[0])}〜{f(days[-1])}休み"
    return "・".join(f(x) for x in days) + "休み"


def _by_day(evs, days):
    sec, n = "", 0
    for k in days:
        xs = sorted([e for e in evs if k in (e.get("days") or [])], key=lambda e: (e.get("start") or 9999, e["t"]))
        if not xs: continue
        n += len(xs)
        sec += f'<h2 id="s{k.replace("/", "-")}">{jp_date(k)}（{len(xs)}件）</h2><ul class="links">' + "".join(matome_item(e, k) for e in xs) + "</ul>"
    return sec, n


def _by_first(evs):
    xs = sorted(evs, key=lambda e: (iso(_up_days(e)[0]), e.get("start") or 9999, e["t"]))
    months = []
    for e in xs:
        mo = f"{iso(_up_days(e)[0]).month}月"
        if not months or months[-1][0] != mo: months.append((mo, []))
        months[-1][1].append(e)
    return "".join(f'<h2 id="s{mo}">{mo}（{len(g)}件）</h2><ul class="links">' + "".join(matome_item(e) for e in g) + "</ul>" for mo, g in months)


def matome_pages(d, track_url):
    MATOME_LINKS.clear()
    evs = d["events"]
    lim = [e for e in evs if e.get("kind") == "limited" and _up_days(e)]
    ong = [e for e in evs if e.get("kind") == "ongoing" and not e["t"].startswith("各区")]
    seasonal = [e for e in ong if re.search(r"\d+/\d+", str(e.get("period") or ""))]  # 会期のある期間イベント（イルミネーションなど）
    asof = f"{TODAY.year}年{TODAY.month}月{TODAY.day}日"
    out, cards = [], []
    note = '<p class="small">情報の時点：' + asof + '（毎日、施設・主催者の公式ページをもとに自動で作り直しています）。中止・変更があることもあるので、出かける前に必ず各イベントの公式ページで確かめてください。</p>'

    def emit(slug, h1, title, desc, lead, sec, items, extra="", count=None):
        path = f"matome/{slug}/"
        ch, cld = crumbs([("トップ", "/"), ("特集・まとめ", "/matome/"), (h1, "")])
        body = f"""{ch}
<article class="card"><h1>{E(h1)}</h1>
<details class="mlead"><summary>この特集について</summary>{lead}</details>
<div class="btns"><a class="btn main" href="/">日にち・区で絞り込む</a><a class="btn" href="/matome/">ほかの特集</a></div>
{sec}{extra}
{note}</article>"""
        ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": h1, "url": SITE + path, "inLanguage": "ja", "dateModified": TODAY.isoformat()}, cld,
              {"@context": "https://schema.org", "@type": "ItemList", "name": h1, "numberOfItems": len(items),
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}event/{e['id']}/", "name": e["t"]} for i, e in enumerate(items)]}]
        out.append((path, page(title, desc, path, body, ld, noindex=not items, track_url=track_url, tpage=path)))
        MATOME_LINKS.append((path, h1))
        cards.append((path, h1, desc, len(items) if count is None else count))
        MATOME_COUNT[path] = cards[-1][3]

    def count_line(xs):
        nf = sum(1 for e in xs if e.get("price") == "free"); nr = sum(1 for e in xs if e.get("rain") == "ok")
        return f"無料のものは{nf}件、雨でも開かれるものは{nr}件です。"

    # 1) 今週末
    wk = next((w for w in d.get("weekends") or [] if iso(w["ds"][-1]) >= TODAY), None)
    if wk:
        days = [k for k in wk["ds"] if iso(k) >= TODAY]
        sec, _ = _by_day(lim, days)
        items = [e for e in lim if set(days) & set(e.get("days") or [])]
        n = len(items)
        sea = [e for e in seasonal if e not in items][:15]
        extra = (f'<h2 id="sseason">期間中ならいつでも行けるイベント（{len(sea)}件）</h2><ul class="links">' + "".join(matome_item(e) for e in sea) + "</ul>") if sea else ""
        lead = (f"<p>{E(wk['h'])}に、横浜市内で開かれる0歳〜小学生の親子向けイベントを{n}件、日にちごと・始まる時間の順にまとめました（2日とも開かれるものは両方の日に出ています）。{count_line(items)}"
                "名前を押すと、時間・料金・予約・雨の日の扱いと、近くの授乳室・ごはんが見られます。</p><p>クリスマスの時期はモールの工作やサンタのグリーティング、地区センターのおはなし会なども多く、整理券や予約がいるものもあります。気になるものは早めに公式ページを見ておくと安心です。</p>")
        emit("weekend", f"今週末（{wk['h']}）の横浜 子連れおでかけ・イベントまとめ", f"今週末の横浜 子連れイベントまとめ（{wk['h']}・{n}件）｜KidsTrip",
             f"{wk['h']}に横浜市内で開かれる親子向けイベント{n}件を、日にち・時間順に。無料・雨でもOK・対象年齢も一目で。", lead, sec, items, extra, count=n)

    def kw(e, pat): return re.search(pat, e["t"] + " " + str(e.get("sum", "")))
    # 2) クリスマス
    xm = [e for e in lim if kw(e, r"クリスマス|Xmas|X'mas|サンタ|ツリー|ノエル|リース")]
    xs_on = [e for e in seasonal if kw(e, r"クリスマス|Xmas|X'mas|サンタ|ツリー|イルミネーション|ノエル")]
    extra = (f'<h2 id="sillumi">期間中ずっと楽しめるクリスマスツリー・イルミネーション（{len(xs_on)}件）</h2><ul class="links">' + "".join(matome_item(e) for e in xs_on) + "</ul>") if xs_on else ""
    lead = (f"<p>横浜市内で開かれる、子どもと楽しめるクリスマスのイベントを{len(xm)}件、日にち順にまとめました。サンタクロースやキャラクターのグリーティング、リースやツリーの工作、クリスマスのおはなし会など。{count_line(xm)}"
            f"{'下のほうには、期間中ならいつでも見られるツリー・イルミネーション' + str(len(xs_on)) + '件も並べています。' if xs_on else ''}</p>"
            "<p>工作やグリーティングは整理券・事前申込みのものが多く、すぐに定員になることもあります。12/24・25の平日に開かれるものもあるので、日にちを確かめてください。</p>")
    emit("christmas", "横浜のクリスマスイベントまとめ【子連れ・親子向け】", f"横浜のクリスマスイベント 子連れ・親子向けまとめ（{len(xm)}件）｜KidsTrip",
         f"横浜市内の子ども・親子向けクリスマスイベント{len(xm)}件。サンタのグリーティング、リース・ツリーの工作、おはなし会、イルミネーションなど。", lead, _by_first(xm), xm + xs_on, extra, count=len(xm))

    # 3) 雨の日
    rn = [e for e in lim if e.get("rain") == "ok" and re.search(r"屋内|館内|室内", str(e.get("place", "")))]
    rp = [e for e in ong if e.get("price") == "free" and play_ok(e) and re.search(r"屋内|館内|室内", str(e.get("place", "")))]
    extra = (f'<h2 id="splay">雨の日の無料の室内遊び場</h2><p>地区センターのプレイルームや子育て支援拠点など、無料の室内遊び場を{len(rp)}か所載せています。区ごとの一覧から探せます：' +
             " ".join(f'<a href="/area/{sl}/">{w}</a>' for w, sl in WARD_SLUG.items() if os.path.exists(os.path.join(ROOT, "area", sl))) + "</p>") if rp else ""
    lead = (f"<p>雨の日でも開かれる、屋内の親子向けイベントを{len(rn)}件まとめました（会場が屋内で、公式に雨でも開くと書いてあるもの）。モールの工作・体験や、地区センター・図書館のおはなし会など。{count_line(rn)}</p>"
            "<p>いつでも行ける無料の室内遊び場（地区センターのプレイルーム・子育て支援拠点）は、下の区ごとの一覧からどうぞ。</p>")
    emit("rainy", "雨の日も行ける 横浜の屋内 子連れイベントまとめ", f"雨の日も行ける 横浜の屋内 子連れイベント（{len(rn)}件）｜KidsTrip",
         f"雨でも開かれる横浜市内の屋内の親子向けイベント{len(rn)}件と、無料の室内遊び場{len(rp)}か所。モールの工作、おはなし会など。", lead, _by_first(rn), rn, extra)

    # 4) 無料
    fr = [e for e in lim if e.get("price") == "free"]
    lead = (f"<p>参加費のいらない、横浜市内の親子向けイベントを{len(fr)}件、日にち順にまとめました。区の地区センター・図書館のおはなし会、モールのワークショップ、公園のイベントなど。雨でも開かれるものは{sum(1 for e in fr if e.get('rain') == 'ok')}件です。</p>"
            "<p>無料でも、事前の申込み・整理券がいるものや、材料がなくなりしだい終わるものがあります。名前を押して、予約の欄を確かめてください。</p>")
    emit("free", "無料で参加できる 横浜の子連れイベントまとめ", f"無料の横浜 子連れイベントまとめ（{len(fr)}件）｜KidsTrip",
         f"参加無料の横浜市内の親子向けイベント{len(fr)}件。おはなし会、モールの工作、公園のイベントなどを日にち順に。", lead, _by_first(fr), fr)

    # 5) 赤ちゃん（0〜2歳）
    def baby_ok(e):
        a = e.get("age") or [0, 99]
        return a[0] == 0 and a[1] <= 3 or kw(e, r"赤ちゃん|0歳|ベビー|乳幼児|親子ふれあい")
    bb = [e for e in lim if baby_ok(e)]
    lead = (f"<p>0歳〜2歳くらいの赤ちゃん・小さな子と行ける、横浜市内の親子向けイベントを{len(bb)}件まとめました（対象が0歳から3歳くらいまでのものと、赤ちゃん向けと書いてあるもの）。わらべうた・リトミック・おはなし会・親子の広場など。{count_line(bb)}</p>"
            '<p>授乳室・おむつ替えの場所は、各イベントのページの「近くのおむつ替え」や、<a href="/spot/">授乳室・おむつ替えのある施設一覧</a>で確かめられます。</p>')
    emit("baby", "赤ちゃん（0〜2歳）と行ける 横浜の親子イベントまとめ", f"赤ちゃん・0〜2歳と行ける横浜の親子イベント（{len(bb)}件）｜KidsTrip",
         f"0〜2歳の赤ちゃんと行ける横浜市内の親子イベント{len(bb)}件。わらべうた、リトミック、おはなし会など。近くの授乳室も。", lead, _by_first(bb), bb)

    # 6) 年末年始・お正月
    ny = [e for e in lim if kw(e, r"お正月|正月|書き初め|書初|餅つき|もちつき|初詣|凧|たこあげ|門松|しめ縄|干支|新春|新年|年末|カウントダウン")]
    # 年末年始に休む・時間が変わる施設（通年の施設・遊び場と、授乳室・おむつ替えのある施設。データに書いてあるものだけ）
    ye = {"closed": [], "open": [], "check": []}
    for e in ong:
        k, txt = yearend_note([e.get("time"), e.get("tip"), e.get("sum"), e.get("rainText")], e.get("closed"), e.get("period"))
        if k:
            ye[k].append((e.get("ward") or "区の記載なし", e["t"], f'/event/{e["id"]}/', txt))
    seen_sp = set(); sids = d.get("_spot_ids") or {}
    for area, lst in d["baby"].items():
        for b in lst:
            if b["n"] in seen_sp or b["n"] in d.get("_ev_of_spot", {}):
                continue
            seen_sp.add(b["n"])
            k, txt = yearend_note([v for v in b.values() if isinstance(v, str)])
            if k:
                ye[k].append((d["areas"].get(area, area) or area, b["n"], f'/spot/{sids[b["n"]]}/' if b["n"] in sids else "", txt))
    ye = {k: list({r[1]: r for r in v}.values()) for k, v in ye.items()}  # 同じ名前は1つに
    n_ye = sum(len(v) for v in ye.values())

    def ye_list(rows, nav=False):
        wl = list(WARD_SLUG)
        uniq = {}
        for r in rows: uniq.setdefault(r[1], r)
        rows = sorted(uniq.values(), key=lambda r: (wl.index(r[0]) if r[0] in wl else len(wl), r[0], r[1]))
        groups = list(dict.fromkeys(r[0] for r in rows))
        html, cur = "", None
        if nav and len(groups) > 3:
            html += '<p class="small">' + " ".join(f'<a href="#ye{i}">{E(g)}</a>' for i, g in enumerate(groups)) + "</p>"
        for w, n, href, txt in rows:
            if w != cur:
                lab = w if w in wl else f"{w}（授乳室・おむつ替えのある施設など）"
                html += ("</ul>" if cur is not None else "") + (f'<h3 id="ye{groups.index(w)}">' if nav else "<h3>") + f'{E(lab)}</h3><ul class="links">'; cur = w
            nm = f'<a href="{href}"><b>{E(n)}</b></a>' if href else f"<b>{E(n)}</b>"
            html += f'<li>{nm}<div class="small">{E(txt)}</div></li>'
        return html + ("</ul>" if cur is not None else "")
    # 年明けから長く休む施設（リニューアル工事など。データに「○年1月○日から…休園」とあるもの）
    long_cl = []
    for e in ong:
        for seg in re.split(r"。", str(e.get("sum", "")) + "。" + str(e.get("tip", ""))):
            if re.search(r"(?:20\d\d年)?1月\d+日から[^。]*休(?:園|館)|(?<![\d/])1/\d{1,2}から[^。]*休(?:園|館)", seg):
                long_cl.append((e, seg.strip())); break
    ye_html = ""
    if long_cl:
        ye_html += ('<h2 id="slong">年明けから長く休む施設</h2><ul class="links">' + "".join(
            f'<li><a href="/event/{e["id"]}/"><b>{E(e["t"])}</b></a><span class="small">（{E(e.get("ward", ""))}）</span><div class="small">{E(seg)}</div></li>' for e, seg in long_cl) + "</ul>")
    if n_ye:
        wl = list(WARD_SLUG)
        grp = {}
        for r in {r[1]: r for r in ye["closed"]}.values():
            ds = yearend_days(r[3])
            grp.setdefault(tuple(ds), []).append(r)
        keys = sorted(grp, key=lambda k: (not k, k[0] if k else None, -len(k)))
        nav = '<p class="small">' + " ".join(f'<a href="#yc{i}">{E(yearend_label(list(k)))}（{len(grp[k])}）</a>' for i, k in enumerate(keys)) + "</p>"
        body_c = ""
        for i, k in enumerate(keys):
            rows = sorted(grp[k], key=lambda r: (wl.index(r[0]) if r[0] in wl else len(wl), r[0], r[1]))
            body_c += f'<h3 id="yc{i}">{E(yearend_label(list(k)))}（{len(rows)}か所）</h3><ul class="links">'
            for w, n, href, txt in rows:
                nm = f'<a href="{href}"><b>{E(n)}</b></a>' if href else f"<b>{E(n)}</b>"
                body_c += f'<li>{nm}<span class="small">（{E(w)}）</span><div class="small">{E(txt)}</div></li>'
            body_c += "</ul>"
        ye_html += (f'<h2 id="sclosed">年末年始に休む施設・遊び場（{sum(len(v) for v in grp.values())}か所）</h2>'
                   '<p class="small">各施設の公式ページに書いてある年末年始の休みを、休む日ごとに分けて載せています（休む日はふだんの休館日を除いた年末年始の分だけ）。書いていない施設は、ここに出ていなくても休むことがあります。</p>' + nav + body_c)
        if ye["open"]:
            ye_html += f'<h2 id="sopen">年末年始に時間が変わる・営業の日が書いてある施設（{len(ye["open"])}か所）</h2>' + ye_list(ye["open"])
        if ye["check"]:
            ye_html += f'<h2 id="scheck">年末年始の日にちは公式で確かめてほしい施設（{len(ye["check"])}か所）</h2>' + ye_list(ye["check"])
    if ny or n_ye:
        lead = (f"<p>年末年始・お正月に、横浜市内で子どもと楽しめるイベントを{len(ny)}件まとめました。お正月飾りの工作、書き初め、もちつき、新春のイベントなど。{count_line(ny)}</p>"
                f"<p>年末年始は施設の休館日が多く、開館日もふだんと違うことがあります。下のほうに、年末年始に休む施設・遊び場（{len(ye['closed'])}か所）と、時間が変わる施設を区ごとに並べています。出かける前に公式ページでも確かめてください。</p>")
        emit("newyear", "年末年始・お正月の横浜 子連れイベントと休館日まとめ", f"年末年始・お正月の横浜 子連れイベントと休館日（{len(ny)}件・休む施設{len(ye['closed'])}か所）｜KidsTrip",
             f"横浜市内の年末年始・お正月の親子イベント{len(ny)}件と、年末年始に休む施設・遊び場{len(ye['closed'])}か所。お正月飾りの工作、書き初め、もちつきなど。", lead, _by_first(ny), ny, ye_html, count=len(ny))

    # 入口 /matome/
    ch, cld = crumbs([("トップ", "/"), ("特集・まとめ", "")])
    lis = "".join(f'<li><a href="/{p_}"><b>{E(h)}</b></a>（{n}件）<div class="small">{E(ds)}</div></li>' for p_, h, ds, n in cards)
    body = f"""{ch}
<article class="card"><h1>横浜の子連れおでかけ 特集・まとめ</h1>
<p>KidsTripに載せている横浜市内の親子向けイベントを、テーマごとにまとめた特集です。今週末のイベント、クリスマス、雨の日、無料、赤ちゃんと行けるものなど。どの特集も毎日の更新に合わせて自動で作り直すので、いつ開いてもこれから開かれるものだけが並びます。</p>
<p>日にち・区・無料かどうかなどで自由に絞り込むときは<a href="/">トップの一覧</a>、いつでも行ける施設・公園は<a href="/area/">区ごとの施設・遊び場</a>からどうぞ。</p>
<h2>特集の一覧</h2><ul class="links">{lis}</ul>
{note}</article>"""
    out.append(("matome/", page("横浜の子連れおでかけ 特集・まとめ｜KidsTrip", "横浜の親子向けイベントをテーマ別に。今週末のイベント、クリスマス、雨の日、無料、赤ちゃんと行けるイベントなど。毎日更新。", "matome/", body,
                                [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "横浜の子連れおでかけ 特集・まとめ", "url": SITE + "matome/", "inLanguage": "ja"}, cld,
                                 {"@context": "https://schema.org", "@type": "ItemList", "name": "特集・まとめ", "numberOfItems": len(cards),
                                  "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + c[0], "name": c[1]} for i, c in enumerate(cards)]}],
                                track_url=track_url, tpage="matome/")))
    return out


def index_pages(d, spots, spot_ids, track_url, form_url):
    """一覧ページ：/event/（日にちのあるイベント）・/spot/（赤ちゃん設備のある施設）・/contact/（お問い合わせ）"""
    out = []
    lim = sorted([e for e in d["events"] if e.get("kind") == "limited" and e.get("days")], key=lambda e: (iso(e["days"][0]), e.get("start") or 0, e["t"]))
    months = []
    for e in lim:
        mo = iso(e["days"][0]).strftime("%Y年%-m月")
        if not months or months[-1][0] != mo: months.append((mo, []))
        months[-1][1].append(e)
    sec = "".join(f'<h2>{mo}から始まるイベント（{len(xs)}件）</h2><ul class="links">' + "".join(
        f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a>（{E(when_text(e)[:30])}・{E(e.get("ward", ""))}）</li>' for e in xs) + "</ul>" for mo, xs in months)
    ch, cld = crumbs([("トップ", "/"), ("イベント一覧", "")])
    body = f"""{ch}
<article class="card"><h1>横浜の子連れイベント一覧（日にち順）</h1>
<p>横浜市内で、これから開かれる0歳〜小学生の親子向けイベント{len(lim)}件を、始まる日の順に並べました。名前を押すと、日にち・時間・料金・予約・雨の日の扱いと、近くの授乳室・ごはんが見られます。日にち・区・無料かどうかで絞り込むときは<a href="/">トップの一覧</a>から。いつでも行ける施設・公園は<a href="/area/">区ごとの施設・遊び場</a>にまとめています。</p>
<div class="btns"><a class="btn main" href="/">日にち・区で絞り込む</a><a class="btn" href="/area/">区ごとの施設・遊び場</a></div>
{sec}
<p class="small">内容は変わることがあるので、出かける前に必ず各イベントの公式ページで確かめてください。</p></article>"""
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}event/{e['id']}/", "name": e["t"]} for i, e in enumerate([e for e in lim if e["id"] not in d.get("_thin", {}).get("event", set())])]
    out.append(("event/", page(f"横浜の子連れイベント一覧（{len(lim)}件・日にち順）｜KidsTrip", f"横浜市内でこれから開かれる0歳〜小学生の親子向けイベント{len(lim)}件を日にち順に。クリスマス・お正月のイベントや区のおはなし会、無料の工作など。",
                               "event/", body, [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "横浜の子連れイベント一覧", "url": SITE + "event/", "inLanguage": "ja"}, cld,
                                                {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜の子連れイベント一覧", "numberOfItems": len(items), "itemListElement": items}],
                               track_url=track_url, tpage="event/")))
    # 赤ちゃん設備のある施設（エリアごと。いちばん最初に出てくるエリアに入れる）
    by_area = {}
    for n, (b, area) in spots.items():
        by_area.setdefault(area, []).append(b)
    order = list(d["baby"].keys())
    sec = "".join(f'<h2>{E(d["areas"].get(a, "") or "そのほか")}（{len(by_area[a])}か所）</h2>' + matrix(by_area[a], spot_ids) for a in order if by_area.get(a))
    nw = sum(1 for b, _ in spots.values() if b.get("w") is True)
    nmw = sum(1 for b, _ in spots.values() if b.get("mw") is True)
    ch, cld = crumbs([("トップ", "/"), ("授乳室・おむつ替えのある施設", "")])
    body = f"""{ch}
<article class="card"><h1>横浜の授乳室・おむつ替えのある施設一覧（エリア別）</h1>
<p>横浜市内の、おむつ替え・授乳室・調乳のお湯・離乳食を温める電子レンジがある施設{len(spots)}か所を、エリアごとにまとめました（お湯が確かめられた施設は{nw}か所、電子レンジは{nmw}か所）。施設の名前を押すと、何階のどこにあるか、パパも使えるか、近くのごはん・子ども服のお店が見られます。○×は施設の公式ページなどで確かめたもので、「？」は調べた範囲で確認できなかったものです。</p>
<div class="btns"><a class="btn main" href="/#foodall">近くのごはん・おむつを地図で探す</a></div>
{sec}
<p class="small">設備は工事などで変わることがあります。間違いに気づいたら<a href="/contact/">お問い合わせ</a>から教えてください。</p></article>"""
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}spot/{spot_ids[n]}/", "name": short(n)} for i, n in enumerate([n for n in spots if spot_ids[n] not in d.get("_thin", {}).get("spot", set())])]
    out.append(("spot/", page(f"横浜の授乳室・おむつ替えのある施設一覧（{len(spots)}か所・エリア別）｜KidsTrip", f"横浜市内の授乳室・おむつ替え・調乳のお湯・電子レンジがある施設{len(spots)}か所をエリア別に。みなとみらい・横浜駅・中華街・新横浜などのモール・駅・博物館の何階にあるか、パパも使えるか。",
                              "spot/", body, [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "横浜の授乳室・おむつ替えのある施設一覧", "url": SITE + "spot/", "inLanguage": "ja"}, cld,
                                              {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜の授乳室・おむつ替えのある施設", "numberOfItems": len(items), "itemListElement": items}],
                              track_url=track_url, tpage="spot/")))
    ch, cld = crumbs([("トップ", "/"), ("お問い合わせ", "")])
    body = f"""{ch}
<article class="card"><h1>お問い合わせ</h1>
<p>KidsTrip（キッズトリップ）へのお問い合わせは、下のお問い合わせフォーム（Googleフォーム）か、メール（<a href="mailto:info@kidstrip.jp">info@kidstrip.jp</a>）でお送りください。フォームはGoogleアカウントでのログインが必要なので、アカウントをお持ちでない方はメールをお使いください。</p>
<h2>こんなときにどうぞ</h2>
<ul class="links"><li>イベントの日にち・時間・料金などが公式と違っていた</li><li>授乳室・おむつ替え・お湯・電子レンジの場所や有無が違っていた、なくなっていた</li><li>主催者・施設の方で、掲載内容を直したい・掲載をやめてほしい</li><li>サイトの使い方で分かりにくいところがある</li></ul>
<p>いただいた内容は、施設・主催者の公式ページで確かめてから直します。いただいた情報の扱いは<a href="/privacy/">プライバシーポリシー</a>のとおりです。</p>
<div class="btns"><a class="btn main" href="{E(form_url)}" target="_blank" rel="noopener">お問い合わせフォームを開く</a><a class="btn" href="mailto:info@kidstrip.jp">メールで送る</a><a class="btn" href="/about/">このサイトについて</a></div></article>"""
    out.append(("contact/", page("お問い合わせ｜KidsTrip（キッズトリップ）", "KidsTrip（キッズトリップ）へのお問い合わせ。イベント・授乳室などの情報の間違い、掲載内容の修正・掲載の取りやめの依頼は、お問い合わせフォームからどうぞ。",
                                 "contact/", body, [{"@context": "https://schema.org", "@type": "ContactPage", "name": "お問い合わせ｜KidsTrip", "url": SITE + "contact/", "inLanguage": "ja"}, cld],
                                 track_url=track_url, tpage="contact/")))
    return out


def main():
    d = load_data()
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = TRACK_URL_RE.search(open(os.path.join(ROOT, "js", "data.js"), encoding="utf-8").read()) or TRACK_URL_RE.search(src)
    track_url = m.group(1) if m else ""
    fm = re.search(r'class="contactbtn" href="([^"]+)"', src)
    ap, ah = about_page(track_url, fm.group(1) if fm else "/")
    os.makedirs(os.path.join(ROOT, ap), exist_ok=True)
    open(os.path.join(ROOT, ap, "index.html"), "w", encoding="utf-8").write(ah)
    pp, ph = privacy_page(track_url, fm.group(1) if fm else "/")
    os.makedirs(os.path.join(ROOT, pp), exist_ok=True)
    open(os.path.join(ROOT, pp, "index.html"), "w", encoding="utf-8").write(ph)
    man = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"event": {}, "spot": {}}
    # 施設（BABY）：名前ごとに1ページ。最初に出てきたエリアを使う
    spots, spot_ids = {}, {}
    for area, lst in d["baby"].items():
        for b in lst:
            if b["n"] not in spots:
                spots[b["n"]] = (b, area)
                spot_ids[b["n"]] = hash_id(b["n"])
    d["_spot_by_name"] = {n: b for n, (b, area) in spots.items()}
    # 同じ施設が /event/（料金・時間・遊び方）と /spot/（授乳室・おむつ替え）の両方にあるとき、互いにリンクする
    ong = {_norm(short(e["t"])): e for e in d["events"] if e.get("kind") == "ongoing"}
    d["_ev_of_spot"], d["_spot_of_ev"] = {}, {}
    for n in spots:
        e = ong.get(_norm(short(n)))
        if e and len(_norm(short(n))) >= 3:
            d["_ev_of_spot"][n] = e
            d["_spot_of_ev"][e["id"]] = n
    d["_spot_ids"] = spot_ids
    built = {"event": {}, "spot": {}}
    for e in d["events"]:
        path, htmltext, name = event_page(e, d, spot_ids, track_url)
        built["event"][e["id"]] = (path, htmltext, name)
    for n, (b, area) in spots.items():
        path, htmltext, name = spot_page(b, area, d, spot_ids, track_url)
        built["spot"][spot_ids[n]] = (path, htmltext, name)
    # 本文が薄くて noindex になるページ（sitemap から外すもの）。一覧ページの ItemList からも外して、sitemap と数を揃える
    d["_thin"] = {k: {pid for pid, (_, h, _) in built[k].items() if body_chars(h) < MIN_CHARS} for k in built}
    gk_man = {}
    for gp, gh in gakudo_pages(track_url) + area_pages(d, track_url) + matome_pages(d, track_url) + index_pages(d, spots, spot_ids, track_url, fm.group(1) if fm else "/"):
        os.makedirs(os.path.join(ROOT, gp), exist_ok=True)
        open(os.path.join(ROOT, gp, "index.html"), "w", encoding="utf-8").write(gh)
        hh = hashlib.sha1(gh.encode()).hexdigest()[:12]
        old = man.get("gakudo", {}).get(gp, {})
        gk_man[gp] = {"hash": hh, "lastmod": old.get("lastmod", TODAY.isoformat()) if old.get("hash") == hh else TODAY.isoformat()}
        # 記録のスプレッドシートの「ページ別」で、まとめ記事・一覧・区のページも型・字数を並べられるように
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", gh, re.S)
        tm = re.search(r'"@type": "(?!BreadcrumbList|ListItem|PostalAddress|GeoCoordinates|Offer|Organization)(\w+)"', gh)
        gk_man[gp].update({"name": re.sub(r"<[^>]+>", "", h1.group(1)).strip()[:60] if h1 else "", "type": tm.group(1) if tm else "",
                           "chars": body_chars(gh), "links": len(set(re.findall(r'href="/(?:event|spot)/[^"/]+/"', gh)))})
    today = TODAY.isoformat()
    new_man = {"event": {}, "spot": {}}
    for kind in ("event", "spot"):
        for pid, (path, htmltext, name) in built[kind].items():
            thin = body_chars(htmltext) < MIN_CHARS
            if thin and 'name="robots"' not in htmltext:  # 中身が薄いページは、厚くなるまで検索に出さない（sitemapにも入れない）
                htmltext = htmltext.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
            h = hashlib.sha1(re.sub(r"情報の時点：[^<]*", "", htmltext).encode()).hexdigest()[:12]
            old = man.get(kind, {}).get(pid, {})
            lm = old.get("lastmod", today) if old.get("hash") == h and not old.get("ended") else today
            new_man[kind][pid] = {"name": name, "hash": h, "lastmod": lm, "added": old.get("added") or (old.get("lastmod") if old else today)}
            # 記録のスプレッドシートで、ページ別の表示回数と並べるための情報（型・本文の字数・ほかの個別ページへのリンク数）
            tm = re.search(r'"@type": "(?!BreadcrumbList|ListItem|PostalAddress|GeoCoordinates|LocationFeatureSpecification|Offer|Place"|Organization)(\w+)"', htmltext) or re.search(r'"@type": "(Place)"', htmltext)
            new_man[kind][pid].update({"type": tm.group(1) if tm else "", "chars": body_chars(htmltext),
                                       "links": len(set(re.findall(r'href="/(?:event|spot)/[^"/]+/"', htmltext)))})
            if thin:
                new_man[kind][pid]["thin"] = True
            out = os.path.join(ROOT, path, "index.html")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(htmltext)
        for pid, old in man.get(kind, {}).items():  # 一覧から外れたもの
            if pid in built[kind]:
                continue
            save_ended_body(kind, pid)
            path, htmltext = ended_page(kind, pid, old.get("name", ""), d)
            out = os.path.join(ROOT, path, "index.html")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(htmltext)
            new_man[kind][pid] = dict(old, ended=True, lastmod=old.get("lastmod", today) if old.get("ended") else today)
    new_man["gakudo"] = gk_man
    # 同じ座標を2つ以上の施設が使っている組（片方は借り物かもしれない。公式で確かめるまで official にしない）
    pts = {}
    for n in spots:
        g = d["extra"]["sp"].get(n, {}).get("geo")
        if g: pts.setdefault(f"{g[0]:.4f},{g[1]:.4f}", []).append(n)
    new_man["geo_dup"] = {k: v for k, v in sorted(pts.items()) if len(v) > 1}
    for v in new_man["geo_dup"].values():
        for n in v:
            if d["extra"]["sp"][n].get("geoSrc") == "official": print("注意：同じ座標の組に official があります →", " / ".join(v))
    new_man["og"], og_made = render_og(d["events"], man.get("og", {}))
    new_man["og_spot"], og_spot = render_og_spots(spots, spot_ids, d["areas"], man.get("og_spot", {}))
    og_made += og_spot
    json.dump(new_man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

    # sitemap
    urls = [(SITE, today, "daily"), (SITE + "en/", man.get("_en", today), "weekly"), (SITE + "about/", "2026-11-16", "monthly"), (SITE + "privacy/", "2026-11-16", "yearly")]
    for gp, v in sorted(gk_man.items()):
        urls.append((SITE + gp, v["lastmod"], "monthly"))
    for kind in ("event", "spot"):
        for pid, v in sorted(new_man[kind].items()):
            if not v.get("ended") and not v.get("thin"):
                urls.append((f"{SITE}{kind}/{pid}/", v["lastmod"], "weekly"))
    # sitemap は種類ごとに分ける（URLは変えない）。sitemap.xml はそれらをまとめる索引
    def urlset(us):
        return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            f"  <url><loc>{u}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq></url>\n" for u, lm, cf in us) + "</urlset>\n"
    IDX = {SITE + "event/", SITE + "spot/"}  # /matome/ は /event/ を含まないので、ふつうのページ（sitemap-pages）に入る  # 一覧ページはふつうのページとして扱う
    def is_event(u):
        if "/event/" not in u or u in IDX: return False
        return new_man["event"].get(u.rstrip("/").split("/")[-1], {}).get("type") == "Event"
    groups = {"sitemap-events.xml": [x for x in urls if is_event(x[0])],
              "sitemap-spots.xml": [x for x in urls if x[0] not in IDX and (("/event/" in x[0] and not is_event(x[0])) or "/spot/" in x[0])],
              "sitemap-pages.xml": [x for x in urls if x[0] in IDX or ("/event/" not in x[0] and "/spot/" not in x[0])]}
    for fn, us in groups.items():
        open(os.path.join(ROOT, fn), "w", encoding="utf-8").write(urlset(us))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <sitemap><loc>{SITE}{fn}</loc><lastmod>{max([x[1] for x in us] or [today])}</lastmod></sitemap>\n" for fn, us in groups.items()) + "</sitemapindex>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)

    # 英語版：英語で載せている場所・イベント・赤ちゃん設備から、日本語の個別ページへのリンク（<!--JA:START-->〜<!--JA:END-->）
    en_links(d, spots, spot_ids)

    # index.html：ページへのリンク一覧と、構造化データ（ItemList・Organization）
    ev_live = [e for e in d["events"]]
    links = ('<details class="fold pagelinks"><summary>イベント・施設のページ一覧</summary><div class="fbody">'
             '<p><a href="/event/">イベント一覧（日にち順）</a>　<a href="/area/">区ごとの施設・遊び場</a>　<a href="/spot/">授乳室・おむつ替えのある施設</a>　<a href="/matome/">特集・まとめ</a></p>'
             '<h3 class="fsum-static">特集・まとめ</h3><ul class="plinks">' + "".join(f'<li><a href="/{mp}">{E(mt)}</a></li>' for mp, mt in MATOME_LINKS) + "</ul>"
             '<h3 class="fsum-static">イベント</h3><ul class="plinks">' + "".join(f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a></li>' for e in ev_live if e.get("kind") != "ongoing") + "</ul>"
             '<h3 class="fsum-static">区ごとの施設・遊び場</h3><ul class="plinks">' + "".join(f'<li><a href="/area/{sl}/">{w}</a></li>' for w, sl in WARD_SLUG.items() if os.path.exists(os.path.join(ROOT, "area", sl))) + "</ul>"
             '<h3 class="fsum-static">赤ちゃん設備のある施設</h3><ul class="plinks">' + "".join(f'<li><a href="/spot/{spot_ids[n]}/">{E(short(n))}</a></li>' for n in spots) + "</ul></div></details>")
    ev_lim = [e for e in ev_live if e.get("kind") != "ongoing"]  # ページ一覧の「イベント」と同じもの
    item_list = {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜の子連れイベント一覧", "numberOfItems": len(ev_lim),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}event/{e['id']}/", "name": e["t"]} for i, e in enumerate(ev_lim)]}
    org = {"@context": "https://schema.org", "@type": "Organization", "name": "KidsTrip", "alternateName": "キッズトリップ", "url": SITE, "logo": SITE + "img/logo.webp"}
    # 新着イベント（載せた日が新しい順に20件）：トップから個別ページへの静的リンク
    def dlabel(e):
        ds = e.get("days") or []
        return (ds[0] + ("〜" if len(ds) > 1 else "")) if ds else ("開催中" if e.get("kind") == "ongoing" else "")
    def dkey(e):
        ds = e.get("days") or []
        if not ds: return 9999
        mo, dd = map(int, ds[0].split("/"))
        return (mo + (12 if mo < TODAY.month - 1 else 0)) * 40 + dd
    # 載せた日が新しい順。同じ日なら、日にちのあるイベント（近い順）→ いつでも行ける場所
    newest = sorted(ev_live, key=lambda e: (-int(new_man["event"][e["id"]]["added"].replace("-", "")), e.get("kind") != "limited", dkey(e), e["id"]))[:20]
    def nli(e):
        dl = dlabel(e)
        return f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a>' + (f'<span class="d">{E(dl)}</span>' if dl else "") + "</li>"
    # 新着はたたんでおき、「いつの更新で何件増えたか」だけ見せる
    last_add = max((new_man["event"][e["id"]]["added"] for e in ev_live), default=TODAY.isoformat())
    n_last = sum(1 for e in ev_live if new_man["event"][e["id"]]["added"] == last_add)
    ly, lm_, ld_ = map(int, last_add.split("-"))
    newhtml = ('<section class="newev" id="newev" aria-label="新着イベント"><details class="fold"><summary><h2 class="fsum">🆕 新しく載せたイベント'
               f'<span class="newcnt">{lm_}月{ld_}日の更新で{n_last}件</span></h2></summary><div class="fbody"><ul>' + "".join(nli(e) for e in newest) + "</ul></div></details></section>")
    # 区ごとの無料の遊び場（タブ「🛝 無料の遊び場」）：JSが動く前・検索エンジン向けの静的な一覧。js/app.js の playOk と同じ条件
    WARD_ORDER = ["鶴見区","神奈川区","西区","中区","南区","港南区","保土ケ谷区","旭区","磯子区","金沢区","港北区","緑区","青葉区","都筑区","戸塚区","栄区","泉区","瀬谷区"]
    play = [e for e in ev_live if e.get("kind") == "ongoing" and e.get("price") == "free" and (e.get("freeplay") or e.get("animal") or e.get("ride"))]
    def pwards(e): return ["市内のまとめ"] if e["t"].startswith("各区") else str(e.get("ward") or "").split("・")
    def pname(e): return re.sub(r"（([^（）]*区)の地域子育て支援拠点）$", "（子育て支援拠点）", re.sub(r"（[^（）]*区）$", "", e["t"]))
    playhtml = '<div id="play-static"><ul>' + "".join(
        f'<li><a href="/area/{WARD_SLUG[w]}/">{w}の施設・遊び場</a>（無料の遊び場{len(xs)}か所）</li>'
        for w in WARD_ORDER for xs in [[e for e in play if w in pwards(e)]] if xs) + "</ul></div>"
    # js/app.js の ?v= を中身のハッシュに合わせる（変えたときだけブラウザが読み直す）
    appv = hashlib.sha1(open(os.path.join(ROOT, "js", "app.js"), "rb").read()).hexdigest()[:10]
    src = re.sub(r'src="js/app\.js\?v=[0-9a-f]*"', f'src="js/app.js?v={appv}"', src)
    datav = hashlib.sha1(open(os.path.join(ROOT, "js", "data.js"), "rb").read()).hexdigest()[:10]
    src = re.sub(r'src="js/data\.js\?v=[0-9a-f]*"', f'src="js/data.js?v={datav}"', src)
    if os.path.exists(GAKUDO_JSON):
        gkv = hashlib.sha1(open(GAKUDO_JSON, "rb").read()).hexdigest()[:10]
        src = re.sub(r'data-src="/tools/gakudo\.json\?v=[0-9a-f]*"', f'data-src="/tools/gakudo.json?v={gkv}"', src)
    if os.path.exists(FAC_JSON):
        fcv = hashlib.sha1(open(FAC_JSON, "rb").read()).hexdigest()[:10]
        src = re.sub(r'data-src="/tools/facilities\.json\?v=[0-9a-f]*"', f'data-src="/tools/facilities.json?v={fcv}"', src)
    src = re.sub(r"<!--PLAY:START-->.*?<!--PLAY:END-->", lambda _: f"<!--PLAY:START-->{playhtml}<!--PLAY:END-->", src, flags=re.S)
    # トップの「📰 特集」：まとめ記事への入口（横にスクロールする丸いボタン）
    MSHORT = {"weekend": "今週末", "christmas": "クリスマス", "rainy": "雨の日", "free": "無料", "baby": "赤ちゃんと", "newyear": "お正月・休館日"}
    mhtml = ('<section class="matome" aria-label="特集・まとめ"><h2>📰 特集<a href="/matome/" data-act="matome">すべての特集</a></h2><ul>' + "".join(
        f'<li><a href="/{c}" data-act="matome">{E(MSHORT.get(c.split("/")[1], t))}' + (f'<span>{MATOME_COUNT[c]}件</span>' if MATOME_COUNT.get(c) else "") + "</a></li>" for c, t in MATOME_LINKS) + "</ul></section>")
    src = re.sub(r"<!--MATOME:START-->.*?<!--MATOME:END-->", lambda _: f"<!--MATOME:START-->{mhtml}<!--MATOME:END-->", src, flags=re.S)
    src = re.sub(r"<!--NEW:START-->.*?<!--NEW:END-->", lambda _: f"<!--NEW:START-->{newhtml}<!--NEW:END-->", src, flags=re.S)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (org, item_list))
    src = re.sub(r"<!--PAGES:START-->.*?<!--PAGES:END-->", lambda _: f"<!--PAGES:START-->{links}<!--PAGES:END-->", src, flags=re.S)
    src = re.sub(r"<!--LD:START-->.*?<!--LD:END-->", lambda _: f"<!--LD:START-->{ld}<!--LD:END-->", src, flags=re.S)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(src)
    print(f"住所 {sum(1 for n in spots if d['extra']['sp'].get(n, {}).get('addr'))}/{len(spots)}  同じ座標の組 {len(new_man['geo_dup'])}")
    print(f"og {og_made}  event {len(built['event'])}  spot {len(built['spot'])}  ended {sum(1 for k in ('event','spot') for v in new_man[k].values() if v.get('ended'))}  sitemap {len(urls)}")


if __name__ == "__main__":
    sys.exit(main())
