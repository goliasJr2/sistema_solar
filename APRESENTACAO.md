# Apresentação dos Planetas: falas, som, visita guiada e quiz

Continuação dos [personagens apresentadores](CHARACTERS.md). Os personagens deixam de
ser só decoração. Agora **falam** (voz + balão de fala), **apontam** para o planeta
enquanto contam factos, e há uma **visita guiada** por todos os planetas que termina
com um **quiz**.

---

## Como usar

| Tecla / ação | O que faz |
|---|---|
| **1–8**, **TAB** ou **clique** num planeta | O apresentador acena, diz quem é e conta um facto, a apontar para o planeta |
| **F** ou **clique no personagem** | Conta o facto seguinte (cada planeta tem 3 factos, em ciclo) |
| **J** | Começa a **visita guiada**; **J** de novo termina-a |
| **1 / 2 / 3** (durante o quiz) | Responde à pergunta (fora do quiz continuam a selecionar planetas) |
| **K** | Liga / silencia todo o som |
| **0** | Vista geral; o apresentador cala-se |

Ao arrancar, a narradora dá as boas-vindas e explica as teclas 1–8 e J.

### Visita guiada (J)
1. A narradora apresenta a visita.
2. Para cada planeta, de Mercúrio a Neptuno: a câmara vai até ao planeta, o apresentador
   cumprimenta (aceno), conta 2 factos (a apontar) e passa a palavra ao planeta seguinte
   ("Agora vamos até Vénus!"). Em Neptuno, que não tem personagem, fala a narradora.
3. **Quiz:** 3 perguntas sorteadas sobre os planetas, com as opções baralhadas.
   Responde-se com 1, 2 ou 3; a resposta certa fica a verde e a errada a vermelho.
4. No fim aparece a pontuação ("Acertaste 2 de 3!").

Escolher outro planeta à mão (teclas, TAB, clique) também termina a visita.
A visita completa dura cerca de 3 a 4 minutos.

---

## O que se vê no ecrã

- **Balão de fala** junto à cabeça do personagem, com o nome dele, e o texto a aparecer
  palavra a palavra ao ritmo da voz. A "cauda" do balão segue o personagem.
- **Balão da narradora** em baixo, ao centro, com outra cor (azul escuro).
- **Faixa da visita/quiz** em baixo: "VISITA GUIADA · Marte (4/8) · [J] sair".
- **Painel do quiz** com a pergunta e as 3 opções.
- **Gestos:** aceno ao cumprimentar; braço estendido para o planeta (e cabeça/tronco
  virados para ele) ao contar um facto; acenos de cabeça e a mão esquerda a gesticular
  enquanto fala. As transições entre gestos são suaves.

---

## Som

| Som | Origem | Ficheiros |
|---|---|---|
| **Vozes** (53 falas, ~5 min) | Síntese de voz do Windows, gerada uma vez por `tools/gerar_vozes.py` | `sounds/voices/*.wav` |
| **Efeitos** (personagem a aparecer, balão, certo/errado) | Sintetizados por código (NumPy) em `tools/gerar_sons.py` | `sounds/sfx/*.wav` |
| **Ambiente** (fundo espacial em ciclo de 24 s) | Sintetizado por código (NumPy) | `sounds/sfx/ambient.wav` |

**Nenhum som foi descarregado da internet**, por isso não há questões de licença.

### Vozes
- **Narradora:** "Microsoft Helia", português de Portugal.
- **Personagens:** "Microsoft Daniel", português do Brasil. É a única voz masculina em
  português que vem com o Windows. Cada personagem tem um tom e uma velocidade
  diferentes: o Warrok e o Maw mais graves e lentos, o Goblin mais agudo e rápido.
  Isto configura-se no campo `"voice"` de cada planeta em `characters.json`.
- As vozes são geradas **antes**, não durante a execução. O simulador só toca ficheiros
  `.wav`, por isso funciona igual em qualquer computador, incluindo fora do Windows.

### Gravar as vossas próprias vozes (recomendado)
As vozes sintetizadas servem para já, mas gravadas pelo grupo ficam muito melhores e dão
identidade ao trabalho.

1. Ver a lista de falas, com a chave e o texto de cada uma:
   ```bash
   .venv\Scripts\python.exe tools\gerar_vozes.py --listar
   ```
2. Gravar cada fala (telemóvel, Audacity, etc.) e guardar em
   `sounds/voices/gravadas/<chave>.wav` (ou `.ogg` / `.mp3`), por exemplo
   `sounds/voices/gravadas/earth_intro.ogg`.
