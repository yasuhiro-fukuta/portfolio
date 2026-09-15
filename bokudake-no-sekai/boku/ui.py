# -*- coding: utf-8 -*-
"""描画まわりの部品：文字組み、メッセージウィンドウ、選択肢、履歴、演出。"""

from __future__ import annotations

import math
import random

import pygame

from . import config as C
from .fonts import get_font


# --------------------------------------------------------------------------
# 文字組み
# --------------------------------------------------------------------------
def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """日本語向けの折り返し。簡易的な禁則処理つき。"""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for ch in paragraph:
            trial = line + ch
            if font.size(trial)[0] <= max_width or not line:
                line = trial
                continue
            # 折り返し位置の調整（行頭・行末にできない文字を送る／引き取る）
            if ch in C.NO_LINE_START and len(line) > 1:
                lines.append(line + ch)   # ぶら下げ
                line = ""
                continue
            if line[-1] in C.NO_LINE_END:
                lines.append(line[:-1])
                line = line[-1] + ch
                continue
            lines.append(line)
            line = ch
        lines.append(line)
    return lines


def draw_text_shadow(surf, text, font, color, pos, shadow=(0, 0, 0), offset=2, alpha=150):
    """影つきで一行描く。left/top 指定。"""
    if shadow is not None:
        sh = font.render(text, True, shadow)
        sh.set_alpha(alpha)
        surf.blit(sh, (pos[0] + offset, pos[1] + offset))
    img = font.render(text, True, color)
    surf.blit(img, pos)
    return img.get_size()


def draw_text_center(surf, text, font, color, center, shadow=(0, 0, 0), alpha=255):
    img = font.render(text, True, color)
    if alpha < 255:
        img.set_alpha(alpha)
    rect = img.get_rect(center=center)
    if shadow is not None:
        sh = font.render(text, True, shadow)
        sh.set_alpha(int(120 * alpha / 255))
        surf.blit(sh, rect.move(2, 2))
    surf.blit(img, rect)
    return rect


def panel(surf, rect, color, alpha=200, radius=14, border=None, border_alpha=120):
    """半透明のパネルを描く。"""
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(layer, (*border, border_alpha), layer.get_rect(),
                         width=2, border_radius=radius)
    surf.blit(layer, rect.topleft)


