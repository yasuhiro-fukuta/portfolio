/**
 * ============================================================
 *  SelfTest.gs - 反映後の動作確認 (v2.10)
 * ============================================================
 *  ★このファイルはシートに一切書き込まない。読むだけ。
 *    何度実行しても安全なので、反映直後にまずこれを叩く。
 *
 *  使い方:
 *    Apps Script エディタで selfTest を選んで実行 → 実行ログを見る。
 *    (または メニュー「🏮 柏屋」→「✅ 反映後の自己診断」)
 *
 *  ここが全部 OK なら、配線とロジックは正しく入っている。
 *  そのうえで実データの中身を見たい場合は diagnoseLodgifyMatch を使う。
 * ============================================================
 */

function selfTest() {
  const R = { ok: 0, ng: 0, warn: 0 };
  const ok   = m => { R.ok++;   Logger.log('  OK   ' + m); };
  const ng   = m => { R.ng++;   Logger.log('  NG   ' + m); };
  const warn = m => { R.warn++; Logger.log('  !!   ' + m); };
  const eq = (label, got, want) =>
    (String(got) === String(want)) ? ok(`${label} = ${got}`)
                                   : ng(`${label} = ${got} (期待 ${want})`);

  Logger.log('======== 柏屋 予約同期 v2.10 自己診断 ========');

  // ── 1. ファイルが全部入っているか ──────────────────────────
  Logger.log('\n[1] 必要な関数が揃っているか');
  const needed = [
    'backfillOptionGuests', 'loadLodgifyBookings', 'findLodgifyBooking',
    'estimatePeopleFromMeal', 'isDirectLodgifySource',           // GuestCount.gs
    'mergeLodgifyStays', 'readStaysFromReservations', 'renderCleaningRows',
    'buildCleaningBoard',                                        // CleaningBoard.gs
    'lodgifyRowKey', 'syncLodgifyBookings',                      // LodgifyFetcher.gs
    'toHalfWidth', 'addDaysStr', 'numOrZero',                    // Utils.gs
    'syncOptions', 'runBatch', 'diagnoseLodgifyMatch',
  ];
  const g = (typeof globalThis !== 'undefined') ? globalThis : this;
  const missing = needed.filter(n => typeof g[n] !== 'function');
  if (missing.length) {
    ng(`未定義の関数: ${missing.join(', ')}`);
    Logger.log('       → 該当ファイルの貼り付け漏れです。特に GuestCount.gs は新規ファイルです。');
  } else {
    ok(`${needed.length} 個すべて定義済み`);
  }

  // ── 2. 旧バージョンの関数が残っていないか ───────────────────
  //  Apps Script は同名関数を「後勝ち」で上書きする。
  //  CleaningBoard.gs / LodgifyFetcher.gs に旧 addDaysStr / numOrZero が
  //  残っていると、Utils.gs の新しい定義が負けることがある。
  //  挙動で判定する (旧版は全角を落として 0 になる)。
  Logger.log('\n[2] 旧定義が残っていないか (全角の扱いで判定)');
  eq('numOrZero("１２")', numOrZero('１２'), 12);
  eq('estimatePeopleFromMeal("Chicken(１人前)")', estimatePeopleFromMeal('Chicken(１人前)'), 1);
  if (numOrZero('１２') !== 12 || estimatePeopleFromMeal('Chicken(１人前)') !== 1) {
    Logger.log('       → CleaningBoard.gs / LodgifyFetcher.gs の末尾に残っている');
    Logger.log('         旧 numOrZero() / addDaysStr() を削除してください。');
  }

  // ── 3. 単体ロジック ────────────────────────────────────────
  Logger.log('\n[3] 単体ロジック');
  eq('estimatePeopleFromMeal("Sukiyaki(4人前), Ochazuke(2人前)")',
     estimatePeopleFromMeal('Sukiyaki(4人前), Ochazuke(2人前)'), 4);
  eq('estimatePeopleFromMeal("Set(2人用)")', estimatePeopleFromMeal('Set(2人用)'), 2);
  eq('parsePersonCount("３ person - ¥8,000")', parsePersonCount('３ person - ¥8,000'), 3);
  eq('addDaysStr("2026-02-28", 1)', addDaysStr('2026-02-28', 1), '2026-03-01');
  eq('addDaysStr("2026-12-31", 1)', addDaysStr('2026-12-31', 1), '2027-01-01');

  // upsert キーが読み方によらず同じになること (数値/文字列/小数付き)
  const k1 = lodgifyRowKey(22483640, 860952);
  const k2 = lodgifyRowKey('22483640', '860952');
  const k3 = lodgifyRowKey('22483640.0', '860952.0');
  (k1 === k2 && k2 === k3 && k1 === '22483640|860952')
    ? ok(`lodgifyRowKey が安定 ("${k1}")`)
    : ng(`lodgifyRowKey が不安定: "${k1}" / "${k2}" / "${k3}"`);

  // 直予約の判定
  isDirectLodgifySource('yasuo.lodgify.com') === true &&
  isDirectLodgifySource('5326808288|6222108251') === false
    ? ok('isDirectLodgifySource の判定')
    : ng('isDirectLodgifySource の判定がおかしい');

  // ── 4. シートが揃っているか ────────────────────────────────
  Logger.log('\n[4] シートの存在');
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  [CONFIG.SHEET.LATEST_RES, CONFIG.SHEET.LATEST_OPT, CONFIG.SHEET.FORM_RAW,
   CONFIG.SHEET.LODGIFY, CONFIG.SHEET.CLEANING].forEach(n => {
    ss.getSheetByName(n) ? ok(`${n}`) : ng(`${n} が無い`);
  });

  // ── 5. Lodgify の取得結果 ──────────────────────────────────
  Logger.log('\n[5] LodgifyBookings の中身');
  const bookings = loadLodgifyBookings();
  if (!bookings.length) {
    ng('有効な Lodgify 予約が 0 件。「🏨 Lodgify取得だけ実行」を先に実行してください。');
  } else {
    ok(`有効な予約 ${bookings.length} 件`);
    const direct = bookings.filter(b => b.isDirect);
    direct.length ? ok(`うち直予約 ${direct.length} 件`)
                  : warn('直予約が 0 件。本当に無いなら正常です。');
    direct.forEach(b => Logger.log(
      `       直予約: ${b.room} ${b.checkin}→${b.checkout} ${b.name} ${b.people}名 src="${b.source}"`));
    const noRoom = bookings.filter(b => !b.room).length;
    noRoom ? ng(`部屋が解決できない有効行が ${noRoom} 件 → ROOM_MAP に room_type_id の追記が必要`)
           : ok('部屋はすべて 1F / 2F に解決済み');
    const noPeople = bookings.filter(b => !b.people).length;
    noPeople ? warn(`人数が 0 の行が ${noPeople} 件`)
             : ok('全行に人数が入っている');
  }

  // ── 6. 直予約が清掃ボードに載るか (メモリ上で再現。書き込まない) ──
  Logger.log('\n[6] 直予約が清掃ボードに載るか');
  const stays = readStaysFromReservations();
  ok(`iCal 由来の滞在 ${stays.length} 件`);
  const added = mergeLodgifyStays(stays, bookings);
  added ? ok(`Lodgify から補完した滞在 ${added} 件`)
        : warn('補完 0 件。iCal がすべての夜を押さえているなら正常です。');
  applyLodgifyPeople(stays, bookings);
  applyOptionsInfo(stays);
  applyOverride(stays);

  const today = fmtDate(todayJst());
  const futureDirect = stays.filter(s => s.origin === 'Lodgify' && s.checkout > today);
  futureDirect.forEach(s => Logger.log(
    `       補完: ${s.room} ${s.checkin}→${s.checkout} ${s.name} ${s.people}名 [${s.notes}]`));

  const rows = renderCleaningRows(stays);
  const C = CONFIG.COL_CLEAN, WS = CONFIG.CLEANING.WRITE_START_COL;
  ok(`生成される行数 ${rows.length} (E列〜T列の ${C.UPDATED_AT - WS + 1} 列)`);

  const occ = rows.filter(r => r[C.GUEST_NAME - WS]);
  const bySrc = {};
  occ.forEach(r => { const k = r[C.GUESTS_SRC - WS] || '(空)'; bySrc[k] = (bySrc[k] || 0) + 1; });
  Logger.log(`       在室行 ${occ.length} / 人数ソース ${JSON.stringify(bySrc)}`);

  const unknown = occ.filter(r => !r[C.GUESTS - WS] && r[C.DATE - WS] >= today);
  unknown.length ? warn(`今日以降で人数不明の行が ${unknown.length} 件 (CleaningOverride に記入)`)
                 : ok('今日以降で人数不明の行は無し');
  unknown.slice(0, 5).forEach(r => Logger.log(
    `       人数不明: ${r[C.DATE - WS]} ${r[C.ROOM - WS]} ${r[C.GUEST_NAME - WS]}`));

  const directRows = rows.filter(r => String(r[C.NOTE - WS]).indexOf('直予約') >= 0);
  Logger.log(`       「直予約」と表示される行: ${directRows.length}`);
  directRows.slice(0, 10).forEach(r => Logger.log(
    `       ${r[C.DATE - WS]} ${r[C.ROOM - WS]} ${r[C.STATE - WS]} ` +
    `${r[C.GUEST_NAME - WS]} ${r[C.GUESTS - WS]}名`));

  const icalMiss = rows.filter(r => String(r[C.NOTE - WS]).indexOf('iCal未掲載') >= 0);
  icalMiss.length ? warn(`iCal未掲載の警告が ${icalMiss.length} 行 (iCal取得もれの可能性)`)
                  : ok('iCal未掲載の警告は無し');

  // ── 7. 食事予約表の人数充足率 (書き込まずに見積もるだけ) ──────
  Logger.log('\n[7] 食事予約表 (LatestOptions) の人数');
  diagnoseOptionGuests(bookings);

  // ── 8. 清掃ボードの手動列が守られているか ────────────────────
  Logger.log('\n[8] 手動列の保護');
  eq('書き込み開始列 (E=5)', CONFIG.CLEANING.WRITE_START_COL, 5);
  CONFIG.CLEANING.WRITE_START_COL > CONFIG.COL_CLEAN.STAFF_NIGHT
    ? ok('A〜D列 (手動) は書き込み範囲の外')
    : ng('手動列が書き込み範囲に入っている');

  Logger.log(`\n======== 結果: OK ${R.ok} / NG ${R.ng} / 注意 ${R.warn} ========`);
  if (R.ng === 0) Logger.log('NG が 0 なら反映は成功しています。');
  return R;
}
