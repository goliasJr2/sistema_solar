"""
===============================================================================
Módulo: educational/earth_content.py
Descrição: Conteúdo científico estruturado e pedagógico sobre o Planeta Terra.
Apresentado pelo Guia Virtual 3D como um professor sénior de astronomia.
===============================================================================
"""

from dataclasses import dataclass
from typing import List


@dataclass
class LessonSection:
    id: int
    title: str
    summary: str
    speech_text: str
    estimated_duration_sec: float
    keywords: List[str]


EARTH_LESSON_SECTIONS: List[LessonSection] = [
    LessonSection(
        id=1,
        title="1. Introdução à Terra: O Nosso Oásis Cósmico",
        summary="Apresentação do terceiro planeta a contar do Sol e o único porto de vida conhecido no cosmos.",
        speech_text=(
            "Ruf! Olá viajante cósmico! Sou o Baskerville, o cão de caça dos Baskerville e o teu guia pelo cosmos. "
            "Com o meu faro apurado, vamos farejar e explorar em detalhe o nosso planeta-mãe: a Terra! "
            "Situada a aproximadamente cento e cinquenta milhões de quilómetros do Sol, a Terra é o terceiro planeta "
            "do Sistema Solar e o único lar com vida conhecido em todo o Universo. Vista do espaço profundo, "
            "assemelha-se a um deslumbrante ponto azul pálido, protegido pela escuridão do vazio estelar."
        ),
        estimated_duration_sec=22.0,
        keywords=["Terra", "Sistema Solar", "Terceiro Planeta", "Vida", "Ponto Azul"],
    ),
    LessonSection(
        id=2,
        title="2. Dimensões e Características Físicas",
        summary="Diâmetro equatorial de 12.742 km, achatamento polar e massa de 5,97 sextilhões de toneladas.",
        speech_text=(
            "Em termos de dimensões, a Terra é o maior dos quatro planetas telúricos ou rochosos. "
            "Apresenta um diâmetro equatorial de cerca de doze mil setecentos e quarenta e dois quilómetros. "
            "No entanto, não é uma esfera geométrica perfeita: devido à força centrífuga originada pela sua rotação, "
            "a Terra tem a forma de um esferoide oblato, ligeiramente achatado nos polos e abaulado no equador. "
            "A sua massa atinge uns impressionantes cinco vírgula noventa e sete vezes dez elevado a vinte e quatro quilogramas, "
            "com uma densidade média de cinco vírgula cinquenta e dois gramas por centímetro cúbico, a mais densa do Sistema Solar."
        ),
        estimated_duration_sec=28.0,
        keywords=["Diâmetro", "Esferoide Oblato", "Massa", "Densidade", "Planeta Telúrico"],
    ),
    LessonSection(
        id=3,
        title="3. Estrutura Interna e Núcleo Dinâmico",
        summary="Crosta superficial, Manto rochoso convectivo, Núcleo Externo líquido e Núcleo Interno sólido de ferro e níquel.",
        speech_text=(
            "Se cortássemos a Terra ao meio, descobriríamos uma estrutura dividida em camadas dinâmicas. "
            "À superfície encontra-se a crosta, uma fina camada rochosa sólida que varia entre cinco quilómetros no fundo oceânico "
            "e até setenta quilómetros sob as maiores cadeias de montanhas. Por baixo, estende-se o manto, que atinge cerca de "
            "dois mil e novecentos quilómetros de profundidade, com rochas em lenta convecção térmica. No coração planetário "
            "reside o núcleo: uma camada externa de ferro e níquel fundidos em estado líquido, que envolve um núcleo interno sólido "
            "com temperaturas na ordem dos cinco mil e quatrocentos graus Celsius, comparáveis à superfície do Sol!"
        ),
        estimated_duration_sec=32.0,
        keywords=["Crosta", "Manto", "Núcleo Externo", "Núcleo Interno", "Geodinamo"],
    ),
    LessonSection(
        id=4,
        title="4. A Atmosfera Protetora",
        summary="Mistura equilibrada de 78% Nitrogénio, 21% Oxigénio e escudo contra radiação ultravioleta e meteoroides.",
        speech_text=(
            "O manto de ar que nos envolve e protege é a atmosfera terrestre. É composta primordialmente por setenta e oito "
            "por cento de nitrogénio molecular, vinte e um por cento de oxigénio vital e um por cento de outros gases como árgon, "
            "vapor de água e dióxido de carbono. Esta fina película gasosa desempenha um papel duplo e crucial: retém o calor térmico "
            "através de um efeito de estufa natural moderado, desintegra a esmagadora maioria dos meteoroides antes de atingirem o solo "
            "e contém a camada de ozono na estratosfera, que absorve as letais radiações ultravioleta emitidas pela nossa estrela."
        ),
        estimated_duration_sec=29.0,
        keywords=["Atmosfera", "Nitrogénio", "Oxigénio", "Camada de Ozono", "Efeito de Estufa"],
    ),
    LessonSection(
        id=5,
        title="5. Movimento de Rotação e Ciclo Circadiano",
        summary="Giro sobre o próprio eixo em 23 horas, 56 minutos e 4 segundos, com inclinação axial de 23,44 graus.",
        speech_text=(
            "A Terra realiza um giro contínuo em torno do seu eixo imaginário de oeste para este, num fenómeno designado por rotação. "
            "O período sideral de rotação é de exatamente vinte e três horas, cinquenta e seis minutos e quatro segundos. "
            "Este movimento é responsável pelo ciclo perpétuo entre o dia e a noite. Um fator de capital importância científica "
            "é a inclinação do eixo terrestre, atualmente fixada em vinte e três vírgula quarenta e quatro graus em relação à perpendicular "
            "da eclítica, um dos maiores pilares para a estabilidade da biosfera."
        ),
        estimated_duration_sec=26.0,
        keywords=["Rotação", "Dia Sideral", "Inclinação Axial", "23.44 graus", "Dia e Noite"],
    ),
    LessonSection(
        id=6,
        title="6. Movimento de Translação e as Estações do Ano",
        summary="Órbita elíptica em torno do Sol completada em 365,25 dias com velocidade média de 107.000 km/h.",
        speech_text=(
            "Simultaneamente à rotação, o planeta percorre uma trajetória elíptica ao redor do Sol a uma impressionante velocidade "
            "orbital média de cento e sete mil quilómetros por hora, perfazendo trinta quilómetros por segundo! O ciclo de translação "
            "completa-se em aproximadamente trezentos e sessenta e cinco dias e seis horas, o que motiva a criação dos anos bissextos. "
            "A combinação mágica entre a translação elíptica e a inclinação constante do eixo de rotação faz com que cada hemisfério "
            "receba insolação variável ao longo dos meses, gerando a sucessão harmoniosa das quatro estações do ano: Primavera, Verão, Outono e Inverno."
        ),
        estimated_duration_sec=32.0,
        keywords=["Translação", "Órbita Elíptica", "Estações do Ano", "Velocidade Orbital", "Ano Bissexto"],
    ),
    LessonSection(
        id=7,
        title="7. A Magnetosfera e o Escudo Invisível",
        summary="Campo magnético bipolar gerado pelo efeito geodinâmico no núcleo externo que canaliza o vento solar.",
        speech_text=(
            "Um dos maiores prodígios físicos da Terra é invisível aos nossos olhos: a magnetosfera. Ela atua como um colossal escudo magnético, "
            "gerado pelo efeito geodinâmico das correntes de ferro líquido condutor em rotação no núcleo externo. Este campo estende-se por "
            "dezenas de milhares de quilómetros no espaço exterior, defletindo o vento solar e partículas cósmicas de alta energia que, de outro modo, "
            "varreriam a atmosfera e extinguiriam toda a vida à superfície. Quando estas partículas energéticas interagem com os gases polares, "
            "somos presenteados com o magnífico espetáculo das auroras boreais e austrais."
        ),
        estimated_duration_sec=31.0,
        keywords=["Magnetosfera", "Geodinamo", "Vento Solar", "Auroras Boreais", "Proteção Cósmica"],
    ),
    LessonSection(
        id=8,
        title="8. A Lua: A Dança Gravitacional e Estabilização",
        summary="Satélite natural que modula as marés oceânicas e impede oscilações caóticas no eixo terrestre.",
        speech_text=(
            "A Terra não viaja sozinha nesta odisseia cósmica: é acompanhada pela Lua, o seu único satélite natural, situado a uma distância "
            "média de trezentos e oitenta e quatro mil quilómetros. A atração gravitacional conjunta da Lua e do Sol gera as marés que "
            "oxigenam os oceanos e moldam os ecossistemas costeiros. Mas o papel mais profundo da Lua reside na estabilidade climática: "
            "a sua presença impede que o eixo de rotação da Terra sofra oscilações oscilatórias caóticas, como as que afetam Marte, "
            "garantindo um clima estável ao longo de centenas de milhões de anos."
        ),
        estimated_duration_sec=28.0,
        keywords=["Lua", "Satélite Natural", "Marés", "Estabilização Axial", "Gravidade"],
    ),
    LessonSection(
        id=9,
        title="9. Água Líquida e a Zona Habitável",
        summary="Cerca de 71% da superfície coberta por oceanos no ponto ideal de equilíbrio térmico da Zona Goldilocks.",
        speech_text=(
            "A grande singularidade da Terra é a abundância perpétua de água nos seus três estados da matéria, com especial primazia "
            "para a água líquida, cobrindo cerca de setenta e um por cento de toda a superfície planetária. Isto só é possível porque "
            "a Terra orbita no centro da chamada Zona Habitável ou Zona Goldilocks do Sol, onde a radiação estelar é perfeitamente "
            "temperada: nem tão quente que evapore irreversivelmente os oceanos, nem tão fria que congele perpetuamente as águas. "
            "A água funciona como solvente universal bioquímico e como regulador térmico global imbatível."
        ),
        estimated_duration_sec=30.0,
        keywords=["Água Líquida", "Zona Habitável", "Oceanos", "Zona Goldilocks", "Ciclo Hidrológico"],
    ),
    LessonSection(
        id=10,
        title="10. O Lugar Singular da Terra no Cosmos",
        summary="A responsabilidade humana na preservação do nosso lar frágil e precioso no oceano do cosmos.",
        speech_text=(
            "Ao contemplarmos os milhares de exoplanetas já catalogados pelos nossos telescópios espaciais, a lição mais profunda que "
            "retiramos é a extrema raridade e preciosidade da Terra. Até ao momento, não encontrámos nenhum outro santuário onde a geologia, "
            "a química, a atmosfera e a astronomia tenham convergido de forma tão miraculosa para gerar a autoconsciência da vida. "
            "A Terra não é apenas uma plataforma rochosa: é o nosso único lar partilhado no imenso vazio interestelar. Cuidar dela e "
            "compreender as leis que a regem é a missão suprema da ciência e de toda a humanidade. Muito obrigado pela vossa atenção!"
        ),
        estimated_duration_sec=33.0,
        keywords=["Conclusão", "Exoplanetas", "Preservação", "Lar Cósmico", "Ciência e Futuro"],
    ),
]
