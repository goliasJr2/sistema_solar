"""
===============================================================================
Módulo: guide/facial_animation.py
Descrição: Sistema de controlo de animação facial em tempo real.
Gere o piscar natural dos olhos, expressões faciais e acoplamento com o Lip Sync.
===============================================================================
"""

import math
import random
from dataclasses import dataclass
from speech.lip_sync import VisemeState


@dataclass
class FacialParameters:
    blink_factor: float = 0.0     # 0.0 = olhos abertos, 1.0 = olhos fechados
    smile_factor: float = 0.15    # Sorriso cordial suave de professor
    mouth_open: float = 0.0
    jaw_drop: float = 0.0
    mouth_round: float = 0.0


class FacialAnimationController:
    """Controlador de animações faciais e expressões em tempo real."""

    def __init__(self):
        self.params = FacialParameters()
        
        # Temporizador para piscar de olhos natural
        self._blink_timer: float = random.uniform(2.0, 4.5)
        self._is_blinking: bool = False
        self._blink_progress: float = 0.0
        self._blink_duration: float = 0.14 # 140 ms - piscar humano natural

        # Estado emocional / expressão
        self._current_expression: str = "NEUTRAL"
        self._target_smile: float = 0.2

    def set_expression(self, expression: str) -> None:
        """Altera a expressão facial base ('NEUTRAL', 'HAPPY', 'THINKING', 'TALKING')."""
        self._current_expression = expression
        if expression == "HAPPY" or expression == "TALKING":
            self._target_smile = 0.35
        elif expression == "THINKING":
            self._target_smile = 0.08
        else:
            self._target_smile = 0.18

    def update(self, delta_time: float, visemes: VisemeState) -> FacialParameters:
        """
        Atualiza o piscar de olhos, expressões e acopla com os visemas do Lip Sync.
        """
        # 1. Atualizar o piscar dos olhos
        self._blink_timer -= delta_time
        if self._blink_timer <= 0.0 and not self._is_blinking:
            self._is_blinking = True
            self._blink_progress = 0.0
            self._blink_timer = random.uniform(2.5, 5.0)

        if self._is_blinking:
            self._blink_progress += delta_time / self._blink_duration
            if self._blink_progress >= 1.0:
                self._is_blinking = False
                self.params.blink_factor = 0.0
            else:
                # Curva senoidal suave de subida e descida
                self.params.blink_factor = math.sin(self._blink_progress * math.pi)
        else:
            self.params.blink_factor = 0.0

        # 2. Transição suave de sorriso
        self.params.smile_factor += (self._target_smile - self.params.smile_factor) * min(1.0, delta_time * 4.0)

        # 3. Integrar com o Lip Sync
        self.params.mouth_open = visemes.mouth_open
        self.params.jaw_drop = visemes.jaw_drop
        self.params.mouth_round = visemes.mouth_round

        return self.params
