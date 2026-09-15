#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ぼくだけのせかい — 起動スクリプト。

    python3 main.py             ふつうに あそぶ
    python3 main.py --headless  画面を出さずに起動（動作確認用）
"""

import sys

from boku.app import main

if __name__ == "__main__":
    sys.exit(main())
