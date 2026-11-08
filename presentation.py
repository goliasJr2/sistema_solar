"""
===============================================================================
Módulo: presentation.py
Descrição: "Realizador" da apresentação dos planetas — decide quem fala, o quê
           e com que gesto; conduz a visita guiada e o quiz.

Modo livre (sempre ativo):
  - Ao selecionar um planeta, o apresentador cumprimenta (aceno) e conta um
    facto (a apontar para o planeta).
  - [F] ou clique no personagem: conta o facto seguinte (circula pelos factos).

Visita guiada [J]:
  - A narradora abre; cada planeta é visitado por ordem, o apresentador
    cumprimenta, conta factos e "passa a palavra" ao planeta seguinte.
  - No fim há um quiz com perguntas sobre os planetas (teclas 1, 2, 3).
  - [J] de novo, ou escolher outro planeta à mão, termina a visita.

Cada fala (Line) tem: chave do áudio, texto, quem fala e o gesto. O texto
aparece letra a letra (máquina de escrever) ao ritmo da voz; sem áudio, a
duração é estimada pelo tamanho do texto.
===============================================================================
"""

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

NARRATOR = "narrator"
CHARS_PER_SECOND = 14.0      # ritmo de leitura quando não há voz
GAP_BETWEEN_LINES = 0.45     # pausa entre falas (s)
BUBBLE_LINGER = 3.5          # quanto tempo o balão fica depois da última fala (s)


@dataclass
class Line:
    key: str            # chave do ficheiro de voz (ver tools/gerar_vozes.py)
    text: str
    speaker: str        # id do planeta ou NARRATOR
    gesture: str = "talk"   # "wave" | "point" | "talk"


