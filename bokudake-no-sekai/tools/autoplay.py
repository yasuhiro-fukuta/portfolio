#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ヘッドレスで最後まで自動プレイして、落ちないことと到達エンディングを確かめる。

    python3 tools/autoplay.py                 選択肢はすべて先頭を選ぶ
    python3 tools/autoplay.py --choices 1,1,0 選択肢を順に指定（足りない分は先頭）
    python3 tools/autoplay.py --seed 3 --random ランダムに選ぶ
    python3 tools/autoplay.py --all           代表的なルートをまとめて確認
"""

from __future__ import annotations

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

DT = 1.0 / 60.0


class _FakeKeys:
    """通学路シーンを進めるため「→ を押しっぱなし」にする。"""

    def __init__(self, held=(pygame.K_RIGHT,)):
        self.held = held

    def __getitem__(self, key):
        return key in self.held


def play(choices=None, seed=0, max_frames=200000, verbose=False, route_policy="walk"):
    from boku.app import App
    from boku.scenes.ending import EndingScene
    from boku.scenes.explore import ExploreScene
    from boku.scenes.route import RouteScene
    from boku.scenes.story import StoryScene
    from boku.scenes.title import TitleScene

    pygame.key.get_pressed = lambda: _FakeKeys()          # 通学路用
    pygame.key.get_mods = lambda: 0
    pygame.mouse.get_pressed = lambda *a, **k: (0, 0, 0)

    rng = random.Random(seed)
    choices = list(choices or [])
    app = App(headless=True)
    app.push(TitleScene(app))

    log = []
    choice_i = 0
    frames = 0

    while frames < max_frames:
        scene = app.scene
        if scene is None:
            break
        kind = type(scene).__name__

        if isinstance(scene, TitleScene):
            scene.menu.index = 0
            scene._select(0)

        elif isinstance(scene, StoryScene):
            if scene.mode == "choice" and scene.menu:
                if choice_i < len(choices):
                    pick = choices[choice_i]
                else:
                    pick = rng.randrange(len(scene.menu.options)) if choices == "random" else 0
                pick = min(pick, len(scene.menu.options) - 1)
                scene.menu.index = pick
                log.append(f"選択 {choice_i}: {scene.menu.options[pick]}")
                choice_i += 1
                scene._advance()
            elif scene.mode in ("message", "caption", "chapter"):
                scene.msg.skip()
                scene._advance()
            elif scene.mode == "run":
                scene.step()

        elif isinstance(scene, ExploreScene):
            if scene.mode == "read":
                scene.msg.skip()
                scene._advance()
            else:
                unseen = [i for i, it in enumerate(scene.items)
                          if it["id"] != "__exit__" and it["id"] not in scene.seen]
                scene.index = unseen[0] if unseen else len(scene.items) - 1
                scene._select()

        elif isinstance(scene, RouteScene):
            if scene.phase == "ready":
                scene.phase = "play"
                if route_policy == "caught" or (
                        route_policy == "caught_chase" and scene.stage_id == "chase"):
                    scene.st.set("shouki", 0)      # わざと正気を削りきる
                    scene.phase = "broken"
            elif scene.phase in ("done", "broken"):
                log.append(f"通学路 {scene.stage_id}: {scene.phase}")
                scene._finish()

        elif isinstance(scene, EndingScene):
            log.append(f"エンディング: {scene.ending_id}（{scene.data['name']}）")
            if verbose:
                print("\n".join(log))
            pygame.quit()
            return scene.ending_id, log, frames

        scene.time += DT
        scene.update(DT)
        app.canvas.fill((0, 0, 0))
        scene.draw(app.canvas)
        frames += 1

    pygame.quit()
    raise RuntimeError(f"エンディングに到達しませんでした（{frames} フレーム, 最後: {kind}）")


# （名前, 選択肢, 外出方針, 期待するエンディング）
ROUTES = [
    ("第一章で わすれる", [0, 0], "walk", "wasureru"),
    ("正気が もたなかった", [1, 1, 0], "caught", "hodou"),
    ("娘の 手を とる", [1, 1, 0, 0, 0, 0], "walk", "mitasareta"),
    ("逃げる（第三章の さいご）", [1, 1, 0, 0, 0, 1], "walk", "tsuzuku"),
    ("スーパーから まわる", [1, 1, 1, 1, 0, 1], "walk", "tsuzuku"),
    ("夢の中で つかまる", [1, 1, 0, 0, 0, 1], "caught_chase", "tsuzuku"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--choices", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--route-policy", default="walk",
                    choices=["walk", "caught", "caught_chase"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if args.all:
        # pygame を同一プロセスで何度も初期化し直すと不安定なので、
        # ルートごとに別プロセスで実行する。
        import subprocess
        ok = True
        for name, ch, route_policy, expected in ROUTES:
            cmd = [sys.executable, os.path.abspath(__file__),
                   "--choices", ",".join(str(c) for c in ch),
                   "--route-policy", route_policy]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            tail = [ln for ln in proc.stdout.splitlines() if ln.startswith("到達")]
            got = tail[-1].split()[1] if tail else ""
            if proc.returncode == 0 and tail and got == expected:
                print(f"✓ {name:24s} → {tail[-1]}")
                if args.verbose:
                    print("   " + "\n   ".join(
                        ln for ln in proc.stdout.splitlines() if ln.startswith(("選択", "通学路", "エンディング"))))
            elif proc.returncode == 0 and tail:
                ok = False
                print(f"✗ {name:24s} → {got} に到達（期待: {expected}）")
            else:
                ok = False
                err = (proc.stderr.strip().splitlines() or ["(出力なし)"])[-1]
                print(f"✗ {name:24s} → 失敗 (returncode={proc.returncode}) {err}")
        return 0 if ok else 1

    choices = [int(x) for x in args.choices.split(",")] if args.choices else []
    ending, log, frames = play(choices, seed=args.seed, verbose=True,
                               route_policy=args.route_policy)
    print(f"\n到達: {ending} / {frames} フレーム")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
