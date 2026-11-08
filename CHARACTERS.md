# Personagens Apresentadores dos Planetas

Cada planeta passa a ter um **personagem 3D animado** que aparece ao lado dele quando é
selecionado. Ao aparecer, o personagem **acena** com o braço direito; depois fica em
**repouso**, com respiração, cabeça a olhar à volta e um leve balanço do corpo. O nome
e uma frase sobre o planeta aparecem no painel de informação (tecla **I**).

> As falas, a voz, os gestos de apontar e falar, a visita guiada e o quiz estão descritos
> em [APRESENTACAO.md](APRESENTACAO.md).

---

## Como usar

| Ação | Resultado |
|---|---|
| **1–8**, **TAB** / **SHIFT+TAB** ou **clique** num planeta | O personagem desse planeta aparece à direita do planeta, acena durante ~3 s e passa para a animação de repouso |
| **9** / **H** (Sol) ou **0** (vista geral) | Nenhum personagem é mostrado |
| **I** | Mostra / oculta o painel; a secção **Apresentador** mostra o nome e a frase do personagem |

Não há teclas novas: o personagem segue a seleção de planetas que já existia.

---

## Personagem de cada planeta

| Planeta | Personagem | Ficheiro usado pelo simulador | FBX de origem (já existia em `Models/`) |
|---|---|---|---|
| Mercúrio | Ely | `Models/characters/ely.npz` | `Models/character (2).fbx` |
| Vénus | Vanguard | `Models/characters/vanguard.npz` | `Models/character (1).fbx` |
| Terra | Remy | `Models/characters/remy.npz` | `Models/character.fbx` |
| Marte | Maw | `Models/characters/maw.npz` | `Models/character (3).fbx` |
| Júpiter | Warrok | `Models/characters/warrok.npz` | `Models/Warrok W Kurniawan.fbx` |
| Saturno | Mutant | `Models/characters/mutant.npz` | `Models/Mutant.fbx` |
| Úrano | Goblin | `Models/characters/goblin.npz` | `Models/goblin_d_shareyko.fbx` |
| Neptuno | — (vago) | — | Só existiam 7 personagens no projeto |

