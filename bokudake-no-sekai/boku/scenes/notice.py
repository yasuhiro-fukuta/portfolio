# -*- coding: utf-8 -*-
"""最初の一回だけ出る注意書き。

このゲームは、第五章でゲームフォルダの中にファイルを作ることがある。
黙ってやるのは行儀が悪いので、始める前に一度だけ知らせる。
"""

from __future__ import annotations

import pygame

from .. import config as C
from .. import meta
from ..app import CONFIRM_KEYS, Scene
from ..fonts import get_font
from ..ui import Fader, draw_text_center, draw_text_shadow, panel

LINES = [
    "このゲームは、物語の途中で",
    "あなたの環境の情報を画面に表示し、",
    "ゲームのフォルダの中にファイルを作ることがあります。",
    "",
    "・触れるのは、このゲームのフォルダの中だけです",
    "・既に あるファイルは書き換えません",
    "・読み取った情報は、どこにも送信しません",
    "",
    "作られたファイルは、次のコマンドで元に戻せます。",
]


class NoticeScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.fader = Fader()
        self.fader.set(255)
        self.fader.to(0, 1.0)
        self.leaving = False

    def handle_event(self, event):
        if self.leaving:
            return
        if (event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS) or \
           (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            self.leaving = True
            meta.mark_notice_seen()
            self.fader.to(255, 0.5)

    def update(self, dt):
        self.fader.update(dt)
        if self.leaving and not self.fader.busy:
            from .title import TitleScene
            self.app.replace(TitleScene(self.app))

    def draw(self, surf):
        surf.fill((10, 12, 18))
        box = pygame.Rect(0, 0, 720, 380)
        box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2 - 10)
        panel(surf, box, (18, 20, 30), alpha=235, radius=16,
              border=C.MIST, border_alpha=90)

        draw_text_center(surf, "はじめる前に", get_font(26, bold=True), C.GOLD,
                         (box.centerx, box.y + 44))
        y = box.y + 92
        font = get_font(20)
        for line in LINES:
            if line:
                draw_text_center(surf, line, font, C.PAPER, (box.centerx, y))
            y += font.get_height() + 8

        cmd = pygame.Rect(0, 0, 420, 42)
        cmd.center = (box.centerx, y + 12)
        panel(surf, cmd, (6, 10, 8), alpha=240, radius=8, border=C.GREEN, border_alpha=140)
        draw_text_center(surf, "python main.py --cleanup", get_font(19), C.GREEN, cmd.center)

        draw_text_shadow(surf, "Z / クリックではじめる", get_font(18), C.MIST,
                         (box.centerx - 90, box.bottom + 24), alpha=180)
        self.fader.draw(surf)
