# -*- coding: utf-8 -*-
"""通学路シーン。

近所の人やクラスメートに見つからないように、保健室まで歩く。
見られている間は「ひそひそ」がたまり、たまりきると引き返してしまう。
"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from ..app import CONFIRM_KEYS, LEFT_KEYS, RIGHT_KEYS, Scene
from ..art import Background, draw_character
from ..fonts import get_font
from ..ui import (Fader, draw_text_center, draw_text_shadow, panel,
                  radial_light)

GROUND_Y = 452
GOAL_X = 876
START_X = 54

STAGES = {
    # 一日目：ひとが すくない
    "1": {
        "label": "一日目　― あさ、七時二十分 ―",
        "watchers": [
            {"x": 330, "kind": "father", "period": 3.6, "phase": 0.0, "radius": 130},
            {"x": 660, "kind": "classmate", "period": 4.2, "phase": 1.8, "radius": 140},
        ],
        "shadows": [(240, 320), (520, 600), (770, 840)],
        "speed": 138.0,
        "fill": 34.0,
    },
    # 二日目：みんな、もう そとに でている
    "2": {
        "label": "二日目　― あさ、七時五十分 ―",
        "watchers": [
            {"x": 250, "kind": "classmate", "period": 3.0, "phase": 0.4, "radius": 130},
            {"x": 500, "kind": "father", "period": 2.6, "phase": 1.1, "radius": 150},
            {"x": 730, "kind": "classmate", "period": 3.4, "phase": 2.2, "radius": 140},
        ],
        "shadows": [(180, 240), (420, 470), (620, 680), (820, 870)],
        "speed": 148.0,
        "fill": 40.0,
    },
    # 三日目：もう、かくれなくてもいい かもしれない
    "3": {
        "label": "三日目　― あさ、八時ちょうど ―",
        "watchers": [
            {"x": 300, "kind": "classmate", "period": 2.4, "phase": 0.2, "radius": 150},
            {"x": 540, "kind": "minami", "period": 3.2, "phase": 1.4, "radius": 120},
            {"x": 760, "kind": "classmate", "period": 2.8, "phase": 2.6, "radius": 150},
        ],
        "shadows": [(200, 250), (440, 490), (660, 700)],
        "speed": 150.0,
        "fill": 44.0,
    },
}


class RouteScene(Scene):
    def __init__(self, app, stage: str = "1"):
        super().__init__(app)
        self.st = app.state
        self.stage_id = stage if stage in STAGES else "1"
        self.stage = STAGES[self.stage_id]
        self.bg = Background("street_morning")
        self.st.bg = "street_morning"
        self.fader = Fader()
        self.fader.set(255)
        self.fader.to(0, 0.7)

        self.x = float(START_X)
        self.gauge = 0.0            # ひそひそ（100 で ひきかえす）
        self.phase = "ready"        # ready / play / done / failed
        self.result_timer = 0.0
        self.seen_now = False
        self.intro_time = 2.6

    # ------------------------------------------------------------------
    def _watching(self, w) -> bool:
        """その人が いま こちらを 見ているか。"""
        cycle = (self.time + w["phase"]) % w["period"]
        return cycle < w["period"] * 0.55

    def _in_shadow(self) -> bool:
        return any(a <= self.x <= b for a, b in self.stage["shadows"])

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS:
            if self.phase == "ready":
                self.phase = "play"
            elif self.phase in ("done", "failed"):
                self._finish()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == "ready":
                self.phase = "play"
            elif self.phase in ("done", "failed"):
                self._finish()

    def _finish(self):
        ok = self.phase == "done"
        self.st.set("route_ok", 1 if ok else 0)
        if ok:
            self.st.add("jibun", 1)
        self.app.pop({"ok": ok, "stage": self.stage_id})

    # ------------------------------------------------------------------
    def update(self, dt):
        self.bg.update(dt, self.time)
        self.fader.update(dt)
        if self.phase == "ready":
            self.intro_time -= dt
            if self.intro_time <= 0:
                self.phase = "play"
            return
        if self.phase != "play":
            return

        keys = pygame.key.get_pressed()
        move = 0.0
        if any(keys[k] for k in RIGHT_KEYS):
            move += 1.0
        if any(keys[k] for k in LEFT_KEYS):
            move -= 1.0
        if pygame.mouse.get_pressed()[0]:
            mx = self.app.mouse_pos()[0]
            move += 1.0 if mx > self.x + 20 else (-1.0 if mx < self.x - 20 else 0.0)
        slow = 0.55 if self._in_shadow() else 1.0
        self.x = max(START_X, min(GOAL_X, self.x + move * self.stage["speed"] * slow * dt))

        self.seen_now = False
        if not self._in_shadow():
            for w in self.stage["watchers"]:
                if self._watching(w) and abs(self.x - w["x"]) < w["radius"]:
                    self.seen_now = True
                    break

        self.gauge += (self.stage["fill"] if self.seen_now else -22.0) * dt
        self.gauge = max(0.0, min(100.0, self.gauge))

        if self.gauge >= 100.0:
            self.phase = "failed"
        elif self.x >= GOAL_X - 2:
            self.phase = "done"

    # ------------------------------------------------------------------
    def draw(self, surf):
        self.bg.draw(surf, self.time)

        # ゴール（保健室のある校舎）
        goal = pygame.Rect(GOAL_X - 30, GROUND_Y - 236, 118, 236)
        pygame.draw.rect(surf, (204, 200, 190), goal)
        pygame.draw.rect(surf, (168, 162, 152), goal, width=3)
        for y in range(goal.y + 24, goal.bottom - 50, 48):
            pygame.draw.rect(surf, (214, 230, 236), pygame.Rect(goal.x + 12, y, 40, 30))
            pygame.draw.rect(surf, (214, 230, 236), pygame.Rect(goal.x + 64, y, 40, 30))
        draw_text_center(surf, "ほけんしつ", get_font(17, bold=True), C.INK,
                         (goal.centerx - 10, goal.y - 18))

        # かくれられる かげ（電柱と、その足もと）
        for a, b in self.stage["shadows"]:
            cx = (a + b) // 2
            pygame.draw.rect(surf, (74, 72, 78), pygame.Rect(cx - 7, GROUND_Y - 186, 14, 186))
            pygame.draw.rect(surf, (92, 90, 96), pygame.Rect(cx - 12, GROUND_Y - 190, 24, 10))
            layer = pygame.Surface((b - a, 96), pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (22, 24, 44, 120), layer.get_rect())
            surf.blit(layer, (a, GROUND_Y - 62))

        # ひとびと と しせん
        for w in self.stage["watchers"]:
            watching = self._watching(w)
            if watching:
                cone = pygame.Surface((w["radius"] * 2, 210), pygame.SRCALPHA)
                pygame.draw.polygon(cone, (250, 176, 128, 58), [
                    (w["radius"], 40), (10, 210), (w["radius"] * 2 - 10, 210)])
                surf.blit(cone, (w["x"] - w["radius"], GROUND_Y - 210))
            draw_character(surf, w["kind"], w["x"] / C.SCREEN_W, self.time,
                           base_y=GROUND_Y, scale=0.62, alpha=255 if watching else 200)
            mark = "！" if watching else "…"
            draw_text_center(surf, mark, get_font(24, bold=True),
                             C.DEEP_RED if watching else C.MIST,
                             (w["x"], GROUND_Y - 236))

        # ぼく
        hidden = self._in_shadow()
        draw_character(surf, "boku", self.x / C.SCREEN_W, self.time,
                       base_y=GROUND_Y, scale=0.66, alpha=150 if hidden else 255)
        if hidden:
            draw_text_center(surf, "かくれている", get_font(16), (170, 200, 230),
                             (self.x, GROUND_Y - 238))
        elif self.seen_now:
            draw_text_center(surf, "見られている", get_font(17, bold=True), C.DEEP_RED,
                             (self.x, GROUND_Y - 238))

        self._draw_hud(surf)
        self.fader.draw(surf)

    def _draw_hud(self, surf):
        bar = pygame.Rect(40, 34, 320, 18)
        panel(surf, bar.inflate(26, 46).move(0, -4), (14, 16, 26), alpha=170, radius=10)
        draw_text_shadow(surf, "ひそひそ", get_font(16, bold=True), C.MIST, (bar.x, bar.y - 22))
        pygame.draw.rect(surf, (24, 26, 38), bar, border_radius=6)
        inner = bar.inflate(-6, -6)
        inner.width = int(inner.width * self.gauge / 100)
        if inner.width:
            color = C.DEEP_RED if self.gauge > 65 else (C.WARM if self.gauge > 30 else C.MIST)
            pygame.draw.rect(surf, color, inner, border_radius=4)
        pygame.draw.rect(surf, C.MIST, bar, width=2, border_radius=6)

        draw_text_shadow(surf, self.stage["label"], get_font(17), C.PAPER,
                         (C.SCREEN_W - 300, 36), alpha=150)
        draw_text_shadow(surf, "← → すすむ・もどる　　かげの なかは 見つからない",
                         get_font(17), C.PAPER, (40, C.SCREEN_H - 30), alpha=150)

        if self.phase == "ready":
            box = pygame.Rect(0, 0, 640, 108)
            box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2 - 40)
            panel(surf, box, (12, 14, 24), alpha=210, radius=14, border=C.GOLD, border_alpha=120)
            draw_text_center(surf, "見つからないように、ほけんしつまで", get_font(24, bold=True),
                             C.PAPER, (box.centerx, box.centery - 18))
            draw_text_center(surf, "← → で いどう　　かげに はいると やりすごせる",
                             get_font(18), C.MIST, (box.centerx, box.centery + 22))
        elif self.phase in ("done", "failed"):
            box = pygame.Rect(0, 0, 620, 120)
            box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2 - 40)
            panel(surf, box, (12, 14, 24), alpha=220, radius=14,
                  border=C.GOLD if self.phase == "done" else C.DEEP_RED, border_alpha=150)
            if self.phase == "done":
                draw_text_center(surf, "ほけんしつに ついた", get_font(26, bold=True),
                                 C.GOLD, (box.centerx, box.centery - 16))
                draw_text_center(surf, "だれにも 見つからなかった。", get_font(19), C.PAPER,
                                 (box.centerx, box.centery + 22))
            else:
                draw_text_center(surf, "見つかった", get_font(26, bold=True),
                                 C.DEEP_RED, (box.centerx, box.centery - 16))
                draw_text_center(surf, "ひそひそ声が、せなかに ささった。", get_font(19), C.PAPER,
                                 (box.centerx, box.centery + 22))
            draw_text_center(surf, "Z / クリックで つづける", get_font(17), C.MIST,
                             (box.centerx, box.bottom + 26))
