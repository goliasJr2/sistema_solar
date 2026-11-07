#version 330 core

/*
 * Shader de Fragmentos para a Interface de Utilizador com Transparência Alfa.
 */

in vec2 TexCoords;
out vec4 FragColor;

uniform sampler2D uTexture;
uniform float uOpacity; // Opacidade geral do elemento de interface

void main()
{
    vec4 col = texture(uTexture, TexCoords);
    FragColor = vec4(col.rgb, col.a * uOpacity);
}
