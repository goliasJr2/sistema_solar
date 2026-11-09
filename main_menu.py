"""
===============================================================================
Módulo: main_menu.py
Descrição: Ecrã principal (menu de entrada) apresentado antes do simulador.
  - Usa a captura de ecrã existente na raiz do projeto como fundo (identidade
    visual da Universidade Eduardo Mondlane).
  - Dois botões no mesmo estilo da UI do simulador (Pillow -> textura OpenGL):
      * START    : arranca o Simulador Astronómico 3D.
      * SETTINGS : abre o Manual do Utilizador, Comandos e Definições.
  - Janela GLFW + contexto OpenGL 3.3 Core autónomos; não interfere com o loop
    da simulação. run() devolve as definições escolhidas (Start) ou None (sair).
===============================================================================
"""

import ctypes
import textwrap
from pathlib import Path
from typing import Dict, Optional, Tuple

import glm
import glfw
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from OpenGL.GL import (
    glGenVertexArrays,
    glBindVertexArray,
    glGenBuffers,
    glBindBuffer,
    glBufferData,
    glVertexAttribPointer,
    glEnableVertexAttribArray,
    glDrawArrays,
    glGenTextures,
    glBindTexture,
    glTexImage2D,
    glTexParameteri,
    glActiveTexture,
    glDeleteVertexArrays,
    glDeleteBuffers,
    glDeleteTextures,
    glEnable,
    glDisable,
    glBlendFunc,
    glClearColor,
    glClear,
    glViewport,
    GL_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    GL_FLOAT,
    GL_TRIANGLES,
    GL_FALSE,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_CLAMP_TO_EDGE,
    GL_LINEAR,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_DEPTH_TEST,
    GL_COLOR_BUFFER_BIT,
)

from shader import Shader


# Paleta institucional (verde UEM) coerente com a captura de ecrã
GREEN = (0, 150, 75, 255)
GREEN_DARK = (0, 105, 52, 255)
GREEN_LIGHT = (0, 175, 88, 255)
GOLD = (240, 185, 25, 255)
BG_COLOR = (245, 246, 250, 255)
INK = (35, 45, 40, 255)


