# -*- coding: utf-8 -*-
"""画像素材を使わず、すべて図形で背景・立ち絵・「ほころび」を描く。

世界はふたつある。
  ゲームの世界（王都・城・虚無）  … 少年がつくった、自分だけが英雄の世界
  現実の世界（部屋・夜道・保健室）… 少年が逃げだしてきた世界
"""

from __future__ import annotations

import math
import random

import pygame

from . import config as C
from .ui import radial_light, vertical_gradient, vignette

SIZE = (C.SCREEN_W, C.SCREEN_H)


def _stars(surf, count, area, color=(255, 255, 255), rng=None):
    rng = rng or random.Random(7)
    for _ in range(count):
        x = rng.uniform(0, C.SCREEN_W)
        y = rng.uniform(*area)
        pygame.draw.circle(surf, (*color, rng.randint(60, 200)),
                           (int(x), int(y)), rng.choice([1, 1, 1, 2]))


# ==========================================================================
# ゲームの世界
# ==========================================================================
def _castle_silhouette(s, color, base_y=330):
    """奥にそびえる城。"""
    pygame.draw.rect(s, color, pygame.Rect(360, base_y - 180, 240, 180))
    for x in (330, 600):
        pygame.draw.rect(s, color, pygame.Rect(x, base_y - 240, 60, 240))
        pygame.draw.polygon(s, color, [(x - 10, base_y - 240), (x + 70, base_y - 240),
                                       (x + 30, base_y - 300)])
    pygame.draw.polygon(s, color, [(350, base_y - 180), (610, base_y - 180),
                                   (480, base_y - 268)])
    pygame.draw.rect(s, tuple(max(0, c - 18) for c in color),
                     pygame.Rect(452, base_y - 90, 56, 90), border_radius=28)


def _bg_capital_day(s):
    """王都の広場。祝祭のあと。ぼくが まもった まち。"""
    s.blit(vertical_gradient(SIZE, (126, 172, 214), (216, 214, 200)), (0, 0))
    pygame.draw.circle(s, (255, 248, 222), (180, 96), 46)
    for cx, cy, r in [(300, 110, 34), (348, 104, 26), (700, 84, 30), (748, 92, 22)]:
        pygame.draw.circle(s, (238, 240, 244), (cx, cy), r)
    _castle_silhouette(s, (150, 152, 172))

    # 石畳の広場
    pygame.draw.rect(s, (188, 180, 166), pygame.Rect(0, 330, C.SCREEN_W, 210))
    for y in range(340, C.SCREEN_H, 34):
        pygame.draw.line(s, (168, 160, 148), (0, y), (C.SCREEN_W, y), 2)
    for x in range(0, C.SCREEN_W, 52):
        pygame.draw.line(s, (168, 160, 148), (x, 330), (x - 40, C.SCREEN_H), 2)

    # 家なみと旗
    rng = random.Random(21)
    for x in range(-30, C.SCREEN_W, 120):
        h = rng.randint(90, 130)
        rect = pygame.Rect(x, 330 - h, 104, h)
        pygame.draw.rect(s, (206, 190, 168), rect)
        pygame.draw.polygon(s, (162, 104, 92), [(rect.x - 10, rect.y), (rect.right + 10, rect.y),
                                                (rect.centerx, rect.y - 34)])
        pygame.draw.rect(s, (120, 150, 176), pygame.Rect(rect.x + 34, rect.y + 34, 30, 34))
    for x in range(60, C.SCREEN_W, 170):
        pygame.draw.line(s, (120, 110, 100), (x, 330), (x, 210), 3)
        pygame.draw.polygon(s, (188, 92, 96), [(x, 212), (x + 52, 228), (x, 250)])

    # ふんすい
    pygame.draw.ellipse(s, (170, 166, 158), pygame.Rect(210, 356, 180, 56))
    pygame.draw.ellipse(s, (150, 186, 206), pygame.Rect(222, 362, 156, 42))
    pygame.draw.rect(s, (182, 176, 166), pygame.Rect(292, 300, 16, 68))
    pygame.draw.ellipse(s, (182, 176, 166), pygame.Rect(266, 288, 68, 22))
    for dx in (-30, 30):
        pygame.draw.arc(s, (196, 220, 236),
                        pygame.Rect(300 + min(0, dx) * 2, 292, 60, 60),
                        0.2 if dx > 0 else 2.6, 1.6 if dx > 0 else 3.0, 3)

    # ぼくの どうぞう
    pygame.draw.rect(s, (168, 162, 150), pygame.Rect(444, 306, 74, 40), border_radius=3)
    pygame.draw.rect(s, (150, 144, 134), pygame.Rect(452, 296, 58, 12), border_radius=3)
    pygame.draw.rect(s, (188, 182, 172), pygame.Rect(470, 232, 22, 66), border_radius=5)
    pygame.draw.circle(s, (188, 182, 172), (481, 222), 15)
    pygame.draw.line(s, (188, 182, 172), (492, 262), (516, 208), 6)   # かかげた けん
    pygame.draw.line(s, (196, 190, 180), (470, 258), (446, 276), 6)

    # パン屋の 露店
    pygame.draw.rect(s, (142, 116, 92), pygame.Rect(640, 256, 130, 10))
    pygame.draw.rect(s, (120, 98, 78), pygame.Rect(648, 266, 8, 74))
    pygame.draw.rect(s, (120, 98, 78), pygame.Rect(754, 266, 8, 74))
    for i in range(5):
        col = (206, 96, 92) if i % 2 == 0 else (238, 232, 220)
        pygame.draw.rect(s, col, pygame.Rect(640 + i * 26, 240, 26, 18))
    pygame.draw.rect(s, (168, 140, 106), pygame.Rect(636, 296, 138, 12), border_radius=3)
    for i in range(4):
        pygame.draw.circle(s, (204, 164, 110), (656 + i * 32, 292), 9)

    # はなかご
    pygame.draw.ellipse(s, (170, 134, 96), pygame.Rect(818, 372, 64, 34))
    for dx, dy, col in [(-16, -8, (226, 132, 150)), (0, -14, (240, 214, 130)),
                        (16, -8, (198, 158, 216)), (-6, -4, (232, 232, 240)),
                        (8, -2, (226, 132, 150))]:
        pygame.draw.circle(s, col, (850 + dx, 372 + dy), 9)


