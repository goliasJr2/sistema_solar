"""
===============================================================================
Módulo: blackhole.py
Descrição: Sistema Cósmico de Buracos Negros Relativísticos (8 Singularidades).
Conceitos aplicados:
  - Modelagem e Renderização de Objetos Relativísticos com Modelos 3D:
      * black_hole.glb (Singularidade Estelar Primária: Cygnus X-1)
      * black_hole_12.glb (Gargantua: Sistema Binário Relativístico)
      * black_hole_galaxy.glb (Sagitário A*: Buraco Negro Supermassivo Central)
      * black_hole (1).glb (V404 Cygni: Microquasar Relativístico)
      * black_hole (2).glb (GRO J1655-40: Vórtice Espaço-Temporal Escarlate)
      * black_hole (3).glb (M87* Progenitor: Horizonte das Sombras Cósmicas)
      * black_hole_12 (1).glb (Sagittarius B2: Gargantua Secundário Hiperdenso)
      * not_a_black_hole_-_1.glb (Anomalia Gravitacional Primordial Exótica)
  - Distribuição Esférica Espacial em 8 Direções Cósmicas Distintas.
  - Rotação Dinâmica dos Discos de Acreção a velocidades ultra-rápidas.
  - Alerta de Perigo Progressivo (5s) e Revelação de Singularidade (+5s).
  - Teletransporte e Enquadramento Frente a Frente com a tecla [ALT].
  - Alternância entre Singularidades Cósmicas com a tecla [G] ou [ALT].
===============================================================================
"""

from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import math
import glm

from model_loader import GLBModel
from shader import Shader


class BlackHole:
    """Representa uma singularidade gravitacional com disco de acreção rotativo."""

    def __init__(
        self,
        name: str,
        position: glm.vec3,
        scale: float,
        model_filename: str,
        models_dir: Path,
        accretion_rotation_speed: float = 35.0,
        warning_radius: float = 520.0,
        visible_radius: float = 420.0,
        pull_radius: float = 160.0,
        light_color: Optional[glm.vec3] = None,
        ambient_color: Optional[glm.vec3] = None,
        description: str = "",
    ):
        self.name = name
        self.position = glm.vec3(position)
        self.scale = scale
        self.rot_speed = accretion_rotation_speed
        self.current_rot_deg = 0.0
        self.warning_radius = warning_radius
        self.visible_radius = visible_radius
        self.pull_radius = pull_radius
        self.description = description

        self.light_color = light_color if light_color is not None else glm.vec3(1.0, 0.85, 0.5)
        self.ambient_color = ambient_color if ambient_color is not None else glm.vec3(0.85, 0.55, 0.25)
        self.is_revealed: bool = False

        self.model: Optional[GLBModel] = None
        p = models_dir / model_filename
        if p.exists():
            try:
                self.model = GLBModel(p)
                print(f"[Buraco Negro 3D] Modelo carregado para '{name}': {model_filename}")
            except Exception as e:
                print(f"[Buraco Negro Warning] Falha ao carregar {model_filename}: {e}")
        else:
            print(f"[Buraco Negro Warning] Ficheiro {model_filename} não encontrado em {models_dir}")

    def is_visible_from(self, view_pos: glm.vec3) -> bool:
        """
        Determina a visibilidade cósmica:
        - Se já foi revelado (após 10s ou tecla ALT), torna-se visível no espaço profundo.
        - Caso contrário, só surge ao entrar no seu raio de aproximação direta.
        """
        if self.is_revealed:
            return glm.length(self.position - view_pos) <= 6500.0
        return glm.length(self.position - view_pos) <= self.visible_radius

    def update(self, delta_time: float) -> None:
        """Faz rodar o disco de acreção de matéria incandescente."""
        self.current_rot_deg = (self.current_rot_deg + self.rot_speed * delta_time) % 360.0

    def get_model_matrix(self) -> glm.mat4:
        """Gera a matriz Model do buraco negro com rotação do disco de acreção."""
        m = glm.mat4(1.0)
        m = glm.translate(m, self.position)
        m = glm.rotate(m, math.radians(self.current_rot_deg), glm.vec3(0.0, 1.0, 0.0))
        m = glm.scale(m, glm.vec3(self.scale))
        return m

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        view_pos: glm.vec3,
    ) -> None:
        """Renderiza o buraco negro com iluminação emissiva e disco incandescente."""
        if not self.model:
            return

        shader.use()
        model_matrix = self.get_model_matrix()
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(model_matrix)))

        shader.set_mat4("uModel", model_matrix)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", self.position)
        shader.set_vec3("uLightColor", self.light_color)
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", self.ambient_color)
        shader.set_float("uShininess", 64.0)
        shader.set_float("uSpecularStrength", 0.7)

        self.model.draw()


