#version 330 core

/*
 * ============================================================================
 * CONCEITOS DE COMPUTAÇÃO GRÁFICA:
 * - Pipeline Gráfico: Etapa de Rasterização e Fragment Shader.
 * - Iluminação Blinn-Phong:
 *     - Luz Ambiente: iluminação cósmica indireta no lado noturno.
 *     - Luz Difusa: reflexão lambertiana (N . L) onde a luz solar atinge a superfície.
 *     - Luz Especular: realce com o vetor a meio caminho (Halfway Vector: H = normalize(L + V)).
 * - Texturas:
 *     - Amostragem (texture sampling) com interpolação bilinear/trilinear e mipmapping.
 *     - Tratamento dinâmico de terminador dia/noite.
 * ============================================================================
 */

in vec3 FragPos;   // Posição no Espaço de Mundo
in vec3 Normal;    // Vetor normal normalizado
in vec2 TexCoords; // Coordenadas UV de textura

out vec4 FragColor;

// Mapeamento de Textura
uniform sampler2D uTexture;

// Parâmetros de Iluminação Solar Dinâmica
uniform vec3 uLightPos;     // Posição da fonte pontual solar no mundo (centro do Sol)
uniform vec3 uLightColor;   // Cor emitida pela luz solar (geralmente branco puro ou quente)
uniform vec3 uViewPos;      // Posição da câmara no mundo

// Propriedades do Material
uniform vec3  uAmbientColor;   // Luz ambiente mínima no lado escuro do planeta
uniform float uShininess;      // Expoente especular de Blinn-Phong (16.0 a 64.0)
uniform float uSpecularStrength; // Intensidade do brilho especular (ex: oceanos da Terra)

void main()
{
    // 1. Obter a cor da textura do planeta
    vec4 texColor = texture(uTexture, TexCoords);

    // 2. Normalização dos vetores geométricos no espaço de mundo
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(uLightPos - FragPos);
    vec3 viewDir = normalize(uViewPos - FragPos);

    // 3. Atenuação quadrática da luz solar com a distância
    float distance = length(uLightPos - FragPos);
    // Atenuação suave adaptada à escala planetária
    float attenuation = 1.0 / (1.0 + 0.0001 * distance + 0.000002 * (distance * distance));

    // 4. Componente Ambiente (iluminação cósmica ténue para o lado noturno não ficar totalmente preto)
    vec3 ambient = uAmbientColor * texColor.rgb;

    // 5. Componente Difusa (Lambertian: cos(teta) = N . L)
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor * texColor.rgb * attenuation;

    // 6. Componente Especular (Blinn-Phong com vetor H a meio caminho)
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), uShininess);
    vec3 specular = uSpecularStrength * spec * uLightColor * attenuation;

    // 7. Composição final da cor (Lado Dia + Lado Noite dinâmico)
    vec3 result = ambient + diffuse + specular;

    // Os corpos planetários são esferas celestes maciças e 100% opacas
    FragColor = vec4(result, 1.0);
}
