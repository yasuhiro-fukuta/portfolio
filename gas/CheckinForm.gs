/**
 * ============================================================
 *  CheckinForm.gs - Check-In Form (宿泊者名簿) の取込 (v2.10.3)
 * ============================================================
 *  ★これは食事・オプションの注文フォーム (FormResponses / LatestOptions)
 *    とは別物。別スプレッドシートに回答が溜まる。
 *
 *    FormResponses  … 食事の注文、泉屋送迎・荷物・タクシー等のオプション
 *    Check-In Form  … 代表者氏名 / 住所 / 職業 / 電話番号 (宿泊者名簿)
 *
 *    v2.10.2 で「Check-In Form 未提出なら E列を赤字」を実装した際、
 *    誤って LatestOptions (= 食事フォーム) を見ていた。
 *    食事を注文していれば未提出でも提出済み扱いになってしまうため、
 *    参照先をこちらに直した。
 *
 *  突合キー: (Check-in Date, Room Name) → 清掃ボードの (宿泊日, 部屋)
 *    Room Name は "1st floor" / "2nd floor" で入ってくるので
 *    normalizeRoom() がそのまま 1F / 2F に解決できる。
 *
 *  列は「見出し名」で探す。フォームに設問を足して列がずれても
 *  壊れないようにするため、位置指定はしない。
 * ============================================================
 */

/**
 * Check-In Form の回答を読み、(宿泊日|部屋) → 提出情報 のマップを返す。
 *
 * @return {Object|null}
 *   マップ … 読めた場合 (空でも {} を返す)
 *   null  … スプレッドシートを開けない/設定が無い等で「判定不能」。
 *           この場合は未提出の警告を一切出さない (誤検知を防ぐため)。
 */
function loadCheckinFormEntries() {
  const F = CONFIG.CHECKIN_FORM || {};

  if (!F.SPREADSHEET_ID) {
    Logger.log('CHECKIN_FORM.SPREADSHEET_ID が未設定です。未提出の判定をスキップします。');
    return null;
  }

  let sh;
  try {
    const ss = SpreadsheetApp.openById(F.SPREADSHEET_ID);
    sh = F.SHEET_NAME ? ss.getSheetByName(F.SHEET_NAME) : null;
    if (!sh) sh = ss.getSheets()[0];
  } catch (e) {
    Logger.log(`Check-In Form を開けません (未提出の判定をスキップ): ${e}`);
    return null;
  }
  if (!sh) return null;

  const last = sh.getLastRow();
  const lastCol = sh.getLastColumn();
  if (last <= 1 || lastCol < 1) return {};

  const headers = sh.getRange(1, 1, 1, lastCol).getValues()[0]
    .map(h => String(h == null ? '' : h).trim());

  const iCheckin = findHeaderIndex(headers, F.HEADER_CHECKIN);
  const iRoom    = findHeaderIndex(headers, F.HEADER_ROOM);
  const iName    = findHeaderIndex(headers, F.HEADER_NAME);

  if (iCheckin < 0 || iRoom < 0) {
    Logger.log('Check-In Form の見出しが見つかりません (未提出の判定をスキップ)。');
    Logger.log(`  探した見出し: 宿泊日=${JSON.stringify(F.HEADER_CHECKIN)} / ` +
               `部屋=${JSON.stringify(F.HEADER_ROOM)}`);
    Logger.log(`  実際の見出し: ${JSON.stringify(headers)}`);
    return null;
  }

  const vals = sh.getRange(2, 1, last - 1, lastCol).getValues();
  const map = {};
  let skipped = 0;

  vals.forEach(row => {
    const d = fmtDate(row[iCheckin]);
    const room = normalizeRoom(row[iRoom]);
    if (!d || !room) { if (row[iCheckin] || row[iRoom]) skipped++; return; }

    const ts = toDate(row[0]);
    const tsMs = (ts && !isNaN(ts.getTime())) ? ts.getTime() : 0;
    const key = `${d}|${room}`;

    // 同じ日・同じ部屋で複数回出されていたら新しい方を残す
    if (!map[key] || tsMs >= map[key].tsMs) {
      map[key] = {
        tsMs: tsMs,
        submittedAt: ts,
        name: (iName >= 0) ? String(row[iName] || '').trim() : '',
        roomRaw: String(row[iRoom] || '').trim(),
      };
    }
  });

  dlog(`Check-In Form: ${Object.keys(map).length} 件を読み込み ` +
       `(日付/部屋が読めず除外 ${skipped} 件)`);
  return map;
}