def _bg_capital_night(s):
    """夜の王都。あかりは ついているのに、しずかすぎる。"""
    s.blit(vertical_gradient(SIZE, (26, 32, 62), (58, 54, 78)), (0, 0))
    _stars(s, 120, (0, 260), rng=random.Random(5))
    pygame.draw.circle(s, (238, 236, 214), (760, 92), 40)
    _castle_silhouette(s, (40, 44, 70))
    pygame.draw.rect(s, (44, 42, 54), pygame.Rect(0, 330, C.SCREEN_W, 210))
    rng = random.Random(21)
    for x in range(-30, C.SCREEN_W, 120):
        h = rng.randint(90, 130)
        rect = pygame.Rect(x, 330 - h, 104, h)
        pygame.draw.rect(s, (52, 50, 64), rect)
        pygame.draw.polygon(s, (40, 34, 44), [(rect.x - 10, rect.y), (rect.right + 10, rect.y),
                                              (rect.centerx, rect.y - 34)])
        if rng.random() < 0.7:
            pygame.draw.rect(s, (234, 202, 132), pygame.Rect(rect.x + 34, rect.y + 34, 30, 34))
    for x in range(90, C.SCREEN_W, 210):
        pygame.draw.line(s, (60, 58, 70), (x, 330), (x, 250), 4)
        pygame.draw.circle(s, (250, 226, 160), (x, 244), 10)
        glow = radial_light(70, (250, 226, 160), strength=70)
        s.blit(glow, glow.get_rect(center=(x, 244)))


def _bg_castle_hall(s):
    """玉座の間。みんなが ぼくを たたえる ばしょ。"""
    s.blit(vertical_gradient(SIZE, (58, 44, 66), (34, 28, 42)), (0, 0))
    pygame.draw.polygon(s, (128, 42, 52), [(300, 300), (660, 300), (900, 540), (60, 540)])
    pygame.draw.polygon(s, (150, 56, 64), [(360, 300), (600, 300), (760, 540), (200, 540)])
    for x in (120, 250, 710, 840):
        pygame.draw.rect(s, (86, 76, 96), pygame.Rect(x, 60, 56, 300))
        pygame.draw.rect(s, (112, 100, 122), pygame.Rect(x - 8, 46, 72, 22))
        pygame.draw.rect(s, (112, 100, 122), pygame.Rect(x - 8, 350, 72, 22))
    win = pygame.Rect(380, 60, 200, 210)
    pygame.draw.rect(s, (66, 54, 78), win.inflate(20, 20), border_radius=100)
    pygame.draw.rect(s, (186, 168, 120), win, border_radius=96)
    pygame.draw.rect(s, (150, 120, 96), pygame.Rect(430, 250, 100, 60))
    pygame.draw.rect(s, (196, 166, 110), pygame.Rect(424, 200, 112, 56), border_radius=8)


