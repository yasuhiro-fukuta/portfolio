#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
amazon_orders_to_csv.py  (cURL貼り付け方式 / 実HTML検証済み)
==========================================================================
amazon.co.jp の注文履歴から、指定「年・月」の経理用一覧を CSV で出力する。

取得項目（1注文 = 1行）:
    注文日 / 注文番号 / 品目 / 注文合計(品代) / カード課金額(ご請求額)
    / 利用ポイント / カードブランド / カード下4桁 / 注文URL

【毎月の操作】
  1. amazon.co.jp にログイン → 注文履歴を開く
     https://www.amazon.co.jp/gp/css/order-history
  2. F12 → ネットワーク → Ctrl+Shift+R →「ドキュメント」で絞る
  3. order-history(ドキュメント, 素の200) を右クリック → cURLとしてコピー(bash)
     ※「(サービスワーカーから)」が付く場合は アプリケーション > Service Workers >
       Bypass for network にチェックしてリロードしてから取得
  4. その内容を、この .py と同じフォルダの curl.txt に保存(UTF-8)
  5. 下の YEAR / MONTH / LIMIT を設定して  python amazon_orders_to_csv.py

  ※ curl.txt の中身(cookie)はアカウントのログイン情報そのもの。ローカルのみに置く。

【設計】公式APIは無いため、ログイン済みセッションで領収書 print.html を
        HTTP取得してパースする純コード(RPA非依存)。HTMLは変わり得る。

【2026-08 修正】直近月(7月)分が0件になる問題への対応:
  - 「領収書」の文言が本文に無いと全skipするゲートを撤廃。新形式の明細ページでは
    文言が変わるため、エラーページ検出＋注文番号/注文日の有無で判定する。
  - 注文日の対応形式を拡張(「2026年7月5日」に加え「2026/07/05」「2026-07-05」)。
  - print.html が解析できない注文は 注文詳細ページ(order-details) から再取得する
    フォールバックを追加。
  - 日付が読めなかった注文は黙って「対象外」で捨てず、警告付きでCSVに含める。
  - skip理由を分類して表示し、最後に内訳を集計する(原因切り分け用)。
