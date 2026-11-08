"""
===============================================================================
Módulo: educational/__init__.py
Pacote educativo para o Astronomical Virtual Guide.
===============================================================================
"""

from .earth_content import EARTH_LESSON_SECTIONS, LessonSection
from .lesson_manager import LessonManager

__all__ = ["EARTH_LESSON_SECTIONS", "LessonSection", "LessonManager"]
