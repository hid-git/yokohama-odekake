#!/usr/bin/env python3
"""日にち・時間・料金が「未発表」「見込み」「予定」「未確認」のままのイベントを、近い日付の順に出す。
毎日の更新で、ここに出たものを会場・主催者の公式サイトのお知らせで確かめ直す（出典がカレンダーやまとめなら、会場のサイトまで行く）。
読むのは js/data.js の2つの書き方：配列の中の `{ t:"…", days:[…], … }` と、`EVENTS.push({"t": …});`（JSON）。"""
import re, json, datetime, pathlib
s = pathlib.Path(__file__).resolve().parent.parent.joinpath("js", "data.js").read_text()
today = datetime.date.today()
FLAG = re.compile(r'(未発表|未定|見込み|予定\)|（予定|分かっていません|まだ分か|未確認|開けず)')

def first_day(days):
    first = None
    for x in days:
        m = re.match(r'(\d+)/(\d+)', x)
        if not m: continue
        mo, d = int(m.group(1)), int(m.group(2))
        y = today.year + (1 if mo < today.month - 1 else 0)
        dt = datetime.date(y, mo, d)
        if dt >= today and (first is None or dt < first): first = dt
    return first

rows = {}
def add(t, days, text, url, venue):
    flag = sorted(set(FLAG.findall(text)))
    if not flag: return
    first = first_day(days)
    if days and first is None: return  # もう終わった
    rows[t] = (first or datetime.date.max, t, flag, url or "", venue or "")

# 1) 古い書き方
pat = re.compile(r'\{ t:"([^"]+)", days:\[([^\]]*)\](.*?)(?=\n  \{ t:"|\n\);)', re.S)
for m in pat.finditer(s):
    t, days, body = m.group(1), m.group(2), m.group(3)
    url = re.search(r'url:"([^"]+)"', body)
    venue = re.search(r'venue:"([^"]+)"', body)
    add(t, re.findall(r'"(\d+/\d+)"', days), body, url and url.group(1), venue and venue.group(1))

# 2) EVENTS.push({...}) の書き方（JSON）
for m in re.finditer(r'EVENTS\.push\((\{"t".*?\})\);\n', s):
    try:
        e = json.loads(m.group(1))
    except ValueError:
        continue
    text = " ".join(str(e.get(k, "")) for k in ("time", "priceText", "resvText", "ageText", "rainText", "period", "sum", "tip"))
    add(e["t"], e.get("days") or [], text, e.get("url"), e.get("venue"))

for d, t, f, u, v in sorted(rows.values()):
    print(f'{"いつでも" if d == datetime.date.max else d.strftime("%m/%d")}\t{t}\t会場：{v}\t{"・".join(f)}\t出典：{u}')
print(f"--- {len(rows)}件")
