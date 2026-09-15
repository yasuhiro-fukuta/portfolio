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


def _street(s, night: bool):
    """住宅街のみち。night=True なら よるの いろ。"""
    if night:
        s.blit(vertical_gradient(SIZE, (22, 26, 48), (52, 52, 70)), (0, 0))
        _stars(s, 90, (0, 220), rng=random.Random(9))
        pygame.draw.circle(s, (238, 236, 214), (820, 92), 38)
        wall, roof, win_on, road, curb = ((52, 50, 62), (38, 32, 40),
                                          (232, 202, 134), (44, 44, 54), (66, 66, 76))
    else:
        s.blit(vertical_gradient(SIZE, (150, 184, 214), (224, 214, 196)), (0, 0))
        pygame.draw.circle(s, (255, 246, 216), (820, 96), 52)
        wall, roof, win_on, road, curb = ((188, 182, 176), (128, 106, 98),
                                          (150, 176, 190), (110, 110, 118), (150, 148, 150))
    rng = random.Random(41)
    for x in range(-40, C.SCREEN_W, 140):
        h = rng.randint(110, 170)
        rect = pygame.Rect(x, 360 - h, 120, h)
        pygame.draw.rect(s, wall, rect)
        pygame.draw.polygon(s, roof, [(rect.x - 10, rect.y), (rect.right + 10, rect.y),
                                      (rect.centerx, rect.y - 30)])
        lit = (not night) or rng.random() < 0.55
        pygame.draw.rect(s, win_on if lit else (40, 40, 52),
                         pygame.Rect(rect.x + 40, rect.y + 40, 30, 28))
    pygame.draw.rect(s, road, pygame.Rect(0, 360, C.SCREEN_W, 180))
    pygame.draw.rect(s, curb, pygame.Rect(0, 360, C.SCREEN_W, 14))
    for x in range(20, C.SCREEN_W, 120):
        pygame.draw.rect(s, (220, 220, 214) if not night else (150, 150, 158),
                         pygame.Rect(x, 452, 70, 8))
    if night:
        for x in range(120, C.SCREEN_W, 320):
            pygame.draw.rect(s, (60, 60, 70), pygame.Rect(x - 5, 200, 10, 160))
            pygame.draw.circle(s, (232, 228, 196), (x, 196), 12)
            g = radial_light(180, (240, 226, 178), strength=70)
            s.blit(g, g.get_rect(center=(x, 196)))


def _bg_street_morning(s):
    """あさの つうがくろ。"""
    _street(s, night=False)


def _bg_street_night(s):
    """よるの じゅうたくがい。おつかいの みち。"""
    _street(s, night=True)


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


