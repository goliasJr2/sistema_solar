"""
===============================================================================
Módulo: speech/audio_player.py
Descrição: Reprodutor de áudio com pygame.mixer e monitorização de tempo.
Oferece controlo total de reprodução, volume e eventos de conclusão.
===============================================================================
"""

import time
from typing import Optional, Callable
import pygame


class AudioPlayer:
    """Reprodutor de áudio thread-safe baseado no pygame.mixer."""

    def __init__(self, initial_volume: float = 1.0):
        self._volume = max(0.0, min(1.0, initial_volume))
        self._is_paused = False
        self._current_file: Optional[str] = None
        self._start_time: float = 0.0
        self._pause_time: float = 0.0
        self._paused_duration: float = 0.0
        self._on_finish_callback: Optional[Callable[[], None]] = None
        self._is_active = False

        self._init_mixer()

    def _init_mixer(self) -> None:
        """Inicializa o subsistema de áudio se ainda não estiver ativo."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            except Exception as e:
                print(f"[AudioPlayer] Aviso ao inicializar mixer: {e}")

    def play(self, filepath: str, on_finish: Optional[Callable[[], None]] = None) -> bool:
        """Carrega e inicia a reprodução do ficheiro áudio especificado."""
        self._init_mixer()
        try:
            self.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()

            self._current_file = filepath
            self._start_time = time.time()
            self._pause_time = 0.0
            self._paused_duration = 0.0
            self._is_paused = False
            self._on_finish_callback = on_finish
            self._is_active = True
            return True
        except Exception as e:
            print(f"[AudioPlayer] Erro ao reproduzir {filepath}: {e}")
            self._is_active = False
            return False

    def pause(self) -> None:
        """Pausa a reprodução atual."""
        if self._is_active and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            self._pause_time = time.time()

    def resume(self) -> None:
        """Retoma a reprodução pausada."""
        if self._is_active and self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            if self._pause_time > 0.0:
                self._paused_duration += (time.time() - self._pause_time)
                self._pause_time = 0.0

    def stop(self) -> None:
        """Interrompe imediatamente a reprodução."""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self._is_active = False
        self._is_paused = False
        self._current_file = None
        self._on_finish_callback = None

    def set_volume(self, volume: float) -> None:
        """Ajusta o volume [0.0 a 1.0]."""
        self._volume = max(0.0, min(1.0, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self._volume)

    @property
    def volume(self) -> float:
        return self._volume

    def is_playing(self) -> bool:
        """Verifica se há áudio a tocar ativamente (não pausado)."""
        if not self._is_active:
            return False
        if self._is_paused:
            return False
        if pygame.mixer.get_init():
            return pygame.mixer.music.get_busy()
        return False

    def get_playback_time(self) -> float:
        """
        Retorna o tempo de reprodução decorrido em segundos.
        Essencial para a sincronização labial (Lip Sync).
        """
        if not self._is_active:
            return 0.0
        if self._is_paused:
            return max(0.0, self._pause_time - self._start_time - self._paused_duration)
        return max(0.0, time.time() - self._start_time - self._paused_duration)

    def update(self) -> None:
        """Atualização periódica por frame para deteção de fim de faixa."""
        if self._is_active and not self._is_paused:
            if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                # Música terminou
                self._is_active = False
                cb = self._on_finish_callback
                self._on_finish_callback = None
                if cb:
                    cb()
