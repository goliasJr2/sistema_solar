"""
===============================================================================
Módulo: orbits.py
Descrição: Mecânica orbital kepleriana e cálculo de órbitas elípticas.
Conceitos aplicados:
  - Leis de Kepler do Movimento Planetário:
      * 1ª Lei: Órbitas elípticas com o Sol posicionado num foco da elipse.
      * 2ª Lei: Lei das Áreas (velocidade orbital variável: mais rápida no periélio).
      * 3ª Lei: Relação entre período orbital e semi-eixo maior.
  - Resolução Numérica da Equação Transcendental de Kepler:
      * M = E - e * sin(E) (Anomalia Média para Anomalia Excêntrica).
      * Método Iterativo de Newton-Raphson com convergência quadrática.
  - Transformações Geométricas em 3D:
      * Posição orbital no plano focal (x', z').
      * Rotação pela inclinação orbital (matriz de rotação tridimensional).
      * Geração de malha fechada de vértices para renderização da trajetória.
===============================================================================
"""

import math
from typing import List, Tuple
import glm


class KeplerianOrbit:
    """
    Calcula a posição 3D exata de um corpo celeste ao longo de uma órbita elíptica
    resolvendo a Equação de Kepler em cada instante de tempo simulado.
    """

    def __init__(
        self,
        semi_major_axis: float,
        eccentricity: float,
        inclination_deg: float,
        orbital_period_days: float,
        initial_mean_anomaly_deg: float = 0.0,
    ):
        self.a = float(semi_major_axis)            # Semi-eixo maior (distância média)
        self.e = float(eccentricity)               # Excentricidade da elipse (0 = circular, < 1 = elíptica)
        self.inclination = math.radians(inclination_deg)  # Inclinação em relação ao plano da eclítica
        self.period = float(orbital_period_days)   # Período de translação orbital em dias
        self.m0 = math.radians(initial_mean_anomaly_deg)

        # Semi-eixo menor: b = a * sqrt(1 - e^2)
        self.b = self.a * math.sqrt(max(0.0, 1.0 - self.e * self.e))

    def solve_kepler(self, mean_anomaly: float, tolerance: float = 1e-6, max_iterations: int = 30) -> float:
        """
        Resolve a equação transcendental M = E - e * sin(E) para a Anomalia Excêntrica E
        utilizando o método de Newton-Raphson.
        """
        # Estimativa inicial de E
        E = mean_anomaly if self.e < 0.8 else math.pi

        for _ in range(max_iterations):
            f_E = E - self.e * math.sin(E) - mean_anomaly
            f_prime_E = 1.0 - self.e * math.cos(E)

            delta_E = f_E / f_prime_E
            E -= delta_E

            if abs(delta_E) < tolerance:
                break

        return E

    def get_position_at_time(self, time_days: float) -> glm.vec3:
        """
        Calcula a posição tridimensional (X, Y, Z) do planeta no espaço de mundo
        para um determinado instante t (em dias simulados).
        O Sol encontra-se exatamente no foco da elipse em (0, 0, 0).
        """
        # 1. Anomalia Média: M(t) = M0 + (2*pi / T) * t
        n = (2.0 * math.pi) / self.period  # Movimento médio diário (rad/dia)
        M = (self.m0 + n * time_days) % (2.0 * math.pi)

        # 2. Resolução da Equação de Kepler para Anomalia Excêntrica E
        E = self.solve_kepler(M)

        # 3. Coordenadas no plano orbital 2D (com o foco/Sol na origem)
        # x' = a * (cos(E) - e)  -> deslocado pelo foco 'a*e'
        # z' = b * sin(E)
        x_prime = self.a * (math.cos(E) - self.e)
        z_prime = self.b * math.sin(E)

        # 4. Rotação pela Inclinação Orbital (em torno do eixo X)
        # x = x'
        # y = z' * sin(i)
        # z = z' * cos(i)
        x = x_prime
        y = z_prime * math.sin(self.inclination)
        z = z_prime * math.cos(self.inclination)

        return glm.vec3(x, y, z)

    def generate_orbit_points(self, num_points: int = 240) -> List[Tuple[float, float, float]]:
        """
        Gera uma lista de pontos 3D contíguos que descrevem a trajetória elíptica
        completa para desenho da linha da órbita em OpenGL.
        """
        points: List[Tuple[float, float, float]] = []

        for k in range(num_points):
            # Percorre a anomalia excêntrica de 0 a 2*pi
            E = (2.0 * math.pi * float(k)) / float(num_points)

            x_prime = self.a * (math.cos(E) - self.e)
            z_prime = self.b * math.sin(E)

            x = x_prime
            y = z_prime * math.sin(self.inclination)
            z = z_prime * math.cos(self.inclination)

            points.append((x, y, z))

        return points