def _bg_ball_room(s):
    """舞踏会の広間。シャンデリアと、顔のない人影たち。"""
    s.blit(vertical_gradient(SIZE, (64, 48, 78), (40, 30, 48)), (0, 0))
    pygame.draw.polygon(s, (110, 76, 88), [(0, 300), (C.SCREEN_W, 300),
                                           (C.SCREEN_W, C.SCREEN_H), (0, C.SCREEN_H)])
    for i in range(14):                      # 市松の床
        for j in range(5):
            if (i + j) % 2 == 0:
                pygame.draw.polygon(s, (126, 92, 102), [
                    (i * 80 - 40 + j * 10, 320 + j * 46), (i * 80 + 40 + j * 10, 320 + j * 46),
                    (i * 80 + 46 + j * 12, 366 + j * 46), (i * 80 - 46 + j * 12, 366 + j * 46)])
    for x in (100, 860):                     # 柱
        pygame.draw.rect(s, (96, 82, 106), pygame.Rect(x - 26, 40, 52, 264))
        pygame.draw.rect(s, (124, 108, 134), pygame.Rect(x - 34, 30, 68, 20))
    win = pygame.Rect(370, 40, 220, 220)     # 大窓
    pygame.draw.rect(s, (72, 60, 88), win.inflate(18, 18), border_radius=110)
    pygame.draw.rect(s, (40, 46, 84), win, border_radius=106)
    pygame.draw.circle(s, (238, 232, 206), (480, 110), 26)
    # シャンデリア
    pygame.draw.line(s, (120, 104, 78), (480, 0), (480, 60), 3)
    for r, a in ((54, 90), (38, 120), (22, 150)):
        pygame.draw.circle(s, (206, 178, 110), (480, 70), r, 2)
    for dx in (-44, -22, 0, 22, 44):
        pygame.draw.circle(s, (252, 236, 180), (480 + dx, 78 + abs(dx) // 4), 5)
        g = radial_light(60, (252, 236, 180), strength=70)
        s.blit(g, g.get_rect(center=(480 + dx, 78 + abs(dx) // 4)))
    # 踊る人影
    rng = random.Random(55)
    for _ in range(9):
        x = rng.randint(60, C.SCREEN_W - 60)
        y = rng.randint(300, 420)
        h = int(60 + (y - 300) * 0.5)
        col = (56, 44, 62)
        pygame.draw.ellipse(s, col, pygame.Rect(x - h // 5, y - h, h * 2 // 5, h))
        pygame.draw.circle(s, col, (x, y - h), h // 7)


def _bg_bedroom(s):
    """天蓋つきの寝室。ろうそくの あかり。"""
    s.blit(vertical_gradient(SIZE, (58, 38, 48), (34, 22, 30)), (0, 0))
    pygame.draw.rect(s, (72, 48, 46), pygame.Rect(0, 390, C.SCREEN_W, 150))
    pygame.draw.rect(s, (120, 66, 74), pygame.Rect(280, 300, 400, 130), border_radius=6)
    pygame.draw.rect(s, (216, 202, 196), pygame.Rect(300, 286, 360, 40), border_radius=10)
    pygame.draw.rect(s, (236, 228, 222), pygame.Rect(320, 274, 110, 34), border_radius=10)
    for x in (270, 690):                     # 天蓋の柱
        pygame.draw.rect(s, (86, 56, 52), pygame.Rect(x - 8, 90, 16, 320))
    pygame.draw.rect(s, (86, 56, 52), pygame.Rect(262, 84, 436, 16), border_radius=6)
    for i, x in enumerate(range(270, 700, 60)):   # 天蓋の布
        pygame.draw.polygon(s, (150, 76, 92), [(x, 100), (x + 60, 100), (x + 30, 140)])
    for x in (150, 820):                     # ろうそく
        pygame.draw.rect(s, (226, 214, 190), pygame.Rect(x - 6, 300, 12, 70))
        pygame.draw.circle(s, (252, 226, 150), (x, 292), 8)
        g = radial_light(150, (250, 208, 130), strength=80)
        s.blit(g, g.get_rect(center=(x, 292)))


def _bg_corridor_dark(s):
    """まっくらな 学校の 廊下。奥に いくほど くらい。"""
    s.fill((14, 14, 20))
    # 遠近のある廊下
    pygame.draw.polygon(s, (30, 30, 40), [(0, 60), (C.SCREEN_W, 60),
                                          (620, 220), (340, 220)])       # 天井
    pygame.draw.polygon(s, (42, 40, 48), [(0, C.SCREEN_H), (C.SCREEN_W, C.SCREEN_H),
                                          (620, 300), (340, 300)])       # 床
    pygame.draw.polygon(s, (36, 34, 44), [(0, 60), (340, 220), (340, 300), (0, C.SCREEN_H)])
    pygame.draw.polygon(s, (28, 28, 36), [(C.SCREEN_W, 60), (620, 220),
                                          (620, 300), (C.SCREEN_W, C.SCREEN_H)])
    # 教室のドアと窓（左右）
    for i, (x0, x1) in enumerate([(30, 150), (170, 280), (300, 336)]):
        pygame.draw.rect(s, (52, 50, 60), pygame.Rect(x0, 150 + i * 14, x1 - x0, 160 - i * 20))
        pygame.draw.rect(s, (86, 96, 100), pygame.Rect(x0 + 8, 160 + i * 14, (x1 - x0) - 16, 40))
    for i, (x0, x1) in enumerate([(810, 930), (690, 800), (624, 680)]):
        pygame.draw.rect(s, (52, 50, 60), pygame.Rect(x0, 150 + i * 14, x1 - x0, 160 - i * 20))
        pygame.draw.rect(s, (86, 96, 100), pygame.Rect(x0 + 8, 160 + i * 14, (x1 - x0) - 16, 40))
    # 教室から もれる あかり（泣き声の する 部屋）
    pygame.draw.rect(s, (214, 206, 160), pygame.Rect(178, 174, 96, 34))
    pygame.draw.polygon(s, (120, 112, 86), [(170, 208), (280, 208), (330, 330), (150, 330)])
    spill = radial_light(190, (250, 236, 176), strength=54)
    s.blit(spill, spill.get_rect(center=(232, 266)))

    # 奥の非常口の みどりの あかり
    pygame.draw.rect(s, (60, 140, 90), pygame.Rect(452, 214, 56, 20))
    g = radial_light(120, (80, 200, 130), strength=60)
    s.blit(g, g.get_rect(center=(480, 224)))


def _bg_school_out(s):
    """学校の 校舎前。ひるまなのに、いろが うすい。"""
    s.blit(vertical_gradient(SIZE, (150, 172, 196), (208, 206, 198)), (0, 0))
    pygame.draw.rect(s, (188, 184, 176), pygame.Rect(120, 120, 720, 260))
    pygame.draw.rect(s, (160, 156, 148), pygame.Rect(120, 120, 720, 24))
    for y in range(160, 360, 62):
        for x in range(150, 820, 72):
            pygame.draw.rect(s, (206, 222, 230), pygame.Rect(x, y, 52, 42))
            pygame.draw.rect(s, (150, 150, 154), pygame.Rect(x, y, 52, 42), width=2)
    pygame.draw.rect(s, (140, 136, 130), pygame.Rect(430, 300, 100, 80))
    pygame.draw.rect(s, (168, 164, 158), pygame.Rect(0, 380, C.SCREEN_W, 160))
    for x in range(40, C.SCREEN_W, 160):     # 校庭のライン
        pygame.draw.line(s, (196, 192, 186), (x, 440), (x + 90, 440), 3)


def _bg_supermarket(s):
    """スーパーの なか。蛍光灯が しろい。"""
    s.blit(vertical_gradient(SIZE, (232, 234, 232), (206, 208, 206)), (0, 0))
    pygame.draw.rect(s, (188, 186, 184), pygame.Rect(0, 400, C.SCREEN_W, 140))
    for x in range(0, C.SCREEN_W, 68):       # 床タイル
        pygame.draw.line(s, (176, 176, 174), (x, 400), (x - 50, C.SCREEN_H), 2)
    for x in range(60, C.SCREEN_W, 300):     # 蛍光灯
        pygame.draw.rect(s, (250, 250, 244), pygame.Rect(x, 40, 220, 14), border_radius=4)
        g = radial_light(180, (255, 255, 240), strength=60)
        s.blit(g, g.get_rect(center=(x + 110, 54)))
    # 商品棚
    rng = random.Random(63)
    for i, x in enumerate((60, 380)):
        pygame.draw.rect(s, (168, 170, 172), pygame.Rect(x, 190, 220, 210))
        for y in range(206, 390, 44):
            pygame.draw.rect(s, (148, 150, 152), pygame.Rect(x, y + 34, 220, 8))
            for k in range(6):
                col = rng.choice([(206, 128, 108), (150, 176, 140), (222, 208, 150),
                                  (140, 156, 198), (216, 160, 190)])
                pygame.draw.rect(s, col, pygame.Rect(x + 10 + k * 34, y, 26, 34))
    # 冷蔵ケース（牛乳）
    case = pygame.Rect(690, 160, 230, 250)
    pygame.draw.rect(s, (156, 168, 176), case)
    pygame.draw.rect(s, (206, 228, 236), case.inflate(-16, -26))
    for y in range(190, 380, 46):
        pygame.draw.rect(s, (140, 152, 160), pygame.Rect(case.x + 8, y + 36, case.w - 16, 6))
        for k in range(5):
            pygame.draw.rect(s, (246, 246, 250),
                             pygame.Rect(case.x + 18 + k * 40, y, 28, 36))
            pygame.draw.rect(s, (130, 170, 210),
                             pygame.Rect(case.x + 18 + k * 40, y, 28, 10))


def _bg_dream_home(s, blackout=False):
    """夢の家の リビング。あたたかい 食卓。"""
    if blackout:
        s.blit(vertical_gradient(SIZE, (26, 26, 34), (14, 14, 20)), (0, 0))
        wall, floor, table = (38, 36, 44), (30, 28, 34), (44, 38, 38)
    else:
        s.blit(vertical_gradient(SIZE, (188, 162, 132), (150, 124, 100)), (0, 0))
        wall, floor, table = (196, 168, 136), (128, 96, 74), (156, 110, 78)
    pygame.draw.rect(s, floor, pygame.Rect(0, 386, C.SCREEN_W, 154))
    pygame.draw.line(s, (90, 70, 56) if not blackout else (20, 20, 26),
                     (0, 386), (C.SCREEN_W, 386), 3)
    # 窓
    win = pygame.Rect(96, 110, 190, 150)
    pygame.draw.rect(s, (110, 82, 62) if not blackout else (28, 28, 34), win.inflate(16, 16))
    pygame.draw.rect(s, (238, 226, 190) if not blackout else (38, 40, 52), win)
    pygame.draw.line(s, (110, 82, 62) if not blackout else (28, 28, 34),
                     (win.centerx, win.y), (win.centerx, win.bottom), 5)
    # 食卓
    pygame.draw.rect(s, table, pygame.Rect(300, 344, 400, 20), border_radius=4)
    pygame.draw.rect(s, tuple(max(0, c - 20) for c in table), pygame.Rect(330, 364, 16, 80))
    pygame.draw.rect(s, tuple(max(0, c - 20) for c in table), pygame.Rect(654, 364, 16, 80))
    for dx in (-110, 0, 110):                # 食器
        pygame.draw.ellipse(s, (240, 238, 232) if not blackout else (60, 60, 68),
                            pygame.Rect(440 + dx, 330, 70, 20))
    if not blackout:
        pygame.draw.rect(s, (230, 210, 170), pygame.Rect(470, 300, 40, 32), border_radius=4)
        g = radial_light(260, (255, 226, 170), strength=70)
        s.blit(g, g.get_rect(center=(480, 200)))
        pygame.draw.circle(s, (250, 232, 180), (480, 96), 20)      # 照明
        pygame.draw.line(s, (120, 100, 80), (480, 0), (480, 84), 3)
    else:
        pygame.draw.circle(s, (54, 54, 62), (480, 96), 20)
        pygame.draw.line(s, (40, 38, 44), (480, 0), (480, 84), 3)
        # ブレーカーの ある かべ
        pygame.draw.rect(s, (58, 58, 66), pygame.Rect(806, 150, 70, 90))
        pygame.draw.rect(s, (80, 80, 90), pygame.Rect(816, 166, 50, 20))


def _bg_dream_home_dark(s):
    _bg_dream_home(s, blackout=True)


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
    "street_night": _bg_street_night,
    "hoken": _bg_hoken,
    "ball_room": _bg_ball_room,
    "bedroom": _bg_bedroom,
    "corridor_dark": _bg_corridor_dark,
    "school_out": _bg_school_out,
    "supermarket": _bg_supermarket,
    "dream_home": _bg_dream_home,
    "dream_home_dark": _bg_dream_home_dark,
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


class GlitchDriver:
    """ほころびの出かたを管理する。

    ずっと画面が揺れていると見ていて疲れるので、
    ふだんは何も起きず、ときどき短く走る——という出しかたにする。
      base   … その場面の不安定さ（0〜5）。大きいほど発作の間隔が短い
      hit()  … その瞬間だけ強く走らせる（扉が変わる、悲鳴、など）
    """

    def __init__(self, base: float = 0.0):
        self.rng = random.Random()
        self.base = 0.0
        self.level = 0.0
        self.timer = 0.0            # 発作の残り時間
        self.wait = 0.0             # 次の発作まで
        self.set_base(base)

    def set_base(self, base: float):
        self.base = max(0.0, float(base))
        self.wait = self._interval() * self.rng.uniform(0.2, 0.7)

    def _interval(self) -> float:
        if self.base <= 0:
            return 999.0
        return max(1.1, 6.2 - self.base * 1.0)

    def hit(self, power: float = 2.5, duration: float = 0.3):
        self.level = max(self.level, power)
        self.timer = max(self.timer, duration)

    def update(self, dt: float):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.level = 0.0
                self.wait = self._interval() * self.rng.uniform(0.7, 1.5)
        elif self.base > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.level = self.base * self.rng.uniform(0.7, 1.15)
                self.timer = min(0.42, 0.10 + self.base * 0.055)

    @property
    def current(self) -> float:
        return self.level if self.timer > 0 else 0.0

    def draw(self, surf, t):
        level = self.current
        if level > 0:
            glitch(surf, level, t)


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
        "street_night": ("dust", (170, 176, 196)),
        "hoken": ("light", (255, 252, 240)),
        "ball_room": ("light", (250, 226, 170)),
        "bedroom": ("light", (250, 210, 150)),
        "corridor_dark": ("dust", (90, 96, 110)),
        "school_out": ("light", (255, 250, 236)),
        "supermarket": ("dust", (230, 232, 230)),
        "dream_home": ("dust", (250, 226, 180)),
        "dream_home_dark": ("dust", (90, 90, 106)),
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


def _draw_girl(surf, cx, base_y, h, t):
    """げんじつの 女子。セーラー服。"""
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


def _draw_princess(surf, cx, base_y, h, t):
    """国王の むすめ。ドレスと ティアラ。"""
    glow = radial_light(int(h * 0.5), (250, 220, 240), strength=48)
    surf.blit(glow, glow.get_rect(center=(cx, base_y - int(h * 0.5))))
    head_y, head_r = _body(surf, cx, base_y, h, (236, 222, 236), (244, 222, 208),
                           (222, 196, 150), "long", arm_col=(232, 216, 232))
    pygame.draw.polygon(surf, (222, 200, 232), [      # ドレスの すそ
        (cx - int(h * 0.26), base_y), (cx + int(h * 0.26), base_y),
        (cx + int(h * 0.11), base_y - int(h * 0.34)),
        (cx - int(h * 0.11), base_y - int(h * 0.34))])
    pygame.draw.rect(surf, (200, 168, 210), pygame.Rect(
        cx - int(h * 0.12), base_y - int(h * 0.37), int(h * 0.24), int(h * 0.035)))
    for i, dx in enumerate((-10, 0, 10)):             # ティアラ
        pygame.draw.polygon(surf, (250, 226, 140), [
            (cx + dx - 6, head_y - int(head_r * 1.0)),
            (cx + dx + 6, head_y - int(head_r * 1.0)),
            (cx + dx, head_y - int(head_r * 1.34))])


def _draw_heroine_b(surf, cx, base_y, h, t):
    """ヒロインその二。"""
    _body(surf, cx, base_y, h, (222, 236, 234), (240, 216, 202), (120, 170, 186), "long",
          arm_col=(214, 230, 228))
    pygame.draw.polygon(surf, (206, 230, 228), [
        (cx - int(h * 0.19), base_y), (cx + int(h * 0.19), base_y),
        (cx + int(h * 0.11), base_y - int(h * 0.30)),
        (cx - int(h * 0.11), base_y - int(h * 0.30))])


def _draw_heroine_c(surf, cx, base_y, h, t):
    """ヒロインその三。"""
    _body(surf, cx, base_y, h, (240, 228, 214), (238, 214, 198), (96, 78, 70), "short",
          arm_col=(232, 220, 206))
    pygame.draw.polygon(surf, (228, 214, 198), [
        (cx - int(h * 0.19), base_y), (cx + int(h * 0.19), base_y),
        (cx + int(h * 0.11), base_y - int(h * 0.30)),
        (cx - int(h * 0.11), base_y - int(h * 0.30))])
    pygame.draw.rect(surf, (200, 150, 120), pygame.Rect(
        cx - int(h * 0.12), base_y - int(h * 0.33), int(h * 0.24), int(h * 0.03)))


def _draw_mother(surf, cx, base_y, h, t):
    """やさしい母。"""
    _body(surf, cx, base_y, h, (196, 170, 156), (226, 200, 186), (104, 82, 72), "long",
          arm_col=(186, 160, 148))
    pygame.draw.polygon(surf, (176, 150, 140), [      # エプロン
        (cx - int(h * 0.10), base_y - int(h * 0.56)), (cx + int(h * 0.10), base_y - int(h * 0.56)),
        (cx + int(h * 0.13), base_y - int(h * 0.04)), (cx - int(h * 0.13), base_y - int(h * 0.04))])


def _draw_king(surf, cx, base_y, h, t):
    """国王。"""
    head_y, head_r = _body(surf, cx, base_y, h, (132, 64, 74), (214, 190, 174),
                           (222, 218, 212), "short", arm_col=(118, 56, 66))
    pygame.draw.polygon(surf, (150, 74, 84), [
        (cx - int(h * 0.22), base_y), (cx + int(h * 0.22), base_y),
        (cx + int(h * 0.12), base_y - int(h * 0.40)),
        (cx - int(h * 0.12), base_y - int(h * 0.40))])
    pygame.draw.ellipse(surf, (226, 222, 216), pygame.Rect(   # ひげ
        cx - int(head_r * 0.8), head_y + int(head_r * 0.4),
        int(head_r * 1.6), int(head_r * 1.5)))
    crown_y = head_y - int(head_r * 1.05)
    pygame.draw.rect(surf, (244, 208, 110),
                     pygame.Rect(cx - head_r, crown_y, head_r * 2, int(head_r * 0.4)))
    for dx in (-head_r + 4, 0, head_r - 4):
        pygame.draw.polygon(surf, (244, 208, 110), [
            (cx + dx - 5, crown_y), (cx + dx + 5, crown_y), (cx + dx, crown_y - 12)])


CHARACTERS = {
    "yuusha": _draw_yuusha,
    "boku": _draw_boku,
    "riina": _draw_riina,
    "girl": _draw_girl,
    "father": _draw_father,
    "nurse": _draw_nurse,
    "classmate": _draw_classmate,
    "bug": _draw_bug,
    "princess": _draw_princess,
    "heroine_b": _draw_heroine_b,
    "heroine_c": _draw_heroine_c,
    "mother": _draw_mother,
    "king": _draw_king,
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