3. Pronto: as gravações têm prioridade sobre as vozes geradas. Podem gravar só
   algumas; as restantes continuam com a voz sintetizada.

### Mudar textos
1. Editar os textos em `characters.json` (`intro`, `facts`, `handoff`, `quiz`, e as
   falas da narradora em `narrator.lines`).
2. Gerar as vozes de novo: `.venv\Scripts\python.exe tools\gerar_vozes.py`
   (Windows; demora cerca de 1 minuto).

Se um texto mudar e as vozes não forem geradas outra vez, o simulador deteta-o (pelo
`sounds/voices/manifest.json`) e mostra só o texto dessa fala, sem a voz antiga errada.

### Sem som
Se não houver placa de som, ou se o `pygame-ce` não estiver instalado, aparece um aviso
no terminal e tudo funciona na mesma, só com texto: a duração de cada fala passa a ser
estimada pelo tamanho do texto.

---

## O que mudou no código

| Ficheiro | Tipo | O que faz |
|---|---|---|
| `presentation.py` | **novo** | "Realizador": fila de falas, ritmo do texto, gestos pedidos a cada momento, visita guiada e quiz |
| `audio.py` | **novo** | Som com `pygame.mixer`: canais de voz, efeitos e ambiente; tecla K; gravações do grupo > vozes geradas |
| `tools/gerar_vozes.py` + `tools/tts_winrt.ps1` | **novo** | Geram as vozes a partir de `characters.json` (API WinRT do Windows) |
| `tools/gerar_sons.py` | **novo** | Sintetiza os efeitos e o ambiente |
| `sounds/` | **novo** | Vozes (~9 MB) e efeitos (~1 MB) gerados |
| `characters.json` | alterado | Para cada planeta: `intro`, 3 `facts`, `handoff`, `quiz` e `voice`; secções `narrator` e `tour` |
| `character_rig.py` | alterado | Novos gestos: **apontar** (braço na direção do planeta, cabeça e tronco viram-se) e **falar** (cabeça e mão esquerda) |
| `characters.py` | alterado | Os gestos vêm do `presentation.py` (com transições suaves); calcula a direção do planeta no espaço do personagem, a posição da cabeça (para o balão) e uma esfera para o clique |
| `ui.py` | alterado | Balão de fala, faixa da visita, painel do quiz; **camadas em cache** (ver abaixo) |
| `main.py` | alterado | Teclas J, F, K e 1–3 no quiz; clique no personagem; projeção da cabeça do personagem para o ecrã; ligação de tudo |
| `requirements.txt` | alterado | `pygame` → `pygame-ce` (o som passa a ser usado; o `pygame-ce` tem versões para Python 3.10–3.14) |

### Melhoria de desempenho na interface
Ao medir o simulador, a interface 2D era o principal gargalo. Desenhar texto com o Pillow
custa **~5 ms por linha** (medido; igual nas versões 11, 12 e 13 do Pillow), e o painel de
informação sozinho tinha ~40 linhas por frame. Com o balão e o quiz, o simulador chegava
a **~6 FPS**.

Agora as partes que mudam pouco (barra superior exceto o relógio, painel de informação,
faixa/quiz e o corpo do balão) são desenhadas **uma vez** numa camada em cache e só
coladas nos frames seguintes; só são redesenhadas quando o conteúdo muda. O aspeto no
ecrã é o mesmo. Resultado medido com a Terra selecionada: **6,3 → 22,6 FPS**, acima até
dos ~12 FPS de antes destas alterações.

> Nota: o FPS mostrado na barra superior não é o real quando o simulador está lento,
> porque o `main.py` limita o `delta_time` a 0,016 s quando um frame demora mais de
> 0,15 s, e o contador usa esse valor. Os valores acima foram medidos com o relógio real.
> Pela mesma razão, as falas usam o relógio real (`time.perf_counter`), para o texto e os
> gestos acompanharem sempre a voz.

---

## Testes feitos

- Visita guiada completa simulada sem gráficos nem som: 8 planetas visitados por ordem,
  40 falas, 3 perguntas, fim correto (~3,5 min).
- Simulador aberto com capturas: boas-vindas; saudação com aceno; facto a apontar para a
  Terra; Marte; visita guiada; pergunta do quiz; resposta certa a verde; ecrã final.
- Áudio: confirmado que cada fala está realmente a tocar no canal de voz durante os testes.
- Pré-visualização das poses (repouso, falar, apontar, apontar + falar) no Remy e no Warrok.
- `test_sim.py` continua a passar.
