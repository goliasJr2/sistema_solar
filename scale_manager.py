"""
===============================================================================
Módulo: scale_manager.py
Descrição: Gestor dos 4 Níveis de Escala Cósmica e Transições Cinematográficas Suaves.
Níveis implementados:
  [Nível 1] Galáxia: Visão macroscópica da Via Láctea, Sagitário A* e braços espirais.
  [Nível 2] Região Local: Estrelas vizinhas (Alfa Centauri, CoRoT-7b) e asteroides errantes.
  [Nível 3] Sistema Solar: Sol, planetas, luas, cintura de asteroides, cometa e satélites.
  [Nível 4] Superfície Planetária: Visão imersiva à superfície da Terra e da Lua.
Conceitos aplicados:
  - Interpolação Linear e Esférica (Lerp/Slerp) para transição cinematográfica suave.
  - Planos Near e Far dinâmicos adaptados à ordem de magnitude da escala.
  - Velocidade da câmara adaptativa em função da distância focal.
===============================================================================
"""

from typing import Tuple, Optional
import math
import glm

from camera import Camera
from galaxy import GALAXY_CENTER_POS


class ScaleLevel:
    GALAXY = 1       # Nível 1: Visão Geral da Galáxia
    LOCAL_REGION = 2 # Nível 2: Vizinhança Estelar Local
    SOLAR_SYSTEM = 3 # Nível 3: Sistema Solar (Padrão)
    SURFACE = 4      # Nível 4: Superfície Planetária


class ScaleManager:
    """Controla as transições cinematográficas entre as escalas do universo."""

    def __init__(self, camera: Camera):
        self.camera = camera
        self.current_level = ScaleLevel.SOLAR_SYSTEM

        # Parâmetros de Interpolação Cinematográfica (Smooth Transition)
        self.is_transitioning = False
        self.transition_t = 1.0
        self.transition_duration = 2.2  # segundos

        self.start_pos = glm.vec3(camera.position)
        self.start_target = glm.vec3(camera.target)
        self.dest_pos = glm.vec3(camera.position)
        self.dest_target = glm.vec3(camera.target)

    def set_level(self, level: int, target_body_pos: Optional[glm.vec3] = None) -> None:
        """Inicia uma transição suave para o nível de escala especificado."""
        self.current_level = level
        self.start_pos = glm.vec3(self.camera.position)
        self.start_target = glm.vec3(self.camera.target)
        self.transition_t = 0.0
        self.is_transitioning = True

        if level == ScaleLevel.GALAXY:
            # Vista macroscópica inclinada de topo de toda a galáxia
            self.dest_target = glm.vec3(GALAXY_CENTER_POS)
            self.dest_pos = GALAXY_CENTER_POS + glm.vec3(0.0, 3200.0, 2800.0)
            self.camera.near_plane = 20.0
            self.camera.far_plane = 30000.0
            print("[Escala] Transição para Nível 1: GALÁXIA ESPIRAL (Via Láctea)")

        elif level == ScaleLevel.LOCAL_REGION:
            # Visão das estrelas vizinhas ao redor do Sistema Solar
            self.dest_target = glm.vec3(0.0, 0.0, -400.0)
            self.dest_pos = glm.vec3(450.0, 600.0, 1100.0)
            self.camera.near_plane = 5.0
            self.camera.far_plane = 15000.0
            print("[Escala] Transição para Nível 2: REGIÃO ESTELAR LOCAL")

        elif level == ScaleLevel.SOLAR_SYSTEM:
            # Visão completa do Sistema Solar centrado no Sol
            self.dest_target = glm.vec3(0.0, 0.0, 0.0)
            self.dest_pos = glm.vec3(0.0, 110.0, 320.0)
            self.camera.near_plane = 0.5
            self.camera.far_plane = 8000.0
            print("[Escala] Transição para Nível 3: SISTEMA SOLAR")

        elif level == ScaleLevel.SURFACE:
            # Descida cinematográfica à superfície da Terra ou Lua
            center = target_body_pos or glm.vec3(0.0, 0.0, 60.0)  # Posição da Terra
            self.dest_target = center
            # Posicionamento rasante logo acima da superfície
            self.dest_pos = center + glm.vec3(0.0, 3.8, 3.2)
            self.camera.near_plane = 0.05
            self.camera.far_plane = 4000.0
            print("[Escala] Transição para Nível 4: SUPERFÍCIE PLANETÁRIA")

    def update(self, delta_time: float) -> None:
        """Executa a interpolação suave (Smoothstep) de posição e alvo da câmara."""
        if not self.is_transitioning:
            return

        self.transition_t += delta_time / self.transition_duration
        if self.transition_t >= 1.0:
            self.transition_t = 1.0
            self.is_transitioning = False

        # Curva de aceleração e desaceleração suave (S-Curve / Smoothstep)
        t = self.transition_t
        smooth_t = t * t * (3.0 - 2.0 * t)

        # Interpolação linear dos vetores
        self.camera.position = glm.mix(self.start_pos, self.dest_pos, smooth_t)
        self.camera.target = glm.mix(self.start_target, self.dest_target, smooth_t)

        # Atualiza a orientação interna da câmara
        diff = self.camera.position - self.camera.target
        self.camera.distance = glm.length(diff)
        if self.camera.distance > 0.01:
            self.camera.yaw = math.degrees(math.atan2(diff.z, diff.x))
            self.camera.pitch = math.degrees(math.asin(diff.y / self.camera.distance))
        self.camera._update_camera_vectors()
