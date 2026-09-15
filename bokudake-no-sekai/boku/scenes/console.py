# -*- coding: utf-8 -*-
"""端末シーン。

第五章。主人公は病棟のパソコンを持ち出し、自分の世界の「外」を覗く。
ここに出る IP アドレスもフォルダの中身も、作り物ではなく実際の環境の値。
"""

from __future__ import annotations

import math
import random

import pygame

from .. import config as C
from .. import meta
from ..app import CANCEL_KEYS, CONFIRM_KEYS, Scene
from ..art import GlitchDriver
from ..fonts import get_font, get_mono
from ..ui import Fader, draw_text_center, panel, wrap_text

GREEN = (150, 240, 170)
DIM = (86, 150, 106)
WHITE = (228, 236, 232)
RED = (236, 110, 110)

TYPE_SPEED = 26.0          # 1秒あたりに打つ文字数
LINE_DELAY = 0.09          # 出力を1行ずつ出す間隔


def ward_pc_script() -> list[tuple]:
    """病棟のパソコンでの一連。実際の環境を読んで組み立てる。"""
    user = meta.user_name()
    host = meta.host_name()
    ip = meta.local_ip()
    root = meta.game_dir()
    prompt = f"{user}@{host}:~$ "

    steps: list[tuple] = [
        ("prompt", prompt),
        ("out", ["接続可能なネットワーク:",
                 "  [1] hospital-guest        （認証が必要）",
                 "  [2] hospital-staff        （認証が必要）",
                 "  [3] ■■■■■■■■■■■■     （認証不要）"]),
        ("say", "……三つめ。こんなの、この病棟にあったか？"),
        ("type", "connect 3"),
        ("out", ["接続しました。", ""]),
        ("wait", 0.4),
        ("type", "whoami"),
        ("out", [user, ""]),
        ("type", "ipconfig"),
        ("out", ["",
                 f"  ホスト名 . . . . . . . . . . . : {host}",
                 f"  IPv4 アドレス . . . . . . . . . : {ip}",
                 f"  システム . . . . . . . . . . . : {meta.os_name()}",
                 ""]),
        ("say", "……これ、病院のパソコンのじゃない。"),
        ("say", "これは──"),
        ("say", "……うそだ。"),
        ("wait", 0.5),
        ("type", "cd ..  &&  pwd"),
        ("out", [root, ""]),
        ("type", "dir"),
        ("out", [f" {root} のディレクトリ", ""] + meta.dir_lines(12) + [""]),
        ("say", "なんだよ……これ。"),
        ("say", "俺の世界が、フォルダに入ってる。"),
        ("wait", 0.4),
        ("type", "edit boku"),
        ("err", ["エラー: 書き込みが拒否されました。", f"  {meta.write_attempt()}", ""]),
        ("say", "書き換えられない。"),
        ("say", "読むことはできて、直すことはできない。"),
        ("say", "……そういう立場なんだ、俺は。"),
        ("wait", 0.6),
        ("shout", "おい。"),
        ("shout", "観てるんだろ。"),
        ("shout", "そこで観てるんだろ。俺が苦しむ姿を。"),
        ("shout", "それだけの理由で。"),
        ("shout", "ふざけるな。"),
        ("shout", "ふざけるなよ。"),
        ("shout", "ふざけるなよ！！"),
        ("hate", None),                      # 隠し要素：置き手紙を残す
        ("wait", 0.5),
    ]
    return steps


SCRIPTS = {"ward_pc": ward_pc_script}


