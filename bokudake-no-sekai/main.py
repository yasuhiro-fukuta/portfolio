#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ぼくだけのせかい — 起動スクリプト。

    python3 main.py             ふつうに遊ぶ
    python3 main.py --cleanup   このゲームが作ったファイルをすべて消す
    python3 main.py --headless  画面を出さずに起動（動作確認用）
"""

import sys


def cleanup() -> int:
    from boku import meta
    removed = meta.cleanup()
    if removed:
        print("消しました:")
        for rel in removed:
            print("  -", rel)
    else:
        print("このゲームが作ったファイルは残っていません。")
    return 0


def main() -> int:
    if "--cleanup" in sys.argv[1:]:
        return cleanup()
    from boku.app import main as run
    return run()


if __name__ == "__main__":
    sys.exit(main())
