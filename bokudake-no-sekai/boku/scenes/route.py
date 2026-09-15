# -*- coding: utf-8 -*-
"""外出シーン。

第二章：近所の人やクラスメートに見つからないように、学校とスーパーへ行く。
        見られているあいだ「正気」が削られる。ゼロになるとエンディング２。
第三章：追いかけてくる男子グループから逃げる（chase モード）。
"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from ..app import CONFIRM_KEYS, LEFT_KEYS, RIGHT_KEYS, Scene
from ..art import Background, draw_character, glitch as draw_glitch
from ..fonts import get_font
from ..ui import (Fader, draw_text_center, draw_text_shadow, panel,
                  radial_light)

GROUND_Y = 452
GOAL_X = 876
START_X = 54

STAGES = {
    # ---- 第二章：おつかい ----
    # かげは、それぞれの 視線の 手前に 置いてある。
    # 「見られる前に かげへ、目を そらした すきに 進む」が 基本。
    "school": {
        "bg": "street_night",
        "label": "学校へ　― プリントを だす ―",
        "goal": "がっこう",
        "goal_kind": "school",
        "watchers": [
            {"x": 330, "kind": "father", "period": 3.8, "phase": 0.0, "radius": 118},
            {"x": 660, "kind": "classmate", "period": 4.4, "phase": 1.9, "radius": 124},
        ],
        "shadows": [(140, 206), (466, 532), (752, 826)],
        "speed": 142.0,
        "drain": 9.0,
    },
    "super": {
        "bg": "street_night",
        "label": "スーパーへ　― 牛乳を かう ―",
        "goal": "スーパー",
        "goal_kind": "shop",
        "watchers": [
            {"x": 250, "kind": "classmate", "period": 3.4, "phase": 0.4, "radius": 112},
            {"x": 500, "kind": "girl", "period": 3.0, "phase": 1.3, "radius": 122},
            {"x": 740, "kind": "classmate", "period": 3.6, "phase": 2.3, "radius": 118},
        ],
        "shadows": [(72, 132), (296, 374), (540, 614), (784, 846)],
        "speed": 146.0,
        "drain": 10.0,
    },
    "home": {
        "bg": "street_night",
        "label": "いえへ　― もう、かえりたい ―",
        "goal": "いえ",
        "goal_kind": "home",
        "watchers": [
            {"x": 300, "kind": "girl", "period": 3.6, "phase": 0.6, "radius": 114},
            {"x": 640, "kind": "classmate", "period": 3.2, "phase": 2.0, "radius": 126},
        ],
        "shadows": [(118, 182), (396, 508), (716, 792)],
        "speed": 146.0,
        "drain": 10.0,
    },
    # ---- 第三章：逃走 ----
    "chase": {
        "bg": "corridor_dark",
        "label": "にげろ",
        "goal": "むこう",
        "goal_kind": "corridor",
        "chase": True,
        "pursuers": [
            {"kind": "classmate", "x": -60, "speed": 120.0},
            {"kind": "classmate", "x": -150, "speed": 114.0},
            {"kind": "classmate", "x": -240, "speed": 126.0},
        ],
        "watchers": [],
        "shadows": [],
        "speed": 158.0,
        "drain": 26.0,
        "glitch": 2.4,
    },
}


class RouteScene(Scene):
    def __init__(self, app, stage: str = "school"):
        super().__init__(app)
        self.st = app.state
        self.stage_id = stage if stage in STAGES else "school"
        self.stage = STAGES[self.stage_id]
        self.chase = bool(self.stage.get("chase"))

        bg_name = self.stage.get("bg", "street_night")
        self.bg = Background(bg_name)
        self.st.bg = bg_name
        self.fader = Fader()
        self.fader.set(255)
        self.fader.to(0, 0.7)

        self.x = float(START_X)
        self.pursuers = [dict(p) for p in self.stage.get("pursuers", [])]
        self.phase = "ready"        # ready / play / done / broken
        self.seen_now = False
        self.hit_flash = 0.0
        self.intro_time = 2.8
        if self.st.get("shouki") <= 0:
            self.st.set("shouki", 100)

    # ------------------------------------------------------------------
    @property
    def shouki(self) -> int:
        return self.st.get("shouki")

    def _watching(self, w) -> bool:
        cycle = (self.time + w["phase"]) % w["period"]
        return cycle < w["period"] * 0.46

    def _in_shadow(self) -> bool:
        return any(a <= self.x <= b for a, b in self.stage["shadows"])

    # ------------------------------------------------------------------
    def handle_event(self, event):
        pressed = (event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS) or \
                  (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if not pressed:
            return
        if self.phase == "ready":
            self.phase = "play"
        elif self.phase in ("done", "broken"):
            self._finish()

    def _finish(self):
        ok = self.phase == "done"
        self.st.set("route_ok", 1 if ok else 0)
        self.st.set("shouki_broken", 0 if ok else 1)
        self.app.pop({"ok": ok, "stage": self.stage_id})

    def _damage(self, amount: float):
        before = self.st.get("shouki")
        self.st.set("shouki", max(0, min(100, int(round(before - amount)))))
        if self.st.get("shouki") <= 0:
            self.phase = "broken"

    # ------------------------------------------------------------------
    def update(self, dt):
        self.bg.update(dt, self.time)
        self.fader.update(dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
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
        if self.chase:
            for p in self.pursuers:
                p["x"] += p["speed"] * dt
                if abs(p["x"] - self.x) < 46:
                    self.seen_now = True
                    self.hit_flash = 0.25
        elif not self._in_shadow():
            for w in self.stage["watchers"]:
                if self._watching(w) and abs(self.x - w["x"]) < w["radius"]:
                    self.seen_now = True
                    break

        if self.seen_now:
            self._damage(self.stage["drain"] * dt)
        elif self._in_shadow():
            self._damage(-7.0 * dt)          # かげでは すこし ととのう

        if self.phase == "play" and self.x >= GOAL_X - 2:
            self.phase = "done"

    # ------------------------------------------------------------------
    def draw(self, surf):
        self.bg.draw(surf, self.time)
        self._draw_goal(surf)

        for a, b in self.stage["shadows"]:
            cx = (a + b) // 2
            pygame.draw.rect(surf, (74, 72, 78), pygame.Rect(cx - 7, GROUND_Y - 186, 14, 186))
            pygame.draw.rect(surf, (92, 90, 96), pygame.Rect(cx - 12, GROUND_Y - 190, 24, 10))
            layer = pygame.Surface((b - a, 96), pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (22, 24, 44, 120), layer.get_rect())
            surf.blit(layer, (a, GROUND_Y - 62))

        for w in self.stage["watchers"]:
            watching = self._watching(w)
            if watching:
                cone = pygame.Surface((w["radius"] * 2, 210), pygame.SRCALPHA)
                pygame.draw.polygon(cone, (250, 176, 128, 58), [
                    (w["radius"], 40), (10, 210), (w["radius"] * 2 - 10, 210)])
                surf.blit(cone, (w["x"] - w["radius"], GROUND_Y - 210))
            draw_character(surf, w["kind"], w["x"] / C.SCREEN_W, self.time,
                           base_y=GROUND_Y, scale=0.62, alpha=255 if watching else 200)
            draw_text_center(surf, "！" if watching else "…", get_font(24, bold=True),
                             C.DEEP_RED if watching else C.MIST,
                             (w["x"], GROUND_Y - 236))

        for p in self.pursuers:
            draw_character(surf, p["kind"], p["x"] / C.SCREEN_W, self.time,
                           base_y=GROUND_Y, scale=0.64)
            draw_text_center(surf, "！", get_font(24, bold=True), C.DEEP_RED,
                             (p["x"], GROUND_Y - 236))

        hidden = self._in_shadow()
        draw_character(surf, "boku", self.x / C.SCREEN_W, self.time,
                       base_y=GROUND_Y, scale=0.66, alpha=150 if hidden else 255)
        if hidden:
            draw_text_center(surf, "かくれている", get_font(16), (170, 200, 230),
                             (self.x, GROUND_Y - 238))
        elif self.seen_now:
            draw_text_center(surf, "見られている", get_font(17, bold=True), C.DEEP_RED,
                             (self.x, GROUND_Y - 238))

        if self.stage.get("glitch"):
            draw_glitch(surf, self.stage["glitch"], self.time)
        if self.hit_flash > 0 or (self.seen_now and not self.chase):
            layer = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
            layer.fill((180, 40, 60, int(26 + 40 * self.hit_flash)))
            surf.blit(layer, (0, 0))

        self._draw_hud(surf)
        self.fader.draw(surf)

    def _draw_goal(self, surf):
        kind = self.stage.get("goal_kind", "school")
        goal = pygame.Rect(GOAL_X - 30, GROUND_Y - 236, 118, 236)
        if kind == "corridor":
            pygame.draw.rect(surf, (48, 46, 58), goal)
            pygame.draw.rect(surf, (80, 150, 110), pygame.Rect(goal.x + 24, goal.y + 40, 70, 150))
            g = radial_light(140, (90, 210, 140), strength=70)
            surf.blit(g, g.get_rect(center=goal.center))
        elif kind == "shop":
            pygame.draw.rect(surf, (222, 218, 210), goal)
            pygame.draw.rect(surf, (196, 92, 88), pygame.Rect(goal.x, goal.y, goal.w, 40))
            for i in range(4):
                pygame.draw.rect(surf, (238, 236, 230),
                                 pygame.Rect(goal.x + 10 + i * 28, goal.y + 60, 20, 120))
        elif kind == "home":
            pygame.draw.rect(surf, (168, 152, 140), goal.inflate(0, -60).move(0, 30))
            pygame.draw.polygon(surf, (120, 86, 76), [
                (goal.x - 14, goal.y + 40), (goal.right + 14, goal.y + 40),
                (goal.centerx, goal.y - 10)])
            pygame.draw.rect(surf, (96, 74, 62), pygame.Rect(goal.centerx - 20, GROUND_Y - 110,
                                                             40, 110), border_radius=3)
        else:
            pygame.draw.rect(surf, (204, 200, 190), goal)
            pygame.draw.rect(surf, (168, 162, 152), goal, width=3)
            for y in range(goal.y + 24, goal.bottom - 50, 48):
                pygame.draw.rect(surf, (214, 230, 236), pygame.Rect(goal.x + 12, y, 40, 30))
                pygame.draw.rect(surf, (214, 230, 236), pygame.Rect(goal.x + 64, y, 40, 30))
        draw_text_center(surf, self.stage["goal"], get_font(17, bold=True),
                         C.PAPER if kind == "corridor" else C.INK,
                         (goal.centerx - 10, goal.y - 18))

    def _draw_hud(self, surf):
        bar = pygame.Rect(48, 50, 300, 18)
        panel(surf, pygame.Rect(30, 22, 336, 70), (14, 16, 26), alpha=180, radius=10)
        draw_text_shadow(surf, "正気", get_font(17, bold=True), C.MIST, (48, 28))
        draw_text_shadow(surf, f"{self.shouki} / 100", get_font(15), C.MIST,
                         (268, 30), alpha=130)
        pygame.draw.rect(surf, (24, 26, 38), bar, border_radius=6)
        inner = bar.inflate(-6, -6)
        inner.width = int(inner.width * self.shouki / 100)
        if inner.width:
            ratio = self.shouki / 100
            color = C.MIST if ratio > 0.5 else (C.WARM if ratio > 0.25 else C.DEEP_RED)
            if ratio <= 0.25:
                pulse = 0.6 + 0.4 * math.sin(self.time * 8)
                color = tuple(int(c * pulse) for c in C.DEEP_RED)
            pygame.draw.rect(surf, color, inner, border_radius=4)
        pygame.draw.rect(surf, C.MIST, bar, width=2, border_radius=6)

        draw_text_shadow(surf, self.stage["label"], get_font(17), C.PAPER,
                         (C.SCREEN_W - 340, 36), alpha=150)
        hint = ("← → いそげ。つかまると 正気が けずれる"
                if self.chase else "← → すすむ・もどる　　かげの なかは 見つからない")
        draw_text_shadow(surf, hint, get_font(17), C.PAPER, (40, C.SCREEN_H - 30), alpha=150)

        if self.phase == "ready":
            box = pygame.Rect(0, 0, 660, 108)
            box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2 - 40)
            panel(surf, box, (12, 14, 24), alpha=215, radius=14, border=C.GOLD, border_alpha=120)
            title = "にげろ" if self.chase else f"{self.stage['goal']}まで、見つからないように"
            draw_text_center(surf, title, get_font(24, bold=True), C.PAPER,
                             (box.centerx, box.centery - 18))
            sub = ("つかまっているあいだ、正気が けずれていく"
                   if self.chase else "← → で いどう　　かげに はいると やりすごせる")
            draw_text_center(surf, sub, get_font(18), C.MIST, (box.centerx, box.centery + 22))
        elif self.phase in ("done", "broken"):
            box = pygame.Rect(0, 0, 640, 120)
            box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2 - 40)
            panel(surf, box, (12, 14, 24), alpha=225, radius=14,
                  border=C.GOLD if self.phase == "done" else C.DEEP_RED, border_alpha=150)
            if self.phase == "done":
                draw_text_center(surf, f"{self.stage['goal']}に ついた", get_font(26, bold=True),
                                 C.GOLD, (box.centerx, box.centery - 16))
                draw_text_center(surf, f"正気：{self.shouki}", get_font(19), C.PAPER,
                                 (box.centerx, box.centery + 22))
            else:
                draw_text_center(surf, "もう、むりだ", get_font(26, bold=True),
                                 C.DEEP_RED, (box.centerx, box.centery - 16))
                draw_text_center(surf, "あたまの なかが、しろい おとで いっぱいになる。",
                                 get_font(19), C.PAPER, (box.centerx, box.centery + 22))
            draw_text_center(surf, "Z / クリックで つづける", get_font(17), C.MIST,
                             (box.centerx, box.bottom + 26))
