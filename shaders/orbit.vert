#version 330 core

/*
 * Shader para renderização da trajetória orbital elíptica kepleriana.
 */

layout (location = 0) in vec3 aPos;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

void main()
{
    gl_Position = uProjection * uView * uModel * vec4(aPos, 1.0);
}
