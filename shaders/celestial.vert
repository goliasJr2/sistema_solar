#version 330 core

/*
 * ============================================================================
 * CONCEITOS DE COMPUTAÇÃO GRÁFICA:
 * - Pipeline Gráfico: Etapa de Processamento de Vértices (Vertex Shader).
 * - Coordenadas 3D:
 *     1. Espaço de Objeto (Local): aPos e aNormal
 *     2. Espaço de Mundo (World Space): FragPos = uModel * aPos
 *     3. Espaço de Vista/Câmara (View Space): uView * FragPos
 *     4. Espaço de Recorte Homogéneo (Clip Space): gl_Position = uProjection * ...
 * - Matrizes:
 *     - uModel: posiciona, orienta (inclinação axial e rotação) e escala o corpo celeste.
 *     - uView: posiciona e orienta a câmara no universo.
 *     - uProjection: projeta a cena 3D com perspetiva e razão de aspeto corretas.
 *     - uNormalMatrix: matriz 3x3 (inversa transposta de model) que preserva a
 *       ortogonalidade das normais em escalas não uniformes.
 * ============================================================================
 */

layout (location = 0) in vec3 aPos;       // Posição local do vértice na esfera UV
layout (location = 1) in vec3 aNormal;    // Vetor normal à superfície da esfera
layout (location = 2) in vec2 aTexCoords; // Coordenadas de textura UV [0, 1]

out vec3 FragPos;      // Posição do fragmento no Espaço de Mundo
out vec3 Normal;       // Vetor normal transformado no Espaço de Mundo
out vec2 TexCoords;    // Coordenadas UV interpoladas para o Fragment Shader

uniform mat4 uModel;        // Matriz de Modelo (Model)
uniform mat4 uView;         // Matriz de Vista (View)
uniform mat4 uProjection;   // Matriz de Projeção em Perspetiva (Projection)
uniform mat3 uNormalMatrix; // Matriz Normal: transpose(inverse(mat3(uModel)))

void main()
{
    // 1. Transformação para Espaço de Mundo
    vec4 worldPos = uModel * vec4(aPos, 1.0);
    FragPos = vec3(worldPos);

    // 2. Transformação correta do vetor normal
    Normal = normalize(uNormalMatrix * aNormal);

    // 3. Passagem de coordenadas UV para mapeamento de textura
    TexCoords = aTexCoords;

    // 4. Projeção final para Clip Space (Pipeline Gráfico da GPU)
    gl_Position = uProjection * uView * worldPos;
}