A escolha foi feita pelo "feitio" de cada um: o humano casual (Remy) na Terra, o
gigante (Warrok) em Júpiter, o soldado de armadura clara (Vanguard) no planeta mais
quente, etc. Tudo isto é configurável — ver [Trocar ou adicionar um personagem](#trocar-ou-adicionar-um-personagem).

---

## De onde vieram os modelos

- Os 7 ficheiros `.fbx` **já estavam no repositório**, na pasta `Models/`, desde o
  commit inicial (`79a82bf`). Não foi descarregado nenhum modelo novo.
- Todos vêm da **[Mixamo](https://www.mixamo.com)** (Adobe). Isso é confirmado pelo
  conteúdo dos próprios ficheiros: o esqueleto chama-se `mixamorig:*` e os caminhos
  internos das texturas apontam para `.../mixamo-mini/...`.
- Os nomes dos personagens são os nomes do catálogo Mixamo: *Ely By K.Atienza*,
  *Vanguard By T. Choonyung*, *Remy*, *Maw J Laygo*, *Warrok W Kurniawan*, *Mutant*,
  *Goblin D Shareyko*.
- **Licença:** os personagens Mixamo podem ser usados sem custos em projetos pessoais,
  académicos e comerciais, segundo os termos da Adobe (ver as FAQ da Mixamo); o que não é permitido é
  redistribuí-los como ficheiros soltos (por exemplo, num pacote de modelos).
  Aqui são usados dentro do simulador, que é o caso previsto.
- Os FBX **não traziam animações**. Todo o movimento é **procedural** (gerado no
  código), por isso não foi preciso descarregar animações.

---

## O que mudou no código

| Ficheiro | Tipo | O que faz |
|---|---|---|
| `tools/fbx_to_glb.py` | **novo** | Converte `.fbx` para `.npz` (animado) ou `.glb` (estático) — ver abaixo |
| `Models/characters/*.npz` | **novo** | Os 7 personagens convertidos, com esqueleto (0,5 a 2,2 MB cada; ~6 MB no total) |
| `character_rig.py` | **novo** | Animação procedural do esqueleto (NumPy puro, sem OpenGL) |
| `shaders/skinned.vert` | **novo** | Vertex shader de *skinning* (deforma a malha com as matrizes dos ossos) |
| `characters.json` | **novo** | Tabela planeta → personagem (modelo, frase, créditos, ajustes) |
| `characters.py` | **novo** | Carrega e desenha o personagem do planeta selecionado (`.npz` animado ou `.glb` estático) |
| `main.py` | alterado | Cria `PlanetCharacters`, desenha-o a seguir ao Sistema Solar (passo **7b** do ciclo) e envia os dados do personagem para a UI ao selecionar um planeta |
| `ui.py` | alterado | Novo método `set_presenter()` e secção **Apresentador** no painel de informação |
| `model_loader.py` | alterado | `GLBModel` guarda `normalized_extents` (dimensões do modelo normalizado), para escalar um personagem `.glb` pela sua altura |

### Porque é que foi preciso converter os FBX

O `model_loader.py` lê os modelos com a biblioteca **trimesh**, que **não lê `.fbx`**.
Além disso, 4 dos 7 personagens (`character*.fbx`) estão no formato antigo
**FBX 6.1 (2006)**, que nem a biblioteca Assimp suporta. Por isso foi escrito um
leitor próprio do FBX binário em `tools/fbx_to_glb.py`, sem dependências novas
(usa só `numpy`, `trimesh` e `Pillow`, que já estão no `requirements.txt`).

O conversor:
1. Lê a árvore de nós binária do FBX (versões 6.1 e 7.x);
2. Extrai vértices, polígonos (triangulados em leque), coordenadas UV e o material
   de cada polígono;
3. Extrai a **textura difusa** de cada material — as imagens PNG vêm embutidas
   dentro do `.fbx` (nós `Video`), por isso não há ficheiros de textura soltos;
4. Extrai o **esqueleto**: os ossos (`Model` do tipo `LimbNode`), a hierarquia, a
   matriz global de cada osso na pose de ligação (`Cluster.TransformLink`) e os
   **pesos de pele** — para cada vértice, os 4 ossos com mais influência;
5. Põe o personagem de pé (+Y), virado para +Z, com altura 2,0 e centrado
   (a mesma transformação é aplicada à malha e aos ossos);
6. Reduz as texturas a 1024 px no máximo (as originais têm até 4096 px) e grava o
   `.npz` (arrays NumPy comprimidos: malhas, ossos, pesos e texturas em JPEG/PNG).

> **Nota técnica:** nos FBX da Mixamo, o campo `Cluster.Transform` **não** é a matriz
> global da malha (como diz a documentação do FBX SDK), mas sim o inverso da matriz
> do osso (`Transform · TransformLink = identidade`). Por isso os vértices são usados
> no seu espaço próprio, que já coincide com o dos ossos.

### Como funciona a animação

A animação usa **skinning linear** (*Linear Blend Skinning*), a técnica padrão dos jogos:

1. **No CPU, a cada frame** (`character_rig.py`, ~0,5 ms): para cada osso calcula-se a
   pose atual por cinemática direta, `C_i = C_pai · L_i · Q_i`, onde `L_i` é a posição
   local do osso na pose de ligação e `Q_i` a rotação animada. A matriz enviada à GPU
   é `S_i = C_i · G_i⁻¹` (`G_i` = osso na pose de ligação), que é a identidade quando
   o personagem está na pose original.
2. **Na GPU** (`shaders/skinned.vert`): cada vértice mistura as matrizes dos seus 4
   ossos, pesadas pelos pesos de pele, antes das transformações Model/View/Projection
   habituais. A iluminação usa o `celestial.frag` existente.

As rotações são definidas no espaço do personagem (por exemplo "baixar o braço na
direção de −Y") e convertidas para o referencial de cada osso (`Q_i = R_iᵀ · R_mundo · R_i`).
Os ossos são encontrados pelo nome Mixamo (`LeftArm`, `Head`, …), por isso **qualquer
personagem com esqueleto Mixamo é animado automaticamente**.

| Animação | O que mexe |
|---|---|
| **Repouso** | Braços descem da pose em T até ~20° do corpo, cotovelos ligeiramente dobrados para a frente; respiração (tronco); cabeça e pescoço olham à volta; balanço lento da anca |
| **Aceno** | Ao aparecer: o braço direito sobe (~0,35 s), o antebraço acena (~2,4 s) e volta a baixar (~0,6 s), com transições suaves para o repouso |

### Como o personagem é posicionado (`characters.py`)

- **Carregamento preguiçoso:** cada modelo só é lido na primeira vez que o seu planeta
  é selecionado; depois fica em cache.
- **Posição:** `planeta + camera.right × (raio × side_offset)` — sempre à direita do
  planeta no ecrã, fora do painel de informação, que está à esquerda.
- **Tamanho:** `altura = raio visual do planeta × height_factor`.
- **Orientação:** rotação em Y para ficar de frente para a câmara e leve flutuação vertical.
- **Entrada:** escala de 0 → 1 em 0,6 s com *easing* ao mudar de planeta.
- **Iluminação:** luz junto à câmara ("luz de estúdio") e ambiente mais forte, para o
  personagem nunca ficar às escuras no lado noturno do planeta.
- O *face culling* é desligado só durante o desenho do personagem (cabelo e roupa têm
  faces visíveis dos dois lados).
- Se a placa gráfica não aceitar 128 matrizes de ossos no vertex shader (muito raro),
  aparece um aviso no terminal e os personagens `.npz` não são mostrados; o resto do
  simulador funciona normalmente.

---

## Trocar ou adicionar um personagem

Exemplo: pôr a Nami (One Piece) em Neptuno.

1. **Arranjar o modelo** (por exemplo no [Sketchfab](https://sketchfab.com), que exige
   conta para descarregar). **Verifique a licença**: personagens de anime são
   propriedade dos seus autores, e muitos modelos feitos por fãs só permitem uso não
   comercial. Registe o autor e a licença em `characters.json` (`source` / `license`).
2. **Para ficar animado**, o modelo precisa de um esqueleto Mixamo:
   - Envie o modelo (`.fbx` ou `.obj`) para [mixamo.com](https://www.mixamo.com) → o
     **auto-rigger** coloca o esqueleto automaticamente (marca-se queixo, pulsos,
     cotovelos, joelhos e virilha);
   - Descarregue em **FBX Binary**, **T-pose**, **sem animação** (*Download → Format: FBX Binary, Pose: T-pose*);
   - Converta:
     ```bash
     .venv\Scripts\python.exe tools\fbx_to_glb.py "Models\nami.fbx" "Models\characters\nami.npz" --preview
     ```
     O `--preview` grava `nami.preview.png` com três poses (ligação, repouso, aceno) para
     confirmar que ficou bem — apague a imagem depois; não deve ir para o repositório.
3. **Sem esqueleto** (estático): converta para `.glb` (`... "Models\characters\nami.glb"`)
   ou use diretamente um `.glb` que esteja de pé (+Y) e virado para +Z.
4. **Editar `characters.json`:**
   ```json
   "neptune": {
     "character": "Nami",
     "model": "Models/characters/nami.npz",
     "tagline": "Navegadora do planeta dos ventos mais fortes: 2100 km/h.",
     "source": "Sketchfab — <autor> — <link>; esqueleto: Mixamo auto-rigger",
     "license": "<licença do modelo>"
   }
   ```
5. Correr o simulador e carregar em **8**.

Ajustes opcionais por planeta em `characters.json`:

| Campo | Padrão | Efeito |
|---|---|---|
| `height_factor` | 1.4 | Altura do personagem em múltiplos do raio do planeta |
| `side_offset` | 2.1 | Distância ao centro do planeta, para a direita (Saturno usa 2.9 por causa dos anéis) |

Com `"model": null`, o planeta fica sem personagem.

Para mudar os movimentos (ângulos, velocidades, novas animações), edite
`ProceduralRig.pose_rotations()` em `character_rig.py` e confirme com `--preview`.

### Reconverter os 7 personagens Mixamo

```bash
.venv\Scripts\python.exe tools\fbx_to_glb.py
```
A lista de ficheiros a converter está no dicionário `CHARACTERS` no início do script.

---

## Testes feitos

- Conversão dos 7 FBX: todos com geometria, textura e esqueleto (37 a 81 ossos).
- Pré-visualização das três poses (`--preview`) para os 7: a pose de ligação é idêntica
  ao modelo original, e no repouso e no aceno os braços mexem-se corretamente.
- Simulador aberto: com cada planeta selecionado (1–8), o personagem certo aparece ao lado
  do planeta, com nome e frase no painel; Neptuno e Sol ficam sem personagem. Capturas na Terra e em
  Júpiter a 1,2 s e 2 s (aceno) e a 5 s (repouso).
- Custo: ~0,5 ms por frame para calcular a pose (81 ossos); FPS igual com e sem personagem.
- `test_sim.py` continua a passar.
