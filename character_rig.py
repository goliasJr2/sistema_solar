"""
===============================================================================
Módulo: character_rig.py
Descrição: Animação procedural do esqueleto dos personagens (sem OpenGL).
Conceitos aplicados:
  - Hierarquia de ossos (cinemática direta / forward kinematics):
        C_i = C_pai · L_i · Q_i
    onde L_i é a transformação local do osso na pose de ligação e Q_i a
    rotação animada, expressa no referencial do próprio osso.
  - Skinning linear (Linear Blend Skinning): a matriz de cada osso enviada ao
    shader é S_i = C_i · G_i⁻¹ (G_i = matriz global na pose de ligação). Na
    pose de ligação S_i = identidade; o vertex shader mistura até 4 S_i por
    vértice, pesadas pelos pesos de pele.
  - Rotações definidas no espaço do mundo do personagem (ex.: "baixar o braço
    em direção a -Y") e convertidas para o referencial do osso:
        Q_i = R_iᵀ · R_mundo · R_i
  - Fórmula de Rodrigues para rotações em torno de um eixo arbitrário.

Espaço do personagem (garantido pelo tools/fbx_to_glb.py):
  +Y para cima, de frente para +Z, altura 2.0. Os nomes dos ossos seguem o
  esqueleto Mixamo ("mixamorig:LeftArm", ...); só o sufixo depois de ':' conta,
  por isso qualquer personagem com auto-rig da Mixamo é animado.

Animações:
  - Repouso (idle): braços baixam da pose em T, cotovelos ligeiramente
    dobrados, respiração no tronco, cabeça a olhar à volta, balanço da anca.
  - Aceno (wave): o braço direito sobe e o antebraço acena; usado quando o
    personagem aparece, misturado com o repouso pelo peso `wave` (0 a 1).
  - Apontar (point): o braço direito estende-se na direção do planeta e a
    cabeça/tronco viram-se para ele; usado enquanto conta um facto.
  - Falar (talk): acenos de cabeça e a mão esquerda a gesticular, enquanto
    a voz está a tocar.
  Todos os pesos são misturados entre si, por isso as transições são suaves.
===============================================================================
"""

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

UP = np.array([0.0, 1.0, 0.0])
DOWN = -UP
FORWARD = np.array([0.0, 0.0, 1.0])
SIDE = np.array([1.0, 0.0, 0.0])


def rotation(axis: Sequence[float], angle: float) -> np.ndarray:
    """Matriz 3x3 de rotação de `angle` radianos em torno de `axis` (Rodrigues)."""
    a = np.asarray(axis, dtype=np.float64)
    n = np.linalg.norm(a)
    if n < 1e-9 or abs(angle) < 1e-9:
        return np.eye(3)
    x, y, z = a / n
    c, s = math.cos(angle), math.sin(angle)
    k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + s * k + (1 - c) * (k @ k)


def _angle_between(u: np.ndarray, v: np.ndarray) -> float:
    cu = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12)
    return math.acos(max(-1.0, min(1.0, cu)))


