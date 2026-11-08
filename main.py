"""
===============================================================================
PROJETO: Simulador Astronómico Inteligente 3D (Grupo 1)
DISCIPLINA: Computação Gráfica
AUTOR: Engenheiro Sénior de Computação Gráfica

REQUISITOS OBRIGATÓRIOS IMPLEMENTADOS (Fase 1):
  [1] Rotação planetária individual (eixo, período e inclinação axial reais)
  [2] Translação orbital elíptica (Equação de Kepler com Sol no foco, órbitas 3D)
  [3] Texturas reais dos planetas (com gerador procedural resiliente)
  [5] Zoom e rotação de câmara (Rato: esquerdo=órbita, roda=zoom, direito=pan; Teclado: WASD, Q/E)
  [9] Fundo espacial com estrelas (GL_POINTS com cores espectrais e dimensão dinâmica)
  [10] Sistema de pausa e reinício (ESPAÇO = pausa/retomar, R = reinício completo)
  [11] Animação em tempo real (Delta time, 60 FPS, física independente da taxa de quadros)

CONCEITOS DE COMPUTAÇÃO GRÁFICA APLICADOS:
  - Pipeline Gráfico:
      1. Vértices e Topologia (Arrays de dados intercalados: posição, normal, UV).
      2. Vertex Shader (Transformações Model, View, Projection, gl_Position, gl_PointSize).
      3. Rasterização e Interpolação (Geração de fragmentos a partir dos triângulos).
      4. Fragment Shader (Iluminação Blinn-Phong, amostragem de textura, cálculo dia/noite).
      5. Testes de Fragmento (Depth Test GL_LESS para oclusão, Face Culling GL_BACK, Blending).
      6. Framebuffer e Viewport (glViewport e buffer duplo com SwapBuffers).
  - Transformações Geométricas: Translate, Rotate, Scale e composição hierárquica.
  - Coordenadas 3D: Espaço Local -> Mundo -> Vista (Câmara) -> Recorte (Clip).
  - Matrizes: PyGLM para Model, View (lookAt) e Projection (perspective).
  - Texturas: Pillow, glTexImage2D, Mipmaps trilineares e filtragem anisotrópica.
  - Iluminação: Blinn-Phong (Ambiente + Difusa + Especular) e matriz normal inversa transposta.
  - Viewport: glViewport dinâmico no redimensionamento da janela.
===============================================================================

GUIA COMPLETO DE CONTROLOS DE TECLADO:
  ─────────────────────────── CÂMARA ───────────────────────────
  [W / S]           : Avançar / Recuar no espaço
  [A / D]           : Pan lateral (Strafe)
  [Q / E]           : Descer / Subir verticalmente
  [Rato Esquerdo]   : Rotação orbital (Yaw / Pitch)
  [Rato Direito]    : Pan no plano da câmara
  [Roda do Rato]    : Zoom suave (aproximar / afastar)

  ─────────────────── SELEÇÃO DE PLANETAS ──────────────────────
  [1] Mercúrio      [2] Vénus         [3] Terra
  [4] Marte         [5] Júpiter       [6] Saturno
  [7] Úrano         [8] Neptuno       [9] Sol
  [0]               : Focar no Sistema Solar completo (vista padrão)
  [Clique]          : Selecionar planeta por Ray Picking 3D

  ──────────────── SIMULAÇÃO E TEMPO ───────────────────────────
  [ESPAÇO]          : Pausar / Retomar a simulação
  [R]               : Reinício completo (tempo=0, câmara=inicial)
  [+ / =]           : Acelerar velocidade orbital (até 1.000.000x)
  [-]               : Desacelerar velocidade orbital (mín. 0.01x)

  ───────────────── VISUALIZAÇÃO CÓSMICA ───────────────────────
  [O]               : Ligar / Desligar órbitas elípticas
  [M]               : Ligar / Desligar chuva de meteoros e bólides
  [G]               : Focar/Ciclar Buracos Negros (Sagitário A*, Cygnus X-1, Gargantua)
  [L]               : Ligar / Desligar satélite artificial e foguetão lunar
  [C]               : Ligar / Desligar cometa e sua órbita
  [B]               : Ligar / Desligar cintura de asteroides
  [V]               : Ligar / Desligar galáxia espiral
  [N]               : Ligar / Desligar campo de estrelas de fundo
  [H]               : Focar no Sol (centro do Sistema Solar)
  [TAB]             : Ciclar para o próximo planeta em órbita
  [TAB + SHIFT]     : Ciclar para o planeta anterior

  ──────────────── ESCALAS CÓSMICAS ───────────────────────────
  [F2]              : Nível 1 — Vista Galáctica (Via Láctea + Sagitário A*)
  [F3]              : Nível 2 — Região Estelar Local (Alfa Centauri, CoRoT-7b)
  [F4]              : Nível 3 — Sistema Solar (vista padrão)
  [ENTER]           : Nível 4 — Superfície Planetária (planeta selecionado)
  [ESC]             : Voltar ao Sistema Solar (se em superfície) / Sair

  ─────────────────── INTERFACE (UI) ──────────────────────────
  [I]               : Mostrar / Ocultar painel de informações do planeta
  [F1]              : Mostrar / Ocultar ecrã de ajuda e créditos
===============================================================================
"""

import sys
import time
from pathlib import Path
from typing import Optional
import glm
import glfw
from OpenGL.GL import (
    glClearColor,
    glClear,
    glViewport,
    glEnable,
    glDisable,
    glDepthFunc,
    glCullFace,
    glFrontFace,
    glBlendFunc,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LESS,
    GL_CULL_FACE,
    GL_BACK,
    GL_CCW,
    GL_MULTISAMPLE,
    GL_BLEND,
    GL_SRC_ALPHA,
    GL_ONE_MINUS_SRC_ALPHA,
)

from shader import Shader
from camera import Camera
from planets import SolarSystem, CELESTIAL_DATA
from starfield import Starfield
from picking import RayPicker
from ui import UIManager
from asteroids import AsteroidBelt
from comet import Comet
from blackhole import BlackHoleSystem
from galaxy import SpiralGalaxy
from satellites import EarthSatellite, LunarRocket
from meteors import MeteorShower
from scale_manager import ScaleManager, ScaleLevel
from characters import PlanetCharacters
from guide.virtual_guide import AstronomicalVirtualGuide


class CameraMode:
    """Modos de câmara unificados do simulador cósmico."""
    EXPLORE = 0  # Navegação livre e panorâmica pelo espaço
    FOLLOW = 1   # Acompanha a translação do planeta em órbita a média distância
    FOCUS = 2    # Foco orbital próximo no planeta selecionado para inspeção


