"""
===============================================================================
Script de Validação e Testes: test_virtual_guide.py
Testa minuciosamente todos os componentes do Astronomical Virtual Guide:
1. Conteúdo Educativo da Terra (10 seções completas)
2. Gestor de Lições (LessonManager)
3. Motor Lip Sync e Fonemas em Português
4. Síntese TTS (Text-to-Speech com edge-tts)
5. Reprodutor de Áudio (pygame.mixer)
6. Animação Facial e Piscar de Olhos
7. Animação Esquelética e Corporal (IDLE, TALKING, THINKING, LISTENING)
8. Interface do Guia e Gestão de Eventos
===============================================================================
"""

import sys
import time
from pathlib import Path

def test_educational_content():
    print("\n[TESTE 1] Conteúdo Educativo da Terra...")
    from educational.earth_content import EARTH_LESSON_SECTIONS
    assert len(EARTH_LESSON_SECTIONS) == 10, f"Esperadas 10 seções, obtidas {len(EARTH_LESSON_SECTIONS)}"
    for sec in EARTH_LESSON_SECTIONS:
        assert sec.title, "Seção sem título"
        assert len(sec.speech_text) > 50, f"Texto muito curto na seção {sec.id}"
        assert sec.estimated_duration_sec > 10.0, f"Duração irrealista na seção {sec.id}"
        print(f"  ✓ Seção {sec.id}: {sec.title} ({sec.estimated_duration_sec}s, {len(sec.speech_text)} chars)")
    print("  -> TESTE 1 PASSOU COM SUCESSO!")

def test_lesson_manager():
    print("\n[TESTE 2] Gestor de Lições (LessonManager)...")
    from educational.lesson_manager import LessonManager
    lm = LessonManager("Terra")
    assert lm.total_sections == 10
    assert lm.current_index == 0
    sec1 = lm.start()
    assert sec1.id == 1
    assert lm.is_playing == True
    
    sec2 = lm.next_section()
    assert sec2.id == 2
    assert lm.current_index == 1
    
    sec_prev = lm.prev_section()
    assert sec_prev.id == 1
    
    rep = lm.restart_current_section()
    assert rep.id == 1
    print("  -> TESTE 2 PASSOU COM SUCESSO!")

def test_lip_sync():
    print("\n[TESTE 3] Motor de Lip Sync e Visemas...")
    from speech.lip_sync import LipSyncEngine
    ls = LipSyncEngine()
    test_text = "A Terra é um planeta rochoso no Sistema Solar com oceanos e vida."
    ls.prepare_speech(test_text, estimated_duration=5.0)
    assert len(ls.phoneme_timeline) > 10, "Timeline fonética vazia"
    print(f"  Fonemas mapeados: {len(ls.phoneme_timeline)}")
    
    # Simular frames de animação
    state1 = ls.update(delta_time=0.016, current_playback_time=0.5, is_speaking=True)
    assert 0.0 <= state1.mouth_open <= 1.0
    print(f"  Estado a falar (t=0.5s): mouth_open={state1.mouth_open:.2f}, jaw_drop={state1.jaw_drop:.2f}")
    
    # Simular silêncio após o fim
    state_silence = ls.update(delta_time=0.5, current_playback_time=6.0, is_speaking=False)
    assert state_silence.mouth_open < 0.1, "Boca não fechou no silêncio"
    print("  ✓ Boca regressou ao repouso no silêncio")
    print("  -> TESTE 3 PASSOU COM SUCESSO!")