def vertical_gradient(size, top_color, bottom_color):
    """縦グラデーションの Surface を作る。"""
    w, h = size
    surf = pygame.Surface((1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        surf.set_at((0, y), (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
        ))
    return pygame.transform.smoothscale(surf, (w, h))


def radial_light(radius, color, strength=120, steps=18):
    """ふんわりした光の円。"""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(strength * (1 - t) ** 2)
        pygame.draw.circle(surf, (*color, a), (radius, radius), int(radius * t))
    return surf


def vignette(size, strength=110):
    """画面のふちを暗く落とす。"""
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = 26
    for i in range(steps):
        t = i / steps
        a = int(strength * t ** 2 / steps * 4)
        inset = int(min(w, h) * 0.5 * t)
        pygame.draw.rect(surf, (0, 0, 0, a),
                         pygame.Rect(inset // 2, inset // 2, w - inset, h - inset),
                         width=max(2, inset // 6), border_radius=inset)
    return surf


# --------------------------------------------------------------------------
# 漂う粒子（ほこり・ひかり・雨）
# --------------------------------------------------------------------------
class Particles:
    def __init__(self, count=48, color=C.PAPER, speed=(-6, -18), size=(1, 3), alpha=90, drift=12.0):
        self.color = color
        self.alpha = alpha
        self.drift = drift
        self.speed = speed
        self.size_range = size
        self.items = [self._spawn(initial=True) for _ in range(count)]

    def _spawn(self, initial=False):
        return {
            "x": random.uniform(0, C.SCREEN_W),
            "y": random.uniform(0, C.SCREEN_H) if initial else C.SCREEN_H + 8,
            "vy": random.uniform(*self.speed),
            "r": random.uniform(*self.size_range),
            "phase": random.uniform(0, math.tau),
            "a": random.uniform(0.35, 1.0),
        }

    def update(self, dt, t):
        for i, p in enumerate(self.items):
            p["y"] += p["vy"] * dt
            p["x"] += math.sin(t * 0.6 + p["phase"]) * self.drift * dt
            out = (p["y"] < -12 or p["y"] > C.SCREEN_H + 12
                   or p["x"] < -24 or p["x"] > C.SCREEN_W + 24)
            if out:
                self.items[i] = self._spawn()

    def draw(self, surf, t):
        layer = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        for p in self.items:
            a = int(self.alpha * p["a"] * (0.6 + 0.4 * math.sin(t * 1.4 + p["phase"])))
            pygame.draw.circle(layer, (*self.color, max(0, a)),
                               (int(p["x"]), int(p["y"])), max(1, int(p["r"])))
        surf.blit(layer, (0, 0))


# --------------------------------------------------------------------------
# メッセージウィンドウ
# --------------------------------------------------------------------------
class MessageWindow:
    """タイプライタ表示のメッセージ枠。"""

    def __init__(self):
        self.font = get_font(C.TEXT_SIZE)
        self.name_font = get_font(C.NAME_SIZE, bold=True)
        self.name = ""
        self.lines: list[str] = []
        self.full_text = ""
        self.shown = 0.0
        self.visible = True
        self.fast = False
        self.color = C.PAPER

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            C.WIN_MARGIN_X,
            C.SCREEN_H - C.WIN_MARGIN_BOTTOM - C.WIN_HEIGHT,
            C.SCREEN_W - C.WIN_MARGIN_X * 2,
            C.WIN_HEIGHT,
        )

    @property
    def text_width(self) -> int:
        return self.rect.width - C.WIN_PAD * 2

    def set_text(self, text: str, name: str = "", color=C.PAPER):
        self.name = name
        self.color = color
        self.full_text = text
        self.lines = wrap_text(text, self.font, self.text_width)
        self.shown = 0.0
        self.visible = True

    def clear(self):
        self.name = ""
        self.full_text = ""
        self.lines = []
        self.shown = 0.0

    @property
    def finished(self) -> bool:
        return self.shown >= len(self.full_text.replace("\n", ""))

    def skip(self):
        self.shown = float(len(self.full_text))

    def update(self, dt):
        speed = C.TYPE_SPEED_FAST if self.fast else C.TYPE_SPEED
        self.shown = min(len(self.full_text), self.shown + speed * dt)

    def draw(self, surf, t):
        if not self.visible or (not self.lines and not self.name):
            return
        rect = self.rect
        panel(surf, rect, (14, 16, 26), alpha=196, radius=16,
              border=C.MIST, border_alpha=70)

        if self.name:
            nrect = pygame.Rect(rect.x + 18, rect.y - 20, 0, 38)
            nw = self.name_font.size(self.name)[0] + 34
            nrect.width = nw
            panel(surf, nrect, (30, 34, 52), alpha=225, radius=12,
                  border=C.GOLD, border_alpha=90)
            draw_text_center(surf, self.name, self.name_font, C.GOLD, nrect.center)

        remaining = int(self.shown)
        y = rect.y + C.WIN_PAD
        for line in self.lines:
            if remaining <= 0:
                break
            part = line[:remaining]
            remaining -= len(line)
            draw_text_shadow(surf, part, self.font, self.color,
                             (rect.x + C.WIN_PAD, y), offset=2, alpha=170)
            y += self.font.get_height() + C.LINE_GAP

        if self.finished:
            bob = math.sin(t * 5.0) * 3
            cx = rect.right - 26
            cy = rect.bottom - 22 + bob
            pygame.draw.polygon(surf, C.GOLD,
                                [(cx - 8, cy - 5), (cx + 8, cy - 5), (cx, cy + 6)])


# --------------------------------------------------------------------------
# 選択肢
# --------------------------------------------------------------------------
class ChoiceMenu:
    def __init__(self, options: list[str], center_y: int | None = None, width: int = 560):
        self.font = get_font(24)
        self.options = options
        self.index = 0
        self.width = width
        self.item_h = 52
        self.gap = 12
        total = len(options) * self.item_h + (len(options) - 1) * self.gap
        cy = center_y if center_y is not None else C.SCREEN_H // 2 - 40
        self.top = cy - total // 2

    def rect_of(self, i) -> pygame.Rect:
        return pygame.Rect(
            (C.SCREEN_W - self.width) // 2,
            self.top + i * (self.item_h + self.gap),
            self.width, self.item_h,
        )

    def move(self, delta):
        self.index = (self.index + delta) % len(self.options)

    def hover(self, pos) -> bool:
        for i in range(len(self.options)):
            if self.rect_of(i).collidepoint(pos):
                self.index = i
                return True
        return False

    def click(self, pos) -> int | None:
        for i in range(len(self.options)):
            if self.rect_of(i).collidepoint(pos):
                return i
        return None

    def draw(self, surf, t):
        for i, text in enumerate(self.options):
            r = self.rect_of(i)
            selected = i == self.index
            if selected:
                glow = radial_light(r.height, C.GOLD, strength=60)
                surf.blit(glow, glow.get_rect(center=r.center))
            panel(surf, r, (30, 34, 54) if not selected else (58, 62, 92),
                  alpha=225, radius=10,
                  border=C.GOLD if selected else C.MIST,
                  border_alpha=200 if selected else 60)
            color = C.PAPER if selected else C.MIST
            draw_text_center(surf, text, self.font, color, r.center)
            if selected:
                bob = math.sin(t * 6) * 2
                draw_text_center(surf, "▶", self.font, C.GOLD,
                                 (r.x + 22 + bob, r.centery))


# --------------------------------------------------------------------------
# バックログ（既読履歴）
# --------------------------------------------------------------------------
class Backlog:
    LIMIT = 120

    def __init__(self):
        self.entries: list[tuple[str, str]] = []
        self.open = False
        self.offset = 0

    def push(self, name: str, text: str):
        self.entries.append((name, text))
        if len(self.entries) > self.LIMIT:
            self.entries.pop(0)

    def toggle(self):
        self.open = not self.open
        self.offset = 0

    def scroll(self, delta):
        self.offset = max(0, min(len(self.entries), self.offset + delta))

    def draw(self, surf):
        overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((8, 10, 18, 235))
        surf.blit(overlay, (0, 0))
        title_font = get_font(22, bold=True)
        draw_text_shadow(surf, "── これまでのはなし　［↑↓ でスクロール／B・ESC でもどる］",
                         title_font, C.MIST, (48, 28))

        font = get_font(21)
        name_font = get_font(19, bold=True)
        shown = self.entries[::-1][self.offset:]
        y = C.SCREEN_H - 60
        for name, text in shown:
            body = wrap_text(text, font, C.SCREEN_W - 180)
            block_h = len(body) * (font.get_height() + 6) + 14
            y -= block_h
            if y < 70:
                break
            yy = y
            if name:
                draw_text_shadow(surf, name, name_font, C.GOLD, (60, yy - 2))
            for line in body:
                draw_text_shadow(surf, line, font, C.PAPER, (150, yy))
                yy += font.get_height() + 6


# --------------------------------------------------------------------------
# 画面演出
# --------------------------------------------------------------------------
class Fader:
    """フェードイン／アウトの管理。"""

    def __init__(self):
        self.alpha = 0.0
        self.target = 0.0
        self.speed = 255.0 / 0.5
        self.color = (0, 0, 0)

    def to(self, alpha, duration=0.5, color=(0, 0, 0)):
        self.target = float(alpha)
        self.color = color
        self.speed = abs(alpha - self.alpha) / max(0.01, duration)

    def set(self, alpha, color=(0, 0, 0)):
        self.alpha = self.target = float(alpha)
        self.color = color

    @property
    def busy(self) -> bool:
        return abs(self.alpha - self.target) > 0.5

    def update(self, dt):
        if self.alpha < self.target:
            self.alpha = min(self.target, self.alpha + self.speed * dt)
        elif self.alpha > self.target:
            self.alpha = max(self.target, self.alpha - self.speed * dt)

    def draw(self, surf):
        if self.alpha <= 0.5:
            return
        layer = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        layer.fill((*self.color, int(min(255, self.alpha))))
        surf.blit(layer, (0, 0))


class Shake:
    def __init__(self):
        self.time = 0.0
        self.power = 0.0

    def kick(self, power=10.0, duration=0.35):
        self.power = power
        self.time = duration

    def update(self, dt):
        self.time = max(0.0, self.time - dt)

    @property
    def offset(self) -> tuple[int, int]:
        if self.time <= 0:
            return (0, 0)
        p = self.power * self.time
        return (int(random.uniform(-p, p)), int(random.uniform(-p, p)))