/**
 * 見出し候補から列番号(0始まり)を探す。
 * 完全一致 → 部分一致(小文字) の順。見つからなければ -1。
 */
function findHeaderIndex(headers, candidates) {
  const cands = candidates || [];
  for (let c = 0; c < cands.length; c++) {
    const i = headers.indexOf(cands[c]);
    if (i >= 0) return i;
  }
  for (let i = 0; i < headers.length; i++) {
    const h = headers[i].toLowerCase();
    if (!h) continue;
    for (let c = 0; c < cands.length; c++) {
      if (h.indexOf(String(cands[c]).toLowerCase()) >= 0) return i;
    }
  }
  return -1;
}

/**
 * 各滞在に Check-In Form の提出状況を書き込む。
 *
 *   s.formDone      true=提出済み / false=未提出 / null=判定不能
 *   s.formName      フォームに書かれた代表者名 (表記ゆれの確認用)
 *   s.formSubmitted 提出日時
 *
 * 連泊の場合、フォームはチェックイン日で出されるのが原則だが、
 * 中日の日付で出す人もいるため滞在期間内も見る。
 */
function applyCheckinFormStatus(stays, entries) {
  const map = (entries === undefined) ? loadCheckinFormEntries() : entries;

  if (map === null) {
    stays.forEach(s => { s.formDone = null; });   // 判定不能
    return null;
  }

  let done = 0;
  stays.forEach(s => {
    let hit = map[`${s.checkin}|${s.room}`];

    if (!hit) {
      let d = addDaysStr(s.checkin, 1);
      let guard = 0;
      while (d < s.checkout && guard++ < 400) {
        if (map[`${d}|${s.room}`]) { hit = map[`${d}|${s.room}`]; break; }
        d = addDaysStr(d, 1);
      }
    }

    s.formDone = !!hit;
    if (hit) {
      done++;
      s.formName = hit.name;
      s.formSubmitted = hit.submittedAt;
    }
  });

  dlog(`Check-In Form 提出済み: ${done} / ${stays.length} 滞在`);
  return map;
}

/**
 * 診断: Check-In Form が実際に読めているかを確認する。
 * 「赤字が付かない / 付きすぎる」ときは、まずこれを実行する。
 */
function dumpCheckinForm() {
  const F = CONFIG.CHECKIN_FORM || {};
  Logger.log('=== Check-In Form 読み込み確認 ===');
  Logger.log(`SPREADSHEET_ID: ${F.SPREADSHEET_ID || '(未設定)'}`);
  Logger.log(`SHEET_NAME    : ${F.SHEET_NAME || '(先頭シート)'}`);

  const map = loadCheckinFormEntries();
  if (map === null) {
    Logger.log('!! 読み込めませんでした。上のエラー内容を確認してください。');
    Logger.log('   ・スプレッドシートIDが正しいか');
    Logger.log('   ・このスクリプトの実行者がそのファイルを開けるか');
    return;
  }

  const keys = Object.keys(map).sort();
  Logger.log(`読み込めた回答: ${keys.length} 件`);
  Logger.log('--- 直近20件 ---');
  keys.slice(-20).forEach(k => {
    const v = map[k];
    Logger.log(`  ${k}  ${v.name || '(氏名なし)'}  提出=${fmtDateTime(v.submittedAt) || '-'} ` +
               `(部屋の生値="${v.roomRaw}")`);
  });

  // 清掃ボードの滞在と突合してみる
  const bookings = loadLodgifyBookings();
  const stays = readStaysFromReservations();
  mergeLodgifyStays(stays, bookings);
  applyLodgifyPeople(stays, bookings);
  applyCheckinFormStatus(stays, map);

  const today = fmtDate(todayJst());
  const recent = stays.filter(s => s.checkin <= today && s.checkin >= addDaysStr(today, -14))
                      .sort((a, b) => (a.checkin < b.checkin ? -1 : 1));
  Logger.log(`\n--- 直近14日のチェックイン ${recent.length} 件の提出状況 ---`);
  recent.forEach(s => {
    Logger.log(`  ${s.checkin} ${s.room} ${(s.name || '(氏名未取得)')} → ` +
      (s.formDone ? `提出済み (フォーム上の氏名: ${s.formName || '-'})` : '★未提出'));
  });
}
