# -*- coding: utf-8 -*-
"""日本語フォントの検出とキャッシュ。

環境によって使えるフォントが違うので、
  1. 環境変数 BOKU_FONT
  2. よくある日本語フォントのパス
  3. fc-match による問い合わせ
  4. pygame の SysFont
の順に探す。どれも見つからなければ既定フォント（豆腐になるかもしれない）。
"""

from __future__ import annotations

import functools
import os
import subprocess

import pygame

_CANDIDATE_PATHS = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
]

_SYSFONT_NAMES = [
    "ipagothic", "notosanscjkjp", "notosansjp", "takaogothic",
    "vlgothic", "meiryo", "yugothic", "msgothic",
    "hiraginosans", "applegothic", "unifont",
]


@functools.lru_cache(maxsize=1)
def font_path() -> str | None:
    """使える日本語フォントファイルのパスを返す（無ければ None）。"""
    env = os.environ.get("BOKU_FONT")
    if env and os.path.exists(env):
        return env
    for path in _CANDIDATE_PATHS:
        if os.path.exists(path):
            return path
    try:
        out = subprocess.run(
            ["fc-match", "-f", "%{file}", ":lang=ja"],
            capture_output=True, text=True, timeout=4,
        ).stdout.strip()
        if out and os.path.exists(out):
            return out
    except Exception:
        pass
    for name in _SYSFONT_NAMES:
        found = pygame.font.match_font(name)
        if found:
            return found
    return None


@functools.lru_cache(maxsize=64)
def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """指定サイズのフォントを返す（結果はキャッシュされる）。"""
    path = font_path()
    if path:
        font = pygame.font.Font(path, size)
    else:
        font = pygame.font.SysFont(",".join(_SYSFONT_NAMES), size)
    font.set_bold(bold)
    return font