class Presentation:
    def __init__(self, config_path: Path, audio, select_body: Callable[[str], None],
                 planet_names: Optional[Dict[str, str]] = None):
        cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
        self.planet_names = planet_names or {}
        self.planets: Dict[str, dict] = cfg.get("planets", {})
        self.narrator: dict = cfg.get("narrator", {"name": "Narradora", "lines": {}})
        self.tour_cfg: dict = cfg.get("tour", {})
        self.audio = audio
        self.select_body = select_body

        self.queue: List[Line] = []
        self.current: Optional[Line] = None
        self.elapsed = 0.0
        self.duration = 0.0
        self.gap = 0.0
        self.last_line: Optional[Line] = None
        self.since_end = 99.0
        self.fact_index: Dict[str, int] = {}

        self.tour_active = False
        self.tour_steps: List[Tuple[str, object]] = []
        self.tour_planet: Optional[str] = None
        self.quiz: Optional[dict] = None   # estado do quiz (ver _quiz_*)
        self.quiz_result_timer = 0.0
        self._clock: Optional[float] = None

    # ================================================================ textos
    def speaker_name(self, speaker: str) -> str:
        if speaker == NARRATOR:
            return self.narrator.get("name", "Narradora")
        p = self.planets.get(speaker, {})
        return p.get("character") if p.get("model") and p.get("character") else self.narrator.get("name", "Narradora")

    def _planet_line(self, pid: str, kind: str, gesture: str, index: int = 0) -> Optional[Line]:
        p = self.planets.get(pid, {})
        if kind == "intro" and p.get("intro"):
            return Line(f"{pid}_intro", p["intro"], pid, gesture)
        if kind == "fact" and p.get("facts"):
            i = index % len(p["facts"])
            return Line(f"{pid}_fact{i + 1}", p["facts"][i], pid, gesture)
        if kind == "handoff" and p.get("handoff"):
            return Line(f"{pid}_handoff", p["handoff"], pid, gesture)
        return None

    def _narrator_line(self, key: str) -> Optional[Line]:
        text = self.narrator.get("lines", {}).get(key)
        return Line(f"narrator_{key}", text, NARRATOR, "talk") if text else None

    def _next_fact_line(self, pid: str) -> Optional[Line]:
        i = self.fact_index.get(pid, 0)
        line = self._planet_line(pid, "fact", "point", i)
        if line:
            self.fact_index[pid] = i + 1
        return line

    # ============================================================ modo livre
    def welcome(self) -> None:
        """Boas-vindas da narradora ao arrancar o simulador."""
        self._enqueue(self._narrator_line("welcome"))

    def on_user_select(self, pid: Optional[str]) -> None:
        """Seleção feita pelo utilizador (teclas, TAB, clique)."""
        if self.tour_active:
            self.stop_tour(announce=False)
        self._interrupt()
        if pid and pid in self.planets:
            self._on_planet_shown(pid)
            self._enqueue(self._planet_line(pid, "intro", "wave"), self._next_fact_line(pid))

    def next_fact(self, pid: Optional[str]) -> None:
        """[F] / clique no personagem: conta o facto seguinte do planeta atual."""
        if self.quiz is not None or not pid or pid not in self.planets:
            return
        self._interrupt()
        self._enqueue(self._next_fact_line(pid))

    def _on_planet_shown(self, pid: str) -> None:
        if self.planets.get(pid, {}).get("model"):
            self.audio.play_sfx("whoosh")

    # ======================================================= visita guiada
    def toggle_tour(self) -> None:
        if self.tour_active:
            self.stop_tour()
        else:
            self.start_tour()

    def start_tour(self) -> None:
        order = [p for p in self.tour_cfg.get("order", list(self.planets)) if p in self.planets]
        n_facts = int(self.tour_cfg.get("facts_per_planet", 2))
        steps: List[Tuple[str, object]] = [("say", self._narrator_line("tour_intro"))]
        for k, pid in enumerate(order):
            steps.append(("select", pid))
            steps.append(("wait", 1.0))
            steps.append(("say", self._planet_line(pid, "intro", "wave")))
            for _ in range(n_facts):
                steps.append(("say", self._next_fact_line(pid)))
            if k < len(order) - 1:
                steps.append(("say", self._planet_line(pid, "handoff", "talk")))
        steps.append(("quiz", None))
        steps.append(("say", self._narrator_line("end")))
        steps.append(("end", None))
        self._interrupt()
        self.tour_steps = [s for s in steps if s[0] != "say" or s[1] is not None]
        self.tour_order = order
        self.tour_active = True
        self.tour_planet = None
        print("[Visita Guiada] Início — [J] para sair.")

    def stop_tour(self, announce: bool = True) -> None:
        self.tour_active = False
        self.tour_steps = []
        self.quiz = None
        self._interrupt()
        if announce:
            print("[Visita Guiada] Terminada.")

    def _advance_tour(self) -> None:
        while self.tour_steps:
            kind, arg = self.tour_steps.pop(0)
            if kind == "say":
                self._enqueue(arg)
                return
            if kind == "select":
                self.tour_planet = arg
                self.select_body(arg)
                self._on_planet_shown(arg)
                continue
            if kind == "wait":
                self.gap = float(arg)
                return
            if kind == "quiz":
                self._quiz_start()
                return
            if kind == "end":
                self.tour_active = False
                self.quiz_result_timer = 6.0 if self.quiz else 0.0
                print("[Visita Guiada] Concluída.")
                return

    # ================================================================= quiz
    def _quiz_start(self) -> None:
        pool = [pid for pid in getattr(self, "tour_order", self.planets) if self.planets[pid].get("quiz")]
        n = min(int(self.tour_cfg.get("quiz_questions", 3)), len(pool))
        questions = []
        for pid in random.sample(pool, n):
            q = self.planets[pid]["quiz"]
            opts = list(enumerate(q["options"]))
            random.shuffle(opts)
            questions.append({
                "pid": pid,
                "question": q["question"],
                "options": [o for _, o in opts],
                "answer": [i for i, _ in opts].index(int(q.get("answer", 0))),
            })
        self.quiz = {"questions": questions, "index": -1, "score": 0, "state": "intro", "chosen": None}
        self._enqueue(self._narrator_line("quiz_intro"))

    def _quiz_next_question(self) -> None:
        q = self.quiz
        q["index"] += 1
        q["chosen"] = None
        if q["index"] >= len(q["questions"]):
            q["state"] = "done"
            self._advance_tour()
            return
        cur = q["questions"][q["index"]]
        q["state"] = "asking"
        self.audio.play_sfx("pop")
        self._enqueue(Line(f"{cur['pid']}_quiz", cur["question"], NARRATOR, "talk"))

    @property
    def quiz_waiting(self) -> bool:
        return self.quiz is not None and self.quiz["state"] in ("asking", "waiting")

    def answer(self, option: int) -> None:
        """Teclas 1/2/3 durante o quiz (option = 0, 1 ou 2)."""
        if not self.quiz_waiting:
            return
        q = self.quiz
        cur = q["questions"][q["index"]]
        if not 0 <= option < len(cur["options"]):
            return
        q["chosen"] = option
        q["state"] = "feedback"
        self._interrupt()
        if option == cur["answer"]:
            q["score"] += 1
            self.audio.play_sfx("correct")
            self._enqueue(self._narrator_line("correct"))
        else:
            self.audio.play_sfx("wrong")
            self._enqueue(self._narrator_line("wrong"))

    def _quiz_on_idle(self) -> bool:
        """Chamado quando não há falas a decorrer; devolve True se o quiz tratou do momento."""
        q = self.quiz
        if q is None or q["state"] == "done":
            return False
        if q["state"] == "intro":
            self._quiz_next_question()
            return True
        if q["state"] == "asking":
            q["state"] = "waiting"       # pergunta lida: espera pela resposta
            return True
        if q["state"] == "waiting":
            return True
        if q["state"] == "feedback":
            q["state"] = "pause"
            self.gap = 1.2               # deixa ver a resposta certa a verde
            return True
        if q["state"] == "pause":
            self._quiz_next_question()
            return True
        return False

    # ======================================================== motor das falas
    def _enqueue(self, *lines: Optional[Line]) -> None:
        self.queue.extend(l for l in lines if l is not None)

    def _interrupt(self) -> None:
        self.queue.clear()
        if self.current is not None:
            self.last_line = self.current
            self.since_end = BUBBLE_LINGER   # esconde o balão antigo de imediato
        self.current = None
        self.gap = 0.0
        self.audio.stop_voice()

    def _start(self, line: Line) -> None:
        self.current = line
        self.elapsed = 0.0
        dur = self.audio.play_voice(line.key, line.text)
        self.duration = dur if dur else max(1.6, len(line.text) / CHARS_PER_SECOND)

    def update(self, delta_time: float) -> None:
        # As falas seguem o relógio real (como o áudio), e não o delta_time do ciclo
        # principal, que é limitado a 0,016 s quando um frame demora mais de 0,15 s.
        now = time.perf_counter()
        delta_time = 0.0 if self._clock is None else min(now - self._clock, 1.0)
        self._clock = now
        if self.quiz_result_timer > 0.0:
            self.quiz_result_timer -= delta_time
            if self.quiz_result_timer <= 0.0 and not self.tour_active:
                self.quiz = None
        if self.current is not None:
            self.elapsed += delta_time
            if self.elapsed >= self.duration + 0.1:
                self.last_line = self.current
                self.current = None
                self.since_end = 0.0
                self.gap = GAP_BETWEEN_LINES
            return
        self.since_end += delta_time
        if self.gap > 0.0:
            self.gap -= delta_time
            return
        if self.queue:
            self._start(self.queue.pop(0))
            return
        if self.tour_active:
            if self._quiz_on_idle():
                return
            self._advance_tour()

    # ======================================================== saída (render/UI)
    def gestures_for(self, pid: Optional[str]) -> Tuple[float, float, float]:
        """Pesos-alvo (aceno, apontar, falar) para o personagem do planeta `pid`."""
        line = self.current
        if line is None or line.speaker != pid:
            return 0.0, 0.0, 0.0
        progress = self.elapsed / max(self.duration, 1e-6)
        if line.gesture == "wave":
            return (1.0 if self.elapsed < 2.6 and progress < 0.9 else 0.0), 0.0, 1.0
        if line.gesture == "point":
            return 0.0, (1.0 if 0.08 < progress < 0.92 else 0.0), 1.0
        return 0.0, 0.0, 1.0

    def bubble(self) -> Optional[dict]:
        """Balão de fala atual: {speaker, name, text (completo), visible (nº de caracteres
        já "escritos")} ou None."""
        line = self.current
        if line is not None and self.quiz is not None and line.key.endswith("_quiz"):
            return None   # a pergunta já aparece no painel do quiz
        if line is not None:
            visible = int(len(line.text) * min(1.0, self.elapsed / max(self.duration * 0.85, 1e-6)))
            return {"speaker": line.speaker, "name": self.speaker_name(line.speaker),
                    "text": line.text, "visible": max(1, visible)}
        if self.last_line is not None and self.since_end < BUBBLE_LINGER and not self.quiz_waiting:
            l = self.last_line
            return {"speaker": l.speaker, "name": self.speaker_name(l.speaker), "text": l.text, "visible": len(l.text)}
        return None

    def status(self) -> Optional[dict]:
        """Faixa de estado (visita/quiz) e painel do quiz para a UI."""
        if self.quiz is not None and self.quiz["state"] != "intro" and self.quiz["index"] >= 0:
            q = self.quiz
            total = len(q["questions"])
            if q["state"] == "done" or q["index"] >= total:
                return {"banner": f"QUIZ TERMINADO · {q['score']}/{total} certas",
                        "quiz": {"final": True, "score": q["score"], "total": total}}
            cur = q["questions"][q["index"]]
            return {
                "banner": f"QUIZ · Pergunta {q['index'] + 1}/{total} · Pontos {q['score']} · [J] sair",
                "quiz": {"final": False, "question": cur["question"], "options": cur["options"],
                         "chosen": q["chosen"], "answer": cur["answer"] if q["chosen"] is not None else None,
                         "waiting": q["state"] in ("asking", "waiting")},
            }
        if self.tour_active:
            order = getattr(self, "tour_order", [])
            if self.tour_planet in order:
                name = self.planet_names.get(self.tour_planet, self.tour_planet)
                return {"banner": f"VISITA GUIADA · {name} ({order.index(self.tour_planet) + 1}/{len(order)}) · [J] sair"}
            return {"banner": "VISITA GUIADA · [J] sair"}
        return None
