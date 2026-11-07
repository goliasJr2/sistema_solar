#version 330 core

out vec4 FragColor;

uniform vec4 uOrbitColor; // Cor da órbita com transparência suave

void main()
{
    FragColor = uOrbitColor;
}
