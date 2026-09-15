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


def _advance(scene, frames=1, dt=1 / 60):
    for _ in range(frames):
        scene.time += dt
        scene.update(dt)


def _save(app, scene, name, frames=1):
    _advance(scene, frames)
    app.canvas.fill((0, 0, 0))
    scene.draw(app.canvas)
    path = os.path.join(OUT, name)
    pygame.image.save(app.canvas, path)
    print("saved:", os.path.relpath(path))


def main():
    os.makedirs(OUT, exist_ok=True)
    from boku.app import App
    from boku.scenes.battle import BattleScene
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

    # 第一章：王都（ほころびを探す）
    story = StoryScene(app)
    app.push(story)
    story.fader.set(0)
    for _ in range(84):
        if story.mode == "message":
            story.msg.skip()
            story._advance()
        elif story.mode == "run":
            story.step()
        else:
            break
    _save(app, story, "02_story_castle.png", 30)

    story.st.bg = "capital_day"
    story.bg.change("capital_day", instant=True)
    story.mode = "message"
    story.st.characters = [["yuusha", "left"], ["riina", "right"]]
    story.st.glitch = 1.6
    story.msg.set_text("リィナ：やっぱり わたしの えらんだ ひとは ちが ぁ ぁ", "リィナ")
    story.msg.skip()
    _save(app, story, "03_glitch.png", 30)

    story.st.bg = "capital_broken"
    story.bg.change("capital_broken", instant=True)
    story.mode = "message"
    story.st.characters = [["bug", "center"]]
    story.st.glitch = 4.2
    story.msg.set_text("ほころび：目を 覚ますな！！", "ほころび")
    story.msg.skip()
    _save(app, story, "04_broken.png", 20)

    story.st.bg = "room_pc"
    story.bg.change("room_pc", instant=True)
    story.mode = "message"
    story.st.characters = [["boku", "right"]]
    story.st.glitch = 0.0
    story.st.flags["hokorobi"] = 4
    story.st.chapter = "第二章"
    story.msg.set_text("モニタには、かきかけの コードが ひらいたまま。", "")
    story.msg.skip()
    _save(app, story, "05_room.png", 20)
    app.pop()

    explore = ExploreScene(app, "capital_square")
    app.push(explore)
    explore.fader.set(0)
    explore.seen = {"fountain", "npc"}
    _save(app, explore, "06_explore.png", 40)
    app.pop()

    route = RouteScene(app, "2")
    app.push(route)
    route.fader.set(0)
    route.phase = "play"
    route.x = 470.0
    route.gauge = 58.0
    _save(app, route, "07_route.png", 44)
    app.pop()

    app.state.bg = "void"
    battle = BattleScene(app, "yuusha")
    app.push(battle)
    battle.fader.set(0)
    battle.mode = "command"
    battle.moya = 62
    battle.courage = 24
    battle.opened = True
    _save(app, battle, "08_battle.png", 30)
    app.pop()

    ending = EndingScene(app, "jibun")
    app.push(ending)
    ending.fader.set(0)
    _save(app, ending, "09_ending_card.png", 30)
    ending.phase = "epilogue"
    ending.line_index = 8
    _save(app, ending, "10_ending_text.png", 20)
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
