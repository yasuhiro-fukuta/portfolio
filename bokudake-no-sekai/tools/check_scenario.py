#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""シナリオの静的チェック。

ラベルの飛び先だけでなく、背景名・立ち絵ID・敵ID・部屋ID・通学路ステージ・
エンディングIDが実装側に存在するかを確かめる。CI 代わりに使える。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
pygame.init()

from boku import art                       # noqa: E402
from boku.data.enemies import ENEMIES      # noqa: E402
from boku.data.rooms import ROOMS          # noqa: E402
from boku.scenes.ending import ENDINGS     # noqa: E402
from boku.scenes.route import STAGES       # noqa: E402
from boku.script import load_script        # noqa: E402

KNOWN_FLAGS = {"jibun", "kizuna", "yuusha", "hokorobi", "day", "route_ok"}


def main() -> int:
    script = load_script()
    errors: list[str] = []
    warnings: list[str] = []

    for cmd in script.commands:
        where = f"{cmd.src}:{cmd.line}"
        a = cmd.args
        if cmd.op == "bg" and a["name"] not in art._BUILDERS:
            errors.append(f"知らない背景 '{a['name']}' ({where})")
        elif cmd.op == "chara" and a.get("id") and a["id"] not in art.CHARACTERS:
            errors.append(f"知らない立ち絵 '{a['id']}' ({where})")
        elif cmd.op == "battle" and a["enemy"] not in ENEMIES:
            errors.append(f"知らない敵 '{a['enemy']}' ({where})")
        elif cmd.op == "explore" and a["room"] not in ROOMS:
            errors.append(f"知らない探索先 '{a['room']}' ({where})")
        elif cmd.op == "route" and a["stage"] not in STAGES:
            errors.append(f"知らない通学路 '{a['stage']}' ({where})")
        elif cmd.op == "ending" and a["id"] not in ENDINGS:
            errors.append(f"知らないエンディング '{a['id']}' ({where})")
        elif cmd.op in ("flag", "if") and a["key"] not in KNOWN_FLAGS:
            warnings.append(f"見慣れないフラグ '{a['key']}' ({where})")

    # 到達できないラベルを洗い出す
    referenced = set()
    for cmd in script.commands:
        if cmd.op in ("jump", "if"):
            referenced.add(cmd.args["label"])
        elif cmd.op == "choice":
            referenced.update(o["label"] for o in cmd.args["options"])
    fallthrough = set()
    for name, idx in script.labels.items():
        if idx > 0 and script[idx - 1].op not in ("jump", "ending"):
            fallthrough.add(name)
    for name in script.labels:
        if name not in referenced and name not in fallthrough:
            warnings.append(f"どこからも飛んでこないラベル: {name}")

    says = sum(1 for c in script.commands if c.op == "say")
    chars = sum(len(c.args["text"]) for c in script.commands if c.op == "say")
    print(f"コマンド数 : {len(script)}")
    print(f"ラベル数   : {len(script.labels)}")
    print(f"セリフ数   : {says}（本文 {chars} 文字）")
    print(f"選択肢     : {sum(1 for c in script.commands if c.op == 'choice')}")
    print(f"エンディング: {sorted({c.args['id'] for c in script.commands if c.op == 'ending'})}")

    for w in warnings:
        print("警告:", w)
    for e in errors:
        print("エラー:", e)
    if errors:
        print(f"\n✗ {len(errors)} 件のエラー")
        return 1
    print("\n✓ シナリオの参照はすべて解決しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