==========================================================================
"""

import csv
import os
import random
import re
import shlex
import sys
import time
from collections import Counter

import requests
from bs4 import BeautifulSoup

# ==========================================================================
# ① 設定
# ==========================================================================
YEAR = 2026
MONTH = 7         # 例: 5 で5月分。None でその年の全件。
#   ↑ 初回テストは MONTH=None / LIMIT=3 推奨（3件だけ取得し動作確認）
#     本番は MONTH=対象月 / LIMIT=None

LIMIT = None            # 先頭 N 件だけ処理（動作確認用）。本番は None で全件。

CURL_FILE = "curl.txt"
OUTPUT_CSV = f"amazon_orders_{YEAR}{'' if MONTH is None else f'-{MONTH:02d}'}.csv"
SAVE_INVOICE_HTML = True
INVOICE_DIR = "invoices"

SLEEP_MIN, SLEEP_MAX = 1.2, 2.6
MAX_LIST_PAGES = 30
BASE = "https://www.amazon.co.jp"

# ==========================================================================
# ② 正規表現
# ==========================================================================
ORDER_ID = r"\d{3}-\d{7}-\d{7}"
ID_IN_LINK = re.compile(r"order[Ii][Dd]=(" + ORDER_ID + r")")
ID_RAW = re.compile(r"\b(" + ORDER_ID + r")\b")
SESSION_ID_RE = re.compile(r"session-id=(" + ORDER_ID + r")")

# 注文日: 新旧レイアウトの表記ゆれに対応。ラベル付きを優先し、
# 汎用パターンは値域チェック(find_date)で誤検出を弾く。
DATE_PATTERNS = [
    re.compile(r"注文日\s*[:：]?\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"),
    re.compile(r"注文日\s*[:：]?\s*(\d{4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})"),
    re.compile(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"),
    re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})"),
]

TOTAL_RE = re.compile(r"注文合計\s*[:：]?\s*[¥￥]?\s*([\d,]+)")
SUBTOTAL_RE = re.compile(r"商品の小計\s*[:：]?\s*[¥￥]?\s*([\d,]+)")
GRAND_RE = re.compile(r"(?:ご請求額|請求額|お支払い合計|支払い合計)\s*[:：]?\s*[¥￥]?\s*([\d,]+)")
POINT_RE = re.compile(r"(?:Amazon\s*ポイント|ポイント利用|利用ポイント)\s*[:：]?\s*-?\s*[¥￥]?\s*([\d,]+)")
# マスク(••••等)に続く4桁＝カード下4桁。改行(別span)も許容。
LAST4_RE = re.compile(r"(?:[••･・·＊●\*]{2,4})\s*(\d{4})")
LAST4_ALT_RE = re.compile(r"(?:下\s*4\s*桁|末尾)\D{0,10}(\d{4})")
CARD_BRANDS = ["Mastercard", "MasterCard", "マスターカード", "Visa", "VISA", "ビザ",
               "JCB", "American Express", "AMEX", "アメリカン・エキスプレス",
               "Diners", "ダイナース", "Discover"]
BRAND_ALIASES = {"MasterCard": "Mastercard", "マスターカード": "Mastercard",
                 "VISA": "Visa", "ビザ": "Visa",
                 "AMEX": "American Express",
                 "アメリカン・エキスプレス": "American Express",
                 "ダイナース": "Diners"}

ERROR_SIGNS = ["ご注文の詳細を読み込めません", "ご注文の詳細を表示できません"]
BLOCKED_SIGNS = ["ap/signin", "サインイン してください", "ロボットではありません",
                 "Enter the characters you see", "automated access"]

# ==========================================================================
# ③ cURL パース
# ==========================================================================
def parse_curl(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(
            f"【設定エラー】{path} が見つかりません。\n"
            "  注文履歴の order-history 行を右クリック → cURLとしてコピー(bash) し、\n"
            f"  その内容を {path} に保存してください。"
        )
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    raw = raw.replace("\\\n", " ").replace("^\n", " ").replace("`\n", " ")
    raw = raw.replace("\r", " ").replace("\n", " ")
    try:
        tokens = shlex.split(raw)
    except ValueError:
        tokens = []

    # curl.txt には複数のcurlコマンドが入り得る（広告等）。cookie候補を全部集めて、
    # 認証トークン(at-acbjp)を含むものを採用する。
    cookie_candidates: list[str] = []
    if tokens:
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in ("-H", "--header") and i + 1 < len(tokens):
                hv = tokens[i + 1]
                if ":" in hv:
                    name, val = hv.split(":", 1)
                    if name.strip().lower() == "cookie":
                        cookie_candidates.append(val.strip())
                i += 2; continue
            if t in ("-b", "--cookie") and i + 1 < len(tokens):
                cookie_candidates.append(tokens[i + 1].strip()); i += 2; continue
            i += 1
    else:
        for m in re.finditer(r"-H\s+(['\"])[Cc]ookie:\s*(.*?)\1", raw):
            cookie_candidates.append(m.group(2).strip())
        for m in re.finditer(r"-b\s+(['\"])(.*?)\1", raw):
            cookie_candidates.append(m.group(2).strip())

    # at-acbjp を含む候補を最優先。無ければ session-id を含むもの、最後に最長のもの。
    cookie = ""
    for c in cookie_candidates:
        if "at-acbjp=" in c or "at-main=" in c:
            cookie = c; break
    if not cookie:
        for c in cookie_candidates:
            if "session-id=" in c:
                cookie = c; break
    if not cookie and cookie_candidates:
        cookie = max(cookie_candidates, key=len)

    if not cookie:
        sys.exit(
            "【cookieが見つかりません】\n"
            "  コピーした cURL に cookie が含まれていません。原因はほぼ\n"
            "  『200 OK (サービスワーカーから)』です。\n"
            "  → DevTools の アプリケーション > Service Workers で 'Bypass for network' に\n"
            "    チェックを入れて Ctrl+R、素の『200 OK』になった order-history を\n"
            "    右クリック → cURLとしてコピー し直してください。\n"
            "  （cookie 内に at-acbjp= があれば認証OKの目印）"
        )
    if "at-acbjp=" not in cookie and "at-main=" not in cookie:
        print("【警告】cookieに at-acbjp= が見当たりません。未認証かも。続行します。",
              file=sys.stderr)

    sid_m = SESSION_ID_RE.search(cookie)
    session_id = sid_m.group(1) if sid_m else ""

    # 送信ヘッダは検証済み環境と揃えるためデスクトップ固定のクリーンなものにする
    # （curl.txt がモバイルUAだと一覧ページがモバイル型で返り、注文IDが拾えないため）
    send_headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
        "accept-language": "ja,en-US;q=0.9,en;q=0.8",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    return {"cookie": cookie, "headers": send_headers, "session_id": session_id}

# ==========================================================================
# ④ 取得・解析
# ==========================================================================
def make_session(curl: dict) -> requests.Session:
    s = requests.Session()
    s.headers.update(curl["headers"])
    s.headers["Cookie"] = curl["cookie"]
    return s


def check_blocked(html: str) -> None:
    head = html[:4000]
    for sign in BLOCKED_SIGNS:
        if sign in head:
            sys.exit(
                f"【セッション切れ/ロボット判定の可能性】検出: 「{sign}」\n"
                "→ 再ログインして cURL を取り直し、curl.txt を更新してください。")


def polite_sleep() -> None:
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def collect_order_ids(session: requests.Session, year: int, session_id: str) -> list[str]:
    """注文ID一覧を収集。orderID= リンクを優先抽出し、session-id等の誤検出を排除。"""
    found, seen = [], {session_id} if session_id else set()
    templates = [
        BASE + "/your-orders/orders?timeFilter=year-{year}&startIndex={idx}",
        BASE + "/gp/css/order-history?orderFilter=year-{year}&startIndex={idx}",
    ]
    for tmpl in templates:
        empty = 0
        for page in range(MAX_LIST_PAGES):
            url = tmpl.format(year=year, idx=page * 10)
            r = session.get(url, timeout=30)
            check_blocked(r.text)
            ids = ID_IN_LINK.findall(r.text)         # 第一候補: orderID= 限定
            if not ids:                              # フォールバック: 生正規表現
                ids = ID_RAW.findall(r.text)
            new = [i for i in dict.fromkeys(ids) if i not in seen]
            for i in new:
                seen.add(i); found.append(i)
            print(f"  一覧 page {page+1}: +{len(new)}件 (累計 {len(found)})")
            if not new:
                empty += 1
                if empty >= 2:
                    break
            else:
                empty = 0
            polite_sleep()
        if found:
            break
    return found


def find_date(text: str):
    """本文から注文日 (y, m, d) を探す。ラベル付き優先・値域チェックで誤検出排除。"""
    for rx in DATE_PATTERNS:
        for m in rx.finditer(text):
            y, mo, d = (int(x) for x in m.groups())
            if 2000 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                return y, mo, d
    return None


def parse_invoice(html: str, order_id: str):
    """領収書/注文詳細ページを解析。(row, None) または (None, skip理由) を返す。"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    if any(s in text for s in ERROR_SIGNS):
        return None, "エラーページ"

    date = find_date(text)
    # 「領収書」の文言は新形式ページに無いことがあるので判定に使わない。
    # 注文番号か注文日が読み取れれば注文ページとみなす。
    if order_id not in text and date is None:
        return None, "注文情報なし(HTML要確認)"

    if date:
        y, mo, d = date
        order_date = f"{y:04d}-{mo:02d}-{d:02d}"
    else:
        order_date, mo = "", None

    titles = []
    for a in soup.find_all("a", href=True):
        if re.search(r"/(?:dp|gp/product)/", a["href"]):
            t = a.get_text(" ", strip=True)
            if t and t not in titles:
                titles.append(t)
    item = " / ".join(titles)

    def grab(rx):
        mm = rx.search(text)
        return int(mm.group(1).replace(",", "")) if mm else None

    total, subtotal = grab(TOTAL_RE), grab(SUBTOTAL_RE)
    grand, points = grab(GRAND_RE), grab(POINT_RE)
    goods = total if total is not None else subtotal

    brand = next((b for b in CARD_BRANDS if b in text), "")
    brand = BRAND_ALIASES.get(brand, brand)
    m4 = LAST4_RE.search(text) or LAST4_ALT_RE.search(text)
    last4 = m4.group(1) if m4 else ""

    return {
        "month": mo, "注文日": order_date, "注文番号": order_id, "品目": item,
        "注文合計(品代)": goods if goods is not None else "",
        "カード課金額(ご請求額)": grand if grand is not None else "",
        "利用ポイント": points if points is not None else "",
        "カードブランド": brand, "カード下4桁": last4,
        "注文URL": f"{BASE}/gp/css/summary/print.html?orderID={order_id}",
    }, None


