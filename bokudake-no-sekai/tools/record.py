#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ヘッドレスで通しプレイし、そのまま動画（mp4）に録画する。

    python3 tools/record.py --chapter 1
    python3 tools/record.py --all

人のプレイに近い間合いで自動操作する：
  ・文字が出きってから すこし ためて 送る
  ・選択肢は いちど 見せてから 選ぶ
  ・探索は ひとつずつ 調べる
  ・外出シーンは 見られそうなら かげで やりすごす
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import imageio_ffmpeg  # noqa: E402

FPS = 24
DT = 1.0 / FPS
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recordings")

# （名前, 開始ラベル, 終了条件のラベル, 選択肢, 出力名）
CHAPTERS = {
    "1": {"title": "第一章 まもったせかい", "start": None, "stop_label": "ch2_start",
          "choices": [1, 1], "file": "ch1_matta_sekai.mp4"},
    "2": {"title": "第二章 めがさめる", "start": "ch2_start", "stop_label": "ch3_start",
          "choices": [0], "file": "ch2_megasameru.mp4"},
    "3": {"title": "第三章 また、ゆめのなかで", "start": "ch3_start", "stop_label": None,
          "choices": [0, 0, 1], "file": "ch3_yume_no_naka.mp4"},
}


class _Keys:
    def __init__(self, held=()):
        self.held = set(held)

    def __getitem__(self, key):
        return key in self.held


class Recorder:
    """フレームを ffmpeg に流しこむ。"""

    def __init__(self, path, scale=(720, 406)):
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            exe, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "960x540", "-r", str(FPS), "-i", "-",
            "-vf", f"scale={scale[0]}:{scale[1]}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", path,
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.frames = 0

    def add(self, surface):
        self.proc.stdin.write(pygame.image.tostring(surface, "RGB"))
        self.frames += 1

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def _route_direction(scene) -> tuple:
    """外出シーンの自動操作。見られる前に かげへ、目を そらした すきに 進む。"""
    import pygame as pg
    if scene.chase:
        return (pg.K_RIGHT,)

    x = scene.x
    in_shadow = scene._in_shadow()
    for w in scene.stage["watchers"]:
        if x > w["x"] + w["radius"]:
            continue                                   # もう 通りすぎた
        if not scene._watching(w):
            continue                                   # いまは 見ていない
        if x < w["x"] - w["radius"] - 30:
            # まだ 手前。視線の 手前の かげで 待つ
            ahead = [sh for sh in scene.stage["shadows"]
                     if sh[0] > x - 10 and sh[1] < w["x"] - w["radius"] + 40]
            if in_shadow:
                return ()
            if ahead:
                return (pg.K_RIGHT,)
            return ()
        if in_shadow:
            return ()                                  # かげの 中で やりすごす
        back = [sh for sh in scene.stage["shadows"] if sh[1] <= x + 6]
        if back and x - back[-1][1] < 140:
            return (pg.K_LEFT,)                        # 手前の かげへ もどる
        return (pg.K_RIGHT,)                           # もう 走りぬけるしかない
    return (pg.K_RIGHT,)


