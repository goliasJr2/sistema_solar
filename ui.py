"""
===============================================================================
Módulo: ui.py
Descrição: Interface de utilizador 2D moderna com painel de informações dos planetas.
Conceitos aplicados:
  - Projeção Ortográfica 2D (glm.ortho) para renderização em coordenadas de ecrã (pixels).
  - Buffer de textura dinâmica RGBA gerado com Pillow e atualizado no OpenGL.
  - Painel de Informações Planetárias (Obrigatório 7):
      * Diâmetro, Massa, Gravidade, Período de Rotação, Translação, Temperatura, Luas, Atmosfera.
  - Controlo de Velocidade Orbital (Obrigatório 6):
      * Indicador e slider de velocidade de 0x a 1.000.000x, data simulada em dias e anos.
  - Ecrã de Ajuda (F1) com comandos e créditos completos dos recursos.
===============================================================================
"""

from typing import Dict, Optional, Tuple, Any
import ctypes
import numpy as np
import glm
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
    glTexSubImage2D,
    glTexParameteri,
    glActiveTexture,
    glDeleteVertexArrays,
    glDeleteBuffers,
    glDeleteTextures,
    glEnable,
    glDisable,
    glBlendFunc,
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
)

from shader import Shader


class UIManager:
    """Gere a interface gráfica do utilizador em 2D sobreposta à cena 3D."""

    def __init__(self, screen_width: int, screen_height: int, shader: Shader):
        self.width = screen_width
        self.height = screen_height
        self.shader = shader

        self.selected_body_data: Optional[dict] = None
        self.presenter_data: Optional[dict] = None  # Personagem apresentador (characters.json)
        self.show_help: bool = False
        self.show_info_panel: bool = True

        # Coordenadas do botão "Saber Mais" em espaço de ecrã (x0, y0, x1, y1)
        self.learn_more_btn_rect: tuple = (0, 0, 0, 0)

        # Textura do painel de informação lateral (360 x 520 px)
        self.panel_width = 380
        self.panel_height = 540
        self.panel_x = 20
        self.panel_y = 60

        # Textura da barra superior (largura x 45 px)
        self.hud_height = 45

        # Fontes Pillow padrão seguras e nítidas
        try:
            self.font_title = ImageFont.truetype("arial.ttf", 22)
            self.font_subtitle = ImageFont.truetype("arial.ttf", 15)
            self.font_text = ImageFont.truetype("arial.ttf", 13)
            self.font_small = ImageFont.truetype("arial.ttf", 11)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_text = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

        # Configuração do Quad 2D em OpenGL (2 triângulos = 6 vértices)
        self.vao = 0
        self.vbo = 0
        self.texture_id = 0
        self._init_gl_buffers()

    def _init_gl_buffers(self) -> None:
        """Cria o VAO e VBO para renderizar quads 2D em espaço de ecrã."""
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # Reserva buffer dinâmico de 6 vértices x 4 floats (pos_x, pos_y, uv_u, uv_v)
        glBufferData(GL_ARRAY_BUFFER, 6 * 4 * 4, None, GL_STATIC_DRAW)

        stride = 4 * 4
        # Atributo 0: Pos 2D
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        # Atributo 1: UV 2D
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

        # Textura 2D RGBA para transferência dos desenhos do Pillow
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def resize(self, width: int, height: int) -> None:
        """Atualiza dimensões de ecrã para projeção ortográfica."""
        self.width = width
        self.height = height

    def set_selected_body(self, data: Optional[dict]) -> None:
        """Atualiza os dados astronómicos do corpo celeste selecionado."""
        self.selected_body_data = data
        self.presenter_data = None  # o main.py define o apresentador logo a seguir (set_presenter)
        if data is not None:
            self.show_info_panel = True

    def set_presenter(self, presenter: Optional[dict]) -> None:
        """Define o personagem apresentador do corpo selecionado (entrada de characters.json)."""
        self.presenter_data = presenter

    def toggle_help(self) -> None:
        """Alterna a visualização da tela de ajuda (Tecla F1)."""
        self.show_help = not self.show_help

    def toggle_info_panel(self) -> None:
        """Alterna o painel lateral de informações (Tecla I)."""
        self.show_info_panel = not self.show_info_panel

    def is_learn_more_clicked(self, mouse_x: float, mouse_y: float) -> bool:
        """Verifica se as coordenadas do rato estão dentro do botão 'Saber Mais'.

        A origem (0,0) do GLFW é no canto superior esquerdo, igual ao Pillow,
        pelo que as coordenadas são diretamente comparáveis.
        """
        x0, y0, x1, y1 = self.learn_more_btn_rect
        return x0 <= mouse_x <= x1 and y0 <= mouse_y <= y1

    def draw(
        self,
        is_paused: bool,
        time_scale: float,
        simulated_days: float,
        fps: float,
        show_orbits: bool,
        active_modules: Optional[dict] = None,
    ) -> None:
        """Desenha a interface gráfica completa sobreposta na tela."""
        # Cria uma imagem Pillow transparente com as dimensões da janela
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 1. Barra Superior (HUD)
        self._draw_top_bar(draw, is_paused, time_scale, simulated_days, fps, show_orbits, active_modules)

        # 2. Alerta de Entrada na Área de Atuação de Buraco Negro
        if active_modules and active_modules.get("black_hole_alert"):
            self._draw_black_hole_warning(draw, active_modules["black_hole_alert"])

        # 3. Painel Lateral de Informações (Obrigatório 7)
        if self.show_info_panel and self.selected_body_data:
            self._draw_planet_info_panel(draw)

        # 4. Ecrã de Ajuda e Créditos (F1)
        if self.show_help:
            self._draw_help_screen(draw)

        # 5. Caixa de Fala do Guia Virtual 3D (Subtítulos / Apresentação)
        if active_modules and active_modules.get("guide_info"):
            self._draw_guide_speech_box(draw, active_modules["guide_info"])

        # Envia a imagem composta do Pillow para a textura OpenGL
        img_data = overlay.tobytes()
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        # Renderização do Quad de tela cheia com projeção ortográfica
        glDisable(GL_DEPTH_TEST)  # Garante que a interface fica sempre no topo da cena
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.shader.use()
        # Matriz Ortográfica: [0, width] x [0, height] com origem no canto superior esquerdo
        ortho = glm.ortho(0.0, float(self.width), float(self.height), 0.0, -1.0, 1.0)
        self.shader.set_mat4("uOrthoProjection", ortho)
        self.shader.set_float("uOpacity", 1.0)

        # Vértices cobrindo a janela inteira
        quad_data = np.array([
            # x, y, u, v
            0.0, float(self.height), 0.0, 1.0,
            float(self.width), float(self.height), 1.0, 1.0,
            float(self.width), 0.0, 1.0, 0.0,

            0.0, float(self.height), 0.0, 1.0,
            float(self.width), 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
        ], dtype=np.float32)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, GL_STATIC_DRAW)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        self.shader.set_int("uTexture", 0)

        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)

    def _draw_top_bar(
        self,
        draw: ImageDraw.ImageDraw,
        is_paused: bool,
        time_scale: float,
        simulated_days: float,
        fps: float,
        show_orbits: bool,
        active_modules: Optional[dict] = None,
    ) -> None:
        """Desenha a barra superior informativa com status, velocidade, data simulada e módulos."""
        # Fundo translúcido com gradiente escuro
        draw.rectangle([0, 0, self.width, self.hud_height], fill=(12, 16, 28, 220))
        draw.line([(0, self.hud_height), (self.width, self.hud_height)], fill=(45, 65, 110, 255), width=2)

        # Estado da Simulação
        status_text = "PAUSADO [ESPAÇO]" if is_paused else "A CORRER"
        status_color = (255, 90, 90) if is_paused else (80, 240, 140)
        draw.text((15, 12), f"● {status_text}", fill=status_color, font=self.font_subtitle)

        # Data Simulada
        years = simulated_days / 365.256
        time_str = f"Tempo: {simulated_days:.1f}d ({years:.2f}a)"
        draw.text((180, 14), time_str, fill=(230, 235, 245), font=self.font_text)

        # Velocidade Orbital
        vel_str = f"Vel: {time_scale:.1f}x [+/-]"
        draw.text((375, 14), vel_str, fill=(120, 200, 255), font=self.font_text)

        # Indicadores de Módulos Rápidos e Modo de Câmara
        if active_modules:
            cmode = active_modules.get("camera_mode", 2)
            mode_labels = {0: "EXPLORE [P]", 1: "FOLLOW [P]", 2: "FOCUS [P]"}
            mode_colors = {0: (255, 170, 70), 1: (80, 220, 255), 2: (120, 255, 150)}
            draw.text((505, 14), mode_labels.get(cmode, "FOCUS [P]"), fill=mode_colors.get(cmode, (120, 255, 150)), font=self.font_text)

            curr_x = 615
            mod_items = [
                ("Órb[O]", active_modules.get("orbits", True)),
                ("Est[N]", active_modules.get("starfield", True)),
                ("Ast[B]", active_modules.get("asteroids", True)),
                ("Com[C]", active_modules.get("comet", True)),
                ("Sat[L]", active_modules.get("satellites", True)),
                ("Met[M]", active_modules.get("meteors", True)),
                ("Gal[V]", active_modules.get("galaxy", True)),
            ]
            for label, active in mod_items:
                c = (90, 230, 150) if active else (130, 140, 155)
                draw.text((curr_x, 15), label, fill=c, font=self.font_small)
                curr_x += 46
        else:
            orbit_str = f"Órbitas: {'ON' if show_orbits else 'OFF'} [O]"
            draw.text((540, 14), orbit_str, fill=(200, 200, 210), font=self.font_text)

        # Ajuda e FPS no canto direito
        fps_str = f"FPS: {fps:.0f} | [F1] Ajuda"
        draw.text((self.width - 150, 14), fps_str, fill=(255, 215, 80), font=self.font_text)

    def _draw_black_hole_warning(self, draw: ImageDraw.ImageDraw, alert: dict) -> None:
        """Desenha o banner de alerta sci-fi de aproximação à área de atuação de um buraco negro."""
        alert_type = alert.get("type", "PROXIMITY")

        box_width = min(660, self.width - 40)
        box_height = 80
        x0 = (self.width - box_width) // 2
        y0 = self.hud_height + 14
        x1 = x0 + box_width
        y1 = y0 + box_height

        if alert_type == "FACE_TO_FACE":
            bg_col = (35, 12, 50, 240)
            border_col = (195, 80, 255, 255)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            draw.text((x0 + 18, y0 + 10), "👁 FRENTE A FRENTE COM O BURACO NEGRO", fill=(230, 180, 255), font=self.font_subtitle)
            name_str = f"Singularidade: {alert.get('name', 'Buraco Negro')}  |  Distância: {alert.get('distance', 0.0):.1f} UA"
            draw.text((x0 + 18, y0 + 32), name_str, fill=(255, 255, 255), font=self.font_text)
            sub_str = "Prima [ALT] para o próximo buraco negro (8 no total)  |  [0] Sistema Solar"
            draw.text((x0 + 18, y0 + 54), sub_str, fill=(210, 180, 250), font=self.font_small)

        elif alert_type == "DANGER":
            bg_col = (48, 8, 12, 240)
            border_col = (255, 45, 45, 255)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            draw.text((x0 + 18, y0 + 10), "⚠ ALERTA DE PERIGO: DISTORÇÃO ESPAÇO-TEMPORAL DETETADA!", fill=(255, 65, 65), font=self.font_subtitle)
            draw.text((x0 + 18, y0 + 32), "Horizonte de eventos iminente à sua frente no espaço profundo!", fill=(255, 230, 230), font=self.font_text)
            sec_held = alert.get("progress_sec", 0.0)
            rem = max(0.0, 5.0 - sec_held)
            sub_str = f"Mantenha premido [▲ Seta Cima] mais {rem:.1f}s para revelar  |  Prima [ALT] Frente a Frente"
            draw.text((x0 + 18, y0 + 54), sub_str, fill=(255, 175, 50), font=self.font_small)

        elif alert_type == "REVEALED":
            bg_col = (25, 18, 38, 235)
            border_col = (255, 185, 40, 255)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            draw.text((x0 + 18, y0 + 10), "🌌 BURACO NEGRO VISÍVEL À SUA FRENTE!", fill=(255, 215, 60), font=self.font_subtitle)
            name_str = f"Singularidade: {alert.get('name', 'Cygnus X-1')}  |  Distância: {alert.get('distance', 0.0):.1f} UA"
            draw.text((x0 + 18, y0 + 32), name_str, fill=(245, 245, 250), font=self.font_text)
            sub_str = "Prima [ALT] agora para ficar Frente a Frente com o Buraco Negro!"
            draw.text((x0 + 18, y0 + 54), sub_str, fill=(255, 230, 150), font=self.font_small)

        elif alert_type == "WORMHOLE_PULL":
            bg_col = (45, 6, 25, 245)
            border_col = (255, 30, 80, 255)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            draw.text((x0 + 18, y0 + 10), "⚠ VÓRTICE DE ATRAÇÃO GRAVITACIONAL — BURACO DE MINHOCA!", fill=(255, 55, 100), font=self.font_subtitle)
            grav_pct = int(alert.get("warp_factor", 0.5) * 100)
            name_str = f"Singularidade: {alert.get('name', 'Buraco Negro')}  |  Gravidade Relativística: {grav_pct}%  |  Distância: {alert.get('distance', 0.0):.1f} UA"
            draw.text((x0 + 18, y0 + 32), name_str, fill=(255, 230, 240), font=self.font_text)
            sub_str = "🔥 MANTENHA PREMIDO [SHIFT] PARA ACIONAR A PROPULSÃO WARP DE FUGA!"
            draw.text((x0 + 18, y0 + 54), sub_str, fill=(255, 220, 50), font=self.font_small)

        elif alert_type == "WARP_ESCAPE":
            bg_col = (8, 30, 48, 245)
            border_col = (40, 220, 255, 255)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            draw.text((x0 + 18, y0 + 10), "⚡ PROPULSÃO WARP DE FUGA ATIVA [SHIFT]", fill=(50, 230, 255), font=self.font_subtitle)
            name_str = f"A romper o horizonte de eventos de {alert.get('name', 'Buraco Negro')}!  |  Distância: {alert.get('distance', 0.0):.1f} UA"
            draw.text((x0 + 18, y0 + 32), name_str, fill=(220, 250, 255), font=self.font_text)
            sub_str = "Motores a impulsão máxima de escape relativístico contra o buraco de minhoca!"
            draw.text((x0 + 18, y0 + 54), sub_str, fill=(160, 255, 200), font=self.font_small)

        elif alert_type == "OUTSIDE_CHARGING":
            box_height = 54
            y1 = y0 + box_height
            bg_col = (12, 18, 32, 220)
            border_col = (70, 140, 245, 220)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=bg_col, outline=border_col, width=1)
            sec_held = alert.get("progress_sec", 0.0)
            draw.text((x0 + 18, y0 + 8), "🚀 SAÍDA DO SISTEMA SOLAR EM CURSO", fill=(100, 185, 255), font=self.font_subtitle)
            sub_str = f"Avanço no vazio cósmico: {sec_held:.1f}s / 5.0s (Mantenha premido [▲ Seta Cima] para acionar alerta)"
            draw.text((x0 + 18, y0 + 29), sub_str, fill=(200, 220, 255), font=self.font_small)

        else:
            is_crit = alert.get("is_critical", False)
            bg_col = (48, 8, 12, 235) if is_crit else (26, 12, 18, 220)
            border_col = (255, 45, 45, 255) if is_crit else (255, 145, 40, 240)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=bg_col, outline=border_col, width=2)
            title = "⚠ ALERTA CRÍTICO: HORIZONTE DE EVENTOS PRÓXIMO!" if is_crit else "⚠ AVISO: CAMPO DE ATRAÇÃO GRAVITACIONAL"
            title_col = (255, 65, 65) if is_crit else (255, 185, 45)
            draw.text((x0 + 18, y0 + 10), title, fill=title_col, font=self.font_subtitle)
            name_str = f"Singularidade Detetada: {alert.get('name', 'Buraco Negro')}"
            draw.text((x0 + 18, y0 + 31), name_str, fill=(245, 245, 250), font=self.font_text)
            dist = alert.get('distance', 0.0)
            status_txt = "FORÇA DE MARÉ CRÍTICA — ATRAÇÃO ATIVA!" if is_crit else "Aproximação ao espaço exterior (Prima [ALT] Frente a Frente)"
            sub_str = f"Distância: {dist:.1f} UA  |  {status_txt}"
            sub_col = (255, 140, 140) if is_crit else (220, 180, 130)
            draw.text((x0 + 18, y0 + 51), sub_str, fill=sub_col, font=self.font_small)

    def _draw_planet_info_panel(self, draw: ImageDraw.ImageDraw) -> None:
        """Desenha o painel lateral com a ficha técnica astronómica completa do corpo selecionado."""
        data = self.selected_body_data
        if not data:
            return

        presenter = self.presenter_data
        x0, y0 = self.panel_x, self.panel_y
        x1, y1 = x0 + self.panel_width, y0 + self.panel_height + (66 if presenter else 0)

        # Caixa de fundo com cantos arredondados e transparência moderna
        draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=(10, 14, 25, 230), outline=(50, 80, 150, 255), width=2)

        # Cabeçalho com o Nome do Planeta
        name = data.get("name", "Corpo Celeste")
        draw.text((x0 + 20, y0 + 16), name.upper(), fill=(255, 255, 255), font=self.font_title)

        subtitle = "Ficha Astronómica e Dados Físicos Reais"
        draw.text((x0 + 20, y0 + 46), subtitle, fill=(130, 160, 210), font=self.font_small)
        draw.line([(x0 + 20, y0 + 64), (x1 - 20, y0 + 64)], fill=(40, 65, 110), width=1)

        # Linhas de Informação Obrigatórias do Enunciado
        items = [
            ("Diâmetro Equatorial:", f"{data.get('radius_km', 0) * 2:,.1f} km"),
            ("Massa Estimada:", str(data.get("mass_kg", "N/A"))),
            ("Gravidade Superficial:", str(data.get("gravity", "N/A"))),
            ("Período de Rotação:", f"{abs(data.get('rotation_period_hours', 0)):.2f} horas {'(Retrógrado)' if data.get('rotation_period_hours', 0) < 0 else ''}"),
            ("Inclinação Axial:", f"{data.get('axial_tilt_deg', 0):.2f}°"),
            ("Período Orbital:", f"{data.get('orbital_period_days', 0):.2f} dias"),
            ("Semi-Eixo Maior (Distância):", f"{data.get('distance_au', 0):.3f} UA"),
            ("Excentricidade Orbital:", f"{data.get('eccentricity', 0):.4f}"),
            ("Temperatura Média:", str(data.get("temperature", "N/A"))),
            ("Número de Luas:", f"{data.get('moons_count', 0)} luas conhecidas"),
        ]

        curr_y = y0 + 75
        for label, val in items:
            draw.text((x0 + 20, curr_y), label, fill=(150, 175, 215), font=self.font_small)
            draw.text((x0 + 20, curr_y + 14), val, fill=(245, 245, 250), font=self.font_text)
            curr_y += 36

        # Atmosfera
        draw.line([(x0 + 20, curr_y + 4), (x1 - 20, curr_y + 4)], fill=(40, 65, 110), width=1)
        draw.text((x0 + 20, curr_y + 12), "Composição Atmosférica:", fill=(150, 175, 215), font=self.font_small)
        atmos = str(data.get("atmosphere", "N/A"))
        draw.text((x0 + 20, curr_y + 28), atmos, fill=(120, 220, 180), font=self.font_small)

        # Personagem apresentador do planeta (characters.py / characters.json)
        if presenter:
            py = curr_y + 50
            draw.line([(x0 + 20, py), (x1 - 20, py)], fill=(40, 65, 110), width=1)
            draw.text((x0 + 20, py + 8), "Apresentador:", fill=(150, 175, 215), font=self.font_small)
            draw.text((x0 + 110, py + 6), str(presenter.get("character", "")), fill=(255, 210, 120), font=self.font_text)
            tagline = str(presenter.get("tagline") or "")
            # Quebra simples da frase em linhas que cabem no painel
            lines, line = [], ""
            for word in tagline.split():
                trial = f"{line} {word}".strip()
                if draw.textlength(trial, font=self.font_small) > self.panel_width - 40 and line:
                    lines.append(line)
                    line = word
                else:
                    line = trial
            if line:
                lines.append(line)
            for i, ln in enumerate(lines[:3]):
                draw.text((x0 + 20, py + 28 + i * 14), ln, fill=(225, 225, 235), font=self.font_small)

        # Botão "🔭 Saber Mais" — abre o Guia Virtual 3D sobre o planeta selecionado
        btn_w, btn_h = 180, 34
        btn_x0 = x0 + (self.panel_width - btn_w) // 2
        btn_y0 = y1 - btn_h - 12
        btn_x1 = btn_x0 + btn_w
        btn_y1 = btn_y0 + btn_h
        draw.rounded_rectangle(
            [btn_x0, btn_y0, btn_x1, btn_y1],
            radius=8,
            fill=(20, 60, 140, 240),
            outline=(80, 160, 255, 255),
            width=2,
        )
        draw.text(
            (btn_x0 + btn_w // 2, btn_y0 + btn_h // 2),
            "🔭 Saber Mais",
            fill=(255, 255, 255),
            font=self.font_text,
            anchor="mm",
        )
        # Guardar coordenadas do botão em espaço de ecrã para deteção de clique
        self.learn_more_btn_rect = (btn_x0, btn_y0, btn_x1, btn_y1)

    def _draw_help_screen(self, draw: ImageDraw.ImageDraw) -> None:
        """Desenha a janela central de Ajuda (F1) com todos os comandos e créditos."""
        w, h = 740, 600
        x0 = (self.width - w) // 2
        y0 = (self.height - h) // 2
        x1, y1 = x0 + w, y0 + h

        # Fundo escuro com contorno ciano
        draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(8, 12, 22, 248), outline=(70, 140, 230, 255), width=2)

        # Título
        draw.text((x0 + 25, y0 + 14), "SIMULADOR ASTRONÓMICO INTELIGENTE 3D", fill=(255, 215, 80), font=self.font_title)
        draw.text((x0 + 25, y0 + 42), "Computação Gráfica — Grupo 1  |  OpenGL 3.3 Core Profile", fill=(160, 190, 230), font=self.font_subtitle)
        draw.line([(x0 + 25, y0 + 65), (x1 - 25, y0 + 65)], fill=(45, 75, 130), width=1)

        # Secção 1 — Câmara e Rato
        cy = y0 + 72
        draw.text((x0 + 30, cy), "CÂMARA E NAVEGAÇÃO", fill=(100, 180, 255), font=self.font_subtitle)
        cy += 18
        cam_cmds = [
            ("[Rato Esq + Arrastar]", "Rotação orbital (Yaw / Pitch)"),
            ("[Rato Dir + Arrastar]", "Pan da câmara (deslocamento do alvo)"),
            ("[Roda do Rato]      ", "Zoom suave (aproximar / afastar)"),
            ("[W / S]             ", "Avançar / Recuar no espaço"),
            ("[A / D]             ", "Strafe esquerda / direita"),
            ("[Q / E]             ", "Descer / Subir verticalmente"),
            ("[T]                 ", "Ligar / Desligar rastreamento dinâmico do planeta"),
        ]
        for key, desc in cam_cmds:
            draw.text((x0 + 30, cy), key, fill=(255, 230, 130), font=self.font_small)
            draw.text((x0 + 220, cy), desc, fill=(220, 225, 235), font=self.font_small)
            cy += 17

        # Secção 2 — Planetas
        cy += 3
        draw.line([(x0 + 25, cy), (x1 - 25, cy)], fill=(30, 55, 100), width=1)
        cy += 5
        draw.text((x0 + 30, cy), "SELEÇÃO DE PLANETAS E SISTEMA SOLAR", fill=(100, 180, 255), font=self.font_subtitle)
        cy += 18
        planet_cmds = [
            ("[1] Mercúrio  [2] Vénus  [3] Terra  [4] Marte", ""),
            ("[5] Júpiter   [6] Saturno  [7] Úrano  [8] Neptuno  [9/H] Sol", ""),
            ("[0]                     ", "Vista completa do Sistema Solar"),
            ("[TAB / Shift+TAB]       ", "Ciclar para o próximo planeta / anterior"),
            ("[Clique no Planeta]     ", "Selecionar por Ray Picking 3D"),
        ]
        for key, desc in planet_cmds:
            draw.text((x0 + 30, cy), key, fill=(255, 230, 130), font=self.font_small)
            if desc:
                draw.text((x0 + 220, cy), desc, fill=(220, 225, 235), font=self.font_small)
            cy += 17

        # Secção 3 — Simulação e Módulos Cósmicos
        cy += 3
        draw.line([(x0 + 25, cy), (x1 - 25, cy)], fill=(30, 55, 100), width=1)
        cy += 5
        draw.text((x0 + 30, cy), "SIMULAÇÃO E MÓDULOS CÓSMICOS", fill=(100, 180, 255), font=self.font_subtitle)
        cy += 18
        sim_cmds = [
            ("[ESPAÇO]", "Pausar / Retomar a simulação física"),
            ("[R]     ", "Reinício completo (tempo=0, câmara=padrão)"),
            ("[+ / -] ", "Acelerar / Desacelerar velocidade orbital"),
            ("[O]     ", "Ligar / Desligar órbitas elípticas keplerianas"),
            ("[N / P] ", "Ligar / Desligar campo de estrelas (Starfield)"),
            ("[B]     ", "Ligar / Desligar cintura de asteroides"),
            ("[C]     ", "Ligar / Desligar cometa e sua cauda/órbita"),
            ("[L]     ", "Ligar / Desligar satélite artificial e foguetão lunar"),
            ("[M]     ", "Ligar / Desligar chuva de meteoros e bólides"),
            ("[▲]     ", "Fora do Sist. Solar: Segurar 5s Alerta Perigo | +5s Revela Buraco Negro"),
            ("[ALT]   ", "Frente a Frente com o Buraco Negro (cicla entre as 8 singularidades)"),
            ("[SHIFT] ", "Propulsão Warp de Fuga ao ser atraído pelo Buraco de Minhoca"),
            ("[G]     ", "Ciclar foco entre os 8 Buracos Negros cósmicos"),
            ("[V]     ", "Ligar / Desligar galáxia espiral Via Láctea"),
        ]
        for key, desc in sim_cmds:
            draw.text((x0 + 30, cy), key, fill=(255, 230, 130), font=self.font_small)
            draw.text((x0 + 130, cy), desc, fill=(220, 225, 235), font=self.font_small)
            cy += 16

        # Secção 4 — Escalas e UI
        cy += 3
        draw.line([(x0 + 25, cy), (x1 - 25, cy)], fill=(30, 55, 100), width=1)
        cy += 5
        scale_cmds = [
            ("[F2] Galáxia      [F3] Região Estelar      [F4] Sistema Solar      [ENTER] Superfície", ""),
            ("[I] Painel de Informações       [F1] Ajuda       [ESC] Voltar / Sair", ""),
        ]
        for key, desc in scale_cmds:
            draw.text((x0 + 30, cy), key, fill=(180, 230, 255), font=self.font_small)
            cy += 16

        # Créditos
        cy += 3
        draw.line([(x0 + 25, cy), (x1 - 25, cy)], fill=(45, 75, 130), width=1)
        draw.text((x0 + 30, cy + 8), "Dados astronómicos reais: NASA Horizons, JPL, ESA, USGS Astrogeology.", fill=(130, 160, 200), font=self.font_small)
        draw.text((x0 + 30, cy + 23), "Prima [F1] para fechar este ecrã de ajuda.", fill=(180, 210, 255), font=self.font_small)

    def _draw_guide_speech_box(self, draw: ImageDraw.ImageDraw, info: dict) -> None:
        """Desenha uma elegante caixa de legendas/diálogo na parte inferior do ecrã."""
        import textwrap

        box_w = min(820, self.width - 60)
        box_h = 130
        x0 = (self.width - box_w) // 2
        y0 = self.height - box_h - 18
        x1 = x0 + box_w
        y1 = y0 + box_h

        # Fundo translúcido moderno sci-fi
        draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=12,
            fill=(10, 16, 28, 240),
            outline=(60, 160, 255, 255),
            width=2,
        )

        # Cabeçalho do Guia
        planet_name = info.get("planet_name", "Planeta")
        title = info.get("title", "Apresentação Cósmica")
        header_text = f"🎓 GUIA VIRTUAL 3D  |  {planet_name.upper()}  —  {title}"
        draw.text((x0 + 18, y0 + 12), header_text, fill=(255, 215, 80), font=self.font_subtitle)
        draw.line([(x0 + 18, y0 + 34), (x1 - 18, y0 + 34)], fill=(40, 75, 130), width=1)

        # Texto falado pelo guia (com quebra de linha suave)
        speech_text = info.get("text", "")
        # Ajusta comprimento de linha conforme a largura da caixa
        wrap_chars = max(50, int(box_w / 8.5))
        wrapped_lines = textwrap.wrap(speech_text, width=wrap_chars)[:3]

        text_y = y0 + 42
        for line in wrapped_lines:
            draw.text((x0 + 20, text_y), line, fill=(235, 240, 250), font=self.font_text)
            text_y += 18

        # Barra de rodapé com atalhos e estado
        is_playing = info.get("is_playing", True)
        status_str = "● A narrar..." if is_playing else "❚❚ Pausa"
        status_col = (80, 240, 140) if is_playing else (255, 180, 50)
        draw.text((x0 + 20, y1 - 22), status_str, fill=status_col, font=self.font_small)

        controls_str = "[ENTER] Próxima Seção  |  [X] Fechar Guia  |  [I] Informações"
        draw.text((x1 - 380, y1 - 22), controls_str, fill=(160, 190, 230), font=self.font_small)
