# -*- coding: utf-8 -*-
"""「こころのかたち」との たたかい。

ふつうの RPG のように HP を削りきるのではなく、
はなして・みとめて、きもちの かたちを ほどいていく戦い。
負けても物語は終わらない（うずくまって、また立ち上がる）。
"""

from __future__ import annotations

import math
import random

import pygame

from .. import config as C
from ..app import (CANCEL_KEYS, CONFIRM_KEYS, DOWN_KEYS, LEFT_KEYS,
                   RIGHT_KEYS, Scene, UP_KEYS)
from ..art import Background, draw_character, glitch as draw_glitch
from ..data.enemies import COMMANDS, ENEMIES
from ..fonts import get_font
from ..ui import (Fader, MessageWindow, Shake, draw_text_center,
                  draw_text_shadow, panel, radial_light)


def _bar(surf, rect, ratio, fill, back=(24, 26, 38), border=C.MIST):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=6)
    inner = rect.inflate(-6, -6)
    inner.width = max(0, int(inner.width * max(0.0, min(1.0, ratio))))
    if inner.width > 0:
        pygame.draw.rect(surf, fill, inner, border_radius=4)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=6)


class BattleScene(Scene):
    def __init__(self, app, enemy_id: str):
        super().__init__(app)
        self.st = app.state
        self.data = ENEMIES[enemy_id]
        self.enemy_id = enemy_id

        self.moya_max = self.data["moya"]
        self.moya = self.moya_max
        self.courage_max = 30 + self.st.get("jibun") * 5 + self.st.get("kizuna") * 3
        self.courage = self.courage_max

        self.opened = False       # 「はなす」でこころが ひらいた状態
        self.anger = 0            # ふりはらわれて かたくなった状態
        self.guard = False
        self.accepts = 0
        self.denies = 0
        self.downs = 0
        self.turn = 1

        self.bg = Background(self.st.bg if self.st.bg != "black" else "capital_broken")
        self.glitch_level = max(1.0, self.st.glitch)
        self.msg = MessageWindow()
        self.fader = Fader()
        self.shake = Shake()
        self.rng = random.Random()

        self.index = 0
        self.queue: list[str] = list(self.data["intro"])
        self.mode = "talk"        # talk（メッセージ送り）/ command（コマンド選択）
        self.after_queue = "command"
        self.result = {"outcome": "win"}
        self.enemy_alpha = 255
        self.flash = 0.0

        self.fader.set(200)
        self.fader.to(0, 0.6)
        self._next_line()

    # ------------------------------------------------------------------
    # メッセージ送り
    # ------------------------------------------------------------------
    def _say(self, lines, after="command"):
        self.queue = list(lines)
        self.after_queue = after
        self.mode = "talk"
        self._next_line()

    def _next_line(self):
        if self.queue:
            line = self.queue.pop(0)
            name, text = "", line
            if "：" in line:
                head, body = line.split("：", 1)
                if len(head) <= 8:
                    name, text = head, body
            self.msg.set_text(text, name)
            self.mode = "talk"
        else:
            self._finish_queue()

    def _finish_queue(self):
        nxt = self.after_queue
        self.msg.clear()
        if nxt == "command":
            self.mode = "command"
        elif nxt == "enemy":
            self._enemy_turn()
        elif nxt == "end":
            self.app.pop(self.result)
        elif nxt == "revive":
            self.courage = max(6, self.courage_max // 2)
            self.mode = "command"

    # ------------------------------------------------------------------
    # プレイヤーの行動
    # ------------------------------------------------------------------
    def _player_action(self, cid: str):
        lines: list[str] = []
        damage = 0

        if cid == "talk":
            damage = self.rng.randint(5, 9)
            self.opened = True
            self.anger = max(0, self.anger - 1)
            lines.append("ぼくは、そのきもちに はなしかけた。")
            lines.append(self.rng.choice(self.data["on_talk"]))

        elif cid == "accept":
            lines.append(self.rng.choice(self.data["on_accept"]))
            if self.opened:
                damage = self.rng.randint(14, 19)
                lines.append("ことばが、まっすぐ とどいた。")
                self.opened = False
            else:
                damage = self.rng.randint(5, 8)
                self.courage = max(0, self.courage - 3)
                lines.append("うまく みとめきれなくて、むねが きしんだ。")
            self.accepts += 1

        elif cid == "deny":
            damage = self.rng.randint(10, 14)
            self.anger = 2
            self.opened = False
            self.denies += 1
            lines.extend(self.data["on_deny"])

        else:  # wait
            heal = self.rng.randint(6, 9)
            self.courage = min(self.courage_max, self.courage + heal)
            self.guard = True
            lines.append("ぼくは いきを ととのえた。")
            lines.append(f"こころが すこし もどった。（こころ +{heal}）")

        if damage:
            self.moya = max(0, self.moya - damage)
            self.flash = 0.3
            lines.append(f"{self.data['name']}の ざわめきが {damage} しずまった。")

        if self.moya <= 0:
            self._win(lines)
        else:
            self._say(lines, after="enemy")

    # ------------------------------------------------------------------
    # 敵の行動
    # ------------------------------------------------------------------
    def _enemy_turn(self):
        self.turn += 1
        low = self.moya < self.moya_max * 0.35
        pool = []
        for act in self.data["actions"]:
            weight = 3
            if act["kind"] in ("guard", "heal"):
                weight = 3 if low else 1
            pool.extend([act] * weight)
        act = self.rng.choice(pool)

        lines = [act["text"]]
        if act["kind"] == "heal":
            healed = act.get("heal", 6)
            self.moya = min(self.moya_max, self.moya + healed)
            lines.append(f"{self.data['name']}の ざわめきが {healed} もどった。")
        elif act["kind"] == "guard":
            lines.append("かたちが かたく なった。")
            self.anger = max(self.anger, 1)
        else:
            lo, hi = act["damage"]
            dmg = self.rng.randint(lo, hi) + self.data["power"] // 3
            if self.anger:
                dmg = int(dmg * 1.4)
                self.anger -= 1
            if self.guard:
                dmg = max(1, dmg // 2)
                lines.append("ぼくは、いきを とめて うけとめた。")
            self.courage = max(0, self.courage - dmg)
            self.shake.kick(8, 0.3)
            lines.append(f"ぼくの こころが {dmg} けずれた。")

        self.guard = False

        if self.courage <= 0:
            self.downs += 1
            lines.extend(self.data["down"])
            if self.downs >= 2:
                lines.append("……もう、たてなかった。")
                lines.append("ぼくは めを とじて、こえが とおざかるのを まった。")
                self.result = {"outcome": "escape"}
                self.st.add("yuusha", 1)
                self._say(lines, after="end")
            else:
                lines.append("もういちど、たちあがる。")
                self._say(lines, after="revive")
        else:
            self._say(lines, after="command")

    # ------------------------------------------------------------------
    def _win(self, lines):
        lines = list(lines) + list(self.data["win"])
        reward = self.data.get("reward", {})
        for key, value in reward.items():
            self.st.add(key, value)
        if self.accepts > self.denies:
            self.st.add("jibun", 1)
            lines.append("（じぶんで うけとめた ぶんだけ、あしもとが かたくなった）")
        else:
            self.st.add("yuusha", 1)
            lines.append("（はねのけた ぶんだけ、あの すがたに よりかかった）")
        self.result = {"outcome": "win", "accepts": self.accepts, "denies": self.denies}
        self.enemy_alpha = 0
        self._say(lines, after="end")

    # ------------------------------------------------------------------
    # 入力
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "talk":
                if event.key in CONFIRM_KEYS or event.key in CANCEL_KEYS:
                    self._advance_talk()
            elif self.mode == "command":
                if event.key in UP_KEYS:
                    self.index = (self.index - 2) % len(COMMANDS)
                elif event.key in DOWN_KEYS:
                    self.index = (self.index + 2) % len(COMMANDS)
                elif event.key in LEFT_KEYS:
                    self.index = (self.index - 1) % len(COMMANDS)
                elif event.key in RIGHT_KEYS:
                    self.index = (self.index + 1) % len(COMMANDS)
                elif event.key in CONFIRM_KEYS:
                    self._player_action(COMMANDS[self.index]["id"])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode == "talk":
                self._advance_talk()
            elif self.mode == "command":
                pos = self.app.mouse_pos()
                for i in range(len(COMMANDS)):
                    if self._cmd_rect(i).collidepoint(pos):
                        self.index = i
                        self._player_action(COMMANDS[i]["id"])
                        break
        elif event.type == pygame.MOUSEMOTION and self.mode == "command":
            pos = self.app.mouse_pos()
            for i in range(len(COMMANDS)):
                if self._cmd_rect(i).collidepoint(pos):
                    self.index = i
                    break

    def _advance_talk(self):
        if not self.msg.finished:
            self.msg.skip()
        else:
            self._next_line()

    # ------------------------------------------------------------------
    # 更新・描画
    # ------------------------------------------------------------------
    def update(self, dt):
        self.msg.fast = bool(pygame.key.get_mods() & pygame.KMOD_CTRL)
        self.bg.update(dt, self.time)
        self.msg.update(dt)
        self.fader.update(dt)
        self.shake.update(dt)
        self.flash = max(0.0, self.flash - dt)
        if self.result.get("outcome") == "win" and self.enemy_alpha < 255:
            pass

    def _cmd_rect(self, i) -> pygame.Rect:
        w, h, gap = 206, 52, 10
        left = C.SCREEN_W - (w * 2 + gap) - 40
        top = C.SCREEN_H - 72 - (h * 2 + gap)
        return pygame.Rect(left + (i % 2) * (w + gap), top + (i // 2) * (h + gap), w, h)

    def draw(self, surf):
        frame = pygame.Surface((C.SCREEN_W, C.SCREEN_H))
        self.bg.draw(frame, self.time)
        dark = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        dark.fill((8, 10, 20, 120))
        frame.blit(dark, (0, 0))

        # 敵
        if self.moya > 0:
            shake = int(self.flash * 30)
            enemy_glitch = self.glitch_level if self.data["art"] in ("bug", "yuusha") else 0.0
            draw_character(frame, self.data["art"], 0.5, self.time,
                           base_y=392 + (self.rng.randint(-shake, shake) if shake else 0),
                           scale=0.94,
                           glitch_level=enemy_glitch * (0.5 if self.data["art"] == "yuusha" else 1.0))
        draw_character(frame, "boku", 0.13, self.time, base_y=460, scale=0.60)

        self._draw_enemy_gauge(frame)
        self._draw_player_gauge(frame)

        if self.mode == "command":
            self._draw_commands(frame)
        else:
            self.msg.draw(frame, self.time)

        if self.glitch_level > 0:
            draw_glitch(frame, min(3.0, self.glitch_level * 0.6), self.time)

        if self.flash > 0:
            layer = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
            layer.fill((255, 255, 255, int(70 * self.flash / 0.3)))
            frame.blit(layer, (0, 0))

        self.fader.draw(frame)
        surf.blit(frame, self.shake.offset)

    def _draw_enemy_gauge(self, frame):
        rect = pygame.Rect(0, 0, 454, 16)
        rect.center = (C.SCREEN_W // 2 + 100, 58)
        panel(frame, pygame.Rect(C.SCREEN_W // 2 - 140, 22, 480, 74), (16, 18, 30),
              alpha=185, radius=12, border=C.MIST, border_alpha=60)
        draw_text_shadow(frame, self.data["name"], get_font(21, bold=True), C.PAPER,
                         (C.SCREEN_W // 2 - 124, 32))
        count = f"ざわめき {self.moya} / {self.moya_max}"
        draw_text_shadow(frame, count, get_font(14), C.MIST,
                         (C.SCREEN_W // 2 + 330 - get_font(14).size(count)[0], 38), alpha=130)
        _bar(frame, rect, self.moya / self.moya_max, (120, 132, 196))
        if self.opened:
            draw_text_shadow(frame, "こころが すこし ひらいている", get_font(15),
                             C.GOLD, (C.SCREEN_W // 2 - 124, 70))
        elif self.anger:
            draw_text_shadow(frame, "かたちが かたく なっている", get_font(15),
                             C.DEEP_RED, (C.SCREEN_W // 2 - 124, 70))

    def _draw_player_gauge(self, frame):
        rect = pygame.Rect(48, 54, 264, 18)
        panel(frame, pygame.Rect(30, 22, 300, 74), (16, 18, 30), alpha=185, radius=12,
              border=C.MIST, border_alpha=60)
        draw_text_shadow(frame, "こころ", get_font(17, bold=True), C.GOLD, (48, 30))
        draw_text_shadow(frame, f"{self.courage} / {self.courage_max}", get_font(15),
                         C.MIST, (214, 32), alpha=120)
        ratio = self.courage / max(1, self.courage_max)
        color = C.GOLD if ratio > 0.5 else (C.WARM if ratio > 0.25 else C.DEEP_RED)
        _bar(frame, rect, ratio, color)

    def _draw_commands(self, frame):
        for i, cmd in enumerate(COMMANDS):
            r = self._cmd_rect(i)
            sel = i == self.index
            if sel:
                glow = radial_light(r.height, C.GOLD, strength=54)
                frame.blit(glow, glow.get_rect(center=r.center))
            panel(frame, r, (52, 56, 84) if sel else (26, 30, 46), alpha=230, radius=10,
                  border=C.GOLD if sel else C.MIST, border_alpha=200 if sel else 60)
            draw_text_center(frame, cmd["name"], get_font(23),
                             C.PAPER if sel else C.MIST, r.center)
        desc_rect = pygame.Rect(40, C.SCREEN_H - 58, C.SCREEN_W - 80, 40)
        panel(frame, desc_rect, (14, 16, 26), alpha=190, radius=10)
        draw_text_shadow(frame, COMMANDS[self.index]["desc"], get_font(18), C.PAPER,
                         (desc_rect.x + 18, desc_rect.y + 9))
