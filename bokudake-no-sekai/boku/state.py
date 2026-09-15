# -*- coding: utf-8 -*-
"""ゲームの進行状態（フラグ・現在地・画面の状態）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    # シナリオ上の位置
    pc: int = 0                                  # 実行中のコマンド番号
    chapter: str = "プロローグ"

    # こころのパラメータ
    flags: dict[str, int] = field(default_factory=lambda: {
        "hokorobi": 0,        # 見つけた「ほころび」の数
        "shouki": 100,        # 正気（外に出ているあいだ削られる）
        "errand_school": 0,   # プリントを出した
        "errand_super": 0,    # 牛乳を買った
        "errand_done": 0,     # 終えたおつかいの数
        "route_ok": 1,        # 直前の外出に成功したか
        "shouki_broken": 0,   # 正気がゼロになったか
        "day": 0,
    })

    # 画面の状態（セーブ復帰のために持っておく）
    bg: str = "black"
    characters: list = field(default_factory=list)   # [[id, pos], ...]
    glitch: float = 0.0                              # 画面のほころび具合

    endings_seen: list[str] = field(default_factory=list)

    # ---- フラグ操作 -------------------------------------------------------
    def get(self, key: str) -> int:
        return self.flags.get(key, 0)

    def set(self, key: str, value: int):
        self.flags[key] = int(value)

    def add(self, key: str, value: int):
        self.flags[key] = self.get(key) + int(value)

    def check(self, key: str, op: str, value: int) -> bool:
        cur = self.get(key)
        return {
            ">=": cur >= value, "<=": cur <= value,
            ">": cur > value, "<": cur < value,
            "==": cur == value, "!=": cur != value,
        }[op]

    # ---- 保存・復元 -------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "pc": self.pc, "chapter": self.chapter, "flags": dict(self.flags),
            "bg": self.bg, "characters": [list(c) for c in self.characters],
            "glitch": self.glitch,
            "endings_seen": list(self.endings_seen),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        st = cls()
        st.pc = int(data.get("pc", 0))
        st.chapter = data.get("chapter", "")
        st.flags.update({k: int(v) for k, v in data.get("flags", {}).items()})
        st.bg = data.get("bg", "black")
        st.glitch = float(data.get("glitch", 0.0))
        st.characters = [list(c) for c in data.get("characters", [])]
        st.endings_seen = list(data.get("endings_seen", []))
        return st
