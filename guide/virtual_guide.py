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

    def __init__(self, model_path: str = "Models/guide_remy.glb"):
        self.controller = GuideController("Terra")
        self.renderer: Optional[GuideRenderer] = None
        self._model_path = model_path
        self._is_visible = False

        # Dimensões da janela do guia (Picture-in-Picture elegante)
        self.panel_x: int = 0
        self.panel_y: int = 0
        self.panel_w: int = 380
        self.panel_h: int = 480

    def initialize_gl(self) -> None:
        """Inicializa os recursos OpenGL do renderizador após o contexto GLFW estar ativo."""
        if self.renderer is None:
            self.renderer = GuideRenderer(self._model_path)

    @property
    def is_visible(self) -> bool:
        return self._is_visible

    def open(self, planet_name: str = "Terra") -> None:
        """Abre a apresentação do Guia Virtual para o planeta indicado."""
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
        """Renderiza o personagem 3D no painel lateral direito do ecrã."""
        if not self._is_visible or self.renderer is None:
            return

        # Posicionamento no canto superior/médio direito, sem tapar o centro da Terra
        # Em OpenGL, a origem da viewport (0,0) é no canto inferior esquerdo!
        view_w = int(min(360, screen_w * 0.32))
        view_h = int(min(420, screen_h * 0.55))
        view_x = int(screen_w - view_w - 30)
        view_y = int(screen_h * 0.22) # Meio/alto

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
