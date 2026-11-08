# Apresentação dos Planetas: falas, som, visita guiada e quiz

Continuação dos [personagens apresentadores](CHARACTERS.md). Os personagens deixam de
ser só decoração. Agora **falam**: o apresentador aparece num **retrato** (cabeça e
ombros) no canto superior direito, com um balão de fala em letra grande ao lado. Cada
planeta tem **6 factos detalhados**, e há uma **visita guiada** por todos os planetas
que termina com um **quiz**.

---

## Como usar

| Tecla / ação | O que faz |
|---|---|
| **1–8**, **TAB** ou **clique** num planeta | O retrato do apresentador entra no canto superior direito; ele acena, diz quem é e conta um facto |
| **F** ou **clique no retrato** | Conta o facto seguinte (cada planeta tem 6 factos, em ciclo) |
| **J** | Começa a **visita guiada**; **J** de novo termina-a |
| **1 / 2 / 3** (durante o quiz) | Responde à pergunta (fora do quiz continuam a selecionar planetas) |
| **K** | Liga / silencia todo o som |
| **0** | Vista geral; o apresentador cala-se |

Ao arrancar, a narradora dá as boas-vindas e explica as teclas 1–8 e J.

### Visita guiada (J)
1. A narradora apresenta a visita.
2. Para cada planeta, de Mercúrio a Neptuno: a câmara vai até ao planeta, o apresentador
   cumprimenta (aceno), conta 3 factos e passa a palavra ao planeta seguinte
   ("Agora vamos até Vénus!"). Em Neptuno, que não tem personagem, fala a narradora.
3. **Quiz:** 3 perguntas sorteadas sobre os planetas, com as opções baralhadas.
   Responde-se com 1, 2 ou 3; a resposta certa fica a verde e a errada a vermelho.
4. No fim aparece a pontuação ("Acertaste 2 de 3!").

Escolher outro planeta à mão (teclas, TAB, clique) também termina a visita.
A visita completa dura cerca de 5 a 6 minutos. Os restantes factos de cada planeta
ouvem-se em modo livre, com **F**.

---

## O que se vê no ecrã

- **Retrato do apresentador** no canto superior direito: cabeça e ombros do personagem
  3D, numa moldura dourada com o nome. Entra a deslizar quando ele começa a falar e sai
  quando se cala. O planeta continua visível no centro, sem o corpo inteiro do personagem.
- **Balão de fala** ao lado do retrato, com letra grande (20 px), o nome do personagem, e o
  texto a aparecer palavra a palavra ao ritmo da voz. A "cauda" aponta para o retrato.
- **Boca e cabeça ao ritmo da voz:** a intensidade do áudio de cada fala comanda os
  movimentos da cabeça. O **Warrok** é o único com osso de maxilar no esqueleto, e abre e
  fecha a boca a falar.
- **Gestos:** aceno ao cumprimentar (a mão aparece no retrato); ao contar um facto, olha
  na direção do planeta, em três quartos, sem virar a cara a quem vê; acenos de cabeça
  enquanto fala. As transições entre gestos são suaves.
- **Balão da narradora** em baixo, ao centro, com outra cor (azul escuro). Em Neptuno, que
  não tem personagem, o balão aparece por cima do planeta.
- **Faixa da visita/quiz** em baixo: "VISITA GUIADA · Marte (4/8) · [J] sair".
- **Painel do quiz** com a pergunta e as 3 opções.
- Com o **Guia Virtual** aberto ("Saber Mais"), o retrato e as falas ficam em silêncio,
  para não falarem por cima dele.

---

## Som

| Som | Origem | Ficheiros |
|---|---|---|
| **Vozes** (77 falas, ~21 MB) | Síntese de voz do Windows, gerada uma vez por `tools/gerar_vozes.py` | `sounds/voices/*.wav` |
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
| `characters.json` | alterado | Para cada planeta: `intro`, 6 `facts` detalhados, `handoff`, `quiz` e `voice`; secções `narrator` e `tour` |
| `character_rig.py` | alterado | Novos gestos: **apontar** (cabeça e tronco viram-se para o planeta), **falar** (cabeça e mão esquerda) e **boca** (maxilar "Jaw", quando existe, ao ritmo da voz) |
| `characters.py` | alterado | Desenha o **retrato** num viewport próprio (`glViewport` + `glScissor`) com câmara e luz só suas, enquadrando a cabeça a partir dos ossos "Head" e "HeadTop_End"; o retrato entra/sai a deslizar; clique no retrato = facto seguinte |
| `audio.py` | alterado | `voice_envelope()`: curva de intensidade de cada fala (30 valores/s), usada para mexer a boca e a cabeça |
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
dos ~12 FPS de antes destas alterações. Com o retrato (sem o corpo inteiro na cena), o
FPS real medido com o apresentador a falar é **~34**.

> Nota: o FPS mostrado na barra superior não é o real quando o simulador está lento,
> porque o `main.py` limita o `delta_time` a 0,016 s quando um frame demora mais de
> 0,15 s, e o contador usa esse valor. Os valores acima foram medidos com o relógio real.
> Pela mesma razão, as falas usam o relógio real (`time.perf_counter`), para o texto e os
> gestos acompanharem sempre a voz.

---

## Testes feitos

- Visita guiada completa simulada sem gráficos nem som: 8 planetas visitados por ordem,
  48 falas, 3 perguntas, fim correto (~5,5 min).
- Retrato: capturas do Remy, do Maw e do Warrok a falar (saudação e a meio de um facto);
  a boca do Warrok acompanha a voz.
- Simulador aberto com capturas: boas-vindas; saudação com aceno; facto a apontar para a
  Terra; Marte; visita guiada; pergunta do quiz; resposta certa a verde; ecrã final.
- Áudio: confirmado que cada fala está realmente a tocar no canal de voz durante os testes.
- Pré-visualização das poses (repouso, falar, apontar, apontar + falar) no Remy e no Warrok.
- `test_sim.py` continua a passar.
