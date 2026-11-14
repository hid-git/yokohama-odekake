#!/usr/bin/env python3
"""KidsTrip の個別ページを作る（毎日の更新で、commit の前に実行する）。

  python3 tools/build_pages.py

- index.html をブラウザで開いてデータ（EVENTS・BABY など）を読み、
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
    return "・".join(jp_date(k) for k in e["days"])


CSS = """
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
.legend,.small{font-size:12px;color:var(--muted)}ul.links{padding-left:1.2em}ul.links li{margin:4px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0;margin:8px 0}.chips li{font-size:12.5px;padding:2px 10px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-weight:700}
footer{margin:28px 0 8px;font-size:12px;color:var(--muted)}
"""

SHARE_JS = """document.addEventListener("click",async ev=>{const b=ev.target.closest("[data-share]");if(!b)return;const url=location.href.split("?")[0],title=document.title;
if(navigator.share){try{await navigator.share({title,url})}catch(_){}return}
try{await navigator.clipboard.writeText(url);b.textContent="コピーしました"}catch(_){b.textContent=url}});"""


def track_js(track_url, page):
    if not track_url:
        return ""
    return """(function(){var U=%s;if(!/(github\\.io|kidstrip\\.jp)$/.test(location.hostname))return;var v="";try{v=localStorage.getItem("vid")||"";if(!v){v=Math.random().toString(36).slice(2,10);localStorage.setItem("vid",v)}}catch(_){}
var ua=navigator.userAgent,dev=/iPhone|iPod/.test(ua)?"iPhone":/iPad/.test(ua)?"iPad":/Android/.test(ua)?(/Mobile/.test(ua)?"Androidスマホ":"Androidタブレット"):"PC",app=/\\bLine\\//i.test(ua)?"LINEアプリ内":/Instagram/.test(ua)?"Instagramアプリ内":/FBAN|FBAV/.test(ua)?"Facebookアプリ内":"ブラウザ",tz="";try{tz=Intl.DateTimeFormat().resolvedOptions().timeZone||""}catch(_){}
function t(type,value,target){var ref="";try{ref=document.referrer?new URL(document.referrer).hostname:""}catch(_){}var body=JSON.stringify({type:type,value:String(value||"").slice(0,200),target:String(target||"").slice(0,200),dev:dev,app:app,ref:ref.slice(0,100),vid:v,page:%s,lang:(navigator.language||"").slice(0,10),tz:tz.slice(0,40),jp:tz?(tz==="Asia/Tokyo"?"日本":"海外"):""});try{navigator.sendBeacon?navigator.sendBeacon(U,new Blob([body],{type:"text/plain"})):fetch(U,{method:"POST",body:body,mode:"no-cors",keepalive:true})}catch(_){}}
t("pageview",document.title);document.addEventListener("click",function(ev){var a=ev.target.closest("a,[data-share]");if(!a)return;var h=a.getAttribute("href")||"",n=document.querySelector("h1")?document.querySelector("h1").textContent:"";
if(a.hasAttribute("data-share"))return t("copy_link","個別ページ",n);if(a.dataset.act)return t(a.dataset.act,a.href,n);if(/line\\.me\\/R\\/share/.test(h))return t("line_share","個別ページ",n);if(/^https?:/.test(h)&&h.indexOf(location.hostname)<0)return t("outlink",a.href,n)})})();""" % (json.dumps(track_url), json.dumps(page))


def page(title, desc, path, body, ld, noindex=False, track_url="", tpage="", og=None, og_alt=None):
    url = SITE + path
    up = "../" * path.strip("/").count("/") + "../"
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
<link rel="icon" href="{up}img/favicon.png">
<link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">
{lds}<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<div class="top"><a href="/"><img src="{up}img/logo.webp" width="640" height="191" alt="KidsTrip（キッズトリップ）トップへ"></a><a class="btn" href="/">イベント一覧へ</a></div>
{body}
<footer><p>KidsTrip（キッズトリップ）横浜の子連れおでかけ・イベント一覧。施設・主催者の公式情報などをもとに要約しています。内容は変わることがあるので、出かける前に必ず公式ページで確認してください。</p>
<p>サイトをよくするため、押されたボタン・リンクの回数を、名前などの個人情報なしで記録しています。</p></footer>
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
    rows = "".join(f'<tr><th scope="row"><a href="/spot/{spot_ids[b["n"]]}/">{E(short(b["n"]))}</a></th>{mark(b.get("d"))}{mark(b.get("f"))}{mark(b.get("w"))}</tr>' for b in list_)
    return f'<table class="bm"><thead><tr><th>場所</th><th>おむつ替え</th><th>授乳室</th><th>お湯</th></tr></thead><tbody>{rows}</tbody></table><p class="legend">○ あり　× なし　？ 調べた範囲で確認できず</p>'


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


def event_page(e, d, spot_ids, track_url):
    path = f"event/{e['id']}/"
    ward1 = e["ward"].split("・")[0]
    title = f"{e['t']}（{e['ward']}）｜横浜の子連れイベント｜KidsTrip"
    desc = f"{when_text(e)[:60]}　{e['venue']}。{e['sum']}"[:120]
    area = e.get("area") or ""
    babies = d["baby"].get(area, [])
    ch, cld = crumbs([("トップ", "/"), ("イベント", "/"), (e["t"], "")])
    chips = "".join(f"<li>{E(x)}</li>" for x in [
        {"free": "無料", "admission": "入園料のみ", "paid": "有料"}.get(e["price"], "料金要確認"), e["ageText"], e["place"], d["rain"].get(e["rain"], "")] if x)
    resv = f'<a class="btn" data-act="resv" href="{E(e["resvUrl"])}" target="_blank" rel="noopener">予約ページへ</a>' if e.get("resvUrl") else ""
    url = SITE + path
    share_text = f"【{e['t']}】\n{when_text(e)}　{e['time']}\n場所：{e['ward']}・{e['venue']}\n{url}"
    others = [x for x in d["events"] if x.get("area") == area and area and x["id"] != e["id"]][:8]
    body = f"""{ch}
