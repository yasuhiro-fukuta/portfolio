# -*- coding: utf-8 -*-
"""シナリオ記法のパーサ。

scenario/*.txt を読み込み、1本のコマンド列にする。

    # これはコメント
    @bg room_morning
    @chapter プロローグ|六月のあさ
    @chara boku left
    ぼく：きょうも、そとには でない。
    かべの むこうで、あさが はじまっている。
    @choice
    - カーテンを あける -> open_curtain
    - ふとんに もぐる -> stay_bed  [courage>=1]
    @label open_curtain
    @flag courage + 1
    @jump ch1

対応コマンド：
    bg / chara / chapter / caption / say / wait / clear / choice / label /
    jump / flag / if / explore / route / shake / flash / glitch /
    bgm / ending / save
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field

SCENARIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scenario")

_COND_RE = re.compile(r"^\s*(\w+)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)\s*$")


class ScriptError(Exception):
    pass


@dataclass
class Command:
    op: str
    args: dict = field(default_factory=dict)
    src: str = ""
    line: int = 0

    def __repr__(self):  # デバッグしやすさのため
        return f"<{self.op} {self.args} @{self.src}:{self.line}>"


@dataclass
class Script:
    commands: list[Command]
    labels: dict[str, int]

    def __len__(self):
        return len(self.commands)

    def __getitem__(self, i) -> Command:
        return self.commands[i]

    def index_of(self, label: str) -> int:
        if label not in self.labels:
            raise ScriptError(f"ラベルが見つかりません: {label}")
        return self.labels[label]


def _parse_condition(text: str) -> tuple[str, str, int]:
    m = _COND_RE.match(text)
    if not m:
        raise ScriptError(f"条件式が読めません: {text}")
    return m.group(1), m.group(2), int(m.group(3))


def _parse_line(raw: str, src: str, lineno: int) -> Command | None:
    line = raw.rstrip("\n").strip()
    if not line or line.startswith("#") or line.startswith("//"):
        return None

    if not line.startswith("@"):
        # セリフ or 地の文。「名前：本文」なら名前つき。
        name, text = "", line
        for sep in ("：", ":"):
            if sep in line:
                head, body = line.split(sep, 1)
                if head and len(head) <= 12 and " " not in head and "、" not in head:
                    name, text = head.strip(), body.strip()
                break
        text = text.replace("\\n", "\n")
        return Command("say", {"name": name, "text": text}, src, lineno)

    parts = line[1:].split(None, 1)
    op = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if op == "bg":
        a = rest.split()
        return Command("bg", {"name": a[0] if a else "black",
                              "instant": "instant" in a[1:]}, src, lineno)

    if op == "chara":
        a = rest.split()
        if not a or a[0] == "clear":
            return Command("chara", {"clear": True}, src, lineno)
        if a[0] == "hide":
            return Command("chara", {"hide": a[1] if len(a) > 1 else ""}, src, lineno)
        return Command("chara", {"id": a[0], "pos": a[1] if len(a) > 1 else "center"},
                       src, lineno)

    if op == "chapter":
        title, _, subtitle = rest.partition("|")
        return Command("chapter", {"title": title.strip(), "subtitle": subtitle.strip()},
                       src, lineno)

    if op == "caption":
        return Command("caption", {"text": rest.replace("\\n", "\n")}, src, lineno)

    if op == "wait":
        try:
            sec = float(rest) if rest else 0.0
        except ValueError:
            sec = 0.0
        return Command("wait", {"seconds": sec}, src, lineno)

    if op in ("clear", "choice", "save"):
        return Command(op, {}, src, lineno)

    if op == "label":
        return Command("label", {"name": rest}, src, lineno)

    if op == "jump":
        return Command("jump", {"label": rest}, src, lineno)

    if op == "flag":
        a = rest.split()
        if len(a) == 3:
            key, oper, val = a
        elif len(a) == 2:                       # 「@flag courage +1」形式
            key, token = a
            oper, val = token[0], token[1:]
        else:
            raise ScriptError(f"@flag の書き方が不正です: {rest}")
        if oper not in ("+", "-", "="):
            raise ScriptError(f"@flag の演算子が不正です: {oper}")
        return Command("flag", {"key": key, "op": oper, "value": int(val)}, src, lineno)

    if op == "if":
        cond, _, label = rest.partition("->")
        key, oper, val = _parse_condition(cond)
        return Command("if", {"key": key, "cmp": oper, "value": val,
                              "label": label.strip()}, src, lineno)

    if op == "explore":
        return Command("explore", {"room": rest.strip()}, src, lineno)

    if op == "route":
        a = rest.split()
        return Command("route", {"stage": a[0] if a else "1"}, src, lineno)

    if op == "shake":
        try:
            power = float(rest) if rest else 12.0
        except ValueError:
            power = 12.0
        return Command("shake", {"power": power}, src, lineno)

    if op == "glitch":
        try:
            level = float(rest) if rest else 1.0
        except ValueError:
            level = 1.0
        return Command("glitch", {"level": level}, src, lineno)

    if op == "flash":
        return Command("flash", {"color": rest.strip() or "white"}, src, lineno)

    if op == "bgm" or op == "se":
        return Command("sound", {"name": rest.strip()}, src, lineno)

    if op == "ending":
        return Command("ending", {"id": rest.strip()}, src, lineno)

    raise ScriptError(f"知らないコマンドです: @{op}  ({src}:{lineno})")


def _parse_option(raw: str, src: str, lineno: int) -> dict:
    """`- テキスト -> ラベル  [courage>=2]` を読む。"""
    body = raw.strip()[1:].strip()
    cond = None
    if body.endswith("]") and "[" in body:
        body, _, cond_text = body.rpartition("[")
        cond = _parse_condition(cond_text[:-1])
        body = body.strip()
    text, _, label = body.partition("->")
    label = label.strip()
    if not label:
        raise ScriptError(f"選択肢に飛び先がありません: {raw.strip()} ({src}:{lineno})")
    return {"text": text.strip(), "label": label, "cond": cond}


def parse_text(text: str, src: str = "<text>") -> list[Command]:
    commands: list[Command] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped.startswith("-") and commands and commands[-1].op == "choice":
            commands[-1].args.setdefault("options", []).append(
                _parse_option(stripped, src, i + 1))
            i += 1
            continue
        cmd = _parse_line(raw, src, i + 1)
        if cmd:
            if cmd.op == "choice":
                cmd.args["options"] = []
            commands.append(cmd)
        i += 1
    return commands


def load_script(directory: str = SCENARIO_DIR) -> Script:
    """scenario ディレクトリの .txt をファイル名順に連結して読み込む。"""
    files = sorted(glob.glob(os.path.join(directory, "*.txt")))
    if not files:
        raise ScriptError(f"シナリオが見つかりません: {directory}")
    commands: list[Command] = []
    for path in files:
        with open(path, encoding="utf-8") as fp:
            commands.extend(parse_text(fp.read(), os.path.basename(path)))

    labels: dict[str, int] = {}
    for idx, cmd in enumerate(commands):
        if cmd.op == "label":
            name = cmd.args["name"]
            if name in labels:
                raise ScriptError(f"ラベルが重複しています: {name} ({cmd.src}:{cmd.line})")
            labels[name] = idx

    script = Script(commands, labels)
    validate(script)
    return script


def validate(script: Script) -> None:
    """飛び先ラベルがすべて存在するか、選択肢が空でないかを確かめる。"""
    for cmd in script.commands:
        targets = []
        if cmd.op in ("jump", "if"):
            targets.append(cmd.args["label"])
        elif cmd.op == "choice":
            if not cmd.args.get("options"):
                raise ScriptError(f"選択肢が空です ({cmd.src}:{cmd.line})")
            targets.extend(o["label"] for o in cmd.args["options"])
        for target in targets:
            if target not in script.labels:
                raise ScriptError(
                    f"飛び先ラベルがありません: {target} ({cmd.src}:{cmd.line})")
