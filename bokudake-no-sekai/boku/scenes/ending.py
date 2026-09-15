# -*- coding: utf-8 -*-
"""エンディングとスタッフロール。"""

from __future__ import annotations

import math

import pygame

from .. import config as C
from .. import save as save_mod
from ..app import CONFIRM_KEYS, Scene
from ..art import Background, draw_character, glitch as draw_glitch
from ..fonts import get_font
from ..ui import Fader, draw_text_center, draw_text_shadow, radial_light

ENDINGS = {
    # 第一章で「わすれる」を選んだとき
    "wasureru": {
        "name": "しあわせなゆうしゃ",
        "label": "ENDING 1",
        "bg": "capital_day",
        "chara": ("yuusha", 0.5),
        "color": C.GOLD,
        "glitch": 0.0,
        "epilogue": [
            "ぼくは、ほころびから 目を そらした。",
            "そらした とたん、それは はじめから なかったように うすれていった。",
            "",
            "まちは きょうも ぼくを たたえ、リィナは きょうも ぼくを ほめる。",
            "パン屋の おやじは、きょうも おなじ せりふで わらう。",
            "ふんすいは、きっちり 四びょうで おなじ しぶきを あげる。",
            "",
            "なにも こまらない。なにも かわらない。",
            "きずつくことは、もう ぜったいに ない。",
            "",
            "── ほころびは どんどん うすれていき、",
            "　　勇者は いつまでも しあわせに くらしました。",
            "",
            "　　　　いつまでも。やすらかに。",
        ],
    },

    # 第二章：正気がゼロになったとき
    "hodou": {
        "name": "しろい おと",
        "label": "ENDING 2",
        "bg": "outside_night",
        "chara": ("boku", 0.5),
        "color": C.DEEP_RED,
        "glitch": 2.2,
        "epilogue": [
            "あたまの なかが、しろい おとで いっぱいに なった。",
            "きづいたら、ぼくは 道の まんなかで さけんでいた。",
            "",
            "ことばでは なかった。ただの おとだった。",
            "窓が つぎつぎ あかるくなって、カーテンが ゆれて、また とじた。",
            "",
            "父さんが 家から 出てきて、ぼくを 見た。",
            "それから、けいたいを ひらいて、みじかく なにか 話した。",
            "父さん：「……はい。うちの 息子です。おねがいします」",
            "",
            "赤い ひかりが、道の かべを ぐるぐる まわっていた。",
            "近所の人たちは、こんども 出てこなかった。カーテンの うしろにいた。",
            "",
            "── この後、彼は 問題を 起こし、",
            "　　警察に 補導されたのち、入院する 事になる。",
        ],
    },

    # 第三章：娘の誘いを受けたとき
    "mitasareta": {
        "name": "みたされたせかい",
        "label": "ENDING 3",
        "bg": "bedroom",
        "chara": ("princess", 0.5),
        "color": C.ROSE,
        "glitch": 0.8,
        "epilogue": [
            "ぼくは、さしだされた 手を とった。",
            "ろうそくの ひかりが、ひとつずつ きえていく。",
            "",
            "ドアの むこうの 廊下の ことは、もう かんがえなかった。",
            "泣いていた 声の ことも、かんがえなかった。",
            "かんがえないと きめれば、この 世界では ほんとうに なかったことに なる。",
            "",
            "── この後、俺たちは 何度も 愛し合った。",
            "　　人々は みな、その後 夫婦と なった 俺たちを 祝福した。",
            "",
            "　　何もかも 満たされた 世界。",
            "　　欲しかったものを 独占できる 世界。",
            "",
            "　　　　ただ一点、彼女の 眼に 光が 無かったことを 除いて。",
        ],
    },

    # 第三章の終わり（物語はここから続く）
    "tsuzuku": {
        "name": "つづく",
        "label": "第三章 おわり",
        "bg": "room_dark",
        "chara": ("boku", 0.5),
        "color": C.MIST,
        "glitch": 0.4,
        "epilogue": [
            "じぶんの 悲鳴で、目が さめた。",
            "",
            "いつもの、くらい へや。",
            "モニタだけが つけっぱなしで、青白く ひかっている。",
            "ゆかには、ゆうべ 買ってきた 牛乳の ふくろ。",
            "",
            "ゆめの 中の 父さんの こえと、ほんものの 父さんの こえが、",
            "おなじ ことを 言っていた。",
            "",
            "「牛乳を 買ってきてくれ」",
            "「保健室に プリントを 出してきてくれ」",
            "",
            "ぼくは、まだ どちらの 世界にも 立っていない。",
        ],
        "credits": [
            ("", C.TITLE),
            ("", ""),
            ("テーマ", "自分の生きる理由は自分で決める"),
            ("", ""),
            ("ここまでのプレイ、ありがとうございました", "物語は、まだ 途中です"),
            ("", ""),
            ("", "― つづく ―"),
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
        "epilogue": ["ものがたりは、ここで とまっている。"],
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
    ("そして", "ここまで つきあってくれた あなた"),
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
        if self.data.get("glitch"):
            draw_glitch(surf, self.data["glitch"], self.time)

        if self.phase == "card":
            self._draw_card(surf)
        elif self.phase == "epilogue":
            self._draw_epilogue(surf)
        else:
            self._draw_credits(surf)

        if self.skip_hint > 0 and self.phase != "done":
            alpha = int(140 * min(1.0, self.skip_hint / 1.5))
            img = get_font(16).render("Z / クリックで すすむ", True, C.MIST)
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
            draw_text_center(surf, "Z / クリックで タイトルへ", get_font(20), C.GOLD,
                             (C.SCREEN_W // 2, C.SCREEN_H - 70))
