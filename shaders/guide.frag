#version 330 core

/*
 * ============================================================================
 * SHADER: guide.frag
 * Descrição: Fragment Shader para o Astronomical Virtual Guide 3D.
 * Iluminação de Estúdio 3-Point Lighting (Key, Fill e Rim Light) com
 * reflexão Blinn-Phong e realce cinematográfico de apresentador cósmico.
 * ============================================================================
 */

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoords;

out vec4 FragColor;

uniform sampler2D uTexture;
uniform vec3 uViewPos;          // Posição da câmara do guia
uniform int uMeshType;          // Tipo de submalha
uniform vec3 uHighlightColor;   // Realce opcional de expressão

// Parâmetros de iluminação de estúdio
const vec3 KEY_LIGHT_DIR  = normalize(vec3(0.5, 0.8, 1.0));    // Luz principal frontal/superior
const vec3 KEY_LIGHT_COL  = vec3(1.15, 1.10, 1.05);

const vec3 FILL_LIGHT_DIR = normalize(vec3(-0.8, 0.2, 0.4));   // Luz de preenchimento suave azulada
const vec3 FILL_LIGHT_COL = vec3(0.35, 0.42, 0.55);

const vec3 RIM_LIGHT_DIR  = normalize(vec3(0.0, 0.6, -1.0));   // Luz de contorno posterior dourada/ciano
const vec3 RIM_LIGHT_COL  = vec3(0.55, 0.70, 0.95);

const vec3 AMBIENT_COL    = vec3(0.22, 0.24, 0.28);

void main()
{
    vec4 texColor = texture(uTexture, TexCoords);

    // Alpha test para cabelos e pestanas
    if (texColor.a < 0.15) {
        discard;
    }

    vec3 N = normalize(Normal);
    vec3 V = normalize(uViewPos - FragPos);

    // 1. Componente Ambiente
    vec3 ambient = AMBIENT_COL * texColor.rgb;

    // 2. Luz Principal (Key Light) - Difusa + Especular Blinn-Phong
    float diffKey = max(dot(N, KEY_LIGHT_DIR), 0.0);
    vec3 diffuseKey = diffKey * KEY_LIGHT_COL * texColor.rgb;

    vec3 H_Key = normalize(KEY_LIGHT_DIR + V);
    float specKey = pow(max(dot(N, H_Key), 0.0), 32.0);
    vec3 specularKey = specKey * vec3(0.25) * KEY_LIGHT_COL;

    // 3. Luz de Preenchimento (Fill Light)
    float diffFill = max(dot(N, FILL_LIGHT_DIR), 0.0);
    vec3 diffuseFill = diffFill * FILL_LIGHT_COL * texColor.rgb;

    // 4. Luz de Contorno (Rim Light - Efeito Fresnel para destacar o personagem do fundo)
    float rimFactor = 1.0 - max(dot(N, V), 0.0);
    rimFactor = pow(rimFactor, 3.0);
    float diffRim = max(dot(N, RIM_LIGHT_DIR), 0.0);
    vec3 rimLight = rimFactor * diffRim * RIM_LIGHT_COL * 1.4;

    // 5. Ajustes específicos por material
    if (uMeshType == 1) {
        // Eyes: brilho especular mais intenso na córnea
        specularKey *= 2.2;
    }

    vec3 finalRGB = ambient + diffuseKey + diffuseFill + rimLight + specularKey;

    // Correção gama ligeira para contraste natural
    finalRGB = pow(finalRGB, vec3(0.95));

    FragColor = vec4(finalRGB, texColor.a);
}
