"""
===============================================================================
Módulo: guide/guide_controller.py
Descrição: Orquestrador e controlador do Astronomical Virtual Guide.
Coordena a lição educativa, síntese vocal assíncrona, áudio, lip sync e animação.
===============================================================================
"""

from typing import Optional, Callable, Tuple
from educational.lesson_manager import LessonManager
from educational.earth_content import LessonSection
from speech.text_to_speech import TextToSpeechEngine
from speech.audio_player import AudioPlayer
from speech.lip_sync import LipSyncEngine, VisemeState
from .guide_animation import GuideAnimationEngine, SkeletalTransformState
from .facial_animation import FacialAnimationController, FacialParameters


class GuideController:
    """Controlador central de lógica e multimédia do Guia Virtual."""

    def __init__(self, planet_name: str = "Terra"):
        self.planet_name = planet_name
        self.lesson_manager = LessonManager(planet_name)
        self.tts = TextToSpeechEngine()
        self.audio_player = AudioPlayer(initial_volume=1.0)
        self.lip_sync = LipSyncEngine()
        self.anim_engine = GuideAnimationEngine()
        self.facial_ctrl = FacialAnimationController()

        self.is_active: bool = False
        self.is_muted: bool = False
        self._saved_volume: float = 1.0

        # Estados interpolados em cache para renderização suave
        self.last_skeletal_state: SkeletalTransformState = self.anim_engine.update(0.016)
        self.last_facial_params: FacialParameters = self.facial_ctrl.update(0.016, VisemeState())

        # Conectar callbacks da lição
        self.lesson_manager.on_section_changed = self._on_section_changed
        self.lesson_manager.on_lesson_completed = self._on_lesson_completed

    def activate(self, is_meditating: bool = False) -> None:
        """Ativa o Guia e inicia a apresentação educativa."""
        self.is_active = True
        self.anim_engine.is_meditating = is_meditating
        self.anim_engine.set_state("LISTENING")
        self.facial_ctrl.set_expression("HAPPY")
        sec = self.lesson_manager.start()
        self._speak_section(sec)

    def deactivate(self) -> None:
        """Encerra a apresentação e desliga áudio."""
        self.is_active = False
        self.audio_player.stop()
        self.lesson_manager.reset()
        self.anim_engine.set_state("IDLE")

    def _speak_section(self, section: LessonSection) -> None:
        """Sintetiza e reproduz o texto da seção atual com Lip Sync."""
        self.anim_engine.set_state("THINKING")
        self.facial_ctrl.set_expression("THINKING")

        # Prepara a linha temporal fonética
        self.lip_sync.prepare_speech(section.speech_text, section.estimated_duration_sec)

        def _on_audio_ready(audio_path: str):
            if not self.is_active:
                return
            self.anim_engine.set_state("TALKING")
            self.facial_ctrl.set_expression("TALKING")
            self.audio_player.play(audio_path, on_finish=self._on_speech_finished)

        self.tts.synthesize_async(
            text=section.speech_text,
            on_success=_on_audio_ready
        )

    def _on_speech_finished(self) -> None:
        """Chamado quando a reprodução de áudio da seção termina."""
        if not self.is_active:
            return
        self.anim_engine.set_state("LISTENING")
        self.facial_ctrl.set_expression("HAPPY")

    def next_section(self) -> None:
        """Avança para a seção seguinte."""
        self.audio_player.stop()
        sec = self.lesson_manager.next_section()
        if sec:
            self._speak_section(sec)

    def prev_section(self) -> None:
        """Recua para a seção anterior."""
        self.audio_player.stop()
        sec = self.lesson_manager.prev_section()
        self._speak_section(sec)

    def repeat_section(self) -> None:
        """Repete a explicação atual."""
        self.audio_player.stop()
        sec = self.lesson_manager.restart_current_section()
        self._speak_section(sec)

    def toggle_pause(self) -> None:
        """Alterna entre pausar e retomar a fala e animação."""
        if self.audio_player.is_playing():
            self.audio_player.pause()
            self.lesson_manager.pause()
            self.anim_engine.set_state("LISTENING")
        else:
            self.audio_player.resume()
            self.lesson_manager.resume()
            self.anim_engine.set_state("TALKING")

    def toggle_mute(self) -> None:
        """Alterna o som entre silenciado e audível."""
        if self.is_muted:
            self.is_muted = False
            self.audio_player.set_volume(self._saved_volume)
        else:
            self._saved_volume = self.audio_player.volume
            self.is_muted = True
            self.audio_player.set_volume(0.0)

    def _on_section_changed(self, section: LessonSection) -> None:
        pass

    def _on_lesson_completed(self) -> None:
        self.anim_engine.set_state("LISTENING")
        self.facial_ctrl.set_expression("HAPPY")

    def update(self, delta_time: float) -> Tuple[SkeletalTransformState, FacialParameters]:
        """
        Atualiza o player de áudio, lip-sync, expressões faciais e animações corporais.
        Retorna os estados de transformação para o renderizador GPU.
        """
        self.audio_player.update()

        if delta_time > 0.0:
            playback_t = self.audio_player.get_playback_time()
            is_speaking = self.audio_player.is_playing()

            # Atualizar Lip Sync
            visemes = self.lip_sync.update(delta_time, playback_t, is_speaking)

            # Atualizar Animação Facial
            self.last_facial_params = self.facial_ctrl.update(delta_time, visemes)

            # Se parou de falar, volta para LISTENING (ou meditação)
            if not is_speaking and self.anim_engine.state == "TALKING":
                self.anim_engine.set_state("LISTENING")

            # Atualizar Animação Esquelética
            self.last_skeletal_state = self.anim_engine.update(delta_time)

        return self.last_skeletal_state, self.last_facial_params

    def get_current_state(self) -> Tuple[SkeletalTransformState, FacialParameters]:
        """Retorna o estado calculado mais recente sem avançar o tempo."""
        return self.last_skeletal_state, self.last_facial_params
