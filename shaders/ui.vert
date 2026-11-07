#version 330 core

/*
 * Shader de Vértices para a Interface 2D (Overlay Ortográfico).
 */

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoords;

out vec2 TexCoords;

uniform mat4 uOrthoProjection; // Matriz ortográfica 2D (largura x altura)

void main()
{
    TexCoords = aTexCoords;
    gl_Position = uOrthoProjection * vec4(aPos, 0.0, 1.0);
}
