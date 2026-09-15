# -*- coding: utf-8 -*-
"""セーブデータの読み書き（JSON）。"""

from __future__ import annotations

import datetime as _dt
import json
import os

from . import config as C
from .state import GameState

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(_BASE, C.SAVE_DIR)


def _path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"save{slot}.json")


def save(slot: int, state: GameState, headline: str = "") -> bool:
    """スロットに保存する。失敗しても落とさない。"""
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        payload = {
            "version": C.VERSION,
            "saved_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "headline": headline[:40],
            "state": state.to_dict(),
        }
        with open(_path(slot), "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def load(slot: int) -> GameState | None:
    info = peek(slot)
    if not info:
        return None
    return GameState.from_dict(info["state"])


def peek(slot: int) -> dict | None:
    """セーブの中身（見出しや日時）だけ覗く。無ければ None。"""
    try:
        with open(_path(slot), encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, ValueError):
        return None


def exists(slot: int) -> bool:
    return os.path.exists(_path(slot))


def any_exists() -> bool:
    return any(exists(i) for i in range(1, C.SAVE_SLOTS + 1))


def latest_slot() -> int | None:
    best, best_at = None, ""
    for i in range(1, C.SAVE_SLOTS + 1):
        info = peek(i)
        if info and info.get("saved_at", "") >= best_at:
            best, best_at = i, info.get("saved_at", "")
    return best
