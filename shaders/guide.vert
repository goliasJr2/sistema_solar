#version 330 core

/*
 * ============================================================================
 * SHADER: guide.vert
 * Descrição: Vertex Shader para o Astronomical Virtual Guide 3D.
 * Suporta deformações esqueléticas e faciais em tempo real (Lip Sync, Piscar de Olhos,
 * Movimentos da Cabeça, Respiração e Gestos dos Braços).
 * ============================================================================
 */

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoords;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoords;

uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat3 uNormalMatrix;

// Uniformes de Animação Corporal e Esquelética
uniform mat4 uHeadRotation;     // Rotação da cabeça e pescoço
uniform vec3 uHeadPivot;        // Ponto de articulação do pescoço (ex: Y ~ 325.0)
uniform float uBreathingScale;   // Simulação de respiração no tórax (Y entre 180 e 320)
uniform mat4 uRightArmRotation; // Gestos do braço direito
uniform vec3 uRightShoulderPivot; // Articulação do ombro direito
uniform mat4 uLeftArmRotation;  // Gestos do braço esquerdo
uniform vec3 uLeftShoulderPivot;  // Articulação do ombro esquerdo

// Uniformes de Animação Facial e Lip Sync
uniform int uMeshType;          // 0=Body, 1=Eyes, 2=Eyelashes, 3=Hair, 4=Tops, 5=Bottoms, 6=Shoes
uniform float uMouthOpen;       // Abertura da boca [0.0 .. 1.0]
uniform float uJawDrop;         // Descida da mandíbula [0.0 .. 1.0]
uniform float uMouthRound;      // Arredondamento labial [0.0 .. 1.0]
uniform float uBlinkFactor;      // Fechamento das pálpebras/pestanas [0.0 = aberto, 1.0 = fechado]
uniform int uIsSitting;         // 1 = postura sentada sobre o topo do planeta, 0 = postura em pé

