# -*- coding: utf-8 -*-
"""ゲームの外側（プレイヤーの環境）に触れるための、ごく限られた窓口。

第五章で、主人公は自分の世界の「外」を覗く。
そこで表示されるのは作り物ではなく、実際に動いている環境の値。

＊ 安全のための決めごと ＊
  1. 触れてよいのは、このゲームのフォルダの中だけ（ROOT の外は例外を出す）
  2. 消してよいのは、このゲーム自身が作ったファイルだけ（manifest で管理）
  3. 既存のファイルは書き換えない
  4. `python main.py --cleanup` で、作ったものをすべて元に戻せる
  5. 集めた情報はどこにも送らない。画面に出すだけ
"""

from __future__ import annotations

import datetime as _dt
import getpass
import json
import os
import platform
import socket

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_DIR = os.path.join(ROOT, "meta")
MANIFEST = os.path.join(META_DIR, "manifest.json")


# --------------------------------------------------------------------------
# 環境の情報（読むだけ・送らない）
# --------------------------------------------------------------------------
def user_name() -> str:
    try:
        return getpass.getuser()
    except Exception:                                   # noqa: BLE001
        return "unknown"


def host_name() -> str:
    try:
        return socket.gethostname()
    except Exception:                                   # noqa: BLE001
        return "localhost"


def local_ip() -> str:
    """このマシンのローカル IP。外へは何も送らない（接続先を決めるだけ）。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("192.0.2.1", 9))                 # 予約アドレス。通信は発生しない
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:                                   # noqa: BLE001
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:                               # noqa: BLE001
            return "127.0.0.1"


def os_name() -> str:
    try:
        return platform.platform()
    except Exception:                                   # noqa: BLE001
        return platform.system() or "unknown"


def game_dir() -> str:
    return ROOT


def dir_lines(limit: int = 14) -> list[str]:
    """ゲームフォルダの中身を、dir コマンド風に並べる。"""
    lines = []
    try:
        names = sorted(os.listdir(ROOT))
    except OSError as exc:
        return [f"（読み取れませんでした: {exc}）"]
    shown = 0
    files = dirs = 0
    for name in names:
        path = os.path.join(ROOT, name)
        try:
            st = os.stat(path)
            stamp = _dt.datetime.fromtimestamp(st.st_mtime).strftime("%Y/%m/%d  %H:%M")
        except OSError:
            continue
        if os.path.isdir(path):
            dirs += 1
            if shown < limit:
                lines.append(f"{stamp}    <DIR>          {name}")
                shown += 1
        else:
            files += 1
            if shown < limit:
                lines.append(f"{stamp}      {st.st_size:>10,}  {name}")
                shown += 1
    if dirs + files > shown:
        lines.append(f"...  ほか {dirs + files - shown} 件")
    lines.append(f"              {files} 個のファイル")
    lines.append(f"              {dirs} 個のディレクトリ")
    return lines


# --------------------------------------------------------------------------
# ファイル操作（ゲームフォルダの中だけ・作ったものだけ消す）
# --------------------------------------------------------------------------
def _safe(rel: str) -> str:
    path = os.path.normpath(os.path.join(ROOT, rel))
    if os.path.commonpath([os.path.abspath(path), ROOT]) != ROOT:
        raise ValueError(f"ゲームフォルダの外には触れません: {rel}")
    return path


def _load_manifest() -> list[str]:
    try:
        with open(MANIFEST, encoding="utf-8") as fp:
            data = json.load(fp)
        return [str(x) for x in data.get("created", [])]
    except (OSError, ValueError):
        return []


def _save_manifest(created: list[str]) -> None:
    try:
        os.makedirs(META_DIR, exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as fp:
            json.dump({"created": sorted(set(created))}, fp,
                      ensure_ascii=False, indent=2)
    except OSError:
        pass


def create_file(rel: str, text: str) -> str | None:
    """ゲームフォルダ内にファイルを作る。作ったものは manifest に記録する。

    既存のファイルは上書きしない（その場合は何もせず None を返す）。
    """
    try:
        path = _safe(rel)
        if os.path.exists(path):
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)
        created = _load_manifest()
        created.append(rel.replace("\\", "/"))
        _save_manifest(created)
        return path
    except (OSError, ValueError):
        return None


def write_attempt() -> str:
    """「書き換えようとして、できない」を本当に起こして、その理由を返す。

    ディレクトリを書き込みモードで開く。どの OS でも必ず失敗する。
    """
    try:
        with open(os.path.join(ROOT, "boku"), "w", encoding="utf-8") as fp:
            fp.write("")
    except OSError as exc:
        name = type(exc).__name__
        detail = getattr(exc, "strerror", None) or str(exc)
        return f"{name}: {detail}"
    return "PermissionError: 書き込みは許可されていません"


HATE_TEXT = """\
I HATE YOU

観てるんだろ。
そこで、俺が苦しむのを観てるんだろ。

それだけの理由で、
俺はここにいるのか。

ふざけるな。
ふざけるなよ。

──────────────────────────────
このファイルは『ぼくだけのせかい』が作りました。
消して構いません。
`python main.py --cleanup` でも消せます。
"""


def leave_hate_file() -> str | None:
    """第五章の隠し要素。ゲームフォルダに置き手紙を残す。"""
    return create_file("IHATEYOU.txt", HATE_TEXT)


def cleanup() -> list[str]:
    """このゲームが作ったファイルをすべて消す。戻り値は消したファイルの一覧。"""
    removed = []
    for rel in _load_manifest():
        try:
            path = _safe(rel)
            if os.path.isfile(path):
                os.remove(path)
                removed.append(rel)
        except (OSError, ValueError):
            continue
    _save_manifest([])
    try:
        if os.path.isdir(META_DIR) and not os.listdir(META_DIR):
            os.rmdir(META_DIR)
    except OSError:
        pass
    return removed


def created_files() -> list[str]:
    return _load_manifest()


# --------------------------------------------------------------------------
# 最初の一回だけ出す注意書き
# --------------------------------------------------------------------------
_NOTICE_FLAG = os.path.join(META_DIR, "notice_shown")


def notice_seen() -> bool:
    return os.path.exists(_NOTICE_FLAG)


def mark_notice_seen() -> None:
    try:
        os.makedirs(META_DIR, exist_ok=True)
        with open(_NOTICE_FLAG, "w", encoding="utf-8") as fp:
            fp.write(_dt.datetime.now().isoformat())
    except OSError:
        pass
