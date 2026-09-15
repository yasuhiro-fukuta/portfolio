#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主要な画面を PNG に書き出す（見た目の確認・ポートフォリオ用）。"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")


def _save(app, scene, name, frames=1, dt=1 / 60):
    for _ in range(frames):
        scene.time += dt
        scene.update(dt)
    app.canvas.fill((0, 0, 0))
    scene.draw(app.canvas)
    pygame.image.save(app.canvas, os.path.join(OUT, name))
    print("saved:", name)


def _story_shot(app, story, name, bg, chars, text, speaker="", glitch=0.0, chapter=""):
    story.mode = "message"
    story.st.bg = bg
    story.bg.change(bg, instant=True)
    story.st.characters = [list(c) for c in chars]
    story.st.glitch = glitch
    story.glitch.set_base(glitch)
    story.glitch.level = 0.0
    story.glitch.timer = 0.0
    if glitch:
        story.glitch.hit(glitch, 9.0)          # 静止画なので発作を止めておく
    if chapter:
        story.st.chapter = chapter
    story.card = None
    story.msg.set_text(text, speaker)
    story.msg.skip()
    _save(app, story, name, 24)


def main():
    os.makedirs(OUT, exist_ok=True)
    from boku.app import App
    from boku.scenes.ending import EndingScene
    from boku.scenes.explore import ExploreScene
    from boku.scenes.route import RouteScene
    from boku.scenes.story import StoryScene
    from boku.scenes.title import TitleScene

    app = App(headless=True)

    title = TitleScene(app)
    app.push(title)
    title.fader.set(0)
    _save(app, title, "01_title.png", 60)
    app.pop()

    story = StoryScene(app)
    app.push(story)
    story.fader.set(0)
    story.hint_time = 0.0

    _story_shot(app, story, "02_castle.png", "castle_hall",
                [["yuusha", "center"], ["king", "right"]],
                "よくぞ参られた、我が国の英雄よ。", "国王", chapter="第一章")
    _story_shot(app, story, "03_glitch.png", "capital_day",
                [["yuusha", "left"], ["riina", "right"]],
                "やっぱり私の選んだ人は違ぁ ぁ", "リィナ", glitch=2.6)
    _story_shot(app, story, "04_broken.png", "capital_broken", [["bug", "center"]],
                "目を覚ますな！！", "ほころび", glitch=4.4)
    story.st.flags["shouki"] = 46
    _story_shot(app, story, "05_father.png", "outside_night", [["father", "right"]],
                "学校も行かない、働きもしないなら、それくらいの役に立て。", "父さん",
                chapter="第二章")
    _story_shot(app, story, "06_ballroom.png", "ball_room", [["princess", "center"]],
                "……こんな席、抜け出してしまいませんか。", "娘", chapter="第三章")
    _story_shot(app, story, "07_corridor.png", "corridor_dark", [],
                "まじでキモすぎるよね。あの顔で■■に告白とか、しかもみんな見てる前で。",
                "女子C", glitch=2.2)
    _story_shot(app, story, "08_bug_parents.png", "dream_home_dark",
                [["mother", "right"], ["father", "left"]],
                "あなたは、そのままでいいのよ。あなたは、そのままでいいのよ。", "母さん",
                glitch=5.0)
    _story_shot(app, story, "16_living.png", "living_real",
                [["father", "right"], ["mother", "left"]],
                "いつまでこうしてるつもりだ。答えろ。", "父さん", chapter="第四章")
    _story_shot(app, story, "17_office.png", "office", [["clerk", "right"]],
                "中学生の方を、こちらで直接お預かりすることはできません。", "職員")
    _story_shot(app, story, "18_park.png", "park_red",
                [["police", "right"], ["clerk", "left"]],
                "ぼくは、親から虐待を受けています！", "ぼく", glitch=1.6)
    _story_shot(app, story, "19_counsel.png", "counsel", [["doctor", "right"]],
                "統合失調症の併発も疑っています。しばらく、ここで休みましょう。", "医師",
                chapter="第五章")
    _story_shot(app, story, "20_knife.png", "ward_night", [["boku_knife", "center"]],
                "見てるんだろ。そこで。", "ぼく", glitch=2.6)
    _story_shot(app, story, "21_village.png", "village", [["mura", "center"]],
                "わたしが、知りたいからです。", "少女", chapter="第六章")
    _story_shot(app, story, "22_edge.png", "village_edge", [["mura", "right"]],
                "たとえ作られた世界だとしても、私が好きな人は私が決めます。", "少女",
                glitch=1.4)
    _story_shot(app, story, "23_hospital_out.png", "hospital_out",
                [["father", "right"], ["mother", "left"]],
                "俺、働くよ。", "ぼく", chapter="第七章")
    _story_shot(app, story, "24_room_clean.png", "room_clean", [["boku_clean", "center"]],
                "俺が生きる理由は、俺が作る。", "ぼく")
    app.pop()

    explore = ExploreScene(app, "capital_square")
    app.push(explore)
    explore.fader.set(0)
    explore.seen = {"fountain", "npc"}
    _save(app, explore, "09_explore.png", 40)
    app.pop()

    shop = ExploreScene(app, "supermarket")
    app.push(shop)
    shop.fader.set(0)
    shop.seen = {"magazine"}
    shop.index = 0
    _save(app, shop, "10_supermarket.png", 40)
    app.pop()

    app.state.set("shouki", 54)
    route = RouteScene(app, "super")
    app.push(route)
    route.fader.set(0)
    route.phase = "play"
    route.x = 470.0
    _save(app, route, "11_errand.png", 44)
    app.pop()

    app.state.set("shouki", 28)
    chase = RouteScene(app, "chase")
    app.push(chase)
    chase.fader.set(0)
    chase.phase = "play"
    chase.x = 520.0
    for p in chase.pursuers:
        p["x"] += 620
    _save(app, chase, "12_chase.png", 20)
    app.pop()

    from boku.scenes.console import ConsoleScene
    con = ConsoleScene(app, "ward_pc")
    app.push(con)
    con.fader.set(0)
    for _ in range(4000):                   # dir の出力まで進める
        con.time += 1 / 60
        con.update(1 / 60)
        if con.say_hold > 0:
            con._skip()
        if any("個のディレクトリ" in ln for ln, _c in con.lines):
            break
    _save(app, con, "25_console.png", 10)
    app.pop()

    for eid, tag in (("hodou", "13_ending2"), ("mitasareta", "14_ending3"),
                     ("kimeru", "15_kimeru")):
        ending = EndingScene(app, eid)
        app.push(ending)
        ending.fader.set(0)
        _save(app, ending, f"{tag}_card.png", 30)
        ending.phase = "epilogue"
        ending.line_index = 9
        _save(app, ending, f"{tag}_text.png", 20)
        app.pop()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
