/**
 * 横浜おでかけ一覧 — 使われ方の記録（Google Apps Script）
 *
 * サイト（GitHub Pages）から送られた記録を、このスプレッドシートにためます。
 * - 月ごとに「2026-11」のような名前のシートを自動で作って、1行ずつ追記します。
 * - 「まとめ」シートに、月ごとの合計と、よく検索された言葉・よく見られたイベント・出発駅などを毎日書き出します。
 * - 経路検索の「内容」には出発駅と、イベント当日に調べたか（当日／前もって）が入ります。
 * - 全部の記録に、端末の言語と時間帯の設定（例：Asia/Tokyo）から出した「日本・海外」のめやすを付けます（位置は使いません）。
 * - 0件だった検索、カードの「くわしく」を開いた回数、「残りを見る」が押された回数もまとめに出します。
 * - ブラウザ情報（ユーザーエージェント）と「区分」（人／自分／ボット）も記録します。まとめは「人」だけで数えます。
 *   ブラウザ情報がない古い行（2026/11/19 に新しくデプロイする前）は、ボットか分からないので「人」に入れたまま、その数を別に出します。同じ人の10秒以内の同じ記録は1回にします。
 * - 「日別」シート（日ごとの表示回数）と「ページ別」シート（ページごとの表示回数と、ページの型・本文の字数。サイトの tools/pages.json を読む）も毎日作ります。
 *   ページの情報を読むため、初めて実行するときに「外部のサービスへの接続」の許可を求められます。
 *   「自分」は、サイトを ?me=1 で開いた端末（訪問者IDが「自分_」で始まる）と、下の OWN_VIDS に入れたID。
 *   「ボット」は、ブラウザ情報に bot・crawler などが入っているものや、自動操作のブラウザ。
 * - 出発駅・近くで探すの駅から「地域」（例：神奈川県横浜市中区）と「横浜市内／神奈川県内／県外」を出します。
 *   現在地は位置を送らず、サイト側で「横浜市のあたり／神奈川県内／県外」の大まかな区分にしてから送ります。
 *
 * 使い方（最初の1回だけ）
 * 1. 新しいGoogleスプレッドシートを作る → メニュー「拡張機能」→「Apps Script」
 * 2. 最初からある中身を全部消して、このファイルの中身を全部貼り付けて保存
 * 3. 上の関数の選択で「setup」を選んで「実行」→ 許可を求められたら自分のアカウントで許可
 *    （「まとめ」シートと、毎日の集計の予約が作られます）
 * 4. 右上「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
 *    次のユーザーとして実行：自分 ／ アクセスできるユーザー：全員 → 「デプロイ」
 * 5. 出てきた「ウェブアプリのURL」（https://script.google.com/macros/s/…/exec）をClaudeに伝える
 */

const TZ = "Asia/Tokyo";
const HEADER = ["日時", "種類", "内容", "イベント・お店", "端末", "アプリ", "来た場所", "訪問者ID", "タブ", "地域", "地域の区分", "言語", "時間帯の設定", "日本・海外", "ブラウザ情報", "区分"];
// 自分の端末の訪問者ID（「自分_」の印を付ける前の記録も、自分として除くため）
const OWN_VIDS = ["1wj62hoy", "rmxuelmd"];
const BOT_RE = /bot|crawl|spider|slurp|mediapartners|adsbot|headless|lighthouse|pagespeed|facebookexternalhit|python|curl|wget|preview|inspectiontool|googleother|google-read-aloud|bytespider|phantom|puppeteer|playwright|selenium/i;
function kindOf_(vid, ua, bot) {
  vid = String(vid || "");
  if (/^自分_/.test(vid) || OWN_VIDS.indexOf(vid) >= 0) return "自分";
  if (bot === "1" || BOT_RE.test(String(ua || ""))) return "ボット";
  return "人";
}
const TYPES = { pageview:"ページ表示", search:"検索", filter:"絞り込み", tab:"タブ", official:"公式サイト", route:"経路検索", tel:"電話", resv:"予約ページ", line_share:"LINEで送る", outlink:"ほかのリンク", origin:"出発駅", near:"近くで探す", detail:"くわしくを開いた", more:"残りを見る", fav:"お気に入り", copy_link:"リンクを送る・コピー", open_link:"送られたリンクから来た", play:"遊び場で探す", play_open:"遊び場のリンク", gakudo:"学童で探す", gakudo_open:"学童のリンク", gakudo_quiz:"学童の区分の目安", restore:"前回の続き", shisetsu:"施設で探す", shisetsu_open:"施設のリンク", matome:"特集を開いた（トップから）", matome_item:"特集から個別ページへ" };

