#version 330 core

/*
 * ============================================================================
 * CONCEITOS DE COMPUTAÇÃO GRÁFICA:
 * - Skinning Linear (Linear Blend Skinning) na GPU para os personagens animados.
 * - Cada vértice é influenciado por até 4 ossos (aJoints) com pesos (aWeights).
 *   A matriz de pele do vértice é a média pesada das matrizes dos ossos:
 *       Skin = w0·B[j0] + w1·B[j1] + w2·B[j2] + w3·B[j3]
 *   onde B[i] = C_i · G_i⁻¹ (pose atual × inverso da pose de ligação),
 *   calculada a cada frame no CPU por character_rig.py.
 * - Depois do skinning, o resto é igual ao celestial.vert: Model → View →
 *   Projection, e as normais seguem a mesma deformação.
 * - Usa o mesmo fragment shader (celestial.frag) para a iluminação Blinn-Phong.
 * ============================================================================
 */

const int MAX_BONES = 128;

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoords;
layout (location = 3) in vec4 aJoints;    // índices dos ossos (guardados como float)
layout (location = 4) in vec4 aWeights;   // pesos (somam 1)

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoords;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat3 uNormalMatrix;
uniform mat4 uBones[MAX_BONES];

void main()
{
    mat4 skin = aWeights.x * uBones[int(aJoints.x)]
              + aWeights.y * uBones[int(aJoints.y)]
              + aWeights.z * uBones[int(aJoints.z)]
              + aWeights.w * uBones[int(aJoints.w)];

    vec4 skinnedPos = skin * vec4(aPos, 1.0);
    vec3 skinnedNormal = mat3(skin) * aNormal;

    vec4 worldPos = uModel * skinnedPos;
    FragPos = vec3(worldPos);
    Normal = normalize(uNormalMatrix * skinnedNormal);
    TexCoords = aTexCoords;
    gl_Position = uProjection * uView * worldPos;
}
