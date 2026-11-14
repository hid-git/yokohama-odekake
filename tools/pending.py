#!/usr/bin/env python3
"""日にち・時間・料金が「未発表」「見込み」「予定」のままのイベントを、近い日付の順に出す。
毎日の更新で、ここに出たものを会場・主催者の公式サイトのお知らせで確かめ直す（出典がカレンダーやまとめなら、会場のサイトまで行く）。"""
import re, datetime, pathlib
s = pathlib.Path(__file__).resolve().parent.parent.joinpath("index.html").read_text()
today = datetime.date.today()
pat = re.compile(r'\{ t:"([^"]+)", days:\[([^\]]*)\](.*?)(?=\n  \{ t:"|\n\);)', re.S)
rows = []
for m in pat.finditer(s):
    t, days, body = m.group(1), m.group(2), m.group(3)
    flag = re.findall(r'(未発表|未定|見込み|予定\)|（予定|分かっていません|まだ分か)', body)
    if not flag: continue
    ds = re.findall(r'"(\d+)/(\d+)"', days)
    first = None
    for mo, d in ds:
        y = today.year + (1 if int(mo) < today.month - 1 else 0)
        dt = datetime.date(y, int(mo), int(d))
        if dt >= today and (first is None or dt < first): first = dt
    if ds and first is None: continue
    url = re.search(r'url:"([^"]+)"', body)
    venue = re.search(r'venue:"([^"]+)"', body)
    rows.append((first or datetime.date.max, t, sorted(set(flag)), url.group(1) if url else "", venue.group(1) if venue else ""))
rows.sort()
for d, t, f, u, v in rows:
    print(f'{"いつでも" if d == datetime.date.max else d.strftime("%m/%d")}\t{t}\t会場：{v}\t{"・".join(f)}\t出典：{u}')
print(f"--- {len(rows)}件")
