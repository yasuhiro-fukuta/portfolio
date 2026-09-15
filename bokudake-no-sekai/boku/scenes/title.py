# -*- coding: utf-8 -*-
"""タイトル画面。"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from .. import save as save_mod
from ..app import CONFIRM_KEYS, DOWN_KEYS, Scene, UP_KEYS
from ..art import Background, draw_character
from ..fonts import get_font
from ..state import GameState
from ..ui import (ChoiceMenu, Fader, draw_text_center, draw_text_shadow,
                  radial_light)

ENDING_NAMES = {
    "wasureru": "幸せな勇者",
    "hodou": "白い音",
    "mitasareta": "満たされた世界",
    "tsuzuku": "つづく",
}


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = Background("capital_night")
        self.fader = Fader()
        self.fader.set(255)
        self.fader.to(0, 1.2)
        self.has_save = save_mod.any_exists()
        self.options = ["はじめから"] + (["つづきから"] if self.has_save else []) + ["終わる"]
        self.menu = ChoiceMenu(self.options, center_y=396, width=360)
        self.leaving = None

    def handle_event(self, event):
        if self.leaving:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self.menu.move(-1)
            elif event.key in DOWN_KEYS:
                self.menu.move(1)
            elif event.key in CONFIRM_KEYS:
                self._select(self.menu.index)
        elif event.type == pygame.MOUSEMOTION:
            self.menu.hover(self.app.mouse_pos())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            picked = self.menu.click(self.app.mouse_pos())
            if picked is not None:
                self._select(picked)

    def _select(self, index):
        choice = self.options[index]
        if choice == "終わる":
            self.app.quit()
            return
        self.leaving = choice
        self.fader.to(255, 0.7)

    def update(self, dt):
        self.bg.update(dt, self.time)
        self.fader.update(dt)
        if self.leaving and not self.fader.busy:
            from .story import StoryScene
            if self.leaving == "つづきから":
                slot = save_mod.latest_slot()
                loaded = save_mod.load(slot) if slot is not None else None
                self.app.state = loaded or GameState()
            else:
                self.app.state = GameState()
            self.app.replace(StoryScene(self.app))

    def draw(self, surf):
        self.bg.draw(surf, self.time)

        glow = radial_light(300, C.GOLD, strength=46)
        surf.blit(glow, glow.get_rect(center=(C.SCREEN_W // 2, 200)))
        draw_character(surf, "yuusha", 0.5, self.time, base_y=336, scale=0.82,
                       glitch_level=1.0 + math.sin(self.time * 0.7) * 0.8)

        title_font = get_font(58, bold=True)
        y = 150 + math.sin(self.time * 0.8) * 3
        draw_text_center(surf, C.TITLE, title_font, C.PAPER, (C.SCREEN_W // 2, y))
        draw_text_center(surf, "― 自分の生きる理由は、自分で決める ―",
                         get_font(18), C.MIST, (C.SCREEN_W // 2, y + 48))

        self.menu.draw(surf, self.time)

        seen = self.app.state.endings_seen
        if seen:
            names = "　".join(ENDING_NAMES.get(e, e) for e in seen)
            draw_text_center(surf, f"見たエンディング：{names}", get_font(16), C.GOLD,
                             (C.SCREEN_W // 2, C.SCREEN_H - 52))
        draw_text_shadow(surf, f"ver {C.VERSION}", get_font(15), C.MIST,
                         (C.SCREEN_W - 96, C.SCREEN_H - 28), alpha=120)
        draw_text_shadow(surf, "↑↓ 選ぶ　　Z / Enter 決定", get_font(16), C.MIST,
                         (28, C.SCREEN_H - 28), alpha=140)
        self.fader.draw(surf)
