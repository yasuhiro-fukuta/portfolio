# 柏屋 予約同期 (Kashiwaya Reservation Sync) v2.10

Google スプレッドシート + Apps Script。Booking.com / Airbnb の iCal、
Lodgify Public API、Google フォームから宿泊者情報を集め、
**清掃予定表 (CleaningBoard)** と **食事予約表 (LatestOptions)** を作る。

---

## v2.10 で直した不具合

### 1. Lodgify 直予約の情報が取れない

**症状**: 自社予約ページ・Lodgify 管理画面から入った予約が清掃ボードに出ず、
実際には客がいる部屋が「空室」と表示される。

**原因**: Lodgify API からの取得自体は成功していた。落ちていたのは取得後の突合。
清掃ボードの在室骨格を `LatestReservations` (= Booking.com / Airbnb の iCal) だけから
作っており、`LodgifyBookings` は「その骨格に人数を後から載せる」用途にしか
使われていなかった。直予約はどの OTA の iCal にも現れないので、
骨格に行が無い = board にも出ない。

実データ (2026-09-02 時点) で確認した取りこぼし:

| 宿泊日 | 部屋 | 宿泊者 | 人数 | 修正前の表示 |
|---|---|---|---|---|
| 2026-11-24 | 2F | Gloria Cereda | 2 | OUT→空室 |
| 2026-11-25 | 2F | Michael Conor Cook | 2 | 空室 |
| 2027-03-31 | 1F | Amanda McLaughlin | 3 | 空室 |

**対策**: `CleaningBoard.gs` の `mergeLodgifyStays()` を追加。
iCal が押さえていない「夜」だけを拾って骨格に合流させる。

- 判定は **夜単位**。直予約でも Booking.com が `CLOSED` ブロックを出していれば
  iCal に夜が存在するので、その場合は従来どおり iCal の行に人数と氏名だけを載せる。
  **二重計上はしない。**
- 合流した行の備考には「直予約」と出る。
- OTA 予約なのに未来の夜が iCal に無い場合は
  「⚠iCal未掲載 (取得もれの可能性)」と出す。iCal 取得障害の早期発見用。
  (過去の夜は iCal が配信しないので無印)

### 2. 食事予約表の人数が取れないことがある

**症状**: `LatestOptions` の G列 (人数) が空欄のまま。

**原因**: 現行の Google フォームに人数設問が無い。
`Number of guests` は旧フォーム (21列目 / 28列目) にしか存在せず、
現行フォームからの回答では常に空欄になる。
実データでは有効44行のうち **23行** が空欄だった。

**対策**: `GuestCount.gs` の `backfillOptionGuests()` を追加。
毎バッチ、G列の空欄だけを次の優先順で埋める。

1. Lodgify API (権威データ)
2. 食事サマリの「N人前 / N人用」の最大値からの推定

すでに値が入っている行と、論理削除済みの行には触らない。
書き込むのは G列だけで、M列の曜日数式や L列「ほなみや転記済」には一切触れない。

実データでの結果: **23行中 21行を Lodgify から、2行を食事推定から補完し、未解決 0**。

### あわせて直した細かい不具合

| 箇所 | 内容 |
|---|---|
| `LodgifyFetcher.gs` | upsert キーが「解決後の部屋 (1F/2F)」だったため、`ROOM_MAP` を直すと同じ予約が別行として増え、古い行に「削除」が立っていた (実際に 149行まで膨張)。キーを `room_type_id` ベースの安定値に変更 |
| `GuestCount.gs` | 人数突合が `Array.find()` の先頭一致で、期間が重なる予約が複数あると行順まかせだった。`findLodgifyBooking()` に統一し、チェックイン完全一致 → 直近の重なり の順で選ぶ |
| `Utils.gs` | 全角数字 (`"１人前"` が実データに存在) で人数推定が 0 になっていた。`toHalfWidth()` を通してから解析 |
| `CleaningBoard.gs` | 連泊の中日の日付でフォームが出されると食事が丸ごと落ちていた。滞在期間内の日付も拾うようにした |
| `CleaningBoard.gs` | 毎行 `stays.filter()` を3回まわしていたのを日付×部屋の索引に変更 |
| `Main.gs` | 処理順を変更。Lodgify 取得をフォーム同期より **前** に移した。旧順序では人数補完が常に1バッチ前の Lodgify を見ることになり、当日入った予約の人数が1時間遅れていた |
| `IcalFetcher.gs` | 継続行 (先頭が空白) が iCal の1行目に来た場合に落ちる可能性があった |
| `ReservationSync.gs` | 引数の `now` を無視して内部で `nowJst()` を呼び直しており、バッチ内で時刻が食い違っていた |

---

## ファイル構成

| ファイル | 役割 |
|---|---|
| `Config.gs` | 全設定。列定義、iCal URL、ROOM_MAP、食事/オプションの対応表 |
| `Main.gs` | エントリポイント、毎時トリガー、カスタムメニュー |
| `IcalFetcher.gs` | Booking.com / Airbnb の iCal 取得とパース |
| `ReservationSync.gs` | 予約同期と消失(キャンセル)検知 |
| `LodgifyFetcher.gs` | Lodgify Public API v2 の取得と `LodgifyBookings` への upsert |
| `OptionSync.gs` | フォーム回答の取込、食事/オプションサマリ生成 |
| `GuestCount.gs` | **人数解決の共通ロジック** (v2.10 新規) |
| `CleaningBoard.gs` | 清掃予定表の生成 |
| `Diagnose.gs` | 突合が合わないときの原因切り分け |
| `Utils.gs` | 日付・全角変換などの共通処理 |

---

## 反映手順

1. Apps Script エディタで各ファイルの中身を差し替える。
   **`GuestCount.gs` は新規ファイル**なので追加すること。
2. スプレッドシートを開き直してメニュー「🏮 柏屋」を再読み込み。
3. 「🏨 Lodgify取得だけ実行」→「🧹 清掃ボードだけ再生成」の順に手動実行して確認。
4. 「🩺 直予約・人数の突合診断」でログを確認する。

`addDaysStr()` と `numOrZero()` は `Utils.gs` に集約した。
`CleaningBoard.gs` / `LodgifyFetcher.gs` に残っている旧定義があれば消すこと
(Apps Script は同名関数を後勝ちで上書きするため、重複すると事故のもとになる)。

## 既知の制限

- **`CONFIG.CLEANING.DAYS_AHEAD = 120`**。清掃ボードは今日から120日先までしか
  作らない。上の表の Amanda McLaughlin (2027-03-31) はまだこの範囲外なので、
  12月頃になるまで board には出てこない。取得済みで `LodgifyBookings` には
  入っているため、必要なら日数を伸ばす。
- Airbnb 経由の予約は Lodgify に入らないため人数が取れない。
  該当行は備考に「⚠人数不明 → CleaningOverride に記入」と出る
  (実データでは 2026-10-14 1F の1件)。
- `CONFIG.CLEANING.START_DATE` は固定。ここを変えると A〜D列の手動入力が
  日付とずれるので変更しないこと。
