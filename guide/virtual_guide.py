"""
===============================================================================
Módulo: guide/virtual_guide.py
Descrição: Fachada unificada do Astronomical Virtual Guide (Guia Virtual 3D).
Ponto de entrada integrado no simulador para apresentação, renderização e controlos.
===============================================================================
"""

from typing import Optional, Dict, Any, Tuple
from .guide_controller import GuideController
from .guide_renderer import GuideRenderer


class AstronomicalVirtualGuide:
    """
    Guia Virtual 3D Animado com inteligência pedagógica, voz sintetizada,
    sincronização labial e integração na interface gráfica do simulador.
    """

    def __init__(self, model_path: str = "Models/guide_remy.glb", initial_character: str = "remy"):
        self.controller = GuideController("Terra")
        self.renderer: Optional[GuideRenderer] = None
        self._model_path = model_path
        self._current_character: str = initial_character
        self._is_visible = False

        # Dimensões da janela do guia (Picture-in-Picture elegante ampliado)
        self.panel_x: int = 0
        self.panel_y: int = 0
        self.panel_w: int = 360
        self.panel_h: int = 420

    def initialize_gl(self) -> None:
        """Inicializa os recursos OpenGL do renderizador após o contexto GLFW estar ativo."""
        if self.renderer is None:
            self.renderer = GuideRenderer(self._model_path, initial_character=self._current_character)

    @property
    def current_character(self) -> str:
        """Identificador do modelo 3D atual ('remy', 'goblin', 'mutant', 'warrok')."""
        return self._current_character

    @property
    def current_profile(self) -> dict:
        """Perfil visual, badge e papel do personagem ativo."""
        from .guide_renderer import CHARACTER_PROFILES
        return CHARACTER_PROFILES.get(self._current_character, CHARACTER_PROFILES["remy"])

    def set_character(self, character_id: str) -> None:
        """Define e troca a variação do personagem em tempo real."""
        self._current_character = character_id
        if self.renderer:
            self.renderer.set_character(character_id)

    def cycle_character(self) -> str:
        """Alterna ciclicamente entre as variações: Remy -> Goblin -> Mutant -> Warrok -> Remy."""
        from .guide_renderer import CHARACTER_PROFILES
        keys = list(CHARACTER_PROFILES.keys())
        try:
            idx = keys.index(self._current_character)
            next_idx = (idx + 1) % len(keys)
        except ValueError:
            next_idx = 0
        new_char = keys[next_idx]
        self.set_character(new_char)
        return new_char

    @property
    def is_visible(self) -> bool:
        return self._is_visible

    def open(self, planet_name: str = "Terra", character_id: Optional[str] = None) -> None:
        """Abre a apresentação do Guia Virtual para o planeta indicado com o personagem escolhido."""
        if character_id:
            self.set_character(character_id)
        self._is_visible = True
        self.controller.planet_name = planet_name
        self.controller.activate()

    def close(self) -> None:
        """Fecha o painel do Guia Virtual."""
        self._is_visible = False
        self.controller.deactivate()

    def toggle(self, planet_name: str = "Terra") -> None:
        """Alterna a visibilidade do Guia Virtual."""
        if self._is_visible:
            self.close()
        else:
            self.open(planet_name)

    def open_on_planet(self, planet_name: str, planet_id: str) -> None:
        """Abre o Guia Virtual sentado em posição de lótus no topo do planeta, meditando e narrando sobre ele."""
        self._is_visible = True
        self.controller.planet_name = planet_name
        # Atualiza as lições para o planeta correto
        self.controller.lesson_manager.set_planet(planet_id)
        self.controller.activate(is_meditating=True)

    def update(self, delta_time: float) -> None:
        """Atualização de física, áudio e animações a 60 FPS."""
        if not self._is_visible:
            return
        self.controller.update(delta_time)

    def render(self, screen_w: int, screen_h: int) -> None:
        """Renderiza a cabeça do Baskerville 3D no canto superior direito do ecrã."""
        if not self._is_visible or self.renderer is None:
            return

        # Posicionamento no canto superior direito, logo abaixo da barra superior (HUD)
        # Em OpenGL, a origem da viewport (0,0) é no canto inferior esquerdo!
        view_w = 360
        view_h = 420
        view_x = int(screen_w - view_w - 20)
        view_y = int(screen_h - view_h - 55)

        self.panel_x = view_x
        self.panel_y = view_y
        self.panel_w = view_w
        self.panel_h = view_h

        # Obter poses esqueléticas e faciais calculadas dinamicamente
        skeletal_state, facial_params = self.controller.get_current_state()

        self.renderer.render(
            viewport_x=view_x,
            viewport_y=view_y,
            viewport_w=view_w,
            viewport_h=view_h,
            skeletal_state=skeletal_state,
            facial_params=facial_params,
        )

        # CRÍTICO: Restaurar imediatamente o viewport completo da janela
        # para que o resto da cena (galáxia, estrelas, planetas e UI) continue em ecrã inteiro
        from OpenGL.GL import glViewport
        glViewport(0, 0, screen_w, screen_h)

    def render_on_planet(
        self,
        view_mat,
        proj_mat,
        cam_pos,
        planet_pos,
        planet_radius: float,
        axial_tilt_deg: float = 0.0,
    ) -> None:
        """Renderiza o Guia Virtual 3D sentado no topo do planeta em posição de lótus meditativa."""
        if not self._is_visible or self.renderer is None:
            return

        skeletal_state, facial_params = self.controller.get_current_state()
        self.renderer.render_on_planet(
            view_mat=view_mat,
            proj_mat=proj_mat,
            cam_pos=cam_pos,
            planet_pos=planet_pos,
            planet_radius=planet_radius,
            skeletal_state=skeletal_state,
            facial_params=facial_params,
            axial_tilt_deg=axial_tilt_deg,
        )

    def cleanup(self) -> None:
        """Desaloca recursos da GPU e para áudio."""
        self.controller.deactivate()
        if self.renderer:
            self.renderer.cleanup()
            self.renderer = None
