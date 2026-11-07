"""
===============================================================================
Módulo: texture.py
Descrição: Carregamento e gestão de texturas 2D com Pillow e PyOpenGL.
Conceitos aplicados:
  - Carregamento de imagem e decodificação de formatos (JPEG, PNG).
  - Alinhamento de eixos UV com o sistema OpenGL (FLIP_TOP_BOTTOM).
  - Configuração de amostragem: Wrapping (GL_REPEAT, GL_CLAMP_TO_EDGE)
    e Filtragem (GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR).
  - Geração de Mipmaps para antialiasing em superfícies distantes.
  - Filtragem Anisotrópica para superfícies vistas em ângulos oblíquos.
  - Fallback Procedural: Geração de texturas planetárias procedurais em caso
    de ausência de ficheiros externos, garantindo resiliência total contra falhas.
===============================================================================
"""

from pathlib import Path
from typing import Dict, Tuple
import math
import numpy as np
from PIL import Image, ImageDraw
from OpenGL.GL import (
    glGenTextures,
    glBindTexture,
    glTexImage2D,
    glGenerateMipmap,
    glTexParameteri,
    glTexParameterf,
    glGetFloatv,
    glActiveTexture,
    glDeleteTextures,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_RGB,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_REPEAT,
    GL_CLAMP_TO_EDGE,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
)

# Constantes para Filtragem Anisotrópica (Extensão EXT)
GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE
GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FF


class Texture:
    """Encapsula um objeto de textura 2D do OpenGL."""

    def __init__(self, texture_id: int, width: int, height: int):
        self.id = texture_id
        self.width = width
        self.height = height

    def bind(self, unit: int = 0) -> None:
        """Ativa a unidade de textura e vincula o objeto."""
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, self.id)

    def cleanup(self) -> None:
        """Desaloca a textura da GPU."""
        if self.id != 0:
            glDeleteTextures(1, [self.id])
            self.id = 0