def rotation_between(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Menor rotação que leva a direção u à direção v."""
    return rotation(np.cross(u, v), _angle_between(u, v))


def blend_rotations(a: np.ndarray, b: np.ndarray, w: float) -> np.ndarray:
    """Mistura duas rotações (interpolação linear + reortogonalização por SVD)."""
    if w <= 0.0:
        return a
    if w >= 1.0:
        return b
    u, _, vt = np.linalg.svd((1.0 - w) * a + w * b)
    r = u @ vt
    if np.linalg.det(r) < 0:
        u[:, -1] *= -1
        r = u @ vt
    return r


class ProceduralRig:
    """Calcula, a cada instante, a paleta de matrizes de ossos (S_i) para o shader."""

    def __init__(self, names: List[str], parents: np.ndarray, bind_global: np.ndarray):
        self.names = [str(n) for n in names]
        self.parents = np.asarray(parents, dtype=np.int64)
        self.G = np.asarray(bind_global, dtype=np.float64)
        self.count = len(self.names)
        self.G_inv = np.linalg.inv(self.G)

        # Transformação local de ligação de cada osso (relativa ao pai)
        self.L = np.empty_like(self.G)
        for i, p in enumerate(self.parents):
            self.L[i] = self.G[i] if p < 0 else self.G_inv[p] @ self.G[i]

        # Referencial de rotação de cada osso (sem escala), para converter rotações do mundo
        self.R = np.empty((self.count, 3, 3))
        for i in range(self.count):
            m = self.G[i][:3, :3]
            u, _, vt = np.linalg.svd(m)
            self.R[i] = u @ vt

        # Ossos pelo nome curto ("mixamorig:LeftArm" -> "LeftArm")
        # (o maxilar "Jaw" só existe em alguns modelos, ex.: Warrok)
        self.idx: Dict[str, int] = {}
        for i, n in enumerate(self.names):
            self.idx.setdefault(n.split(":")[-1], i)

        self._pos = self.G[:, :3, 3]
        self._dir_cache: Dict[str, Optional[np.ndarray]] = {}

    # ------------------------------------------------------------- utilitários
    def _bone_dir(self, bone: str, child: str) -> Optional[np.ndarray]:
        """Direção do osso na pose de ligação (da articulação até à do osso filho)."""
        key = bone + ">" + child
        if key not in self._dir_cache:
            a, b = self.idx.get(bone), self.idx.get(child)
            d = None
            if a is not None and b is not None:
                v = self._pos[b] - self._pos[a]
                if np.linalg.norm(v) > 1e-6:
                    d = v / np.linalg.norm(v)
            self._dir_cache[key] = d
        return self._dir_cache[key]

    def _world_to_local(self, i: int, rot_world: np.ndarray) -> np.ndarray:
        return self.R[i].T @ rot_world @ self.R[i]

    # ------------------------------------------------------------------- pose
    def pose_rotations(self, t: float, wave: float, point: float = 0.0,
                       point_dir: Optional[Sequence[float]] = None,
                       talk: float = 0.0, mouth: float = 0.0) -> Dict[int, np.ndarray]:
        """Rotações no mundo do personagem para cada osso animado, no instante t.

        wave      0–1: aceno com o braço direito.
        point     0–1: braço direito estendido na direção `point_dir`
                  (vetor no espaço do personagem, ex.: para o planeta); a cabeça
                  e o tronco viram-se nessa direção.
        talk      0–1: gestos de fala (acenos de cabeça, mão esquerda a gesticular).
        mouth     0–1: intensidade da voz neste instante (curva do áudio): abre o
                  maxilar (osso "Jaw", se existir) e acentua os movimentos da cabeça.
        """
        rots: Dict[int, np.ndarray] = {}

        def put(bone: str, r: np.ndarray) -> None:
            i = self.idx.get(bone)
            if i is not None:
                rots[i] = r @ rots.get(i, np.eye(3))

        breathe = math.sin(t * 1.7)
        wave = max(0.0, min(1.0, wave))
        point = max(0.0, min(1.0, point)) if point_dir is not None else 0.0
        talk = max(0.0, min(1.0, talk))
        target = None
        look_yaw = 0.0
        if point > 0.0:
            target = np.asarray(point_dir, dtype=np.float64)
            target = target / (np.linalg.norm(target) + 1e-12)
            # Para onde olhar (ângulo horizontal), limitado a ±55°
            look_yaw = max(-math.radians(55), min(math.radians(55), math.atan2(target[0], target[2])))

        # Anca e tronco: balanço lento + respiração; ao apontar, o tronco roda um pouco
        put("Hips", rotation(UP, math.radians(4.0) * math.sin(t * 0.55)))
        put("Spine", rotation(SIDE, math.radians(1.5) * breathe))
        put("Spine1", rotation(SIDE, math.radians(1.5) * breathe))
        put("Spine2", rotation(UP, 0.3 * look_yaw * point)
            @ rotation(SIDE, math.radians(1.0) * breathe)
            @ rotation(FORWARD, math.radians(2.0) * math.sin(t * 0.55)))

        # Cabeça: olha à volta; acena ao falar; olha para o planeta ao apontar
        mouth = max(0.0, min(1.0, mouth))
        nod = (math.radians(5.0) * talk * math.sin(t * 6.5) * (0.6 + 0.4 * math.sin(t * 1.3))
               - math.radians(4.0) * mouth)   # a cabeça sobe ligeiramente nas sílabas fortes
        put("Jaw", rotation(SIDE, math.radians(16.0) * mouth))
        put("Neck", rotation(UP, math.radians(6.0) * math.sin(t * 0.45) * (1 - point) + 0.3 * look_yaw * point))
        put("Head", rotation(UP, math.radians(10.0) * math.sin(t * 0.45 + 0.6) * (1 - point) + 0.4 * look_yaw * point)
            @ rotation(SIDE, math.radians(4.0) * math.sin(t * 0.8) + nod)
            @ rotation(FORWARD, math.radians(-8.0) * wave))

        for side, waving in (("Left", False), ("Right", True)):
            arm_dir = self._bone_dir(f"{side}Arm", f"{side}ForeArm")
            fore_dir = self._bone_dir(f"{side}ForeArm", f"{side}Hand")
            if arm_dir is None:
                continue
            w = wave if waving else 0.0
            gesture = talk if not waving else 0.0   # a mão esquerda gesticula ao falar

            # Braço: de onde estiver (pose em T ou A) até ~20° do corpo, com
            # ligeira oscilação. A aceno, sobe até ~35° acima da horizontal.
            down_axis = np.cross(arm_dir, DOWN)
            to_down = _angle_between(arm_dir, DOWN)
            idle_angle = to_down - math.radians(20.0 + 6.0 * gesture) + math.radians(2.0) * breathe
            wave_angle = to_down - math.radians(125.0)
            arm_rot = rotation(down_axis, (1 - w) * idle_angle + w * wave_angle)
            # Braços ligeiramente para a frente do corpo (mais ao gesticular)
            arm_rot = rotation(np.cross(DOWN, FORWARD), math.radians(8.0 + 14.0 * gesture) * (1 - w)) @ arm_rot

            fore_rot = np.eye(3)
            if fore_dir is not None:
                # Cotovelo: dobra para a frente em repouso; no aceno fica vertical e abana;
                # ao gesticular, o antebraço sobe e desce como quem explica
                gest_angle = (35.0 + 15.0 * math.sin(t * 2.6)) * gesture
                bend_fwd = rotation(np.cross(fore_dir, FORWARD), math.radians(18.0 + gest_angle) * (1 - w))
                bend_up = rotation(np.cross(fore_dir, UP), math.radians(60.0) * w)
                wag = rotation(FORWARD, math.radians(22.0) * w * math.sin(t * 9.0))
                fore_rot = wag @ bend_up @ bend_fwd

            if waving and target is not None:
                # Apontar: braço na direção do alvo (ligeiramente abaixo, mais natural),
                # antebraço quase esticado
                aim = target + np.array([0.0, -0.15, 0.0])
                aim_rot = rotation_between(arm_dir, aim / np.linalg.norm(aim))
                arm_rot = blend_rotations(arm_rot, aim_rot, point)
                if fore_dir is not None:
                    fore_rot = blend_rotations(fore_rot, rotation(np.cross(fore_dir, FORWARD), math.radians(6.0)), point)

            put(f"{side}Arm", arm_rot)
            if fore_dir is not None:
                put(f"{side}ForeArm", fore_rot)
            put(f"{side}Hand", rotation(FORWARD, math.radians(6.0 + 10.0 * gesture) * math.sin(t * (1.1 + 1.5 * gesture) + (0 if waving else 1.5))))
        return rots

    def palette(self, t: float, wave: float = 0.0, point: float = 0.0,
                point_dir: Optional[Sequence[float]] = None, talk: float = 0.0,
                mouth: float = 0.0) -> np.ndarray:
        """Matrizes S_i = C_i · G_i⁻¹ (float32, (B, 4, 4)) prontas para o shader."""
        rots = self.pose_rotations(t, wave, point, point_dir, talk, mouth)
        C = np.empty_like(self.G)
        for i in range(self.count):
            local = self.L[i]
            if i in rots:
                q = np.eye(4)
                q[:3, :3] = self._world_to_local(i, rots[i])
                local = local @ q
            p = self.parents[i]
            C[i] = local if p < 0 else C[p] @ local
        return np.einsum("bij,bjk->bik", C, self.G_inv).astype(np.float32)


def skin_vertices(palette: np.ndarray, positions: np.ndarray, joints: np.ndarray,
                  weights: np.ndarray) -> np.ndarray:
    """Skinning no CPU (o mesmo cálculo do shader) — usado para pré-visualizações."""
    hom = np.concatenate([positions, np.ones((len(positions), 1))], axis=1)
    out = np.zeros((len(positions), 3))
    for k in range(4):
        m = palette[joints[:, k].astype(np.int64)]          # (n, 4, 4)
        out += weights[:, k:k + 1] * np.einsum("nij,nj->ni", m, hom)[:, :3]
    return out