function doPost(e) {
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (!TYPES[d.type]) return out_("ignored");
    // 文字のまま入れる（「11月20日」が日付に、「=…」が数式に変わらないよう、先頭に ' を付ける）
    const cut = (v, n) => { const s = String(v || "").replace(/[\r\n\t]/g, " ").slice(0, n); return s && /^[=+\-@\d０-９'\s]|月\s*\d+\s*日|^\d+\/\d+/.test(s) ? "'" + s : s; };
    const now = new Date();
    const sh = monthSheet_(Utilities.formatDate(now, TZ, "yyyy-MM"));
    const area = areaOf_(d.type, cut(d.value, 200));
    sh.appendRow([Utilities.formatDate(now, TZ, "yyyy/MM/dd HH:mm:ss"), TYPES[d.type], cut(d.value, 200), cut(d.target, 200), cut(d.dev, 20), cut(d.app, 20), cut(d.ref, 100), cut(d.vid, 12), cut(d.page, 40), area[0], area[1], cut(d.lang, 10), cut(d.tz, 40), cut(d.jp, 4), cut(d.ua, 160), kindOf_(d.vid, d.ua, d.bot)]);
    return out_("ok");
  } catch (err) {
    return out_("error");
  }
}
// 出発駅・近くで探すの駅から、住所（都道府県・市区町村）と「横浜市内／神奈川県内／県外」を出す
// 駅の場所はGoogleマップの住所検索（Apps Scriptに入っている機能）で調べ、結果は保存して使い回す
function areaOf_(type, value) {
  if (type === "near") {
    const m = /現在地から探す（(.+)）/.exec(value);
    if (m) return ["", m[1] === "横浜市のあたり" ? "横浜市内（目安）" : m[1] === "神奈川県内" ? "神奈川県内（横浜市外）" : "県外"];
    const st = /^駅：(.+)$/.exec(value); if (st) return stationArea_(st[1]);
    return ["", ""];
  }
  if (type === "origin") return stationArea_(value);
  return ["", ""];
}
function stationArea_(name) {
  name = String(name).replace(/駅$/, "").trim(); if (!name) return ["", ""];
  const props = PropertiesService.getScriptProperties(), key = "st:" + name, saved = props.getProperty(key);
  if (saved) return JSON.parse(saved);
  let res = ["分からない", "分からない"];
  try {
    const g = Maps.newGeocoder().setLanguage("ja").setRegion("jp").setBounds(34.8, 138.4, 36.4, 140.9).geocode(name + "駅");
    const addr = g && g.results && g.results[0] ? g.results[0].formatted_address : "";
    const m = /(東京都|北海道|京都府|大阪府|.{2,3}県)(.+?市.+?区|.+?[市区町村])/.exec(addr);
    if (m) {
      const pref = m[1], city = m[2];
      res = [pref + city, /^横浜市/.test(city) && pref === "神奈川県" ? "横浜市内" : pref === "神奈川県" ? "神奈川県内（横浜市外）" : "県外"];
    }
  } catch (err) {}
  try { props.setProperty(key, JSON.stringify(res)); } catch (err) {}
  return res;
}

function doGet() { return out_("ok"); }
function out_(t) { return ContentService.createTextOutput(t); }

function monthSheet_(name) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    const lock = LockService.getScriptLock(); lock.waitLock(10000);
    try {
      sh = ss.getSheetByName(name);
      if (!sh) {
        sh = ss.insertSheet(name, 1);
        sh.appendRow(HEADER); sh.setFrozenRows(1); sh.getRange(1, 1, 1, HEADER.length).setFontWeight("bold");
      }
    } finally { lock.releaseLock(); }
  }
  // 列を足す前に作ったシートは、見出しの行だけ新しくする
  if (sh.getLastColumn() < HEADER.length) sh.getRange(1, 1, 1, HEADER.length).setValues([HEADER]).setFontWeight("bold");
  return sh;
}

