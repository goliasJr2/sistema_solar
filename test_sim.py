"""
Script de validação automatizada de todos os módulos da Fase 1.
Cria um contexto OpenGL 3.3 Core Profile oculto para verificar compilação de shaders e funcionamento físico.
"""

import sys
from pathlib import Path
import glfw
from OpenGL.GL import *
import glm

from shader import Shader
from camera import Camera
from mesh import SphereMesh, OrbitMesh
from orbits import KeplerianOrbit
from planets import SolarSystem, CELESTIAL_DATA
from starfield import Starfield
from picking import RayPicker
from ui import UIManager
from asteroids import AsteroidBelt
from comet import Comet
from blackhole import BlackHoleSystem
from galaxy import SpiralGalaxy
from satellites import EarthSatellite, LunarRocket
from meteors import MeteorShower
from scale_manager import ScaleManager, ScaleLevel

def test_phase1():
    print("========================================")
    print("A TESTAR MÓDULOS DA FASE 1")
    print("========================================")

    # 1. Teste de Mecânica Kepleriana
    print("\n1. Teste de Mecânica Kepleriana (orbits.py)...")
    orbit_earth = KeplerianOrbit(
        semi_major_axis=60.0,
        eccentricity=0.0167,
        inclination_deg=0.0,
        orbital_period_days=365.256
    )
    pos_t0 = orbit_earth.get_position_at_time(0.0)
    pos_t91 = orbit_earth.get_position_at_time(91.31)
    pos_t182 = orbit_earth.get_position_at_time(182.62)
    print(f"   Posição t=0 dias:   X={pos_t0.x:.3f}, Y={pos_t0.y:.3f}, Z={pos_t0.z:.3f}")
    print(f"   Posição t=91 dias:  X={pos_t91.x:.3f}, Y={pos_t91.y:.3f}, Z={pos_t91.z:.3f}")
    print(f"   Posição t=182 dias: X={pos_t182.x:.3f}, Y={pos_t182.y:.3f}, Z={pos_t182.z:.3f}")
    pts = orbit_earth.generate_orbit_points(120)
    assert len(pts) == 120, "Falha na geração de pontos da órbita!"
    print("   [OK] Mecânica Kepleriana validada com sucesso!")

    # 2. Teste de Câmara e Matrizes
    print("\n2. Teste de Matrizes de Câmara (camera.py)...")
    cam = Camera()
    view = cam.get_view_matrix()
    proj = cam.get_projection_matrix()
    assert isinstance(view, glm.mat4), "View matrix não é mat4!"
    assert isinstance(proj, glm.mat4), "Projection matrix não é mat4!"
    print(f"   Posição da câmara: {cam.position}")
    print(f"   Alvo da câmara: {cam.target}")
    print("   [OK] Matrizes View e Projection validadas!")

    # 3. Teste com Contexto OpenGL 3.3 Core Profile
    print("\n3. Inicialização de contexto OpenGL 3.3 Core para teste de shaders...")
    if not glfw.init():
        raise RuntimeError("Falha ao inicializar GLFW!")

    glfw.window_hint(glfw.VISIBLE, False) # Janela oculta
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(640, 480, "Test Window", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Falha ao criar janela oculta OpenGL 3.3!")

    glfw.make_context_current(window)

    base_dir = Path(__file__).resolve().parent
    shaders_dir = base_dir / "shaders"
    textures_dir = base_dir / "textures"
    models_dir = base_dir / "Models"

    # 4. Compilação dos Shaders
    print("\n4. Teste de compilação dos shaders GLSL...")
    celestial_shader = Shader(shaders_dir / "celestial.vert", shaders_dir / "celestial.frag")
    print("   [OK] celestial.vert e celestial.frag compilados com sucesso!")

    sun_shader = Shader(shaders_dir / "sun.vert", shaders_dir / "sun.frag")
    print("   [OK] sun.vert e sun.frag compilados com sucesso!")

    orbit_shader = Shader(shaders_dir / "orbit.vert", shaders_dir / "orbit.frag")
    print("   [OK] orbit.vert e orbit.frag compilados com sucesso!")

    starfield_shader = Shader(shaders_dir / "starfield.vert", shaders_dir / "starfield.frag")
    print("   [OK] starfield.vert e starfield.frag compilados com sucesso!")

    ui_shader = Shader(shaders_dir / "ui.vert", shaders_dir / "ui.frag")
    print("   [OK] ui.vert e ui.frag compilados com sucesso!")

    # 5. Teste de Geração de Geometrias e Carregamento dos Modelos 3D GLB
    print("\n5. Teste de geração de malhas e carregamento dos modelos 3D GLB...")
    starfield = Starfield(num_stars=500, radius=2000.0)
    solar_sys = SolarSystem(textures_dir=textures_dir, models_dir=models_dir)
    assert len(solar_sys.bodies) == 9, "Devem existir Sol + 8 planetas!"
    
    # Validação do Sistema de Luas (Obrigatório 4)
    earth_moons = solar_sys.bodies["earth"].moons
    jupiter_moons = solar_sys.bodies["jupiter"].moons
    assert len(earth_moons) == 1, "A Terra deve ter 1 lua!"
    assert len(jupiter_moons) == 4, "Júpiter deve ter 4 luas galileanas!"
    print(f"   [OK] Sistema de Luas validado: Terra({len(earth_moons)}), Júpiter({len(jupiter_moons)}), Marte({len(solar_sys.bodies['mars'].moons)})!")

    # 6. Teste de Ray Picking 3D (Obrigatório 7)
    print("\n6. Teste de Ray Picking 3D...")
    ray_origin, ray_dir = RayPicker.get_ray_direction(320, 240, 640, 480, view, proj)
    hit = RayPicker.intersect_sphere(ray_origin, ray_dir, glm.vec3(0.0), 15.0)
    assert hit is not None, "O raio central deve intersetar a esfera solar!"
    print(f"   [OK] Ray Picking validado com sucesso (hit distance: {hit:.2f})!")

    # 7. Teste de Elementos Cósmicos Expandidos (Galáxia, Asteroides, Cometa, Buracos Negros)
    print("\n7. Teste dos elementos cósmicos e Galáxia Espiral...")
    galaxy = SpiralGalaxy(models_dir=models_dir, num_stars=10000)
    belt = AsteroidBelt(models_dir=models_dir, count=30)
    comet = Comet(models_dir=models_dir)
    bh_system = BlackHoleSystem(models_dir=models_dir)
    satellite = EarthSatellite(models_dir=models_dir)
    rocket = LunarRocket(models_dir=models_dir)
    meteors = MeteorShower(models_dir=models_dir, num_meteors=20)
    scale_mgr = ScaleManager(cam)
    print(f"   [OK] Galáxia ({galaxy.num_stars} estrelas), Asteroides({len(belt.asteroids)}), Buracos Negros({len(bh_system.black_holes)}) instanciados!")

    # 8. Teste de Interface UI e Execução de Frame Completo
    print("\n8. Teste de Interface UI e execução de frame cósmico completo...")
    ui_mgr = UIManager(640, 480, ui_shader)
    ui_mgr.set_selected_body(CELESTIAL_DATA["earth"])

    solar_sys.update(delta_time_seconds=0.016, time_scale_days_per_sec=10.0)
    belt.update(10.0, 0.16)
    comet.update(10.0, 0.16)
    bh_system.update(0.016)
    satellite.update(0.016)
    rocket.update(0.016)
    earth_pos = solar_sys.bodies["earth"].current_position
    meteors.update(0.016, earth_pos)
    scale_mgr.update(0.016)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    starfield.draw(starfield_shader, view, proj, current_time=0.1)
    galaxy.draw(starfield_shader, celestial_shader, view, proj, cam.position, 0.1)
    bh_system.draw(celestial_shader, view, proj, cam.position)
    solar_sys.draw(celestial_shader, sun_shader, orbit_shader, view, proj, cam.position, show_orbits=True)
    belt.draw(celestial_shader, view, proj, cam.position, glm.vec3(0.0))
    comet.draw(celestial_shader, view, proj, cam.position, glm.vec3(0.0))
    comet.draw_orbit(orbit_shader, view, proj)
    satellite.draw(celestial_shader, view, proj, cam.position, glm.vec3(0.0), earth_pos)
    meteors.draw(orbit_shader, view, proj)
    ui_mgr.draw(is_paused=False, time_scale=10.0, simulated_days=10.0, fps=60.0, show_orbits=True)
    glfw.swap_buffers(window)
    print("   [OK] Frame cósmico total com Galáxia, Buracos Negros e Sistema Solar renderizado sem erros!")

    glfw.destroy_window(window)
    glfw.terminate()
    print("\n========================================")
    print("TODOS OS TESTES DA FASE 1 PASSARAM A 100%!")
    print("========================================")

if __name__ == "__main__":
    test_phase1()
