"""
===============================================================================
Módulo: educational/lesson_manager.py
Descrição: Gere o ciclo de vida e estado das lições astronómicas educativas.
Controla o avanço, recuo, repetição, progresso e notificações para o guia.
===============================================================================
"""

from typing import List, Optional, Callable
from .earth_content import EARTH_LESSON_SECTIONS, LessonSection
from .planet_content import PLANET_LESSONS


class LessonManager:
    """Gestor de aulas astronómicas interativas."""

    def __init__(self, target_planet: str = "Terra"):
        self.target_planet = target_planet
        self.sections: List[LessonSection] = PLANET_LESSONS.get(target_planet.lower(), EARTH_LESSON_SECTIONS)
        self.current_index: int = 0
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.is_finished: bool = False
        
        # Callbacks para notificar o sistema
        self.on_section_changed: Optional[Callable[[LessonSection], None]] = None
        self.on_lesson_completed: Optional[Callable[[], None]] = None

    @property
    def current_section(self) -> LessonSection:
        if 0 <= self.current_index < len(self.sections):
            return self.sections[self.current_index]
        return self.sections[0]

    @property
    def total_sections(self) -> int:
        return len(self.sections)

    @property
    def progress_ratio(self) -> float:
        if not self.sections:
            return 0.0
        return (self.current_index + 1) / float(len(self.sections))

    def start(self) -> LessonSection:
        """Inicia a lição a partir da primeira seção."""
        self.current_index = 0
        self.is_playing = True
        self.is_paused = False
        self.is_finished = False
        sec = self.current_section
        if self.on_section_changed:
            self.on_section_changed(sec)
        return sec

    def next_section(self) -> Optional[LessonSection]:
        """Avança para a próxima seção."""
        if self.current_index + 1 < len(self.sections):
            self.current_index += 1
            sec = self.current_section
            if self.on_section_changed:
                self.on_section_changed(sec)
            return sec
        else:
            self.is_finished = True
            self.is_playing = False
            if self.on_lesson_completed:
                self.on_lesson_completed()
            return None

    def prev_section(self) -> LessonSection:
        """Recua para a seção anterior."""
        if self.current_index > 0:
            self.current_index -= 1
        self.is_finished = False
        sec = self.current_section
        if self.on_section_changed:
            self.on_section_changed(sec)
        return sec

    def restart_current_section(self) -> LessonSection:
        """Reinicia a seção atual."""
        sec = self.current_section
        if self.on_section_changed:
            self.on_section_changed(sec)
        return sec

    def jump_to_section(self, index: int) -> Optional[LessonSection]:
        """Salta diretamente para uma seção específica."""
        if 0 <= index < len(self.sections):
            self.current_index = index
            self.is_finished = False
            sec = self.current_section
            if self.on_section_changed:
                self.on_section_changed(sec)
            return sec
        return None

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def reset(self) -> None:
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.is_finished = False

    def set_planet(self, planet_id: str) -> None:
        """Recarrega as secções de lição para o planeta indicado e reinicia o estado."""
        self.target_planet = planet_id
        self.sections = PLANET_LESSONS.get(planet_id.lower(), EARTH_LESSON_SECTIONS)
        self.reset()
