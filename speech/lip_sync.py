"""
===============================================================================
Módulo: speech/lip_sync.py
Descrição: Sistema de sincronização labial baseado em fonemas, visemas e tempo.
Calcula coeficientes de abertura e formato da boca com interpolação suave.
===============================================================================
"""

from dataclasses import dataclass
import re
from typing import List, Tuple


@dataclass
class VisemeState:
    """Estado instantâneo da boca para animação facial."""
    mouth_open: float = 0.0     # 0.0 (fechada) a 1.0 (aberta - som A)
    mouth_round: float = 0.0    # 0.0 a 1.0 (arredondada - sons O, U)
    mouth_wide: float = 0.0     # 0.0 a 1.0 (esticada - sons E, I)
    jaw_drop: float = 0.0       # 0.0 a 1.0 (descida do queixo)


class LipSyncEngine:
    """
    Motor de Lip Sync fonético temporal em Língua Portuguesa.
    Mapeia o texto pronunciado e o timestamp atual do áudio para visemas realistas.
    """

    def __init__(self):
        self.phoneme_timeline: List[Tuple[float, float, str]] = [] # (start_time, end_time, viseme_code)
        self.current_state = VisemeState()
        self.target_state = VisemeState()
        self._total_duration: float = 1.0

    def prepare_speech(self, text: str, estimated_duration: float) -> None:
        """
        Gera a linha temporal de visemas a partir do texto e da duração estimada.
        Divide palavras e fonemas em intervalos temporais proporcionais.
        """
        self._total_duration = max(0.5, estimated_duration)
        self.phoneme_timeline.clear()

        # Tokenização limpa preservando pontuação para pausas
        words = re.findall(r"[\w]+|[.,!?;:]", text.lower())
        if not words:
            return

        # Atribui peso temporal relativo a cada elemento
        weights = []
        for w in words:
            if w in ".,!?;:":
                weights.append(3.0) # Pausa respiratória
            else:
                weights.append(len(w) * 1.0 + 1.0)

        total_weight = sum(weights)
        if total_weight == 0:
            return

        current_time = 0.0
        for w, weight in zip(words, weights):
            duration = (weight / total_weight) * self._total_duration
            start_t = current_time
            end_t = current_time + duration
            current_time = end_t

            if w in ".,!?;:":
                self.phoneme_timeline.append((start_t, end_t, "SILENCE"))
                continue

            # Decompõe a palavra em sílabas/sons fonéticos
            sub_count = len(w)
            sub_dur = duration / max(1, sub_count)
            for i, char in enumerate(w):
                s_t = start_t + i * sub_dur
                e_t = s_t + sub_dur
                if char in "aáàãâ":
                    code = "A"
                elif char in "oóòõôuú":
                    code = "O_U"
                elif char in "eéèêií":
                    code = "E_I"
                elif char in "mbp":
                    code = "M_B_P"
                elif char in "fv":
                    code = "F_V"
                else:
                    code = "MID"
                self.phoneme_timeline.append((s_t, e_t, code))

    def update(self, delta_time: float, current_playback_time: float, is_speaking: bool) -> VisemeState:
        """
        Calcula o estado suave da boca interpolando o visema alvo com delta_time.
        Se não estiver a falar, regressa ao repouso suavemente.
        """
        if not is_speaking or current_playback_time < 0.0 or current_playback_time > self._total_duration:
            # Em repouso
            self.target_state = VisemeState(mouth_open=0.0, mouth_round=0.0, mouth_wide=0.0, jaw_drop=0.0)
        else:
            # Procura o fonema correspondente ao tempo atual
            current_code = "SILENCE"
            for start_t, end_t, code in self.phoneme_timeline:
                if start_t <= current_playback_time < end_t:
                    current_code = code
                    break

            if current_code == "A":
                self.target_state = VisemeState(mouth_open=0.85, mouth_round=0.15, mouth_wide=0.3, jaw_drop=0.8)
            elif current_code == "O_U":
                self.target_state = VisemeState(mouth_open=0.45, mouth_round=0.9, mouth_wide=0.05, jaw_drop=0.4)
            elif current_code == "E_I":
                self.target_state = VisemeState(mouth_open=0.35, mouth_round=0.0, mouth_wide=0.8, jaw_drop=0.3)
            elif current_code == "M_B_P":
                # Lábios fechados sob pressão
                self.target_state = VisemeState(mouth_open=0.0, mouth_round=0.05, mouth_wide=0.2, jaw_drop=0.05)
            elif current_code == "F_V":
                self.target_state = VisemeState(mouth_open=0.2, mouth_round=0.1, mouth_wide=0.4, jaw_drop=0.15)
            elif current_code == "MID":
                self.target_state = VisemeState(mouth_open=0.3, mouth_round=0.2, mouth_wide=0.3, jaw_drop=0.25)
            else:
                self.target_state = VisemeState(mouth_open=0.0, mouth_round=0.0, mouth_wide=0.0, jaw_drop=0.0)

        # Interpolação suave exponencial (LERP) independente da taxa de quadros
        blend_speed = 18.0 * delta_time # Reatividade rápida e orgânica
        alpha = min(1.0, blend_speed)

        self.current_state.mouth_open += (self.target_state.mouth_open - self.current_state.mouth_open) * alpha
        self.current_state.mouth_round += (self.target_state.mouth_round - self.current_state.mouth_round) * alpha
        self.current_state.mouth_wide += (self.target_state.mouth_wide - self.current_state.mouth_wide) * alpha
        self.current_state.jaw_drop += (self.target_state.jaw_drop - self.current_state.jaw_drop) * alpha

        return self.current_state