# Diretórios do projeto (caminhos relativos resilientes com pathlib)
BASE_DIR = Path(__file__).resolve().parent
SHADERS_DIR = BASE_DIR / "shaders"
TEXTURES_DIR = BASE_DIR / "textures"
MODELS_DIR = BASE_DIR / "Models"


class SolarSimulatorApp:
    """
    Aplicação principal do Simulador Astronómico 3D.
    Coordena a janela GLFW, contexto OpenGL 3.3 Core Profile, ciclo de eventos e renderização.
    """

    def __init__(self, window_width: int = 1280, window_height: int = 720,
                 title: str = "Simulador Astronómico 3D - Grupo 1"):
        self.width = window_width
        self.height = window_height
        self.base_title = title
        self.window = None

        # ─── Controlo temporal ───
        self.is_paused: bool = False
        self.time_scale_days_per_sec: float = 10.0
        self.show_orbits: bool = True

        # ─── Visibilidade de módulos cósmicos (controlados pelo teclado) ───
        self.show_meteors: bool = False
        self.show_satellites: bool = True
        self.show_comet: bool = True
        self.show_asteroids: bool = True
        self.show_blackholes: bool = True
        self.show_galaxy: bool = True
        self.show_starfield: bool = True   # Campo de estrelas de fundo [N]

        # ─── Estado do rato ───
        self.first_mouse: bool = True
        self.last_mouse_x: float = float(window_width) / 2.0
        self.last_mouse_y: float = float(window_height) / 2.0
        self.mouse_left_down: bool = False
        self.mouse_right_down: bool = False
        self.mouse_press_pos = (0.0, 0.0)

        # ─── Métricas de desempenho ───
        self.fps_counter: int = 0
        self.fps_timer: float = 0.0
        self.current_fps: float = 60.0

        # ─── Câmara inicial centrada no Sistema Solar ───
        self.camera = Camera(
            position=glm.vec3(0.0, 90.0, 260.0),
            target=glm.vec3(0.0, 0.0, 0.0),
            up=glm.vec3(0.0, 1.0, 0.0),
            aspect_ratio=float(window_width) / float(window_height),
        )

        # ─── Módulos gráficos ───
        self.starfield: Optional[Starfield] = None
        self.solar_system: Optional[SolarSystem] = None
        self.ui_manager: Optional[UIManager] = None
        self.asteroid_belt: Optional[AsteroidBelt] = None
        self.comet: Optional[Comet] = None
        self.black_hole_system: Optional[BlackHoleSystem] = None
        self.galaxy: Optional[SpiralGalaxy] = None
        self.earth_satellite: Optional[EarthSatellite] = None
        self.lunar_rocket: Optional[LunarRocket] = None
        self.meteor_shower: Optional[MeteorShower] = None
        self.scale_manager: Optional[ScaleManager] = None
        self.planet_characters: Optional[PlanetCharacters] = None  # Personagem apresentador de cada planeta

        # ─── Guia Virtual 3D ───
        self.virtual_guide: Optional[AstronomicalVirtualGuide] = None
        self.guide_active: bool = False

        # ─── Rastreio do planeta selecionado ───
        self.selected_body_id: Optional[str] = "earth"
        self.camera_tracking: bool = True  # Rastreamento dinâmico da câmara no planeta selecionado [T]
        self.camera_mode: int = CameraMode.FOCUS  # Modos de câmara: Explore / Follow / Focus [P]
        self.current_black_hole_alert: Optional[dict] = None  # Alerta de proximidade de buraco negro

        # ─── Estado do Sistema de Buracos Negros Cósmicos ───
        self.bh_arrow_up_timer: float = 0.0
        self.bh_danger_alert_active: bool = False
        self.bh_revealed: bool = False
        self.bh_primary_aligned: bool = False
        self.bh_face_to_face: Optional[str] = None
        self.bh_face_to_face_timer: float = 0.0

        # ─── Shaders ───
        self.celestial_shader: Optional[Shader] = None
        self.sun_shader: Optional[Shader] = None
        self.orbit_shader: Optional[Shader] = None
        self.starfield_shader: Optional[Shader] = None
        self.ui_shader: Optional[Shader] = None
        self.ring_shader: Optional[Shader] = None

    # =========================================================================
    # INICIALIZAÇÃO
    # =========================================================================
    def initialize(self) -> None:
        """Inicializa o subsistema GLFW e cria a janela OpenGL 3.3 Core Profile."""
        if not glfw.init():
            raise RuntimeError("[Erro GLFW] Não foi possível inicializar a biblioteca GLFW.")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.SAMPLES, 4)  # MSAA 4x

        self.window = glfw.create_window(self.width, self.height, self.base_title, None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("[Erro GLFW] Falha ao criar janela OpenGL 3.3 Core.")

        glfw.make_context_current(self.window)
        glfw.swap_interval(1)  # V-Sync

        glfw.set_framebuffer_size_callback(self.window, self._framebuffer_size_callback)
        glfw.set_cursor_pos_callback(self.window, self._cursor_pos_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)
        glfw.set_scroll_callback(self.window, self._scroll_callback)
        glfw.set_key_callback(self.window, self._key_callback)

        # Pipeline OpenGL
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_MULTISAMPLE)
        glClearColor(0.01, 0.01, 0.02, 1.0)

        # Compilação de shaders
        print("[Simulador] A compilar shaders GLSL 3.3...")
        self.celestial_shader = Shader(SHADERS_DIR / "celestial.vert", SHADERS_DIR / "celestial.frag")
        self.sun_shader = Shader(SHADERS_DIR / "sun.vert", SHADERS_DIR / "sun.frag")
        self.orbit_shader = Shader(SHADERS_DIR / "orbit.vert", SHADERS_DIR / "orbit.frag")
        self.starfield_shader = Shader(SHADERS_DIR / "starfield.vert", SHADERS_DIR / "starfield.frag")
        self.ui_shader = Shader(SHADERS_DIR / "ui.vert", SHADERS_DIR / "ui.frag")
        self.ring_shader = Shader(SHADERS_DIR / "ring.vert", SHADERS_DIR / "ring.frag")

        print("[Simulador] A carregar Sistema Solar (planetas, luas, texturas e modelos 3D)...")
        self.starfield = Starfield(num_stars=3500, radius=4000.0)
        self.solar_system = SolarSystem(textures_dir=TEXTURES_DIR, models_dir=MODELS_DIR)
        self.planet_characters = PlanetCharacters(base_dir=BASE_DIR, shaders_dir=SHADERS_DIR)

        print("[Simulador] A inicializar interface de utilizador (UI)...")
        self.ui_manager = UIManager(self.width, self.height, self.ui_shader)
        self.ui_manager.set_selected_body(CELESTIAL_DATA["earth"])
        self.ui_manager.set_presenter(self.planet_characters.info_for("earth"))

        print("[Simulador] A instanciar módulos cósmicos (Galáxia, Buracos Negros, Asteroides, Cometa...)...")
        self.galaxy = SpiralGalaxy(models_dir=MODELS_DIR, num_stars=250000)
        self.asteroid_belt = AsteroidBelt(models_dir=MODELS_DIR, count=160)
        self.comet = Comet(models_dir=MODELS_DIR)
        self.black_hole_system = BlackHoleSystem(models_dir=MODELS_DIR)
        self.earth_satellite = EarthSatellite(models_dir=MODELS_DIR)
        self.lunar_rocket = LunarRocket(models_dir=MODELS_DIR)
        self.meteor_shower = MeteorShower(models_dir=MODELS_DIR, num_meteors=45)
        self.scale_manager = ScaleManager(self.camera)

        print("[Simulador] A inicializar Guia Virtual 3D (Astronomical Virtual Guide)...")
        self.virtual_guide = AstronomicalVirtualGuide(model_path=str(MODELS_DIR / "guide_remy.glb"))
        self.virtual_guide.initialize_gl()

        print("[Simulador] Inicialização concluída! Sistema Solar em destaque.")
        self._print_controls_guide()

    def _print_controls_guide(self) -> None:
        """Exibe o guia completo de controlos no terminal."""
        print("\n" + "=" * 75)
        print("SIMULADOR ASTRONÓMICO INTELIGENTE 3D - GUIA COMPLETO DE CONTROLOS")
        print("=" * 75)
        print(" ─── CÂMARA ──────────────────────────────────────────────────────")
        print(" [Rato Esquerdo + Arrastar]  : Rotação orbital da câmara")
        print(" [Rato Direito  + Arrastar]  : Pan (deslocamento lateral/vertical)")
        print(" [Roda do Rato / Scroll]     : Zoom suave (aproximar/afastar)")
        print(" [Setas / WASD]              : Navegar e voar pelo espaço (sair do Sistema Solar)")
        print(" [SHIFT + Setas/WASD]        : Propulsão Interestelar Turbo (velocidade aumentada)")
        print(" [Q / E]                     : Descer / Subir verticalmente")
        print(" ─── SELEÇÃO DE PLANETAS ─────────────────────────────────────────")
        print(" [1] Mercúrio  [2] Vénus    [3] Terra     [4] Marte")
        print(" [5] Júpiter   [6] Saturno  [7] Úrano     [8] Neptuno   [9] Sol")
        print(" [0]           : Focar no Sistema Solar completo (vista padrão)")
        print(" [Clique]      : Selecionar planeta por Ray Picking 3D")
        print(" ─── SIMULAÇÃO ───────────────────────────────────────────────────")
        print(" [ESPAÇO]      : Pausar / Retomar a simulação física")
        print(" [R]           : Reinício completo (Tempo=0, Câmara=padrão)")
        print(" [+ / =]       : Acelerar velocidade orbital (até 1.000.000x)")
        print(" [-]           : Desacelerar velocidade orbital (mín. 0.01x)")
        print(" ─── MÓDULOS CÓSMICOS (ligar/desligar) ──────────────────────────")
        print(" [O]           : Órbitas elípticas dos planetas")
        print(" [M]           : Chuva de meteoros e bólides")
        print(" [G]           : Focar/ciclar Buracos Negros (Sgr A*, Cygnus X-1, Gargantua)")
        print(" [L]           : Satélite artificial + Foguetão Lunar")
        print(" [C]           : Cometa + órbita do cometa")
        print(" [B]           : Cintura de Asteroides")
        print(" [V]           : Galáxia espiral")
        print(" [N]           : Campo de estrelas de fundo")
        print(" [H]           : Focar no Sol (centro do Sistema Solar)")
        print(" [TAB]         : Ciclar para o próximo planeta em órbita")
        print(" ─── ESCALAS CÓSMICAS ────────────────────────────────────────────")
        print(" [F2]          : Nível 1 — Vista da Galáxia Via Láctea")
        print(" [F3]          : Nível 2 — Região Estelar Local")
        print(" [F4]          : Nível 3 — Sistema Solar (padrão)")
        print(" [ENTER]       : Nível 4 — Superfície do planeta selecionado")
        print(" [ESC]         : Voltar ao Sistema Solar / Sair")
        print(" ─── INTERFACE E GUIA VIRTUAL ───────────────────────────────────")
        print(" [I]           : Painel de informações do planeta selecionado")
        print(" [Saber Mais]  : Clique no botão do painel para o Guia sentar no planeta e falar!")
        print(" [X]           : Fechar / Encerrar o Guia Virtual 3D")
        print(" [F1]          : Ecrã de ajuda e créditos completos")
        print("=" * 75 + "\n")

    # =========================================================================
    # CALLBACKS GLFW
    # =========================================================================
    def _framebuffer_size_callback(self, window, width: int, height: int) -> None:
        if height == 0:
            height = 1
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.camera.update_aspect_ratio(width, height)
        if self.ui_manager:
            self.ui_manager.resize(width, height)

    def _mouse_button_callback(self, window, button: int, action: int, mods: int) -> None:
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.mouse_left_down = True
                xpos, ypos = glfw.get_cursor_pos(window)
                self.mouse_press_pos = (xpos, ypos)
            elif action == glfw.RELEASE:
                self.mouse_left_down = False
                xpos, ypos = glfw.get_cursor_pos(window)
                dx = xpos - self.mouse_press_pos[0]
                dy = ypos - self.mouse_press_pos[1]
                if (dx * dx + dy * dy) < 25.0:
                    # Verificar se clicou no botão "🔭 Saber Mais"
                    if (
                        self.ui_manager
                        and self.ui_manager.show_info_panel
                        and self.ui_manager.selected_body_data
                    ):
                        if self.ui_manager.is_learn_more_clicked(xpos, ypos):
                            self._activate_guide_on_planet()
                            return
                    self._perform_ray_picking(xpos, ypos)
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            self.mouse_right_down = (action == glfw.PRESS)

    def _perform_ray_picking(self, mouse_x: float, mouse_y: float) -> None:
        view = self.camera.get_view_matrix()
        proj = self.camera.get_projection_matrix()
        ray_origin, ray_dir = RayPicker.get_ray_direction(
            mouse_x, mouse_y, self.width, self.height, view, proj
        )
        closest_body_id = None
        min_dist = float("inf")
        for b_id, body in self.solar_system.bodies.items():
            hit_dist = RayPicker.intersect_sphere(
                ray_origin, ray_dir, body.current_position, body.visual_radius * 1.5
            )
            if hit_dist is not None and hit_dist < min_dist:
                min_dist = hit_dist
                closest_body_id = b_id
        if closest_body_id:
            self._select_body_by_id(closest_body_id)

    def _cursor_pos_callback(self, window, xpos: float, ypos: float) -> None:
        if self.first_mouse:
            self.last_mouse_x = xpos
            self.last_mouse_y = ypos
            self.first_mouse = False
        xoffset = xpos - self.last_mouse_x
        yoffset = self.last_mouse_y - ypos
        self.last_mouse_x = xpos
        self.last_mouse_y = ypos
        if self.mouse_left_down:
            self.camera.process_mouse_orbit(xoffset, yoffset)
        elif self.mouse_right_down:
            self.camera.process_mouse_pan(xoffset, yoffset)

    def _scroll_callback(self, window, xoffset: float, yoffset: float) -> None:
        self.camera.process_mouse_scroll(yoffset)

    # =========================================================================
    # SISTEMA DE TECLADO UNIFICADO
    # =========================================================================
    def _key_callback(self, window, key: int, scancode: int, action: int, mods: int) -> None:
        """
        Processamento centralizado de todos os atalhos de teclado da simulação.
        Inclui câmara, planetas, módulos cósmicos, escalas e interface.
        """
        if action not in (glfw.PRESS,):
            return

        # ── ESC: Voltar ao Sistema Solar ou Sair ──────────────────────────────
        if key == glfw.KEY_ESCAPE:
            if self.scale_manager and self.scale_manager.current_level == ScaleLevel.SURFACE:
                self.scale_manager.set_level(ScaleLevel.SOLAR_SYSTEM)
                print("[Escala] Voltou ao Sistema Solar.")
            else:
                glfw.set_window_should_close(window, True)

        # ── ESPAÇO: Pausar / Retomar ──────────────────────────────────────────
        elif key == glfw.KEY_SPACE:
            self.is_paused = not self.is_paused
            print(f"[Simulador] {'PAUSADO' if self.is_paused else 'A CORRER'}")

        # ── R: Reinício completo ──────────────────────────────────────────────
        elif key == glfw.KEY_R:
            self.camera.reset()
            self.solar_system.reset_time()
            self.time_scale_days_per_sec = 10.0
            self.is_paused = False
            print("[Simulador] Reiniciado — Tempo=0, Câmara=padrão, Velocidade=10 dias/s.")

        # ── Velocidade orbital: + / - ─────────────────────────────────────────
        elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            self.time_scale_days_per_sec = min(1_000_000.0, self.time_scale_days_per_sec * 2.0)
            print(f"[Velocidade] {self.time_scale_days_per_sec:.1f} dias/s")
        elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            self.time_scale_days_per_sec = max(0.01, self.time_scale_days_per_sec / 2.0)
            print(f"[Velocidade] {self.time_scale_days_per_sec:.2f} dias/s")

        # ── [O] Órbitas ───────────────────────────────────────────────────────
        elif key == glfw.KEY_O:
            self.show_orbits = not self.show_orbits
            print(f"[Órbitas] {'LIGADAS' if self.show_orbits else 'DESLIGADAS'}")

        # ── [M] Meteoros ──────────────────────────────────────────────────────
        elif key == glfw.KEY_M:
            self.show_meteors = self.meteor_shower.toggle()

        # ── [G] Buracos Negros — ciclar foco ─────────────────────────────────
        elif key == glfw.KEY_G:
            self.show_blackholes = True
            self.bh_revealed = True
            if self.black_hole_system:
                self.black_hole_system.reveal_all()
                bh = self.black_hole_system.cycle_next()
                self.camera.target = glm.vec3(bh.position)
                self.camera.distance = max(40.0, bh.scale * 3.5)
                self.camera._update_camera_vectors()
                self.camera_tracking = False
                print(f"[Buraco Negro] Foco em: {bh.name}")

        # ── [ALT] Frente a Frente com o Buraco Negro ──────────────────────────
        elif key in (glfw.KEY_LEFT_ALT, glfw.KEY_RIGHT_ALT):
            self.show_blackholes = True
            self.bh_revealed = True
            self.bh_arrow_up_timer = max(self.bh_arrow_up_timer, 10.0)
            self.camera_tracking = False

            if self.black_hole_system:
                self.black_hole_system.reveal_all()
                if self.bh_face_to_face:
                    bh = self.black_hole_system.cycle_next()
                else:
                    bh = self.black_hole_system.get_current()

                self.bh_face_to_face = bh.name
                self.bh_face_to_face_timer = 9.0

                # Posicionamento direto da câmara face a face com o buraco negro
                self.camera.target = glm.vec3(bh.position)
                self.camera.distance = max(42.0, bh.scale * 2.8)
                self.camera.pitch = 5.0
                self.camera.yaw = 90.0
                self.camera._update_camera_vectors()
                if self.ui_manager:
                    self.ui_manager.set_selected_body(None)
                print(f"[Buraco Negro] FRENTE A FRENTE com {bh.name} a {self.camera.distance:.1f} UA!")

        # ── [L] Satélite + Foguetão Lunar ─────────────────────────────────────
        elif key == glfw.KEY_L:
            self.show_satellites = not self.show_satellites
            print(f"[Satélites] {'LIGADOS' if self.show_satellites else 'DESLIGADOS'}")

        # ── [C] Cometa ────────────────────────────────────────────────────────
        elif key == glfw.KEY_C:
            self.show_comet = not self.show_comet
            print(f"[Cometa] {'VISÍVEL' if self.show_comet else 'OCULTO'}")

        # ── [B] Asteroides ────────────────────────────────────────────────────
        elif key == glfw.KEY_B:
            self.show_asteroids = not self.show_asteroids
            print(f"[Asteroides] {'VISÍVEIS' if self.show_asteroids else 'OCULTOS'}")

        # ── [V] Galáxia ───────────────────────────────────────────────────────
        elif key == glfw.KEY_V:
            self.show_galaxy = not self.show_galaxy
            print(f"[Galáxia] {'VISÍVEL' if self.show_galaxy else 'OCULTA'}")

        # ── [N] Campo de estrelas de fundo (Starfield) ────────────────────────
        elif key == glfw.KEY_N:
            self.show_starfield = not self.show_starfield
            print(f"[Estrelas] {'VISÍVEIS' if self.show_starfield else 'OCULTAS'}")

        # ── [P] Alternar Modos de Câmara (Explore / Follow / Focus) ───────────
        elif key == glfw.KEY_P:
            self.camera_mode = (self.camera_mode + 1) % 3
            if self.camera_mode == CameraMode.EXPLORE:
                self.camera_tracking = False
                print("[Modo Câmara] EXPLORE: Navegação livre com WASD e Rato.")
            elif self.camera_mode == CameraMode.FOLLOW:
                self.camera_tracking = True
                if self.selected_body_id and self.selected_body_id in self.solar_system.bodies:
                    b = self.solar_system.bodies[self.selected_body_id]
                    self.camera.target = glm.vec3(b.current_position)
                    self.camera.distance = max(25.0, b.visual_radius * 12.0)
                    self.camera._update_camera_vectors()
                print("[Modo Câmara] FOLLOW: A acompanhar a translação do planeta em órbita.")
            elif self.camera_mode == CameraMode.FOCUS:
                self.camera_tracking = True
                if self.selected_body_id and self.selected_body_id in self.solar_system.bodies:
                    b = self.solar_system.bodies[self.selected_body_id]
                    self.camera.target = glm.vec3(b.current_position)
                    self.camera.distance = max(8.0, b.visual_radius * 3.8)
                    self.camera._update_camera_vectors()
                print("[Modo Câmara] FOCUS: Foco próximo na superfície do planeta.")

        # ── [H] Focar no Sol (centro do Sistema Solar) ────────────────────────
        elif key == glfw.KEY_H:
            self._select_body_by_id("sun")

        # ── [T] Alternar rastreamento dinâmico da câmara no planeta ───────────
        elif key == glfw.KEY_T:
            self.camera_tracking = not self.camera_tracking
            estado = "LIGADO (A câmara acompanha a órbita)" if self.camera_tracking else "DESLIGADO (Câmara estática)"
            print(f"[Rastreamento Orbital] {estado}")

        # ── [TAB] Ciclar entre planetas em sequência orbital ──────────────────
        elif key == glfw.KEY_TAB:
            reverse = bool(mods & glfw.MOD_SHIFT)
            self._cycle_planet(reverse=reverse)

        # ── Escalas Cósmicas: F2, F3, F4 ─────────────────────────────────────
        elif key == glfw.KEY_F2:
            self.scale_manager.set_level(ScaleLevel.GALAXY)
        elif key == glfw.KEY_F3:
            self.scale_manager.set_level(ScaleLevel.LOCAL_REGION)
        elif key == glfw.KEY_F4:
            self.scale_manager.set_level(ScaleLevel.SOLAR_SYSTEM)

        # ── ENTER: Descer à superfície do planeta selecionado ─────────────────
        elif key == glfw.KEY_ENTER:
            target_pos = glm.vec3(0.0)
            if self.selected_body_id and self.selected_body_id in self.solar_system.bodies:
                target_pos = self.solar_system.bodies[self.selected_body_id].current_position
            self.scale_manager.set_level(ScaleLevel.SURFACE, target_pos)

        # ── [0] Vista completa do Sistema Solar ───────────────────────────────
        elif key == glfw.KEY_0:
            self.selected_body_id = None
            self.camera.target = glm.vec3(0.0, 0.0, 0.0)
            self.camera.distance = 280.0
            self.camera.pitch = 20.0
            self.camera.yaw = 90.0
            self.camera._update_camera_vectors()
            if self.ui_manager:
                self.ui_manager.set_selected_body(None)
            print("[Câmara] Vista do Sistema Solar completo.")

        # ── [1–9] Seleção direta de planetas ──────────────────────────────────
        elif key == glfw.KEY_1:
            self._select_body_by_id("mercury")
        elif key == glfw.KEY_2:
            self._select_body_by_id("venus")
        elif key == glfw.KEY_3:
            self._select_body_by_id("earth")
        elif key == glfw.KEY_4:
            self._select_body_by_id("mars")
        elif key == glfw.KEY_5:
            self._select_body_by_id("jupiter")
        elif key == glfw.KEY_6:
            self._select_body_by_id("saturn")
        elif key == glfw.KEY_7:
            self._select_body_by_id("uranus")
        elif key == glfw.KEY_8:
            self._select_body_by_id("neptune")
        elif key == glfw.KEY_9:
            self._select_body_by_id("sun")

        # ── [I] Painel de informações ─────────────────────────────────────────
        elif key == glfw.KEY_I:
            self.ui_manager.toggle_info_panel()

        # ── [X] Fechar o Guia Virtual ─────────────────────────────────────────
        elif key == glfw.KEY_X:
            if self.virtual_guide and self.guide_active:
                self.virtual_guide.close()
                self.guide_active = False
                if self.ui_manager:
                    self.ui_manager.show_info_panel = True
                print("[Guia Virtual] Apresentação encerrada.")

        # ── [F1] Ajuda ────────────────────────────────────────────────────────
        elif key == glfw.KEY_F1:
            self.ui_manager.toggle_help()

    def _select_body_by_id(self, body_id: str) -> None:
        """Seleciona um corpo celeste pelo ID, foca a câmara e atualiza o painel."""
        if body_id in self.solar_system.bodies:
            body = self.solar_system.bodies[body_id]
            self.selected_body_id = body_id
            self.ui_manager.set_selected_body(body.data)
            self.ui_manager.set_presenter(self.planet_characters.info_for(body_id))
            # Foca suavemente no corpo selecionado com distância proporcional ao tamanho
            self.camera.target = glm.vec3(body.current_position)
            if body_id == "sun":
                self.camera.distance = 55.0
            else:
                self.camera.distance = max(10.0, body.visual_radius * 5.5)
            self.camera._update_camera_vectors()
            print(f"[Seleção] Foco → {body.name} (Rastreamento ativo)")

    def _activate_guide_on_planet(self) -> None:
        """
        Ativa o Guia Virtual sentado no topo do planeta selecionado.
        Posiciona a câmara com visão privilegiada e inicia a narração científica.
        """
        if not self.selected_body_id or not self.virtual_guide:
            return

        body = self.solar_system.bodies.get(self.selected_body_id)
        if not body:
            return

        planet_name = body.name
        planet_id = self.selected_body_id

        # Enquadra a câmara no topo do planeta
        planet_pos = body.current_position
        planet_radius = body.visual_radius

        # Alvo aponta diretamente para o topo do planeta
        self.camera.target = glm.vec3(planet_pos.x, planet_pos.y + planet_radius * 0.95, planet_pos.z)
        if planet_id == "sun":
            self.camera.distance = 45.0
        else:
            self.camera.distance = max(6.5, planet_radius * 3.0)
        self.camera.pitch = 16.0
        self.camera.yaw = 90.0
        self.camera._update_camera_vectors()
        self.camera_tracking = True

        # Oculta o painel lateral para vista limpa
        if self.ui_manager:
            self.ui_manager.show_info_panel = False

        # Inicia a apresentação com o personagem sentado
        self.virtual_guide.open_on_planet(planet_name, planet_id)
        self.guide_active = True

        print(f"\n[Guia Virtual 3D] Sentado no topo de {planet_name.upper()} a falar sobre o planeta!")

    def _cycle_planet(self, reverse: bool = False) -> None:
        """Cicla para o próximo planeta ou anterior na ordem orbital natural."""
        orbit_order = [
            "mercury", "venus", "earth", "mars",
            "jupiter", "saturn", "uranus", "neptune", "sun"
        ]
        curr = self.selected_body_id or "earth"
        try:
            curr_idx = orbit_order.index(curr)
        except ValueError:
            curr_idx = 2  # Earth

        step = -1 if reverse else 1
        next_idx = (curr_idx + step) % len(orbit_order)
        next_id = orbit_order[next_idx]
        self._select_body_by_id(next_id)

    def _process_continuous_input(self, delta_time: float) -> None:
        """
        Navegação livre e contínua pelo espaço com Setas (Arrow Keys) ou WASD + Q/E.
        Suporta propulsão turbo com SHIFT para voos interestelares rápidos.
        """
        nav_forward = (
            glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS
        )
        nav_backward = (
            glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_DOWN) == glfw.PRESS
        )
        nav_left = (
            glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS
        )
        nav_right = (
            glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS
        )
        nav_up = glfw.get_key(self.window, glfw.KEY_E) == glfw.PRESS
        nav_down = glfw.get_key(self.window, glfw.KEY_Q) == glfw.PRESS

        # Se o utilizador navegar manualmente, desativa o rastreio automático do planeta para sair livremente do Sistema Solar
        if nav_forward or nav_backward or nav_left or nav_right or nav_up or nav_down:
            self.camera_tracking = False

        # Turbo Boost com tecla SHIFT para navegar a grandes distâncias cósmicas
        boost = 2.5 if (
            glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS
        ) else 1.0

        if nav_forward:
            self.camera.process_keyboard("FORWARD", delta_time * boost)
        if nav_backward:
            self.camera.process_keyboard("BACKWARD", delta_time * boost)
        if nav_left:
            self.camera.process_keyboard("LEFT", delta_time * boost)
        if nav_right:
            self.camera.process_keyboard("RIGHT", delta_time * boost)
        if nav_up:
            self.camera.process_keyboard("UP", delta_time * boost)
        if nav_down:
            self.camera.process_keyboard("DOWN", delta_time * boost)

        # ── Controlo de Ativação do Buraco Negro: Seta Cima por 5s + 5s ────────
        dist_from_sun = glm.length(self.camera.position)
        outside_solar_system = dist_from_sun >= 200.0
        is_pressing_up = (
            glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS
        )

        if outside_solar_system and is_pressing_up:
            self.bh_arrow_up_timer += delta_time

            # 1. Alerta de Perigo após 5 segundos contínuos
            if self.bh_arrow_up_timer >= 5.0 and not self.bh_danger_alert_active:
                self.bh_danger_alert_active = True
                print("\n" + "=" * 70)
                print("[ALERTA DE PERIGO] DISTORÇÃO ESPAÇO-TEMPORAL CRÍTICA DETETADA!")
                print("Mantenha premida a Seta Cima mais 5s para revelar ou prima [ALT] para ficar Frente a Frente!")
                print("=" * 70 + "\n")

            # 2. Revelação e manifestação do Buraco Negro após mais 5 segundos (10s total)
            if self.bh_arrow_up_timer >= 10.0 and not self.bh_revealed:
                self.bh_revealed = True
                self.show_blackholes = True
                if self.black_hole_system:
                    self.black_hole_system.reveal_all()
                    if not self.bh_primary_aligned:
                        self.black_hole_system.align_primary_ahead(self.camera.position, self.camera.front, 260.0)
                        self.bh_primary_aligned = True
                print("\n" + "=" * 70)
                print("[BURACO NEGRO] SINGULARIDADE REVELADA DIRETAMENTE À SUA FRENTE!")
                print("Prima [ALT] a qualquer momento para se colocar Frente a Frente com o Buraco Negro!")
                print("=" * 70 + "\n")
        else:
            if self.bh_arrow_up_timer < 5.0:
                self.bh_arrow_up_timer = max(0.0, self.bh_arrow_up_timer - delta_time * 1.5)

        if self.bh_face_to_face_timer > 0.0:
            self.bh_face_to_face_timer -= delta_time
            if self.bh_face_to_face_timer <= 0.0:
                self.bh_face_to_face = None

    def _update_window_title(self, delta_time: float) -> None:
        """Atualiza o título da janela com FPS, estado e tempo simulado."""
        self.fps_counter += 1
        self.fps_timer += delta_time
        if self.fps_timer >= 0.5:
            self.current_fps = float(self.fps_counter) / self.fps_timer
            self.fps_counter = 0
            self.fps_timer = 0.0
            state_str = "PAUSA" if self.is_paused else "ATIVO"
            sim_years = self.solar_system.simulated_days / 365.25
            title = (
                f"{self.base_title} | [{state_str}] | "
                f"Vel: {self.time_scale_days_per_sec:.1f} dias/s | "
                f"Tempo: {self.solar_system.simulated_days:.1f}d ({sim_years:.2f}a) | "
                f"FPS: {self.current_fps:.1f}"
            )
            glfw.set_window_title(self.window, title)

    # =========================================================================
    # CICLO PRINCIPAL
    # =========================================================================
    def run(self) -> None:
        """Executa o ciclo de renderização a 60 FPS com delta time independente."""
        last_frame_time = time.perf_counter()

        while not glfw.window_should_close(self.window):
            current_time = time.perf_counter()
            delta_time = current_time - last_frame_time
            last_frame_time = current_time
            # Protege contra freezes / breakpoints
            if delta_time > 0.15:
                delta_time = 0.016

            # 1. Eventos de entrada
            glfw.poll_events()
            self._process_continuous_input(delta_time)

            # 2. Atualização física da simulação
            if not self.is_paused:
                self.solar_system.update(delta_time, self.time_scale_days_per_sec)
                delta_sim_days = delta_time * self.time_scale_days_per_sec

                if self.show_asteroids:
                    self.asteroid_belt.update(self.solar_system.simulated_days, delta_sim_days)
                if self.show_comet:
                    self.comet.update(self.solar_system.simulated_days, delta_sim_days)
                if self.show_blackholes:
                    self.black_hole_system.update(delta_time)
                if self.show_satellites:
                    self.earth_satellite.update(delta_time)
                    self.lunar_rocket.update(delta_time)
                if self.show_meteors:
                    earth_pos = self.solar_system.bodies["earth"].current_position
                    self.meteor_shower.update(delta_time, earth_pos)

            # Verificação e Alertas de Buracos Negros Cósmicos
            if self.black_hole_system:
                dist_from_sun = glm.length(self.camera.position)
                outside_solar = dist_from_sun >= 200.0
                prox = self.black_hole_system.check_proximity(self.camera.position)

                is_shift_pressed = (
                    glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS
                    or glfw.get_key(self.window, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS
                )

                # Zona de Sucção Gravitacional e Buraco de Minhoca
                in_gravitational_trap = (
                    prox is not None
                    and prox["is_critical"]
                    and not (self.bh_face_to_face and self.bh_face_to_face_timer > 3.0)
                )

                if in_gravitational_trap:
                    bh_pos = prox["position"]
                    pull_radius = prox["pull_radius"]
                    dist = prox["distance"]
                    pull_dir = glm.normalize(bh_pos - self.camera.position)
                    warp_factor = max(0.0, min(1.0, 1.0 - (dist / pull_radius)))

                    if is_shift_pressed:
                        # ── PROPULSÃO WARP DE FUGA COM SHIFT ─────────────────
                        # Motores a 100%: empuxo potente na direção oposta ao vórtice
                        escape_dir = -pull_dir
                        escape_speed = 190.0
                        self.camera.position += escape_dir * (escape_speed * delta_time)
                        self.camera.target += escape_dir * (escape_speed * delta_time)

                        # O campo visual (FOV) regressa progressivamente a 45°
                        self.camera.fov += (45.0 - self.camera.fov) * min(1.0, delta_time * 6.0)

                        self.current_black_hole_alert = {
                            "type": "WARP_ESCAPE",
                            "name": prox["name"],
                            "distance": dist,
                        }
                    else:
                        # ── SUCÇÃO RELATIVÍSTICA DO BURACO DE MINHOCA ─────────
                        # Atração gravitacional acelera exponencialmente em direção à singularidade
                        pull_speed = 36.0 + warp_factor * 85.0
                        self.camera.position += pull_dir * (pull_speed * delta_time)
                        self.camera.target += pull_dir * (pull_speed * delta_time * 0.7)

                        # Efeito visual de distorção de túnel (Wormhole Tunneling / Lente Gravitacional)
                        target_fov = 45.0 + (warp_factor ** 1.3) * 32.0  # Expande até 77°!
                        self.camera.fov += (target_fov - self.camera.fov) * min(1.0, delta_time * 4.0)

                        # Turbulência e tremuras de maré espacial
                        if warp_factor > 0.15:
                            shake_intensity = (warp_factor - 0.15) * 1.4
                            jitter = glm.vec3(
                                random.uniform(-1.0, 1.0),
                                random.uniform(-1.0, 1.0),
                                random.uniform(-1.0, 1.0),
                            ) * shake_intensity
                            self.camera.position += jitter * (delta_time * 16.0)

                        self.current_black_hole_alert = {
                            "type": "WORMHOLE_PULL",
                            "name": prox["name"],
                            "distance": dist,
                            "warp_factor": warp_factor,
                            "pull_radius": pull_radius,
                        }
                else:
                    # Fora da zona crítica, o FOV recupera o ângulo de perspetiva padrão
                    if abs(self.camera.fov - 45.0) > 0.1:
                        self.camera.fov += (45.0 - self.camera.fov) * min(1.0, delta_time * 3.0)

                    if self.bh_face_to_face and self.bh_face_to_face_timer > 0.0:
                        self.current_black_hole_alert = {
                            "type": "FACE_TO_FACE",
                            "name": self.bh_face_to_face,
                            "distance": self.camera.distance,
                        }
                    elif self.bh_revealed and 10.0 <= self.bh_arrow_up_timer <= 18.0:
                        pri_bh = self.black_hole_system.get_primary()
                        pri_dist = glm.length(pri_bh.position - self.camera.position)
                        self.current_black_hole_alert = {
                            "type": "REVEALED",
                            "name": pri_bh.name,
                            "distance": pri_dist,
                        }
                    elif self.bh_danger_alert_active and self.bh_arrow_up_timer < 10.0:
                        self.current_black_hole_alert = {
                            "type": "DANGER",
                            "progress_sec": self.bh_arrow_up_timer - 5.0,
                        }
                    elif outside_solar and 1.0 < self.bh_arrow_up_timer < 5.0:
                        self.current_black_hole_alert = {
                            "type": "OUTSIDE_CHARGING",
                            "progress_sec": self.bh_arrow_up_timer,
                        }
                    elif prox:
                        self.current_black_hole_alert = {
                            "type": "PROXIMITY",
                            "name": prox["name"],
                            "distance": prox["distance"],
                            "is_critical": prox["is_critical"],
                            "position": prox["position"],
                            "pull_radius": prox["pull_radius"],
                        }
                    else:
                        self.current_black_hole_alert = None

            # Atualização da transição de escala
            self.scale_manager.update(delta_time)

            # Atualização das animações, lip sync e voz do Guia Virtual 3D
            if self.guide_active and self.virtual_guide:
                self.virtual_guide.update(delta_time)

            # Rastreamento dinâmico da câmara: acompanha o planeta selecionado em sua órbita elíptica
            if (
                self.selected_body_id
                and self.selected_body_id in self.solar_system.bodies
                and self.camera_tracking
                and not self.is_paused
            ):
                if not (self.scale_manager and self.scale_manager.is_transitioning):
                    tracked_body = self.solar_system.bodies[self.selected_body_id]
                    if self.guide_active:
                        target_spot = tracked_body.current_position + glm.vec3(0.0, tracked_body.visual_radius * 0.95, 0.0)
                    else:
                        target_spot = glm.vec3(tracked_body.current_position)
                    delta_move = target_spot - self.camera.target
                    self.camera.target = glm.vec3(target_spot)
                    self.camera.position += delta_move

            # 3. Limpeza do framebuffer
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # 4. Matrizes de câmara
            view_matrix = self.camera.get_view_matrix()
            projection_matrix = self.camera.get_projection_matrix()
            camera_pos = self.camera.position
            sun_pos = self.solar_system.bodies["sun"].current_position
            earth_pos = self.solar_system.bodies["earth"].current_position

            # 5. Fundo cósmico — Estrelas + Galáxia Espiral (renderizadas sem culling)
            glDisable(GL_CULL_FACE)
            if self.show_starfield:
                self.starfield.draw(self.starfield_shader, view_matrix, projection_matrix, current_time)
            if self.show_galaxy:
                self.galaxy.draw(
                    starfield_shader=self.starfield_shader,
                    celestial_shader=self.celestial_shader,
                    view=view_matrix,
                    proj=projection_matrix,
                    view_pos=camera_pos,
                    current_time=current_time,
                )
            glEnable(GL_CULL_FACE)

            # 6. Buracos Negros
            if self.show_blackholes:
                self.black_hole_system.draw(
                    self.celestial_shader, view_matrix, projection_matrix, camera_pos
                )

            # 7. ★ SISTEMA SOLAR — Foco principal da simulação ★
            #    Inclui Sol emissivo, 8 planetas com órbitas keplerianas, todas as luas e anéis com sombra
            self.solar_system.draw(
                celestial_shader=self.celestial_shader,
                sun_shader=self.sun_shader,
                orbit_shader=self.orbit_shader,
                view=view_matrix,
                projection=projection_matrix,
                view_pos=camera_pos,
                show_orbits=self.show_orbits,
                current_time=current_time,
                ring_shader=self.ring_shader,
            )

            # 7b. Personagem apresentador do planeta selecionado (characters.json)
            if self.planet_characters:
                self.planet_characters.update(delta_time, self.selected_body_id)
                self.planet_characters.draw(
                    self.celestial_shader,
                    view_matrix,
                    projection_matrix,
                    self.camera,
                    # Com o Guia Virtual aberto ("Saber Mais"), o apresentador esconde-se
                    None if self.guide_active else self.solar_system.bodies.get(self.selected_body_id or ""),
                    current_time,
                )

            # 8. Cintura de Asteroides
            if self.show_asteroids:
                self.asteroid_belt.draw(
                    self.celestial_shader, view_matrix, projection_matrix, camera_pos, sun_pos
                )

            # 9. Cometa
            if self.show_comet:
                self.comet.draw(
                    self.celestial_shader, view_matrix, projection_matrix, camera_pos, sun_pos
                )
                if self.show_orbits:
                    self.comet.draw_orbit(self.orbit_shader, view_matrix, projection_matrix)

            # 10. Satélites artificiais e foguetão lunar
            if self.show_satellites:
                self.earth_satellite.draw(
                    self.celestial_shader, view_matrix, projection_matrix,
                    camera_pos, sun_pos, earth_pos
                )
                moon_pos = earth_pos
                earth_body = self.solar_system.bodies["earth"]
                if earth_body.moons:
                    moon_pos = earth_body.moons[0].world_position
                self.lunar_rocket.draw(
                    self.celestial_shader, view_matrix, projection_matrix,
                    camera_pos, sun_pos, moon_pos
                )

            # 11. Chuva de Meteoros
            if self.show_meteors:
                self.meteor_shower.draw(self.orbit_shader, view_matrix, projection_matrix)

            # 12. Guia Virtual 3D — Personagem sentado no topo do planeta selecionado
            if (
                self.guide_active
                and self.virtual_guide
                and self.selected_body_id
                and self.selected_body_id in self.solar_system.bodies
            ):
                target_body = self.solar_system.bodies[self.selected_body_id]
                self.virtual_guide.render_on_planet(
                    view_mat=view_matrix,
                    proj_mat=projection_matrix,
                    cam_pos=camera_pos,
                    planet_pos=target_body.current_position,
                    planet_radius=target_body.visual_radius,
                    axial_tilt_deg=target_body.data.get("axial_tilt_deg", 0.0),
                )

            # 13. Interface 2D — HUD + Painel de Informações + Legendas Pedagógicas
            if self.ui_manager:
                self.ui_manager.draw(
                    is_paused=self.is_paused,
                    time_scale=self.time_scale_days_per_sec,
                    simulated_days=self.solar_system.simulated_days,
                    fps=self.current_fps,
                    show_orbits=self.show_orbits,
                    active_modules={
                        "orbits": self.show_orbits,
                        "meteors": self.show_meteors,
                        "satellites": self.show_satellites,
                        "comet": self.show_comet,
                        "asteroids": self.show_asteroids,
                        "blackholes": self.show_blackholes,
                        "galaxy": self.show_galaxy,
                        "starfield": self.show_starfield,
                        "tracking": self.camera_tracking,
                        "camera_mode": self.camera_mode,
                        "black_hole_alert": self.current_black_hole_alert,
                        "guide_info": {
                            "planet_name": self.solar_system.bodies[self.selected_body_id].name if (self.selected_body_id and self.selected_body_id in self.solar_system.bodies) else "",
                            "title": self.virtual_guide.controller.lesson_manager.current_section.title if self.virtual_guide else "",
                            "text": self.virtual_guide.controller.lesson_manager.current_section.speech_text if self.virtual_guide else "",
                            "is_playing": self.virtual_guide.controller.audio_player.is_playing() if self.virtual_guide else False,
                        } if self.guide_active else None,
                    },
                )

            # 14. Apresentação do frame (Double Buffering)
            glfw.swap_buffers(self.window)
            self._update_window_title(delta_time)

        self._cleanup()

    def _cleanup(self) -> None:
        """Liberta recursos do OpenGL e encerra o GLFW."""
        if self.planet_characters:
            self.planet_characters.cleanup()
        if self.virtual_guide:
            self.virtual_guide.cleanup()
        glfw.destroy_window(self.window)
        glfw.terminate()
        print("[Simulador] Aplicação terminada com sucesso.")


def main():
    """Ponto de entrada do executável."""
    app = SolarSimulatorApp()
    try:
        app.initialize()
        app.run()
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
