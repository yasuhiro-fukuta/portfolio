# -*- coding: utf-8 -*-
"""物語シーン。シナリオのコマンドを解釈して進める、このゲームの中心。"""

from __future__ import annotations

import pygame

from .. import config as C
from .. import save as save_mod
from ..app import (CANCEL_KEYS, CONFIRM_KEYS, DOWN_KEYS, Scene, UP_KEYS)
from ..art import Background, GlitchDriver, draw_character, draw_tear
from ..fonts import get_font
from ..script import Script, load_script
from ..ui import (Backlog, ChoiceMenu, Fader, MessageWindow, Shake,
                  draw_text_center, draw_text_shadow, panel, radial_light)

AUTO_SLOT = 0


class StoryScene(Scene):
    def __init__(self, app, script: Script | None = None, start_label: str | None = None):
        super().__init__(app)
        self.script = script or load_script()
        self.st = app.state

        self.bg = Background(self.st.bg)
        self.msg = MessageWindow()
        self.backlog = Backlog()
        self.fader = Fader()
        self.shake = Shake()
        self.glitch = GlitchDriver(self.st.glitch)

        self.mode = "run"            # run / message / choice / wait / chapter / caption / menu / slots
        self.timer = 0.0
        self.menu: ChoiceMenu | None = None
        self.choice_cmd = None
        self.card: tuple[str, str] | None = None
        self.caption_text = ""
        self.slot_purpose = ""
        self.toast = ""
        self.toast_time = 0.0
        self.hint_time = 6.0
        self.save_pc = self.st.pc

        if start_label:
            self.st.pc = self.script.index_of(start_label)
        self.fader.set(255)
        self.fader.to(0, 0.8)

    # ------------------------------------------------------------------
    # 進行
    # ------------------------------------------------------------------
    def on_enter(self):
        self._sync_screen()
        self.step()

    def _sync_screen(self):
        self.bg.change(self.st.bg, instant=True)

    def notify(self, text: str):
        self.toast = text
        self.toast_time = 2.2

    def step(self):
        """入力待ちになるまでコマンドを実行する。"""
        guard = 0
        while self.mode == "run":
            guard += 1
            if guard > 2000:
                self.notify("シナリオがループしています")
                self.mode = "message"
                return
            if self.st.pc >= len(self.script):
                self._goto_ending("stay")
                return
            cmd = self.script[self.st.pc]
            self.st.pc += 1
            self._execute(cmd)

    def _execute(self, cmd):
        op, a = cmd.op, cmd.args

        if op == "say":
            self.save_pc = self.st.pc - 1
            self.msg.set_text(a["text"], a["name"])
            self.backlog.push(a["name"], a["text"])
            self.mode = "message"

        elif op == "bg":
            self.st.bg = a["name"]
            self.bg.change(a["name"], instant=a.get("instant", False))

        elif op == "chara":
            if a.get("clear"):
                self.st.characters = []
            elif a.get("hide"):
                self.st.characters = [c for c in self.st.characters if c[0] != a["hide"]]
            else:
                self.st.characters = [c for c in self.st.characters if c[0] != a["id"]]
                self.st.characters.append([a["id"], a["pos"]])

        elif op == "chapter":
            self.st.chapter = a["title"]
            self.card = (a["title"], a["subtitle"])
            self.timer = 3.4
            self.mode = "chapter"
            self.msg.clear()
            save_mod.save(AUTO_SLOT, self.st, f"{a['title']}　{a['subtitle']}")

        elif op == "caption":
            self.save_pc = self.st.pc - 1
            self.caption_text = a["text"]
            self.backlog.push("", a["text"])
            self.msg.clear()
            self.mode = "caption"

        elif op == "wait":
            self.timer = a["seconds"] or 0.8
            self.mode = "wait"

        elif op == "clear":
            self.msg.clear()

        elif op == "label":
            pass

        elif op == "jump":
            self.st.pc = self.script.index_of(a["label"])

        elif op == "flag":
            if a["op"] == "+":
                self.st.add(a["key"], a["value"])
            elif a["op"] == "-":
                self.st.add(a["key"], -a["value"])
            else:
                self.st.set(a["key"], a["value"])

        elif op == "if":
            if self.st.check(a["key"], a["cmp"], a["value"]):
                self.st.pc = self.script.index_of(a["label"])

        elif op == "choice":
            options = [o for o in a["options"]
                       if not o["cond"] or self.st.check(*o["cond"])]
            if not options:
                options = a["options"]
            self.choice_cmd = options
            self.menu = ChoiceMenu([o["text"] for o in options],
                                   center_y=C.SCREEN_H // 2 + 20)
            self.msg.clear()
            self.mode = "choice"

        elif op == "explore":
            from .explore import ExploreScene
            self.mode = "suspend"
            self.msg.clear()
            self.app.push(ExploreScene(self.app, a["room"]))

        elif op == "glitch":
            self.st.glitch = a["level"]
            self.glitch.set_base(a["level"])

        elif op == "burst":
            self.glitch.hit(a["power"], 0.34)

        elif op == "console":
            from .console import ConsoleScene
            self.mode = "suspend"
            self.msg.clear()
            self.app.push(ConsoleScene(self.app, a["id"]))

        elif op == "route":
            from .route import RouteScene
            self.mode = "suspend"
            self.msg.clear()
            self.app.push(RouteScene(self.app, a["stage"]))

        elif op == "shake":
            self.shake.kick(a["power"], 0.4)

        elif op == "flash":
            color = (255, 255, 255) if a["color"] == "white" else C.INK
            self.fader.set(230, color)
            self.fader.to(0, 0.7, color)

        elif op == "sound":
            pass                                  # 効果音は未実装（素材なしで作る方針のため）

        elif op == "ending":
            self._goto_ending(a["id"])

    def _goto_ending(self, ending_id: str):
        from .ending import EndingScene
        if ending_id not in self.st.endings_seen:
            self.st.endings_seen.append(ending_id)
        self.mode = "suspend"
        self.app.replace(EndingScene(self.app, ending_id))

    def on_resume(self, result=None):
        """バトルや探索から戻ってきた。"""
        self.mode = "run"
        self._sync_screen()
        self.fader.set(180)
        self.fader.to(0, 0.5)
        self.step()

    # ------------------------------------------------------------------
    # 入力
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if self.backlog.open:
            self._handle_backlog(event)
            return
        if self.mode in ("menu", "slots"):
            self._handle_menu(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.backlog.toggle()
                return
            if event.key in CANCEL_KEYS:
                self._open_menu()
                return
            if event.key == pygame.K_F5:
                self._quick_save()
                return
            if event.key == pygame.K_F9:
                self._quick_load()
                return
            if event.key in CONFIRM_KEYS:
                self._advance()
                return
            if self.mode == "choice" and self.menu:
                if event.key in UP_KEYS:
                    self.menu.move(-1)
                elif event.key in DOWN_KEYS:
                    self.menu.move(1)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.app.mouse_pos()
            if self.mode == "choice" and self.menu:
                picked = self.menu.click(pos)
                if picked is not None:
                    self.menu.index = picked
                    self._advance()
            else:
                self._advance()

        elif event.type == pygame.MOUSEMOTION and self.mode == "choice" and self.menu:
            self.menu.hover(self.app.mouse_pos())

        elif event.type == pygame.MOUSEWHEEL and event.y > 0:
            self.backlog.toggle()

    def _handle_backlog(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self.backlog.scroll(1)
            elif event.key in DOWN_KEYS:
                self.backlog.scroll(-1)
            elif event.key == pygame.K_b or event.key in CANCEL_KEYS:
                self.backlog.toggle()
        elif event.type == pygame.MOUSEWHEEL:
            self.backlog.scroll(event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.backlog.toggle()

    def _handle_menu(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self.menu.move(-1)
            elif event.key in DOWN_KEYS:
                self.menu.move(1)
            elif event.key in CONFIRM_KEYS:
                self._menu_select(self.menu.index)
            elif event.key in CANCEL_KEYS:
                self._close_menu()
        elif event.type == pygame.MOUSEMOTION:
            self.menu.hover(self.app.mouse_pos())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            picked = self.menu.click(self.app.mouse_pos())
            if picked is not None:
                self._menu_select(picked)

    def _advance(self):
        if self.mode == "message":
            if not self.msg.finished:
                self.msg.skip()
            else:
                self.mode = "run"
                self.step()
        elif self.mode == "caption":
            self.mode = "run"
            self.caption_text = ""
            self.step()
        elif self.mode == "chapter":
            self.timer = min(self.timer, 0.4)
        elif self.mode == "choice" and self.menu:
            picked = self.choice_cmd[self.menu.index]
            self.backlog.push("→", picked["text"])
            self.menu = None
            self.mode = "run"
            self.st.pc = self.script.index_of(picked["label"])
            self.step()

    # ---- メニュー ------------------------------------------------------
    def _open_menu(self):
        self.mode = "menu"
        self.menu = ChoiceMenu(["戻る", "セーブする", "ロードする", "タイトルへ"],
                               center_y=C.SCREEN_H // 2, width=420)

    def _close_menu(self):
        self.menu = None
        self.mode = "message" if self.msg.lines else "run"
        if self.mode == "run":
            self.step()

    def _slot_labels(self):
        labels = []
        for i in range(1, C.SAVE_SLOTS + 1):
            info = save_mod.peek(i)
            if info:
                labels.append(f"{i}　{info.get('headline', '')}　{info.get('saved_at', '')}")
            else:
                labels.append(f"{i}　- 空きスロット -")
        labels.append("戻る")
        return labels

    def _menu_select(self, index):
        if self.mode == "menu":
            if index == 0:
                self._close_menu()
            elif index in (1, 2):
                self.slot_purpose = "save" if index == 1 else "load"
                self.mode = "slots"
                self.menu = ChoiceMenu(self._slot_labels(),
                                       center_y=C.SCREEN_H // 2, width=620)
            else:
                from .title import TitleScene
                self.app.replace(TitleScene(self.app))
            return

        # スロット選択
        if index >= C.SAVE_SLOTS:
            self._open_menu()
            return
        slot = index + 1
        if self.slot_purpose == "save":
            st = self.st
            keep_pc, st.pc = st.pc, self.save_pc
            ok = save_mod.save(slot, st, st.chapter)
            st.pc = keep_pc
            self.notify(f"スロット{slot}にセーブしました" if ok else "セーブに失敗しました")
            self._close_menu()
        else:
            loaded = save_mod.load(slot)
            if loaded:
                self._apply_state(loaded)
            else:
                self.notify("データがありません")

    def _apply_state(self, loaded):
        self.app.state = loaded
        self.st = loaded
        self.glitch.set_base(loaded.glitch)
        self.menu = None
        self.msg.clear()
        self.mode = "run"
        self._sync_screen()
        self.fader.set(255)
        self.fader.to(0, 0.6)
        self.notify("読み込みました")
        self.step()

    def _quick_save(self):
        st = self.st
        keep_pc, st.pc = st.pc, self.save_pc
        ok = save_mod.save(1, st, st.chapter)
        st.pc = keep_pc
        self.notify("クイックセーブ（スロット1）" if ok else "セーブに失敗しました")

    def _quick_load(self):
        loaded = save_mod.load(1)
        if loaded:
            self._apply_state(loaded)
        else:
            self.notify("スロット1にデータがありません")

    # ------------------------------------------------------------------
    # 更新・描画
    # ------------------------------------------------------------------
    def update(self, dt):
        mods = pygame.key.get_mods()
        self.msg.fast = bool(mods & pygame.KMOD_CTRL) or pygame.key.get_pressed()[pygame.K_LSHIFT]
        self.bg.update(dt, self.time)
        self.msg.update(dt)
        self.fader.update(dt)
        self.shake.update(dt)
        self.glitch.update(dt)
        self.hint_time = max(0.0, self.hint_time - dt)
        self.toast_time = max(0.0, self.toast_time - dt)

        if self.mode == "wait":
            self.timer -= dt
            if self.timer <= 0:
                self.mode = "run"
                self.step()
        elif self.mode == "chapter":
            self.timer -= dt
            if self.timer <= 0:
                self.card = None
                self.mode = "run"
                self.step()

    def draw(self, surf):
        frame = pygame.Surface((C.SCREEN_W, C.SCREEN_H))
        self.bg.draw(frame, self.time)
        now = self.glitch.current
        for cid, pos in self.st.characters:
            # ノイズの人がたは、発作が起きていなくても かたちが ゆらぐ
            level = max(now, 1.2) if cid == "bug" else now * 0.6
            draw_character(frame, cid, pos, self.time, glitch_level=level)
        self.glitch.draw(frame, self.time)

        if self.mode == "caption" and self.caption_text:
            self._draw_caption(frame)
        else:
            self.msg.draw(frame, self.time)

        if self.mode == "choice" and self.menu:
            self.menu.draw(frame, self.time)

        self._draw_hud(frame)

        if self.mode in ("menu", "slots") and self.menu:
            overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
            overlay.fill((8, 10, 18, 190))
            frame.blit(overlay, (0, 0))
            title = "メニュー" if self.mode == "menu" else (
                "どのスロットにセーブする？" if self.slot_purpose == "save" else "どのデータを読み込む？")
            draw_text_center(frame, title, get_font(24, bold=True), C.MIST,
                             (C.SCREEN_W // 2, self.menu.top - 56))
            self.menu.draw(frame, self.time)

        if self.card:
            self._draw_chapter_card(frame)

        if self.backlog.open:
            self.backlog.draw(frame)

        self.fader.draw(frame)
        surf.blit(frame, self.shake.offset)

    def _draw_caption(self, frame):
        overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((6, 8, 14, 170))
        frame.blit(overlay, (0, 0))
        font = get_font(28)
        lines = self.caption_text.split("\n")
        y = C.SCREEN_H // 2 - len(lines) * (font.get_height() + 14) // 2
        for line in lines:
            draw_text_center(frame, line, font, C.PAPER, (C.SCREEN_W // 2, y))
            y += font.get_height() + 14

    def _draw_chapter_card(self, frame):
        title, subtitle = self.card
        alpha = 255
        if self.timer > 3.0:
            alpha = int(255 * (3.4 - self.timer) / 0.4)
        elif self.timer < 0.6:
            alpha = int(255 * self.timer / 0.6)
        alpha = max(0, min(255, alpha))

        overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((6, 8, 14, int(200 * alpha / 255)))
        frame.blit(overlay, (0, 0))
        glow = radial_light(220, C.GOLD, strength=int(70 * alpha / 255))
        frame.blit(glow, glow.get_rect(center=(C.SCREEN_W // 2, C.SCREEN_H // 2 - 10)))
        draw_text_center(frame, title, get_font(42, bold=True), C.PAPER,
                         (C.SCREEN_W // 2, C.SCREEN_H // 2 - 26), alpha=alpha)
        if subtitle:
            draw_text_center(frame, subtitle, get_font(24), C.GOLD,
                             (C.SCREEN_W // 2, C.SCREEN_H // 2 + 32), alpha=alpha)
        line_w = int(200 * alpha / 255)
        pygame.draw.line(frame, C.MIST,
                         (C.SCREEN_W // 2 - line_w, C.SCREEN_H // 2 + 2),
                         (C.SCREEN_W // 2 + line_w, C.SCREEN_H // 2 + 2), 1)

    def _draw_hud(self, frame):
        font = get_font(17)
        if self.st.chapter:
            draw_text_shadow(frame, self.st.chapter, font, C.MIST, (22, 16), alpha=140)
        hokorobi = self.st.get("hokorobi")
        if hokorobi:
            draw_text_shadow(frame, "ほころび", get_font(15), C.MIST,
                             (C.SCREEN_W - 96 - hokorobi * 20, 16), alpha=140)
            for i in range(hokorobi):
                draw_tear(frame, (C.SCREEN_W - 24 - i * 20, 26), 11, self.time, seed=i)
        shouki = self.st.get("shouki")
        if shouki < 100:
            bar = pygame.Rect(C.SCREEN_W - 196, 44, 160, 12)
            draw_text_shadow(frame, "正気", get_font(15), C.MIST,
                             (bar.x - 40, bar.y - 4), alpha=150)
            pygame.draw.rect(frame, (24, 26, 38), bar, border_radius=4)
            inner = bar.inflate(-4, -4)
            inner.width = int(inner.width * min(100, max(0, shouki)) / 100)
            if inner.width:
                ratio = shouki / 100
                col = C.MIST if ratio > 0.5 else (C.WARM if ratio > 0.25 else C.DEEP_RED)
                pygame.draw.rect(frame, col, inner, border_radius=3)
            pygame.draw.rect(frame, C.MIST, bar, width=1, border_radius=4)

        if self.hint_time > 0:
            alpha = int(150 * min(1.0, self.hint_time / 1.5))
            hint = "Z / クリック：進む　　B：履歴　　ESC：メニュー　　F5/F9：クイックセーブ・ロード"
            img = font.render(hint, True, C.MIST)
            img.set_alpha(alpha)
            frame.blit(img, (22, C.SCREEN_H - 24))
        if self.toast_time > 0:
            alpha = int(230 * min(1.0, self.toast_time / 0.6))
            rect = pygame.Rect(0, 0, get_font(19).size(self.toast)[0] + 40, 40)
            rect.center = (C.SCREEN_W // 2, 54)
            panel(frame, rect, (20, 24, 38), alpha=int(alpha * 0.85), radius=10,
                  border=C.GOLD, border_alpha=int(alpha * 0.5))
            draw_text_center(frame, self.toast, get_font(19), C.PAPER, rect.center, alpha=alpha)