<article class="card">
<h1>{E(e['t'])}</h1>
<ul class="chips">{chips}</ul>
<table class="info">
<tr><th>日にち</th><td>{E(when_text(e))}</td></tr>
<tr><th>時間</th><td>{E(e['time'])}</td></tr>
<tr><th>場所</th><td>{E(e['ward'])}・{E(e['venue'])}</td></tr>
<tr><th>料金</th><td>{E(e['priceText'])}</td></tr>
<tr><th>対象</th><td>{E(e['ageText'])}</td></tr>
<tr><th>予約</th><td>{E(e['resvText'])}</td></tr>
<tr><th>雨の日</th><td>{E(d['rain'].get(e['rain'], ''))}（{E(e['rainText'])}）</td></tr>
</table>
<p class="sum">{E(e['sum'])}</p>
{f'<p class="tip">💡 {E(e["tip"])}</p>' if e.get('tip') else ''}
<p class="small">{("情報の時点：" + E(e["asof"]) + "　") if e.get("asof") else ""}出典：{E(e['src'])}</p>
<div class="btns"><a class="btn main" data-act="official" href="{E(e['url'])}" target="_blank" rel="noopener">公式ページで確認</a>{resv}
<a class="btn" href="/?e={E(e['id'])}">一覧で見る（行き方・近くのごはん）</a>
<button type="button" class="btn" data-share="1">🔗 リンクを送る・コピー</button>
<a class="btn line" href="{E(line_url(share_text))}" target="_blank" rel="noopener">LINEで送る</a></div>
</article>
{f'<h2>近くのおむつ替え・授乳室・お湯（{E(d["areas"].get(area, ""))}）</h2>' + matrix(babies, spot_ids) if babies else ''}
{('<h2>近くのほかのイベント</h2><ul class="links">' + ''.join(f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(when_text(x)[:30])}）</li>' for x in others) + '</ul>') if others else ''}
"""
    ld = [cld]
    if e["kind"] == "limited" and e["days"]:
        days = sorted(iso(k) for k in e["days"])
        start = days[0].isoformat()
        if len(days) == 1 and isinstance(e.get("start"), int) and 0 < e["start"] < 1440 and re.search(r"\d", e["time"]):
            start += "T%02d:%02d:00+09:00" % divmod(e["start"], 60)
        ev = {"@context": "https://schema.org", "@type": "Event", "name": e["t"], "startDate": start, "endDate": days[-1].isoformat(),
              "eventStatus": "https://schema.org/EventCancelled" if e.get("cancelled") else "https://schema.org/EventScheduled",
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "location": {"@type": "Place", "name": e["venue"], "address": {"@type": "PostalAddress", "addressLocality": "横浜市" + ward1, "addressRegion": "神奈川県", "addressCountry": "JP"}},
              "description": e["sum"], "image": [SITE + "img/ogp.jpg"], "url": url, "isAccessibleForFree": e["price"] == "free", "inLanguage": "ja"}
        ld.append(ev)
    elif e["kind"] == "ongoing":
        # 通年の施設・遊び場・公園：Event ではなく場所として出す（公園は Park）
        typ = "Park" if re.search(r"公園|広場|ふるさと村", e["t"]) and e.get("place", "").startswith("屋外") else "TouristAttraction"
        pl = {"@context": "https://schema.org", "@type": typ, "name": e["t"], "description": e["sum"], "url": url, "image": [SITE + "img/ogp.jpg"],
              "address": {"@type": "PostalAddress", "streetAddress": e["venue"], "addressLocality": "横浜市" + ward1, "addressRegion": "神奈川県", "addressCountry": "JP"},
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
    has = [n for n, v in (("おむつ替え", b.get("d")), ("授乳室", b.get("f")), ("調乳のお湯", b.get("w"))) if v is True]
    title = f"{short(b['n'])}の授乳室・おむつ替え・お湯｜KidsTrip"
    desc = f"{short(b['n'])}（{d['areas'].get(area, '')}）の赤ちゃん設備。" + ("・".join(has) + "あり。" if has else "") + (b.get("where") or "")
    ch, cld = crumbs([("トップ", "/"), ("ごはん・おむつ", "/#foodall"), (short(b["n"]), "")])
    evs = [x for x in d["events"] if x.get("area") == area][:10]
    near = [x for x in d["baby"].get(area, []) if x["n"] != b["n"]]
    ex = "".join(f"<li>{E(x)}</li>" for x in b.get("ex") or [])
    body = f"""{ch}
<article class="card">
<h1>{E(b['n'])}の授乳室・おむつ替え・お湯</h1>
<table class="bm"><thead><tr><th>場所</th><th>おむつ替え</th><th>授乳室</th><th>お湯</th></tr></thead><tbody><tr><th>{E(short(b['n']))}</th>{mark(b.get('d'))}{mark(b.get('f'))}{mark(b.get('w'))}</tr></tbody></table>
<p class="legend">○ あり　× なし　？ 調べた範囲で確認できず</p>
<table class="info"><tr><th>場所</th><td>{E(b.get('where'))}</td></tr><tr><th>エリア</th><td>{E(d['areas'].get(area, ''))}</td></tr></table>
{f'<ul class="chips">{ex}</ul>' if ex else ''}
<p class="sum">{E(b.get('note'))}</p>
<p class="small">出典：{E(b.get('src'))}</p>
<div class="btns"><a class="btn main" data-act="official" href="{E(b.get('url'))}" target="_blank" rel="noopener">公式ページで確認</a>
<a class="btn" href="https://www.google.com/maps/search/?api=1&amp;query={E(short(b['n']))}" target="_blank" rel="noopener">地図で見る</a>
<button type="button" class="btn" data-share="1">🔗 リンクを送る・コピー</button></div>
</article>
{('<h2>同じエリアのほかの赤ちゃん設備</h2>' + matrix(near, spot_ids)) if near else ''}
{('<h2>このあたりのイベント</h2><ul class="links">' + ''.join(f'<li><a href="/event/{x["id"]}/">{E(x["t"])}</a>（{E(when_text(x)[:30])}）</li>' for x in evs) + '</ul>') if evs else ''}
"""
    return path, page(title, desc, path, body, [cld], track_url=track_url, tpage=path), b["n"]


def ended_page(kind, pid, name):
    path = f"{kind}/{pid}/"
    what = "イベント" if kind == "event" else "施設の情報"
    body = f"""<article class="card"><p class="ended">この{what}の掲載は終わりました</p><h1>{E(name)}</h1>
<p>開催が終わったか、情報を確かめられなくなったため、一覧から外しました。いま行けるイベントや、赤ちゃん設備のある場所はトップから探せます。</p>
<div class="btns"><a class="btn main" href="/">いまのイベントを見る</a><a class="btn" href="/#foodall">ごはん・おむつを見る</a></div></article>"""
    return path, page(f"{name}（掲載終了）｜KidsTrip", f"{name}の掲載は終わりました。いまのイベントはKidsTripのトップから探せます。", path, body, [], noindex=True)


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
<p>各ページの文章は、元のページをもとにこのサイトが短くまとめたものです。必ず元のページへのリンクを付けています。内容は予告なく変わったり、中止になったりすることがあります。出かける前に、必ず公式ページで最新の情報を確かめてください。このサイトの情報を使って生じた損害について、運営者は責任を負いかねます。</p>
<h2>文章と画像の扱い</h2>
<p>他のサイトの文章を長く写したり、写真を転載したりはしていません。このサイトの文章・イラストを使いたいときは、お問い合わせからご連絡ください。</p>
<h2>投稿の扱い</h2>
<p>いまは、このサイトで投稿を受け付けていません。設備の情報の追加・訂正は、お問い合わせフォームからお送りください。いただいた情報は、確かめたうえで「利用者の情報（○年○月）」として載せることがあります。送ってくださった方の名前などは載せません。事実と違うもの、ほかの人の権利を傷つけるもの、宣伝だけのものは載せません。</p>
<h2>使われ方の記録</h2>
<p>サイトをよくするため、表示されたページ、検索した言葉、押されたボタン・リンク、端末の種類（スマホ・PCなど）、どのサイトから来たか、日本からのアクセスかどうか（時間帯の設定から判定）を記録しています。名前・メールアドレス・正確な位置などの個人情報は記録しません。Cookieは使わず、同じ人の訪問をまとめて数えるために、ランダムな番号だけをブラウザに保存しています。「近くで探す」の現在地は、画面の中で距離を計算するためだけに使い、記録するのは「横浜市のあたり」などの大まかな区分だけです。</p>
<h2>お問い合わせ・掲載のご相談</h2>
<p>イベント情報の追加・訂正、掲載や協賛のご相談、サイトへのご質問は、お問い合わせフォームからどうぞ（Googleアカウントでのログインが必要です）。</p>
<div class="btns"><a class="btn main" href="FORM_URL" target="_blank" rel="noopener">お問い合わせフォーム</a><a class="btn" href="/">イベント一覧へ</a><a class="btn" href="/en/">English</a></div>
</article>"""


def about_page(track_url, form_url):
    path = "about/"
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "name": "KidsTrip について", "url": SITE + path, "inLanguage": "ja",
          "publisher": {"@type": "Organization", "name": "KidsTrip", "url": SITE, "logo": SITE + "img/logo.webp"}}
    return path, page("このサイトについて｜KidsTrip（キッズトリップ）", "KidsTrip（キッズトリップ）の運営方針。情報の集め方と出典、内容の扱い、使われ方の記録、お問い合わせについて。",
                      path, ABOUT_BODY.replace("FORM_URL", E(form_url)), [ld], track_url=track_url, tpage=path)


def main():
    d = load_data()
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = TRACK_URL_RE.search(src)
    track_url = m.group(1) if m else ""
    fm = re.search(r'class="contactbtn" href="([^"]+)"', src)
    ap, ah = about_page(track_url, fm.group(1) if fm else "/")
    os.makedirs(os.path.join(ROOT, ap), exist_ok=True)
    open(os.path.join(ROOT, ap, "index.html"), "w", encoding="utf-8").write(ah)
    man = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"event": {}, "spot": {}}
    # 施設（BABY）：名前ごとに1ページ。最初に出てきたエリアを使う
    spots, spot_ids = {}, {}
    for area, lst in d["baby"].items():
        for b in lst:
            if b["n"] not in spots:
                spots[b["n"]] = (b, area)
                spot_ids[b["n"]] = hash_id(b["n"])
    built = {"event": {}, "spot": {}}
    for e in d["events"]:
        path, htmltext, name = event_page(e, d, spot_ids, track_url)
        built["event"][e["id"]] = (path, htmltext, name)
    for n, (b, area) in spots.items():
        path, htmltext, name = spot_page(b, area, d, spot_ids, track_url)
        built["spot"][spot_ids[n]] = (path, htmltext, name)
    today = TODAY.isoformat()
    new_man = {"event": {}, "spot": {}}
    for kind in ("event", "spot"):
        for pid, (path, htmltext, name) in built[kind].items():
            h = hashlib.sha1(re.sub(r"情報の時点：[^<]*", "", htmltext).encode()).hexdigest()[:12]
            old = man.get(kind, {}).get(pid, {})
            lm = old.get("lastmod", today) if old.get("hash") == h and not old.get("ended") else today
            new_man[kind][pid] = {"name": name, "hash": h, "lastmod": lm, "added": old.get("added") or (old.get("lastmod") if old else today)}
            out = os.path.join(ROOT, path, "index.html")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(htmltext)
        for pid, old in man.get(kind, {}).items():  # 一覧から外れたもの
            if pid in built[kind]:
                continue
            path, htmltext = ended_page(kind, pid, old.get("name", ""))
            out = os.path.join(ROOT, path, "index.html")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(htmltext)
            new_man[kind][pid] = dict(old, ended=True, lastmod=old.get("lastmod", today) if old.get("ended") else today)
    new_man["og"], og_made = render_og(d["events"], man.get("og", {}))
    json.dump(new_man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

    # sitemap
    urls = [(SITE, today, "daily"), (SITE + "en/", man.get("_en", today), "weekly"), (SITE + "about/", "2026-11-13", "monthly")]
    for kind in ("event", "spot"):
        for pid, v in sorted(new_man[kind].items()):
            if not v.get("ended"):
                urls.append((f"{SITE}{kind}/{pid}/", v["lastmod"], "weekly"))
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{u}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq></url>\n" for u, lm, cf in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)

    # index.html：ページへのリンク一覧と、構造化データ（ItemList・Organization）
    ev_live = [e for e in d["events"]]
    links = ('<details class="fold pagelinks"><summary>イベント・施設のページ一覧</summary><div class="fbody">'
             '<h3 class="fsum-static">イベント</h3><ul class="plinks">' + "".join(f'<li><a href="/event/{e["id"]}/">{E(e["t"])}</a></li>' for e in ev_live) + "</ul>"
             '<h3 class="fsum-static">赤ちゃん設備のある施設</h3><ul class="plinks">' + "".join(f'<li><a href="/spot/{spot_ids[n]}/">{E(short(n))}</a></li>' for n in spots) + "</ul></div></details>")
    item_list = {"@context": "https://schema.org", "@type": "ItemList", "name": "横浜の子連れイベント一覧", "numberOfItems": len(ev_live),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}event/{e['id']}/", "name": e["t"]} for i, e in enumerate(ev_live)]}
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
    newhtml = ('<section class="newev" id="newev" aria-label="新着イベント"><h2>🆕 新しく載せたイベント</h2><ul>' + "".join(nli(e) for e in newest[:5]) + "</ul>"
               '<details class="fold"><summary>ほかの新着（あと' + str(len(newest[5:])) + '件）</summary><div class="fbody"><ul>' + "".join(nli(e) for e in newest[5:]) + "</ul></div></details></section>")
    src = re.sub(r"<!--NEW:START-->.*?<!--NEW:END-->", lambda _: f"<!--NEW:START-->{newhtml}<!--NEW:END-->", src, flags=re.S)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (org, item_list))
    src = re.sub(r"<!--PAGES:START-->.*?<!--PAGES:END-->", lambda _: f"<!--PAGES:START-->{links}<!--PAGES:END-->", src, flags=re.S)
    src = re.sub(r"<!--LD:START-->.*?<!--LD:END-->", lambda _: f"<!--LD:START-->{ld}<!--LD:END-->", src, flags=re.S)
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(src)
    print(f"og {og_made}  event {len(built['event'])}  spot {len(built['spot'])}  ended {sum(1 for k in ('event','spot') for v in new_man[k].values() if v.get('ended'))}  sitemap {len(urls)}")


if __name__ == "__main__":
    sys.exit(main())
