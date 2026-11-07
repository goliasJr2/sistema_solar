#version 330 core

/*
 * ============================================================================
 * SHADER SOLAR DINÂMICO AVANÇADO
 * - Emissão de Luz Primária do Sistema Solar
 * - Efeito de Borda (Limb Darkening & Corona Glow)
 * - Plasma Solar Procedural em Tempo Real (Turbulência animada via uTime)
 * - Proeminências e Flares solares na borda
 * ============================================================================
 */

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoords;
in vec3 ObjectPos;

out vec4 FragColor;

uniform sampler2D uTexture;
uniform vec3 uSunColor;   // Cor estelar base
uniform vec3 uViewPos;    // Posição da câmara
uniform float uTime;      // Tempo contínuo em segundos para animação do plasma

// Função pseudo-aleatória de ruído na GPU
float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

// Interpolação suave bilinear de ruído
float noise(vec2 uv) {
    vec2 i = floor(uv);
    vec2 f = fract(uv);
    float a = rand(i);
    float b = rand(i + vec2(1.0, 0.0));
    float c = rand(i + vec2(0.0, 1.0));
    float d = rand(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

void main()
{
    vec4 texColor = texture(uTexture, TexCoords);

    // Vetor para a câmara e normalização
    vec3 viewDir = normalize(uViewPos - FragPos);
    vec3 norm = normalize(Normal);

    // Efeito de bordo e halo estelar (Limb Darkening & Corona Glow)
    float edgeFactor = clamp(dot(norm, viewDir), 0.0, 1.0);
    float glow = pow(1.0 - edgeFactor, 2.8);

    // Animação de plasma procedural em duas camadas de rotação turbulenta
    vec2 pCoords = ObjectPos.xy + TexCoords * 4.0;
    float swirl1 = noise(pCoords * 3.5 + vec2(uTime * 0.15, uTime * 0.10));
    float swirl2 = noise(pCoords * 6.0 - vec2(uTime * 0.25, uTime * 0.20));
    float plasma = pow(mix(swirl1, swirl2, 0.5), 1.8);

    // Flares solares dinâmicos na coroa
    float rimFlare = pow(1.0 - edgeFactor, 3.2);
    vec3 flareColor = vec3(1.0, 0.55, 0.15) * (plasma * rimFlare * 1.6);

    // Cor base emitida (Textura NASA + Plasma procedural + Incandescência)
    vec3 baseEmission = texColor.rgb * uSunColor * 1.25;
    vec3 coronaGlow = vec3(1.0, 0.65, 0.25) * glow * 1.2;
    vec3 plasmaVariation = vec3(1.0, 0.85, 0.4) * (plasma * 0.35);

    vec3 finalColor = baseEmission + coronaGlow + flareColor + plasmaVariation;

    FragColor = vec4(finalColor, 1.0);
}
