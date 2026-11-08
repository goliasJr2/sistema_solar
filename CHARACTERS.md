# Personagens Apresentadores dos Planetas

Cada planeta passa a ter um **personagem 3D** que aparece ao lado dele quando é
selecionado. O personagem fica virado para a câmara e balança suavemente; o nome
e uma frase sobre o planeta aparecem no painel de informação (tecla **I**).

---

## Como usar

| Ação | Resultado |
|---|---|
| **1–8**, **TAB** / **SHIFT+TAB** ou **clique** num planeta | O personagem desse planeta aparece à direita do planeta (com uma pequena animação de entrada) |
| **9** / **H** (Sol) ou **0** (vista geral) | Nenhum personagem é mostrado |
| **I** | Mostra / oculta o painel; a secção **Apresentador** mostra o nome e a frase do personagem |

Não há teclas novas: o personagem segue a seleção de planetas que já existia.

---

## Personagem de cada planeta

| Planeta | Personagem | Modelo usado pelo simulador | FBX de origem (já existia em `Models/`) |
|---|---|---|---|
| Mercúrio | Ely | `Models/characters/ely.glb` | `Models/character (2).fbx` |
| Vénus | Vanguard | `Models/characters/vanguard.glb` | `Models/character (1).fbx` |
| Terra | Remy | `Models/characters/remy.glb` | `Models/character.fbx` |
| Marte | Maw | `Models/characters/maw.glb` | `Models/character (3).fbx` |
| Júpiter | Warrok | `Models/characters/warrok.glb` | `Models/Warrok W Kurniawan.fbx` |
| Saturno | Mutant | `Models/characters/mutant.glb` | `Models/Mutant.fbx` |
| Úrano | Goblin | `Models/characters/goblin.glb` | `Models/goblin_d_shareyko.fbx` |
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

---

## O que mudou no código

| Ficheiro | Tipo | O que faz |
|---|---|---|
| `tools/fbx_to_glb.py` | **novo** | Converte os `.fbx` para `.glb` (ver abaixo) |
| `Models/characters/*.glb` | **novo** | Os 7 personagens convertidos (1,6 a 6,4 MB cada; ~18 MB no total) |
| `characters.json` | **novo** | Tabela planeta → personagem (modelo, frase, créditos, ajustes) |
| `characters.py` | **novo** | Classe `PlanetCharacters`: carrega e desenha o personagem do planeta selecionado |
| `main.py` | alterado | Cria `PlanetCharacters`, desenha-o a seguir ao Sistema Solar (passo **7b** do ciclo) e envia os dados do personagem para a UI ao selecionar um planeta |
| `ui.py` | alterado | Novo método `set_presenter()` e secção **Apresentador** no painel de informação |

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
4. Aplica a transformação local da malha, põe o personagem de pé (+Y), virado
   para +Z, com altura 2,0 e centrado;
5. Reduz as texturas a 1024 px no máximo (as originais têm até 4096 px) e grava o `.glb`.

O esqueleto e as animações são ignorados: o personagem fica na pose em T em que
foi exportado.

### Como o personagem é desenhado (`characters.py`)

- **Carregamento preguiçoso:** cada `.glb` só é lido na primeira vez que o seu planeta
  é selecionado (pode haver uma pausa de ~1 s nessa primeira vez); depois fica em cache.
- **Posição:** `planeta + camera.right × (raio × side_offset)` — sempre à direita do
  planeta no ecrã, fora do painel de informação, que está à esquerda.
- **Tamanho:** `altura = raio visual do planeta × height_factor`.
- **Orientação:** rotação em Y para ficar de frente para a câmara, com balanço de ±12°
  e uma leve flutuação vertical.
- **Entrada:** escala de 0 → 1 em 0,6 s com *easing* ao mudar de planeta.
- **Iluminação:** usa o shader `celestial` já existente, mas com a luz junto à câmara
  ("luz de estúdio") e ambiente mais forte, para o personagem nunca ficar às escuras
  no lado noturno do planeta.
- O *face culling* é desligado só durante o desenho do personagem (cabelo e roupa têm
  faces visíveis dos dois lados).

---

## Trocar ou adicionar um personagem

Exemplo: pôr a Nami (One Piece) em Neptuno.

1. **Arranjar o modelo** em `.glb` (por exemplo no [Sketchfab](https://sketchfab.com),
   que exige conta para descarregar). **Verifique a licença**: personagens de anime
   são propriedade dos seus autores, e muitos modelos feitos por fãs só permitem uso
   não comercial. Registe o autor e a licença em `characters.json` (`source` / `license`).
2. **Pôr o ficheiro** em `Models/characters/nami.glb`.
   - Se o modelo vier em `.fbx` binário, converta-o:
     ```bash
     .venv\Scripts\python.exe tools\fbx_to_glb.py "Models\nami.fbx" "Models\characters\nami.glb" --preview
     ```
     O `--preview` grava `nami.preview.png` ao lado, para confirmar que ficou de pé e com textura
     (apague a imagem depois; não deve ir para o repositório).
   - Se já vier em `.glb`, convém que esteja de pé (+Y) e virado para +Z.
3. **Editar `characters.json`:**
   ```json
   "neptune": {
     "character": "Nami",
     "model": "Models/characters/nami.glb",
     "tagline": "Navegadora do planeta dos ventos mais fortes: 2100 km/h.",
     "source": "Sketchfab — <autor> — <link>",
     "license": "<licença do modelo>"
   }
   ```
4. Correr o simulador e carregar em **8**.

Ajustes opcionais por planeta em `characters.json`:

| Campo | Padrão | Efeito |
|---|---|---|
| `height_factor` | 1.4 | Altura do personagem em múltiplos do raio do planeta |
| `side_offset` | 2.1 | Distância ao centro do planeta, para a direita (Saturno usa 2.9 por causa dos anéis) |

Com `"model": null`, o planeta fica sem personagem.

### Reconverter os 7 personagens Mixamo

```bash
.venv\Scripts\python.exe tools\fbx_to_glb.py
```
A lista de ficheiros a converter está no dicionário `CHARACTERS` no início do script.

---

## Testes feitos

- Conversão dos 7 FBX: todos com geometria e textura (verificado com as imagens `--preview`).
- Simulador aberto e cada planeta (1–8) selecionado com capturas de ecrã: personagem
  visível ao lado do planeta, com nome e frase no painel; Neptuno e Sol sem personagem.
- FPS igual com e sem personagem no ecrã (o custo é de 11–35 mil triângulos).
- `test_sim.py` continua a passar.
