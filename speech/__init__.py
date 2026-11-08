"""
===============================================================================
Módulo: speech/__init__.py
Pacote de voz, síntese e sincronização labial (Lip Sync).
===============================================================================
"""

from .text_to_speech import TextToSpeechEngine
from .audio_player import AudioPlayer
from .lip_sync import LipSyncEngine, VisemeState

__all__ = ["TextToSpeechEngine", "AudioPlayer", "LipSyncEngine", "VisemeState"]
