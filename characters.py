"""
===============================================================================
Módulo: characters.py
Descrição: Personagens 3D "apresentadores" — cada planeta tem o seu personagem,
           que aparece ao lado do planeta quando este é focado
           (teclas 1–8, TAB ou clique com o rato).
Conceitos aplicados:
  - Configuração orientada por dados (characters.json): trocar um personagem
    não exige alterar código.
  - Carregamento preguiçoso (lazy loading) com cache: cada modelo .glb só é
    lido e enviado para a GPU na primeira vez que o seu planeta é focado.
  - Posicionamento relativo à câmara: o personagem fica à direita do planeta
    no plano da câmara (vetor camera.right), à escala do raio visual do planeta.
  - Billboarding em Y: rotação em torno do eixo vertical para ficar virado para
    a câmara, mais um balanço e flutuação suaves (animação por tempo).
  - Animação de entrada (escala 0 -> 1 com easing) ao trocar de planeta.
  - Iluminação "de estúdio": luz posicionada junto à câmara para o personagem
    estar sempre visível, mesmo quando o planeta está no lado noturno.
===============================================================================
"""

import json
import math
from pathlib import Path
from typing import Dict, Optional

import glm
from OpenGL.GL import glDisable, glEnable, GL_CULL_FACE

from model_loader import GLBModel
from shader import Shader


class PlanetCharacters:
    """Gere e desenha o personagem apresentador do planeta selecionado."""

    APPEAR_SECONDS = 0.6   # Duração da animação de entrada

    def __init__(self, base_dir: Path, config_file: str = "characters.json"):
        self.base_dir = Path(base_dir)
        self.config: Dict[str, dict] = {}
        self.defaults = {"height_factor": 1.4, "side_offset": 2.1}
        self._models: Dict[str, Optional[GLBModel]] = {}   # cache: caminho -> modelo (None = falhou)
        self._active_id: Optional[str] = None
        self._appear_t = 0.0
        self._load_config(self.base_dir / config_file)

    # ------------------------------------------------------------------ config
    def _load_config(self, path: Path) -> None:
        if not path.exists():
            print(f"[Personagens] {path.name} não encontrado — planetas sem apresentador.")
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Personagens Warning] Erro ao ler {path.name}: {e}")
            return
        self.defaults.update(raw.get("defaults", {}))
        self.config = {k: v for k, v in raw.get("planets", {}).items() if isinstance(v, dict)}
        n = sum(1 for v in self.config.values() if v.get("model"))
        print(f"[Personagens] {n} apresentadores configurados em {path.name}.")

    def info_for(self, body_id: Optional[str]) -> Optional[dict]:
        """Dados do personagem de um planeta (para o painel da UI), ou None."""
        entry = self.config.get(body_id or "")
        if not entry or not entry.get("model"):
            return None
        return entry

    def _get_model(self, rel_path: str) -> Optional[GLBModel]:
        if rel_path not in self._models:
            path = self.base_dir / rel_path
            try:
                self._models[rel_path] = GLBModel(path)
                print(f"[Personagens] Modelo carregado: {path.name}")
            except Exception as e:
                self._models[rel_path] = None
                print(f"[Personagens Warning] Falha ao carregar {rel_path}: {e}")
        return self._models[rel_path]

    # ------------------------------------------------------------------ ciclo
    def update(self, delta_time: float, selected_id: Optional[str]) -> None:
        """Reinicia a animação de entrada sempre que muda o planeta selecionado."""
        if selected_id != self._active_id:
            self._active_id = selected_id
            self._appear_t = 0.0
        else:
            self._appear_t = min(self.APPEAR_SECONDS, self._appear_t + delta_time)

    def draw(
        self,
        shader: Shader,
        view: glm.mat4,
        proj: glm.mat4,
        camera,
        body,
        current_time: float,
    ) -> None:
        """Desenha o personagem do planeta `body` (objeto CelestialBody selecionado)."""
        if body is None:
            return
        entry = self.info_for(self._active_id)
        if entry is None:
            return
        model = self._get_model(entry["model"])
        if model is None:
            return

        radius = float(body.visual_radius)
        height = radius * float(entry.get("height_factor", self.defaults["height_factor"]))
        side = radius * float(entry.get("side_offset", self.defaults["side_offset"]))

        # Animação de entrada com easing (ease-out-back: cresce e assenta)
        t = self._appear_t / self.APPEAR_SECONDS
        c = 1.70158
        appear = 1.0 + (c + 1.0) * (t - 1.0) ** 3 + c * (t - 1.0) ** 2 if t > 0.0 else 0.0
        if appear <= 0.001:
            return

        # Posição: à direita do planeta no plano da câmara, a flutuar ligeiramente
        bob = math.sin(current_time * 1.6) * radius * 0.06
        pos = glm.vec3(body.current_position) + camera.right * side + camera.up * bob

        # Rotação em Y para ficar de frente para a câmara (+ balanço suave)
        to_cam = camera.position - pos
        yaw = math.atan2(to_cam.x, to_cam.z) + math.sin(current_time * 0.9) * math.radians(12.0)

        # O GLBModel normaliza pelo raio base; os personagens convertidos têm 2.0 de
        # altura antes disso, logo a altura em unidades do modelo é 2 / base_radius.
        model_height = 2.0 / max(model.base_radius, 1e-6)
        scale = (height / model_height) * appear

        m = glm.mat4(1.0)
        m = glm.translate(m, pos)
        m = glm.rotate(m, yaw, glm.vec3(0.0, 1.0, 0.0))
        m = glm.scale(m, glm.vec3(scale))
        normal_matrix = glm.mat3(glm.transpose(glm.inverse(m)))

        # Luz "de estúdio": acima e atrás da câmara, para o personagem nunca ficar às escuras
        light_pos = camera.position + camera.up * (radius * 4.0) + camera.right * (radius * 2.0)

        shader.use()
        shader.set_mat4("uModel", m)
        shader.set_mat4("uView", view)
        shader.set_mat4("uProjection", proj)
        shader.set_mat3("uNormalMatrix", normal_matrix)
        shader.set_vec3("uLightPos", light_pos)
        shader.set_vec3("uLightColor", glm.vec3(1.0, 0.97, 0.92))
        shader.set_vec3("uViewPos", camera.position)
        shader.set_vec3("uAmbientColor", glm.vec3(0.38, 0.38, 0.42))
        shader.set_float("uShininess", 24.0)
        shader.set_float("uSpecularStrength", 0.25)

        # Algumas malhas (cabelo, roupa) têm faces viradas para os dois lados
        glDisable(GL_CULL_FACE)
        model.draw()
        glEnable(GL_CULL_FACE)

    def cleanup(self) -> None:
        for m in self._models.values():
            if m is not None:
                m.cleanup()
        self._models.clear()
