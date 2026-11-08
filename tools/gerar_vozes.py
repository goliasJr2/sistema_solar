"""
===============================================================================
Ferramenta: tools/gerar_vozes.py
Descrição: Gera as falas dos apresentadores e da narradora (.wav) a partir dos
           textos em characters.json, com as vozes do Windows (síntese de voz).

  - Narradora: "Microsoft Helia" (português de Portugal).
  - Personagens: "Microsoft Daniel" (português do Brasil — é a única voz
    masculina em português incluída no Windows), com tom (pitch) e
    velocidade (rate) diferentes para cada personagem (campo "voice").

Os ficheiros vão para sounds/voices/<chave>.wav e o sounds/voices/manifest.json
guarda o texto de cada fala: se um texto mudar no characters.json e as vozes
não forem geradas de novo, o simulador deteta-o e mostra só o texto.

Vozes gravadas pelo grupo: ponha-as em sounds/voices/gravadas/<chave>.wav
(ou .ogg / .mp3) — têm prioridade sobre as geradas e este script não lhes toca.
Para ver a lista de chaves e textos:  python tools/gerar_vozes.py --listar

Uso (Windows, a partir da pasta do projeto):
  .venv\\Scripts\\python.exe tools\\gerar_vozes.py
===============================================================================
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG = BASE_DIR / "characters.json"
OUT_DIR = BASE_DIR / "sounds" / "voices"
PS_SCRIPT = Path(__file__).resolve().parent / "tts_winrt.ps1"

LANG_BY_VOICE = {"Helia": "pt-PT", "Daniel": "pt-BR", "Maria": "pt-BR"}


def collect_lines(cfg: dict) -> List[Tuple[str, str, dict]]:
    """Lista de (chave, texto, voz) — a mesma convenção de chaves usada por presentation.py."""
    narrator = cfg["narrator"]
    lines: List[Tuple[str, str, dict]] = []
    for key, text in narrator["lines"].items():
        lines.append((f"narrator_{key}", text, narrator["voice"]))
    for pid, p in cfg["planets"].items():
        voice = p.get("voice") if p.get("model") else narrator["voice"]
        voice = voice or narrator["voice"]
        if p.get("intro"):
            lines.append((f"{pid}_intro", p["intro"], voice))
        for i, fact in enumerate(p.get("facts", []), start=1):
            lines.append((f"{pid}_fact{i}", fact, voice))
        if p.get("handoff"):
            lines.append((f"{pid}_handoff", p["handoff"], voice))
        if p.get("quiz"):
            lines.append((f"{pid}_quiz", p["quiz"]["question"], narrator["voice"]))
    return lines


def ssml(text: str, voice: dict) -> str:
    lang = LANG_BY_VOICE.get(voice.get("name", ""), "pt-PT")
    pitch = voice.get("pitch", "0%")
    rate = voice.get("rate", 1.0)
    return (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
            f'<prosody pitch="{pitch}" rate="{rate}">{escape(text)}</prosody></speak>')


def main(argv: List[str]) -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    lines = collect_lines(cfg)
    if "--listar" in argv:
        for key, text, voice in lines:
            print(f"{key:22s} [{voice.get('name')}] {text}")
        return 0
    if sys.platform != "win32":
        print("Este gerador usa as vozes do Windows; corra-o em Windows.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [{"out": str(OUT_DIR / f"{key}.wav"), "voice": voice.get("name", "Helia"), "ssml": ssml(text, voice)}
            for key, text, voice in lines]
    with tempfile.TemporaryDirectory() as tmp:
        jobs_file = Path(tmp) / "jobs.json"
        jobs_file.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        print(f"A gerar {len(jobs)} falas em {OUT_DIR} ...")
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS_SCRIPT), "-Jobs", str(jobs_file)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    out = proc.stdout.strip().splitlines()
    ok = sum(1 for l in out if l.startswith("OK"))
    for l in out:
        if not l.startswith("OK"):
            print("  " + l)
    if proc.returncode != 0:
        print(proc.stderr)

    manifest: Dict[str, str] = {key: text for key, text, _ in lines if (OUT_DIR / f"{key}.wav").exists()}
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{ok}/{len(jobs)} falas geradas; manifest.json atualizado.")
    return 0 if ok == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