void main()
{
    vec3 pos = aPos;
    vec3 norm = aNormal;

    // ─── 1. ANIMAÇÃO FACIAL: PISCAR DE OLHOS ──────────────────────────────
    if (uMeshType == 2) {
        // Eyelashes (pestanas): desce verticalmente quando pisca
        pos.y -= uBlinkFactor * 5.2;
        pos.z += uBlinkFactor * 1.5;
    } else if (uMeshType == 1) {
        // Eyes (olhos): pequena escala vertical no ápice do blink
        if (uBlinkFactor > 0.4) {
            float squash = 1.0 - (uBlinkFactor - 0.4) * 0.9;
            pos.y = uHeadPivot.y + (pos.y - uHeadPivot.y) * squash;
        }
    }

    // ─── 2. ANIMAÇÃO FACIAL: LIP SYNC E MANDÍBULA NO BODY ─────────────────
    if (uMeshType == 0) {
        // Altura labial adaptativa calculada a partir do pivô da cabeça (uHeadPivot)
        float mouthCenterY = uHeadPivot.y + 13.0;
        if (pos.y > (mouthCenterY - 10.0) && pos.y < (mouthCenterY + 7.0) && pos.z > 8.0 && abs(pos.x) < 22.0) {
            // Fator de proximidade ao centro labial
            float distToMouth = length(vec3(pos.x * 1.5, pos.y - mouthCenterY, (pos.z - (uHeadPivot.z + 15.0)) * 0.8));
            float mouthWeight = clamp(1.0 - distToMouth / 16.0, 0.0, 1.0);
            mouthWeight = mouthWeight * mouthWeight * (3.0 - 2.0 * mouthWeight); // Smoothstep

            // Descida do lábio inferior e mandíbula
            if (pos.y < mouthCenterY + 1.0) {
                pos.y -= uJawDrop * 3.8 * mouthWeight;
                pos.z += uMouthOpen * 0.8 * mouthWeight;
            } else {
                // Lábio superior sobe suavemente
                pos.y += uMouthOpen * 1.2 * mouthWeight;
            }

            // Arredondamento lateral (vogais O, U)
            if (uMouthRound > 0.05) {
                pos.x *= (1.0 - uMouthRound * 0.22 * mouthWeight);
                pos.z += uMouthRound * 1.8 * mouthWeight;
            }
        }
    }

    // ─── 3. ANIMAÇÃO ESQUELÉTICA: CABEÇA E PESCOÇO ─────────────────────────
    // Aplica-se à cabeça: Hair (3), Eyes (1), Eyelashes (2) e parte superior do corpo acima do pescoço
    bool isHeadPart = (uMeshType == 1 || uMeshType == 2 || uMeshType == 3) ||
                      (uMeshType == 0 && pos.y >= (uHeadPivot.y - 2.0));

    if (isHeadPart) {
        vec3 localHead = pos - uHeadPivot;
        pos = vec3(uHeadRotation * vec4(localHead, 1.0)) + uHeadPivot;
        norm = normalize(mat3(uHeadRotation) * norm);
    }

    // ─── 4. ANIMAÇÃO CORPORAL: GESTOS DOS BRAÇOS ──────────────────────────
    // Braço direito: X > 35.0 e Y entre 180.0 e 325.0
    if (uMeshType == 0 || uMeshType == 4) {
        if (pos.x > 35.0 && pos.y > 170.0 && pos.y < 330.0) {
            float armWeight = clamp((pos.x - 35.0) / 45.0, 0.0, 1.0);
            vec3 localArm = pos - uRightShoulderPivot;
            vec3 rotatedArm = vec3(uRightArmRotation * vec4(localArm, 1.0)) + uRightShoulderPivot;
            pos = mix(pos, rotatedArm, armWeight);
        } else if (pos.x < -35.0 && pos.y > 170.0 && pos.y < 330.0) {
            float armWeight = clamp((-pos.x - 35.0) / 45.0, 0.0, 1.0);
            vec3 localArm = pos - uLeftShoulderPivot;
            vec3 rotatedArm = vec3(uLeftArmRotation * vec4(localArm, 1.0)) + uLeftShoulderPivot;
            pos = mix(pos, rotatedArm, armWeight);
        }
    }

    // ─── 5. SIMULAÇÃO DE RESPIRAÇÃO (TÓRAX E OMBROS) ──────────────────────
    if (uMeshType == 0 || uMeshType == 4) {
        if (pos.y > 185.0 && pos.y < 325.0) {
            float chestWeight = sin(clamp((pos.y - 185.0) / 140.0, 0.0, 1.0) * 3.14159);
            pos.z += uBreathingScale * 2.2 * chestWeight;
            pos.y += uBreathingScale * 0.8 * chestWeight;
            pos.x *= (1.0 + uBreathingScale * 0.012 * chestWeight);
        }
    }

    // ─── 6. POSTURA DE LÓTUS MEDITATIVA (PADMASANA / MEDITAÇÃO CÓSMICA) ───
    if (uIsSitting == 1) {
        if (pos.y < 185.0) {
            float isRight = (pos.x >= 0.0) ? 1.0 : -1.0;

            if (pos.y >= 90.0) {
                // COXAS (Y entre 90 e 185): abrem para os lados e projetam-se à frente
                float f = clamp((180.0 - pos.y) / 90.0, 0.0, 1.0);

                // Afasta os joelhos lateralmente para a posição aberta de lótus
                pos.x += isRight * f * 28.0;
                // Projeta os joelhos para a frente
                pos.z += f * 42.0;
                // Baixa os joelhos em direção ao solo
                pos.y = 180.0 - f * 85.0;
            } else {
                // CANELAS E PÉS (Y < 90): cruzam horizontalmente em lótus
                float f_knee = clamp((90.0 - pos.y) / 90.0, 0.0, 1.0);

                // Posição base do joelho
                float knee_x = pos.x + isRight * 28.0;
                float knee_y = 95.0;
                float knee_z = pos.z + 42.0;

                // Cruzamento da perna para o lado oposto em lótus
                float cross_x = knee_x - isRight * f_knee * 52.0;
                float cross_z = knee_z + f_knee * 14.0 + (isRight > 0.0 ? 6.0 : -6.0);
                float cross_y = knee_y - f_knee * 82.0 + (isRight > 0.0 ? 10.0 : 0.0);

                pos.x = cross_x;
                pos.y = cross_y;
                pos.z = cross_z;
            }
        }

        // Ajusta a altura para que a base da postura sentada em lótus assente em Y = 0
        pos.y -= 75.0;
    }

    // Transformação para World Space e Clip Space
    vec4 worldPos = uModel * vec4(pos, 1.0);
    FragPos = vec3(worldPos);
    Normal = normalize(uNormalMatrix * norm);
    TexCoords = aTexCoords;

    gl_Position = uProjection * uView * worldPos;
}
