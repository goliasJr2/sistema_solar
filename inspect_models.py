"""
===============================================================================
Script: inspect_models.py (FASE 0 OBRIGATÓRIA)
Descrição: Analisa minuciosamente todos os modelos 3D (.glb, .gltf, .obj) na pasta Models/.
Inspeciona e reporta:
  - Nome do ficheiro e dimensão em disco
  - Número total de geometrias / nós na cena
  - Número total de vértices e triângulos (faces)
  - Limites espaciais (Bounding Box: min_bound, max_bound e dimensões extents)
  - Presença de coordenadas de textura UV (uv_coords)
  - Presença e propriedades de materiais e texturas embutidas (BaseColor / Diffuse)
  - Presença de dados de animação embutidos no ficheiro glTF
  - Diagnóstico e recomendações para o motor gráfico (normalização, decimação, etc.)
===============================================================================
"""

from pathlib import Path
import json
import trimesh
import numpy as np

def inspect_all_models(models_dir: Path):
    print("=" * 85)
    print("FASE 0: INSPEÇÃO DETALHADA DOS MODELOS 3D EM MODELS/")
    print("=" * 85)

    if not models_dir.exists():
        print(f"[ERRO] Diretório de modelos não encontrado: {models_dir}")
        return

    model_files = sorted(list(models_dir.glob("*.glb")) + list(models_dir.glob("*.gltf")) + list(models_dir.glob("*.obj")))
    print(f"Total de ficheiros 3D encontrados para inspeção: {len(model_files)}\n")

    report_summary = []

    for file_path in model_files:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print("-" * 85)
        print(f"FICHEIRO: {file_path.name} ({size_mb:.2f} MB)")

        try:
            loaded = trimesh.load(file_path, process=False)
            is_scene = isinstance(loaded, trimesh.Scene)

            geometries = {}
            if is_scene:
                geometries = loaded.geometry
            elif isinstance(loaded, trimesh.Trimesh):
                geometries = {"single_mesh": loaded}

            total_vertices = 0
            total_faces = 0
            has_uvs = False
            has_textures = False
            texture_info = []

            min_box = np.array([float("inf")] * 3)
            max_box = np.array([float("-inf")] * 3)

            for g_name, geom in geometries.items():
                if isinstance(geom, trimesh.Trimesh):
                    n_v = len(geom.vertices)
                    n_f = len(geom.faces)
                    total_vertices += n_v
                    total_faces += n_f

                    if geom.bounds is not None and not np.isnan(geom.bounds).any():
                        min_box = np.minimum(min_box, geom.bounds[0])
                        max_box = np.maximum(max_box, geom.bounds[1])

                    if hasattr(geom.visual, "uv") and geom.visual.uv is not None and len(geom.visual.uv) > 0:
                        has_uvs = True

                    mat = getattr(geom.visual, "material", None)
                    if mat is not None:
                        img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
                        if img is not None:
                            has_textures = True
                            img_size = getattr(img, "size", "N/A")
                            img_mode = getattr(img, "mode", "N/A")
                            texture_info.append(f"{g_name} ({img_size}, {img_mode})")

            # Verificação de animações no ficheiro glTF através de metadados brutos se disponíveis
            has_animations = False
            num_animations = 0
            if hasattr(loaded, "metadata") and isinstance(loaded.metadata, dict):
                gltf_header = loaded.metadata.get("header", {})
                animations = loaded.metadata.get("animations") or gltf_header.get("animations")
                if animations:
                    has_animations = True
                    num_animations = len(animations)

            extents = (max_box - min_box) if total_vertices > 0 else np.zeros(3)

            print(f"  Tipo Estrutural: {'Cena Multi-Objeto (' + str(len(geometries)) + ' nós)' if is_scene else 'Malha Única'}")
            print(f"  Vértices Totais: {total_vertices:,} | Triângulos/Faces: {total_faces:,}")
            print(f"  Bounding Box Min: {np.round(min_box, 3)}")
            print(f"  Bounding Box Max: {np.round(max_box, 3)}")
            print(f"  Extents (LxAxP): {np.round(extents, 3)} -> Diâmetro Aprox: {np.max(extents):.2f}")
            print(f"  Coordenadas UV: {'SIM' if has_uvs else 'NÃO (necessita projeção procedural)'}")
            print(f"  Texturas Embutidas: {'SIM: ' + ', '.join(texture_info[:3]) if has_textures else 'NÃO'}")
            print(f"  Animações Embutidas: {'SIM (' + str(num_animations) + ' faixas)' if has_animations else 'NÃO (Animação controlada 100% por matrizes em código)'}")

            # Diagnóstico
            recommendation = "OK"
            if total_faces > 200000:
                recommendation = f"AVISO: Modelo denso ({total_faces:,} tris) - aplicar decimação ou LOD"
            elif total_faces == 0:
                recommendation = "AVISO: Sem faces poligonais"

            print(f"  Recomendação Técnica: {recommendation}")

            report_summary.append({
                "file": file_path.name,
                "size_mb": round(size_mb, 2),
                "is_scene": is_scene,
                "objects": len(geometries),
                "faces": total_faces,
                "has_textures": has_textures,
                "max_extent": float(np.max(extents)) if total_vertices > 0 else 1.0,
            })

        except Exception as e:
            print(f"  [ERRO AO ANALISAR]: {e}")

    print("\n" + "=" * 85)
    print("RESUMO DA INSPEÇÃO E CLASSIFICAÇÃO DOS RECURSOS")
    print("=" * 85)
    print(f"{'Ficheiro':<40} {'Faces':<12} {'MB':<8} {'Textura':<10} {'Classificação':<20}")
    print("-" * 85)

    for item in report_summary:
        fname = item["file"].lower()
        if any(p in fname for p in ["sun", "mercurio", "venus", "tierra", "marte", "jupiter", "saturno", "neptuno", "pluton", "lua"]):
            cat = "Sistema Solar"
        elif "black_hole" in fname:
            cat = "Buraco Negro"
        elif "asteroid" in fname:
            cat = "Asteroide / Campo"
        elif "comet" in fname or "3iatlas" in fname:
            cat = "Cometa"
        elif "corot" in fname:
            cat = "Exoplaneta"
        elif "satellite" in fname or "rocket" in fname:
            cat = "Artificial / Satélite"
        else:
            cat = "Especial / Extra"

        print(f"{item['file'][:39]:<40} {item['faces']:<12,d} {item['size_mb']:<8.2f} {'SIM' if item['has_textures'] else 'NÃO':<10} {cat:<20}")

    print("=" * 85)
    print("Inspeção da Fase 0 concluída com sucesso!")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    inspect_all_models(base_dir / "Models")
