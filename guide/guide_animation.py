"""
===============================================================================
Módulo: guide/guide_animation.py
Descrição: Sistema de animação corporal em tempo real para o Guia Virtual 3D.
Implementa máquina de estados (IDLE, TALKING, THINKING, LISTENING) com
respiração natural, movimentos da cabeça, gestos dos braços e interpolação.
===============================================================================
"""

import math
import glm
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SkeletalTransformState:
    head_rotation: glm.mat4
    right_arm_rotation: glm.mat4
    left_arm_rotation: glm.mat4
    breathing_scale: float


class GuideAnimationEngine:
    """Motor de animação esquelética e corporal procedural em tempo real."""

    def __init__(self):
        self.state: str = "IDLE" # "IDLE", "TALKING", "THINKING", "LISTENING"
        self._time_elapsed: float = 0.0

        # Ângulos da cabeça (Yaw, Pitch, Roll)
        self.head_pitch: float = 0.0
        self.head_yaw: float = 0.0
        self.head_roll: float = 0.0

        # Ângulos do braço direito
        self.r_arm_pitch: float = 0.0
        self.r_arm_yaw: float = 0.0
        self.r_arm_roll: float = 0.0

        # Ângulos do braço esquerdo
        self.l_arm_pitch: float = 0.0
        self.l_arm_yaw: float = 0.0
        self.l_arm_roll: float = 0.0

        # Ângulos alvo para interpolação suave
        self.target_head_pitch: float = 0.0
        self.target_head_yaw: float = 0.0
        self.target_head_roll: float = 0.0

        self.target_r_arm_pitch: float = 0.0
        self.target_r_arm_yaw: float = 0.0
        self.target_r_arm_roll: float = 0.0

        self.target_l_arm_pitch: float = 0.0
        self.target_l_arm_yaw: float = 0.0
        self.target_l_arm_roll: float = 0.0

        # Pontos de pivô anatómicos (espaço local do modelo Remy)
        self.head_pivot = glm.vec3(0.0, 325.0, 3.0)
        self.right_shoulder_pivot = glm.vec3(38.0, 280.0, 0.0)
        self.left_shoulder_pivot = glm.vec3(-38.0, 280.0, 0.0)

        # Modo Meditação Cósmica (Posição de Lótus / Padmasana)
        self.is_meditating: bool = False

    def set_state(self, new_state: str) -> None:
        """Transita para um novo estado de animação."""
        if new_state != self.state:
            self.state = new_state

    def update(self, delta_time: float) -> SkeletalTransformState:
        """
        Atualiza os ciclos temporais e calcula as matrizes de rotação de cada osso.
        """
        self._time_elapsed += delta_time
        t = self._time_elapsed

        # ─── 1. CICLO DE RESPIRAÇÃO (Frequência ~0.26 Hz = ~16 respirações/min) ─
        # Curva de respiração humana: inspiração ligeiramente mais rápida que expiração
        breath_speed = 1.35 if self.is_meditating else 1.65
        breath_cycle = math.sin(t * breath_speed) * 0.5 + 0.5
        breath_scale = breath_cycle * (1.15 if self.is_meditating else 0.85)

        # ─── 2. COMPORTAMENTO ESPECÍFICO POR ESTADO ─────────────────────────
        if self.is_meditating:
            # ── Modo Meditação Cósmica em Posição de Lótus ───────────────────
            if self.state == "TALKING":
                # Enquanto fala: mão direita faz gestos serenos; esquerda descansa no joelho
                gesture = math.sin(t * 1.8)
                self.target_r_arm_pitch = 42.0 + gesture * 18.0
                self.target_r_arm_roll = -28.0 + math.cos(t * 1.4) * 12.0
                self.target_r_arm_yaw = 22.0 + math.sin(t * 1.2) * 10.0

                self.target_l_arm_pitch = 28.0 + math.sin(t * 1.2) * 2.0
                self.target_l_arm_roll = 40.0
                self.target_l_arm_yaw = -16.0

                self.target_head_yaw = math.sin(t * 1.2) * 7.5
                self.target_head_pitch = math.sin(t * 1.8) * 4.5 - 1.0
                self.target_head_roll = math.sin(t * 0.9) * 2.5
            else:
                # Postura zen pura com mãos descansadas nos joelhos
                self.target_r_arm_pitch = 30.0 + math.sin(t * 1.2) * 1.8
                self.target_r_arm_roll = -42.0 + math.cos(t * 1.5) * 1.5
                self.target_r_arm_yaw = 16.0

                self.target_l_arm_pitch = 30.0 + math.sin(t * 1.2) * 1.8
                self.target_l_arm_roll = 42.0 - math.cos(t * 1.5) * 1.5
                self.target_l_arm_yaw = -16.0

                self.target_head_yaw = math.sin(t * 0.45) * 4.0
                self.target_head_pitch = -2.5 + math.sin(t * 0.8) * 2.5
                self.target_head_roll = math.sin(t * 0.4) * 1.8

        elif self.state == "IDLE":
            # Repouso natural com micro-oscilações sutis
            self.target_head_yaw = math.sin(t * 0.45) * 4.0
            self.target_head_pitch = math.sin(t * 0.8) * 2.0 - 1.0
            self.target_head_roll = math.sin(t * 0.35) * 1.5

            # Braços em repouso elegante junto ao tronco
            self.target_r_arm_pitch = math.sin(t * 0.5) * 2.0
            self.target_r_arm_roll = -62.0 + math.sin(t * 1.65) * 1.2
            self.target_r_arm_yaw = 0.0

            self.target_l_arm_pitch = -math.sin(t * 0.5) * 2.0
            self.target_l_arm_roll = 62.0 - math.sin(t * 1.65) * 1.2
            self.target_l_arm_yaw = 0.0

        elif self.state == "TALKING":
            # Durante a explicação: movimentos expressivos da cabeça
            self.target_head_yaw = math.sin(t * 1.4) * 8.5 + math.cos(t * 0.6) * 4.0
            self.target_head_pitch = math.sin(t * 2.2) * 5.0 - 2.0
            self.target_head_roll = math.sin(t * 1.1) * 3.0

            # Gestos explicativos com as mãos e antebraços alternados
            gesture_cycle = math.sin(t * 1.8)
            # Braço direito eleva-se explicando para a cena
            self.target_r_arm_pitch = 28.0 + gesture_cycle * 22.0
            self.target_r_arm_roll = -42.0 + math.cos(t * 1.5) * 15.0
            self.target_r_arm_yaw = 18.0 + math.sin(t * 1.2) * 12.0

            # Braço esquerdo apoia com menor amplitude
            self.target_l_arm_pitch = 12.0 - gesture_cycle * 14.0
            self.target_l_arm_roll = 50.0 + math.sin(t * 1.3) * 10.0
            self.target_l_arm_yaw = -10.0

        elif self.state == "THINKING":
            # Cabeça inclinada reflexiva
            self.target_head_yaw = -12.0
            self.target_head_pitch = 6.0 + math.sin(t * 0.6) * 2.0
            self.target_head_roll = 7.0

            # Mão direita sobe perto do queixo
            self.target_r_arm_pitch = 55.0
            self.target_r_arm_roll = -25.0
            self.target_r_arm_yaw = 35.0

            self.target_l_arm_pitch = 5.0
            self.target_l_arm_roll = 60.0
            self.target_l_arm_yaw = 0.0

        elif self.state == "LISTENING":
            # Foco absoluto no utilizador
            self.target_head_yaw = math.sin(t * 0.3) * 2.0
            self.target_head_pitch = -4.0 + math.sin(t * 0.5) * 1.5
            self.target_head_roll = 0.0

            self.target_r_arm_pitch = 0.0
            self.target_r_arm_roll = -64.0
            self.target_r_arm_yaw = 0.0

            self.target_l_arm_pitch = 0.0
            self.target_l_arm_roll = 64.0
            self.target_l_arm_yaw = 0.0

        # ─── 3. INTERPOLAÇÃO SUAVE (LERP) ──────────────────────────────────
        if delta_time > 0.0:
            lerp_speed = min(1.0, delta_time * 5.5)

            self.head_pitch += (self.target_head_pitch - self.head_pitch) * lerp_speed
            self.head_yaw += (self.target_head_yaw - self.head_yaw) * lerp_speed
            self.head_roll += (self.target_head_roll - self.head_roll) * lerp_speed

            self.r_arm_pitch += (self.target_r_arm_pitch - self.r_arm_pitch) * lerp_speed
            self.r_arm_yaw += (self.target_r_arm_yaw - self.r_arm_yaw) * lerp_speed
            self.r_arm_roll += (self.target_r_arm_roll - self.r_arm_roll) * lerp_speed

            self.l_arm_pitch += (self.target_l_arm_pitch - self.l_arm_pitch) * lerp_speed
            self.l_arm_yaw += (self.target_l_arm_yaw - self.l_arm_yaw) * lerp_speed
            self.l_arm_roll += (self.target_l_arm_roll - self.l_arm_roll) * lerp_speed

        self.head_pitch += (self.target_head_pitch - self.head_pitch) * lerp_speed
        self.head_yaw += (self.target_head_yaw - self.head_yaw) * lerp_speed
        self.head_roll += (self.target_head_roll - self.head_roll) * lerp_speed

        self.r_arm_pitch += (self.target_r_arm_pitch - self.r_arm_pitch) * lerp_speed
        self.r_arm_yaw += (self.target_r_arm_yaw - self.r_arm_yaw) * lerp_speed
        self.r_arm_roll += (self.target_r_arm_roll - self.r_arm_roll) * lerp_speed

        self.l_arm_pitch += (self.target_l_arm_pitch - self.l_arm_pitch) * lerp_speed
        self.l_arm_yaw += (self.target_l_arm_yaw - self.l_arm_yaw) * lerp_speed
        self.l_arm_roll += (self.target_l_arm_roll - self.l_arm_roll) * lerp_speed

        # ─── 4. CONSTRUÇÃO DAS MATRIZES DE ROTAÇÃO COM PYGLM ────────────────
        head_mat = glm.mat4(1.0)
        head_mat = glm.rotate(head_mat, glm.radians(self.head_yaw), glm.vec3(0, 1, 0))
        head_mat = glm.rotate(head_mat, glm.radians(self.head_pitch), glm.vec3(1, 0, 0))
        head_mat = glm.rotate(head_mat, glm.radians(self.head_roll), glm.vec3(0, 0, 1))

        r_arm_mat = glm.mat4(1.0)
        r_arm_mat = glm.rotate(r_arm_mat, glm.radians(self.r_arm_yaw), glm.vec3(0, 1, 0))
        r_arm_mat = glm.rotate(r_arm_mat, glm.radians(self.r_arm_pitch), glm.vec3(1, 0, 0))
        r_arm_mat = glm.rotate(r_arm_mat, glm.radians(self.r_arm_roll), glm.vec3(0, 0, 1))

        l_arm_mat = glm.mat4(1.0)
        l_arm_mat = glm.rotate(l_arm_mat, glm.radians(self.l_arm_yaw), glm.vec3(0, 1, 0))
        l_arm_mat = glm.rotate(l_arm_mat, glm.radians(self.l_arm_pitch), glm.vec3(1, 0, 0))
        l_arm_mat = glm.rotate(l_arm_mat, glm.radians(self.l_arm_roll), glm.vec3(0, 0, 1))

        return SkeletalTransformState(
            head_rotation=head_mat,
            right_arm_rotation=r_arm_mat,
            left_arm_rotation=l_arm_mat,
            breathing_scale=breath_scale,
        )
