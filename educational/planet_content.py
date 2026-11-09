"""
===============================================================================
Módulo: educational/planet_content.py
Descrição: Conteúdo científico estruturado e pedagógico para todos os corpos
           do Sistema Solar. Apresentado pelo Guia Virtual 3D.
===============================================================================
"""

from typing import List, Dict
from .earth_content import LessonSection, EARTH_LESSON_SECTIONS


PRESENTERS_CONFIG: Dict[str, dict] = {
    "earth": {
        "name": "Tracy",
        "title": "Guia Astronómica Terrestre",
        "badge": "👩‍🚀 TRACY",
        "role": "Apresentadora do Lar Cósmico",
        "character": "remy",
    },
    "mercury": {
        "name": "Tracy",
        "title": "Apresentadora do Mensageiro Veloz",
        "badge": "👩‍🚀 TRACY",
        "role": "Especialista em Planetas Interiores",
        "character": "remy",
    },
    "venus": {
        "name": "Tracy",
        "title": "Apresentadora de Mundos Extremos",
        "badge": "👩‍🚀 TRACY",
        "role": "Investigadora da Atmosfera de Vénus",
        "character": "remy",
    },
    "mars": {
        "name": "Goblin Kayden",
        "title": "Explorador Marciano",
        "badge": "👺 GOBLIN KAYDEN",
        "role": "Desbravador do Planeta Vermelho",
        "character": "goblin",
    },
    "uranus": {
        "name": "Goblin Kayden",
        "title": "Explorador de Gigantes de Gelo",
        "badge": "👺 GOBLIN KAYDEN",
        "role": "Investigador de Mundos Inclinados",
        "character": "goblin",
    },
    "jupiter": {
        "name": "Mutante Travor",
        "title": "Comandante de Titãs Gasosos",
        "badge": "🧬 MUTANTE TRAVOR",
        "role": "Comandante da Frota Joviana",
        "character": "mutant",
    },
    "saturn": {
        "name": "Mutante Travor",
        "title": "Comandante das Joias Aneladas",
        "badge": "🧬 MUTANTE TRAVOR",
        "role": "Guardião dos Anéis de Saturno",
        "character": "mutant",
    },
    "neptune": {
        "name": "Warrok Yin Yang",
        "title": "Mestre dos Ventos Cósmicos",
        "badge": "🐾 WARROK YIN YANG",
        "role": "Filósofo das Fronteiras Cósmicas",
        "character": "warrok",
    },
    "sun": {
        "name": "Warrok Baskerville",
        "title": "O Guardião Feroz dos Baskerville",
        "badge": "🐾 WARROK BASKERVILLE",
        "role": "Farejador do Fogo Solar",
        "character": "warrok",
    },
    "black_hole": {
        "name": "Mutante Travor",
        "title": "Sentinela do Vazio & Buracos Negros",
        "badge": "🛡️ SENTINELA MUTANTE",
        "role": "Defesa & Escape Gravitacional",
        "character": "mutant",
    },
}


def get_presenter_for(body_id: str) -> dict:
    """Retorna os dados do apresentador responsável pelo corpo celeste ou singularidade."""
    return PRESENTERS_CONFIG.get(body_id or "", PRESENTERS_CONFIG["earth"])


