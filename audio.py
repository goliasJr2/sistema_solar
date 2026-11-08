"""
===============================================================================
Módulo: audio.py
Descrição: Som do simulador (vozes dos apresentadores, efeitos e ambiente),
           com pygame.mixer (pygame-ce).

  - Canal 0: voz (uma fala de cada vez; uma fala nova interrompe a anterior).
  - Canal 1: efeitos (whoosh, pop, certo/errado).
  - Canal 2: som ambiente em ciclo contínuo, com volume baixo.
  - Tecla [K]: silenciar / repor. Silenciar baixa o volume a 0 mas as falas
    continuam a "correr", para o texto e os gestos seguirem o mesmo ritmo.

Vozes: procura primeiro sounds/voices/gravadas/<chave>.(wav|ogg|mp3)
(gravações do grupo) e depois sounds/voices/<chave>.wav (geradas por
tools/gerar_vozes.py). Uma voz gerada só é usada se o texto no manifest.json
for igual ao texto atual — se o texto mudou, mostra-se só o texto.

Se não houver dispositivo de som (ou o pygame não estiver instalado), o
simulador continua a funcionar sem som.
===============================================================================
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import pygame
except Exception:  # pygame / pygame-ce não instalado
    pygame = None

AMBIENT_VOLUME = 0.22
VOICE_VOLUME = 1.0
SFX_VOLUME = 0.6


class AudioManager:
    def __init__(self, sounds_dir: Path):
        self.dir = Path(sounds_dir)
        self.enabled = False
        self.muted = False
        self._cache: Dict[str, Optional["pygame.mixer.Sound"]] = {}
        self._warned_outdated = False
        self.manifest: Dict[str, str] = {}
        manifest_path = self.dir / "voices" / "manifest.json"
        if manifest_path.exists():
            try:
                self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        if pygame is None:
            print("[Som] pygame não instalado — simulador sem som.")
            return
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.set_num_channels(8)
            self.voice_ch = pygame.mixer.Channel(0)
            self.sfx_ch = pygame.mixer.Channel(1)
            self.amb_ch = pygame.mixer.Channel(2)
            self.enabled = True
            print("[Som] Áudio ativo. [K] silencia / repõe o som.")
        except Exception as e:
            print(f"[Som Warning] Sem dispositivo de som ({e}) — simulador sem som.")

    # ------------------------------------------------------------- carregamento
    def _load(self, path: Path) -> Optional["pygame.mixer.Sound"]:
        key = str(path)
        if key not in self._cache:
            try:
                self._cache[key] = pygame.mixer.Sound(str(path)) if path.exists() else None
            except Exception as e:
                print(f"[Som Warning] {path.name}: {e}")
                self._cache[key] = None
        return self._cache[key]

    def voice_sound(self, key: str, text: str) -> Optional["pygame.mixer.Sound"]:
        """Som da fala `key`: gravação do grupo > voz gerada (se o texto coincidir)."""
        if not self.enabled:
            return None
        for ext in (".wav", ".ogg", ".mp3"):
            rec = self.dir / "voices" / "gravadas" / f"{key}{ext}"
            if rec.exists():
                return self._load(rec)
        gen = self.dir / "voices" / f"{key}.wav"
        if gen.exists():
            if self.manifest.get(key) == text:
                return self._load(gen)
            if not self._warned_outdated:
                self._warned_outdated = True
                print("[Som] Há textos alterados sem voz atualizada — corra tools/gerar_vozes.py.")
        return None

    ENVELOPE_RATE = 30   # amostras da curva de intensidade por segundo

    def voice_envelope(self, key: str, text: str):
        """Curva de intensidade da fala (0–1, 30 valores por segundo), usada para mexer
        a boca/cabeça do personagem ao ritmo da voz. None se não houver áudio."""
        snd = self.voice_sound(key, text)
        if snd is None:
            return None
        cache_key = ("env", key)
        if cache_key not in self._cache:
            try:
                import numpy as np
                freq, _, channels = pygame.mixer.get_init()
                samples = np.frombuffer(snd.get_raw(), dtype=np.int16).astype(np.float32)
                samples = samples.reshape(-1, channels).mean(axis=1) if channels > 1 else samples
                win = max(1, freq // self.ENVELOPE_RATE)
                n = len(samples) // win
                rms = np.sqrt((samples[: n * win].reshape(n, win) ** 2).mean(axis=1))
                ref = np.percentile(rms, 95) if n else 1.0
                env = np.clip(rms / (ref + 1e-6), 0.0, 1.0)
                self._cache[cache_key] = env
            except Exception:
                self._cache[cache_key] = None
        return self._cache[cache_key]

    # ------------------------------------------------------------------ tocar
    def play_voice(self, key: str, text: str) -> Optional[float]:
        """Toca a fala e devolve a sua duração em segundos (None se não houver áudio)."""
        snd = self.voice_sound(key, text)
        if snd is None:
            self.stop_voice()
            return None
        self.voice_ch.set_volume(0.0 if self.muted else VOICE_VOLUME)
        self.voice_ch.play(snd)
        return float(snd.get_length())

    def stop_voice(self) -> None:
        if self.enabled:
            self.voice_ch.stop()

    def play_sfx(self, name: str) -> None:
        if not self.enabled:
            return
        snd = self._load(self.dir / "sfx" / f"{name}.wav")
        if snd is not None:
            self.sfx_ch.set_volume(0.0 if self.muted else SFX_VOLUME)
            self.sfx_ch.play(snd)

    def start_ambient(self) -> None:
        if not self.enabled:
            return
        snd = self._load(self.dir / "sfx" / "ambient.wav")
        if snd is not None:
            self.amb_ch.set_volume(0.0 if self.muted else AMBIENT_VOLUME)
            self.amb_ch.play(snd, loops=-1, fade_ms=2500)

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        if self.enabled:
            self.voice_ch.set_volume(0.0 if self.muted else VOICE_VOLUME)
            self.sfx_ch.set_volume(0.0 if self.muted else SFX_VOLUME)
            self.amb_ch.set_volume(0.0 if self.muted else AMBIENT_VOLUME)
        print(f"[Som] {'SILENCIADO' if self.muted else 'LIGADO'}")
        return self.muted

    def cleanup(self) -> None:
        if self.enabled:
            pygame.mixer.quit()
            self.enabled = False