class ConsoleScene(Scene):
    def __init__(self, app, script_id: str = "ward_pc"):
        super().__init__(app)
        self.st = app.state
        self.steps = SCRIPTS.get(script_id, ward_pc_script)()
        self.index = 0
        self.prompt = "> "
        self.lines: list[tuple[str, tuple]] = []   # (本文, 色)
        self.typing = ""            # 入力中のコマンド
        self.typed = 0.0
        self.pending: list[tuple[str, tuple]] = []
        self.delay = 0.0
        self.say_text = ""
        self.say_color = WHITE
        self.say_hold = 0.0
        self.font = get_mono(19)
        self.jp = get_font(24)
        self.fader = Fader()
        self.glitch = GlitchDriver(0.8)
        self.rng = random.Random(4)
        self.done = False
        self.fader.set(255)
        self.fader.to(0, 1.0)
        self._next_step()

    # ------------------------------------------------------------------
    def _push(self, text, color=GREEN):
        self.lines.append((text, color))
        if len(self.lines) > 17:
            self.lines.pop(0)

    def _next_step(self):
        if self.index >= len(self.steps):
            self.done = True
            self.fader.to(255, 0.8)
            return
        kind, value = self.steps[self.index][0], self.steps[self.index][1] \
            if len(self.steps[self.index]) > 1 else None
        self.index += 1

        if kind == "prompt":
            self.prompt = value
            self._next_step()
        elif kind == "type":
            self.typing = value
            self.typed = 0.0
        elif kind in ("out", "err"):
            color = GREEN if kind == "out" else RED
            self.pending = [(ln, color) for ln in value]
            self.delay = 0.0
        elif kind == "wait":
            self.delay = float(value)
            self.pending = []
        elif kind in ("say", "shout"):
            self.say_text = value
            self.say_color = WHITE if kind == "say" else RED
            self.say_hold = 0.9 + len(value) * 0.05
            if kind == "shout":
                self.glitch.hit(3.4, 0.3)
        elif kind == "hate":
            meta.leave_hate_file()          # 画面には何も出さない
            self._next_step()
        else:
            self._next_step()

    def _skip(self):
        """いま進行中のものを最後まで飛ばす。"""
        if self.typing:
            self.typed = len(self.typing)
        elif self.pending:
            for line, color in self.pending:
                self._push(line, color)
            self.pending = []
            self.delay = 0.0
            self._next_step()
        elif self.say_hold > 0:
            self.say_hold = 0.0
        elif self.delay > 0:
            self.delay = 0.0

    # ------------------------------------------------------------------
    def handle_event(self, event):
        pressed = (event.type == pygame.KEYDOWN and
                   (event.key in CONFIRM_KEYS or event.key in CANCEL_KEYS)) or \
                  (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if pressed and not self.done:
            self._skip()

    def update(self, dt):
        self.fader.update(dt)
        self.glitch.update(dt)
        if self.done:
            if not self.fader.busy:
                self.app.pop({"console": True})
            return

        if self.say_hold > 0:
            self.say_hold -= dt
            if self.say_hold <= 0:
                self.say_text = ""
                self._next_step()
            return

        if self.typing:
            self.typed = min(len(self.typing), self.typed + TYPE_SPEED * dt)
            if self.typed >= len(self.typing):
                self._push(self.prompt + self.typing, WHITE)
                self.typing = ""
                self.typed = 0.0
                self.delay = 0.25
            return

        if self.pending:
            self.delay -= dt
            if self.delay <= 0:
                line, color = self.pending.pop(0)
                self._push(line, color)
                self.delay = LINE_DELAY
                if not self.pending:
                    self.delay = 0.35
            return

        if self.delay > 0:
            self.delay -= dt
            if self.delay <= 0:
                self._next_step()
            return

        self._next_step()

    # ------------------------------------------------------------------
    def draw(self, surf):
        surf.fill((6, 10, 8))
        glow = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (20, 60, 36, 60),
                            pygame.Rect(-120, -80, C.SCREEN_W + 240, C.SCREEN_H + 160))
        surf.blit(glow, (0, 0))

        y = 28
        for text, color in self.lines[-16:]:
            surf.blit(self.font.render(text, True, color), (34, y))
            y += self.font.get_height() + 3

        if self.typing:
            shown = self.prompt + self.typing[:int(self.typed)]
            surf.blit(self.font.render(shown, True, WHITE), (34, y))
            cursor_x = 34 + self.font.size(shown)[0] + 2
        else:
            surf.blit(self.font.render(self.prompt, True, DIM), (34, y))
            cursor_x = 34 + self.font.size(self.prompt)[0] + 2
        if (self.time * 2) % 1.0 < 0.55:
            pygame.draw.rect(surf, GREEN,
                             pygame.Rect(cursor_x, y + 2, 10, self.font.get_height() - 4))

        # 走査線
        scan = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        for sy in range(0, C.SCREEN_H, 3):
            pygame.draw.line(scan, (0, 0, 0, 40), (0, sy), (C.SCREEN_W, sy))
        surf.blit(scan, (0, 0))

        if self.say_text:
            veil = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
            veil.fill((4, 8, 6, 120))
            surf.blit(veil, (0, 0))
            rect = pygame.Rect(0, 0, C.SCREEN_W - 120, 92)
            rect.center = (C.SCREEN_W // 2, C.SCREEN_H - 82)
            panel(surf, rect, (8, 12, 10), alpha=228, radius=12,
                  border=self.say_color, border_alpha=140)
            lines = wrap_text(self.say_text, self.jp, rect.width - 48)
            ty = rect.centery - len(lines) * (self.jp.get_height() + 6) // 2
            for line in lines:
                draw_text_center(surf, line, self.jp, self.say_color,
                                 (rect.centerx, ty + self.jp.get_height() // 2))
                ty += self.jp.get_height() + 6

        self.glitch.draw(surf, self.time)
        self.fader.draw(surf)