class MainMenu:
    """Ecrã principal com Start e Settings, renderizado em OpenGL 2D (Pillow)."""

    def __init__(self, base_dir: Path, width: int = 1280, height: int = 720):
        self.base_dir = Path(base_dir)
        self.width = width
        self.height = height
        self.window = None
        self.shader: Optional[Shader] = None

        self.state = "menu"            # "menu" | "settings"
        self.tab = "manual"            # "manual" | "comandos" | "definicoes"
        self.settings: Dict[str, bool] = {
            "show_orbits": True,
            "show_starfield": True,
            "show_galaxy": True,
        }

        self.mouse: Tuple[float, float] = (-1.0, -1.0)
        self.hover: Optional[str] = None
        self.rects: Dict[str, Tuple[int, int, int, int]] = {}
        self._started = False

        self._bg_original: Optional[Image.Image] = None
        self._bg_scaled: Optional[Image.Image] = None
        self._bg_size: Tuple[int, int] = (0, 0)
        self._load_background()
        self._load_fonts()

        self.vao = 0
        self.vbo = 0
        self.texture_id = 0

    # ------------------------------------------------------------------ assets
    def _load_background(self) -> None:
        """Carrega a captura de ecrã da raiz como fundo do menu (com fallback)."""
        candidates = sorted(self.base_dir.glob("Captura*.png"))
        exact = self.base_dir / "Captura de ecrã 2026-11-09 150316.png"
        path = exact if exact.exists() else (candidates[0] if candidates else None)
        if path is not None:
            try:
                self._bg_original = Image.open(path).convert("RGBA")
            except Exception:
                self._bg_original = None

    def _load_fonts(self) -> None:
        def font(size: int, bold: bool = False):
            name = "arialbd.ttf" if bold else "arial.ttf"
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                try:
                    return ImageFont.truetype("arial.ttf", size)
                except Exception:
                    return ImageFont.load_default()

        self.font_button = font(22, bold=True)
        self.font_title = font(26, bold=True)
        self.font_tab = font(15, bold=True)
        self.font_head = font(16, bold=True)
        self.font_text = font(14)
        self.font_small = font(12)

    def _background(self) -> Image.Image:
        """Fundo escalado para a janela (cache por dimensão); fallback procedural."""
        if self._bg_size == (self.width, self.height) and self._bg_scaled is not None:
            return self._bg_scaled
        if self._bg_original is not None:
            bg = self._bg_original.resize((self.width, self.height), Image.LANCZOS)
        else:
            bg = Image.new("RGBA", (self.width, self.height), BG_COLOR)
            d = ImageDraw.Draw(bg)
            d.text((self.width // 2, int(self.height * 0.30)),
                   "UNIVERSIDADE EDUARDO MONDLANE",
                   fill=GREEN_DARK, font=self.font_head, anchor="mm")
            d.text((self.width // 2, int(self.height * 0.42)),
                   "Simulador Astronomico Inteligente",
                   fill=GREEN, font=self.font_title, anchor="mm")
        self._bg_scaled = bg
        self._bg_size = (self.width, self.height)
        return bg

    # --------------------------------------------------------------------- GL
    def _init_gl(self) -> None:
        shaders_dir = self.base_dir / "shaders"
        self.shader = Shader(shaders_dir / "ui.vert", shaders_dir / "ui.frag")

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 6 * 4 * 4, None, GL_STATIC_DRAW)
        stride = 4 * 4
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)
        glBindVertexArray(0)

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def _render_overlay(self, overlay: Image.Image) -> None:
        """Envia a imagem Pillow para a textura e desenha o quad de ecrã inteiro."""
        img_data = overlay.tobytes()
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.shader.use()
        ortho = glm.ortho(0.0, float(self.width), float(self.height), 0.0, -1.0, 1.0)
        self.shader.set_mat4("uOrthoProjection", ortho)
        self.shader.set_float("uOpacity", 1.0)

        quad = np.array([
            0.0, float(self.height), 0.0, 1.0,
            float(self.width), float(self.height), 1.0, 1.0,
            float(self.width), 0.0, 1.0, 0.0,
            0.0, float(self.height), 0.0, 1.0,
            float(self.width), 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
        ], dtype=np.float32)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        self.shader.set_int("uTexture", 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

    # ---------------------------------------------------------------- drawing
    def _button(self, draw: ImageDraw.ImageDraw, key: str, cx: int, cy: int,
                w: int, h: int, label: str, primary: bool = False) -> None:
        x0, y0 = cx - w // 2, cy - h // 2
        x1, y1 = x0 + w, y0 + h
        hovered = self.hover == key
        if primary:
            fill = GREEN_LIGHT if hovered else GREEN
            outline, text_col = GREEN_DARK, (255, 255, 255, 255)
        else:
            fill = (232, 247, 238, 255) if hovered else (255, 255, 255, 240)
            outline, text_col = GREEN, GREEN_DARK
        draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=fill,
                               outline=outline, width=3 if hovered else 2)
        draw.text((cx, cy), label, fill=text_col, font=self.font_button, anchor="mm")
        self.rects[key] = (x0, y0, x1, y1)

    def _draw_menu(self, draw: ImageDraw.ImageDraw) -> None:
        cx = self.width // 2
        y_start = int(self.height * 0.66)
        self._button(draw, "start", cx, y_start, 320, 60, "START", primary=True)
        self._button(draw, "settings", cx, y_start + 82, 320, 60, "SETTINGS")
        draw.text((cx, self.height - 26),
                  "Universidade Eduardo Mondlane  |  Computação Gráfica — Grupo 1",
                  fill=(120, 130, 125, 255), font=self.font_small, anchor="mm")

    def _draw_settings(self, draw: ImageDraw.ImageDraw) -> None:
        pw = min(940, self.width - 40)
        ph = min(640, self.height - 40)
        x0 = (self.width - pw) // 2
        y0 = (self.height - ph) // 2
        x1, y1 = x0 + pw, y0 + ph

        draw.rounded_rectangle([x0, y0, x1, y1], radius=16,
                               fill=(255, 255, 255, 252), outline=GREEN, width=2)
        draw.rounded_rectangle([x0, y0, x1, y0 + 52], radius=16, fill=GREEN)
        draw.rectangle([x0, y0 + 30, x1, y0 + 52], fill=GREEN)
        draw.text((x0 + 22, y0 + 26), "MANUAL & DEFINIÇÕES",
                  fill=(255, 255, 255, 255), font=self.font_title, anchor="lm")

        # Separadores (tabs)
        tabs = [("manual", "MANUAL"), ("comandos", "COMANDOS"), ("definicoes", "DEFINIÇÕES")]
        tab_w = 150
        tx = x0 + 22
        for tab_key, label in tabs:
            active = self.tab == tab_key
            hovered = self.hover == f"tab_{tab_key}"
            r = [tx, y0 + 64, tx + tab_w, y0 + 98]
            fill = GREEN if active else ((232, 247, 238, 255) if hovered else (242, 244, 243, 255))
            draw.rounded_rectangle(r, radius=8, fill=fill, outline=GREEN, width=1)
            draw.text(((r[0] + r[2]) // 2, (r[1] + r[3]) // 2), label,
                      fill=(255, 255, 255, 255) if active else GREEN_DARK,
                      font=self.font_tab, anchor="mm")
            self.rects[f"tab_{tab_key}"] = tuple(r)
            tx += tab_w + 12

        cy = y0 + 116
        if self.tab == "manual":
            self._draw_manual(draw, x0 + 26, cy, x1 - 26)
        elif self.tab == "comandos":
            self._draw_commands(draw, x0 + 26, cy, x1 - 26)
        else:
            self._draw_definitions(draw, x0 + 26, cy, x1 - 26)

        # Botão voltar
        self._button(draw, "back", x0 + 130, y1 - 34, 220, 44, "VOLTAR AO MENU")

    def _draw_manual(self, draw: ImageDraw.ImageDraw, lx: int, cy: int, rx: int) -> None:
        draw.text((lx, cy), "Manual do Utilizador", fill=GREEN_DARK, font=self.font_head)
        cy += 28
        paragraphs = [
            "1. Prima START para carregar e iniciar o Simulador Astronómico 3D.",
            "2. Navegue pelo espaço com o rato (arrastar para orbitar, roda para zoom) "
            "e pelas teclas W/A/S/D + Q/E. SHIFT ativa a propulsão turbo.",
            "3. Selecione um planeta clicando nele ou pelas teclas [1] a [9]. "
            "O painel lateral mostra a ficha astronómica completa.",
            "4. Use o botão 'Saber Mais' no painel para o apresentador 3D narrar "
            "factos sobre o planeta selecionado.",
            "5. Explore os módulos cósmicos (buracos negros, cometa, asteroides, "
            "galáxia) com as teclas indicadas no separador COMANDOS.",
            "6. Prima [F1] dentro do simulador para a ajuda completa e [ESC] para sair.",
        ]
        width_chars = max(40, int((rx - lx) / 7.2))
        for p in paragraphs:
            for line in textwrap.wrap(p, width=width_chars):
                draw.text((lx, cy), line, fill=INK, font=self.font_text)
                cy += 19
            cy += 8

    def _draw_commands(self, draw: ImageDraw.ImageDraw, lx: int, cy: int, rx: int) -> None:
        draw.text((lx, cy), "Comandos de Teclado e Rato", fill=GREEN_DARK, font=self.font_head)
        cy += 26
        cmds = [
            ("Rato Esq. + Arrastar", "Rotação orbital da câmara"),
            ("Roda do Rato", "Zoom (aproximar / afastar)"),
            ("W/A/S/D + Q/E", "Voar pelo espaço / subir / descer"),
            ("SHIFT", "Propulsão interestelar turbo"),
            ("[1]..[9] / Clique", "Selecionar planeta / Sol"),
            ("[TAB]", "Ciclar para o próximo planeta"),
            ("[ESPAÇO] / [R]", "Pausar / Reiniciar a simulação"),
            ("[+ / -]", "Acelerar / desacelerar o tempo"),
            ("[O] [N] [V]", "Órbitas / Estrelas / Galáxia"),
            ("[B] [C] [L] [M]", "Asteroides / Cometa / Satélites / Meteoros"),
            ("[G] / [ALT]", "Focar / frente a frente com buraco negro"),
            ("[F2]..[F4] / ENTER", "Escalas: Galáxia / Região / Sistema / Superfície"),
            ("[I] / [F1]", "Painel de informações / Ajuda"),
            ("[K] [U] [X]", "Personagem / Mudo / Fechar guia"),
        ]
        for key, desc in cmds:
            draw.text((lx, cy), key, fill=GREEN_DARK, font=self.font_small)
            draw.text((lx + 175, cy), desc, fill=INK, font=self.font_small)
            cy += 19

    def _draw_definitions(self, draw: ImageDraw.ImageDraw, lx: int, cy: int, rx: int) -> None:
        draw.text((lx, cy), "Definições Iniciais", fill=GREEN_DARK, font=self.font_head)
        cy += 26
        draw.text((lx, cy), "Preferências aplicadas ao iniciar o simulador (também ajustáveis em jogo).",
                  fill=(110, 120, 115, 255), font=self.font_small)
        cy += 30
        toggles = [
            ("show_orbits", "Órbitas dos planetas", "Tecla [O]"),
            ("show_starfield", "Campo de estrelas de fundo", "Tecla [N]"),
            ("show_galaxy", "Galáxia Via Láctea", "Tecla [V]"),
        ]
        for key, label, hint in toggles:
            draw.text((lx, cy + 4), label, fill=INK, font=self.font_text)
            draw.text((lx, cy + 23), hint, fill=(130, 140, 135, 255), font=self.font_small)
            on = self.settings[key]
            bw, bh = 110, 34
            bx1 = rx - 10
            bx0 = bx1 - bw
            by0 = cy
            hovered = self.hover == f"toggle_{key}"
            fill = GREEN if on else (210, 214, 212, 255)
            if hovered:
                fill = GREEN_LIGHT if on else (190, 196, 192, 255)
            r = [bx0, by0, bx1, by0 + bh]
            draw.rounded_rectangle(r, radius=8, fill=fill, outline=GREEN_DARK, width=1)
            draw.text(((bx0 + bx1) // 2, by0 + bh // 2), "ON" if on else "OFF",
                      fill=(255, 255, 255, 255) if on else (70, 80, 75, 255),
                      font=self.font_tab, anchor="mm")
            self.rects[f"toggle_{key}"] = tuple(r)
            cy += 56

    # --------------------------------------------------------------- callbacks
    def _on_cursor(self, window, xpos: float, ypos: float) -> None:
        self.mouse = (xpos, ypos)

    def _on_mouse(self, window, button: int, action: int, mods: int) -> None:
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self._handle_click(self.mouse[0], self.mouse[1])

    def _on_key(self, window, key: int, scancode: int, action: int, mods: int) -> None:
        if action != glfw.PRESS:
            return
        if key == glfw.KEY_ESCAPE:
            if self.state == "settings":
                self.state = "menu"
            else:
                glfw.set_window_should_close(window, True)
        elif key == glfw.KEY_ENTER and self.state == "menu":
            self._started = True
            glfw.set_window_should_close(window, True)

    def _on_resize(self, window, width: int, height: int) -> None:
        self.width = max(1, width)
        self.height = max(1, height)
        glViewport(0, 0, self.width, self.height)

    def _handle_click(self, x: float, y: float) -> None:
        def hit(key: str) -> bool:
            r = self.rects.get(key)
            return bool(r and r[0] <= x <= r[2] and r[1] <= y <= r[3])

        if self.state == "menu":
            if hit("start"):
                self._started = True
                glfw.set_window_should_close(self.window, True)
            elif hit("settings"):
                self.state = "settings"
        else:
            if hit("back"):
                self.state = "menu"
            for t in ("manual", "comandos", "definicoes"):
                if hit(f"tab_{t}"):
                    self.tab = t
            for k in self.settings:
                if hit(f"toggle_{k}"):
                    self.settings[k] = not self.settings[k]

    def _update_hover(self) -> None:
        x, y = self.mouse
        self.hover = None
        for key, (x0, y0, x1, y1) in self.rects.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                self.hover = key
                break

    # --------------------------------------------------------------------- run
    def run(self) -> Optional[Dict[str, bool]]:
        """Corre o menu. Devolve as definições (Start) ou None (utilizador saiu)."""
        if not glfw.init():
            raise RuntimeError("[Menu] Não foi possível inicializar o GLFW.")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.SAMPLES, 4)

        self.window = glfw.create_window(
            self.width, self.height, "Simulador Astronomico Inteligente — Menu", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("[Menu] Falha ao criar a janela OpenGL 3.3 Core.")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        glfw.set_cursor_pos_callback(self.window, self._on_cursor)
        glfw.set_mouse_button_callback(self.window, self._on_mouse)
        glfw.set_key_callback(self.window, self._on_key)
        glfw.set_framebuffer_size_callback(self.window, self._on_resize)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.96, 0.965, 0.98, 1.0)
        self._init_gl()

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self._update_hover()

            overlay = self._background().copy()
            draw = ImageDraw.Draw(overlay)
            self.rects = {}
            if self.state == "menu":
                self._draw_menu(draw)
            else:
                self._draw_settings(draw)

            glClear(GL_COLOR_BUFFER_BIT)
            self._render_overlay(overlay)
            glfw.swap_buffers(self.window)

        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        glDeleteTextures(1, [self.texture_id])
        glfw.destroy_window(self.window)
        glfw.terminate()

        return dict(self.settings) if self._started else None