// 行の区分：区分の列があればそれ。ブラウザ情報（UA）がない古い行は、訪問者IDだけで判定する（自分でなければ「人」。ボットかどうかは分からない）
function rowKind_(r) {
  const vid = String(r[7] || "");
  if (/^自分_/.test(vid) || OWN_VIDS.indexOf(vid) >= 0) return "自分";
  return r[15] || kindOf_(r[7], r[14], "");
}
// 同じ人が同じものを10秒以内にもう一度送った行（二重の記録・読み直し）は1回にする
function dedupe_(rows) {
  const last = {};
  return rows.filter(r => {
    const t = r[0] instanceof Date ? r[0].getTime() : new Date(String(r[0]).replace(/\//g, "-").replace(" ", "T") + "+09:00").getTime();
    const k = [r[7], r[1], r[2], r[8]].join("|");
    const dup = last[k] !== undefined && Math.abs(t - last[k]) <= 10000;
    last[k] = t;
    return !dup;
  });
}
function dayOf_(v) { return v instanceof Date ? Utilities.formatDate(v, TZ, "yyyy-MM-dd") : String(v).slice(0, 10).replace(/\//g, "-"); }

// 毎日1回「まとめ」シートを作り直す
function updateSummary() {
  const ss = SpreadsheetApp.getActive();
  const months = ss.getSheets().map(s => s.getName()).filter(n => /^\d{4}-\d{2}$/.test(n)).sort();
  const cols = ["ページ表示", "訪問者数", "1ページで帰った人", "1人あたりページ数", "検索", "公式サイト", "経路検索", "電話", "予約ページ", "LINEで送る", "絞り込み"];
  const rows = [["月"].concat(cols)];
  let latest = null;
  const excluded = [["月", "除いた行", "うち自分", "うちボット", "二重の記録", "「人」のうちブラウザ情報なし（ボットか分からない）"]];
  const daily = {};
  months.forEach(m => {
    const raw = ss.getSheetByName(m).getDataRange().getValues().slice(1);
    const all = dedupe_(raw);
    // 「人」だけで数える。UAを記録する前の行は「不明」として別に数える
    const v = all.filter(r => rowKind_(r) === "人");
    const n_ = k => all.filter(r => rowKind_(r) === k).length;
    excluded.push([m, raw.length - v.length, n_("自分"), n_("ボット"), raw.length - all.length, v.filter(r => !r[14]).length]);
    const c = {}; const vids = new Set(); const pv = {};
    v.forEach(r => { c[r[1]] = (c[r[1]] || 0) + 1; if (r[7]) vids.add(r[7]); if (r[1] === "ページ表示" && r[7]) pv[r[7]] = (pv[r[7]] || 0) + 1; });
    const pvs = Object.values(pv);
    const one = pvs.length ? Math.round(pvs.filter(x => x === 1).length / pvs.length * 100) + "%" : "";
    const per = pvs.length ? Math.round(pvs.reduce((a, b) => a + b, 0) / pvs.length * 100) / 100 : "";
    rows.push([m].concat(cols.map(k => k === "訪問者数" ? vids.size : k === "1ページで帰った人" ? one : k === "1人あたりページ数" ? per : (c[k] || 0))));
    // 日別（ページを直した日の前後で、見られ方が変わったかを見るため）
    all.forEach(r => {
      const d = dayOf_(r[0]), k = rowKind_(r);
      const o = daily[d] || (daily[d] = { pv: 0, vids: {}, off: 0, se: 0, sev: {}, un: 0, me: 0, bot: 0 });
      if (k === "人") { if (r[1] === "ページ表示") { o.pv++; if (/google|yahoo|bing/.test(String(r[6]))) { o.se++; if (r[7]) o.sev[r[7]] = 1; } if (!r[14]) o.un++; } if (r[7]) o.vids[r[7]] = 1; if (r[1] === "公式サイト") o.off++; }
      else if (k === "自分") o.me++; else o.bot++;
    });
    latest = { m, v };
  });
  let sum = ss.getSheetByName("まとめ") || ss.insertSheet("まとめ", 0);
  sum.clear();
  sum.getRange(1, 1).setValue("月ごとの合計（毎日自動で更新・自分とボットを除いた「人」だけ）").setFontWeight("bold");
  sum.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  sum.getRange(2, 1, 1, rows[0].length).setFontWeight("bold");
  const ec = rows[0].length + 2;
  sum.getRange(1, ec).setValue("集計から除いた行").setFontWeight("bold");
  sum.getRange(2, ec, excluded.length, excluded[0].length).setValues(excluded);
  sum.getRange(2, ec, 1, excluded[0].length).setFontWeight("bold");
  // 「日別」シート
  const dsh = ss.getSheetByName("日別") || ss.insertSheet("日別", 1);
  dsh.clear();
  const drows = [["日付", "ページ表示（人）", "訪問者数（人）", "うち検索から（ページ表示）", "検索から来た人", "公式サイト（人）", "うちブラウザ情報なし（ページ表示）", "自分", "ボット"]].concat(
    Object.keys(daily).sort().reverse().map(d => { const o = daily[d]; return ["'" + d, o.pv, Object.keys(o.vids).length, o.se, Object.keys(o.sev).length, o.off, o.un, o.me, o.bot]; }));
  dsh.getRange(1, 1, drows.length, drows[0].length).setValues(drows);
  dsh.getRange(1, 1, 1, drows[0].length).setFontWeight("bold"); dsh.setFrozenRows(1);
  if (!latest) return;
  pageSheet_(ss, latest);
  // 最新の月のランキング
  const txt_ = k => k instanceof Date ? Utilities.formatDate(k, TZ, "M月d日") : k;
  const top = (type, col) => { const c = {}; latest.v.filter(r => r[1] === type).forEach(r => { const k = txt_(r[col]); if (k) c[k] = (c[k] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 20); };
  const top2_ = () => { const c = {}; latest.v.filter(r => r[10]).forEach(r => c[r[10]] = (c[r[10]] || 0) + 1); return Object.entries(c).sort((a, b) => b[1] - a[1]); };
  const top3_ = () => { const c = {}; latest.v.filter(r => r[9]).forEach(r => c[r[9]] = (c[r[9]] || 0) + 1); return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 20); };
  // 前の版で日付に変わってしまった検索語（例：Fri Nov 20 2026）は、上の txt_ で「11月20日」に戻して数える
  const count_ = list => { const c = {}; list.forEach(k => { k = txt_(k); if (k) c[k] = (c[k] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 20); };
  const zero_ = () => count_(latest.v.filter(r => r[1] === "検索" && r[3] === "0件").map(r => r[2]));
  // 訪問者ごとに1回だけ数える：日本・海外、言語
  const perVisitor_ = col => { const seen = {}; latest.v.forEach(r => { if (r[7] && r[col] && !seen[r[7]]) seen[r[7]] = r[col]; }); return count_(Object.values(seen)); };
  // 出発駅・近くで探すから地域が分かった訪問者だけ、訪問者ごとに1回数える
  const visitorArea_ = () => { const seen = {}; latest.v.forEach(r => { if (r[7] && r[10] && r[10] !== "分からない") seen[r[7]] = r[10]; }); return count_(Object.values(seen)); };
  const blocks = [["日本・海外（訪問者数・端末の時間帯の設定から）", perVisitor_(13)], ["訪問者の地域（出発駅・近くで探すを使った人）", visitorArea_()], ["言語（訪問者数）", perVisitor_(11)], ["0件だった検索（載せていないもの）", zero_()], ["よく開かれた「くわしく」", top("くわしくを開いた", 2)], ["「残りを見る」が押された見出し", top("残りを見る", 2)], ["よく検索された言葉", top("検索", 2)], ["公式サイトがよく開かれたイベント", top("公式サイト", 3)], ["経路検索が多いイベント", top("経路検索", 3)], ["よく使われた絞り込み", top("絞り込み", 2)], ["学童：よく使われた探し方（区・種類・検索）", top("学童で探す", 2)], ["学童：区分の目安の結果", top("学童の区分の目安", 2)], ["遊び場：よく使われた探し方", top("遊び場で探す", 2)], ["施設：よく使われた探し方", top("施設で探す", 2)], ["入力された出発駅", top("出発駅", 2)], ["近くで探す（駅・現在地）", top("近くで探す", 2)], ["見ている人の地域の区分（出発駅・近くで探すから）", top2_()], ["見ている人の地域（市区町村）", top3_()], ["来た場所", top("ページ表示", 6)], ["端末", top("ページ表示", 4)], ["アプリ", top("ページ表示", 5)]];
  let r0 = rows.length + 4;
  sum.getRange(r0 - 1, 1).setValue(latest.m + " のランキング").setFontWeight("bold");
  blocks.forEach(([title, list], i) => {
    const c0 = 1 + i * 3;
    sum.getRange(r0, c0).setValue(title).setFontWeight("bold");
    if (list.length) sum.getRange(r0 + 1, c0, list.length, 2).setValues(list);
  });
}

// 「ページ別」シート：最新の月の、ページごとの表示回数（人）と、ページの型・本文の字数・個別ページへのリンク数を並べる
// ページの情報はサイトの tools/pages.json から読む（表示0回のページも出す）
function pageSheet_(ss, latest) {
  const info = {};
  try {
    const res = UrlFetchApp.fetch("https://kidstrip.jp/tools/pages.json", { muteHttpExceptions: true });
    if (res.getResponseCode() === 200) {
      const man = JSON.parse(res.getContentText());
      ["event", "spot"].forEach(k => Object.keys(man[k] || {}).forEach(id => {
        const p = man[k][id];
        info[k + "/" + id + "/"] = { name: p.name || "", type: p.type || "", chars: p.chars || "", links: p.links || "", state: p.ended ? "掲載終了" : p.thin ? "薄い（検索に出さない）" : "" };
      }));
      // まとめ記事（/matome/）・一覧・区のページ・学童のページ（pages.json の "gakudo" に、パスをキーにして入っている）
      Object.keys(man.gakudo || {}).forEach(path => {
        const p = man.gakudo[path];
        info[path] = { name: p.name || "", type: (/^matome\//.test(path) ? "特集・" : "") + (p.type || ""), chars: p.chars || "", links: p.links || "", state: "" };
      });
    }
  } catch (err) {}
  const pv = {}, vis = {}, off = {}, title = {}, toItem = {};
  latest.v.forEach(r => {
    let p = String(r[8] || "");
    if (/^#|^$/.test(p)) p = "（トップ）";
    if (r[1] === "ページ表示") { pv[p] = (pv[p] || 0) + 1; (vis[p] = vis[p] || {})[r[7]] = 1; if (!title[p]) title[p] = String(r[2]).slice(0, 60); }
    if (r[1] === "公式サイト") off[p] = (off[p] || 0) + 1;
    if (r[1] === "特集から個別ページへ") toItem[p] = (toItem[p] || 0) + 1;
  });
  const paths = Object.keys(Object.assign({}, info, pv));
  const list = paths.map(p => { const i = info[p] || {}; return ["'/" + p.replace(/^（トップ）$/, ""), i.name || title[p] || (p === "（トップ）" ? "トップ（一覧）" : ""), i.type || "", i.chars || "", i.links || "", i.state || "", pv[p] || 0, Object.keys(vis[p] || {}).length, off[p] || 0, toItem[p] || ""]; })
    .sort((a, b) => b[6] - a[6] || (b[3] || 0) - (a[3] || 0));
  const total = list.reduce((a, r) => a + r[6], 0);
  const live = list.filter(r => !r[5] && r[0] !== "'/");
  const top20 = list.slice(0, 20).reduce((a, r) => a + r[6], 0);
  const sh = ss.getSheetByName("ページ別") || ss.insertSheet("ページ別", 2);
  sh.clear();
  sh.getRange(1, 1, 1, 6).setValues([[latest.m + " のページ別（人だけ）", "掲載中のページ " + live.length, "表示0回 " + live.filter(r => !r[6]).length, "上位20ページの割合 " + (total ? Math.round(top20 / total * 100) : 0) + "%", "本文800字未満で表示あり " + live.filter(r => r[3] && r[3] < 800 && r[6]).length + "／" + live.filter(r => r[3] && r[3] < 800).length, ""]]).setFontWeight("bold");
  const head = [["パス", "名前", "型", "本文の字数（フッター除く）", "個別ページへのリンク", "状態", "表示回数", "訪問者数", "公式サイトを開いた", "特集から個別ページへ"]];
  sh.getRange(2, 1, 1, head[0].length).setValues(head).setFontWeight("bold");
  if (list.length) sh.getRange(3, 1, list.length, head[0].length).setValues(list);
  sh.setFrozenRows(2);
}

// 最初に1回だけ実行：まとめシートと、毎日の集計の予約を作る
function setup() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === "updateSummary") ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger("updateSummary").timeBased().everyDays(1).atHour(4).inTimezone(TZ).create();
  monthSheet_(Utilities.formatDate(new Date(), TZ, "yyyy-MM"));
  updateSummary();
}
