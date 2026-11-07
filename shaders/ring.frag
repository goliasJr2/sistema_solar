#version 330 core

/*
 * ============================================================================
 * SHADER DE ANÉIS PLANETÁRIOS COM PROJEÇÃO DE SOMBRA ANALÍTICA (RAY-SPHERE)
 * - Projeta a sombra da esfera central do planeta sobre o disco dos anéis
 * - Descarta fragmentos transparentes (canal alfa)
 * - Suporta penumbra suave realista (smoothstep)
 * ============================================================================
 */

in vec3 FragPos;
in vec2 TexCoords;

out vec4 FragColor;

uniform sampler2D uTexture;
uniform vec3 uSunPos;         // Centro da fonte de luz (Sol em 0, 0, 0)
uniform vec3 uPlanetCenter;   // Centro do planeta em espaço de mundo
uniform float uPlanetRadius;  // Raio da esfera física do planeta
uniform vec3 uLightColor;     // Cor da luz emitida pelo Sol
uniform vec3 uAmbientColor;   // Luz ambiente cósmica

void main()
{
    vec4 texColor = texture(uTexture, TexCoords);
    if (texColor.a < 0.05)
        discard;

    // Vetor do Sol para o fragmento do anel
    vec3 distanceVec = FragPos - uSunPos;
    vec3 dir = normalize(distanceVec);

    // Vetor do centro do planeta para a fonte de luz (Sol)
    vec3 L = uSunPos - uPlanetCenter;

    // Resolução da interseção raio-esfera para sombra projetada
    float b = 2.0 * dot(dir, L);
    float c = dot(L, L) - (uPlanetRadius * uPlanetRadius);
    float discriminant = (b * b) - (4.0 * c);

    float distPlanet = length(L);
    float distFrag = length(distanceVec);

    float shadow = 0.0;
    // Se o raio interseta a esfera do planeta e o fragmento está atrás do planeta
    if (discriminant >= 0.0 && distFrag > distPlanet) {
        float interDistance = sqrt(discriminant);
        float penetration = clamp(interDistance / (2.0 * uPlanetRadius), 0.0, 1.0);
        float shadowFactor = smoothstep(0.0, 1.0, penetration);
        shadow = 0.85 * shadowFactor;
    }

    vec3 ambient = uAmbientColor * texColor.rgb;
    vec3 diffuse = uLightColor * texColor.rgb * (1.0 - shadow);

    vec3 finalColor = ambient + diffuse;
    FragColor = vec4(finalColor, texColor.a);
}
