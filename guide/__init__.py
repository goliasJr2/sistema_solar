"""
===============================================================================
Módulo: guide/__init__.py
Pacote do Astronomical Virtual Guide 3D.
===============================================================================
"""

from .virtual_guide import AstronomicalVirtualGuide
from .guide_controller import GuideController
from .guide_renderer import GuideRenderer
from .guide_animation import GuideAnimationEngine, SkeletalTransformState
from .facial_animation import FacialAnimationController, FacialParameters

__all__ = [
    "AstronomicalVirtualGuide",
    "GuideController",
    "GuideRenderer",
    "GuideAnimationEngine",
    "SkeletalTransformState",
    "FacialAnimationController",
    "FacialParameters",
]
