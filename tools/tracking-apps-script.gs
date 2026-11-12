/**
 * 横浜おでかけ一覧 — 使われ方の記録（Google Apps Script）
 *
 * サイト（GitHub Pages）から送られた記録を、このスプレッドシートにためます。
 * - 月ごとに「2026-11」のような名前のシートを自動で作って、1行ずつ追記します。
 * - 「まとめ」シートに、月ごとの合計と、よく検索された言葉・よく見られたイベント・出発駅などを毎日書き出します。
 * - 経路検索の「内容」には出発駅と、イベント当日に調べたか（当日／前もって）が入ります。
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
const HEADER = ["日時", "種類", "内容", "イベント・お店", "端末", "アプリ", "来た場所", "訪問者ID", "タブ"];
const TYPES = { pageview:"ページ表示", search:"検索", filter:"絞り込み", tab:"タブ", official:"公式サイト", route:"経路検索", tel:"電話", resv:"予約ページ", line_share:"LINEで送る", outlink:"ほかのリンク", origin:"出発駅", near:"近くで探す" };

function doPost(e) {
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (!TYPES[d.type]) return out_("ignored");
    const cut = (v, n) => String(v || "").replace(/[\r\n\t]/g, " ").slice(0, n);
    const now = new Date();
    const sh = monthSheet_(Utilities.formatDate(now, TZ, "yyyy-MM"));
    sh.appendRow([Utilities.formatDate(now, TZ, "yyyy/MM/dd HH:mm:ss"), TYPES[d.type], cut(d.value, 200), cut(d.target, 200), cut(d.dev, 20), cut(d.app, 20), cut(d.ref, 100), cut(d.vid, 12), cut(d.page, 40)]);
    return out_("ok");
  } catch (err) {
    return out_("error");
  }
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
  return sh;
}

// 毎日1回「まとめ」シートを作り直す
function updateSummary() {
  const ss = SpreadsheetApp.getActive();
  const months = ss.getSheets().map(s => s.getName()).filter(n => /^\d{4}-\d{2}$/.test(n)).sort();
  const cols = ["ページ表示", "訪問者数", "検索", "公式サイト", "経路検索", "電話", "予約ページ", "LINEで送る", "絞り込み"];
  const rows = [["月"].concat(cols)];
  let latest = null;
  months.forEach(m => {
    const v = ss.getSheetByName(m).getDataRange().getValues().slice(1);
    const c = {}; const vids = new Set();
    v.forEach(r => { c[r[1]] = (c[r[1]] || 0) + 1; if (r[7]) vids.add(r[7]); });
    rows.push([m].concat(cols.map(k => k === "訪問者数" ? vids.size : (c[k] || 0))));
    latest = { m, v };
  });
  let sum = ss.getSheetByName("まとめ") || ss.insertSheet("まとめ", 0);
  sum.clear();
  sum.getRange(1, 1).setValue("月ごとの合計（毎日自動で更新）").setFontWeight("bold");
  sum.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  sum.getRange(2, 1, 1, rows[0].length).setFontWeight("bold");
  if (!latest) return;
  // 最新の月のランキング
  const top = (type, col) => { const c = {}; latest.v.filter(r => r[1] === type).forEach(r => { const k = r[col]; if (k) c[k] = (c[k] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 20); };
  const blocks = [["よく検索された言葉", top("検索", 2)], ["公式サイトがよく開かれたイベント", top("公式サイト", 3)], ["経路検索が多いイベント", top("経路検索", 3)], ["よく使われた絞り込み", top("絞り込み", 2)], ["入力された出発駅", top("出発駅", 2)], ["近くで探す（駅・現在地）", top("近くで探す", 2)], ["来た場所", top("ページ表示", 6)], ["端末", top("ページ表示", 4)], ["アプリ", top("ページ表示", 5)]];
  let r0 = rows.length + 4;
  sum.getRange(r0 - 1, 1).setValue(latest.m + " のランキング").setFontWeight("bold");
  blocks.forEach(([title, list], i) => {
    const c0 = 1 + i * 3;
    sum.getRange(r0, c0).setValue(title).setFontWeight("bold");
    if (list.length) sum.getRange(r0 + 1, c0, list.length, 2).setValues(list);
  });
}

// 最初に1回だけ実行：まとめシートと、毎日の集計の予約を作る
function setup() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === "updateSummary") ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger("updateSummary").timeBased().everyDays(1).atHour(4).inTimezone(TZ).create();
  monthSheet_(Utilities.formatDate(new Date(), TZ, "yyyy-MM"));
  updateSummary();
}