def _bg_capital_broken(s):
    """こわれていく王都。せかいの ほころびが ひろがった すがた。"""
    _bg_capital_night(s)
    dark = pygame.Surface(SIZE, pygame.SRCALPHA)
    dark.fill((6, 6, 14, 150))
    s.blit(dark, (0, 0))
    rng = random.Random(31)
    for _ in range(14):
        x, y = rng.uniform(40, C.SCREEN_W - 40), rng.uniform(20, 380)
        pts = [(x, y)]
        for _ in range(5):
            x += rng.uniform(-50, 50)
            y += rng.uniform(24, 70)
            pts.append((x, y))
        pygame.draw.lines(s, (4, 4, 10), False, pts, rng.randint(4, 9))
        pygame.draw.lines(s, (210, 60, 130), False, [(p[0] + 3, p[1]) for p in pts], 1)
        pygame.draw.lines(s, (70, 220, 210), False, [(p[0] - 3, p[1]) for p in pts], 1)
    for _ in range(26):   # 抜け落ちた地面
        r = pygame.Rect(rng.randint(0, C.SCREEN_W), rng.randint(330, 520),
                        rng.randint(20, 90), rng.randint(10, 40))
        pygame.draw.rect(s, (6, 6, 12), r)


def _bg_void(s):
    """なにもない ところ。データの すきま。"""
    s.fill((8, 8, 14))
    rng = random.Random(77)
    for i in range(40):
        y = rng.randint(0, C.SCREEN_H)
        w = rng.randint(40, 420)
        col = rng.choice([(28, 34, 54), (36, 28, 44), (22, 40, 44)])
        pygame.draw.rect(s, col, pygame.Rect(rng.randint(-40, C.SCREEN_W), y, w, rng.randint(2, 8)))
    for i in range(8):
        x = rng.randint(0, C.SCREEN_W)
        pygame.draw.line(s, (30, 36, 60), (x, 0), (x, C.SCREEN_H), 1)
    glow = radial_light(300, (90, 120, 200), strength=46)
    s.blit(glow, glow.get_rect(center=(C.SCREEN_W // 2, C.SCREEN_H // 2)))


# ==========================================================================
# 現実の世界
# ==========================================================================
def _room_base(s, lit: bool):
    wall_top = (52, 50, 62) if not lit else (74, 72, 86)
    wall_bottom = (30, 28, 38) if not lit else (46, 44, 56)
    s.blit(vertical_gradient(SIZE, wall_top, wall_bottom), (0, 0))
    pygame.draw.rect(s, (34, 30, 36), pygame.Rect(0, 402, C.SCREEN_W, 140))
    pygame.draw.line(s, (16, 14, 20), (0, 402), (C.SCREEN_W, 402), 3)

    # カーテンを閉めた窓
    win = pygame.Rect(96, 110, 210, 180)
    pygame.draw.rect(s, (24, 22, 30), win.inflate(14, 14))
    pygame.draw.rect(s, (58, 56, 72), win)
    pygame.draw.line(s, (86, 84, 104), (win.centerx, win.y), (win.centerx, win.bottom), 6)

    # 机とモニタ
    pygame.draw.rect(s, (60, 52, 48), pygame.Rect(520, 300, 340, 16))
    pygame.draw.rect(s, (48, 42, 38), pygame.Rect(534, 316, 12, 96))
    pygame.draw.rect(s, (48, 42, 38), pygame.Rect(836, 316, 12, 96))
    monitor = pygame.Rect(596, 178, 196, 118)
    pygame.draw.rect(s, (22, 22, 28), monitor.inflate(12, 12), border_radius=6)
    pygame.draw.rect(s, (96, 150, 170) if not lit else (120, 180, 200), monitor)
    for i in range(6):     # 画面のなかのコード
        pygame.draw.line(s, (170, 220, 230),
                         (monitor.x + 12, monitor.y + 14 + i * 16),
                         (monitor.x + 12 + (140 - i * 17), monitor.y + 14 + i * 16), 3)
    pygame.draw.rect(s, (34, 34, 42), pygame.Rect(640, 300, 120, 10), border_radius=3)
    pygame.draw.rect(s, (40, 40, 50), pygame.Rect(600, 320, 180, 18), border_radius=4)

    # ベッドと、ゆかの ちらかり
    pygame.draw.rect(s, (56, 50, 62), pygame.Rect(40, 330, 220, 90), border_radius=8)
    pygame.draw.rect(s, (78, 72, 92), pygame.Rect(40, 318, 220, 30), border_radius=10)
    rng = random.Random(17)
    for _ in range(12):
        x, y = rng.randint(280, 560), rng.randint(420, 510)
        pygame.draw.rect(s, rng.choice([(70, 66, 74), (84, 76, 70), (60, 64, 76)]),
                         pygame.Rect(x, y, rng.randint(16, 40), rng.randint(8, 16)),
                         border_radius=3)
    pygame.draw.rect(s, (48, 44, 52), pygame.Rect(880, 120, 80, 290))   # ドア
    pygame.draw.circle(s, (150, 146, 140), (896, 270), 7)


def _bg_room_pc(s):
    _room_base(s, lit=True)
    glow = radial_light(260, (120, 190, 210), strength=60)
    s.blit(glow, glow.get_rect(center=(694, 240)))


def _bg_room_dark(s):
    _room_base(s, lit=False)
    dark = pygame.Surface(SIZE, pygame.SRCALPHA)
    dark.fill((6, 6, 14, 90))
    s.blit(dark, (0, 0))


def _bg_outside_night(s):
    """いえの そと。よるの じゅうたくがい。"""
    s.blit(vertical_gradient(SIZE, (20, 24, 44), (44, 46, 64)), (0, 0))
    _stars(s, 90, (0, 220), rng=random.Random(9))
    rng = random.Random(29)
    for x in range(-40, C.SCREEN_W, 150):
        h = rng.randint(120, 190)
        rect = pygame.Rect(x, 380 - h, 130, h)
        pygame.draw.rect(s, (38, 38, 52), rect)
        pygame.draw.polygon(s, (30, 30, 42), [(rect.x - 12, rect.y), (rect.right + 12, rect.y),
                                              (rect.centerx, rect.y - 36)])
        if rng.random() < 0.6:
            pygame.draw.rect(s, (226, 198, 130), pygame.Rect(rect.x + 44, rect.y + 44, 34, 30))
    pygame.draw.rect(s, (34, 34, 42), pygame.Rect(0, 380, C.SCREEN_W, 160))
    pygame.draw.line(s, (60, 60, 70), (0, 380), (C.SCREEN_W, 380), 3)
    # 自分の家の玄関
    pygame.draw.rect(s, (52, 48, 56), pygame.Rect(600, 200, 300, 180))
    pygame.draw.rect(s, (70, 58, 50), pygame.Rect(700, 250, 90, 130), border_radius=4)
    pygame.draw.circle(s, (240, 214, 150), (750, 232), 12)
    glow = radial_light(120, (240, 214, 150), strength=80)
    s.blit(glow, glow.get_rect(center=(750, 232)))
    # 街灯
    pygame.draw.rect(s, (54, 54, 64), pygame.Rect(180, 180, 10, 200))
    pygame.draw.circle(s, (226, 226, 200), (185, 176), 14)
    glow2 = radial_light(180, (226, 226, 200), strength=70)
    s.blit(glow2, glow2.get_rect(center=(185, 176)))


def _bg_street_morning(s):
    """あさの つうがくろ。"""
    s.blit(vertical_gradient(SIZE, (150, 184, 214), (224, 214, 196)), (0, 0))
    pygame.draw.circle(s, (255, 246, 216), (820, 96), 52)
    rng = random.Random(41)
    for x in range(-40, C.SCREEN_W, 140):
        h = rng.randint(110, 170)
        rect = pygame.Rect(x, 360 - h, 120, h)
        pygame.draw.rect(s, (188, 182, 176), rect)
        pygame.draw.polygon(s, (128, 106, 98), [(rect.x - 10, rect.y), (rect.right + 10, rect.y),
                                                (rect.centerx, rect.y - 30)])
        pygame.draw.rect(s, (150, 176, 190), pygame.Rect(rect.x + 40, rect.y + 40, 30, 28))
    pygame.draw.rect(s, (110, 110, 118), pygame.Rect(0, 360, C.SCREEN_W, 180))
    pygame.draw.rect(s, (150, 148, 150), pygame.Rect(0, 360, C.SCREEN_W, 14))
    for x in range(20, C.SCREEN_W, 120):
        pygame.draw.rect(s, (220, 220, 214), pygame.Rect(x, 452, 70, 8))


def _bg_hoken(s):
    """ほけんしつ。しろい カーテンと、まどの ひかり。"""
    s.blit(vertical_gradient(SIZE, (216, 224, 226), (188, 196, 200)), (0, 0))
    pygame.draw.rect(s, (168, 158, 140), pygame.Rect(0, 400, C.SCREEN_W, 140))
    pygame.draw.line(s, (140, 130, 116), (0, 400), (C.SCREEN_W, 400), 3)
    win = pygame.Rect(600, 90, 300, 210)
    pygame.draw.rect(s, (150, 150, 156), win.inflate(16, 16))
    pygame.draw.rect(s, (226, 238, 244), win)
    pygame.draw.line(s, (150, 150, 156), (win.centerx, win.y), (win.centerx, win.bottom), 6)
    glow = radial_light(220, (255, 250, 230), strength=70)
    s.blit(glow, glow.get_rect(center=win.center))
    # カーテンで しきられた ベッド
    pygame.draw.rect(s, (238, 240, 242), pygame.Rect(60, 90, 30, 300))
    for i in range(7):
        pygame.draw.rect(s, (244, 246, 248) if i % 2 else (232, 236, 240),
                         pygame.Rect(90 + i * 34, 90, 34, 300))
    pygame.draw.rect(s, (200, 204, 208), pygame.Rect(330, 330, 200, 76), border_radius=6)
    pygame.draw.rect(s, (240, 242, 246), pygame.Rect(330, 320, 200, 26), border_radius=8)
    # せんせいの つくえ
    pygame.draw.rect(s, (156, 140, 120), pygame.Rect(600, 330, 260, 14))
    pygame.draw.rect(s, (140, 124, 108), pygame.Rect(614, 344, 12, 60))
    pygame.draw.rect(s, (140, 124, 108), pygame.Rect(834, 344, 12, 60))


def _bg_black(s):
    s.fill(C.INK)


def _bg_white(s):
    s.fill((246, 246, 250))


_BUILDERS = {
    "black": _bg_black,
    "white": _bg_white,
    # ゲームの世界
    "capital_day": _bg_capital_day,
    "capital_night": _bg_capital_night,
    "castle_hall": _bg_castle_hall,
    "capital_broken": _bg_capital_broken,
    "void": _bg_void,
    # 現実
    "room_pc": _bg_room_pc,
    "room_dark": _bg_room_dark,
    "outside_night": _bg_outside_night,
    "street_morning": _bg_street_morning,
    "hoken": _bg_hoken,
}

_cache: dict[str, pygame.Surface] = {}


def background_surface(name: str) -> pygame.Surface:
    if name not in _cache:
        surf = pygame.Surface(SIZE).convert()
        _BUILDERS.get(name, _bg_black)(surf)
        surf.blit(vignette(SIZE), (0, 0))
        _cache[name] = surf
    return _cache[name]


# ==========================================================================
# ほころび（グリッチ）表現
# ==========================================================================
def glitch(surf: pygame.Surface, level: float, t: float, rng: random.Random | None = None):
    """画面に「ほころび」を走らせる。level は 0.0〜5.0 くらいを想定。"""
    if level <= 0:
        return
    rng = rng or random.Random(int(t * 12) * 7919 + int(level))
    w, h = surf.get_size()

    # 横スライスのずれ
    for _ in range(int(2 + level * 2)):
        sh = rng.randint(6, max(8, int(10 + level * 8)))
        y = rng.randint(0, max(1, h - sh))
        strip = surf.subsurface(pygame.Rect(0, y, w, sh)).copy()
        dx = rng.randint(-int(6 + level * 7), int(6 + level * 7))
        surf.blit(strip, (dx, y))

    # 色ずれの帯
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(int(1 + level)):
        y = rng.randint(0, h - 4)
        bh = rng.randint(2, 8 + int(level * 3))
        color = rng.choice([(226, 60, 140), (60, 226, 210), (250, 240, 120)])
        pygame.draw.rect(layer, (*color, rng.randint(40, 90)), pygame.Rect(0, y, w, bh))
    # 抜け落ちた四角
    for _ in range(int(level)):
        r = pygame.Rect(rng.randint(0, w - 40), rng.randint(0, h - 30),
                        rng.randint(16, 70), rng.randint(8, 30))
        pygame.draw.rect(layer, (8, 8, 14, rng.randint(90, 180)), r)
    surf.blit(layer, (0, 0))


def draw_tear(surf, center, size, t, seed=0):
    """一か所の「ほころび」を描く（探索シーンの目印にも使う）。"""
    rng = random.Random(seed)
    cx, cy = center
    pts = [(cx, cy - size)]
    for i in range(6):
        pts.append((cx + rng.uniform(-size * 0.5, size * 0.5),
                    cy - size + (i + 1) * (size * 2 / 6)))
    wobble = math.sin(t * 6 + seed) * 2
    pygame.draw.lines(surf, (6, 6, 12), False, [(x + wobble, y) for x, y in pts], 5)
    pygame.draw.lines(surf, (232, 70, 150), False, [(x + wobble + 2, y) for x, y in pts], 1)
    pygame.draw.lines(surf, (70, 228, 214), False, [(x + wobble - 2, y) for x, y in pts], 1)


class Background:
    """背景の切り替え（クロスフェード）と、ほころびの層。"""

    AMBIENT = {
        "capital_day": ("light", (255, 246, 220)),
        "capital_night": ("light", (240, 226, 170)),
        "castle_hall": ("light", (236, 210, 150)),
        "capital_broken": ("ash", (70, 66, 80)),
        "void": ("light", (120, 150, 220)),
        "room_pc": ("dust", (150, 190, 210)),
        "room_dark": ("dust", (120, 124, 140)),
        "outside_night": ("dust", (150, 154, 170)),
        "street_morning": ("light", (255, 248, 230)),
        "hoken": ("light", (255, 252, 240)),
    }

    def __init__(self, name="black"):
        from .ui import Particles
        self.name = name
        self.prev = None
        self.blend = 1.0
        self.glitch_level = 0.0
        self._Particles = Particles
        self.particles = self._make_particles(name)

    def _make_particles(self, name):
        kind, color = self.AMBIENT.get(name, (None, C.PAPER))
        if kind == "dust":
            return self._Particles(44, color, speed=(-10, -3), size=(1, 2), alpha=70, drift=10)
        if kind == "light":
            return self._Particles(38, color, speed=(-24, -8), size=(1, 3), alpha=110, drift=16)
        if kind == "ash":
            return self._Particles(60, color, speed=(14, 44), size=(1, 3), alpha=140, drift=8)
        return None

    def change(self, name: str, instant=False):
        if name == self.name:
            return
        self.prev = self.name
        self.name = name
        self.blend = 1.0 if instant else 0.0
        self.particles = self._make_particles(name)

    def update(self, dt, t):
        if self.blend < 1.0:
            self.blend = min(1.0, self.blend + dt / 0.6)
        if self.particles:
            self.particles.update(dt, t)

    def draw(self, surf, t):
        cur = background_surface(self.name)
        if self.prev and self.blend < 1.0:
            surf.blit(background_surface(self.prev), (0, 0))
            img = cur.copy()
            img.set_alpha(int(255 * self.blend))
            surf.blit(img, (0, 0))
        else:
            surf.blit(cur, (0, 0))
        if self.particles:
            self.particles.draw(surf, t)


# ==========================================================================
# 立ち絵
# ==========================================================================
def _body(surf, cx, base_y, h, body_col, head_col, hair_col=None, hair="short",
          arm_col=None, leg_col=None, face=True, eye_col=(46, 44, 56)):
    """人のかたちを描く共通部分。足・腕・顔を持つ簡略シルエット。

    戻り値は (頭の中心 y, 頭の半径)。
    """
    head_r = int(h * 0.125)
    head_y = base_y - int(h * 0.855)
    shoulder_y = head_y + int(head_r * 1.5)
    hip_y = base_y - int(h * 0.30)
    arm_col = arm_col or body_col

    # 足
    if leg_col:
        leg_w = int(h * 0.075)
        for dx in (-int(h * 0.055), int(h * 0.055)):
            pygame.draw.rect(surf, leg_col, pygame.Rect(
                cx + dx - leg_w // 2, hip_y, leg_w, base_y - hip_y), border_radius=4)
        pygame.draw.rect(surf, tuple(max(0, c - 22) for c in leg_col), pygame.Rect(
            cx - int(h * 0.10), base_y - int(h * 0.03), int(h * 0.20), int(h * 0.03)),
            border_radius=3)
        body_bottom = hip_y + int(h * 0.02)
    else:
        body_bottom = base_y

    # 胴
    pygame.draw.polygon(surf, body_col, [
        (cx - int(h * 0.125), body_bottom), (cx + int(h * 0.125), body_bottom),
        (cx + int(h * 0.105), shoulder_y), (cx - int(h * 0.105), shoulder_y)])
    pygame.draw.circle(surf, body_col, (cx, shoulder_y), int(h * 0.105))

    # 腕
    arm_w = int(h * 0.048)
    for dx in (-int(h * 0.125), int(h * 0.125)):
        pygame.draw.rect(surf, arm_col, pygame.Rect(
            cx + dx - arm_w // 2, shoulder_y - int(h * 0.01),
            arm_w, int(h * 0.30)), border_radius=arm_w // 2)
        pygame.draw.circle(surf, head_col, (cx + dx, shoulder_y + int(h * 0.30)),
                           max(2, int(h * 0.026)))

    # くび と あたま
    pygame.draw.rect(surf, head_col, pygame.Rect(
        cx - int(h * 0.026), head_y + int(head_r * 0.6), int(h * 0.052), int(h * 0.05)))
    pygame.draw.circle(surf, head_col, (cx, head_y), head_r)

    if hair_col:
        if hair == "long":
            pygame.draw.ellipse(surf, hair_col, pygame.Rect(
                cx - int(head_r * 1.15), head_y - head_r,
                int(head_r * 2.3), int(head_r * 3.2)))
            pygame.draw.circle(surf, hair_col, (cx, head_y - int(head_r * 0.14)),
                               int(head_r * 1.06))
            pygame.draw.circle(surf, head_col, (cx, head_y + int(head_r * 0.16)),
                               int(head_r * 0.84))
        else:
            pygame.draw.circle(surf, hair_col, (cx, head_y - int(head_r * 0.24)), head_r)
            pygame.draw.rect(surf, head_col, pygame.Rect(
                cx - head_r, head_y + int(head_r * 0.12), head_r * 2, head_r))
            pygame.draw.circle(surf, head_col, (cx, head_y + int(head_r * 0.12)),
                               int(head_r * 0.92))

    if face:
        eye_dx = max(2, int(head_r * 0.36))
        eye_y = head_y + int(head_r * 0.16)
        pygame.draw.circle(surf, eye_col, (cx - eye_dx, eye_y), max(2, int(head_r * 0.13)))
        pygame.draw.circle(surf, eye_col, (cx + eye_dx, eye_y), max(2, int(head_r * 0.13)))
    return head_y, head_r


def _draw_yuusha(surf, cx, base_y, h, t):
    """勇者。少年が つくった「りそうの じぶん」。"""
    glow = radial_light(int(h * 0.62), (250, 228, 150), strength=70)
    surf.blit(glow, glow.get_rect(center=(cx, base_y - int(h * 0.5))))
    sway = math.sin(t * 1.3) * 8
    pygame.draw.polygon(surf, (46, 76, 148), [           # マント
        (cx - int(h * 0.12), base_y - int(h * 0.70)),
        (cx + int(h * 0.12), base_y - int(h * 0.70)),
        (cx + int(h * 0.24) + sway, base_y + 2),
        (cx - int(h * 0.24) + sway, base_y + 2)])
    head_y, head_r = _body(surf, cx, base_y, h, (228, 228, 238), (234, 208, 184),
                           (240, 206, 104), "short", arm_col=(206, 208, 220),
                           leg_col=(78, 92, 130))
    pygame.draw.rect(surf, (182, 152, 62), pygame.Rect(      # ベルト
        cx - int(h * 0.12), base_y - int(h * 0.33), int(h * 0.24), int(h * 0.045)))
    pygame.draw.polygon(surf, (206, 210, 224), [             # 肩あて
        (cx - int(h * 0.17), base_y - int(h * 0.64)),
        (cx - int(h * 0.06), base_y - int(h * 0.68)),
        (cx - int(h * 0.07), base_y - int(h * 0.58))])
    pygame.draw.polygon(surf, (206, 210, 224), [
        (cx + int(h * 0.17), base_y - int(h * 0.64)),
        (cx + int(h * 0.06), base_y - int(h * 0.68)),
        (cx + int(h * 0.07), base_y - int(h * 0.58))])
    pygame.draw.line(surf, (222, 226, 236),                  # けん
                     (cx + int(h * 0.17), base_y - int(h * 0.20)),
                     (cx + int(h * 0.26), base_y - int(h * 0.78)), 5)
    pygame.draw.line(surf, (182, 152, 62),
                     (cx + int(h * 0.13), base_y - int(h * 0.26)),
                     (cx + int(h * 0.21), base_y - int(h * 0.29)), 5)


def _draw_boku(surf, cx, base_y, h, t):
    """げんじつの ぼく。パーカーの フードを かぶって、すこし まえかがみ。"""
    head_y, head_r = _body(surf, cx, base_y, h, (78, 82, 104), (198, 178, 166),
                           None, "short", arm_col=(70, 74, 96),
                           leg_col=(58, 60, 74), face=True, eye_col=(60, 60, 76))
    # フード
    pygame.draw.circle(surf, (64, 68, 88), (cx, head_y - int(head_r * 0.22)),
                       int(head_r * 1.18))
    pygame.draw.circle(surf, (198, 178, 166), (cx, head_y + int(head_r * 0.12)),
                       int(head_r * 0.86))
    shade = pygame.Surface((head_r * 3, head_r * 3), pygame.SRCALPHA)
    pygame.draw.circle(shade, (30, 32, 44, 110), (int(head_r * 1.5), int(head_r * 1.5)),
                       int(head_r * 0.88))
    surf.blit(shade, shade.get_rect(center=(cx, head_y + int(head_r * 0.12))))
    eye_dx = max(2, int(head_r * 0.36))
    pygame.draw.circle(surf, (196, 200, 216), (cx - eye_dx, head_y + int(head_r * 0.18)), 3)
    pygame.draw.circle(surf, (196, 200, 216), (cx + eye_dx, head_y + int(head_r * 0.18)), 3)


def _draw_riina(surf, cx, base_y, h, t):
    """リィナ。ゲームの ヒロイン。いつも ぼくを ほめる。"""
    glow = radial_light(int(h * 0.5), (250, 190, 210), strength=54)
    surf.blit(glow, glow.get_rect(center=(cx, base_y - int(h * 0.5))))
    head_y, head_r = _body(surf, cx, base_y, h, (240, 234, 240), (242, 218, 204),
                           (228, 150, 176), "long", arm_col=(236, 228, 236))
    pygame.draw.polygon(surf, (236, 228, 238), [          # スカート
        (cx - int(h * 0.20), base_y), (cx + int(h * 0.20), base_y),
        (cx + int(h * 0.11), base_y - int(h * 0.30)),
        (cx - int(h * 0.11), base_y - int(h * 0.30))])
    pygame.draw.rect(surf, (226, 150, 176), pygame.Rect(
        cx - int(h * 0.12), base_y - int(h * 0.33), int(h * 0.24), int(h * 0.035)))
    # ほほえみ
    pygame.draw.arc(surf, (206, 140, 150),
                    pygame.Rect(cx - int(head_r * 0.34), head_y + int(head_r * 0.30),
                                int(head_r * 0.68), int(head_r * 0.5)), 3.34, 6.08, 2)


def _draw_minami(surf, cx, base_y, h, t):
    """みなみ。リィナの モデルに なった、げんじつの クラスメート。"""
    _body(surf, cx, base_y, h, (72, 88, 116), (222, 200, 186), (74, 58, 54), "long",
          arm_col=(66, 80, 106), leg_col=(214, 196, 182))
    pygame.draw.polygon(surf, (58, 70, 96), [             # セーラーのスカート
        (cx - int(h * 0.17), base_y - int(h * 0.26)), (cx + int(h * 0.17), base_y - int(h * 0.26)),
        (cx + int(h * 0.12), base_y - int(h * 0.40)), (cx - int(h * 0.12), base_y - int(h * 0.40))])
    pygame.draw.polygon(surf, (226, 232, 238), [          # えり
        (cx - int(h * 0.09), base_y - int(h * 0.70)), (cx + int(h * 0.09), base_y - int(h * 0.70)),
        (cx, base_y - int(h * 0.60))])


def _draw_father(surf, cx, base_y, h, t):
    _body(surf, cx, base_y, h, (62, 62, 72), (190, 172, 160), (46, 44, 46), "short",
          arm_col=(56, 56, 66), leg_col=(44, 44, 54))


def _draw_nurse(surf, cx, base_y, h, t):
    """ほけんしつの せんせい。"""
    head_y, head_r = _body(surf, cx, base_y, h, (244, 246, 248), (228, 204, 188),
                           (96, 78, 66), "long", arm_col=(238, 240, 244),
                           leg_col=(196, 200, 206))
    pygame.draw.rect(surf, (172, 190, 204), pygame.Rect(   # むねポケット
        cx + int(h * 0.02), base_y - int(h * 0.56), int(h * 0.07), int(h * 0.09)))
    pygame.draw.line(surf, (208, 212, 218), (cx, base_y - int(h * 0.66)),
                     (cx, base_y - int(h * 0.34)), 2)


def _draw_classmate(surf, cx, base_y, h, t):
    """かつての クラスメート。かおは、いつも おもいだせない。"""
    head_y, head_r = _body(surf, cx, base_y, h, (64, 68, 80), (176, 170, 168),
                           (40, 40, 46), "short", arm_col=(58, 62, 74),
                           leg_col=(50, 52, 62), face=False)
    blur = pygame.Surface((head_r * 3, head_r * 3), pygame.SRCALPHA)
    for i in range(4):
        pygame.draw.circle(blur, (140, 140, 150, 60),
                           (int(head_r * 1.5) + random.Random(i).randint(-3, 3),
                            int(head_r * 1.5)), int(head_r * (0.8 + i * 0.1)))
    surf.blit(blur, blur.get_rect(center=(cx, head_y)))


def _draw_bug(surf, cx, base_y, h, t):
    """ほころびから でてくる、ノイズの ひとがた。"""
    rng = random.Random(int(t * 10) % 211)
    h2 = int(h * 0.92)
    for i in range(12):
        y = base_y - int(h2 * (i + 1) / 12)
        w = int(h2 * (0.24 if i < 9 else 0.15))
        dx = rng.randint(-9, 9)
        col = rng.choice([(24, 24, 34), (226, 60, 140), (60, 226, 210), (18, 18, 26)])
        pygame.draw.rect(surf, col, pygame.Rect(cx - w // 2 + dx, y, w, int(h2 / 12) + 2))
    pygame.draw.circle(surf, (250, 250, 255), (cx - 10, base_y - int(h2 * 0.88)), 4)
    pygame.draw.circle(surf, (250, 250, 255), (cx + 10, base_y - int(h2 * 0.88)), 4)


CHARACTERS = {
    "yuusha": _draw_yuusha,
    "boku": _draw_boku,
    "riina": _draw_riina,
    "minami": _draw_minami,
    "father": _draw_father,
    "nurse": _draw_nurse,
    "classmate": _draw_classmate,
    "bug": _draw_bug,
}

POSITIONS = {"left": 0.24, "center": 0.5, "right": 0.76}


def draw_character(surf, cid: str, pos="center", t: float = 0.0, alpha: int = 255,
                   scale: float = 1.0, base_y: int | None = None, glitch_level: float = 0.0):
    fn = CHARACTERS.get(cid)
    if fn is None:
        return
    ratio = POSITIONS.get(pos, 0.5) if isinstance(pos, str) else float(pos)
    cx = int(C.SCREEN_W * ratio)
    h = int(300 * scale)
    by = (base_y if base_y is not None else 404) + int(math.sin(t * 1.6 + ratio * 4) * 3)

    layer = pygame.Surface(SIZE, pygame.SRCALPHA)
    shadow = pygame.Surface((160, 30), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
    layer.blit(shadow, shadow.get_rect(center=(cx, by + 6)))
    fn(layer, cx, by, h, t)
    if glitch_level > 0:
        glitch(layer, glitch_level, t)
    if alpha < 255:
        layer.set_alpha(max(0, alpha))
    surf.blit(layer, (0, 0))
