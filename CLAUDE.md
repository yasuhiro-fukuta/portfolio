# Yakkun Games

福田康宏（Yakkun）のブラウザゲーム集。静的HTMLのみ（ビルドなし）。Vercelで公開（`main` = 本番）。

## 構成
- `index.html` — トップ（ゲーム一覧）。カードは手書きHTML。
- `<slug>/index.html` — 各ゲーム（単体HTML、Claudeアーティファクトから書き出したもの）。
- `thumbs/<slug>.jpg` — 一覧用サムネ（640×480、Playwrightでスクショ）。

## ゲーム追加手順
1. アーティファクトを `Artifact read`（`path: "index.html"`）で取得 → `<slug>/index.html` に置く。
2. Playwrightで800×600スクショ → `thumbs/<slug>.jpg`（640×480, q78）。
3. `index.html` に `<article class="game">` を1枚追加（最新を先頭・NEWバッジ移動）、件数を更新。

## 収録
| slug | タイトル | 元アーティファクト |
|---|---|---|
| support-maze | 人間にたどり着け | https://claude.ai/artifact/16vDh5uLKnrZp9hKhMgHQH |
| popup-hunt | ポップアップ狩り | https://claude.ai/artifact/CPvzvnAiSwwSW3MJPSTVKy |
| winning-run | WINNING RUN（日本語） | https://claude.ai/artifact/NjpSSLNvtJ8hAiDz5NGF4o |
| winning-run/en | WINNING RUN（English） | https://claude.ai/artifact/Jhv3fBgXDNyPEL5nqcvkn2 |
| daifugo | 大富豪 | https://claude.ai/artifact/KMAc4rBWub9g9VcZc2juvD |
| kiso-downhill | 木曽路ダウンヒル | https://claude.ai/artifact/5RxzqvZyxXme51XH3dgnwK |
| duel-trump | デュエルトランプ（Firebase。Googleログインは公開ドメインをFirebase Authの承認済みドメインに追加要） | https://claude.ai/artifact/59TRymhDjaDJz3DXwxro8i |