class TextureLoader:
    """Gestor de carregamento de texturas com cache e gerador procedural de fallback."""

    _cache: Dict[str, Texture] = {}

    @classmethod
    def load(cls, file_path: Path, fallback_key: str = "generic") -> Texture:
        """
        Carrega uma textura a partir do ficheiro indicado.
        Se o ficheiro não existir, emite aviso na consola e gera uma textura
        procedural estilizada de alta definição sem interromper o programa.
        """
        path_str = str(file_path)
        if path_str in cls._cache:
            return cls._cache[path_str]

        image = None
        if file_path.exists():
            try:
                # Carregamento com Pillow
                image = Image.open(file_path)
            except Exception as e:
                print(f"[Texture Warning] Falha ao abrir {file_path}: {e}. A usar textura procedural.")

        if image is None:
            print(f"[Texture Info] Textura '{file_path.name}' não encontrada. A gerar textura procedural para '{fallback_key}'...")
            image = cls._generate_procedural_texture(fallback_key)
            # Opcional: gravar a textura procedural gerada para acelerar execuções futuras
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(file_path)
                print(f"[Texture Info] Textura procedural guardada com sucesso em: {file_path}")
            except Exception:
                pass

        # Inverte verticalmente a imagem para igualar a origem (0,0) do OpenGL (canto inferior esquerdo)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)

        mode = image.mode
        if mode == "RGBA":
            gl_format = GL_RGBA
        else:
            image = image.convert("RGB")
            gl_format = GL_RGB

        img_data = image.tobytes()
        width, height = image.size

        # Criação da textura no OpenGL
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        # Envio de pixels para a GPU
        glTexImage2D(GL_TEXTURE_2D, 0, gl_format, width, height, 0, gl_format, GL_UNSIGNED_BYTE, img_data)

        # Geração de Mipmaps
        glGenerateMipmap(GL_TEXTURE_2D)

        # Configuração de Wrapping: REPEAT na horizontal (longitude) e CLAMP_TO_EDGE nos polos (latitude)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # Configuração de Filtragem com interpolação trilinear
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Filtragem Anisotrópica (quando suportada pela GPU)
        try:
            max_aniso = glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
            if max_aniso and max_aniso > 1.0:
                glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, min(8.0, float(max_aniso)))
        except Exception:
            pass

        texture_obj = Texture(tex_id, width, height)
        cls._cache[path_str] = texture_obj
        return texture_obj

    @classmethod
    def _generate_procedural_texture(cls, key: str, width: int = 1024, height: int = 512) -> Image.Image:
        """Gera texturas esféricas equirretangulares estéticas para cada corpo celeste."""
        key = key.lower()
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        if "sun" in key:
            # Sol: Gradiente quente com granulação coronal
            for y in range(height):
                factor = 1.0 - 0.25 * math.sin(math.pi * y / height)
                r = min(255, int(255 * factor))
                g = min(255, int(180 * factor + 40 * math.cos(y * 0.05)))
                b = min(255, int(40 * factor))
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif "mercury" in key:
            # Mercúrio: Superfície rochosa cinza com crateras
            np.random.seed(42)
            noise = np.random.normal(140, 25, (height, width)).clip(70, 200).astype(np.uint8)
            img = Image.fromarray(np.stack([noise, noise, noise], axis=-1))
        elif "venus" in key:
            # Vénus: Atmosfera densa com tons creme, bege e ocre
            for y in range(height):
                v_band = 0.5 + 0.5 * math.sin(y * 0.06) + 0.2 * math.cos(y * 0.15)
                r = int(220 + 25 * v_band)
                g = int(185 + 20 * v_band)
                b = int(120 + 20 * v_band)
                draw.line([(0, y), (width, y)], fill=(min(255, r), min(255, g), min(255, b)))
        elif "earth" in key:
            # Terra: Oceanos azuis, continentes verdes/castanhos e calotas polares
            for y in range(height):
                lat = (y / height - 0.5) * 2.0  # -1 a 1
                if abs(lat) > 0.85:
                    # Calotas de gelo polares
                    draw.line([(0, y), (width, y)], fill=(240, 245, 255))
                else:
                    draw.line([(0, y), (width, y)], fill=(25, 70, 160))  # Oceano
            # Desenha algumas massas continentais representativas
            draw.ellipse([width * 0.15, height * 0.25, width * 0.35, height * 0.70], fill=(50, 130, 60))
            draw.ellipse([width * 0.45, height * 0.20, width * 0.75, height * 0.65], fill=(70, 140, 50))
            draw.ellipse([width * 0.55, height * 0.65, width * 0.70, height * 0.85], fill=(160, 140, 70))
        elif "mars" in key:
            # Marte: Terreno avermelhado com calotas de gelo
            for y in range(height):
                lat = (y / height - 0.5) * 2.0
                if abs(lat) > 0.90:
                    draw.line([(0, y), (width, y)], fill=(245, 240, 235))
                else:
                    band = 0.5 + 0.5 * math.sin(y * 0.08)
                    r = int(185 + 35 * band)
                    g = int(75 + 20 * band)
                    b = int(45 + 15 * band)
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif "jupiter" in key:
            # Júpiter: Bandas atmosféricas zonais e Grande Mancha Vermelha
            for y in range(height):
                band = math.sin(y * 0.12) * math.cos(y * 0.04)
                r = int(195 + 45 * band)
                g = int(145 + 35 * band)
                b = int(105 + 25 * band)
                draw.line([(0, y), (width, y)], fill=(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
            # A Grande Mancha Vermelha
            draw.ellipse([width * 0.60, height * 0.60, width * 0.72, height * 0.72], fill=(190, 65, 45))
        elif "saturn" in key:
            # Saturno: Faixas suaves em tons dourados e bege
            for y in range(height):
                band = math.sin(y * 0.08)
                r = int(210 + 25 * band)
                g = int(185 + 20 * band)
                b = int(140 + 15 * band)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif "uranus" in key:
            # Úrano: Disco ciano/turquesa suave
            for y in range(height):
                draw.line([(0, y), (width, y)], fill=(155, 215, 225))
        elif "neptune" in key:
            # Neptuno: Azul celeste profundo vibrante
            for y in range(height):
                band = math.sin(y * 0.05)
                r = int(45 + 15 * band)
                g = int(95 + 25 * band)
                b = int(210 + 35 * band)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        elif "moon" in key:
            # Lua: Tons de cinza e crateras
            np.random.seed(101)
            noise = np.random.normal(160, 20, (height, width)).clip(80, 220).astype(np.uint8)
            img = Image.fromarray(np.stack([noise, noise, noise], axis=-1))
        else:
            # Padrão genérico
            for y in range(height):
                draw.line([(0, y), (width, y)], fill=(128, 128, 128))

        return img
