#version 330 core

/*
 * Fragment Shader para renderizar estrelas circulares suaves em vez de quadrados secos.
 */

in vec3 StarColor;
in float StarAlpha;

out vec4 FragColor;

void main()
{
    // gl_PointCoord fornece coordenadas [0, 1] dentro de cada ponto rasterizado
    vec2 coord = gl_PointCoord - vec2(0.5);
    float distSq = dot(coord, coord);

    // Se estiver fora do círculo de raio 0.5, descarta o fragmento
    if (distSq > 0.25) {
        discard;
    }

    // Gradiente suave do centro para a borda
    float alpha = smoothstep(0.25, 0.0, distSq) * StarAlpha;
    FragColor = vec4(StarColor, alpha);
}