def record_chapter(key: str, out_dir: str, max_seconds: int = 900) -> str:
    from boku.app import App
    from boku.scenes.ending import EndingScene
    from boku.scenes.explore import ExploreScene
    from boku.scenes.route import RouteScene
    from boku.scenes.story import StoryScene

    conf = CHAPTERS[key]
    pygame.key.get_mods = lambda: 0
    pygame.mouse.get_pressed = lambda *a, **k: (0, 0, 0)
    keys_held: list = []
    pygame.key.get_pressed = lambda: _Keys(keys_held)

    app = App(headless=True)
    story = StoryScene(app, start_label=conf["start"])
    app.push(story)
    stop_pc = story.script.index_of(conf["stop_label"]) if conf["stop_label"] else None

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, conf["file"])
    rec = Recorder(path)
    log: list[str] = [f"=== {conf['title']} ==="]

    choices = list(conf["choices"])
    choice_i = 0
    hold = 0.0            # 次の操作までの ため
    reading = False       # 読み終わるのを 待っている あいだ
    max_frames = max_seconds * FPS
    last_text = None

    while rec.frames < max_frames:
        scene = app.scene
        if scene is None:
            break
        hold = max(0.0, hold - DT)

        if isinstance(scene, StoryScene):
            # 次の章に入ったら そこで 録画を きる
            if stop_pc is not None and scene.st.pc >= stop_pc:
                break
            if scene.mode == "message":
                if scene.msg.full_text != last_text:
                    last_text = scene.msg.full_text
                    name = scene.msg.name
                    log.append(f"{name}：{scene.msg.full_text}" if name else scene.msg.full_text)
                    hold = 0.0
                if scene.msg.finished:
                    if hold <= 0 and not reading:
                        # 読み終わるまでの ま（文字数に応じて）
                        hold = min(2.4, 0.34 + len(scene.msg.full_text) * 0.040)
                        reading = True
                    elif hold <= 0 and reading:
                        reading = False
                        scene._advance()
            elif scene.mode == "caption":
                if scene.caption_text != last_text:
                    last_text = scene.caption_text
                    log.append(f"〔{scene.caption_text}〕")
                    hold = min(4.0, 1.5 + len(scene.caption_text) * 0.055)
                elif hold <= 0:
                    scene._advance()
            elif scene.mode == "choice" and scene.menu:
                pick = choices[choice_i] if choice_i < len(choices) else 0
                pick = min(pick, len(scene.menu.options) - 1)
                if hold <= 0:
                    if scene.menu.index != pick:
                        scene.menu.move(1)
                        hold = 0.7
                    else:
                        log.append(f"▷ 選択：{scene.menu.options[pick]}")
                        choice_i += 1
                        scene._advance()
                        hold = 0.4
            elif scene.mode == "run":
                scene.step()
                last_text = None

        elif isinstance(scene, ExploreScene):
            if scene.mode == "read":
                if scene.msg.full_text != last_text:
                    last_text = scene.msg.full_text
                    log.append(f"　{scene.msg.full_text}")
                    hold = 0.0
                if scene.msg.finished:
                    if hold <= 0 and not reading:
                        hold = min(2.4, 0.34 + len(scene.msg.full_text) * 0.040)
                        reading = True
                    elif hold <= 0 and reading:
                        reading = False
                        scene._advance()
            elif hold <= 0:
                unseen = [i for i, it in enumerate(scene.items)
                          if it["id"] != "__exit__" and it["id"] not in scene.seen]
                want = unseen[0] if unseen else len(scene.items) - 1
                if scene.index != want:
                    scene.index = (scene.index + 1) % len(scene.items)
                    hold = 0.22
                else:
                    log.append(f"▷ しらべる：{scene.items[want]['name']}")
                    scene._select()
                    hold = 0.3

        elif isinstance(scene, RouteScene):
            if scene.phase == "ready":
                keys_held[:] = []
                if not getattr(scene, "_logged", False):
                    scene._logged = True
                    log.append(f"▷ 外出：{scene.stage['label']}")
                    hold = 2.6
                elif hold <= 0:
                    scene.phase = "play"
            elif scene.phase == "play":
                keys_held[:] = _route_direction(scene)
            else:
                keys_held[:] = []
                if hold <= 0:
                    log.append(f"　→ {scene.phase}（正気 {scene.shouki}）")
                    hold = 1.8
                    scene._finish()

        elif isinstance(scene, EndingScene):
            if scene.phase == "credits" and scene.scroll > 240:
                scene.scroll += 260 * DT * 6        # スタッフロールは早送り
            if scene.phase == "done":
                break

        scene.time += DT
        scene.update(DT)
        app.canvas.fill((0, 0, 0))
        scene.draw(app.canvas)
        rec.add(app.canvas)

    rec.close()
    seconds = rec.frames / FPS
    log_path = os.path.splitext(path)[0] + ".txt"
    with open(log_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(log))
    size = os.path.getsize(path) / 1024 / 1024
    print(f"{conf['title']}: {path}  {seconds:.0f}秒  {size:.1f}MB  （ログ: {os.path.basename(log_path)}）")
    pygame.quit()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", default=None, choices=list(CHAPTERS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    if args.all:
        # pygame を同一プロセスで初期化し直すと不安定なので、章ごとに別プロセス
        for key in CHAPTERS:
            proc = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--chapter", key,
                 "--out", args.out], capture_output=True, text=True, timeout=2400)
            out = [ln for ln in proc.stdout.splitlines() if ln.strip()]
            if proc.returncode == 0 and out:
                print(out[-1])
            else:
                err = (proc.stderr.strip().splitlines() or ["(出力なし)"])[-1]
                print(f"✗ 第{key}章 の録画に失敗: {err}")
        return 0
    record_chapter(args.chapter or "1", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
