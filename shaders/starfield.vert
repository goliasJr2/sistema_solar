#version 330 core

/*
 * ============================================================================
 * CONCEITOS DE COMPUTAÇÃO GRÁFICA:
 * - Primitivas Gráficas: GL_POINTS para renderização de campo estelar em massa.
 * - Vertex Shader com gl_PointSize para controlo individual da dimensão do ponto.
 * - Animação Procedural: cintilação estelar baseada na função sin(tempo).
 * ============================================================================
 */

layout (location = 0) in vec3  aPos;   // Coordenadas 3D da estrela na esfera celeste
layout (location = 1) in vec3  aColor; // Cor espectral da estrela (O, B, A, F, G, K, M)
layout (location = 2) in float aSize;  // Tamanho intrínseco da estrela

out vec3 StarColor;
out float StarAlpha;

uniform mat4 uView;       // Matriz de visualização da câmara
uniform mat4 uProjection; // Matriz de projeção
uniform float uTime;      // Tempo decorrido em segundos para cintilação

void main()
{
    // Apenas a rotação da câmara afeta o fundo estelar (ignora translação para simular infinito)
    mat4 viewNoTrans = mat4(mat3(uView));
    gl_Position = uProjection * viewNoTrans * vec4(aPos, 1.0);

    // Efeito sutil de cintilação estelar no tempo
    float twinkle = 0.85 + 0.15 * sin(uTime * 3.0 + aPos.x * 12.0 + aPos.y * 7.0);
    gl_PointSize = aSize * twinkle;

    StarColor = aColor;
    StarAlpha = 0.9 * twinkle;
}
