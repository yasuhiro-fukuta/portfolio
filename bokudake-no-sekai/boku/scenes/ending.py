# -*- coding: utf-8 -*-
"""エンディングとスタッフロール。"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from .. import save as save_mod
from ..app import CONFIRM_KEYS, Scene
from ..art import Background, GlitchDriver, draw_character
from ..fonts import get_font
from ..ui import Fader, draw_text_center, draw_text_shadow, radial_light

ENDINGS = {
    # 第一章で「忘れる」を選んだとき
    "wasureru": {
        "name": "幸せな勇者",
        "label": "ENDING 1",
        "bg": "capital_day",
        "chara": ("yuusha", 0.5),
        "color": C.GOLD,
        "glitch": 0.0,
        "epilogue": [
            "ぼくは、ほころびから目をそらした。",
            "そらしたとたん、それははじめから無かったように薄れていった。",
            "",
            "町は今日もぼくを讃え、リィナは今日もぼくを褒める。",
            "パン屋のおやじは、今日も同じ台詞で笑う。",
            "噴水は、きっちり四秒で同じしぶきを上げる。",
            "",
            "何も困らない。何も変わらない。",
            "傷つくことは、もう絶対にない。",
            "",
            "── ほころびはどんどん薄れていき、",
            "　　勇者はいつまでも幸せに暮らしました。",
            "",
            "　　　　いつまでも。安らかに。",
        ],
    },

    # 第二章：正気がゼロになったとき
    "hodou": {
        "name": "白い音",
        "label": "ENDING 2",
        "bg": "outside_night",
        "chara": ("boku", 0.5),
        "color": C.DEEP_RED,
        "glitch": 1.6,
        "epilogue": [
            "頭の中が、白い音でいっぱいになった。",
            "気づいたら、ぼくは道の真ん中で叫んでいた。",
            "",
            "言葉ではなかった。ただの音だった。",
            "窓が次々明るくなって、カーテンが揺れて、また閉じた。",
            "",
            "父さんが家から出てきて、ぼくを見た。",
            "それから、携帯を開いて、短く何か話した。",
            "父さん：「……はい。うちの息子です。お願いします」",
            "",
            "赤い光が、道の壁をぐるぐる回っていた。",
            "近所の人たちは、今度も出てこなかった。カーテンの後ろにいた。",
            "",
            "── この後、彼は問題を起こし、",
            "　　警察に補導されたのち、入院する事になる。",
        ],
    },

    # 第三章：娘の誘いを受けたとき
    "mitasareta": {
        "name": "満たされた世界",
        "label": "ENDING 3",
        "bg": "bedroom",
        "chara": ("princess", 0.5),
        "color": C.ROSE,
        "glitch": 0.6,
        "epilogue": [
            "ぼくは、差し出された手を取った。",
            "蝋燭の光が、ひとつずつ消えていく。",
            "",
            "ドアの向こうの廊下のことは、もう考えなかった。",
            "泣いていた声のことも、考えなかった。",
            "考えないと決めれば、この世界では本当に無かったことになる。",
            "",
            "── この後、俺たちは何度も愛し合った。",
            "　　人々はみな、その後夫婦となった俺たちを祝福した。",
            "",
            "　　何もかも満たされた世界。",
            "　　欲しかったものを独占できる世界。",
            "",
            "　　　　ただ一点、彼女の眼に光が無かったことを除いて。",
        ],
    },

    # 第七章：退院のあと（真エンディング）
    "kimeru": {
        "name": "俺が決める",
        "label": "TRUE ENDING",
        "bg": "room_clean",
        "chara": ("boku_clean", 0.34),
        "color": C.GOLD,
        "glitch": 0.0,
        "epilogue": [
            "バイトは、泊まり込みの現場だった。",
            "朝から晩まで、他人の書いたコードの、他人の決めた仕様を直す。",
            "俺の理想なんて、どこにも入る余地がない。",
            "",
            "それでも、直したものが動いたとき、誰かが「助かった」と言った。",
            "俺が作ったものが、俺以外の場所で動いている。",
            "はじめてだった。",
            "",
            "夜、寮の机で、あの病院で書いた紙の束を開く。",
            "最後のページの隅には、「100」と書いてあった。",
            "それだけ確かめて、閉じた。",
            "",
            "あの台詞がこの中にあるのかどうかは、探していない。",
            "探さないと決めた。",
            "",
            "書いてあったとしても、なかったとしても、",
            "俺があれを聞いたことは、変わらないからだ。",
            "",
            "続きを書く。今度は、俺だけが無敵な話じゃないやつを。",
            "面白いかどうかは、まだわからない。",
            "",
            "それでも、明日起きる理由には足りる。",
        ],
    },

    # 保険（シナリオ終端に来たとき）
    "stay": {
        "name": "ぼくだけのせかい",
        "label": "ENDING",
        "bg": "room_pc",
        "chara": ("boku", 0.5),
        "color": C.MIST,
        "glitch": 0.0,
        "epilogue": ["物語は、ここで止まっている。"],
    },
}

CREDITS = [
    ("", C.TITLE),
    ("", ""),
    ("テーマ", "自分の生きる理由は自分で決める"),
    ("", ""),
    ("シナリオ・プログラム", "Python 3 / pygame"),
    ("グラフィック", "すべて図形で描画（画像素材なし）"),
    ("", ""),
    ("そして", "ここまで付き合ってくれたあなた"),
    ("", ""),
    ("", "― おわり ―"),
]


class EndingScene(Scene):
    def __init__(self, app, ending_id: str):
        super().__init__(app)
        self.st = app.state
        self.data = ENDINGS.get(ending_id, ENDINGS["stay"])
        self.ending_id = ending_id if ending_id in ENDINGS else "stay"
        self.bg = Background(self.data["bg"])
        self.fader = Fader()
        self.glitch = GlitchDriver(self.data.get("glitch", 0.0))
        self.fader.set(255)
        self.fader.to(0, 1.6)
        self.phase = "card"          # card / epilogue / credits / done
        self.timer = 4.2
        self.scroll = 0.0
        self.line_index = 0
        self.skip_hint = 4.0
        self.credits = self.data.get("credits", CREDITS)
        if ending_id not in self.st.endings_seen:
            self.st.endings_seen.append(ending_id)
        save_mod.save(0, self.st, f"エンディング：{self.data['name']}")

    # ------------------------------------------------------------------
    def handle_event(self, event):
        pressed = (event.type == pygame.KEYDOWN and event.key in CONFIRM_KEYS) or \
                  (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        if not pressed:
            return
        if self.phase == "card":
            self.timer = min(self.timer, 0.3)
        elif self.phase == "epilogue":
            if self.line_index < len(self.data["epilogue"]):
                self.line_index = len(self.data["epilogue"])
            else:
                self._to_credits()
        elif self.phase == "credits":
            self.scroll += 260
        elif self.phase == "done":
            self._back_to_title()

    def _to_credits(self):
        self.phase = "credits"
        self.scroll = 0.0

    def _back_to_title(self):
        from .title import TitleScene
        self.app.replace(TitleScene(self.app))

    # ------------------------------------------------------------------
    def update(self, dt):
        self.bg.update(dt, self.time)
        self.fader.update(dt)
        self.glitch.update(dt)
        self.skip_hint = max(0.0, self.skip_hint - dt)

        if self.phase == "card":
            self.timer -= dt
            if self.timer <= 0:
                self.phase = "epilogue"
                self.timer = 0.0
        elif self.phase == "epilogue":
            self.timer += dt
            want = int(self.timer / 1.5)
            self.line_index = min(len(self.data["epilogue"]), max(self.line_index, want))
            if self.line_index >= len(self.data["epilogue"]) and self.timer > \
                    len(self.data["epilogue"]) * 1.5 + 3.0:
                self._to_credits()
        elif self.phase == "credits":
            self.scroll += dt * 52
            if self.scroll > len(self.credits) * 52 + C.SCREEN_H:
                self.phase = "done"

    # ------------------------------------------------------------------
    def draw(self, surf):
        self.bg.draw(surf, self.time)
        dim = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        dim.fill((6, 8, 16, 118 if self.phase != "card" else 90))
        surf.blit(dim, (0, 0))

        cid, pos = self.data["chara"]
        draw_character(surf, cid, pos, self.time, alpha=170, scale=0.85)
        self.glitch.draw(surf, self.time)

        if self.phase == "card":
            self._draw_card(surf)
        elif self.phase == "epilogue":
            self._draw_epilogue(surf)
        else:
            self._draw_credits(surf)

        if self.skip_hint > 0 and self.phase != "done":
            alpha = int(140 * min(1.0, self.skip_hint / 1.5))
            img = get_font(16).render("Z / クリックで進む", True, C.MIST)
            img.set_alpha(alpha)
            surf.blit(img, (C.SCREEN_W - 220, C.SCREEN_H - 30))

        self.fader.draw(surf)

    def _draw_card(self, surf):
        glow = radial_light(280, self.data["color"], strength=60)
        surf.blit(glow, glow.get_rect(center=(C.SCREEN_W // 2, C.SCREEN_H // 2)))
        draw_text_center(surf, self.data["label"], get_font(20), C.MIST,
                         (C.SCREEN_W // 2, C.SCREEN_H // 2 - 56))
        draw_text_center(surf, self.data["name"], get_font(46, bold=True),
                         self.data["color"], (C.SCREEN_W // 2, C.SCREEN_H // 2 + 4))
        w = 190 + int(math.sin(self.time * 1.4) * 10)
        pygame.draw.line(surf, C.MIST, (C.SCREEN_W // 2 - w, C.SCREEN_H // 2 + 44),
                         (C.SCREEN_W // 2 + w, C.SCREEN_H // 2 + 44), 1)

    def _draw_epilogue(self, surf):
        font = get_font(23)
        lines = self.data["epilogue"][:self.line_index]
        visible = lines[-9:]
        y = C.SCREEN_H // 2 - len(visible) * (font.get_height() + 10) // 2
        for i, line in enumerate(visible):
            if not line:
                y += font.get_height() + 10
                continue
            age = len(visible) - i
            alpha = 255 if age <= 6 else max(60, 255 - (age - 6) * 60)
            draw_text_center(surf, line, font, C.PAPER, (C.SCREEN_W // 2, y), alpha=alpha)
            y += font.get_height() + 10
        draw_text_shadow(surf, self.data["name"], get_font(18), self.data["color"],
                         (34, 28), alpha=150)

    def _draw_credits(self, surf):
        label_font = get_font(17)
        value_font = get_font(24, bold=True)
        y = C.SCREEN_H - self.scroll
        for label, value in self.credits:
            if -60 < y < C.SCREEN_H + 60:
                if label:
                    draw_text_center(surf, label, label_font, C.MIST,
                                     (C.SCREEN_W // 2, y - 18))
                if value:
                    draw_text_center(surf, value, value_font, C.PAPER,
                                     (C.SCREEN_W // 2, y + 8))
            y += 92

        if self.phase == "done":
            draw_text_center(surf, "Z / クリックでタイトルへ", get_font(20), C.GOLD,
                             (C.SCREEN_W // 2, C.SCREEN_H - 70))
