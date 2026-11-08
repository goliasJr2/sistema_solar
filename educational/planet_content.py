"""
===============================================================================
Módulo: educational/planet_content.py
Descrição: Conteúdo científico estruturado e pedagógico para todos os corpos
           do Sistema Solar. Apresentado pelo Guia Virtual 3D.
===============================================================================
"""

from typing import List, Dict
from .earth_content import LessonSection, EARTH_LESSON_SECTIONS


PLANET_LESSONS: Dict[str, List[LessonSection]] = {

    # ── TERRA ─────────────────────────────────────────────────────────────────
    "earth": EARTH_LESSON_SECTIONS,

    # ── SOL ───────────────────────────────────────────────────────────────────
    "sun": [
        LessonSection(
            id=1,
            title="1. O Sol: A Nossa Estrela Mãe",
            summary="O Sol é a estrela central do Sistema Solar e a fonte de quase toda a energia da vida na Terra.",
            speech_text=(
                "Bem-vindos ao centro do nosso Sistema Solar: o Sol! Esta estrela colossal tem um diâmetro de cerca de "
                "um milhão e trezentos e noventa mil quilómetros, sendo aproximadamente cento e nove vezes maior do que "
                "a Terra. Classificada como uma anã amarela do tipo espectral G2V, o Sol contém noventa e nove vírgula "
                "oito por cento de toda a massa do Sistema Solar. A sua gravidade monumental mantém em órbita os oito "
                "planetas, os planetas anões, asteroides, cometas e toda a nuvem de Oort."
            ),
            estimated_duration_sec=24.0,
            keywords=["Sol", "Anã Amarela", "G2V", "Massa", "Gravidade"],
        ),
        LessonSection(
            id=2,
            title="2. Fusão Nuclear e Produção de Energia",
            summary="O Sol converte hidrogénio em hélio pelo processo de fusão nuclear, libertando energia colossal.",
            speech_text=(
                "O motor do Sol é a fusão nuclear termonuclear. No núcleo solar, onde as temperaturas atingem quinze "
                "milhões de graus Celsius e a pressão é duzentas e cinquenta mil vezes superior à da superfície "
                "terrestre, átomos de hidrogénio fundem-se para formar hélio. Cada segundo, o Sol converte cerca de "
                "seiscentos milhões de toneladas de hidrogénio em hélio, libertando uma quantidade de energia "
                "equivalente a quatro vírgula dois vezes dez elevado a vinte e seis watts. Esta fusão é regida pela "
                "famosa equação de Einstein: E é igual a mc ao quadrado."
            ),
            estimated_duration_sec=26.0,
            keywords=["Fusão Nuclear", "Hidrogénio", "Hélio", "Energia", "Einstein"],
        ),
        LessonSection(
            id=3,
            title="3. Estrutura Solar e Atividade Magnética",
            summary="O Sol possui núcleo, zona radiativa, zona convectiva, fotosfera, cromosfera e coroa solar.",
            speech_text=(
                "O Sol é estruturado em camadas distintas. O núcleo é rodeado pela zona radiativa, onde os fotões "
                "demoram dezenas de milhares de anos a viajar até à superfície. A zona convectiva transporta energia "
                "por correntes de plasma quente e frio. A fotosfera visível, a seis mil graus Celsius, é onde surgem "
                "as manchas solares — regiões magneticamente ativas e mais frias. A coroa solar, a camada mais externa, "
                "atinge temperaturas de um a dois milhões de graus Celsius, num paradoxo ainda não totalmente "
                "explicado pela ciência. É daqui que parte o vento solar que atravessa todo o Sistema Solar."
            ),
            estimated_duration_sec=28.0,
            keywords=["Fotosfera", "Coroa Solar", "Manchas Solares", "Vento Solar", "Plasma"],
        ),
    ],

    # ── MERCÚRIO ──────────────────────────────────────────────────────────────
    "mercury": [
        LessonSection(
            id=1,
            title="1. Mercúrio: O Mensageiro Veloz",
            summary="O menor e mais interior planeta do Sistema Solar, com órbita extremamente excêntrica e rápida.",
            speech_text=(
                "Mercúrio é o planeta mais próximo do Sol e o menor do Sistema Solar, com apenas quatro mil "
                "oitocentos e setenta e nove quilómetros de diâmetro, ligeiramente maior do que a Lua da Terra. "
                "Orbita o Sol a uma distância média de apenas cinquenta e oito milhões de quilómetros, completando "
                "uma volta em apenas oitenta e oito dias terrestres. A sua superfície é intensamente craterizada, "
                "recordando a nossa Lua, e está coberta de planícies vulcânicas antigas e escarpas de compressão "
                "denominadas rupes, formadas quando o planeta arrefeceu e contraiu ao longo de milhares de milhões de anos."
            ),
            estimated_duration_sec=23.0,
            keywords=["Mercúrio", "Planeta Interior", "Crateras", "Órbita", "Rupes"],
        ),
        LessonSection(
            id=2,
            title="2. Extremos de Temperatura e Ausência de Atmosfera",
            summary="Mercúrio apresenta as maiores amplitudes térmicas do Sistema Solar devido à quase ausência de atmosfera.",
            speech_text=(
                "Sem uma atmosfera protetora significativa, Mercúrio sofre as maiores amplitudes térmicas de todo o "
                "Sistema Solar. Durante o dia, a temperatura superficial pode atingir quatrocentos e trinta graus "
                "Celsius, enquanto à noite despenca para cento e oitenta graus negativos. Esta amplitude de mais de "
                "seiscentos graus é simplesmente extraordinária. Mercúrio possui apenas uma exosfera vestigial "
                "composta por sódio, oxigénio, hidrogénio e hélio, continuamente reposta pelo vento solar e "
                "impactos de meteoroides."
            ),
            estimated_duration_sec=22.0,
            keywords=["Temperatura", "Exosfera", "Amplitude Térmica", "Vento Solar", "Ausência de Atmosfera"],
        ),
        LessonSection(
            id=3,
            title="3. Campo Magnético e Núcleo Metálico",
            summary="Mercúrio possui surpreendentemente um campo magnético global gerado por um grande núcleo de ferro.",
            speech_text=(
                "Uma das maiores surpresas científicas de Mercúrio é a existência de um campo magnético global, "
                "embora cerca de cem vezes mais fraco do que o da Terra. Este campo é gerado pelo seu imenso núcleo "
                "de ferro, que ocupa aproximadamente oitenta e cinco por cento do raio do planeta — o maior núcleo "
                "relativo de qualquer planeta rochoso. A missão MESSENGER da NASA, que orbitou Mercúrio entre dois "
                "mil e onze e dois mil e quinze, confirmou a existência de gelo de água nos crateras polares "
                "permanentemente na sombra, numa descoberta revolucionária para a ciência planetária."
            ),
            estimated_duration_sec=25.0,
            keywords=["Campo Magnético", "Núcleo de Ferro", "MESSENGER", "Gelo Polar", "NASA"],
        ),
    ],

    # ── VÉNUS ─────────────────────────────────────────────────────────────────
    "venus": [
        LessonSection(
            id=1,
            title="1. Vénus: O Planeta Gémeo Infernal",
            summary="Vénus é o planeta mais brilhante do céu noturno e o mais quente do Sistema Solar.",
            speech_text=(
                "Vénus é frequentemente chamado de planeta gémeo da Terra por ter dimensões semelhantes: "
                "doze mil cento e quatro quilómetros de diâmetro, contra doze mil setecentos e quarenta e dois "
                "da Terra. No entanto, ali termina a semelhança! Vénus é o planeta mais quente do Sistema Solar, "
                "com uma temperatura superficial média de quatrocentos e sessenta e cinco graus Celsius, "
                "suficiente para fundir chumbo. É visível a olho nu como o objeto mais brilhante do céu, "
                "depois do Sol e da Lua, tendo sido chamado de Estrela da Manhã e Estrela da Tarde."
            ),
            estimated_duration_sec=23.0,
            keywords=["Vénus", "Planeta Gémeo", "Temperatura", "Mais Quente", "Estrela da Manhã"],
        ),
        LessonSection(
            id=2,
            title="2. O Efeito de Estufa Descontrolado",
            summary="A atmosfera densa de CO₂ cria o mais intenso efeito de estufa do Sistema Solar.",
            speech_text=(
                "A atmosfera de Vénus é uma lição devastadora sobre o efeito de estufa. Composta por noventa e seis "
                "por cento de dióxido de carbono e quatro por cento de azoto, com nuvens espessas de ácido sulfúrico, "
                "cria uma pressão superficial noventa e duas vezes superior à da Terra — equivalente a um quilómetro "
                "de profundidade oceânica. Este espesso casaco de dióxido de carbono aprisiona o calor de forma tão "
                "eficaz que Vénus é mais quente do que Mercúrio, apesar de estar muito mais afastado do Sol. "
                "É o exemplo clássico de um efeito de estufa descontrolado."
            ),
            estimated_duration_sec=25.0,
            keywords=["Efeito de Estufa", "CO2", "Dióxido de Carbono", "Ácido Sulfúrico", "Pressão"],
        ),
        LessonSection(
            id=3,
            title="3. Rotação Retrógrada e Vulcanismo Ativo",
            summary="Vénus roda no sentido contrário aos outros planetas e possui imenso vulcanismo ativo.",
            speech_text=(
                "Vénus apresenta duas peculiaridades fascinantes. Primeiro, roda no sentido retrógrado — ao contrário "
                "da maioria dos planetas — com um dia venusiano de duzentos e quarenta e três dias terrestres, "
                "mais longo do que o seu próprio ano de duzentos e vinte e cinco dias. Segundo, as sondas espaciais "
                "revelaram uma superfície dominada pelo vulcanismo, com mais de mil setecentos grandes vulcões "
                "identificados. Dados recentes da sonda Magellan e da missão EnVision sugerem que Vénus pode ainda "
                "ter vulcanismo ativo, tornando-o geologicamente dinâmico."
            ),
            estimated_duration_sec=25.0,
            keywords=["Rotação Retrógrada", "Vulcanismo", "Dia Venusiano", "Magellan", "EnVision"],
        ),
    ],

    # ── MARTE ─────────────────────────────────────────────────────────────────
    "mars": [
        LessonSection(
            id=1,
            title="1. Marte: O Planeta Vermelho",
            summary="Marte é o quarto planeta, com metade do diâmetro da Terra e marcas de imenso vulcanismo e canyons.",
            speech_text=(
                "Marte, o Planeta Vermelho, é o quarto planeta a contar do Sol e o destino mais explorado da "
                "humanidade após a Lua. Com um diâmetro de seis mil setecentos e setenta e nove quilómetros — "
                "cerca de metade do da Terra — apresenta a mais alta montanha do Sistema Solar: o Olympus Mons, "
                "com vinte e dois quilómetros de altitude. A sua cor avermelhada deve-se ao óxido de ferro, "
                "literalmente ferrugem, que cobre a sua superfície. Marte possui dois pequenos satélites naturais, "
                "Fobos e Deimos, provavelmente asteroides capturados."
            ),
            estimated_duration_sec=23.0,
            keywords=["Marte", "Olympus Mons", "Óxido de Ferro", "Fobos", "Deimos"],
        ),
        LessonSection(
            id=2,
            title="2. Atmosfera Fina e Condições Climáticas",
            summary="Marte tem atmosfera de CO₂ muito rarefeita, com tempestades de pó globais e temperatura média negativa.",
            speech_text=(
                "A atmosfera marciana é composta por noventa e cinco por cento de dióxido de carbono, mas é "
                "extremamente rarefeita — apenas um por cento da pressão atmosférica da Terra. A temperatura média "
                "superficial é de menos sessenta graus Celsius, variando entre menos cento e vinte e trinta e cinco "
                "graus positivos no equador durante o verão. Marte é famoso pelas suas tempestades de pó globais, "
                "que podem cobrir o planeta inteiro durante meses. O Valles Marineris, o maior sistema de cânions "
                "do Sistema Solar, estende-se por quatro mil quilómetros de comprimento."
            ),
            estimated_duration_sec=25.0,
            keywords=["Atmosfera Marciana", "Valles Marineris", "Tempestades de Pó", "Temperatura", "CO2"],
        ),
        LessonSection(
            id=3,
            title="3. Exploração e Perspetivas de Colonização",
            summary="Múltiplas missões robóticas exploram Marte, com planos humanos para colonização futura.",
            speech_text=(
                "Marte é atualmente explorado por uma frota de robôs: os rovers Curiosity e Perseverance analisam "
                "rochas e procuram sinais de vida passada, enquanto o helicóptero Ingenuity provou ser possível "
                "voar numa atmosfera tão rarefeita. As análises confirmaram que Marte tinha água líquida há "
                "mais de três mil milhões de anos e ainda possui água congelada nos polos e subsolo. Esta "
                "descoberta alimenta o debate sobre vida microbiana passada. Agências como a NASA e a SpaceX "
                "desenvolvem planos para enviar humanos a Marte nas próximas décadas, tornando-o potencialmente "
                "o segundo lar da humanidade."
            ),
            estimated_duration_sec=27.0,
            keywords=["Perseverance", "Curiosity", "Ingenuity", "Água em Marte", "Colonização"],
        ),
    ],

    # ── JÚPITER ───────────────────────────────────────────────────────────────
    "jupiter": [
        LessonSection(
            id=1,
            title="1. Júpiter: O Rei dos Planetas",
            summary="Júpiter é o maior planeta do Sistema Solar, com massa equivalente a 318 Terras.",
            speech_text=(
                "Júpiter é o maior planeta do nosso Sistema Solar por uma margem esmagadora. Com um diâmetro "
                "equatorial de cento e quarenta e dois mil e oitocentos quilómetros — mais de onze vezes o da Terra — "
                "e uma massa equivalente a trezentas e dezoito Terras, Júpiter é verdadeiramente colossal. "
                "Na verdade, Júpiter contém mais do dobro da massa de todos os outros planetas combinados. "
                "O seu campo gravitacional poderoso capturou pelo menos noventa e cinco luas confirmadas, incluindo "
                "as quatro grandes luas galileanas: Io, Europa, Ganimedes e Calisto, descobertas por Galileu em "
                "mil seiscentos e dez."
            ),
            estimated_duration_sec=24.0,
            keywords=["Júpiter", "Maior Planeta", "Luas Galileanas", "Io", "Europa"],
        ),
        LessonSection(
            id=2,
            title="2. A Grande Mancha Vermelha e Dinâmica Atmosférica",
            summary="Júpiter possui a maior tempestade do Sistema Solar, ativa há mais de 350 anos.",
            speech_text=(
                "O símbolo mais icónico de Júpiter é a Grande Mancha Vermelha, um anticiclone gigantesco com "
                "mais de dezasseis mil quilómetros de diâmetro — maior do que a Terra inteira! Esta tempestade "
                "dura há mais de trezentos e cinquenta anos de observação humana, com ventos que ultrapassam "
                "quinhentos quilómetros por hora. A atmosfera joviana é dominada por bandas de nuvens paralelas "
                "de amónia e sulfureto de hidrogénio e amónia, coloridas em castanho, laranja, branco e creme. "
                "Os relâmpagos de Júpiter são milhares de vezes mais poderosos do que os da Terra."
            ),
            estimated_duration_sec=25.0,
            keywords=["Grande Mancha Vermelha", "Tempestade", "Anticiclone", "Amónia", "Relâmpagos"],
        ),
        LessonSection(
            id=3,
            title="3. Protetor do Sistema Solar Interior",
            summary="A massa de Júpiter atua como escudo gravitacional que protege os planetas interiores de impactos.",
            speech_text=(
                "Júpiter desempenha um papel crucial na estabilidade do Sistema Solar interior: a sua enorme massa "
                "atua como um escudo gravitacional, atraindo e desviando cometas e asteroides que de outra forma "
                "poderiam colidir com a Terra. Em mil novecentos e noventa e quatro, o cometa Shoemaker-Levy 9 "
                "fragmentou-se e embateu em Júpiter numa série dramática de impactos televisionados mundialmente. "
                "A lua Europa, com o seu oceano de água salgada líquida sob uma crosta de gelo, é considerada um "
                "dos locais mais promissores para a procura de vida extraterrestre no Sistema Solar."
            ),
            estimated_duration_sec=26.0,
            keywords=["Escudo Gravitacional", "Shoemaker-Levy 9", "Europa", "Oceano Subsuperficial", "Vida Extraterrestre"],
        ),
    ],

    # ── SATURNO ───────────────────────────────────────────────────────────────
    "saturn": [
        LessonSection(
            id=1,
            title="1. Saturno: A Joia do Sistema Solar",
            summary="Saturno é famoso pelos seus magníficos anéis e é o único planeta menos denso do que a água.",
            speech_text=(
                "Saturno é inegavelmente o planeta mais espetacular do Sistema Solar. Com um diâmetro equatorial "
                "de cento e vinte mil e quinhentos quilómetros e uma massa de noventa e cinco Terras, é o segundo "
                "maior planeta. Mas o que o torna verdadeiramente único é o seu vasto sistema de anéis, que se "
                "estende por mais de trezentos mil quilómetros a partir do equador, compostos principalmente de "
                "gelo de água com partículas entre milímetros e metros. Saturno tem a densidade mais baixa de "
                "qualquer planeta — tão baixa que flutuaria sobre água!"
            ),
            estimated_duration_sec=23.0,
            keywords=["Saturno", "Anéis", "Gelo", "Densidade Baixa", "Espetacular"],
        ),
        LessonSection(
            id=2,
            title="2. Os Anéis: Composição e Origem",
            summary="Os anéis de Saturno são compostos de gelo e rocha e têm apenas 10 a 100 metros de espessura.",
            speech_text=(
                "Os anéis de Saturno são uma maravilha da física gravitacional. Apesar de se estenderem por "
                "centenas de milhares de quilómetros em largura, têm uma espessura média de apenas dez a cem "
                "metros. São compostos por fragmentos de gelo, rocha e pó, organizados em faixas concêntricas "
                "denominadas A, B, C, D, E, F e G. A missão Cassini-Huygens, que orbitou Saturno entre dois "
                "mil e quatro e dois mil e dezassete, revelou que os anéis têm apenas trezentos a quatrocentos "
                "milhões de anos de idade — relativamente jovens à escala cósmica — e estão a desaparecer "
                "gradualmente para Saturno, num fenómeno chamado chuva de anéis."
            ),
            estimated_duration_sec=26.0,
            keywords=["Anéis", "Cassini-Huygens", "Gelo de Água", "Chuva de Anéis", "Espessura"],
        ),
        LessonSection(
            id=3,
            title="3. Titã: A Lua com Oceanos de Metano",
            summary="Titã, a maior lua de Saturno, tem atmosfera densa e lagos de metano líquido na superfície.",
            speech_text=(
                "Saturno tem oitenta e três luas confirmadas, sendo Titã a mais fascinante. Com cinco mil cento "
                "e cinquenta quilómetros de diâmetro, é a segunda maior lua do Sistema Solar e a única com uma "
                "atmosfera densa, composta por nitrogénio e metano. Na superfície de Titã, a menos cento e "
                "oitenta graus Celsius, existem lagos e rios de metano e etano líquido, seguindo um ciclo "
                "hidrológico análogo ao da água na Terra. A sonda Huygens aterrou em Titã em dois mil e cinco, "
                "revelando planícies de areia de hidrocarbonetos e rios secos. A missão Dragonfly da NASA, "
                "prevista para a próxima década, irá explorar Titã com um veículo drone."
            ),
            estimated_duration_sec=28.0,
            keywords=["Titã", "Metano", "Atmosfera", "Huygens", "Dragonfly"],
        ),
    ],

    # ── ÚRANO ─────────────────────────────────────────────────────────────────
    "uranus": [
        LessonSection(
            id=1,
            title="1. Úrano: O Planeta Deitado",
            summary="Úrano órbita o Sol praticamente de lado, com uma inclinação axial de 97,8 graus.",
            speech_text=(
                "Úrano é o sétimo planeta do Sistema Solar e um dos mais enigmáticos. Com um diâmetro de "
                "cinquenta e um mil e oitocentos quilómetros — quatro vezes o da Terra — pertence à família "
                "dos gigantes de gelo. O que torna Úrano único é a sua inclinação axial extrema de noventa "
                "e sete vírgula oito graus, o que significa que orbita o Sol praticamente deitado de lado. "
                "Esta inclinação dramática é provavelmente o resultado de uma colisão colossal com um objeto "
                "do tamanho da Terra durante a formação do Sistema Solar há cerca de quatro mil milhões de anos."
            ),
            estimated_duration_sec=23.0,
            keywords=["Úrano", "Inclinação Axial", "Gigante de Gelo", "97.8 Graus", "Colisão Primordial"],
        ),
        LessonSection(
            id=2,
            title="2. Composição e Estrutura Interna",
            summary="Úrano é um gigante de gelo com manto de água, amónia e metano em estado supercrítico.",
            speech_text=(
                "Ao contrário dos gigantes gasosos Júpiter e Saturno, Úrano é classificado como gigante de gelo. "
                "O seu manto é composto por uma mistura de água, amónia e metano em estado supercrítico — nem "
                "sólido nem gasoso. É o metano na atmosfera superior que absorve a luz vermelha e reflete a "
                "luz azul-esverdeada, dando a Úrano a sua cor característica de azul pálido. A temperatura "
                "mínima da sua troposfera é de menos duzentos e vinte e quatro graus Celsius, tornando Úrano "
                "o planeta mais frio do Sistema Solar, apesar de Neptuno estar mais distante do Sol."
            ),
            estimated_duration_sec=24.0,
            keywords=["Gigante de Gelo", "Metano", "Cor Azul", "Temperatura", "Supercrítico"],
        ),
        LessonSection(
            id=3,
            title="3. Sistema de Anéis e Luas",
            summary="Úrano possui 13 anéis escuros e 27 luas com nomes de personagens de Shakespeare e Pope.",
            speech_text=(
                "Úrano possui um sistema de treze anéis conhecidos, muito mais escuros e estreitos do que os "
                "de Saturno, compostos por partículas de poeira e pequenas pedras escuras ricas em carbono. "
                "O planeta tem também vinte e sete luas confirmadas, todas com nomes inspirados em personagens "
                "das obras de William Shakespeare e Alexander Pope, como Miranda, Ariel, Umbriel, Titânia "
                "e Oberon. A lua Miranda destaca-se pela sua superfície caótica de falésias com até dez "
                "quilómetros de altura — as mais altas do Sistema Solar em proporção ao tamanho do corpo celeste."
            ),
            estimated_duration_sec=25.0,
            keywords=["Anéis de Úrano", "Miranda", "Shakespeare", "27 Luas", "Falésias"],
        ),
    ],

    # ── NEPTUNO ───────────────────────────────────────────────────────────────
    "neptune": [
        LessonSection(
            id=1,
            title="1. Neptuno: O Gigante do Vento",
            summary="Neptuno é o planeta mais distante do Sol, com os ventos mais fortes do Sistema Solar.",
            speech_text=(
                "Neptuno é o oitavo e mais distante planeta do Sistema Solar, situado a uma distância média "
                "de trinta unidades astronómicas — trinta vezes a distância Terra-Sol. Com quarenta e nove "
                "mil e quinhentos quilómetros de diâmetro, é ligeiramente mais pequeno do que Úrano, mas "
                "tem uma massa dezassete vezes superior à da Terra. Neptuno foi o único planeta cuja "
                "existência foi prevista matematicamente antes de ser observado: em mil oitocentos e quarenta "
                "e seis, Le Verrier e Adams previram a sua localização com base nas perturbações orbitais "
                "de Úrano, confirmando a genialidade das leis de Newton."
            ),
            estimated_duration_sec=24.0,
            keywords=["Neptuno", "Planeta Mais Distante", "Descoberta Matemática", "Le Verrier", "30 UA"],
        ),
        LessonSection(
            id=2,
            title="2. Ventos Supersónicos e Grande Mancha Escura",
            summary="Neptuno tem ventos de mais de 2.100 km/h e uma grande tempestade oval chamada Grande Mancha Escura.",
            speech_text=(
                "Neptuno é o planeta mais ventoso do Sistema Solar. Os seus ventos atingem velocidades "
                "superiores a dois mil e cem quilómetros por hora — mais rápidos do que o som! Esta "
                "violência atmosférica extrema é surpreendente dado que Neptuno recebe menos de um milésimo "
                "da radiação solar que a Terra. A sua energia interna interna deve ser a fonte desta "
                "dinâmica. A sonda Voyager 2, que sobrevoou Neptuno em mil novecentos e oitenta e nove, "
                "fotografou a Grande Mancha Escura, uma tempestade oval do tamanho da Terra, embora esta "
                "tenha desaparecido e novas tenham surgido posteriormente, observadas pelo Telescópio Hubble."
            ),
            estimated_duration_sec=26.0,
            keywords=["Ventos", "Grande Mancha Escura", "Voyager 2", "Hubble", "Tempestade"],
        ),
        LessonSection(
            id=3,
            title="3. Tritão: A Lua Capturada",
            summary="Tritão é a maior lua de Neptuno, orbita no sentido contrário e tem geysers de azoto.",
            speech_text=(
                "Neptuno tem catorze luas conhecidas, sendo Tritão a maior e mais extraordinária. Com "
                "dois mil setecentos quilómetros de diâmetro, Tritão órbita Neptuno no sentido retrógrado "
                "— o contrário da rotação do planeta — o que revela claramente que foi capturado do "
                "Cinturão de Kuiper e não se formou naturalmente com Neptuno. A sua superfície de azoto "
                "congelado tem apenas trinta e oito graus acima do zero absoluto, e a Voyager 2 detetou "
                "geysers ativos que expelem azoto gasoso a oito quilómetros de altitude. Tritão está em "
                "decaimento orbital e, em cerca de três mil milhões de anos, será destruído pela maré "
                "gravitacional de Neptuno."
            ),
            estimated_duration_sec=27.0,
            keywords=["Tritão", "Órbita Retrógrada", "Geysers", "Cinturão de Kuiper", "Decaimento Orbital"],
        ),
    ],
}