PLANET_LESSONS: Dict[str, List[LessonSection]] = {

    # ── TERRA ─────────────────────────────────────────────────────────────────
    "earth": EARTH_LESSON_SECTIONS,

    # ── SOL ───────────────────────────────────────────────────────────────────
    "sun": [
        LessonSection(
            id=1,
            title="☀️ O Sol, a nossa estrela",
            summary="O coração do sistema. Concentra 99,86% de toda a massa do Sistema Solar.",
            speech_text=(
                "O Sol é o coração do sistema. Concentra 99,86% de toda a massa do Sistema Solar, e os planetas, luas e asteroides somam o resto. "
                "É uma anã amarela (tipo G2V) com cerca de 4,6 mil milhões de anos, e ainda tem combustível para outros 5 mil milhões. "
                "Composição: cerca de 73% hidrogénio e 25% hélio. "
                "Energia: no núcleo, a temperatura chega a 15 milhões de graus Celsius. Aí, a fusão nuclear transforma hidrogénio em hélio e liberta a energia que ilumina tudo. "
                "Superfície (fotosfera): cerca de 5.500 graus Celsius. A coroa, a atmosfera exterior, chega a mais de 1 milhão de graus Celsius, e ninguém sabe ao certo porque é mais quente do que a superfície. É um dos grandes mistérios da astrofísica. "
                "Curiosidade: a luz demora cerca de 8 minutos e 20 segundos a chegar até nós. Quando olhamos para o Sol, vemos o passado."
            ),
            estimated_duration_sec=35.0,
            keywords=["Sol", "Anã Amarela", "G2V", "Fusão Nuclear", "Fotosfera", "Coroa Solar"],
        ),
        LessonSection(
            id=2,
            title="☀️ Composição e Energia Nuclear do Sol",
            summary="Fusão nuclear a 15 milhões °C no núcleo e composição de 73% hidrogénio e 25% hélio.",
            speech_text=(
                "Composição: cerca de 73% hidrogénio e 25% hélio. "
                "Energia: no núcleo, a temperatura chega a 15 milhões de graus Celsius. Aí, a fusão nuclear transforma hidrogénio em hélio e liberta a energia que ilumina tudo."
            ),
            estimated_duration_sec=16.0,
            keywords=["Composição", "Hidrogénio", "Hélio", "Fusão Nuclear", "Núcleo"],
        ),
        LessonSection(
            id=3,
            title="☀️ Superfície, Coroa e o Olhar para o Passado",
            summary="Fotosfera a 5.500 °C, mistério da coroa a 1 milhão °C e luz solar a 8m 20s.",
            speech_text=(
                "Superfície (fotosfera): cerca de 5.500 graus Celsius. A coroa, a atmosfera exterior, chega a mais de 1 milhão de graus Celsius, e ninguém sabe ao certo porque é mais quente do que a superfície. É um dos grandes mistérios da astrofísica. "
                "Curiosidade: a luz demora cerca de 8 minutos e 20 segundos a chegar até nós. Quando olhamos para o Sol, vemos o passado."
            ),
            estimated_duration_sec=20.0,
            keywords=["Fotosfera", "Coroa", "Mistério da Astrofísica", "Luz Solar", "Passado"],
        ),
    ],

    # ── MERCÚRIO ──────────────────────────────────────────────────────────────
    "mercury": [
        LessonSection(
            id=1,
            title="☿ Mercúrio, o mensageiro veloz",
            summary="O mais pequeno e mais próximo do Sol, órbita de 88 dias e temperaturas de 430 °C a -180 °C.",
            speech_text=(
                "O mais pequeno e o mais próximo do Sol. Dá a volta ao Sol em apenas 88 dias. "
                "Atmosfera: praticamente inexistente (uma exosfera muito ténue de oxigénio, sódio e hidrogénio). "
                "Temperaturas extremas: 430 graus Celsius de dia e 180 graus negativos de noite, porque sem atmosfera não há nada que retenha o calor. "
                "Singularidade: um dia solar dura 176 dias terrestres, o dobro do seu ano. Está cheio de crateras e tem gelo de água nas crateras permanentemente à sombra dos polos."
            ),
            estimated_duration_sec=28.0,
            keywords=["Mercúrio", "Exosfera", "Temperaturas Extremas", "Dia Solar", "Crateras"],
        ),
    ],

    # ── VÉNUS ─────────────────────────────────────────────────────────────────
    "venus": [
        LessonSection(
            id=1,
            title="♀ Vénus, o irmão infernal",
            summary="O planeta mais quente do Sistema Solar, 465 °C, pressão 90x da Terra e rotação retrógrada.",
            speech_text=(
                "Quase do tamanho da Terra, mas um inferno. É o planeta mais quente do Sistema Solar, apesar de não ser o mais próximo do Sol. "
                "Atmosfera: 96% dióxido de carbono, com nuvens de ácido sulfúrico. A pressão à superfície é 90 vezes a da Terra, equivalente a estar 900 metros debaixo de água. "
                "Temperatura: cerca de 465 graus Celsius, o suficiente para derreter chumbo. É o efeito de estufa descontrolado. "
                "Singularidade: gira ao contrário (rotação retrógrada) e muito devagar: um dia em Vénus dura mais do que o seu ano. Aí, o Sol nasce a oeste."
            ),
            estimated_duration_sec=30.0,
            keywords=["Vénus", "Efeito de Estufa", "Ácido Sulfúrico", "Rotação Retrógrada", "Pressão"],
        ),
    ],

    # ── MARTE ─────────────────────────────────────────────────────────────────
    "mars": [
        LessonSection(
            id=1,
            title="♂ Marte, o planeta vermelho",
            summary="Óxido de ferro no solo, Monte Olimpo de 22 km, Valles Marineris e luas Fobos e Deimos.",
            speech_text=(
                "A cor vem do óxido de ferro (ferrugem) no solo. "
                "Atmosfera: muito fina, 95% dióxido de carbono, com menos de 1% da pressão terrestre. É por isso que a água líquida não se mantém estável à superfície. "
                "Temperaturas: entre 125 graus negativos e 20 graus positivos. "
                "Singularidade: tem o Monte Olimpo, o maior vulcão do Sistema Solar (cerca de 22 quilómetros de altura, quase 3 vezes o Evereste) e o Valles Marineris, um cânion com mais de 4.000 quilómetros. Há sinais claros de que no passado teve rios e lagos. Tem duas luas pequenas, Fobos e Deimos."
            ),
            estimated_duration_sec=30.0,
            keywords=["Marte", "Óxido de Ferro", "Monte Olimpo", "Valles Marineris", "Fobos", "Deimos"],
        ),
    ],

    # ── JÚPITER ───────────────────────────────────────────────────────────────
    "jupiter": [
        LessonSection(
            id=1,
            title="♃ Júpiter, o gigante",
            summary="O maior planeta, cabem mais de 1.300 Terras, Grande Mancha Vermelha e mais de 90 luas.",
            speech_text=(
                "O maior planeta: cabem mais de 1.300 Terras lá dentro. Tem mais do dobro da massa de todos os outros planetas juntos. "
                "Atmosfera: hidrogénio em cerca de 90% e hélio em cerca de 10%, com faixas de nuvens de amoníaco. "
                "Grande Mancha Vermelha: uma tempestade maior do que a Terra, que dura há séculos. "
                "Singularidade: o dia mais curto de todos, cerca de 10 horas. Tem mais de 90 luas, incluindo Europa, que esconde um oceano debaixo do gelo e é um dos principais candidatos a albergar vida."
            ),
            estimated_duration_sec=30.0,
            keywords=["Júpiter", "Grande Mancha Vermelha", "Europa", "Titã Gasoso", "Mais de 90 Luas"],
        ),
    ],

    # ── SATURNO ───────────────────────────────────────────────────────────────
    "saturn": [
        LessonSection(
            id=1,
            title="♄ Saturno, o senhor dos anéis",
            summary="Densidade menor que a água, anéis de gelo e rocha, tempestade hexagonal e luas Titã e Encélado.",
            speech_text=(
                "O mais fotogénico, e tão leve que flutuaria na água (densidade menor que a da água). "
                "Atmosfera: hidrogénio e hélio, com ventos de até 1.800 quilómetros por hora. "
                "Anéis: feitos de gelo e rocha, de pedaços minúsculos a blocos do tamanho de casas. Estendem-se por centenas de milhares de quilómetros, mas com espessura de apenas dezenas de metros. "
                "Singularidade: no polo norte tem uma tempestade hexagonal. Tem mais de 140 luas confirmadas. Titã tem atmosfera densa e lagos de metano líquido, e Encélado expele jatos de água para o espaço."
            ),
            estimated_duration_sec=30.0,
            keywords=["Saturno", "Anéis de Gelo", "Tempestade Hexagonal", "Titã", "Encélado"],
        ),
    ],

    # ── ÚRANO ─────────────────────────────────────────────────────────────────
    "uranus": [
        LessonSection(
            id=1,
            title="⛢ Urano, o planeta deitado",
            summary="Gigante de gelo azul-esverdeado com inclinação de 98°, atmosfera a -224 °C e 27 luas de Shakespeare.",
            speech_text=(
                "Um gigante de gelo, de cor azul-esverdeada, devido ao metano na atmosfera, que absorve a luz vermelha. "
                "Atmosfera: hidrogénio, hélio e metano. "
                "Singularidade: roda de lado, com eixo inclinado a 98 graus, provavelmente devido a uma colisão gigante no passado. Cada polo passa 42 anos seguidos virado para o Sol e outros 42 na escuridão. "
                "Temperatura: cerca de 224 graus negativos, a atmosfera planetária mais fria registada, apesar de Neptuno estar mais longe. "
                "Tem anéis ténues e 27 luas conhecidas, com nomes de personagens de Shakespeare."
            ),
            estimated_duration_sec=30.0,
            keywords=["Urano", "Inclinação de 98°", "Gigante de Gelo", "Frio Extremo", "Shakespeare"],
        ),
    ],

    # ── NEPTUNO ───────────────────────────────────────────────────────────────
    "neptune": [
        LessonSection(
            id=1,
            title="♆ Neptuno, o azul profundo",
            summary="O último planeta a 4,5 mil milhões de km, ventos a 2.000 km/h, descoberto por matemática e Tritão.",
            speech_text=(
                "O último planeta, a 4,5 mil milhões de quilómetros do Sol. A luz solar demora mais de 4 horas a chegar lá. "
                "Atmosfera: hidrogénio, hélio e metano, com um azul mais vivo que Urano. "
                "Singularidade: tem os ventos mais rápidos do Sistema Solar, que chegam a mais de 2.000 quilómetros por hora. Foi o primeiro planeta descoberto por cálculos matemáticos, antes de ser observado. "
                "Um ano em Neptuno dura 165 anos terrestres. A lua Tritão orbita ao contrário e tem géiseres de azoto."
            ),
            estimated_duration_sec=29.0,
            keywords=["Neptuno", "Ventos Supersónicos", "Cálculos Matemáticos", "Tritão", "4.5 Mil Milhões km"],
        ),
    ],

    # ── BURACOS NEGROS / SINGULARIDADES CÓSMICAS ──────────────────────────────
    "black_hole": [
        LessonSection(
            id=1,
            title="🌀 Sagitário A*, o gigante da nossa casa",
            summary="No centro da Via Láctea a 26.000 anos-luz, 4,3 milhões de massas solares e imagem do EHT em 2022.",
            speech_text=(
                "Está no centro da Via Láctea, a cerca de 26.000 anos-luz de nós. "
                "Massa: cerca de 4,3 milhões de massas solares, concentradas numa região mais pequena do que a órbita de Mercúrio. "
                "Como o conhecemos: durante décadas, os astrónomos seguiram estrelas a orbitar um ponto invisível a velocidades enormes. "
                "Só um objeto supermassivo explicava aquele movimento, e isso valeu o Nobel da Física de 2020. "
                "Singularidade: em 2022, o Event Horizon Telescope divulgou a primeira imagem direta dele. Hoje está relativamente calmo, quase adormecido, com pouca matéria a cair para dentro."
            ),
            estimated_duration_sec=30.0,
            keywords=["Sagitário A*", "Via Láctea", "Nobel da Física 2020", "EHT", "Supermassivo"],
        ),
        LessonSection(
            id=2,
            title="🔥 M87*, o primeiro retrato",
            summary="No centro da galáxia Messier 87 a 55 milhões de anos-luz, 6,5 mil milhões de massas solares e primeiro fotografado.",
            speech_text=(
                "Está no centro da galáxia Messier 87, a cerca de 55 milhões de anos-luz. "
                "Massa: cerca de 6,5 mil milhões de massas solares, um verdadeiro monstro. "
                "Singularidade: foi o primeiro buraco negro fotografado, em abril de 2019. A imagem mostra um anel de luz laranja em redor de uma sombra escura, que é o disco de acreção distorcido pela gravidade. "
                "Jato: lança um jato de partículas a velocidades próximas da luz, com milhares de anos-luz de comprimento."
            ),
            estimated_duration_sec=29.0,
            keywords=["M87*", "Messier 87", "Primeira Fotografia", "Disco de Acreção", "Jato Relativístico"],
        ),
        LessonSection(
            id=3,
            title="⚡ Cygnus X-1, o pioneiro",
            summary="Na constelação do Cisne a 7.000 anos-luz, 21 massas solares e a famosa aposta Hawking-Thorne.",
            speech_text=(
                "Fica na constelação do Cisne, a cerca de 7.000 anos-luz. "
                "Massa: cerca de 21 massas solares, um buraco negro estelar. "
                "Como funciona: está em órbita com uma estrela azul gigante, da qual vai arrancando matéria. Esse gás aquece e emite raios X intensos, e é assim que o detetamos. "
                "Singularidade: foi um dos primeiros candidatos fortes a buraco negro, e ficou famoso por uma aposta entre Stephen Hawking e Kip Thorne sobre se era mesmo um buraco negro. Hawking apostou que não e perdeu."
            ),
            estimated_duration_sec=29.0,
            keywords=["Cygnus X-1", "Constelação do Cisne", "Raios X", "Stephen Hawking", "Kip Thorne"],
        ),
        LessonSection(
            id=4,
            title="🔭 Gaia BH1, o vizinho",
            summary="O buraco negro mais próximo da Terra a 1.600 anos-luz, silencioso e descoberto pelo satélite Gaia em 2022.",
            speech_text=(
                "É um dos buracos negros mais próximos da Terra, a cerca de 1.600 anos-luz, na constelação do Ofiúco. "
                "Massa: cerca de 10 massas solares. "
                "Singularidade: é um buraco negro silencioso. Não tem disco de acreção brilhante, por isso não emite raios X. Foi descoberto em 2022 pelo satélite Gaia, ao detetar uma estrela parecida com o Sol que dançava à volta de um companheiro invisível. "
                "Mensagem: mostra que pode haver milhões de buracos negros escondidos na nossa galáxia que nunca vimos."
            ),
            estimated_duration_sec=28.0,
            keywords=["Gaia BH1", "Ofiúco", "Mais Próximo", "Silencioso", "Satélite Gaia"],
        ),
        LessonSection(
            id=5,
            title="🌊 GW150914, o que fez o espaço tremer",
            summary="Fusão de dois buracos negros a 1,3 mil milhões de anos-luz, detetada por ondas gravitacionais pelo LIGO em 2015.",
            speech_text=(
                "Não é um buraco negro único, mas uma fusão de dois, a cerca de 1,3 mil milhões de anos-luz. "
                "O evento: dois buracos negros de cerca de 36 e 29 massas solares fundiram-se num só, com cerca de 62 massas solares. "
                "Singularidade: as três massas solares que faltam foram convertidas em energia sob a forma de ondas gravitacionais, detetadas pelo LIGO em setembro de 2015. Foi a primeira vez que a humanidade ouviu o universo através do espaço-tempo."
            ),
            estimated_duration_sec=29.0,
            keywords=["GW150914", "Fusão de Buracos Negros", "Ondas Gravitacionais", "LIGO 2015", "Espaço-Tempo"],
        ),
    ],
}

# Aliases diretos para acesso por chave de buraco negro
PLANET_LESSONS["sagittarius_a"] = [PLANET_LESSONS["black_hole"][0]]
PLANET_LESSONS["sagitario_a"] = [PLANET_LESSONS["black_hole"][0]]
PLANET_LESSONS["m87"] = [PLANET_LESSONS["black_hole"][1]]
PLANET_LESSONS["cygnus_x1"] = [PLANET_LESSONS["black_hole"][2]]
PLANET_LESSONS["gaia_bh1"] = [PLANET_LESSONS["black_hole"][3]]
PLANET_LESSONS["gw150914"] = [PLANET_LESSONS["black_hole"][4]]
PLANET_LESSONS["gargantua"] = [PLANET_LESSONS["black_hole"][0]]