def test_audio_and_tts():
    print("\n[TESTE 4] Text-to-Speech e Reprodutor de Áudio...")
    from speech.text_to_speech import TextToSpeechEngine
    from speech.audio_player import AudioPlayer
    
    tts = TextToSpeechEngine()
    player = AudioPlayer(initial_volume=0.8)
    
    short_text = "Observatório astronómico ativado."
    audio_ready = [False]
    audio_file = [""]
    
    def on_ready(path):
        audio_ready[0] = True
        audio_file[0] = path
        print(f"  Áudio gerado com sucesso: {path}")
        
    tts.synthesize_async(short_text, on_success=on_ready)
    
    # Aguardar até 8 segundos pela síntese
    for _ in range(80):
        if audio_ready[0]:
            break
        time.sleep(0.1)
        
    assert audio_ready[0], "Timeout ao gerar áudio TTS"
    assert Path(audio_file[0]).exists(), "Ficheiro de áudio não foi criado"
    
    # Testar reprodução com AudioPlayer
    played = player.play(audio_file[0])
    assert played, "Falha ao reproduzir áudio com AudioPlayer"
    assert player.is_playing() == True
    time.sleep(0.3)
    t = player.get_playback_time()
    assert t > 0.0, f"Tempo decorrido inválido: {t}"
    print(f"  Tempo decorrido no player: {t:.2f}s")
    
    player.pause()
    assert player.is_playing() == False
    player.resume()
    time.sleep(0.2)
    player.stop()
    assert player.is_playing() == False
    print("  -> TESTE 4 PASSOU COM SUCESSO!")

def test_facial_animation():
    print("\n[TESTE 5] Animação Facial e Piscar de Olhos...")
    from guide.facial_animation import FacialAnimationController
    from speech.lip_sync import VisemeState
    
    fac = FacialAnimationController()
    viseme = VisemeState(mouth_open=0.7, jaw_drop=0.6, mouth_round=0.2)
    
    # Forçar piscar
    fac._blink_timer = 0.01
    fac.update(0.02, viseme)
    assert fac._is_blinking == True
    
    # Avançar no meio do piscar
    params = fac.update(0.07, viseme)
    assert params.blink_factor > 0.1, "Blink factor nulo durante o piscar"
    assert params.mouth_open == 0.7
    print(f"  ✓ Piscar ativo: blink_factor={params.blink_factor:.2f}")
    
    # Terminar o piscar
    fac.update(0.2, viseme)
    assert fac._is_blinking == False
    assert fac.params.blink_factor == 0.0
    print("  ✓ Olhos reabertos após piscar")
    print("  -> TESTE 5 PASSOU COM SUCESSO!")

def test_skeletal_animation():
    print("\n[TESTE 6] Animação Esquelética e Corporal...")
    from guide.guide_animation import GuideAnimationEngine
    
    anim = GuideAnimationEngine()
    for state in ["IDLE", "TALKING", "THINKING", "LISTENING"]:
        anim.set_state(state)
        pose = anim.update(delta_time=0.033)
        assert pose.head_rotation is not None
        assert pose.right_arm_rotation is not None
        assert pose.left_arm_rotation is not None
        assert pose.breathing_scale >= 0.0
        print(f"  ✓ Estado '{state}': respiração={pose.breathing_scale:.2f}")
    print("  -> TESTE 6 PASSOU COM SUCESSO!")

def test_virtual_guide_pipeline():
    print("\n[TESTE 7] Fachada do Guia Virtual e Inicialização...")
    from guide.virtual_guide import AstronomicalVirtualGuide
    
    guide = AstronomicalVirtualGuide("Models/guide_remy.glb")
    assert guide.is_visible == False
    guide.open("Terra")
    assert guide.is_visible == True
    assert guide.controller.is_active == True
    
    # Atualizar frames
    for _ in range(5):
        guide.update(0.016)
        
    guide.close()
    assert guide.is_visible == False
    assert guide.controller.is_active == False
    print("  -> TESTE 7 PASSOU COM SUCESSO!")

def main():
    print("=" * 70)
    print("BATERIA DE TESTES DE INTEGRAÇÃO — ASTRONOMICAL VIRTUAL GUIDE")
    print("=" * 70)
    test_educational_content()
    test_lesson_manager()
    test_lip_sync()
    test_audio_and_tts()
    test_facial_animation()
    test_skeletal_animation()
    test_virtual_guide_pipeline()
    print("\n" + "=" * 70)
    print("TODOS OS TESTES FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
    print("=" * 70)

if __name__ == '__main__':
    main()