class BlackHoleSystem:
    """Gere todas as 8 singularidades cósmicas espalhadas em diferentes direções cósmicas."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.black_holes: List[BlackHole] = []
        self.current_index: int = 0
        self.all_revealed: bool = False

        # ---------------------------------------------------------------------
        # 1. Singularidade Estelar Primária: Cygnus X-1 (Setor Frontal: -Z)
        # Rota de saída padrão ao deixar o Sol e avançar em linha reta
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Cygnus X-1 (Singularidade Primária)",
            position=glm.vec3(0.0, 25.0, -650.0),
            scale=24.0,
            model_filename="black_hole.glb",
            models_dir=models_dir,
            accretion_rotation_speed=45.0,
            warning_radius=550.0,
            visible_radius=420.0,
            pull_radius=150.0,
            light_color=glm.vec3(1.0, 0.85, 0.5),
            ambient_color=glm.vec3(0.95, 0.6, 0.2),
            description="Singularidade primária de acreção ultra-rápida no vazio frontal.",
        ))

        # ---------------------------------------------------------------------
        # 2. Gargantua (Sistema Binário Relativístico: Setor Leste: +X)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Gargantua (Sistema Binário Relativístico)",
            position=glm.vec3(800.0, 80.0, -200.0),
            scale=28.0,
            model_filename="black_hole_12.glb",
            models_dir=models_dir,
            accretion_rotation_speed=30.0,
            warning_radius=550.0,
            visible_radius=450.0,
            pull_radius=170.0,
            light_color=glm.vec3(1.0, 0.7, 0.3),
            ambient_color=glm.vec3(0.85, 0.45, 0.15),
            description="Buraco negro massivo com disco de acreção incandescente e lente gravitacional.",
        ))

        # ---------------------------------------------------------------------
        # 3. Sagitário A* (Buraco Negro Supermassivo: Setor Núcleo Profundo: -X, -Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Sagitário A* (Buraco Negro Supermassivo)",
            position=glm.vec3(-950.0, -120.0, -950.0),
            scale=45.0,
            model_filename="black_hole_galaxy.glb",
            models_dir=models_dir,
            accretion_rotation_speed=25.0,
            warning_radius=700.0,
            visible_radius=550.0,
            pull_radius=220.0,
            light_color=glm.vec3(0.8, 0.7, 1.0),
            ambient_color=glm.vec3(0.7, 0.5, 0.95),
            description="Coração supermassivo galáctico no centro do aglomerado cósmico.",
        ))

        # ---------------------------------------------------------------------
        # 4. V404 Cygni (Microquasar Relativístico: Setor Sudeste: +X, +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="V404 Cygni (Microquasar Relativístico)",
            position=glm.vec3(700.0, -90.0, 650.0),
            scale=22.0,
            model_filename="black_hole (1).glb",
            models_dir=models_dir,
            accretion_rotation_speed=55.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=140.0,
            light_color=glm.vec3(0.5, 0.8, 1.0),
            ambient_color=glm.vec3(0.3, 0.6, 0.9),
            description="Microquasar dinâmico com emissão intensa em raios-X e jatos azuis relativísticos.",
        ))

        # ---------------------------------------------------------------------
        # 5. GRO J1655-40 (Vórtice Escarlate: Setor Sudoeste: -X, +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="GRO J1655-40 (Vórtice Espaço-Temporal Escarlate)",
            position=glm.vec3(-750.0, 110.0, 600.0),
            scale=22.0,
            model_filename="black_hole (2).glb",
            models_dir=models_dir,
            accretion_rotation_speed=50.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=140.0,
            light_color=glm.vec3(1.0, 0.35, 0.3),
            ambient_color=glm.vec3(0.9, 0.25, 0.25),
            description="Singularidade escarlate com curvatura espaço-temporal extrema e plasma incandescente.",
        ))

        # ---------------------------------------------------------------------
        # 6. M87* Progenitor (Horizonte das Sombras Cósmicas: Setor Zénite / Superior: +Y)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="M87* Progenitor (Horizonte das Sombras Cósmicas)",
            position=glm.vec3(150.0, 750.0, -300.0),
            scale=26.0,
            model_filename="black_hole (3).glb",
            models_dir=models_dir,
            accretion_rotation_speed=35.0,
            warning_radius=520.0,
            visible_radius=420.0,
            pull_radius=160.0,
            light_color=glm.vec3(1.0, 0.6, 0.2),
            ambient_color=glm.vec3(0.85, 0.5, 0.1),
            description="Gigante cósmico situado no plano superior do espaço profundo.",
        ))

        # ---------------------------------------------------------------------
        # 7. Sagittarius B2 (Gargantua Secundário Hiperdenso: Setor Nadir / Inferior: -Y)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Sagittarius B2 (Gargantua Secundário Hiperdenso)",
            position=glm.vec3(-250.0, -750.0, 350.0),
            scale=28.0,
            model_filename="black_hole_12 (1).glb",
            models_dir=models_dir,
            accretion_rotation_speed=32.0,
            warning_radius=540.0,
            visible_radius=420.0,
            pull_radius=170.0,
            light_color=glm.vec3(0.85, 0.4, 0.95),
            ambient_color=glm.vec3(0.7, 0.3, 0.85),
            description="Singularidade gémea hiperdensa com oscilações violeta no tecido do espaço-tempo.",
        ))

        # ---------------------------------------------------------------------
        # 8. Anomalia Gravitacional Primordial (Setor Sul / Traseiro: +Z)
        # ---------------------------------------------------------------------
        self.black_holes.append(BlackHole(
            name="Anomalia Primordial (Buraco Negro Exótico)",
            position=glm.vec3(0.0, -50.0, 850.0),
            scale=25.0,
            model_filename="not_a_black_hole_-_1.glb",
            models_dir=models_dir,
            accretion_rotation_speed=40.0,
            warning_radius=500.0,
            visible_radius=400.0,
            pull_radius=150.0,
            light_color=glm.vec3(0.4, 1.0, 0.8),
            ambient_color=glm.vec3(0.2, 0.85, 0.65),
            description="Anomalia misteriosa com distorção gravitacional quântica única.",
        ))

    def reveal_all(self) -> None:
        """Revela todas as singularidades no espaço exterior."""
        self.all_revealed = True
        for bh in self.black_holes:
            bh.is_revealed = True
        print("[Buraco Negro] Todas as 8 singularidades cósmicas reveladas no espaço profundo!")

    def align_primary_ahead(self, camera_pos: glm.vec3, camera_front: glm.vec3, distance: float = 260.0) -> None:
        """
        Posiciona a singularidade primária diretamente à frente da trajetória da câmara.
        Garante que, após 10 segundos de avanço com a seta para cima, o utilizador
        vê o buraco negro imediatamente à sua frente.
        """
        if self.black_holes:
            primary = self.black_holes[0]
            primary.position = camera_pos + glm.normalize(camera_front) * distance
            primary.is_revealed = True
            print(f"[Buraco Negro] {primary.name} posicionado diretamente à frente em {primary.position}!")

    def get_primary(self) -> BlackHole:
        """Retorna o buraco negro primário (Cygnus X-1)."""
        return self.black_holes[0]

    def get_nearest(self, pos: glm.vec3) -> BlackHole:
        """Retorna o buraco negro mais próximo da coordenada fornecida."""
        return min(self.black_holes, key=lambda bh: glm.length(bh.position - pos))

    def update(self, delta_time: float) -> None:
        """Atualiza a rotação de todos os discos de acreção."""
        for bh in self.black_holes:
            bh.update(delta_time)

    def check_proximity(self, camera_pos: glm.vec3) -> Optional[Dict[str, Any]]:
        """
        Calcula a proximidade da câmara aos buracos negros.
        Retorna informações para o alerta na interface caso esteja na área de atuação.
        """
        closest_info = None
        min_dist = float("inf")

        for bh in self.black_holes:
            dist = glm.length(bh.position - camera_pos)
            if dist < bh.warning_radius and dist < min_dist:
                min_dist = dist
                closest_info = {
                    "name": bh.name,
                    "distance": dist,
                    "warning_radius": bh.warning_radius,
                    "visible_radius": bh.visible_radius,
                    "pull_radius": bh.pull_radius,
                    "position": bh.position,
                    "is_critical": dist < bh.pull_radius,
                }

        return closest_info

    def draw(self, shader: Shader, view: glm.mat4, proj: glm.mat4, view_pos: glm.vec3) -> None:
        """Renderiza todas as singularidades que se encontrem visíveis."""
        for bh in self.black_holes:
            if bh.is_visible_from(view_pos):
                bh.draw(shader, view, proj, view_pos)

    def cycle_next(self) -> BlackHole:
        """Alterna para o próximo buraco negro (Teclas G e ALT)."""
        self.current_index = (self.current_index + 1) % len(self.black_holes)
        selected = self.black_holes[self.current_index]
        print(f"[Buraco Negro] Foco alternado ({self.current_index + 1}/{len(self.black_holes)}): {selected.name}")
        return selected

    def get_current(self) -> BlackHole:
        """Retorna o buraco negro atualmente selecionado."""
        return self.black_holes[self.current_index]
