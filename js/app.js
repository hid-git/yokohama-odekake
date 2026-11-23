// KidsTrip の動きのコード。データ（EVENTS・BABY など）は index.html の中にある。
// index.html を読み込んだあとに defer で動く。中身を変えたら tools/build_pages.py が ?v= を付け直す。
function band(t){ return t >= 25 ? 5 : t >= 20 ? 4 : t >= 16 ? 3 : t >= 11 ? 2 : 1; }
function figure(who, b, rain){
  const A = who === "adult";
  // 体の比率（子どもは頭が大きく、手足が短い）
  const P = A ? { hy:25, hr:11.5, sy:42, hip:88, sw:32, ww:27, lw:10.5, aw:8, gy:140 }
              : { hy:55, hr:15.5, sy:76, hip:108, sw:29, ww:27, lw:10, aw:7.5, gy:140 };
  const cx = 50, { hy, hr, sy, hip, sw, ww, lw, gy } = P;
  const C = A ? { t5:"#f2b84b", t4:"#5b8fd1", inner:"#f4efe4", t3:"#c48a5c", t2:"#6e7f5c", t1:"#34507d", pants:"#3e4a5c", shorts:"#6f86a8", hair:"#3b2b24", shoe:"#4a3b33", acc:"#b9475a" }
              : { t5:"#ff9c5b", t4:"#ef7d6b", inner:"#fff6e0", t3:"#7cb7a3", t2:"#e7b13b", t1:"#d65f5f", pants:"#4f6d8f", shorts:"#7fa3c9", hair:"#4a342a", shoe:"#e05a4f", acc:"#5b8fd1" };
  const skin = "#f3cba8", skinD = "#e2b28d", line = "rgba(40,30,25,.22)";
  const puffy = b === 1, aw = P.aw + (puffy ? 3 : b <= 2 ? 1.2 : 0);
  const top = b === 5 ? C.t5 : b === 4 ? C.t4 : C.inner;
  const outer = b === 3 ? C.t3 : b === 2 ? C.t2 : b === 1 ? C.t1 : null;
  const coat = rain && !A ? "#f2c230" : outer;           // 子どもの雨の日は黄色いレインコート
  const coatLen = rain && !A ? 12 : b === 1 ? (A ? 22 : 8) : b === 2 ? 4 : b === 3 ? (A ? 10 : 3) : 0;
  const S = (d, c, w, cap) => `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="${cap || "round"}" stroke-linejoin="round"/>`;
  const torso = (w1, w2, y1, y2, r) => `M${cx-w1/2} ${y1+r} Q${cx-w1/2} ${y1} ${cx-w1/2+r} ${y1} L${cx+w1/2-r} ${y1} Q${cx+w1/2} ${y1} ${cx+w1/2} ${y1+r} L${cx+w2/2} ${y2-3} Q${cx+w2/2} ${y2} ${cx+w2/2-3} ${y2} L${cx-w2/2+3} ${y2} Q${cx-w2/2} ${y2} ${cx-w2/2} ${y2-3}Z`;
  let g = `<ellipse cx="${cx}" cy="${gy+3}" rx="${A ? 22 : 18}" ry="3" fill="rgba(0,0,0,.08)"/>`;
  // 腕の通り道（肩→ひじ→手）。雨の日の大人は右手で傘を持つ
  const armL = [[cx-sw/2+aw/2-1, sy+aw/2], [cx-sw/2-4, (sy+hip)/2], [cx-sw/2-3, hip-2]];
  const umb = rain && A;
  const armR = umb ? [[cx+sw/2-aw/2+1, sy+aw/2], [cx+sw/2+7, (sy+hip)/2+2], [cx+sw/2+1, sy+16]]
                   : [[cx+sw/2-aw/2+1, sy+aw/2], [cx+sw/2+4, (sy+hip)/2], [cx+sw/2+3, hip-2]];
  const ap = a => `M${a[0][0]} ${a[0][1]} Q${a[1][0]} ${a[1][1]} ${a[2][0]} ${a[2][1]}`;
  const part = (a, t) => { // 二次ベジエを t で切った前半
    const [p0, p1, p2] = a, q0 = [p0[0]+(p1[0]-p0[0])*t, p0[1]+(p1[1]-p0[1])*t], q1 = [p1[0]+(p2[0]-p1[0])*t, p1[1]+(p2[1]-p1[1])*t];
    const e = [q0[0]+(q1[0]-q0[0])*t, q0[1]+(q1[1]-q0[1])*t];
    return [p0, q0, e];
  };
  // 傘（体の後ろに柄、上に布）
  if (umb) {
    const hx = armR[2][0], ux = hx, uy = 9;
    g += S(`M${hx} ${armR[2][1]+4} L${ux} ${uy}`, "#6b5a4e", 2);
    g += S(`M${hx} ${armR[2][1]+4} q0 6 -4 6`, "#6b5a4e", 2);
  }
  // 脚とくつ
  const legX = [cx - ww/4 - 0.5, cx + ww/4 + 0.5], ankle = gy - 4;
  const pantsLen = b === 5 ? (ankle - hip) * 0.38 : ankle - hip + 2;
  for (const x of legX) {
    const dx = x < cx ? -1 : 1;
    g += S(`M${x} ${hip-4} L${x+dx*0.8} ${ankle}`, skin, lw - 2.5, "butt");
    g += `<rect x="${x-lw/2}" y="${hip-6}" width="${lw}" height="${pantsLen+6}" rx="${b===5?3:2.5}" fill="${b===5?C.shorts:C.pants}"/>`;
    if (b < 5) g += `<line x1="${x-lw/2+0.5}" y1="${hip+pantsLen-1.5}" x2="${x+lw/2-0.5}" y2="${hip+pantsLen-1.5}" stroke="${line}"/>`;
    const boot = rain && !A;
    if (boot) g += `<rect x="${x-lw/2-0.5}" y="${ankle-11}" width="${lw+1}" height="13" rx="2.5" fill="#f2c230"/><line x1="${x-lw/2}" y1="${ankle-9}" x2="${x+lw/2}" y2="${ankle-9}" stroke="rgba(0,0,0,.15)"/>`;
    g += `<path d="M${x-lw/2-0.5+(dx>0?0:-2)} ${gy+1} Q${x-lw/2-0.5+(dx>0?0:-2)} ${ankle-1} ${x} ${ankle-1} Q${x+lw/2+0.5+(dx>0?2:0)} ${ankle-1} ${x+lw/2+0.5+(dx>0?3:0)} ${gy+1}Z" fill="${boot ? "#e2ad1c" : C.shoe}"/>`;
    if (!boot) g += `<rect x="${x-lw/2-0.5+(dx>0?0:-2)}" y="${gy}" width="${lw+3.5}" height="1.6" rx=".8" fill="rgba(255,255,255,.55)"/>`;
  }
  // 腕（素肌→袖）
  const sleeveT = b === 5 ? 0.28 : 0.86;
  for (const a of [armL, armR]) {
    g += S(ap(a), skin, P.aw - 1);
    g += `<circle cx="${a[2][0]}" cy="${a[2][1]+1}" r="${P.aw*0.48}" fill="${skin}"/>`;
    g += S(ap(part(a, sleeveT)), top, P.aw);
  }
  // 胴（中の服）
  g += `<path d="${torso(sw, ww, sy, hip, 7)}" fill="${top}"/>`;
  if (!coat) { // えり元
    g += b === 5 ? `<path d="M${cx-5} ${sy} q5 5 10 0" fill="none" stroke="${line}" stroke-width="1.4"/>`
                 : `<path d="M${cx-5.5} ${sy} l5.5 5 l5.5 -5" fill="${C.inner}" stroke="${line}" stroke-width=".8"/>`;
    if (b === 5 && !A) g += `<circle cx="${cx-6}" cy="${sy+12}" r="3" fill="#fff" opacity=".55"/><circle cx="${cx+5}" cy="${sy+16}" r="2" fill="#fff" opacity=".55"/>`;
  }
  // 上着
  if (coat) {
    const cw1 = sw + (puffy ? 6 : 3), cw2 = ww + (puffy ? 8 : 4) + (rain && !A ? 6 : 0), cy2 = hip + coatLen;
    for (const a of [armL, armR]) {
      g += S(ap(part(a, 0.9)), coat, aw + 1.5);
      const e = part(a, 0.9)[2];
      if (puffy) g += `<circle cx="${e[0]}" cy="${e[1]+2}" r="${P.aw*0.62}" fill="${C.acc}"/>`; // 手ぶくろ
    }
    if (puffy) for (const a of [armL, armR]) for (const t of [0.35, 0.62]) { const p = part(a, t)[2]; g += `<line x1="${p[0]-aw/2}" y1="${p[1]}" x2="${p[0]+aw/2}" y2="${p[1]}" stroke="rgba(255,255,255,.3)" stroke-width="1.2"/>`; }
    if (b === 2 && !(rain && !A)) g += `<path d="M${cx-12} ${sy+3} q12 -12 24 0 q-12 5 -24 0z" fill="${coat}" stroke="${line}" stroke-width=".8"/>`; // フード
    g += `<path d="${torso(cw1, cw2, sy - 1, cy2, puffy ? 10 : 8)}" fill="${coat}"/>`;
    if (puffy) { // ダウンのキルト
      for (let i = 1; i < 5; i++) { const y = sy + (cy2 - sy) * i / 5; g += `<path d="M${cx-cw2/2+1.5} ${y} q${cw2/4} 2.5 ${cw2/2-1.5} 0 q${cw2/4} 2.5 ${cw2/2-1.5} 0" fill="none" stroke="rgba(255,255,255,.3)" stroke-width="1.3"/>`; }
      g += `<line x1="${cx}" y1="${sy+2}" x2="${cx}" y2="${cy2-1}" stroke="rgba(0,0,0,.25)" stroke-width="1.2"/>`;
    } else if (b === 3 && !(rain && !A)) { // カーディガン：前を開けて中が見える
      g += `<path d="M${cx-4} ${sy-1} L${cx-2} ${cy2} L${cx+2} ${cy2} L${cx+4} ${sy-1}Z" fill="${top}"/>`;
      g += `<path d="M${cx-4} ${sy-1} L${cx-2} ${cy2}" stroke="${line}" fill="none"/><path d="M${cx+4} ${sy-1} L${cx+2} ${cy2}" stroke="${line}" fill="none"/>`;
      for (let i = 0; i < 3; i++) g += `<circle cx="${cx-4.6}" cy="${sy+9+i*((cy2-sy-14)/2)}" r="1.1" fill="rgba(0,0,0,.3)"/>`;
    } else { // ジャンパー・レインコート：ファスナーとポケット
      g += `<line x1="${cx}" y1="${sy+1}" x2="${cx}" y2="${cy2-1}" stroke="rgba(0,0,0,.22)" stroke-width="1.2"/>`;
      const py = cy2 - (A ? 16 : 13);
      g += `<path d="M${cx-cw2/2+4} ${py} h7" stroke="rgba(0,0,0,.2)" stroke-width="1.2"/><path d="M${cx+cw2/2-11} ${py} h7" stroke="rgba(0,0,0,.2)" stroke-width="1.2"/>`;
      if (rain && !A) for (let i = 0; i < 3; i++) g += `<circle cx="${cx+3}" cy="${sy+7+i*9}" r="1.2" fill="#c99a14"/>`;
    }
  }
  // 首・頭
  g += `<rect x="${cx-3.2}" y="${hy+hr-3}" width="6.4" height="${sy-hy-hr+4}" fill="${skinD}"/>`;
  if (rain && !A) g += `<circle cx="${cx}" cy="${hy+1}" r="${hr+3.5}" fill="#f2c230"/>`; // フード（後ろ）
  g += `<circle cx="${cx-hr+0.5}" cy="${hy+2}" r="2.6" fill="${skinD}"/><circle cx="${cx+hr-0.5}" cy="${hy+2}" r="2.6" fill="${skinD}"/>`; // 耳
  g += `<circle cx="${cx}" cy="${hy}" r="${hr}" fill="${skin}"/>`;
  // 髪
  g += A ? `<path d="M${cx-hr-0.5} ${hy+2} C${cx-hr-1} ${hy-hr*1.42} ${cx+hr+1} ${hy-hr*1.42} ${cx+hr+0.5} ${hy+2} C${cx+hr*0.7} ${hy-hr*0.35} ${cx-hr*0.1} ${hy-hr*0.55} ${cx-hr*0.55} ${hy-hr*0.25} C${cx-hr*0.75} ${hy-hr*0.05} ${cx-hr*0.9} ${hy+0.5} ${cx-hr-0.5} ${hy+2}Z" fill="${C.hair}"/>`
         : `<path d="M${cx-hr-0.5} ${hy+3} C${cx-hr-1.5} ${hy-hr*1.45} ${cx+hr+1.5} ${hy-hr*1.45} ${cx+hr+0.5} ${hy+3} Q${cx+hr*0.6} ${hy-hr*0.3} ${cx+hr*0.25} ${hy-hr*0.38} Q${cx} ${hy-hr*0.2} ${cx-hr*0.2} ${hy-hr*0.38} Q${cx-hr*0.6} ${hy-hr*0.3} ${cx-hr-0.5} ${hy+3}Z" fill="${C.hair}"/>`;
  // 顔
  const ey = hy + hr * (A ? 0.12 : 0.2), ex = hr * (A ? 0.4 : 0.38);
  g += `<ellipse cx="${cx-ex}" cy="${ey}" rx="1.4" ry="${A ? 1.7 : 2}" fill="#2b2220"/><ellipse cx="${cx+ex}" cy="${ey}" rx="1.4" ry="${A ? 1.7 : 2}" fill="#2b2220"/>`;
  if (!A) g += `<circle cx="${cx-ex+0.5}" cy="${ey-0.7}" r=".5" fill="#fff"/><circle cx="${cx+ex+0.5}" cy="${ey-0.7}" r=".5" fill="#fff"/>`;
  g += `<path d="M${cx-3} ${hy+hr*0.5} q3 ${A ? 2.5 : 3.2} 6 0" stroke="#a5523d" stroke-width="1.3" fill="${A ? "none" : "#e37b6c"}" stroke-linecap="round"/>`;
  g += `<circle cx="${cx-hr*0.62}" cy="${hy+hr*0.45}" r="${A ? 1.8 : 2.4}" fill="#f4a3a0" opacity="${A ? .4 : .7}"/><circle cx="${cx+hr*0.62}" cy="${hy+hr*0.45}" r="${A ? 1.8 : 2.4}" fill="#f4a3a0" opacity="${A ? .4 : .7}"/>`;
  // 小物
  if (rain && !A) g += `<path d="M${cx-hr-3.5} ${hy+1} A${hr+3.5} ${hr+3.5} 0 0 1 ${cx+hr+3.5} ${hy+1} Q${cx} ${hy-hr*0.75} ${cx-hr-3.5} ${hy+1}Z" fill="#f2c230"/>`; // フードのふち
  else if (b === 5) g += A
    ? `<ellipse cx="${cx}" cy="${hy-hr*0.5}" rx="${hr*1.7}" ry="${hr*0.3}" fill="#e8d6a8"/><path d="M${cx-hr*0.9} ${hy-hr*0.5} q0 ${-hr*0.95} ${hr*0.9} ${-hr*0.95} q${hr*0.9} 0 ${hr*0.9} ${hr*0.95}z" fill="#e8d6a8"/><rect x="${cx-hr*0.9}" y="${hy-hr*0.78}" width="${hr*1.8}" height="${hr*0.22}" fill="#c48a5c"/>`
    : `<path d="M${cx-hr*1.25} ${hy-hr*0.28} Q${cx} ${hy-hr*0.55} ${cx+hr*1.25} ${hy-hr*0.28} L${cx+hr*0.85} ${hy-hr*0.6} Q${cx+hr*0.8} ${hy-hr*1.25} ${cx} ${hy-hr*1.25} Q${cx-hr*0.8} ${hy-hr*1.25} ${cx-hr*0.85} ${hy-hr*0.6}Z" fill="#8fc6e8"/>`;
  if (b === 1 && !(rain && !A)) {
    g += `<path d="M${cx-hr*1.04} ${hy-hr*0.12} C${cx-hr*1.1} ${hy-hr*1.35} ${cx+hr*1.1} ${hy-hr*1.35} ${cx+hr*1.04} ${hy-hr*0.12}Z" fill="${C.acc}"/>`;
    g += `<rect x="${cx-hr*1.06}" y="${hy-hr*0.32}" width="${hr*2.12}" height="${hr*0.3}" rx="${hr*0.15}" fill="${C.acc}" stroke="rgba(255,255,255,.35)"/>`;
    g += `<circle cx="${cx}" cy="${hy-hr*1.08}" r="${hr*0.27}" fill="#f4efe4"/>`;
    const sc = A ? "#e3b23c" : "#f4efe4";
    g += `<path d="M${cx-hr*0.95} ${sy-3} Q${cx} ${sy+3} ${cx+hr*0.95} ${sy-3} L${cx+hr*0.95} ${sy+1} Q${cx} ${sy+7} ${cx-hr*0.95} ${sy+1}Z" fill="${sc}"/>`;
    g += `<rect x="${cx+hr*0.25}" y="${sy+1}" width="5" height="${A ? 15 : 10}" rx="2" fill="${sc}"/>`;
  }
  if (umb) { // 傘の布と、持っている手
    const ux = armR[2][0], uy = 9, R = 27;
    g += `<path d="M${ux-R} ${uy+13} Q${ux-R} ${uy-6} ${ux} ${uy-6} Q${ux+R} ${uy-6} ${ux+R} ${uy+13} q${-R/4} -4 ${-R/2} 0 q${-R/4} -4 ${-R/2} 0 q${-R/4} -4 ${-R/2} 0 q${-R/4} -4 ${-R/2} 0z" fill="#3b6fb6"/>`;
    g += `<path d="M${ux} ${uy-6} Q${ux-R/2.3} ${uy} ${ux-R/2} ${uy+13} M${ux} ${uy-6} Q${ux+R/2.3} ${uy} ${ux+R/2} ${uy+13}" stroke="rgba(255,255,255,.3)" fill="none"/>`;
    g += `<circle cx="${ux}" cy="${uy-7}" r="1.6" fill="#6b5a4e"/>`;
    g += `<circle cx="${armR[2][0]}" cy="${armR[2][1]+1}" r="${P.aw*0.5}" fill="${skin}"/>`;
  }
  if (rain) g += `<g stroke="#7ea6d8" stroke-width="1.3" stroke-linecap="round" opacity=".7"><line x1="8" y1="${A?40:62}" x2="6" y2="${A?46:68}"/><line x1="16" y1="${A?70:90}" x2="14" y2="${A?76:96}"/><line x1="90" y1="${A?62:70}" x2="88" y2="${A?68:76}"/><line x1="10" y1="${A?100:116}" x2="8" y2="${A?106:122}"/><line x1="92" y1="${A?96:104}" x2="90" y2="${A?102:110}"/></g>`;
  const label = `${A ? "大人" : "子ども"}の服装：${OUTFIT_TEXT[who][b]}${rain ? (A ? "、傘" : "、レインコートと長ぐつ") : ""}`;
  return `<svg viewBox="0 0 100 146" width="${A ? 96 : 74}" height="${A ? 140 : 108}" role="img" aria-label="${label}">${g}</svg>`;
}
function scene(label, t, extra, rain){
  const b = band(t);
  return `<div class="scene${rain ? " wet" : ""}"><p class="sl">${label}<b>${t}℃前後</b></p>
    <div class="figs"><figure>${figure("adult", b, rain)}<figcaption><b>大人</b>${OUTFIT_TEXT.adult[b]}${rain ? "＋傘" : ""}</figcaption></figure>
    <figure>${figure("child", b, rain)}<figcaption><b>子ども</b>${OUTFIT_TEXT.child[b]}${rain ? "＋レインコート・長ぐつ" : ""}</figcaption></figure></div>
    ${extra ? `<p class="sx">${extra}</p>` : ""}</div>`;
}
function skyIcons(sky){
  const parts = sky.split(/(のち|時々|一時)/);
  return parts.map(x => x === "のち" ? "→" : (x === "時々" || x === "一時") ? "/" : (SKY_ICON[x[0]] || "")).join("");
}
function isRainy(w){ return /雨|雪/.test(w.sky) || w.pop >= 50; }
function renderWeather(){
  const row = document.getElementById("wxrow"); if (!row) return;
  row.innerHTML = WX.map((w, i) => `<div class="wx${isRainy(w) ? " rainy" : ""}" data-i="${i}" title="この日の服装を見る"><span class="d ${w.w === "土" ? "sat" : w.w === "日" ? "sun" : "hol"}">${w.d} ${w.w}</span><span class="sky"><span class="ic" aria-hidden="true">${skyIcons(w.sky)}</span><span class="st">${esc(w.sky.replace(/晴/g,"晴れ").replace(/曇/g,"くもり"))}</span></span><span class="t"><b>${w.max}</b><span class="u">℃</span>/${w.min}℃</span><span class="p${w.pop >= 50 ? " hi" : ""}"><span class="pl">降水 </span>${w.pop}%</span></div>`).join("");
  const wk = WX.filter(w => WEEKENDS[0].ds.includes(w.d));
  const base = wk.length ? wk : WX.slice(0, 2);
  const hi = Math.max(...base.map(w => w.max)), lo = Math.min(...base.map(w => w.min));
  const rainy = base.filter(isRainy);
  let txt = `<b>服装の目安（${base.map(w => w.d).join("・")}）：</b>日中は${Math.min(...base.map(w => w.max))}〜${hi}℃なので長袖1枚で過ごせそうです。朝晩は${lo}℃前後まで下がるので、薄手の上着や子どもの羽織りものがあると安心です。海沿い（みなとみらい・山下公園）は風が出ると体感温度が下がります。`;
  if (rainy.length) txt += `<br><b>☔ ${rainy.map(w => w.d + "(" + w.w + ")").join("・")}は雨の予報：</b>折りたたみ傘か子どものレインコート、ベビーカーのレインカバー、足元が濡れたときの替えの靴下とタオルがあると安心。雨の日は屋内のイベントや「雨でもOK」で絞り込むのがおすすめです。`;
  else if (base.some(w => /曇/.test(w.sky))) txt += `くもりの時間は日差しがなく、予報の気温より肌寒く感じやすいので、羽織りものを一枚多めに。`;
  document.getElementById("wear").innerHTML = txt;
  row.querySelectorAll(".wx").forEach(d => d.addEventListener("click", () => { OUTFIT_DAY = +d.dataset.i; renderOutfit(); const of = document.getElementById("outfit").closest("details"); if (of) of.open = true; document.getElementById("outfit").scrollIntoView({ behavior: "smooth", block: "nearest" }); }));
  document.getElementById("wxnote").textContent = `${WX_ASOF}の予報です。予報は毎日の更新で新しくします。変わることがあるので、出かける前にも確認してください。赤い印の「雨天中止」イベントは当日の天気を確認してから出かけてください。`;
}
let OUTFIT_DAY = 0;
function renderOutfit(){
  const el = document.getElementById("outfit"); if (!el || !WX.length) return;
  if (OUTFIT_DAY >= WX.length) OUTFIT_DAY = 0;
  const w = WX[OUTFIT_DAY], rain = isRainy(w);
  const chips = WX.map((x, i) => `<button type="button" class="odchip${i === OUTFIT_DAY ? " on" : ""}${isRainy(x) ? " rainy" : ""}" data-i="${i}" aria-pressed="${i === OUTFIT_DAY}">${x.d}(${x.w}) ${skyIcons(x.sky)}</button>`).join("");
  const dayNote = rain ? `雨の予報（降水${w.pop}%）。ベビーカーはレインカバーを。替えの靴下とタオルがあると安心。` : /曇/.test(w.sky) ? "くもりで日差しが少ないので、気温より肌寒く感じやすい。羽織りを一枚多めに。" : "日なたは暖かい。脱いだ上着をしまえる袋があると楽。";
  el.innerHTML = `<h3>服装イメージ</h3><div class="odchips" role="group" aria-label="日にちを選ぶ">${chips}</div>
    <p class="odsum">${w.d}(${w.w})　${skyIcons(w.sky)} ${esc(w.sky.replace(/晴/g,"晴れ").replace(/曇/g,"くもり"))}　最高${w.max}℃／最低${w.min}℃</p>
    <div class="scenes">${scene("日中 ", w.max, dayNote, rain && !/のち雨/.test(w.sky) || /^雨/.test(w.sky))}${scene("朝・夕方・夜 ", w.min, "海沿い・花火を見るときは風で寒く感じるので、もう1枚。", rain && /のち雨|雨/.test(w.sky.split(/のち/).pop()))}</div>`;
  el.querySelectorAll(".odchip").forEach(btn => btn.addEventListener("click", () => { OUTFIT_DAY = +btn.dataset.i; renderOutfit(); }));
}
function shopHtml(sh){
  return `<div class="shop"><span class="nm"><a href="${esc(sh.url)}" target="_blank" rel="noopener">${esc(sh.n)}</a></span>
    <p class="meta">${esc(sh.kind)}・${esc(sh.hours)}（出典：${esc(sh.src)}）</p>
    <ul class="ktags">${sh.tags.map(t => `<li class="ktag">${esc(t)}</li>`).join("")}</ul>
    <p class="ds">${esc(sh.d)}</p>${asofHtml(sh.n)}<div data-spot="${esc(sh.n)}"></div></div>`;
}
function babyFoodNear(e){
  const g = venueGeo(e); if (!g) return "";
  const near = BABYFOOD_SHOPS.map(sh => ({ sh, d: distM(g, sh.g) })).filter(x => Math.round(x.d * 1.3 / 70) <= 10).sort((a, b) => a.d - b.d);
  if (!near.length) return "";
  return `<div class="bfood"><b>🥣 歩いて10分以内で離乳食が無料でもらえるお店</b><ul>${near.map(x => `<li><b>${esc(x.sh.n)}</b>　<span class="m">${esc(x.sh.d)}・会場からベビーカーで約${Math.max(1, Math.round(x.d * 1.3 / 70))}分（目安）</span></li>`).join("")}</ul><p class="note">9〜11か月ごろ向け・店内で食べるときだけ。提供の有無や中身は時期で変わることがあります。</p></div>`;
}
function kidsFoodNear(e){
  const g = venueGeo(e); if (!g) return [];
  return KIDS_SHOPS.map(sh => ({ sh, min: Math.max(1, Math.round(distM(g, sh.g) * 1.3 / 70)) })).filter(x => x.min <= 10).sort((a, b) => a.min - b.min);
}
// お店の一覧：基本はお店で食べる。テイクアウトできるかは印で出す。多いときは店名とジャンルだけにして「くわしく」で開く
function isTO(sh){ return sh.tags.some(t => /テイクアウト/.test(t)); }
function isTOonly(sh){ return sh.tags.some(t => /テイクアウトのみ/.test(t)); }
function featBadges(sh){
  const t = sh.tags.join(" "), k = sh.k || "";
  const out = [];
  if (!/記載なし|お店に確認/.test(k) && /キッズ|お子様|お子さま|子ども用ワンプレート|ハーフサイズ|子ばんざい/.test(k + " " + t)) out.push("🧒 キッズメニュー");
  if (/ベビーカー(OK|のまま|で入|ごと)/.test(t)) out.push("👶 ベビーカーOK");
  if (/お子さまシート|子ども用(の)?(いす|椅子)|キッズチェア|ベビーチェア|チャイルドシート/.test(t)) out.push("🪑 子ども用いす");
  if (/離乳食/.test(t + " " + k)) out.push("🥣 離乳食OK");
  return out.map(x => `<span class="fb">${x}</span>`).join("");
}
function toBadge(sh){ return isTOonly(sh) ? `<span class="tob only">🥡 テイクアウトのみ</span>` : isTO(sh) ? `<span class="tob">🥡 テイクアウトもOK</span>` : ""; }
function shopLi(sh, detail, compact){
  const head = `<b>${esc(sh.n)}</b>${sh.gen ? `<span class="gen">${esc(sh.gen)}</span>` : ""}<span class="fbs">${featBadges(sh)}${toBadge(sh)}</span>`;
  return compact ? `<li class="kl">${head}<details class="kd"><summary>くわしく</summary><span class="m">${detail}</span></details></li>` : `<li class="kl">${head}<br><span class="m">${detail}</span></li>`;
}
function shopSort(list, key){ return list.slice().sort((a, b) => (isTOonly(key ? key(a) : a) - isTOonly(key ? key(b) : b))); }
function kidsFoodHtml(e){
  const near = kidsFoodNear(e);
  if (!near.length) { const g = venueGeo(e); if (!g) return ""; const u = `https://www.google.com/maps/search/${encodeURIComponent("キッズメニュー")}/@${g[0]},${g[1]},16z`; return `<div class="bfood kfood"><b>🍽 子連れで入りやすいお店</b><p class="note">このあたりはまだ調べ中です。会場の中のレストランやフードコートも見てみてください。<a href="${esc(u)}" target="_blank" rel="noopener">会場のまわりの「キッズメニュー」を地図で探す</a>　行ったお店の情報をお問い合わせから送ってもらえると、確かめて載せます。</p></div>`; }
  const cp = near.length > SHOP_COMPACT, list = shopSort(near, x => x.sh);
  return `<div class="bfood kfood"><b>🍽 歩いて10分以内の子連れで入りやすいお店（${near.length}店）</b><ul>${list.map(x => shopLi(x.sh, `${esc(x.sh.k)}<br>${x.sh.tags.map(t=>`<span class="ktag">${esc(t)}</span>`).join("")}<br>会場からベビーカーで約${x.min}分（目安）（${esc(x.sh.src)}）`, cp)).join("")}</ul><div class="note">メニュー・値段は記事掲載時点のものです。行く前にお店の情報を確認してください。</div></div>`;
}
function foodCourtNear(e){
  const g = venueGeo(e); if (!g) return [];
  return FOOD_COURTS.map(c => ({ c, min: Math.max(1, Math.round(distM(g, c.g) * 1.3 / 70)) })).filter(x => x.min <= 10).sort((a, b) => a.min - b.min);
}
function foodCourtHtml(e){
  const near = foodCourtNear(e); if (!near.length) return "";
  return `<div class="bfood fcourt"><b>🍴 歩いて10分以内のフードコート</b><ul>${near.map(x => `<li><b>${esc(x.c.n)}</b>　<span class="m">${esc(x.c.f)}${x.c.seat ? "・" + esc(x.c.seat) : ""}<br>${x.c.tags.map(t => `<span class="ktag">${esc(t)}</span>`).join("")}<br>会場からベビーカーで約${x.min}分（目安）（${esc(x.c.src)}）</span></li>`).join("")}</ul></div>`;
}
function famiresHtml(e){
  const g = venueGeo(e); if (!g) return "";
  const q = (w) => `https://www.google.com/maps/search/${encodeURIComponent(w)}/@${g[0]},${g[1]},16z`;
  const anyNear = babyFoodNear(e) || kidsFoodNear(e).length || foodCourtNear(e).length;
  return `<details class="food fami"><summary>${anyNear ? "近くのファミレス・フードコート・離乳食・キッズメニュー" : "近くのごはんを地図で探す"}${babyFoodNear(e) ? "（🥣無料あり）" : ""}${kidsFoodNear(e).length ? "（🍽子連れOKのお店あり）" : ""}${foodCourtNear(e).length ? "（🍴フードコートあり）" : ""}</summary>
    ${babyFoodNear(e)}
    ${foodCourtHtml(e)}
    ${kidsFoodHtml(e)}
    <p class="note">会場のまわりのファミレスを地図で探せます：<a href="${esc(q("ファミレス"))}" target="_blank" rel="noopener">ファミレス</a>　<a href="${esc(q("ガスト"))}" target="_blank" rel="noopener">ガスト</a>　<a href="${esc(q("デニーズ"))}" target="_blank" rel="noopener">デニーズ</a>　<a href="${esc(q("サイゼリヤ"))}" target="_blank" rel="noopener">サイゼリヤ</a>　<a href="${esc(q("バーミヤン"))}" target="_blank" rel="noopener">バーミヤン</a>　<a href="${esc(q("スープストックトーキョー"))}" target="_blank" rel="noopener">スープストック</a>　<a href="${esc(q("和食さと"))}" target="_blank" rel="noopener">和食さと</a></p>
  </details>`;
}
function clothesKinds(c){ return c.kinds ? c.kinds.map(k => `<span class="ktag">${k === "ベビー" ? "👶" : k === "靴" ? "👟子どもの" : "🧒"}${esc(k)}</span>`).join("") : `<span class="ktag">取り扱いは公式で未確認</span>`; }
function clothesNear(g){
  if (!g || typeof CLOTHES === "undefined") return [];
  return CLOTHES.filter(c => c.g).map(c => ({ c, min: Math.max(1, Math.round(distM(g, c.g) * 1.3 / 70)) })).filter(x => x.min <= 15).sort((a, b) => a.min - b.min);
}
function clothesHtml(e){
  const near = clothesNear(venueGeo(e)); if (!near.length) return "";
  return `<details class="food clothes"><summary>👕 歩いて15分以内でベビー服・子ども服・靴が買えるお店（${near.length}店）</summary><ul>${near.map(x => `<li><a href="${esc(x.c.url)}" target="_blank" rel="noopener"><b>${esc(x.c.n)}</b></a> ${clothesKinds(x.c)}　<span class="m">${esc(x.c.addr)}／${esc(x.c.hours)}<br>会場からベビーカーで約${x.min}分（目安）</span></li>`).join("")}</ul><p class="note">急なおもらし・汚れの着替えや、靴を忘れたときに。時間は直線距離からのめやすです。在庫・営業時間はお店で確かめてください（出典：各チェーン公式の店舗検索）。</p></details>`;
}
function clothesListHtml(){
  if (typeof CLOTHES === "undefined" || !CLOTHES.length) return "";
  const by = {}; CLOTHES.forEach(c => (by[c.ward] = by[c.ward] || []).push(c));
  return `<details class="fold clothes"><summary>👕 ベビー服・子ども服・靴が買えるお店（${CLOTHES.length}店）</summary><div class="fbody">
    ${Object.entries(by).sort((p, q) => p[0].localeCompare(q[0], "ja")).map(([w, l]) => `<p><b>${esc(w)}</b></p><ul class="flist">${l.map(c => `<li><a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.n)}</a> ${clothesKinds(c)}　<span class="small">${esc(c.addr)}／${esc(c.hours)}</span></li>`).join("")}</ul>`).join("")}
    <p class="small">いまは西松屋・アカチャンホンポ・バースデイ・しまむら・プティマイン・ブリーズ・ユニクロ（ベビーを置いているお店）・GU（キッズのみ）・ベビーザらス・無印良品（こども服のあるお店）の横浜市内のお店と、みなとみらいのモール（MARK IS・コレットマーレ・東急スクエア）の子ども服のお店です。住所・営業時間は各チェーンやモールの公式ページから（2026年11月17日確認）。年末年始などは変わることがあるので、行く前にお店で確かめてください。</p></div></details>`;
}
function foodHtml(e){
  const k = FOOD_OF[e.t]; if (!k) return "";
  const a = FOOD[k]; if (!a || !a.shops.length) return "";
  return `<details class="food"><summary>近くのごはん（${esc(a.name)}・${a.shops.length}件）</summary>
    <p class="note">${esc(a.note)}</p><div class="shops">${a.shops.map(shopHtml).join("")}</div></details>`;
}
function nearestArea(g){
  let best = null, bd = Infinity;
  for (const A of FOOD_AREAS) { if (A.fallback) continue; const d = distM(A.c, g); if (d <= A.r && d < bd) { bd = d; best = A.k; } }
  if (!best) { const F = FOOD_AREAS.find(A => A.fallback); if (F && distM(F.c, g) <= F.r) best = F.k; }
  return best;
}
let FOOD_PICK = "all";
function renderFoodAll(){
  const areas = FOOD_AREAS.map(A => {
    const f = FOOD[A.k] || {};
    const kids = typeof KIDS_SHOPS !== "undefined" ? KIDS_SHOPS.filter(x => nearestArea(x.g) === A.k) : [];
    const courts = typeof FOOD_COURTS !== "undefined" ? FOOD_COURTS.filter(x => nearestArea(x.g) === A.k) : [];
    const free = typeof BABYFOOD_SHOPS !== "undefined" ? BABYFOOD_SHOPS.filter(x => x.g && nearestArea(x.g) === A.k) : [];
    return { k:A.k, name: f.name || A.name, note: f.note || A.note || "", shops: f.shops || [], baby: BABY[A.k] || [], kids, courts, free };
  }).filter(a => a.shops.length || a.baby.length || a.kids.length || a.courts.length || a.free.length);
  const pick = areas.some(a => a.k === FOOD_PICK) ? FOOD_PICK : "all";
  const chips = `<div class="areabar" role="group" aria-label="エリアを選ぶ"><button type="button" class="achip${pick === "all" ? " on" : ""}" data-k="all">すべて</button>${areas.map(a => `<button type="button" class="achip${pick === a.k ? " on" : ""}" data-k="${a.k}">${esc(a.name.split("（")[0].split("・").slice(0, 2).join("・"))}</button>`).join("")}</div>`;
  const li = (n, sub) => `<li><b>${esc(n)}</b>${sub ? `<br><span class="m">${sub}</span>` : ""}</li>`;
  const html = areas.filter(a => pick === "all" || a.k === pick).map(a => {
    const evs = EVENTS.filter(e => FOOD_OF[e.t] === a.k).length;
    let h = `<div class="farea" data-k="${a.k}"><h3>${esc(a.name)}</h3><p class="for">${evs ? `このエリアのイベント ${evs}件／` : ""}${esc(a.note)}</p>`;
    // 要点（データから自動で作る）
    const nm = b => b.n.replace(/[（(].*$/, "").trim(), few = xs => xs.slice(0, 3).map(nm).join("・") + (xs.length > 3 ? ` ほか${xs.length - 3}` : "");
    const hot = a.baby.filter(b => b.w === true), fed = a.baby.filter(b => b.f === true), nofed = a.baby.filter(b => b.f === false);
    const pts = [];
    // おむつ替え・授乳室・お湯は下の一覧表（○×？）で見せるので、要点には入れない
    if (a.baby.length && !hot.length) pts.push(["🍼", "調乳のお湯は確認できていません（お湯は持参が安心）"]);
    const eat = [a.courts.length ? `フードコート${a.courts.length}` : "", a.free.length ? `離乳食無料${a.free.length}` : "", a.kids.length || a.shops.length ? `子連れで入りやすいお店${a.kids.length + a.shops.length}` : ""].filter(Boolean);
    if (eat.length) pts.push(["🍽", eat.join("・")]);
    if (pts.length) h += `<ul class="points">${pts.map(([i, t]) => `<li><span class="pi">${i}</span><span>${esc(t)}</span></li>`).join("")}</ul>`;
    if (a.baby.length) h += matrixHtml(a.baby);
    h += `<details class="fold"${pick !== "all" ? " open" : ""}><summary>くわしく見る（施設${a.baby.length}・お店${a.courts.length + a.free.length + a.kids.length + a.shops.length}）</summary><div class="fbody">`;
    if (a.baby.length) h += `<p class="for"><b>おむつ替え・授乳・お湯</b></p><div class="shops">${a.baby.map(b => bspotHtml(b)).join("")}</div>`;
    if (a.courts.length) h += `<p class="for"><b>🍴 フードコート</b></p><ul class="flist">${a.courts.map(c => li(c.n, `${esc(c.f)}${c.seat ? "・" + esc(c.seat) : ""}<br>${c.tags.map(t => `<span class="ktag">${esc(t)}</span>`).join("")}（${esc(c.src)}）`)).join("")}</ul>`;
    if (a.free.length) h += `<p class="for"><b>🥣 離乳食が無料でもらえるお店</b></p><ul class="flist">${a.free.map(x => li(x.n, `${esc(x.d || "")}（${esc(x.src || "")}）`)).join("")}</ul>`;
    if (a.kids.length) h += `<p class="for"><b>🍽 子連れで入りやすいお店（${a.kids.length}店）</b></p><ul class="flist">${shopSort(a.kids).map(x => shopLi(x, `${esc(x.k)}<br>${x.tags.map(t => `<span class="ktag">${esc(t)}</span>`).join("")}（${esc(x.src)}）`, a.kids.length > SHOP_COMPACT)).join("")}</ul>`;
    if (a.shops.length) h += `<p class="for"><b>ごはん</b></p><div class="shops">${a.shops.map(shopHtml).join("")}</div>`;
    return h + `</div></details></div>`;
  }).join("");
  const el = document.getElementById("foodall");
  const sp = el.querySelector(".points.static"), spHtml = sp ? sp.outerHTML : "";
  el.innerHTML = `<h2>エリア別 赤ちゃん設備とごはん</h2>${spHtml}${mwListHtml()}${clothesListHtml()}${chips}
    <details class="fold"><summary>この一覧の見方（点線の印・情報の時点）</summary><div class="fbody"><p class="lead">おむつ替え・授乳室・調乳用のお湯がある場所と、フードコート、ベビーカーOK・キッズメニューなどが確認できたお店です。印が点線のものは、調べた範囲では確認できなかった設備です。それぞれに「情報の時点」を書いていて、1年以上前の情報や時点が分からないものは黄色で示しています。混み具合や設備は変わることがあるので、行く前に各リンク先を確認してください。</p></div></details>${html}`;
  el.querySelectorAll(".achip").forEach(btn => btn.addEventListener("click", () => { FOOD_PICK = btn.dataset.k; renderFoodAll(); }));
}
function bi(label, v){ const c = v === true ? "y" : v === false ? "n" : "u"; const t = v === null ? label + "？" : label; return `<li class="bi ${c}">${t}</li>`; }
function venueGeo(e){ const s = e.venue + " " + e.t; for (const [re, g] of VENUE_GEO) if (re.test(s)) return g; return null; }
function walkHtml(e, b){
  if (!e) return "";
  const g1 = venueGeo(e), g2 = SPOT_GEO[b.n];
  const link = `<a href="https://www.google.com/maps/dir/?api=1&travelmode=walking&origin=${encodeURIComponent(e.venue.replace(/（.*?）/g,"")+" 横浜")}&destination=${encodeURIComponent(b.n.replace(/（.*?）/g,"")+" 横浜")}" target="_blank" rel="noopener">徒歩ルートを見る</a>`;
  if (!g1 || !g2) return `<p class="walk">🚶 会場から：${link}</p>`;
  const R = 6371000, toR = x => x * Math.PI / 180;
  const dLa = toR(g2[0]-g1[0]), dLo = toR(g2[1]-g1[1]);
  const m = 2 * R * Math.asin(Math.sqrt(Math.sin(dLa/2)**2 + Math.cos(toR(g1[0]))*Math.cos(toR(g2[0]))*Math.sin(dLo/2)**2));
  const min = Math.max(1, Math.round(m * 1.3 / 70));
  const txt = m < 150 ? "会場の中か、すぐ隣" : m > 2500 ? "歩くと遠い（電車・バスで）" : `ベビーカーで約${min}分（目安）`;
  return `<p class="walk">🚶 会場から：<b>${txt}</b>　${link}</p>`;
}
let ORIGIN = ""; try { ORIGIN = localStorage.getItem("origin") || ""; } catch(_) {}
function pad(n){ return String(n).padStart(2,"0"); }
function tripDate(e){
  const d = (state.day !== "all" && e.days.includes(state.day)) ? state.day : e.days[0];
  const [mo, da] = d.split("/").map(Number); return { mo, da, label:d };
}
let ARRIVE = ""; try { ARRIVE = localStorage.getItem("arrive") || ""; } catch(_) {}
function toMin(v){ const m = /^(\d{1,2}):(\d{2})$/.exec(v || ""); return m ? (+m[1]) * 60 + (+m[2]) : null; }
function tripInner(e, k){
  const to = TRANSIT_TO[k];
  if (!ORIGIN) return `🚃 ページ上の「出発駅」を入れると、ここから${esc(to)}駅までの乗換案内（時間つき）が開けます。`;
  const { mo, da, label } = tripDate(e);
  const vague = /確認/.test(e.time) || !e.start;
  const own = toMin(ARR_BY[e.t]), all = toMin(ARRIVE);
  const t = own != null ? own : all != null ? all : (vague ? 600 : Math.max(0, e.start - 20));
  const why = own != null ? "このイベントだけ指定" : all != null ? "全体の到着時間" : vague ? "時間は仮" : "開始20分前";
  const hh = Math.floor(t/60), mi = t % 60;
  const y = `https://transit.yahoo.co.jp/search/result?from=${encodeURIComponent(ORIGIN)}&to=${encodeURIComponent(to)}&y=${dyear(mo)}&m=${pad(mo)}&d=${pad(da)}&hh=${pad(hh)}&m1=${Math.floor(mi/10)}&m2=${mi%10}&type=4&ticket=ic`;
  const g = `https://www.google.com/maps/dir/?api=1&travelmode=transit&origin=${encodeURIComponent(ORIGIN)}&destination=${encodeURIComponent(e.venue.replace(/（.*?）/g,"")+" 横浜")}`;
  return `🚃 <b>${esc(ORIGIN)} → ${esc(to)}駅</b>（${label}）<br>
    <label class="arrl">駅に着きたい時間 <input type="time" class="arr" data-title="${esc(e.t)}" value="${pad(hh)}:${pad(mi)}" step="300"></label> <span class="why">${why}</span>
    ${AFTER_BUS[k] ? `<br>そのあと：${esc(AFTER_BUS[k])}` : ""}<br>
    <a href="${esc(y)}" target="_blank" rel="noopener">この時間で乗換を調べる（Yahoo!乗換案内）</a>　<a href="${esc(g)}" target="_blank" rel="noopener">会場まで（Googleマップ）</a>`;
}
function transitHtml(e, k){
  if (!TRANSIT_TO[k]) return "";
  return `<div class="trip" data-k="${k}" data-title="${esc(e.t)}">${tripInner(e, k)}</div>`;
}
document.addEventListener("change", ev => {
  const el = ev.target; if (!el.classList || !el.classList.contains("arr")) return;
  const box = el.closest(".trip"), e = EVENTS.find(x => x.t === el.dataset.title); if (!box || !e) return;
  ARR_BY[e.t] = el.value; box.innerHTML = tripInner(e, box.dataset.k);
});
function setArrive(v){ ARRIVE = v; try { localStorage.setItem("arrive", v); } catch(_) {} render(); }
function setOrigin(v){ ORIGIN = v.trim().replace(/駅$/,""); try { localStorage.setItem("origin", ORIGIN); } catch(_) {} render(); }
function papaOf(b){ return PAPA[b.n] || { v:"unk", t:"男性トイレ・多機能トイレのどちらにあるかは未確認" }; }
function papaHtml(b){
  const p = papaOf(b);
  return `<p class="papa ${p.v}"><b>${PAPA_LABEL[p.v]}</b>　${esc(p.t)}${p.src ? `（${esc(p.src)}）` : ""}</p>`;
}
// 設備の一覧表（おむつ替え・授乳室・お湯を ○ × ？ で並べる）
function bmark(v){ return v === true ? `<td class="mk y" aria-label="あり">○</td>` : v === false ? `<td class="mk n" aria-label="なし">×</td>` : `<td class="mk u" aria-label="未確認">？</td>`; }
function matrixHtml(list){
  if (!list.length) return "";
  return `<table class="bmatrix"><thead><tr><th scope="col">場所</th><th scope="col">おむつ替え</th><th scope="col">授乳室</th><th scope="col">お湯</th><th scope="col">レンジ</th></tr></thead><tbody>${list.map(b => `<tr><th scope="row"><a href="/spot/${hashId(b.n)}/">${esc(b.n.replace(/[（(].*$/, "").trim())}</a></th>${bmark(b.d)}${bmark(b.f)}${bmark(b.w)}${bmark(b.mw === undefined ? null : b.mw)}</tr>`).join("")}</tbody></table>
    <p class="mlegend">○ あり　× なし　？ 調べた範囲で確認できず</p>`;
}
function bspotHtml(b, e){
  return `<div class="bspot${state.flags.has("papa") && papaOf(b).v === "women" ? " dim" : ""}"><span class="nm"><a href="${esc(b.url)}" target="_blank" rel="noopener">${esc(b.n)}</a></span>
    <p class="meta">${esc(b.where)}（出典：${esc(b.src)}）</p>
    <ul class="bicons">${bi("おむつ替え", b.d)}${bi("授乳室", b.f)}${bi("調乳のお湯", b.w)}${b.mw === true || b.mw === false ? bi("離乳食のレンジ", b.mw) : ""}${b.ex.map(x => `<li class="bi y">${esc(x)}</li>`).join("")}</ul>
    <p class="ds">${esc(b.note)}</p>${papaHtml(b)}${walkHtml(e, b)}${asofHtml(b.n)}<div data-spot="${esc(b.n)}"></div></div>`;
}
function babyHtml(e){
  const k = FOOD_OF[e.t]; if (!k || !BABY[k]) return "";
  let list = BABY[k].slice(); if (state.flags.has("papa")) list.sort((a, b) => PAPA_RANK[papaOf(a).v] - PAPA_RANK[papaOf(b).v]); const hot = list.filter(b => b.w === true).length;
  return `<details class="food baby"><summary>おむつ替え・授乳・お湯（${list.length}か所${hot ? `・お湯あり${hot}` : ""}）</summary>
    ${matrixHtml(list)}
    <div class="shops">${list.map(b => bspotHtml(b, e)).join("")}</div>
    <p class="note">横浜市内のハマハグ協賛店・かながわ子育て応援パスポートの協力施設では、登録証を見せるとお湯の提供や割引などのサービスが受けられることがあります（<a href="https://www.city.yokohama.lg.jp/kurashi/kosodate-kyoiku/kosodateshien/default2020091.html" target="_blank" rel="noopener">ハマハグについて</a>）。</p></details>`;
}
function hasHotWater(e){ const k = FOOD_OF[e.t]; return !!(k && BABY[k] && BABY[k].some(b => b.w === true)); }
function asofHtml(name){
  const a = ASOF[name];
  if (a === undefined) return "";
  if (a === null) return `<p class="asof old">情報の時点：不明（行く前に公式で確認を）</p>`;
  const label = a[2] || `${a[0]}年${a[1]}月`;
  const months = (NOW_Y - a[0]) * 12 + (NOW_M - a[1]);
  return months >= 12 ? `<p class="asof old">情報の時点：${label}（1年以上前の情報です。行く前に確認を）</p>`
                      : `<p class="asof">情報の時点：${label}</p>`;
}
const DATE_IDX = Object.fromEntries(DATES.map((d,i) => [d.k, i]));
// 日付の並び順（1〜3月は2027年）
function dyear(m){ return m < 4 ? 2027 : 2026; }
function dnum(k){ const [m, d] = k.split("/").map(Number); return dyear(m) * 10000 + m * 100 + d; }
function dlabel(k){ const [m, d] = k.split("/").map(Number); return `${m}/${d}(${"日月火水木金土"[new Date(dyear(m), m - 1, d).getDay()]})`; }
for (const e of EVENTS) if (/旧横ギャラリー|ANAの飛行機|熱気球/.test(e.t)) e.ride = true;
for (const e of EVENTS) if (/ズーラシア|牧場|乳しぼり|バター作り/.test(e.t)) e.animal = true;
for (const e of EVENTS) {
  if (WK[e.t]) e.wk = WK[e.t];
  if (e.paidplay) e.wk = e.wk || "毎日（施設の休館日を除く）・平日は空いていることが多い";
  if (e.wk && !e.period) e.period = "いつでも（通年の施設）";
}
for (const e of EVENTS) if (YEAREND_CLOSED[e.t]) e.closed = (e.closed || []).concat(YEAREND_CLOSED[e.t]);
for (const e of EVENTS) {
  if (e.t === "THE MOVEUM YOKOHAMA「印象派モネと浮世絵」") { e.kind = "ongoing"; e.period = "2026/10/24〜2027/3/31（11/15・11/21・12/13休館、ほかに不定休）"; e.closed = ["11/15","11/21","12/13"]; e.sum = "モネの絵画と浮世絵を大画面の映像で体験する没入型の展示。"; e.tip = "11/15・11/21・12/13は休館（横浜市観光情報サイト）。開館は平日・日祝10:30〜18:30、土・祝前日は19:30まで。チケットはオンライン3,000円・会場3,800円（現金不可）、中学生以下無料"; }
  if (e.t === "こどもの国牧場 乳しぼり体験") { e.kind = "ongoing"; e.period = "毎週土日祝"; }
  if (e.t === "こどもの国牧場 バター作り教室") { e.kind = "ongoing"; e.period = "毎週日曜"; e.only = DATES.filter(d => d.w === "日").map(d => d.k); }
  if (e.kind === "ongoing") {
    const r = RANGE[e.t] || {};
    // 会期（period の「M/D〜M/D」）から対象日を決める。from/to や RANGE があればそちらを優先
    const pm = (e.period || "").match(/^(?:(\d{4})\/)?(\d{1,2})\/(\d{1,2})〜/), qm = (e.period || "").match(/〜(?:(\d{4})\/)?(\d{1,2})\/(\d{1,2})/);
    const pnum = (y, m, d) => (y ? +y : dyear(+m)) * 10000 + (+m) * 100 + (+d);
    const lo = e.from || r.from ? dnum(e.from || r.from) : pm ? pnum(pm[1], pm[2], pm[3]) : 0;
    const hi = e.to || r.to ? dnum(e.to || r.to) : qm ? pnum(qm[1], qm[2], qm[3]) : 99999999;
    let ds = DATES.filter(d => dnum(d.k) >= lo && dnum(d.k) <= hi).map(d => d.k);
    if (e.only) ds = e.only;
    if (e.closed) ds = ds.filter(d => !e.closed.includes(d));
    e.days = ds;
    if (!e.period) e.period = r.to ? `〜${r.to}` : "対象期間の週末・祝日はすべて";
  }
}
Object.assign(FOOD_OF, {
  "ヨコハマミライト2026（横浜駅東口〜みなとみらいのイルミネーション）":"mm", "本は港（日本大通りのブックマーケット・絵本の朗読会も）":"yamashita",
  "子ども縁日（ワールドポーターズ屋上）":"yamashita", "チョコクロ キッズ手作り体験教室（ワールドポーターズ）":"yamashita", "クリスマスリースづくり（ワールドポーターズ）":"yamashita", "防災フェス（消防車の展示・子ども防火服）":"yamashita",
  "抱っこdeシネマ（赤ちゃん連れで見られる映画の回・MARK IS 5F）":"mm",
  "みんなの庭 秋の収穫体験（東京ガスのキッチンで試食・MARK IS）":"mm", "みんなの庭 秋のミニランタン作り（MARK IS）":"mm", "みんなの庭 植物のクリスマスオーナメント作り（MARK IS）":"mm",
  "アドベンチャーアイランド ららぽーと横浜":"lalaport", "ディノグランプリ！（恐竜をぬって走らせるデジタル体験）":"lalaport",
  "よこはまコスモワールド（入園無料・キッズカーニバル・ゾーン）":"mm", "横浜美術館「じゆうエリア」（無料・親子で絵本の「くつぬぎスポット」）":"mm",
  "トレッサ横浜 無料キッズスペース（駐車場も無料）":"tressa", "トレッサ横浜 遊Kids愛ランド／キンダープラッツ":"tressa", "わくわくアイスワールド（トレッサ横浜の屋内スケートリンク）":"tressa",
  "名探偵コナン 芸術花火2026":"yamashita", "Vintage & Artisan Market in みなとみらい（蚤の市）":"mm",
  "こどもの国 冬のブラスフェス":"kodomonokuni", "こどもの国 もみじのかざぐるま":"kodomonokuni", "こどもの国 自然スタンプビンゴ＜紅葉バージョン＞":"kodomonokuni",
  "こどもの国 工作教室「ヒツジをつくろう」":"kodomonokuni", "こどもの国 エコスポ！フェス2026":"kodomonokuni",
  "旧横ギャラリー 展示ガイド（中等客車に乗れる）":"mm", "ANAの飛行機に色をぬろう！親子ワークショップ":"mm", "日本丸「飾り毛布」作り体験":"mm",
  "みなとみらい熱気球係留搭乗体験会":"yamashita",
  "Christmas Market in 横浜赤レンガ倉庫":"yamashita", "BALLPARK Xmas YOKOHAMA KANNAI 2026":"yamashita", "パウ・パトロールのクイズラリー＆マーシャルのグリーティング（BALLPARK Xmas）":"yamashita", "ムーミン MEET & GREET（BALLPARK Xmas・横浜公園）":"yamashita", "アートリンク in 横浜赤レンガ倉庫（屋外スケート）":"yamashita",
  "横浜消防出初式2027（パウパトロールのステージ・消防車の展示）":"yamashita", "TOWERS Milight \"UP\"（みなとみらいのビルが一斉に点灯）":"mm"
});
function dayChips(e){
  if (e.kind === "ongoing") return `<span class="period">${e.wk || /確認|要確認|以外|いつでも/.test(e.period) ? "" : "会期 "}${esc(e.period)}</span>${e.wk ? `<span class="period wk">平日：${esc(e.wk)}</span>` : ""}`;
  return e.days.map(k => { const st = e.stop && e.stop[k] ? " stopped" : ""; const d = DATES[DATE_IDX[k]]; if (!d) return `<span class="day wkday${st}">${dlabel(k)}</span>`; return `<span class="day ${d.c}${st}">${d.s}(${d.w})</span>`; }).join("");
}
function hashId(t){ let h = 0x811c9dc5; for (const ch of t) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; } return h.toString(36); }
{ const used = {}; EVENTS.forEach(e => { let id = e.id || hashId(e.t); if (used[id]) id += "-" + (++used[id]); else used[id] = 1; e.id = id; }); }
const EV_BY_ID = Object.fromEntries(EVENTS.map(e => [e.id, e]));
// 送るリンクはイベントごとのページ（tools/build_pages.py が作る）。そのページの「一覧で見る」から ?e=ID で戻ってくる
function evLink(e){ return SITE_URL + "event/" + encodeURIComponent(e.id) + "/"; }
let FAVS = new Set(); try { FAVS = new Set(JSON.parse(localStorage.getItem("favs") || "[]")); } catch (_) {}
function saveFavs(){ try { localStorage.setItem("favs", JSON.stringify([...FAVS])); } catch (_) {} }
function favBtn(e){ const on = FAVS.has(e.id); return `<button type="button" class="favbtn" data-fav="${esc(e.id)}" aria-pressed="${on}" aria-label="${on ? "お気に入りから外す" : "お気に入りに入れる"}">${on ? "★" : "☆"}<span>${on ? "お気に入り" : "お気に入り"}</span></button>`; }
document.addEventListener("click", async ev => {
  const f = ev.target.closest(".favbtn");
  if (f) {
    const id = f.dataset.fav, on = !FAVS.has(id);
    on ? FAVS.add(id) : FAVS.delete(id); saveFavs();
    document.querySelectorAll(`.favbtn[data-fav="${id}"]`).forEach(b => { b.setAttribute("aria-pressed", on); b.firstChild.textContent = on ? "★" : "☆"; b.setAttribute("aria-label", on ? "お気に入りから外す" : "お気に入りに入れる"); });
    if (typeof track === "function") track("fav", on ? "入れた" : "外した", EV_BY_ID[id] ? EV_BY_ID[id].t : id);
    if (state.flags.has("fav")) render(); else renderEvPoints();
    return;
  }
  const sh = ev.target.closest(".sharebtn"); if (!sh) return;
  const e = EV_BY_ID[sh.dataset.share]; if (!e) return;
  const url = evLink(e), title = e.t;
  if (navigator.share) {
    try { await navigator.share({ title, text: `${title}（KidsTrip）`, url }); if (typeof track === "function") track("copy_link", "共有メニュー", title); } catch (_) {}
    return;
  }
  let ok = false;
  try { await navigator.clipboard.writeText(url); ok = true; } catch (_) {
    try { const ta = document.createElement("textarea"); ta.value = url; document.body.appendChild(ta); ta.select(); ok = document.execCommand("copy"); ta.remove(); } catch (_) {}
  }
  const old = sh.innerHTML; sh.textContent = ok ? "コピーしました" : url; setTimeout(() => { sh.innerHTML = old; }, 2000);
  if (typeof track === "function") track("copy_link", "コピー", title);
});
// ?e=ID で開いたとき：条件をリセットして、そのイベントのカードまで移動して目立たせる
function openFromLink(){
  let id = ""; try { id = new URLSearchParams(location.search).get("e") || ""; } catch (_) {}
  if (!id) return;
  const e = EV_BY_ID[id];
  const box = document.getElementById("results");
  if (!e) {
    if (box) box.insertAdjacentHTML("afterbegin", `<p class="linknote">送られたリンクのイベントは、掲載が終わっています（終了した可能性があります）。ほかのイベントを見てみてください。</p>`);
    setTimeout(() => track("open_link", "掲載終了", id), 0);
    return;
  }
  const c = document.querySelector(`#results .card[data-eid="${e.id}"]`); if (!c) return;
  c.classList.remove("more-hidden"); c.classList.add("linked");
  const dm = c.querySelector("details.evmore"); if (dm) dm.open = true;
  c.insertAdjacentHTML("afterbegin", `<p class="linkflag">🔗 送られたイベント</p>`);
  setTimeout(() => { const y = c.getBoundingClientRect().top + window.scrollY - 70; window.scrollTo({ top: y }); }, 50);
  setTimeout(() => track("open_link", "開いた", e.t), 0);
}
function lineUrl(text){ return "https://line.me/R/share?text=" + encodeURIComponent(text); }
function eventText(e){
  const when = e.kind === "ongoing" ? (/確認|いつでも/.test(e.period) ? e.period : `会期 ${e.period}`) : e.days.map(k => { const d = DATES[DATE_IDX[k]]; if (!d) return dlabel(k); return `${d.k}(${d.w})`; }).join("・");
  return `【${e.t}】\n${when}　${e.time}\n場所：${e.ward}・${e.venue}\n料金：${e.priceText}\n雨の日：${RAIN_LABEL[e.rain]}（${e.rainText}）\nKidsTripで見る：${evLink(e)}\n公式：${e.url}`;
}

// ===== 持ち物チェック =====
function packHtml(e){
  const k = FOOD_OF[e.t]; if (!k) return "";
  const bb = BABY[k] || [], shops = (FOOD[k] || {}).shops || [];
  if (!bb.length && !shops.length) return "";
  if (e.age[0] >= 9) return "";
  const names = arr => arr.slice(0,2).map(b => b.n.replace(/（.*?）/g,"")).join("、");
  const items = [];
  const hot = bb.filter(b => b.w === true);
  if (hot.length) items.push(["leave","いらない",`魔法瓶のお湯（調乳のお湯がもらえる：${names(hot)}）`]);
  else items.push(["bring","持参",`調乳用のお湯（近くでお湯がもらえる場所は確認できず）`]);
  const nurse = bb.filter(b => b.f === true);
  if (!nurse.length) items.push(["bring","持参","授乳ケープ（近くに授乳室が確認できず）"]);
  const stroller = bb.filter(b => b.ex.some(x => x.includes("ベビーカー貸出")));
  if (stroller.length) items.push(["leave","置いてOK",`ベビーカー（貸し出しあり：${names(stroller)}）※台数に限りあり`]);
  const micro = bb.filter(b => b.ex.some(x => x.includes("電子レンジ")));
  if (micro.length) items.push(["leave","温め可",`離乳食はその場で温められる（${names(micro)}）`]);
  const kidsfood = shops.filter(sh => sh.tags.some(t => t.includes("キッズメニュー") || t.includes("園内で食べられる")));
  const bento = shops.some(sh => sh.tags.includes("お弁当持ち込みOK")) || bb.some(b => b.ex.includes("お弁当持ち込みOK"));
  if (kidsfood.length) items.push(["leave","なくてOK",`お弁当（子連れで食べられるお店あり：${names(kidsfood)}）`]);
  if (bento) items.push(["leave","持参OK","お弁当の持ち込みができる"]);
  const diaper = bb.filter(b => b.d === true);
  if (!diaper.length) items.push(["bring","持参","おむつ替えシート（おむつ替えの場所が確認できず）"]);
  return `<div class="pack"><h4>持ち物チェック（赤ちゃん連れ）</h4><ul>${items.map(([c,m,t]) => `<li class="${c}"><span class="m">${m}</span><span>${esc(t)}</span></li>`).join("")}</ul>
    <p class="note">近くの施設情報からの目安です。情報の時点が古いものもあるので、下の「おむつ替え・授乳・お湯」で確認してください。</p></div>`;
}

const state = { day:"all", age:"all", flags:new Set(), area:"all", q:"" };

function esc(s){ return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

// イベントタブの要点：今週末の件数と、よく使う条件（押すとその条件で絞る）
function renderEvPoints(){
  const box = document.getElementById("ev-points"); if (!box || !WEEKENDS.length) return;
  const W = WEEKENDS[0], wk = EVENTS.filter(e => e.days.some(d => W.ds.includes(d)));
  const n = f => wk.filter(f).length;
  const chip = (v, label, c) => `<button type="button" class="pchip" data-flag="${v}" aria-pressed="${state.flags.has(v)}">${label} ${c}件</button>`;
  box.innerHTML = `<li><span class="pi">📅</span><span>直近の週末（${esc(W.h.replace(/\s.*$/, ""))}）は <b>${wk.length}件</b>。<br>下の日にちボタンで日を選べます。</span></li>
    <li><span class="pi">👆</span><span>よく使う条件（全期間で絞ります）<span class="pchips">${(n => n ? chip("fav", "★ お気に入り", n) : "")(EVENTS.filter(e => FAVS.has(e.id)).length)}${chip("rain", "☔ 雨でもOK", EVENTS.filter(e => e.rain === "ok").length)}${chip("free", "🆓 完全無料", EVENTS.filter(e => e.price === "free").length)}${chip("noresv", "🎟 予約なし", EVENTS.filter(e => e.resv === false).length)}</span></span></li>
    <li><span class="pi">🍼</span><span>各カードの「くわしく」に、近くのおむつ替え・授乳室・ごはんがあります。</span></li>`;
  const sel = document.getElementById("more-sel"); if (sel) { const k = state.flags.size + (state.area !== "all" ? 1 : 0); sel.textContent = k ? `（${k}個選択中）` : ""; }
}
document.addEventListener("click", ev => {
  const c = ev.target.closest("#ev-points .pchip"); if (!c) return;
  const b = document.querySelector(`.opts[data-key="flags"] .opt[data-v="${c.dataset.flag}"]`); if (b) b.click();
});

function matches(e){
  if (state.day !== "all" && !e.days.includes(state.day)) return false;
  if (state.age !== "all") {
    const [lo, hi] = state.age.split("-").map(Number);
    if (!(e.age[0] <= hi && e.age[1] >= lo)) return false;
  }
  if (state.flags.has("fav") && !FAVS.has(e.id)) return false;
  if (state.flags.has("free") && e.price !== "free") return false;
  if (state.flags.has("rain") && e.rain !== "ok") return false;
  if (state.flags.has("noresv") && e.resv !== false) return false;
  if (state.flags.has("limited") && e.kind !== "limited") return false;
  if (state.flags.has("ride") && !e.ride) return false;
  if (state.flags.has("animal") && !e.animal) return false;
  if (state.flags.has("freeplay") && !e.freeplay) return false;
  if (state.flags.has("paidplay") && !e.paidplay) return false;
  if (state.flags.has("weekday") && !e.wk) return false;
  if (state.flags.has("hot") && !hasHotWater(e)) return false;
  if (state.area !== "all" && !e.ward.split("・").includes(state.area)) return false;
  if (state.q) {
    const dk = dateKeyQ(state.q);
    if (dk) { if (!e.days.includes(dk)) return false; }
    else {
      const hay = (e.t + e.sum + e.venue + e.ward + (e.tip||"")).toLowerCase();
      if (!hay.includes(state.q.toLowerCase())) return false;
    }
  }
  return true;
}
// 検索欄に「11月20日」「11/20」「20日」のような日付が入ったら、その日のイベントを出す
function dateKeyQ(q){
  const z = String(q).normalize("NFKC").replace(/\s|（.*?）|\(.*?\)|[日月火水木金土祝]曜日?$/g, "");
  let m = /^(\d{1,2})(?:月|\/)(\d{1,2})日?$/.exec(z);
  if (m) return `${+m[1]}/${+m[2]}`;
  m = /^(\d{1,2})日$/.exec(z);
  if (m) { const t = new Date(), d = +m[1]; const mo = d >= t.getDate() ? t.getMonth() + 1 : (t.getMonth() + 1) % 12 + 1; return `${mo}/${d}`; }
  return null;
}
function stationWc(x){ return STATION_WC[x.st + "|" + x.line] || STATION_WC[x.st] || null; }
let PICK_N = 0;
function pickHtml(items, wrap){
  if (!items.length) return "";
  const w = h => wrap ? wrap(h) : h;
  if (items.length === 1) return w(items[0].html);
  const id = "pk" + (++PICK_N);
  return `<div class="pick" id="${id}"><div class="pchips" role="tablist">${items.map((x, i) => `<button type="button" class="pchip${i ? "" : " on"}" aria-selected="${i ? "false" : "true"}" onclick="pickShow('${id}',${i})">${esc(x.label)}</button>`).join("")}</div>${items.map((x, i) => `<div class="pbody"${i ? " hidden" : ""}>${w(x.html)}</div>`).join("")}</div>`;
}
function pickShow(id, i){
  const r = document.getElementById(id); if (!r) return;
  r.querySelectorAll(":scope > .pchips > .pchip").forEach((b, j) => { b.classList.toggle("on", j === i); b.setAttribute("aria-selected", j === i ? "true" : "false"); });
  r.querySelectorAll(":scope > .pbody").forEach((d, j) => { d.hidden = j !== i; });
}
const shortName = n => n.replace(/（.*?）|\(.*?\)/g, "").trim();
function parkLots(e, k){
  const pv = PARK_VENUE.find(([re]) => re.test(e.venue + e.t));
  return (k && PARK_LOTS[k]) || (pv ? pv[1] : []);
}
function bikeNear(e){
  const g = venueGeo(e); if (!g) return [];
  return BIKE_LOTS.map(b => ({ b, min: Math.max(1, Math.round(distM(g, b.g) * 1.3 / 70)) })).filter(x => x.min <= 10).sort((a, b) => a.min - b.min);
}
function bikeHtml(e){
  const near = bikeNear(e);
  const g = venueGeo(e);
  const map = g ? `<a href="https://www.google.com/maps/search/${encodeURIComponent("駐輪場")}/@${g[0]},${g[1]},16z" target="_blank" rel="noopener">地図で近くの駐輪場を探す</a>` : "";
  if (!near.length) return g ? `<div class="bikes"><b>🚲 駐輪場</b><p class="note">このあたりの駐輪場はまだ調べていません。${map}</p></div>` : "";
  return `<div class="bikes"><b>🚲 歩いて10分以内の駐輪場</b>${pickHtml(near.map(x => ({ label: `${shortName(x.b.n)} 約${x.min}分`, html: `<li><b>${esc(x.b.n)}</b><br><span class="m">${esc(x.b.fee)}<br>${x.b.tags.map(t => `<span class="ktag">${esc(t)}</span>`).join("")}<br>会場まで歩いて約${x.min}分（目安）（${esc(x.b.src)}）</span></li>` })), h => `<ul class="flist">${h}</ul>`)}
    <p class="note">子乗せ自転車は2段ラックの上段に入らないことが多いので、平置きか下段の空きを探してください。みなとみらいの遊歩道や公園の中は自転車に乗って走れない場所が多く、押して歩きます。料金は変わることがあるので、現地の表示を確認してください。${map}</p></div>`;
}
function parkHtml(e, k){
  const g = venueGeo(e);
  const lots = parkLots(e, k);
  const free = Object.entries(PARK_FREE).find(([n]) => (e.venue + e.t).includes(n));
  const map = g ? `https://www.google.com/maps/search/${encodeURIComponent("駐車場")}/@${g[0]},${g[1]},16z` : `https://www.google.com/maps/search/${encodeURIComponent(e.venue.replace(/（.*?）/g,"") + " 駐車場")}`;
  return `<div class="park"><b>🅿 近くの駐車場</b>
    ${free ? `<p>${esc(free[1])}</p>` : ""}
    ${pickHtml(lots.map(l => ({ label: shortName(l.n), html: `<li><b>${esc(l.n)}</b><span class="m">${esc(l.fee)}</span>${l.note ? `<span class="m">${esc(l.note)}</span>` : ""}<span class="src">出典：${esc(l.src)}</span></li>` })), h => `<ul>${h}</ul>`)}
    <p class="links"><a href="${esc(map)}" target="_blank" rel="noopener">会場のまわりの駐車場を地図で見る</a>${k && PARK_RESERVE[k] ? `　<a href="${esc(PARK_RESERVE[k])}" target="_blank" rel="noopener">予約できる駐車場を探す（akippa）</a>` : ""}</p>
    <p class="note">料金は変わることがあります。イベントの日は満車になりやすいので、予約できる駐車場か電車がおすすめです。</p></div>`;
}
function accessKey(e){
  const s = e.t + " " + e.venue;
  if (/京急ミュージアム|原鉄道/.test(s)) return "takashima";
  if (/アンパンマン/.test(s)) return "anpan";
  if (/市場まつり|卸売市場/.test(s)) return "ichiba";
  if (/八景島/.test(s)) return "hakkeijima";
  if (/赤レンガ|象の鼻|大さん橋|新港|ハンマーヘッド|ナイトフラワーズ|コナン芸術花火|花火シンフォニア/.test(s)) return "akarenga";
  if (/桜木町|シァル|CIAL/.test(s)) return "sakuragicho";
  if (/MARK IS|ランドマーク|日本丸|美術館|グランモール|シンフォステージ|みなとみらい/.test(s)) return "mm";
  if (/横浜公園|関内|BASEGATE|BALLPARK/.test(s)) return "kannai";
  if (/山下|マリンタワー|人形の家|中華街|MOVEUM|ミナトノアート|かえるのピクルス/.test(s)) return "yamashita";
  if (/横浜駅東口|はまテラス|そごう/.test(s)) return "yokohamaEast";
  if (/横浜アリーナ|新横浜/.test(s)) return "shinyokohama";
  if (/こどもの国/.test(s)) return "kodomonokuni";
  if (/ズーラシア/.test(s)) return "zoorasia";
  if (/三溪園/.test(s)) return "sankeien";
  if (/瀬谷/.test(s)) return "seya";
  if (/岸根/.test(s)) return "kishine";
  if (/センター北|牛久保|都筑/.test(s)) return "centerkita";
  return null;
}
function accPoints(e, k, a){
  const out = [];
  if (a && a.st.length) {
    const info = a.st.map(x => {
      const r = (x.route || "");
      const mins = [...r.matchAll(/約(\d+)分/g)].map(m => +m[1]);
      const min = mins.length ? mins[mins.length - 1] : null;
      const tags = [];
      if (/エレベーター/.test(r)) tags.push("エレベーターあり");
      if (/段差な|平ら/.test(r)) tags.push("段差なし");
      if (/坂|階段/.test(r)) tags.push(/坂/.test(r) ? "坂あり" : "階段あり");
      if (stationWc(x) && stationWc(x).some(w => /◎/.test(w))) tags.push("駅でおむつ替え◎");
      return { st: x.st, line: x.line, min, tags, bus: /バス/.test(x.line + r) };
    }).sort((p, q) => (p.min ?? 99) - (q.min ?? 99));
    info.forEach((x, i) => out.push(`🚃 ${i === 0 ? "最寄り " : ""}${x.st}（${x.line}）${x.min ? (x.bus ? `：バスで約${x.min}分` : `：歩いて約${x.min}分`) : (x.bus ? "：バス" : "")}${x.tags.length ? "・" + x.tags.join("・") : ""}`));
  }
  const lots = parkLots(e, k);
  const free = Object.entries(PARK_FREE).find(([n]) => (e.venue + e.t).includes(n));
  const pb = [];
  if (free) pb.push(`🅿 ${free[1]}`);
  else if (lots.length) pb.push(`🅿 駐車場${lots.length}か所（${shortName(lots[0].n)}など・混みやすい）`);
  const bk = bikeNear(e);
  if (bk.length) pb.push(`🚲 ${shortName(bk[0].b.n)}（約${bk[0].min}分・${bk[0].b.fee}）${bk.length > 1 ? `ほか${bk.length - 1}か所` : ""}`);
  if (pb.length) out.push(pb.join("　"));
  return out.length ? `<div class="apts">${out.map(x => `<span>${esc(x)}</span>`).join("")}</div>` : "";
}
function mapsUrl(e){ return "https://www.google.com/maps/dir/?api=1&travelmode=transit&destination=" + encodeURIComponent(e.venue.replace(/（.*?）/g,"") + " 横浜"); }
function accessHtml(e){
  const k = accessKey(e);
  const go = `<a class="more" href="${esc(mapsUrl(e))}" target="_blank" rel="noopener">経路を調べる（Googleマップ）</a>`;
  if (!k) return `<details class="acc"><summary>行き方・ベビーカー動線・トイレ・駐車場・駐輪場</summary>${accPoints(e, null, null)}<p class="note">この会場の駅からの動線とトイレはまだ調べていません。${go}</p>${(() => { const bk = bikeHtml(e); return pickHtml([{ label: "🚗 車で", html: parkHtml(e, null) }, ...(bk ? [{ label: "🚲 自転車で", html: bk }] : [])]); })()}</details>`;
  const a = ACCESS[k];
  const sat = a.free && e.days.some(d => (DATES.find(x => x.k === d) || {}).w === "土");
  const stItems = a.st.map(s => ({ label: "🚃 " + s.st, html: `<ul><li><b>${esc(s.st)}</b><span class="ln">${esc(s.line)}</span>
      ${s.car ? `<p class="car">🚃 ${esc(s.car)}${/〔/.test(s.car) ? `<span class="m">〔 〕内は8両編成のとき</span>` : ""}</p>` : ""}<p>${esc(s.route)}</p>
      ${stationWc(s) ? `<div class="wc"><b>🚻 駅のトイレ・おむつ替え</b><ul>${stationWc(s).map(x => `<li>${esc(x)}</li>`).join("")}</ul>${stationWc(s).some(x => /◎/.test(x)) ? `<span class="m">◎はおむつ替えできると確認できたところ</span>` : ""}</div>` : ""}
      ${s.map ? `<a href="${esc(s.map)}" target="_blank" rel="noopener">駅の構内図</a>` : ""}${s.src ? `<span class="src">出典：${esc(s.src)}</span>` : ""}
      <details class="srcs"><summary>駅のトイレ情報の出典・時点</summary><p class="note">エレベーターは点検で止まることがあるので、駅の案内も見てください。情報の時点：2026年11月10日。${esc(STATION_WC_SRC)}</p></details></li></ul>` }));
  const pk = parkHtml(e, k), bk = bikeHtml(e);
  const rows = pickHtml([...stItems,
    { label: "🚗 車で", html: `<p><b>🅿 駐車場：</b>${esc(a.park)}</p>${pk}` },
    ...(bk ? [{ label: "🚲 自転車で", html: bk }] : [])]);
  return `<details class="acc"><summary>行き方・ベビーカー動線・トイレ${sat ? `<span class="freeday">土曜は高校生以下無料</span>` : ""}</summary>
    ${accPoints(e, k, a)}
    ${transitHtml(e, k)}
    <p class="note">来かたを選ぶと、駅なら乗る号車・エレベーター・駅のトイレ、車なら駐車場、自転車なら駐輪場が出ます。</p>
    ${rows}
    <p><b>🚻 会場まわりのベビーカーで入れるトイレ：</b>${esc(a.toilet || "駅・商業施設の多目的トイレ（だれでもトイレ）が使えることが多いです。この会場の場所はまだ調べていません。")}</p>
    ${a.free ? `<p><b>無料の日：</b>${esc(a.free)}</p>` : ""}
    ${a.rainAlt ? `<p><b>☔ 雨なら：</b>${esc(a.rainAlt)}</p>` : ""}
    ${go}</details>`;
}
function stepIcon(t){
  const A = (d) => `<svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true"><rect x="1" y="1" width="38" height="38" rx="9" fill="var(--accent-soft)"/>${d}</svg>`;
  const ar = `stroke="var(--accent)" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"`;
  switch (t) {
    case "left": return A(`<path d="M26 32 V18 a4 4 0 0 0 -4 -4 H12" ${ar}/><path d="M17 8 L11 14 L17 20" ${ar}/>`);
    case "right": return A(`<path d="M14 32 V18 a4 4 0 0 1 4 -4 H28" ${ar}/><path d="M23 8 L29 14 L23 20" ${ar}/>`);
    case "straight": return A(`<path d="M20 32 V10" ${ar}/><path d="M13 16 L20 9 L27 16" ${ar}/>`);
    case "ev": return A(`<rect x="10" y="7" width="20" height="26" rx="2" fill="none" stroke="var(--accent)" stroke-width="3"/><line x1="20" y1="7" x2="20" y2="33" stroke="var(--accent)" stroke-width="2"/><path d="M13 16 l3 -4 l3 4 M21 24 l3 4 l3 -4" stroke="var(--accent)" stroke-width="2.4" fill="none"/>`);
    case "cross": return A(`${[9,15,21,27].map(x => `<rect x="${x}" y="8" width="4" height="24" fill="var(--accent)"/>`).join("")}`);
    case "up": return A(`<path d="M7 31 L33 13 V31 Z" fill="var(--warn)" opacity=".85"/><path d="M12 22 l7 -5" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>`);
    case "down": return A(`<path d="M7 13 L33 31 H7 Z" fill="var(--accent)" opacity=".7"/>`);
    case "arrive": return A(`<path d="M20 7 l3.8 7.7 8.5 1.2 -6.2 6 1.5 8.4 -7.6 -4 -7.6 4 1.5 -8.4 -6.2 -6 8.5 -1.2z" fill="#e2b02c"/>`);
    default: return A(`<circle cx="20" cy="20" r="9" fill="#e2483d"/><text x="20" y="24" text-anchor="middle" font-size="10" fill="#fff" font-weight="700">駅</text>`);
  }
}
function routeOverview(r){
  // 曲がり方だけを表した全体図（上が進む方向のスタート）
  let x = 0, y = 0, h = 0; const pts = [[0,0]], marks = [];
  const L = 34, dirs = [[0,-1],[1,0],[0,1],[-1,0]];
  r.steps.forEach((st, i) => {
    const tn = st.turn || (st.t === "left" || st.t === "right" ? st.t : null);
    if (tn === "left") h = (h + 3) % 4; if (tn === "right") h = (h + 1) % 4;
    if (i > 0) { x += dirs[h][0] * L; y += dirs[h][1] * L; pts.push([x, y]); }
    marks.push({ x, y, t: st.t, n: i, w: st.w });
  });
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const pad = 22, minX = Math.min(...xs) - pad, minY = Math.min(...ys) - pad, W = Math.max(...xs) - minX + pad, H = Math.max(...ys) - minY + pad;
  const dots = marks.map(m => {
    const c = m.t === "start" ? "#e2483d" : m.t === "arrive" ? "#e2b02c" : m.w ? "var(--warn)" : "var(--accent)";
    return `<circle cx="${m.x}" cy="${m.y}" r="10" fill="${c}" stroke="#fff" stroke-width="2"/><text x="${m.x}" y="${m.y + 4}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#fff">${m.t === "start" ? "駅" : m.t === "arrive" ? "★" : m.n}</text>`;
  }).join("");
  return `<svg class="rov" viewBox="${minX} ${minY} ${W} ${H}" role="img" aria-label="${esc(r.title)}の曲がり方の全体図">
    <polyline points="${pts.map(p => p.join(",")).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity=".35"/>
    <polyline points="${pts.map(p => p.join(",")).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="4 4"/>${dots}</svg>`;
}
function routeCard(id){
  const r = ROUTES[id];
  return `<div class="route"><p class="rt"><b>🗺 ${esc(r.title)}</b>（ベビーカーで${esc(r.min)}）</p>
    <div class="rov-box"><span class="note">曲がる順番の全体図（駅→★）</span>${routeOverview(r)}</div><div class="rwrap">
    <ol class="rsteps">${r.steps.map((st, i) => `<li class="${st.w ? "w" : ""}">${stepIcon(st.t)}<div><span class="rn">${st.t === "start" || st.t === "arrive" ? ROUTE_LABEL[st.t] : i + "・" + ROUTE_LABEL[st.t]}${st.turn ? "（" + ROUTE_LABEL[st.turn] + "曲がる）" : ""}${st.w ? "・注意" : ""}</span>${esc(st.s)}</div></li>`).join("")}</ol></div>
    <p class="note">🚻 途中の多目的トイレ：${esc(r.wc)}</p>
    <p class="note">全体図は曲がる順番だけを表した図で、実際の距離や形とは違います。道順の出典：${esc(r.src)}。工事などで変わっていることがあるので、現地の案内も見てください。</p></div>`;
}
function routesFor(e){
  const s = e.t + " " + e.venue;
  if (/赤レンガ/.test(s)) return ["nihonodori_renga", "bashamichi_renga"];
  if (/美術館|グランモール|クリスマスマーケット2026/.test(s)) return ["minatomirai_museum", "sakuragicho_museum"];
  return [];
}
function routeHtml(e){
  const ids = routesFor(e); if (!ids.length) return "";
  return `<details class="food rmap"><summary>🗺 ベビーカールート図（${ids.length}ルート）</summary>${ids.map(routeCard).join("")}</details>`;
}

// 電話番号を押せるリンクにする（例：045-251-0119）
function telify(h){ return h.replace(/(^|[^\d-])(0\d{1,4}-\d{1,4}-\d{3,4})(?![\d-])/g, (m, pre, num) => `${pre}<a href="tel:${num.replace(/-/g, "")}" class="tel">${num}</a>`); }
// 雨の日の説明が見出し（「雨天中止」など）と同じなら、二重に出さない
function rainRest(e){
  const lab = RAIN_LABEL[e.rain] || "", t = String(e.rainText || "").trim();
  if (!t || t === lab) return "";
  const rest = t.startsWith(lab) ? t.slice(lab.length).replace(/^[\s　、。：:（(]+/, "").replace(/[）)]$/, "") : t;
  if (/^[とがはの]/.test(rest)) return "　" + esc(t);
  return rest ? "　" + esc(rest) : "";
}
function card(e, ctx){
  const days = dayChips(e);
  const priceChip = e.price === "free" ? `<li class="chip free">無料</li>`
    : e.price === "admission" ? `<li class="chip">入園料のみ</li>`
    : e.price === "paid" ? `<li class="chip">有料</li>` : `<li class="chip">料金要確認</li>`;
  const resvChip = e.resv === true ? `<li class="chip resv">要予約</li>` : e.resv === false ? `<li class="chip">予約不要</li>` : `<li class="chip">予約は要確認</li>`;
  // 中止が分かった日（e.stop = { "11/15":"雨で中止" }）は赤で表示する
  const stops = Object.entries(e.stop || {});
  const stopNote = stops.map(([k, why]) => `<p class="stopnote">⛔ ${dlabel(k)}は${esc(why)}</p>`).join("");
  // この見出しの日がすべて中止なら、題名・時間も赤にする
  const inSec = Array.isArray(ctx) ? e.days.filter(k => ctx.includes(k)) : e.days;
  const allStop = stops.length && inSec.length && inSec.every(k => e.stop[k]);
  return `<article class="card r-${e.rain}${allStop ? " allstop" : ""}" data-eid="${esc(e.id)}" data-ev="${esc(e.t)}">
    <div class="when">${days}<span>${esc(e.time)}</span><span class="acts">${favBtn(e)}${e.noShare ? "" : `<button type="button" class="sharebtn ic" data-share="${esc(e.id)}" aria-label="リンクを送る・コピー" title="リンクを送る・コピー">🔗<span>送る</span></button><a class="linebtn ic" href="${esc(lineUrl(eventText(e)))}" target="_blank" rel="noopener" aria-label="LINEで送る" title="LINEで送る"><svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3C6.5 3 2 6.6 2 11c0 3.9 3.5 7.2 8.3 7.9.3.1.8.2.9.5.1.3.1.7 0 1l-.1.9c0 .3-.2 1 .9.5 1.1-.5 5.9-3.5 8-5.9C21.4 14.4 22 12.8 22 11c0-4.4-4.5-8-10-8z"/></svg><span>LINE</span></a>`}</span></div>
    ${stopNote}<h3>${e.officialOnly ? `<a data-act="official" href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.t)}</a>` : esc(e.t)}</h3>
    ${e.officialOnly ? `<p class="offonly">主催から「公式の情報を見てほしい」とのお願いがあります。くわしくは<a data-act="official" href="${esc(e.url)}" target="_blank" rel="noopener">主催の公式ページ</a>で確認してください。</p>` : ""}
    <p class="where">${esc(e.ward)}・${esc(e.venue)}</p>
    <ul class="chips">${priceChip}<li class="chip">${esc(e.ageText)}</li><li class="chip">${esc(e.place)}</li>${resvChip}</ul>
    <p class="rain ${e.rain}">${RAIN_ICON[e.rain]}<span><b>${RAIN_LABEL[e.rain]}</b>${rainRest(e)}</span></p>
    <p class="sum">${esc(e.sum)}</p>
    <p class="where">料金：${esc(e.priceText)}／予約：${telify(esc(e.resvText))}</p>
    <details class="evmore"><summary>くわしく見る（公式・行き方・おむつ・ごはん）</summary><div class="evbody">
    <p class="tip" style="display:${e.tip ? "block" : "none"}">${telify(esc(e.tip || ""))}</p>
    <p class="asof">情報の時点：${esc(e.asof || "2026年11月9日")}</p>
    <div class="cardfoot"><a class="more" data-act="official" href="${esc(e.url)}" target="_blank" rel="noopener">${e.officialOnly ? esc(e.officialLabel || "主催の公式ページを開く") : `詳細はこちら（${esc(e.src)}）`}</a>${e.resvUrl ? `<a class="more" data-act="resv" href="${esc(e.resvUrl)}" target="_blank" rel="noopener">予約ページへ</a>` : ""}
</div>
    ${routeHtml(e)}
    ${accessHtml(e)}
    ${packHtml(e)}
    ${babyHtml(e)}
    ${foodHtml(e)}
    ${famiresHtml(e)}
    ${clothesHtml(e)}
    </div></details>
  </article>`;
}

function sortKey(e, ds){ const vague = /確認/.test(e.time) ? 50000 : 0; const first = (ds ? e.days.filter(d => ds.includes(d)) : e.days)[0]; return vague + (DATE_IDX[first] || 0) * 2000 + e.start; }
const near = { c:null, label:"", r:1000 };
function distM(a, b){ const R=6371000, t=x=>x*Math.PI/180, dLa=t(b[0]-a[0]), dLo=t(b[1]-a[1]);
  return 2*R*Math.asin(Math.sqrt(Math.sin(dLa/2)**2+Math.cos(t(a[0]))*Math.cos(t(b[0]))*Math.sin(dLo/2)**2)); }
function fmtD(m){ return m < 1000 ? `${Math.round(m/10)*10}m` : `${(m/1000).toFixed(1)}km`; }
function renderNear(){
  const out = document.getElementById("near-out"); if (!out) return;
  document.querySelectorAll("#near-r .opt").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.v === near.r)));
  if (!near.c) { out.innerHTML = `<p class="note">「現在地から探す」を押すか、近くの駅を選んでください。</p>`; return; }
  const items = [];
  EVENTS.filter(matches).forEach(e => { const g = venueGeo(e); if (g) { const d = distM(near.c, g); if (d <= near.r) items.push({ kind:"ev", e, g, d }); } });
  Object.entries(SPOT_GEO).forEach(([n, g]) => { const d = distM(near.c, g); if (d <= near.r) items.push({ kind:"baby", n, g, d }); });
  BABYFOOD_SHOPS.forEach(x => { const d = distM(near.c, x.g); if (d <= near.r) items.push({ kind:"food", n:x.n, g:x.g, d, sub:x.d }); });
  items.sort((a, b) => a.d - b.d);
  // 地図（自前のSVG。上が北）
  const S = 300, sc = (S/2 - 18) / near.r, mPerLat = 111320, mPerLon = 111320 * Math.cos(near.c[0]*Math.PI/180);
  const pos = g => [S/2 + (g[1]-near.c[1]) * mPerLon * sc, S/2 - (g[0]-near.c[0]) * mPerLat * sc];
  let pins = "", n = 0; const seen = {};
  items.forEach(it => { n++; it.no = n; let [x, y] = pos(it.g); const kk = Math.round(x/6)+","+Math.round(y/6), c = seen[kk] = (seen[kk]||0) + 1;
    if (c > 1) { const a = c * 2.1, r = 7 + c * 2.2; x += Math.cos(a) * r; y += Math.sin(a) * r; }
    pins += `<g><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9" fill="${it.kind==="ev" ? "var(--accent)" : it.kind==="food" ? "#d98a1f" : "var(--ok)"}" stroke="#fff" stroke-width="1.5"/><text x="${x.toFixed(1)}" y="${(y+3.5).toFixed(1)}" text-anchor="middle" font-size="9.5" fill="#fff" font-weight="700">${n}</text></g>`; });
  const map = `<svg class="nmap" viewBox="0 0 ${S} ${S}" role="img" aria-label="${esc(near.label)}から${fmtD(near.r)}圏内の地図">
    <circle cx="${S/2}" cy="${S/2}" r="${S/2-18}" fill="var(--accent-soft)" stroke="var(--line)"/>
    <circle cx="${S/2}" cy="${S/2}" r="${(S/2-18)/2}" fill="none" stroke="var(--line)" stroke-dasharray="3 3"/>
    <text x="${S/2}" y="12" text-anchor="middle" font-size="10" fill="var(--muted)">北</text>
    <text x="${S/2+(S/2-18)/2+3}" y="${S/2-3}" font-size="9" fill="var(--muted)">${fmtD(near.r/2)}</text>
    ${pins}<circle cx="${S/2}" cy="${S/2}" r="6" fill="#e2483d" stroke="#fff" stroke-width="2"/></svg>`;
  const list = items.length ? items.map(it => {
    const walk = Math.max(1, Math.round(it.d * 1.3 / 70));
    const gm = `https://www.google.com/maps/dir/?api=1&travelmode=walking&origin=${it.g ? encodeURIComponent(near.c.join(",")) : ""}&destination=${encodeURIComponent(it.g.join(","))}`;
    return it.kind === "ev"
      ? `<li><span class="no ev">${it.no}</span><div><b>${esc(it.e.t)}</b><span class="m">${esc(it.e.venue)}・${dayChipsText(it.e)} ${esc(it.e.time)}</span><span class="m">${fmtD(it.d)}・ベビーカーで約${walk}分（目安）　<a href="${esc(gm)}" target="_blank" rel="noopener">徒歩ルート</a>　<a href="${esc(it.e.url)}" target="_blank" rel="noopener">詳細</a></span></div></li>`
      : `<li><span class="no ${it.kind==="food" ? "fd" : "bb"}">${it.no}</span><div><b>${esc(it.n)}</b><span class="m">${it.kind==="food" ? "🥣 離乳食が無料・" + esc(it.sub) : "おむつ替え・授乳など"}</span><span class="m">${fmtD(it.d)}・ベビーカーで約${walk}分（目安）　<a href="${esc(gm)}" target="_blank" rel="noopener">徒歩ルート</a></span></div></li>`;
  }).join("") : `<li class="none">この範囲には見つかりませんでした。範囲を広げてみてください。</li>`;
  out.innerHTML = `<p class="nhead"><b>${esc(near.label)}</b>から${fmtD(near.r)}以内：イベント${items.filter(i=>i.kind==="ev").length}件・赤ちゃん設備${items.filter(i=>i.kind==="baby").length}か所・離乳食無料のお店${items.filter(i=>i.kind==="food").length}店（上の日付・年齢などの絞り込みも反映）</p>
    <div class="nwrap">${map}<ol class="nlist">${list}</ol></div>
    <p class="note"><span style="color:#e2483d">●</span>赤い点が現在地（または選んだ駅）、<span style="color:var(--accent)">●</span>イベント、<span style="color:var(--ok)">●</span>おむつ替え・授乳、<span style="color:#d98a1f">●</span>離乳食が無料のお店。距離はまっすぐ測った目安で、徒歩の分数は道なりを考えて少し多めにしています。</p>`;
}
function dayChipsText(e){ return e.days.length > 3 ? `${e.days[0]}〜${e.days[e.days.length-1]}` : e.days.join("・"); }
function useHere(){
  const msg = document.getElementById("near-msg");
  if (!navigator.geolocation) { msg.textContent = "この画面では現在地が使えません。近くの駅を選んでください。"; return; }
  msg.textContent = "現在地を確認しています…";
  try {
    navigator.geolocation.getCurrentPosition(p => { near.c = [p.coords.latitude, p.coords.longitude]; near.label = "現在地"; msg.textContent = ""; renderNear(); if (typeof track === "function") track("near", "現在地から探す（" + coarseArea(near.c) + "）"); },
      () => { msg.textContent = "現在地を取得できませんでした（この画面では使えないことがあります）。近くの駅を選んでください。"; },
      { enableHighAccuracy:false, timeout:8000, maximumAge:300000 });
  } catch(_) { msg.textContent = "この画面では現在地が使えません。近くの駅を選んでください。"; }
}
function initNear(){
  const sel = document.getElementById("near-st"); if (!sel) return;
  sel.innerHTML = `<option value="">駅を選ぶ</option>` + Object.keys(ST_GEO).map(k => `<option>${k}</option>`).join("");
  sel.addEventListener("change", () => { if (!sel.value) return; near.c = ST_GEO[sel.value]; near.label = sel.value + "駅"; renderNear(); });
  document.getElementById("near-here").addEventListener("click", useHere);
  document.querySelectorAll("#near-r .opt").forEach(b => b.addEventListener("click", () => { near.r = +b.dataset.v; renderNear(); }));
  renderNear();
}

// 前回の絞り込み（日にち・年齢・区・こだわり・検索語）をこの端末に覚えておき、次に開いたときに戻す
function saveState(){
  try { localStorage.setItem("evstate", JSON.stringify({ day: state.day, age: state.age, area: state.area, q: state.q, flags: [...state.flags], at: Date.now() })); } catch (_) {}
}
function stateLabel(){
  const p = [];
  if (state.day !== "all") p.push(dlabel(state.day));
  if (state.area !== "all") p.push(state.area);
  if (state.age !== "all") { const b = document.querySelector(`.opts[data-key="age"] .opt[data-v="${state.age}"]`); p.push(b ? b.textContent.trim() : state.age); }
  state.flags.forEach(f => { const b = document.querySelector(`.opts[data-key="flags"] .opt[data-v="${f}"]`); p.push(b ? b.textContent.trim() : f); });
  if (state.q) p.push(`「${state.q}」`);
  return p.join("・");
}
function restoreState(){
  if (new URLSearchParams(location.search).get("e")) return;      // 送られたリンクで開いたときは戻さない
  let sv = null; try { sv = JSON.parse(localStorage.getItem("evstate") || "null"); } catch (_) {}
  if (!sv || Date.now() - (sv.at || 0) > 60 * 864e5) return;      // 60日より前のものは使わない
  const has = (key, v) => !!document.querySelector(`.opts[data-key="${key}"] .opt[data-v="${CSS.escape(v)}"]`);
  if (sv.day && sv.day !== "all" && has("day", sv.day)) state.day = sv.day;   // 過ぎた日は戻さない
  if (sv.age && sv.age !== "all" && has("age", sv.age)) state.age = sv.age;
  if (sv.area && sv.area !== "all" && has("area", sv.area)) state.area = sv.area;
  (sv.flags || []).forEach(f => { if (has("flags", f)) state.flags.add(f); });
  if (sv.q) { state.q = sv.q; const qi = document.getElementById("q"); if (qi) qi.value = sv.q; }
  document.querySelectorAll(".opts[data-key]").forEach(box => box.querySelectorAll(".opt").forEach(o => {
    const key = box.dataset.key;
    o.setAttribute("aria-pressed", box.dataset.multi ? String(state.flags.has(o.dataset.v)) : String(o.dataset.v === state[key]));
  }));
  const lb = stateLabel(); if (!lb) return;
  const bar = document.createElement("div"); bar.className = "restored"; bar.id = "restored";
  bar.innerHTML = `<span>前回の条件で表示中：<b>${esc(lb)}</b></span><button type="button" id="restored-x">リセット</button>`;
  const cnt = document.querySelector(".count"); if (cnt) cnt.parentNode.insertBefore(bar, cnt);
  bar.querySelector("#restored-x").addEventListener("click", () => { document.getElementById("reset").click(); });
  if (typeof track === "function") setTimeout(() => track("restore", lb), 1500);
}

function render(){
  saveState();
  { const rb = document.getElementById("restored"); if (rb) { const lb = stateLabel(); if (!lb) rb.remove(); else rb.querySelector("b").textContent = lb; } }
  if (typeof renderEvPoints === "function") renderEvPoints();
  const hit = EVENTS.filter(matches);
  if (typeof renderNear === "function" && near.c) setTimeout(renderNear, 0);
  document.getElementById("n").textContent = hit.length;
  let html = "";
  const secs = [];
  const dkey = dnum;
  for (const w of WEEKENDS) {
    const ds = state.day === "all" ? w.ds : w.ds.filter(d => d === state.day);
    if (!ds.length) continue;
    const list = hit.filter(e => e.kind === "limited" && e.days.some(d => ds.includes(d))).sort((a,b) => sortKey(a,ds) - sortKey(b,ds));
    if (!list.length) continue;
    secs.push([dkey(ds[0]), `<section class="group"><h2>${w.h}<small>${list.length}件・この日だけのイベント</small></h2><div class="list">${list.map(e => card(e, ds)).join("")}</div></section>`]);
  }
  if (state.day === "all") {
    const wkAll = WEEKENDS.flatMap(w => w.ds);
    const byDay = {};
    for (const e of hit.filter(e => e.kind === "limited" && e.days.some(d => !wkAll.includes(d)))) for (const d of e.days.filter(d => !wkAll.includes(d))) (byDay[d] = byDay[d] || []).push(e);
    for (const d of Object.keys(byDay)) {
      const [m, dd] = d.split("/").map(Number); const dow = new Date(dyear(m), m - 1, dd).getDay(); const yb = "日月火水木金土"[dow];
      const isWe = dow === 0 || dow === 6;
      secs.push([dkey(d), `<section class="group"><h2>${isWe ? "" : "平日 "}${m}月${dd}日(${yb})<small>${byDay[d].length}件・${isWe ? "この日のイベント" : "平日だけのイベント"}</small></h2><div class="list">${byDay[d].map(e => card(e, [d])).join("")}</div></section>`]);
    }
  }
  if (["12/26","12/27","1/1","1/2","1/3"].includes(state.day)) html += `<p class="note">年末年始は休館・休園や営業時間の変更が多い時期です。分かっている休みの日は外していますが、出かける前に各施設の公式ページで確認してください。</p>`;
  html += secs.sort((x, y) => x[0] - y[0]).map(x => x[1]).join("");
  const on = hit.filter(e => e.kind === "ongoing").sort((a,b) => sortKey(a) - sortKey(b));
  if (on.length) html += `<section class="group"><h2>会期中ずっとやっているもの<small>${on.length}件・選んだ日も開催中</small></h2><div class="list">${on.map(card).join("")}</div></section>`;
  document.getElementById("results").innerHTML = html || `<div class="empty">条件に合うイベントがありません。条件を減らしてみてください。</div>`;
  const SHOW = 6;
  document.querySelectorAll("#results .group").forEach(g => {
    const cards = [...g.querySelectorAll(".list > .card")];
    if (cards.length <= SHOW + 2) return;
    cards.slice(SHOW).forEach(c => c.classList.add("more-hidden"));
    const b = document.createElement("button");
    b.type = "button"; b.className = "morebtn"; b.textContent = `残り${cards.length - SHOW}件を見る`;
    b.addEventListener("click", () => { cards.forEach(c => c.classList.remove("more-hidden")); b.remove(); });
    g.appendChild(b);
  });
}

function setupAreas(){
  // 「中区・西区」のように複数の区にまたがるイベントは、それぞれの区で出す
  const wards = [...new Set(EVENTS.flatMap(e => e.ward.split("・")))];
  const order = ["中区","西区","神奈川区","鶴見区","港北区","都筑区","青葉区","緑区","保土ケ谷区","旭区","瀬谷区","泉区","戸塚区","栄区","港南区","南区","磯子区","金沢区"];
  const oi = w => { const i = order.indexOf(w); return i < 0 ? 99 : i; };
  wards.sort((a,b) => oi(a) - oi(b));
  const box = document.getElementById("area-opts");
  box.innerHTML = `<button class="opt" id="f-area-all" data-v="all" aria-pressed="true">すべて</button>` +
    wards.map((w,i) => `<button class="opt" id="f-area-${i}" data-v="${w}" aria-pressed="false">${w}</button>`).join("");
}

function bind(){
  document.querySelectorAll(".opts[data-key]").forEach(box => {
    box.addEventListener("click", ev => {
      const b = ev.target.closest(".opt"); if (!b) return;
      const key = box.dataset.key, v = b.dataset.v;
      if (box.dataset.multi) {
        const on = b.getAttribute("aria-pressed") !== "true";
        b.setAttribute("aria-pressed", on);
        on ? state.flags.add(v) : state.flags.delete(v);
      } else {
        box.querySelectorAll(".opt").forEach(o => o.setAttribute("aria-pressed", o === b));
        state[key] = v;
      }
      render();
    });
  });
  document.getElementById("q").addEventListener("input", e => { state.q = e.target.value.trim(); render(); });
  document.getElementById("reset").addEventListener("click", () => {
    state.day = "all"; state.age = "all"; state.area = "all"; state.q = ""; state.flags.clear();
    document.getElementById("q").value = "";
    document.querySelectorAll(".opts[data-key]").forEach(box => box.querySelectorAll(".opt").forEach(o => {
      o.setAttribute("aria-pressed", box.dataset.multi ? "false" : String(o.dataset.v === "all"));
    }));
    render();
  });
}
{ const AREA_WARD = { mm:"西区", yamashita:"中区", "yokohama-st":"西区", honmoku:"中区", kodomonokuni:"青葉区", zoorasia:"旭区", centerkita:"都筑区" };
  const seen = new Set(FAC.map(f => f[1]));
  Object.entries(FOOD).forEach(([k, a]) => (a.shops || []).forEach(sh => { if (!seen.has(sh.n)) { seen.add(sh.n); FAC.push(["r" + hashKey(sh.n), sh.n, AREA_WARD[k] || "西区", "food"]); } }));
  BABYFOOD_SHOPS.forEach(sh => { if (!seen.has(sh.n)) { seen.add(sh.n); FAC.push(["r" + hashKey(sh.n), sh.n, sh.ward || "西区", "food"]); } }); }
const FAC_BY_NAME = Object.fromEntries(FAC.map(f => [f[1], f[0]]));
function dmSummary(fac){
  const c = {}; fac.reps.forEach(r => { if (r.dm && r.dm !== "unk") c[r.dm] = (c[r.dm] || 0) + 1; });
  const parts = DM_OPTS.filter(([v]) => c[v]).map(([v,l]) => `${l} ${c[v]}件`);
  if (!parts.length) return null;
  const papaOk = (c.men || 0) + (c.multi || 0) + (c.room || 0), ng = (c.nomen || 0) + (c.women || 0);
  const cls = papaOk >= CONFIRM && papaOk >= ng * 2 ? "conf" : (papaOk && ng) ? "split" : "one";
  return { cls, text: parts.join("・") };
}
let REPORTS = [], VERIFIED = {}, MYDOC = null, DB = null, UID = null, IS_OWNER = false, VIEW = "fac", CAN_WRITE = true;

function ymLabel(ym){ if (!ym) return ""; const [y,m] = ym.split("-"); return `${y}年${Number(m)}月`; }
function nowYM(){ const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`; }
function hashKey(str){ let h = 0; for (const c of str) h = (h*31 + c.codePointAt(0)) >>> 0; return "o" + h.toString(36); }
function facInfo(r){ return { key:r.fk, name:r.fname, ward:r.ward }; }

function aggregate(){
  const map = {};
  for (const f of FAC) map[f[0]] = { key:f[0], name:f[1], ward:f[2], reps:[] };
  for (const r of REPORTS) { if (!map[r.fk]) map[r.fk] = { key:r.fk, name:r.fname, ward:r.ward, reps:[] }; map[r.fk].reps.push(r); }
  return map;
}
function itemStatus(fac, k){
  const v = VERIFIED[fac.key];
  if (v && (v[k] === "yes" || v[k] === "no")) return { cls:"staff", text:`運営確認済み・${v[k]==="yes"?"あり":"なし"}（${ymLabel(v.ym)}）`, yes:v[k]==="yes" };
  const yes = fac.reps.filter(r => r[k] === "yes"), no = fac.reps.filter(r => r[k] === "no");
  const latest = arr => arr.map(r => r.ym || "").sort().pop();
  if (!yes.length && !no.length) return { cls:"none", text:"まだ投稿がありません", yes:null };
  if (yes.length >= CONFIRM && yes.length >= no.length * 2) return { cls:"conf", text:`利用者確認済み・あり（${yes.length}件・${ymLabel(latest(yes))}現在）`, yes:true };
  if (no.length >= CONFIRM && no.length >= yes.length * 2) return { cls:"conf", text:`利用者確認済み・なし（${no.length}件・${ymLabel(latest(no))}現在）`, yes:false };
  if (yes.length && no.length) return { cls:"split", text:`情報が分かれています（あり${yes.length}件・なし${no.length}件）`, yes:null };
  const arr = yes.length ? yes : no;
  return { cls:"one", text:`利用者の情報・${yes.length?"あり":"なし"}（${arr.length}件・${ymLabel(latest(arr))}）`, yes:!!yes.length };
}

function rStatus(fac, it){
  const [k, l, y, n] = it; const st = itemStatus(fac, k); if (st.cls === "none" || st.cls === "staff") return null;
  return { cls: st.cls, text: st.text.replace("・あり", "・" + y).replace("・なし", "・" + n).replace("（あり", "（" + y).replace("なし", n).replace("あり", y) };
}
function facCard(fac){
  const dms = dmSummary(fac);
  const stats = ITEMS.map(([k,l]) => { const s = itemStatus(fac,k); return `<div class="st"><span class="k">${l}</span><span class="badge ${s.cls}">${esc(s.text)}</span></div>`; }).join("")
    + (dms ? `<div class="st"><span class="k">おむつ台の場所</span><span class="badge ${dms.cls}">${esc(dms.text)}</span></div>` : "")
    + R_ITEMS.map(it => { const r = rStatus(fac, it); return r ? `<div class="st"><span class="k">${it[1]}</span><span class="badge ${r.cls}">${esc(r.text)}</span></div>` : ""; }).join("");
  const cm = fac.reps.filter(r => r.note).sort((a,b) => (b.at||"").localeCompare(a.at||"")).slice(0,5);
  const cmts = cm.length ? `<ul class="cmts">${cm.map(r => `<li><span>${esc(r.note)}</span><span class="ym">${esc(ymLabel(r.ym))}${IS_OWNER ? ` <button class="btn sub" data-del="${esc(r.uid)}|${esc(r.id)}" type="button">削除</button>` : ""}</span></li>`).join("")}</ul>` : "";
  const v = VERIFIED[fac.key] || {};
  const sel = (k) => `<label>${ITEMS.find(i=>i[0]===k)[1]} <select data-vk="${k}"><option value="">未確認</option><option value="yes"${v[k]==="yes"?" selected":""}>あり</option><option value="no"${v[k]==="no"?" selected":""}>なし</option></select></label>`;
  const own = IS_OWNER ? `<div class="own" data-fk="${esc(fac.key)}"><div class="tri"><span class="q">運営確認</span>${sel("d")}${sel("f")}${sel("w")}<label>確認した月 <input type="month" data-vym value="${esc(v.ym || nowYM())}"></label></div><button class="btn sub" data-save type="button">運営確認として保存</button></div>` : "";
  return `<div class="fac"><h4>${esc(fac.name)}<small>${esc(fac.ward)}・投稿${fac.reps.length}件</small></h4><div class="stats">${stats}</div>${cmts}${own}</div>`;
}

function renderPosts(){
  const map = aggregate();
  const facs = Object.values(map).sort((a,b) => b.reps.length - a.reps.length || WARDS.indexOf(a.ward) - WARDS.indexOf(b.ward));
  const box = document.getElementById("p-list");
  const has = f => f.reps.length || VERIFIED[f.key];
  const rest = fs => { const e = fs.filter(f => !has(f)); return e.length ? `<p class="lead">まだ投稿がない場所：${e.map(f => esc(f.name)).join("、")}</p>` : ""; };
  const cards = fs => { const h = fs.filter(has); return h.length ? `<div class="foodall">${h.map(facCard).join("")}</div>` : ""; };
  if (VIEW === "fac") box.innerHTML = (cards(facs) || `<p class="lead">まだ投稿はありません。最初の1件をお待ちしています。</p>`) + rest(facs);
  else {
    const wards = WARDS.filter(w => facs.some(f => f.ward === w));
    box.innerHTML = wards.map(w => { const fs = facs.filter(f => f.ward === w); const n = fs.reduce((a,f)=>a+f.reps.length,0);
      return `<h3 class="wardh">${w}（${fs.length}か所・投稿${n}件）</h3>${cards(fs)}${rest(fs)}`; }).join("");
  }
  // カード内の赤ちゃん設備にも反映
  document.querySelectorAll("[data-spot]").forEach(el => {
    const key = FAC_BY_NAME[el.dataset.spot]; const fac = key && map[key]; if (!fac) return;
    const parts = ITEMS.map(([k,l]) => { const s = itemStatus(fac,k); return s.cls === "none" ? "" : `<span class="badge ${s.cls}">${l}：${esc(s.text)}</span>`; }).filter(Boolean);
    const dms = dmSummary(fac); if (dms) parts.push(`<span class="badge ${dms.cls}">おむつ台の場所：${esc(dms.text)}</span>`);
    R_ITEMS.forEach(it => { const r = rStatus(fac, it); if (r) parts.push(`<span class="badge ${r.cls}">${it[1]}：${esc(r.text)}</span>`); });
    el.innerHTML = parts.length ? `<p class="usermark">みんなの投稿：</p><div class="legend">${parts.join("")}</div>` : "";
  });
}

function buildForm(){
  const fsel = document.getElementById("p-fac");
  fsel.innerHTML = `<option value="">選んでください</option>` + WARDS.filter(w => FAC.some(f=>f[2]===w)).map(w =>
    `<optgroup label="${w}">${FAC.filter(f=>f[2]===w && !f[3]).map(f=>`<option value="${f[0]}">${esc(f[1])}</option>`).join("")}</optgroup>`).join("")
    + `<optgroup label="飲食店">${FAC.filter(f=>f[3]==="food").map(f=>`<option value="${f[0]}">${esc(f[1])}</option>`).join("")}</optgroup>` + `<option value="__other">その他（リストにない場所・お店）</option>`;
  document.getElementById("p-oward").innerHTML = WARDS.map(w=>`<option>${w}</option>`).join("");
  for (const [k] of ITEMS) document.getElementById("tri-"+k).insertAdjacentHTML("beforeend",
    [["yes","あった"],["no","なかった"],["unk","分からない"]].map(([v,l]) => `<label><input type="radio" name="r-${k}" id="r-${k}-${v}" value="${v}"${v==="unk"?" checked":""}>${l}</label>`).join(""));
  document.getElementById("tri-rest").innerHTML = R_ITEMS.map(([k,l,y,n]) => `<div class="tri"><span class="q">${l}</span>` +
    [["yes",y],["no",n],["unk","分からない"]].map(([v,t]) => `<label><input type="radio" name="r-${k}" value="${v}"${v==="unk"?" checked":""}>${t}</label>`).join("") + `</div>`).join("");
  document.getElementById("tri-dm").insertAdjacentHTML("beforeend",
    DM_OPTS.map(([v,l]) => `<label><input type="radio" name="r-dm" value="${v}"${v==="unk"?" checked":""}>${l}</label>`).join(""));
  document.getElementById("p-ym").value = nowYM();
  fsel.addEventListener("change", () => { document.getElementById("p-other").hidden = fsel.value !== "__other"; });
}

function setMsg(t, cls){ const m = document.getElementById("p-msg"); m.textContent = t; m.className = "pmsg " + (cls||""); }

async function submitReport(ev){
  ev.preventDefault();
  if (!DB || !UID) return;
  const fsel = document.getElementById("p-fac").value;
  let fk, fname, ward;
  if (!fsel) { setMsg("場所を選んでください。", "err"); return; }
  if (fsel === "__other") {
    fname = document.getElementById("p-oname").value.trim(); ward = document.getElementById("p-oward").value;
    if (!fname) { setMsg("場所の名前を入れてください。", "err"); return; }
    fk = hashKey(fname + "|" + ward);
  } else { const f = FAC.find(x => x[0] === fsel); fk = f[0]; fname = f[1]; ward = f[2]; }
  const val = k => document.querySelector(`input[name="r-${k}"]:checked`).value;
  const r = { id: Date.now().toString(36), fk, fname, ward, d:val("d"), f:val("f"), w:val("w"), dm:(document.querySelector('input[name="r-dm"]:checked') || {}).value || "unk", ...Object.fromEntries(R_ITEMS.map(([k]) => [k, (document.querySelector(`input[name="r-${k}"]:checked`) || {}).value || "unk"])),
    ym: document.getElementById("p-ym").value || nowYM(), note: document.getElementById("p-note").value.trim().slice(0,100), at: new Date().toISOString() };
  if (r.d === "unk" && r.f === "unk" && r.w === "unk" && r.dm === "unk" && R_ITEMS.every(([k]) => r[k] === "unk") && !r.note) { setMsg("どれか1つは「あった／なかった」を選んでください。", "err"); return; }
  const btn = document.getElementById("p-submit"); btn.disabled = true; setMsg("送信しています…");
  try {
    const items = (MYDOC && Array.isArray(MYDOC.items)) ? MYDOC.items.slice() : [];
    items.push(r);
    await DB.doc("reports/" + UID).set({ items: items.slice(-200) });
    setMsg("投稿しました。ありがとうございます！", "ok");
    document.getElementById("p-note").value = "";
  } catch (e) {
    if (e && e.code === "invalid_argument") { CAN_WRITE = false; setMsg("この共有のされ方では投稿できません。ページの持ち主に「投稿できる」権限で共有してもらってください。", "err"); }
    else if (e && e.code === "quota_exceeded") setMsg("保存できる量の上限に達しました。ページの持ち主に知らせてください。", "err");
    else setMsg("送信できませんでした。少し時間をおいてもう一度お試しください。", "err");
  } finally { btn.disabled = !CAN_WRITE; }
}

async function saveVerified(wrap){
  const fk = wrap.dataset.fk; const data = { ym: wrap.querySelector("[data-vym]").value || nowYM() };
  wrap.querySelectorAll("[data-vk]").forEach(s => { data[s.dataset.vk] = s.value || null; });
  try { await DB.doc("verified/" + fk).set(data); } catch (e) { alertBox("保存できませんでした。"); }
}
async function deleteReport(uid, id){
  try {
    const snap = await DB.doc("reports/" + uid).get(); if (!snap.exists) return;
    const items = (snap.data().items || []).filter(r => r.id !== id);
    await DB.doc("reports/" + uid).set({ items });
  } catch (e) { alertBox("削除できませんでした。"); }
}
function alertBox(t){ setMsg(t, "err"); }

async function initPosts(){
  if (!document.getElementById("posts")) return; // 投稿の受付は休止中
  buildForm();
  document.getElementById("pform").addEventListener("submit", submitReport);
  document.getElementById("v-fac").addEventListener("click", () => { VIEW="fac"; document.getElementById("v-fac").setAttribute("aria-pressed","true"); document.getElementById("v-ward").setAttribute("aria-pressed","false"); renderPosts(); });
  document.getElementById("v-ward").addEventListener("click", () => { VIEW="ward"; document.getElementById("v-ward").setAttribute("aria-pressed","true"); document.getElementById("v-fac").setAttribute("aria-pressed","false"); renderPosts(); });
  document.getElementById("p-list").addEventListener("click", e => {
    const save = e.target.closest("[data-save]"); if (save) { saveVerified(save.closest(".own")); return; }
    const del = e.target.closest("[data-del]"); if (del) { const [u,i] = del.dataset.del.split("|"); deleteReport(u,i); }
  });
  renderPosts();
  if (!window.claude || !window.claude.use) { setMsg("投稿はClaudeのページとして開いたときに使えます。"); return; }
  const timer = setTimeout(() => setMsg("投稿データにまだつながりません。少し待つか、開き直してください。", "err"), 10000);
  let user = null;
  try { [DB, user] = await Promise.all([claude.use("db"), claude.use("user")]); } catch (e) { DB = null; }
  if (!DB) { clearTimeout(timer); setMsg("投稿はClaudeにログインして開いたときに使えます。"); return; }
  try { UID = user ? await user.id() : null; IS_OWNER = user ? !!(await Promise.resolve(user.isOwner())) : false;
        const cw = user ? await Promise.resolve(user.can("data.write")) : null; if (cw === false && !IS_OWNER) CAN_WRITE = false; } catch (e) {}
  DB.collection("reports").onSnapshot(snap => {
    clearTimeout(timer);
    const all = [];
    for (const d of snap.docs) { const items = (d.data() || {}).items; if (Array.isArray(items)) for (const r of items) if (r && r.fk) all.push({ ...r, uid: d.id }); if (d.id === UID) MYDOC = d.data(); }
    REPORTS = all; renderPosts();
    if (!UID) setMsg("投稿するにはClaudeにログインしてください。");
    else if (!CAN_WRITE) setMsg("このページは閲覧のみで共有されています。投稿するには「投稿できる」権限で共有してもらってください。");
    else { document.getElementById("p-submit").disabled = false; if (document.getElementById("p-msg").textContent.includes("読み込んで")) setMsg(""); }
  }, e => { clearTimeout(timer); setMsg("投稿データを読み込めませんでした。開き直してください。", "err"); });
  DB.collection("verified").onSnapshot(snap => { const v = {}; for (const d of snap.docs) v[d.id] = d.data(); VERIFIED = v; renderPosts(); }, () => {});
}


document.getElementById("line-page").href = lineUrl("KidsTrip（キッズトリップ）横浜の子連れおでかけ・イベント一覧\nイベント・天気・近くのごはん・授乳室がまとめて見られるよ\n" + PAGE_URL);
document.getElementById("copy-page").addEventListener("click", async (ev) => {
  const b = ev.currentTarget, old = b.textContent;
  try { await navigator.clipboard.writeText(PAGE_URL); b.textContent = "コピーしました"; }
  catch (e) { b.textContent = PAGE_URL; }
  setTimeout(() => { b.textContent = old; }, 2000);
});
// トップの「☆ お気に入り」：お気に入りに入れたイベントだけを見る（もう一度押すと戻す）
(function(){
  const b = document.getElementById("fav-page"); if (!b) return;
  const sync = () => b.setAttribute("aria-pressed", state.flags.has("fav") ? "true" : "false");
  b.addEventListener("click", () => {
    if (!FAVS.size && !state.flags.has("fav")) { const old = b.textContent; b.textContent = "☆ 各イベントの☆で入れられます"; setTimeout(() => { b.textContent = old; }, 2500); return; }
    const o = document.querySelector('.opts[data-key="flags"] .opt[data-v="fav"]'); if (o) o.click();
    sync(); track("fav_view", state.flags.has("fav") ? "見る" : "戻す", "");
    if (state.flags.has("fav")) { const r = document.getElementById("results"); if (r) window.scrollTo({ top: r.getBoundingClientRect().top + window.scrollY - 80, behavior: "smooth" }); }
  });
  document.addEventListener("click", ev => { if (ev.target.closest('.opt[data-v="fav"], .pchip[data-flag="fav"], #reset')) setTimeout(sync, 0); });
})();

// 背景：7:00〜19:00は昼、19:01〜6:59は夜（見ている人の端末の時刻）
function setHeroTime(){
  const h = document.querySelector(".hero"); if (!h) return;
  const d = new Date(), m = d.getHours() * 60 + d.getMinutes();
  const day = m >= 420 && m <= 1140;
  h.classList.toggle("day", day); h.classList.toggle("night", !day);
}
setHeroTime(); setInterval(setHeroTime, 60000);
setupAreas();
document.getElementById("total").textContent = EVENTS.length;
bind();
restoreState();
render();
openFromLink();
renderFoodAll();
initPosts();
// カードの「くわしく」（ごはん・おむつ・行き方など）を開いたとき
document.addEventListener("toggle", ev => {
  if (!TRACK_ON) return;
  const d = ev.target; if (!d || d.tagName !== "DETAILS" || !d.open) return;
  const sm = d.querySelector("summary"), label = sm ? sm.textContent.replace(/[（(].*$/, "").trim().slice(0, 40) : "";
  const where = d.closest("[data-ev]"); track("detail", label, where ? where.dataset.ev : "");
}, true);
document.addEventListener("click", ev => {
  if (!TRACK_ON) return;
  const b = ev.target.closest(".morebtn"); if (!b) return;
  const g = b.closest("section"), h = g && g.querySelector("h2"); track("more", h ? h.firstChild.textContent.trim().slice(0, 40) : "");
});
{ const o = document.getElementById("origin"); if (o) { o.value = ORIGIN; o.addEventListener("change", ev => setOrigin(ev.target.value)); } }
{ const a = document.getElementById("arrive"); if (a) { a.value = ARRIVE; a.addEventListener("change", ev => setArrive(ev.target.value)); document.getElementById("arrive-clear").addEventListener("click", () => { a.value = ""; setArrive(""); }); } }
initNear();
(function(){
  const btn = document.getElementById("theme-btn"); if (!btn) return;
  const cur = () => document.documentElement.getAttribute("data-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => { btn.textContent = cur() === "dark" ? "☀️ 明るい表示にする" : "🌙 暗い表示にする"; };
  label();
  btn.addEventListener("click", () => {
    const next = cur() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (_) {}
    label();
  });
})();
renderWeather();
renderOutfit();
// イベントのエリア早見ボタン（押すと絞り込んで一覧までスクロール）
function renderEvArea(){
  const box = document.getElementById("evarea"); if (!box) return;
  const src = [...document.querySelectorAll("#area-opts .opt")];
  box.innerHTML = `<span class="albl">エリア：</span>` + src.map(b => `<button type="button" class="achip${b.getAttribute("aria-pressed") === "true" ? " on" : ""}" data-id="${b.id}">${esc(b.textContent)}</button>`).join("");
  box.querySelectorAll(".achip").forEach(c => c.addEventListener("click", () => {
    const o = document.getElementById(c.dataset.id); if (o) o.click();
    renderEvArea();
    const r = document.querySelector(".count"); if (r) r.scrollIntoView({ behavior: "smooth", block: "start" });
  }));
}
document.getElementById("area-opts").addEventListener("click", () => setTimeout(renderEvArea, 0));
document.getElementById("reset") && document.getElementById("reset").addEventListener("click", () => setTimeout(renderEvArea, 0));
renderEvArea();
// 絞り込みの日付ボタンを押したら、その日の服装イメージに切り替える
document.addEventListener("click", ev => {
  const b = ev.target.closest('button[id^="f-day-"]'); if (!b) return;
  const i = WX.findIndex(w => w.d === b.dataset.v); if (i < 0) return;
  OUTFIT_DAY = i; renderOutfit();
});
const TRACK_ON = !!TRACK_URL && /(github\.io|kidstrip\.jp)$/.test(location.hostname);
let TRACK_VID = ""; try { TRACK_VID = localStorage.getItem("vid") || ""; if (!TRACK_VID) { TRACK_VID = Math.random().toString(36).slice(2, 10); localStorage.setItem("vid", TRACK_VID); } } catch (_) {}
try { const q = new URLSearchParams(location.search).get("me"); if (q === "1") localStorage.setItem("me", "1"); if (q === "0") localStorage.removeItem("me"); if (q === "1" || q === "0") setTimeout(() => { const d = document.createElement("div"); d.textContent = q === "1" ? "この端末からの記録に「自分_」の印を付けます（やめるときは ?me=0 を開く）" : "この端末の「自分」の印を外しました"; d.style.cssText = "position:fixed;left:12px;right:12px;bottom:12px;z-index:99;background:#17324a;color:#fff;padding:10px 12px;border-radius:10px;font-size:14px"; document.body.appendChild(d); setTimeout(() => d.remove(), 5000); }, 300); if (localStorage.getItem("me") === "1") TRACK_VID = "自分_" + TRACK_VID; } catch (_) {}
const TRACK_DEV = /iPhone|iPod/.test(navigator.userAgent) ? "iPhone" : /iPad/.test(navigator.userAgent) ? "iPad" : /Android/.test(navigator.userAgent) ? (/Mobile/.test(navigator.userAgent) ? "Androidスマホ" : "Androidタブレット") : "PC";
let TRACK_TZ = ""; try { TRACK_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (_) {}
const TRACK_LANG = (navigator.language || "").slice(0, 10);
// 端末の時間帯の設定から、日本か海外かのめやすを出す（位置は使わない）
const TRACK_JP = TRACK_TZ ? (TRACK_TZ === "Asia/Tokyo" ? "日本" : "海外") : "";
const TRACK_APP = /\bLine\//i.test(navigator.userAgent) ? "LINEアプリ内" : /Instagram/.test(navigator.userAgent) ? "Instagramアプリ内" : /FBAN|FBAV/.test(navigator.userAgent) ? "Facebookアプリ内" : "ブラウザ";
// 現在地は送らず、「横浜市のあたり／神奈川県内／県外」の大まかな区分だけにする（範囲は目安）
function coarseArea(c){
  const [la, lo] = c;
  if (la > 35.31 && la < 35.60 && lo > 139.47 && lo < 139.70) return "横浜市のあたり";
  if (la > 35.13 && la < 35.67 && lo > 138.91 && lo < 139.80) return "神奈川県内";
  return "県外";
}
function track(type, value, target){
  if (!TRACK_ON) return;
  const qs = new URLSearchParams(location.search);
  let ref = qs.get("utm_source") || qs.get("ref") || ""; if (!ref) { try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch (_) {} }
  const body = JSON.stringify({ type, value: String(value || "").slice(0, 200), target: String(target || "").slice(0, 200), dev: TRACK_DEV, app: TRACK_APP, ref: ref.slice(0, 100), vid: TRACK_VID, page: (location.hash || "#events").slice(0, 40), lang: TRACK_LANG, tz: TRACK_TZ.slice(0, 40), jp: TRACK_JP, ua: navigator.userAgent.slice(0, 160), bot: navigator.webdriver ? "1" : "" });
  try { if (navigator.sendBeacon) navigator.sendBeacon(TRACK_URL, new Blob([body], { type: "text/plain" })); else fetch(TRACK_URL, { method: "POST", body, mode: "no-cors", keepalive: true }); } catch (_) {}
}
track("pageview", document.title);
document.addEventListener("click", ev => {
  if (!TRACK_ON) return;
  const a = ev.target.closest("a"), opt = ev.target.closest(".opts[data-key] .opt, #evarea .achip"), tab = ev.target.closest("#tabs a[data-tab]");
  const where = ev.target.closest("[data-ev]"), name = where ? where.dataset.ev : "";
  if (tab) return track("tab", tab.textContent.trim());
  if (opt) { const box = opt.closest(".opts"); return track("filter", (box ? box.dataset.key + ":" : "area:") + opt.textContent.trim()); }
  if (!a) return;
  const href = a.getAttribute("href") || "";
  if (a.dataset.act === "official") return track("official", a.href, name);
  if (a.dataset.act === "resv") return track("resv", a.href, name);
  if (/^tel:/.test(href)) return track("tel", href.slice(4), name);
  if (/google\.[^/]+\/maps|transit\.yahoo/.test(href)) {
    const kind = /transit\.yahoo/.test(href) ? "Yahoo!乗換案内" : /travelmode=walking/.test(href) ? "徒歩ルート" : "Googleマップ";
    const ev2 = name && EVENTS.find(x => x.t === name), td = new Date(), tk = `${td.getMonth() + 1}/${td.getDate()}`;
    const when = ev2 ? (ev2.days.includes(tk) ? "・当日" : "・前もって") : "";
    return track("route", `${kind}（出発：${ORIGIN || "未入力"}${when}）`, name);
  }
  if (/line\.me\/R\/share/.test(href)) return track("line_share", name ? "イベント" : "ページ", name);
  if (/^https?:/.test(href) && !href.includes(location.hostname)) return track("outlink", a.href, name);
});
{ const o = document.getElementById("origin"); if (o) o.addEventListener("change", () => { const v = o.value.trim(); if (v) track("origin", v.replace(/駅$/, "")); });
  const ns = document.getElementById("near-st"); if (ns) ns.addEventListener("change", () => { if (ns.value) track("near", "駅：" + ns.value); });
}
{ let tq = null, last = ""; const q = document.getElementById("q");
  if (q) q.addEventListener("input", () => { clearTimeout(tq); tq = setTimeout(() => { const v = q.value.trim(); if (v && v !== last) { last = v; track("search", v, document.getElementById("n") ? document.getElementById("n").textContent + "件" : ""); } }, 1500); }); }
{ const cb = document.getElementById("chains-body"); if (cb) cb.innerHTML = `<h3>離乳食・子ども無料のチェーン</h3><ul class="chains">${BABYFOOD_CHAINS.map(c => `<li><b>${esc(c.n)}</b>${esc(c.t)}<span class="src">（${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.src)}</a>` : esc(c.src)}）</span></li>`).join("")}</ul>
  <h3>ファミレスの子ども向けサービス</h3><ul class="chains">${CHAINS.filter(c => c.n !== "デニーズ").map(c => `<li><b>${esc(c.n)}</b>${esc(c.t)}<span class="src">（${esc(c.src)}）</span></li>`).join("")}</ul>`; }
function showTab(name, scroll){
  // 送られたリンクの後ろに「）」などが付いても開けるように（例：#gakudo%EF%BC%89）
  try { name = decodeURIComponent(name || ""); } catch (e) {}
  name = String(name).replace(/[^a-z].*$/, "");
  if (!TABS[name]) name = "events";
  for (const [k, sels] of Object.entries(TABS)) sels.forEach(sel => document.querySelectorAll(sel).forEach(el => { el.hidden = k !== name; }));
  document.querySelectorAll("#tabs a").forEach(a => { const on = a.dataset.tab === name; a.classList.toggle("on", on); if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  if (name === "gakudo" && typeof gkLoad === "function") gkLoad();
  if (name === "near" && typeof renderNear === "function" && near && near.c) renderNear();
  if (scroll) { const nav = document.getElementById("tabs"); const y = nav.getBoundingClientRect().top + window.scrollY; if (window.scrollY > y) window.scrollTo({ top: y }); }
}
document.getElementById("tabs").addEventListener("click", ev => {
  const a = ev.target.closest("a[data-tab]"); if (!a) return;
  ev.preventDefault();
  try { history.replaceState(null, "", "#" + a.dataset.tab); } catch (_) {}
  showTab(a.dataset.tab, true);
});
window.addEventListener("hashchange", () => showTab(location.hash.slice(1), true));
showTab(location.hash.slice(1), false);

// ---- 区ごとの無料の遊び場（タブ「🛝 無料の遊び場」）----
// 載せる条件：いつでも行ける（ongoing）・無料・遊び場／動物／乗り物のフラグがあるもの。build_pages.py の play_ok と同じ条件にする。
const WARD_ORDER = ["鶴見区","神奈川区","西区","中区","南区","港南区","保土ケ谷区","旭区","磯子区","金沢区","港北区","緑区","青葉区","都筑区","戸塚区","栄区","泉区","瀬谷区"];
const PLAY_TYPES = ["プレイルーム","支援拠点","ログハウス","公園","モール・施設"];
function playOk(e){ return e.kind === "ongoing" && e.price === "free" && (e.freeplay || e.animal || e.ride); }
function playType(e){
  if (/地域子育て支援拠点/.test(e.t)) return "支援拠点";
  if (/地区センター|コミュニティハウス/.test(e.t)) return "プレイルーム";
  if (/ログハウス/.test(e.t)) return "ログハウス";
  if (/屋外/.test(e.place || "") || /公園|広場|ふるさと村/.test(e.t)) return "公園";
  return "モール・施設";
}
function playWards(e){ return /^各区/.test(e.t) ? ["市内のまとめ"] : String(e.ward || "").split("・"); }
function playName(e){ return e.t.replace(/（[^（）]*区）$/, "").replace(/（([^（）]*区)の地域子育て支援拠点）$/, "（子育て支援拠点）"); }
const PLAY = { q: "", ward: "", type: "", age: "" };
try { const sv = JSON.parse(localStorage.getItem("playstate") || "null"); if (sv) Object.assign(PLAY, { ward: sv.ward || "", type: sv.type || "", age: sv.age || "" }); } catch (_) {}
function playMatch(e, skip){
  if (skip !== "ward" && PLAY.ward && !playWards(e).includes(PLAY.ward)) return false;
  if (skip !== "type" && PLAY.type && playType(e) !== PLAY.type) return false;
  if (skip !== "age" && PLAY.age) {
    const a = e.age || [0, 99], pl = e.place || "";
    if (PLAY.age === "baby" && a[0] > 2) return false;
    if (PLAY.age === "pre" && !(a[0] <= 6 && a[1] >= 3)) return false;
    if (PLAY.age === "sch" && a[1] < 7) return false;
    if (PLAY.age === "in" && !/屋内/.test(pl)) return false;
    if (PLAY.age === "out" && !/屋外/.test(pl)) return false;
  }
  if (PLAY.q) {
    const hay = [e.t, e.venue, e.ward, e.sum, e.tip, e.time, playType(e), ...(e.circles || []).map(c => c.n + c.what + "サークル")].join(" ");
    if (!PLAY.q.split(/\s+/).every(w => hay.includes(w))) return false;
  }
  return true;
}
function renderPlay(){
  const out = document.getElementById("play-out"); if (!out) return;
  const all = EVENTS.filter(playOk);
  const opt = (k, v, label, n) => `<button type="button" class="opt" data-k="${k}" data-v="${esc(v)}" aria-pressed="${PLAY[k] === v}">${esc(label)}${n === undefined ? "" : ` <small>${n}</small>`}</button>`;
  const wards = [...WARD_ORDER, "市内のまとめ"].filter(w => all.some(e => playWards(e).includes(w)));
  const cnt = (k, f) => all.filter(e => playMatch(e, k) && f(e)).length;
  document.getElementById("play-ward").innerHTML = opt("ward", "", "すべての区") + wards.map(w => { const n = cnt("ward", e => playWards(e).includes(w)); return n ? opt("ward", w, w.replace(/区$/, ""), n) : ""; }).join("");
  document.getElementById("play-type").innerHTML = opt("type", "", "すべての種類") + PLAY_TYPES.map(t => { const n = cnt("type", e => playType(e) === t); return n ? opt("type", t, t, n) : ""; }).join("");
  document.getElementById("play-age").innerHTML = opt("age", "", "すべての年齢・場所") + [["baby","0〜2歳"],["pre","3〜6歳"],["sch","小学生"],["in","屋内"],["out","屋外"]].map(([v, l]) => opt("age", v, l)).join("");
  const hit = all.filter(e => playMatch(e));
  document.getElementById("play-n").textContent = `${hit.length}か所` + (PLAY.ward || PLAY.type || PLAY.age || PLAY.q ? `（全${all.length}か所から絞り込み）` : "");
  const li = e => `<li><details><summary><b>${esc(playName(e))}</b><span class="chip free">${esc(playType(e))}</span><span class="chip">${esc((e.place || "").replace(/（.*/, ""))}</span><span class="chip">${esc(e.ageText || "")}</span>${e.circles && e.circles.length ? `<span class="chip">👟 サークル${e.circles.length}</span>` : ""}</summary>
    <div class="pld"><div>📍 ${esc(e.venue || "")}</div>${e.time ? `<div>🕘 ${esc(e.time)}</div>` : ""}${e.period ? `<div>📆 ${esc(e.period)}</div>` : (e.wk ? `<div>📆 ${esc(e.wk)}</div>` : "")}
    ${e.sum ? `<div>${esc(e.sum)}</div>` : ""}${e.tip ? `<div>💡 ${esc(e.tip)}</div>` : ""}
    ${e.circles && e.circles.length ? `<div class="plc"><b>👟 子ども向けサークル（地区センターで活動）</b><ul>${e.circles.map(c => `<li>${esc(c.n)}：${esc(c.what)}／${esc(c.when)}／${esc(c.age)}</li>`).join("")}</ul><span class="plw">活動日は団体の登録時の情報で、変わっていることがあります。入会・見学は地区センターに問い合わせ。${e.circlesUrl ? `<a href="${esc(e.circlesUrl)}" target="_blank" rel="noopener" data-play-out="${esc(e.id)}">サークル紹介 ↗</a>` : ""}（${esc(e.circlesAsof || "")}）</span></div>` : ""}
    <div class="lk"><a href="${esc(e.url)}" target="_blank" rel="noopener" data-play-out="${esc(e.id)}">公式ページ ↗</a><a href="?e=${encodeURIComponent(e.id)}#events">近くのおむつ替え・ごはん</a><a href="${esc(evLink(e))}">この場所のページ</a>${favBtn(e)}</div>
    <div class="plw">出典：${esc(e.src || "")}（${esc(e.asof || "")}時点）</div></div></details></li>`;
  const groups = PLAY.ward ? [PLAY.ward] : [...WARD_ORDER, "市内のまとめ"];
  const html = groups.map(w => { const xs = hit.filter(e => playWards(e).includes(w)); if (!xs.length) return "";
    xs.sort((a, b) => PLAY_TYPES.indexOf(playType(a)) - PLAY_TYPES.indexOf(playType(b)) || a.t.localeCompare(b.t, "ja"));
    return `<h3>${esc(w)}（${xs.length}）</h3><ul class="pl">${xs.map(li).join("")}</ul>`; }).join("");
  out.innerHTML = html || `<p class="note">条件に合う場所がありません。条件を減らしてみてください。</p>`;
}
{ const sec = document.getElementById("play");
  if (sec) {
    let tq = null;
    sec.addEventListener("click", ev => {
      const b = ev.target.closest("button.opt[data-k]"); if (b) { const k = b.dataset.k, v = b.dataset.v; PLAY[k] = PLAY[k] === v ? "" : v;
        try { localStorage.setItem("playstate", JSON.stringify({ ward: PLAY.ward, type: PLAY.type, age: PLAY.age })); } catch (_) {}
        renderPlay(); if (v) track("play", k + "：" + v, document.getElementById("play-n").textContent); return; }
      const a = ev.target.closest("a[data-play-out]"); if (a) track("play_open", a.dataset.playOut);
    });
    const q = document.getElementById("play-q");
    q.addEventListener("input", () => { PLAY.q = q.value.trim(); renderPlay(); clearTimeout(tq); tq = setTimeout(() => { if (PLAY.q) track("play", "検索：" + PLAY.q, document.getElementById("play-n").textContent); }, 1500); });
    renderPlay();
  }
}

// ---- 学童・放課後（タブ「🎒 学童・放課後」）。データ tools/gakudo.json はタブを開いたときだけ読む ----
var GK = { rows: null, q: "", ward: "", type: "", ans: {} };
const GK_TYPE = { kids: "キッズクラブ", club: "学童（児童クラブ）", hamakko: "はまっ子" };
const GK_SLUG = {"鶴見区":"tsurumi","神奈川区":"kanagawa","西区":"nishi","中区":"naka","南区":"minami","港南区":"konan","保土ケ谷区":"hodogaya","旭区":"asahi","磯子区":"isogo","金沢区":"kanazawa","港北区":"kohoku","緑区":"midori","青葉区":"aoba","都筑区":"tsuzuki","戸塚区":"totsuka","栄区":"sakae","泉区":"izumi","瀬谷区":"seya"};
function gkLoad(){
  const sec = document.getElementById("gakudo"); if (!sec || !GK || GK.rows || GK.loading) return;
  GK.loading = true;
  fetch(sec.dataset.src).then(r => r.json()).then(rows => { GK.rows = rows; renderGk(); }).catch(() => { document.getElementById("gk-out").innerHTML = '<p class="note">読み込めませんでした。<a href="/gakudo/">区ごとの一覧</a>をご覧ください。</p>'; });
}
function gkNorm(s){ return String(s || "").normalize("NFKC").replace(/[ヶケ]/g, "ケ").replace(/小学校|小$/g, "").toLowerCase(); }
function gkMatch(r, skip){
  if (skip !== "ward" && GK.ward && r.ward !== GK.ward) return false;
  if (skip !== "type" && GK.type && r.type !== GK.type) return false;
  if (GK.q) { const q = gkNorm(GK.q).replace(/小学校|小$/g, ""); if (!q) return true;
    if (!gkNorm([r.name, r.schools, r.addr, r.ward, r.operator].join(" ")).includes(q)) return false; }
  return true;
}
function renderGk(){
  const rows = GK.rows; if (!rows) return;
  const opt = (k, v, label, n) => `<button type="button" class="opt" data-gk="${k}" data-v="${esc(v)}" aria-pressed="${GK[k] === v}">${esc(label)}${n === undefined ? "" : ` <small>${n}</small>`}</button>`;
  document.getElementById("gk-ward").innerHTML = opt("ward", "", "すべての区") + WARD_ORDER.map(w => { const n = rows.filter(r => r.ward === w && gkMatch(r, "ward")).length; return n ? opt("ward", w, w.replace(/区$/, ""), n) : ""; }).join("");
  document.getElementById("gk-type").innerHTML = opt("type", "", "すべての種類") + Object.keys(GK_TYPE).map(t => { const n = rows.filter(r => r.type === t && gkMatch(r, "type")).length; return n ? opt("type", t, GK_TYPE[t], n) : ""; }).join("");
  const hit = rows.filter(r => gkMatch(r));
  const out = document.getElementById("gk-out"), nEl = document.getElementById("gk-n");
  if (!GK.ward && !GK.q && !GK.type) { nEl.textContent = `全${rows.length}か所`; out.innerHTML = `<p class="note">区を選ぶか、小学校名で探してください。区ごとの一覧は<a href="/gakudo/">学童・放課後キッズクラブ一覧</a>でも見られます。</p>`; return; }
  nEl.textContent = `${hit.length}か所`;
  const show = hit.slice(0, 120);
  const card = r => { const where = r.addr || (r.schools ? r.schools + (/(学園|学校)$/.test(r.schools) ? "" : "小学校") + "の中" : "");
    const mq = encodeURIComponent(r.addr ? `横浜市${r.ward}${r.addr}` : `横浜市${r.ward} ${r.name.split("放課後")[0]}`);
    return `<li><details><summary><b>${esc(r.name)}</b><span class="chip ${r.type === "kids" ? "free" : ""}">${esc(GK_TYPE[r.type])}</span><span class="chip">${esc(r.ward)}</span></summary>
    <div class="pld">${where ? `<div>📍 ${esc(where)}</div>` : ""}${r.tel ? `<div>☎ <a href="tel:${esc(r.tel)}" data-gk-out="tel">${esc(r.tel)}</a></div>` : ""}${r.hours ? `<div>🕘 ${esc(r.hours)}</div>` : (r.type === "kids" ? `<div>🕘 平日 放課後〜19時・土曜 8時30分〜19時（区分で変わる。市の共通）</div>` : `<div>🕘 時間・料金はクラブに問い合わせ</div>`)}
    ${r.schools && r.type === "club" ? `<div>🏫 主な小学校：${esc(r.schools)}</div>` : ""}${r.operator ? `<div>運営：${esc(r.operator)}</div>` : ""}${r.note ? `<div>📝 ${esc(r.note)}</div>` : ""}
    <div class="lk"><a href="https://www.google.com/maps/search/?api=1&query=${mq}" target="_blank" rel="noopener" data-gk-out="map">地図</a><a href="/gakudo/${GK_SLUG[r.ward] || ""}/">${esc(r.ward)}の一覧</a><a href="${esc(r.src)}" target="_blank" rel="noopener" data-gk-out="src">区の案内 ↗</a></div>
    <div class="plw">出典：横浜市${esc(r.ward)}の案内（${esc(r.asof)}時点）</div></div></details></li>`; };
  out.innerHTML = hit.length ? `<ul class="pl">${show.map(card).join("")}</ul>${hit.length > show.length ? `<p class="note">ほか${hit.length - show.length}か所。区や小学校名で絞ってください。</p>` : ""}` : `<p class="note">見つかりませんでした。小学校名は「○○」だけ（「小学校」なし）でも探せます。</p>`;
}
function renderGkQuiz(){
  const a = GK.ans, el = document.getElementById("gk-result"); if (!el) return;
  document.querySelectorAll("#gk-quiz .gkq").forEach(q => q.querySelectorAll(".opt").forEach(b => b.setAttribute("aria-pressed", a[q.dataset.q] === b.dataset.v)));
  if (!a.away || !a.until) { el.innerHTML = ""; return; }
  const gen = a.gen === "yes", sat = a.sat === "yes";
  let k, why = [];
  if (a.away === "no") { k = "wk"; why.push("家に大人がいる場合は、すくすく（ゆうやけ・ほしぞら）は使えません。"); }
  else if (a.until === "16" && !sat) k = "wk";
  else if (a.until === "16" || a.until === "17") k = "yu";
  else k = "ho";
  const R = { wk: ["わくわく（区分1）", "無料", "平日の放課後〜16時。土曜はなく、夏休みなどは1日2時間ほど。"],
    yu: ["すくすく ゆうやけ（区分2A）", gen ? "無料（減免）" : "月2,000円（7・8月は2,500円）", "平日 放課後〜17時・土曜 8時30分〜17時・休みの日 8時〜17時。"],
    ho: ["すくすく ほしぞら（区分2B）", gen ? "月2,500円（7・8月は3,000円・減免）" : "月5,000円（7・8月は5,500円）", "平日 放課後〜19時・土曜 8時30分〜19時・休みの日 8時〜19時。"] }[k];
  const tips = [];
  if (k === "wk" && a.away === "yes") tips.push("たまに遅くなる日は、すくすくに空きがあれば「スポット利用」（1回800円＋おやつ代・19時まで）もあります。");
  if (k === "wk" && a.away === "no" && (a.until !== "16" || sat)) tips.push("わくわくは16時まで・土曜なしです。たまに遅くなる日は、空きがあれば「スポット利用」（1回800円＋おやつ代・19時まで）ができます。");
  if (k !== "wk") tips.push("すくすくに申し込むときは、就労証明書などが要ります。");
  if (a.until === "late") tips.push("キッズクラブは19時までです。20時・21時まで開いている学童（放課後児童クラブ）もあるので、下の一覧で「学童（児童クラブ）」を選んで、時間の欄を見てください。");
  if (a.away === "yes") tips.push("学校の外の学童（放課後児童クラブ）も選べます。学区の決まりがなく、送迎やお弁当があるクラブもあります（料金はクラブごと）。");
  el.innerHTML = `<div class="gkres"><p><b>目安：${esc(R[0])}</b>　料金：${esc(R[1])}</p><p>${esc(R[2])}${why.map(esc).join("")}</p><ul>${tips.map(t => `<li>${esc(t)}</li>`).join("")}</ul>
    <p class="note">ほかに、おやつ代（実費ほど）と保険料（年800円以下）がかかります。これは市の決まりから出した目安です。くわしくは各クラブ・区役所に確かめてください（申し込みは各クラブへ直接）。出典：<a href="https://www.city.yokohama.lg.jp/kosodate-kyoiku/hokago/hokagokids/houkago-kids.html" target="_blank" rel="noopener">横浜市「放課後キッズクラブ」</a></p></div>`;
  track("gakudo_quiz", R[0]);
}
{ const sec = document.getElementById("gakudo");
  if (sec) {
    let tq = null;
    sec.addEventListener("click", ev => {
      const qb = ev.target.closest("#gk-quiz .gkq .opt"); if (qb) { const q = qb.closest(".gkq").dataset.q; GK.ans[q] = GK.ans[q] === qb.dataset.v ? undefined : qb.dataset.v; renderGkQuiz(); return; }
      const b = ev.target.closest("button.opt[data-gk]"); if (b) { const k = b.dataset.gk, v = b.dataset.v; GK[k] = GK[k] === v ? "" : v; renderGk(); if (v) track("gakudo", k + "：" + v, document.getElementById("gk-n").textContent); return; }
      const a = ev.target.closest("a[data-gk-out]"); if (a) track("gakudo_open", a.dataset.gkOut);
    });
    const q = document.getElementById("gk-q");
    q.addEventListener("input", () => { GK.q = q.value.trim(); renderGk(); clearTimeout(tq); tq = setTimeout(() => { if (GK.q) track("gakudo", "検索：" + GK.q, document.getElementById("gk-n").textContent); }, 1500); });
    q.addEventListener("focus", gkLoad);
    if (/^#gakudo/.test(location.hash)) gkLoad();
  }
}

// 離乳食を温められる電子レンジがある施設（エリアをまたいで一覧）
function mwListHtml(){
  const all = Object.values(BABY).flat(), yes = all.filter(b => b.mw === true), no = all.filter(b => b.mw === false);
  if (!yes.length && !no.length) return "";
  return `<details class="fold mwlist"><summary>🍲 離乳食を温められる電子レンジがある施設（${yes.length}か所）</summary><div class="fbody">
    <ul class="flist">${yes.map(b => `<li><a href="/spot/${hashId(b.n)}/">${esc(b.n)}</a>　<span class="small">${esc(b.mwText || "")}</span></li>`).join("")}</ul>
    ${no.length ? `<p class="small">電子レンジがないと分かっている所：${no.map(b => esc(b.n.replace(/[（(].*$/, "").trim())).join("・")}</p>` : ""}
    <p class="small">表の「レンジ」が「？」の施設は、まだ確かめられていません。順番に公式の情報で確かめて足していきます。</p></div></details>`;
}

// カードの「くわしく見る」を開いた回数（どのイベントが気になられたか）
document.addEventListener("toggle", ev => { const d = ev.target; if (d && d.classList && d.classList.contains("evmore") && d.open) { const c = d.closest(".card"); track("card_open", "くわしく見る", c ? c.dataset.ev : ""); } }, true);

// 日にちボタン：月ごとにたたむ（はじめは最初の月だけ開く。選んでいる日がある月も開く）
(function(){
  const rows = [...document.querySelectorAll('.opts[data-key="day"] .mrow')]; if (!rows.length) return;
  rows.forEach((r, i) => {
    const lab = r.querySelector(".mlab"); if (!lab) return;
    const n = r.querySelectorAll(".opt").length;
    lab.setAttribute("role", "button"); lab.tabIndex = 0;
    const hint = document.createElement("button"); hint.type = "button"; hint.className = "mhint"; hint.textContent = `${n}日を見る ▸`;
    r.appendChild(hint);
    const set = open => { r.classList.toggle("closed", !open); lab.setAttribute("aria-expanded", open ? "true" : "false"); };
    const sel = r.querySelector('.opt[aria-pressed="true"]');
    set(i === 0 || !!sel);
    const toggle = () => set(r.classList.contains("closed"));
    lab.addEventListener("click", toggle);
    lab.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); toggle(); } });
    hint.addEventListener("click", () => set(true));
  });
})();