def _fetch_and_save(session: requests.Session, url: str, fname: str) -> str:
    r = session.get(url, timeout=30)
    check_blocked(r.text)
    if SAVE_INVOICE_HTML:
        os.makedirs(INVOICE_DIR, exist_ok=True)
        with open(os.path.join(INVOICE_DIR, fname), "w", encoding="utf-8") as f:
            f.write(r.text)
    return r.text


def fetch_invoice(session: requests.Session, order_id: str) -> str:
    url = f"{BASE}/gp/css/summary/print.html?orderID={order_id}"
    return _fetch_and_save(session, url, f"{order_id}.html")


def fetch_order_details(session: requests.Session, order_id: str) -> str:
    url = f"{BASE}/gp/css/order-details?orderID={order_id}"
    return _fetch_and_save(session, url, f"{order_id}_details.html")


def main() -> None:
    curl = parse_curl(CURL_FILE)
    session = make_session(curl)

    print(f"■ {YEAR}年 の注文ID一覧を取得中 …")
    order_ids = collect_order_ids(session, YEAR, curl["session_id"])
    print(f"  → {len(order_ids)} 件\n")
    if not order_ids:
        sys.exit("注文IDが0件。cookie失効か年指定ミスの可能性。curl.txt を取り直してください。")
    if LIMIT is not None:
        order_ids = order_ids[:LIMIT]
        print(f"  ※ LIMIT={LIMIT} のため先頭 {len(order_ids)} 件のみ処理（動作確認モード）\n")

    rows, skip_reasons = [], Counter()
    print("■ 各注文の領収書を取得・解析中 …")
    for n, oid in enumerate(order_ids, 1):
        tag = f"  [{n}/{len(order_ids)}] {oid}"
        try:
            row, reason = parse_invoice(fetch_invoice(session, oid), oid)
            if row is None:
                # print.html が読めなくても注文詳細ページなら取れることがある(新形式対策)
                polite_sleep()
                row2, reason2 = parse_invoice(fetch_order_details(session, oid), oid)
                if row2 is not None:
                    print(f"{tag} … print.html解析不可({reason}) → 注文詳細ページから取得")
                    row, reason = row2, None
        except Exception as e:  # noqa: BLE001
            print(f"{tag} 失敗: {e}")
            polite_sleep(); continue
        if row is None:
            skip_reasons[reason] += 1
            print(f"{tag} … skip: {reason}")
        elif MONTH is not None and row["month"] is not None and row["month"] != MONTH:
            print(f"{tag} … {row['注文日']} 対象外")
        else:
            if MONTH is not None and row["month"] is None:
                print(f"{tag} 【警告】注文日を読み取れず月判定不可。CSVに含めるので"
                      f" ./{INVOICE_DIR}/{oid}.html を確認してください")
            rows.append(row)
            print(f"{tag} … {row['注文日'] or '日付不明'} "
                  f"¥{row['カード課金額(ご請求額)']} ****{row['カード下4桁'] or '----'} "
                  f"{row['品目'][:30]}")
        polite_sleep()

    rows.sort(key=lambda x: x["注文日"])
    cols = ["注文日", "注文番号", "品目", "注文合計(品代)", "カード課金額(ご請求額)",
            "利用ポイント", "カードブランド", "カード下4桁", "注文URL"]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})

    skipped = sum(skip_reasons.values())
    print(f"\n✓ 完了: {len(rows)} 件 → {OUTPUT_CSV}"
          + (f"（skip {skipped} 件）" if skipped else ""))
    if skip_reasons:
        print("  skip内訳: " + " / ".join(f"{k}×{v}" for k, v in skip_reasons.items()))
    if not rows:
        print(f"【0件】skip内訳と ./{INVOICE_DIR}/ 内のHTML(特に *_details.html)を確認してください。")
    if SAVE_INVOICE_HTML:
        print(f"  領収書HTML: ./{INVOICE_DIR}/ (証憑用)")


if __name__ == "__main__":
    main()
