"""
===============================================================================
Ferramenta: tools/gerar_sons.py
Descrição: Sintetiza os efeitos sonoros e o som ambiente com NumPy (síntese
           aditiva + ruído filtrado). Nenhum som foi descarregado: não há
           questões de licença.

Gera em sounds/sfx/:
  whoosh.wav   — personagem a aparecer (ruído com filtro passa-banda a varrer)
  pop.wav      — balão de fala a abrir
  correct.wav  — resposta certa no quiz (dois tons a subir)
  wrong.wav    — resposta errada (zumbido grave)
  ambient.wav  — fundo espacial em ciclo contínuo (drone grave que "respira")

O ambiente dura 24 s e todas as frequências e modulações completam um número
inteiro de ciclos nesse tempo, por isso o ciclo repete sem estalido.

Uso:  .venv\\Scripts\\python.exe tools\\gerar_sons.py
===============================================================================
"""

import sys
import wave
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "sounds" / "sfx"
SR = 22050
rng = np.random.default_rng(7)


def save(name: str, signal: np.ndarray, peak: float = 0.8) -> None:
    signal = signal / (np.max(np.abs(signal)) + 1e-9) * peak
    data = (np.clip(signal, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT_DIR / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"  {name}: {len(signal) / SR:.2f} s")


def t_axis(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SR)) / SR


def bandpass_sweep(noise: np.ndarray, f_start: float, f_end: float, width: float = 0.35,
                   frames: int = 48) -> np.ndarray:
    """Filtra o ruído por blocos (FFT), com a frequência central a variar no tempo."""
    out = np.zeros_like(noise)
    block = len(noise) // frames
    window = np.hanning(block * 2)
    for i in range(frames):
        start = max(0, i * block - block // 2)
        seg = noise[start:start + block * 2]
        if len(seg) < block * 2:
            break
        fc = f_start * (f_end / f_start) ** (i / frames)
        spec = np.fft.rfft(seg * window)
        freqs = np.fft.rfftfreq(len(seg), 1 / SR)
        spec *= np.exp(-((np.log(freqs + 1) - np.log(fc)) ** 2) / (2 * width ** 2))
        out[start:start + block * 2] += np.fft.irfft(spec, len(seg))
    return out


def whoosh() -> np.ndarray:
    t = t_axis(0.9)
    s = bandpass_sweep(rng.standard_normal(len(t)), 300, 3200)
    env = np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 1.5
    return s * env


def pop() -> np.ndarray:
    t = t_axis(0.12)
    f = 900 * np.exp(-t * 18) + 300
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * np.exp(-t * 35)


def chime(freqs, dur=0.9) -> np.ndarray:
    t = t_axis(dur)
    out = np.zeros_like(t)
    for k, f in enumerate(freqs):
        start = int(k * 0.12 * SR)
        tt = t[: len(t) - start]
        tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 5)
        out[start:] += tone
    return out


def wrong() -> np.ndarray:
    t = t_axis(0.45)
    tone = np.sign(np.sin(2 * np.pi * 140 * t)) * 0.5 + np.sin(2 * np.pi * 70 * t)
    env = np.clip(t / 0.02, 0, 1) * np.exp(-t * 4)
    return tone * env


def ambient(seconds: int = 24) -> np.ndarray:
    t = t_axis(seconds)
    base = 1.0 / seconds  # frequência que completa 1 ciclo em `seconds`
    out = np.zeros_like(t)
    # Drone: harmónicos graves, cada um com uma "respiração" lenta própria
    for f, amp, lfo_cycles in ((55.0, 1.0, 1), (82.5, 0.6, 2), (110.0, 0.45, 3), (164.875, 0.25, 4)):
        f = round(f / base) * base                     # inteiro de ciclos -> ciclo sem estalido
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * lfo_cycles * base * t)
        out += amp * lfo * np.sin(2 * np.pi * f * t)
    # Ruído "cósmico" suave, filtrado e periódico (FFT de um sinal periódico)
    noise = rng.standard_normal(len(t))
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(len(t), 1 / SR)
    spec *= np.exp(-((freqs - 400) / 250) ** 2)
    out += 0.35 * np.fft.irfft(spec, len(t)) / (np.std(np.fft.irfft(spec, len(t))) + 1e-9) * 0.3
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"A gerar efeitos em {OUT_DIR}:")
    save("whoosh.wav", whoosh(), 0.7)
    save("pop.wav", pop(), 0.5)
    save("correct.wav", chime([659.25, 880.0]), 0.6)
    save("wrong.wav", wrong(), 0.5)
    save("ambient.wav", ambient(), 0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
