"""
===============================================================================
Módulo: blackhole.py
Descrição: Buraco Negro Supermassivo (Sagitário A*) e Buracos Negros Estelares Secundários.
Conceitos aplicados:
  - Modelagem e Renderização de Objetos Relativísticos com Modelos 3D:
      * black_hole_galaxy.glb (Buraco Negro Central Supermassivo).
      * black_hole.glb e black_hole_12.glb (Buracos Negros Estelares Visitáveis).
  - Rotação Dinâmica do Disco de Acreção a velocidades ultra-rápidas.
  - Navegação Rápida com a tecla G (alternância entre buracos negros cósmicos).
===============================================================================
"""

from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import math
import glm

from model_loader import GLBModel
from shader import Shader


class BlackHole:
    """Representa uma singularidade gravitacional com disco de acreção."""

    def __init__(
        self,
        name: str,
        position: glm.vec3,
        scale: float,
        model_filename: str,
        models_dir: Path,
        accretion_rotation_speed: float = 35.0,
        warning_radius: float = 480.0,
        visible_radius: float = 360.0,
        pull_radius: float = 160.0,
    ):
        self.name = name
        self.position = position
        self.scale = scale
        self.rot_speed = accretion_rotation_speed
        self.current_rot_deg = 0.0
        self.warning_radius = warning_radius
        self.visible_radius = visible_radius
        self.pull_radius = pull_radius

        self.model: Optional[GLBModel] = None
        p = models_dir / model_filename
        if p.exists():
            try:
                self.model = GLBModel(p)
                print(f"[Buraco Negro 3D] Modelo carregado para '{name}': {model_filename}")
            except Exception as e:
                print(f"[Buraco Negro Warning] Falha ao carregar {model_filename}: {e}")

    def is_visible_from(self, view_pos: glm.vec3) -> bool:
        """Só se torna visível quando o observador navega até ao seu alcance cósmico."""
        return glm.length(self.position - view_pos) <= self.visible_radius

    def update(self, delta_time: float) -> None:
        """Faz rodar o disco de acreção de matéria incandescente."""
        self.current_rot_deg = (self.current_rot_deg + self.rot_speed * delta_time) % 360.0

    def get_model_matrix(self) -> glm.mat4:
        """Gera a matriz Model do buraco negro."""
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
        """Renderiza o buraco negro com iluminação emissiva auto-iluminada."""
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
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.85, 0.5))
        shader.set_vec3("uViewPos", view_pos)
        shader.set_vec3("uAmbientColor", glm.vec3(0.8, 0.5, 0.2))  # Radiação de Hawking e disco quente
        shader.set_float("uShininess", 64.0)
        shader.set_float("uSpecularStrength", 0.6)

        self.model.draw()


class BlackHoleSystem:
    """Gere todos os buracos negros da cena cósmica."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.black_holes: List[BlackHole] = []
        self.current_index: int = 0

        # 1. Buraco Negro Estelar no Vazio Profundo (ao sair do Sistema Solar na direção frontal -Z)
        # Ao navegar para a frente por ~10 segundos, o observador entra na sua área de atuação!
        cygnus_x1 = BlackHole(
            name="Cygnus X-1 (Singularidade Estelar)",
            position=glm.vec3(0.0, 0.0, -850.0),
            scale=18.0,
            model_filename="black_hole.glb",
            models_dir=models_dir,
            accretion_rotation_speed=55.0,
            warning_radius=480.0,
            visible_radius=360.0,
            pull_radius=150.0,
        )
        self.black_holes.append(cygnus_x1)

        # 2. Buraco Negro Binário: Gargantua (setor exterior lateral)
        gargantua = BlackHole(
            name="Gargantua (Sistema Binário Relativístico)",
            position=glm.vec3(1100.0, 150.0, 750.0),
            scale=26.0,
            model_filename="black_hole_12.glb",
            models_dir=models_dir,
            accretion_rotation_speed=30.0,
            warning_radius=500.0,
            visible_radius=380.0,
            pull_radius=170.0,
        )
        self.black_holes.append(gargantua)

        # 3. Buraco Negro Central da Galáxia: Sagitário A* (profundezas galácticas)
        sagittarius_a = BlackHole(
            name="Sagitário A* (Buraco Negro Supermassivo)",
            position=glm.vec3(-1400.0, -200.0, -1800.0),
            scale=42.0,
            model_filename="black_hole_galaxy.glb",
            models_dir=models_dir,
            accretion_rotation_speed=40.0,
            warning_radius=650.0,
            visible_radius=500.0,
            pull_radius=220.0,
        )
        self.black_holes.append(sagittarius_a)

    def update(self, delta_time: float) -> None:
        """Atualiza a rotação dos discos de acreção."""
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
        """
        Renderiza apenas os buracos negros que estejam dentro do raio de visibilidade.
        Ficam ocultos no Sistema Solar e só surgem quando nos aproximamos pelo espaço profundo.
        """
        for bh in self.black_holes:
            if bh.is_visible_from(view_pos):
                bh.draw(shader, view, proj, view_pos)

    def cycle_next(self) -> BlackHole:
        """Alterna para o próximo buraco negro (Tecla G)."""
        self.current_index = (self.current_index + 1) % len(self.black_holes)
        selected = self.black_holes[self.current_index]
        print(f"[Buraco Negro] Foco alternado (Tecla G) para: {selected.name}")
        return selected

    def get_current(self) -> BlackHole:
        """Retorna o buraco negro atualmente selecionado."""
        return self.black_holes[self.current_index]
