# Simulador Astronómico Inteligente 3D (Grupo 1)
**Trabalho Prático de Computação Gráfica**  
**Implementação:** Python com PyOpenGL e GLFW (OpenGL 3.3 Core Profile)

---

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de que tem o Python instalado (Python 3.10 ou 3.11 recomendado). As dependências necessárias estão no ficheiro `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Dependências: `PyOpenGL`, `glfw`, `Pillow`, `numpy`, `PyGLM`, `trimesh`)*

### 2. Iniciar a Simulação
Para iniciar o simulador completo:
```bash
python main.py
```

---

## 🎮 Manual de Execução e Tabela Completa de Controlos

### 🎥 Câmara e Navegação
| Tecla / Controlo | Ação |
|---|---|
| **Rato Esquerdo + Arrastar** | Rotação orbital ao redor do foco (Yaw / Pitch) |
| **Rato Direito + Arrastar** | Pan da câmara (deslocamento lateral / vertical) |
| **Roda do Rato (Scroll)** | Zoom suave contínuo (aproximar / afastar) |
| **W / S** | Avançar / Recuar no espaço 3D |
| **A / D** | Strafe esquerda / direita |
| **Q / E** | Descer / Subir verticalmente |
| **T** | **Ligar / Desligar Rastreamento Dinâmico**: A câmara acompanha o planeta em sua órbita elíptica em torno do Sol, mantendo-o sempre enquadrado |
| **P** | **Alternar Modos de Câmara (Fusão WilmerCP)**: Cicla entre **EXPLORE** (voo livre panorâmico), **FOLLOW** (acompanhamento orbital à distância) e **FOCUS** (inspeção próxima da superfície) |

### 🪐 Planetas e Sistema Solar
| Tecla | Ação |
|---|---|
| **1** | Focar em **Mercúrio** |
| **2** | Focar em **Vénus** |
| **3** | Focar na **Terra** (com Lua subordinada) |
| **4** | Focar em **Marte** (com Fobos e Deimos) |
| **5** | Focar em **Júpiter** (com 4 luas Galileanas) |
| **6** | Focar em **Saturno** (com Anéis poligonais e Titã) |
| **7** | Focar em **Úrano** (com rotação retrógrada a 97°) |
| **8** | Focar em **Neptuno** (com Tritão) |
| **9** ou **H** | Focar no **Sol** (centro do Sistema Solar) |
| **0** | **Vista Geral do Sistema Solar**: enquadramento completo centrado no Sol |
| **TAB** | **Ciclar para o próximo planeta** na sequência orbital |
| **SHIFT + TAB** | **Ciclar para o planeta anterior** |
| **Clique com o Rato** | **Ray Picking 3D**: seleção direta do corpo celeste clicado |

### ⏱️ Tempo e Simulação Física
| Tecla | Ação |
|---|---|
| **ESPAÇO** | **Pausar / Retomar** a simulação física |
| **R** | **Reinício completo** (Tempo=0, Câmara padrão, Velocidade=10 dias/s) |
| **+** ou **=** | Acelerar velocidade orbital simulada (até 1.000.000x) |
| **-** | Desacelerar velocidade orbital (mínimo 0.01x) |

### 🌌 Módulos Cósmicos
| Tecla | Módulo | Descrição |
|---|---|---|
| **O** | **Órbitas Elípticas** | Alterna as trajetórias keplerianas 3D dos planetas e cometas |
| **N** ou **P** | **Campo de Estrelas (Starfield)** | Alterna o fundo espacial com 3500 estrelas cintilantes |
| **B** | **Cintura de Asteroides** | Alterna a cintura de asteroides principal entre Marte e Júpiter |
| **C** | **Cometa 3I/ATLAS** | Alterna o cometa em órbita altamente excêntrica com cauda dinâmica |
| **L** | **Satélites Artificiais** | Alterna a estação orbital da Terra e o foguetão lunar Apollo |
| **M** | **Chuva de Meteoros** | Alterna a tempestade de meteoros e bólides atmosféricos |
| **▲ (Seta Cima)** | **Alerta & Descoberta Cósmica** | Ao sair do Sistema Solar (deixando o Sol para trás): segurar por 5s dispara o **Alerta de Perigo Espaço-Temporal**; continuar por mais 5s revela o **Buraco Negro** diretamente à sua frente |
| **ALT** | **Frente a Frente Cósmico** | Teleporta a câmara e coloca-a imediatamente **Frente a Frente** com a singularidade (e cicla entre os 8 modelos 3D espalhados pelo espaço profundo) |
| **G** | **Buracos Negros** | Cicla o foco e inspeciona as 8 singularidades cósmicas |
| **V** | **Galáxia Espiral** | Alterna a visualização da Via Láctea com 250.000 estrelas |

### 🔭 Escalas Cósmicas e Transições Cinematográficas
| Tecla | Nível de Escala | Descrição |
|---|---|---|
| **F2** | **Nível 1 — Galáxia** | Visão macroscópica da Via Láctea e Sagitário A* |
| **F3** | **Nível 2 — Região Estelar** | Vizinhança local (Alfa Centauri, CoRoT-7b) |
| **F4** | **Nível 3 — Sistema Solar** | Visão didática padrão centrada no Sol |
| **ENTER** | **Nível 4 — Superfície** | Descida suave rasante à superfície do planeta selecionado |
| **ESC** | **Voltar / Sair** | Se estiver na superfície, volta ao Sistema Solar; caso contrário fecha |

### 📊 Interface e Informação
| Tecla | Ação |
|---|---|
| **I** | Mostrar / Ocultar Painel de Dados Astronómicos Reais (NASA/JPL) |
| **F1** | Mostrar / Ocultar Ecrã de Ajuda com todos os comandos |

---

## 🛠️ Correções e Melhorias Implementadas

1. **Normalização Geométrica Global de Modelos 3D (.glb)**:
   - Resolução das distorções de Júpiter (fatiado em 8 submalhas), Saturno (esfera + múltiplos anéis) e Neptuno através da extração com hierarquia de nós resolvida (`dump(concatenate=False)`) e normalização universal pelo diâmetro esférico central.
2. **Posicionamento e Translação Orbital**:
   - Inicialização correta de todos os corpos celestes no tempo inicial T=0 (`body.update(0.0, 0.0)`).
   - Rastreamento dinâmico de câmara (`[T]`): a câmara move-se junto com o planeta selecionado sem que ele fuja do campo de visão durante o movimento kepleriano.
3. **Iluminação Cósmica e Visibilidade**:
   - Luz ambiente estelar ajustada para evitar o escurecimento total (100% preto) dos planetas exteriores (Saturno, Úrano, Neptuno) no lado noturno.
4. **Shader Solar Dinâmico Procedural (Fusão WilmerCP)**:
   - Incorporação de ruído procedural e turbulência de plasma em tempo real no `sun.frag`, criando atividade solar dinâmica, flares e incandescência estelar em constante movimento.
5. **Shader de Anéis com Projeção Analítica de Sombra (Fusão WilmerCP)**:
   - Implementação de ray-tracing analítico em `ring.frag`: a esfera física de Saturno projeta uma sombra escura e suave (*smoothstep penumbra*) diretamente sobre a malha de anéis `saturn_ring.png`, simulando a oclusão física da luz solar.
6. **Modos de Câmara Unificados (Explore / Follow / Focus)**:
   - Ciclo de navegação acionado por `[P]`, com exibição em tempo real do estado no HUD superior.
7. **Sistema Cósmico de 8 Buracos Negros e Encontro Imediato**:
   - Carregamento de todos os 8 modelos 3D de singularidades presentes em `Models/` (`black_hole.glb`, `black_hole_12.glb`, `black_hole_galaxy.glb`, `black_hole (1).glb`, `black_hole (2).glb`, `black_hole (3).glb`, `black_hole_12 (1).glb` e `not_a_black_hole_-_1.glb`), distribuídos em direções cósmicas esféricas a 360°.
   - Mecânica dinâmica de descoberta: ao sair do Sistema Solar e navegar com a seta para cima `[▲]` (ou `W`), 5 segundos acionam um alerta de perigo gravitacional no HUD; mais 5 segundos revelam e posicionam a singularidade primária à frente da sua trajetória.
   - Tecla `[ALT]`: teletransporte instantâneo para ficar frente a frente com o buraco negro, permitindo inspecionar o horizonte de eventos e ciclar entre todas as singularidades.
