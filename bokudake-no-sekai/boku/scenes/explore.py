# -*- coding: utf-8 -*-
"""探索シーン。場所の中の「しらべるところ」をえらんで見ていく。"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from ..app import (CANCEL_KEYS, CONFIRM_KEYS, DOWN_KEYS, LEFT_KEYS,
                   RIGHT_KEYS, Scene, UP_KEYS)
from ..art import Background, draw_tear, glitch as draw_glitch
from ..data.rooms import ROOMS
from ..fonts import get_font
from ..ui import (Fader, MessageWindow, draw_text_center, draw_text_shadow,
                  panel, radial_light)


class ExploreScene(Scene):
    def __init__(self, app, room_id: str):
        super().__init__(app)
        self.st = app.state
        self.room = ROOMS[room_id]
        self.room_id = room_id
        self.points = self.room["points"]
        self.seen: set[str] = set()
        self.index = 0
        self.bg = Background(self.room["bg"])
        self.st.bg = self.room["bg"]
        self.msg = MessageWindow()
        self.fader = Fader()
        self.queue: list[str] = []
        self.mode = "select"        # select / read
        self.leaving = False
        self.notice = ""
        self.notice_time = 0.0
        self.fader.set(255)
        self.fader.to(0, 0.7)

    # ------------------------------------------------------------------
    @property
    def items(self) -> list[dict]:
        """しらべるところ ＋ 出口。"""
        return list(self.points) + [{"id": "__exit__", "name": self.room["exit"]["name"],
                                     "pos": (C.SCREEN_W // 2, C.SCREEN_H - 62)}]

    def _select(self):
        item = self.items[self.index]
        if item["id"] == "__exit__":
            need = self.room["exit"].get("require", 0)
            if len(self.seen) < need:
                self.notice = self.room["exit"].get("locked", "まだ すすめない。")
                self.notice_time = 2.4
                return
            self.leaving = True
            self.queue = list(self.room["exit"]["text"])
            self.mode = "read"
            self._next_line()
            return

        if item["id"] not in self.seen:
            self.seen.add(item["id"])
            flag = item.get("flag")
            if flag:
                self.st.add(flag[0], flag[1])
        self.queue = list(item["text"])
        self.mode = "read"
        self._next_line()

    def _next_line(self):
        if self.queue:
            self.msg.set_text(self.queue.pop(0))
        elif self.leaving:
            self.fader.to(255, 0.5)
            self.mode = "exit"
        else:
            self.msg.clear()
            self.mode = "select"

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if self.mode == "exit":
            return
        if event.type == pygame.KEYDOWN:
            if self.mode == "read":
                if event.key in CONFIRM_KEYS or event.key in CANCEL_KEYS:
                    self._advance()
                return
            if event.key in (UP_KEYS + LEFT_KEYS):
                self.index = (self.index - 1) % len(self.items)
            elif event.key in (DOWN_KEYS + RIGHT_KEYS):
                self.index = (self.index + 1) % len(self.items)
            elif event.key in CONFIRM_KEYS:
                self._select()
            elif event.key in CANCEL_KEYS:
                self.index = len(self.items) - 1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode == "read":
                self._advance()
                return
            pos = self.app.mouse_pos()
            for i, item in enumerate(self.items):
                if self._hit_rect(i, item).collidepoint(pos):
                    self.index = i
                    self._select()
                    break
        elif event.type == pygame.MOUSEMOTION and self.mode == "select":
            pos = self.app.mouse_pos()
            for i, item in enumerate(self.items):
                if self._hit_rect(i, item).collidepoint(pos):
                    self.index = i
                    break

    def _advance(self):
        if not self.msg.finished:
            self.msg.skip()
        else:
            self._next_line()

    def _hit_rect(self, i, item) -> pygame.Rect:
        font = get_font(18)
        w = font.size(item["name"])[0] + 34
        rect = pygame.Rect(0, 0, w, 34)
        rect.center = item["pos"]
        return rect

    # ------------------------------------------------------------------
    def update(self, dt):
        self.bg.update(dt, self.time)
        self.msg.update(dt)
        self.fader.update(dt)
        self.notice_time = max(0.0, self.notice_time - dt)
        if self.mode == "exit" and not self.fader.busy:
            self.app.pop({"seen": sorted(self.seen), "room": self.room_id})

    def draw(self, surf):
        self.bg.draw(surf, self.time)
        for i, item in enumerate(self.points):
            if item.get("tear"):
                draw_tear(surf, (item["pos"][0], item["pos"][1] - 52), 30, self.time, seed=i)
        if self.st.glitch > 0:
            draw_glitch(surf, self.st.glitch, self.time)

        if self.mode != "read":
            for i, item in enumerate(self.items):
                rect = self._hit_rect(i, item)
                sel = i == self.index
                done = item["id"] in self.seen
                if sel:
                    glow = radial_light(52, C.GOLD, strength=70)
                    surf.blit(glow, glow.get_rect(center=rect.center))
                panel(surf, rect, (46, 50, 74) if sel else (20, 22, 34),
                      alpha=225 if sel else 180, radius=8,
                      border=C.GOLD if sel else C.MIST, border_alpha=200 if sel else 60)
                color = C.PAPER if sel else (C.MIST if not done else (140, 150, 160))
                label = ("✓ " if done else "") + item["name"]
                draw_text_center(surf, label, get_font(18), color, rect.center)
                if sel:
                    bob = math.sin(self.time * 5) * 3
                    pygame.draw.polygon(surf, C.GOLD, [
                        (rect.centerx - 7, rect.top - 12 - bob),
                        (rect.centerx + 7, rect.top - 12 - bob),
                        (rect.centerx, rect.top - 4 - bob)])

            head = pygame.Rect(0, 0, 460, 44)
            head.center = (C.SCREEN_W // 2, 40)
            panel(surf, head, (14, 16, 26), alpha=190, radius=10,
                  border=C.MIST, border_alpha=60)
            draw_text_center(surf, self.room["title"], get_font(22, bold=True),
                             C.PAPER, head.center)
            draw_text_shadow(surf, self.room["hint"], get_font(17), C.MIST,
                             (30, C.SCREEN_H - 30), alpha=120)
            draw_text_shadow(surf, f"しらべた：{len(self.seen)} / {len(self.points)}",
                             get_font(17), C.GOLD, (C.SCREEN_W - 150, 78))
        else:
            self.msg.draw(surf, self.time)

        if self.notice_time > 0:
            rect = pygame.Rect(0, 0, get_font(19).size(self.notice)[0] + 44, 42)
            rect.center = (C.SCREEN_W // 2, C.SCREEN_H - 120)
            alpha = int(230 * min(1.0, self.notice_time / 0.6))
            panel(surf, rect, (20, 24, 38), alpha=int(alpha * 0.9), radius=10,
                  border=C.MIST, border_alpha=int(alpha * 0.4))
            draw_text_center(surf, self.notice, get_font(19), C.PAPER, rect.center, alpha=alpha)

        self.fader.draw(surf)
