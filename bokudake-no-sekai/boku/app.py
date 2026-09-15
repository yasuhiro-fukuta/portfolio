# -*- coding: utf-8 -*-
"""アプリ本体。ウィンドウ、メインループ、シーンのスタック管理。"""

from __future__ import annotations

import datetime as _dt
import os
import sys

import pygame

from . import config as C
from .state import GameState

# 入力の意味づけ（キーボードは複数受け付ける）
CONFIRM_KEYS = (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
CANCEL_KEYS = (pygame.K_x, pygame.K_ESCAPE, pygame.K_BACKSPACE)
UP_KEYS = (pygame.K_UP, pygame.K_w, pygame.K_k)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s, pygame.K_j)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a, pygame.K_h)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d, pygame.K_l)


class Scene:
    """シーンの基底クラス。"""

    def __init__(self, app: "App"):
        self.app = app
        self.time = 0.0

    # ライフサイクル
    def on_enter(self):
        pass

    def on_resume(self, result=None):
        """上に積まれたシーンが終わって戻ってきたときに呼ばれる。"""

    def on_exit(self):
        pass

    # 毎フレーム
    def handle_event(self, event: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, surf: pygame.Surface):
        pass


class App:
    def __init__(self, headless: bool = False):
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        pygame.init()
        try:                                   # 音が出せない環境でも動かす
            pygame.mixer.init()
        except Exception:                      # noqa: BLE001  ドライバ不在など
            pass

        self.headless = headless
        self.screen = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        pygame.display.set_caption(f"{C.TITLE}　- {C.VERSION}")
        self.canvas = pygame.Surface((C.SCREEN_W, C.SCREEN_H)).convert()
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = False

        self.state = GameState()
        self.scenes: list[Scene] = []

    # ---- シーン操作 -------------------------------------------------------
    @property
    def scene(self) -> Scene | None:
        return self.scenes[-1] if self.scenes else None

    def push(self, scene: Scene):
        self.scenes.append(scene)
        scene.on_enter()

    def pop(self, result=None):
        if not self.scenes:
            return
        old = self.scenes.pop()
        old.on_exit()
        if self.scenes:
            self.scenes[-1].on_resume(result)
        else:
            self.running = False

    def replace(self, scene: Scene):
        while self.scenes:
            self.scenes.pop().on_exit()
        self.push(scene)

    def quit(self):
        self.running = False

    # ---- その他 -----------------------------------------------------------
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN | pygame.SCALED if self.fullscreen else 0
        self.screen = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H), flags)

    def screenshot(self) -> str:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "screenshots")
        os.makedirs(base, exist_ok=True)
        name = _dt.datetime.now().strftime("shot_%Y%m%d_%H%M%S.png")
        path = os.path.join(base, name)
        pygame.image.save(self.canvas, path)
        return path

    def mouse_pos(self) -> tuple[int, int]:
        """ウィンドウ拡大にも耐える座標変換。"""
        mx, my = pygame.mouse.get_pos()
        w, h = self.screen.get_size()
        return int(mx * C.SCREEN_W / max(1, w)), int(my * C.SCREEN_H / max(1, h))

    # ---- メインループ -----------------------------------------------------
    def run(self, max_frames: int | None = None):
        frames = 0
        while self.running:
            dt = min(0.05, self.clock.tick(C.FPS) / 1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F12:
                    print("screenshot:", self.screenshot())
                elif self.scene:
                    self.scene.handle_event(event)

            if self.scene:
                self.scene.time += dt
                self.scene.update(dt)
                self.canvas.fill(C.INK)
                self.scene.draw(self.canvas)

            self.screen.blit(
                self.canvas if self.screen.get_size() == self.canvas.get_size()
                else pygame.transform.smoothscale(self.canvas, self.screen.get_size()),
                (0, 0))
            pygame.display.flip()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        pygame.quit()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    headless = "--headless" in argv
    app = App(headless=headless)
    from . import meta
    from .scenes.title import TitleScene
    if meta.notice_seen() or headless:
        app.push(TitleScene(app))
    else:
        from .scenes.notice import NoticeScene
        app.push(NoticeScene(app))
    app.run()
    return 0
