#!/usr/bin/env python3
import UnityPy
import os
import struct
from pathlib import Path
from PIL import Image

game_path = Path("/home/yunustas/ULTRAKILL/game")
output_dir = Path("/home/yunustas/ultrakill_extracted")
output_dir.mkdir(exist_ok=True)

total = 0
success = 0
failed = 0

def save_as_obj(data, name, out_path):
    """Mesh'i Wavefront OBJ formatinda kaydet"""
    with open(str(out_path), "w") as f:
        f.write(f"# {name}\n\n")
        if hasattr(data, "vertices") and data.vertices:
            for v in data.vertices:
                f.write(f"v {v.x} {v.y} {v.z}\n")
        if hasattr(data, "normals") and data.normals:
            f.write("\n")
            for n in data.normals:
                f.write(f"vn {n.x} {n.y} {n.z}\n")
        f.write("\n")
        if hasattr(data, "triangles") and data.triangles is not None:
            tris = data.triangles
            for i in range(0, len(tris), 3):
                if i + 2 < len(tris):
                    a, b, c = tris[i]+1, tris[i+1]+1, tris[i+2]+1
                    f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
    return True

def save_as_mtl(data, name, out_path):
    """Material'i Wavefront MTL formatinda kaydet"""
    with open(str(out_path), "w") as f:
        f.write(f"# {name}\n")
        f.write(f"newmtl {name}\n")
        if hasattr(data, "m_SavedProperties"):
            props = data.m_SavedProperties
            if hasattr(props, "m_Colors"):
                for k, v in props.m_Colors.items():
                    if "color" in k.lower() or "Color" in k:
                        f.write(f"Kd {v.r} {v.g} {v.b}\n")
                        f.write(f"d {v.a}\n")
                        break
        f.write("illum 1\n")
    return True

def get_raw_bytes(obj):
    """Objenin ham byte'larini al"""
    try:
        obj.reset()
        return obj.get_raw_data()
    except:
        try:
            return bytes(obj.raw_data)
        except:
            return None

for ext in ["*.assets", "*.resource"]:
    for f in game_path.rglob(ext):
        if f.is_file() and ".backup" not in str(f).lower() and ".resS" not in str(f):
            try:
                env = UnityPy.load(str(f))
                for obj in env.objects:
                    total += 1
                    try:
                        data = obj.read()
                        t = obj.type.name if hasattr(obj.type, "name") else str(obj.type)

                        # TEXTURE -> PNG
                        if t == "Texture2D" and hasattr(data, "image") and data.image:
                            name = data.m_Name or f"tex_{obj.path_id}"
                            out = output_dir / "textures" / f"{name}.png"
                            out.parent.mkdir(exist_ok=True)
                            data.image.save(str(out))
                            success += 1
                            print(f"  [TX] {name}.png")

                        # SPRITE -> PNG
                        elif t == "Sprite" and hasattr(data, "image") and data.image:
                            name = data.m_Name or f"sprite_{obj.path_id}"
                            out = output_dir / "sprites" / f"{name}.png"
                            out.parent.mkdir(exist_ok=True)
                            data.image.save(str(out))
                            success += 1
                            print(f"  [SP] {name}.png")

                        # AUDIO -> WAV
                        elif t == "AudioClip" and hasattr(data, "samples"):
                            for clip_name, clip_data in data.samples.items():
                                out = output_dir / "audio" / f"{clip_name}.wav"
                                out.parent.mkdir(exist_ok=True)
                                with open(str(out), "wb") as fw:
                                    fw.write(clip_data)
                                success += 1
                                print(f"  [AU] {clip_name}.wav")

                        # MESH -> OBJ
                        elif t == "Mesh":
                            name = data.m_Name or f"mesh_{obj.path_id}"
                            out = output_dir / "meshes" / f"{name}.obj"
                            out.parent.mkdir(exist_ok=True)
                            save_as_obj(data, name, out)
                            success += 1
                            print(f"  [MS] {name}.obj")

                        # MATERIAL -> MTL
                        elif t == "Material":
                            name = data.m_Name or f"mat_{obj.path_id}"
                            out = output_dir / "materials" / f"{name}.mtl"
                            out.parent.mkdir(exist_ok=True)
                            save_as_mtl(data, name, out)
                            success += 1
                            print(f"  [MT] {name}.mtl")

                        # SHADER -> .shader (bytecode)
                        elif t == "Shader":
                            name = data.m_Name or f"shader_{obj.path_id}"
                            out = output_dir / "shaders" / f"{name}.shader"
                            out.parent.mkdir(exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                                print(f"  [SH] {name}.shader")
                            else:
                                print(f"  [SH] {name}.shader HATA")

                        # FONT -> TTF/OTF
                        elif t == "Font":
                            name = data.m_Name or f"font_{obj.path_id}"
                            out = output_dir / "fonts" / f"{name}.ttf"
                            out.parent.mkdir(exist_ok=True)
                            if hasattr(data, "m_FontData") and data.m_FontData:
                                with open(str(out), "wb") as fw:
                                    fw.write(bytes(data.m_FontData))
                                success += 1
                                print(f"  [FN] {name}.ttf")
                            else:
                                # Bytecode kaydet
                                raw = get_raw_bytes(obj)
                                if raw:
                                    with open(str(out), "wb") as fw:
                                        fw.write(raw)
                                    success += 1
                                    print(f"  [FN] {name}.ttf (raw)")
                                else:
                                    print(f"  [FN] {name} HATA")

                        # GAMEOBJECT -> .prefab (Unity YAML)
                        elif t == "GameObject":
                            name = data.m_Name or f"go_{obj.path_id}"
                            out = output_dir / "gameobjects" / f"{name}.prefab"
                            out.parent.mkdir(exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                                print(f"  [GO] {name}.prefab")
                            else:
                                print(f"  [GO] {name} HATA")

                        # TEXT ASSET -> .txt
                        elif t == "TextAsset":
                            name = data.m_Name or f"text_{obj.path_id}"
                            out_dir = output_dir / "texts"
                            out_dir.mkdir(exist_ok=True)
                            if hasattr(data, "m_Script"):
                                content = data.m_Script
                                if isinstance(content, bytes):
                                    out = out_dir / f"{name}.bin"
                                    with open(str(out), "wb") as fw:
                                        fw.write(content)
                                else:
                                    out = out_dir / f"{name}.txt"
                                    with open(str(out), "w") as fw:
                                        fw.write(content)
                                success += 1
                                print(f"  [TX] {name}")

                        # VIDEO -> .video (raw bytes)
                        elif t == "VideoClip":
                            name = data.m_Name or f"video_{obj.path_id}"
                            out = output_dir / "videos" / f"{name}.video"
                            out.parent.mkdir(exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                                print(f"  [VD] {name}.video")
                            else:
                                print(f"  [VD] {name} HATA")

                        # ANIMATION -> .anim (raw)
                        elif t == "AnimationClip":
                            name = data.m_Name or f"anim_{obj.path_id}"
                            out = output_dir / "animations" / f"{name}.anim"
                            out.parent.mkdir(exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                                print(f"  [AN] {name}.anim")
                            else:
                                print(f"  [AN] {name} HATA")

                        # MONOSCRIPT -> .dll (yonetilen kod)
                        elif t == "MonoScript":
                            name = data.m_Name or f"script_{obj.path_id}"
                            out = output_dir / "scripts" / f"{name}.dll"
                            out.parent.mkdir(exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                                print(f"  [SC] {name}.dll")
                            else:
                                print(f"  [SC] {name} HATA")

                        # DIGERLERI -> .bin (ham byte)
                        else:
                            name = data.m_Name if hasattr(data, "m_Name") and data.m_Name else f"obj_{obj.path_id}"
                            cat_dir = t.lower().replace("controller", "").replace("snapshot", "")
                            out = output_dir / "other" / cat_dir / f"{name}_{obj.path_id}.bin"
                            out.parent.mkdir(parents=True, exist_ok=True)
                            raw = get_raw_bytes(obj)
                            if raw:
                                with open(str(out), "wb") as fw:
                                    fw.write(raw)
                                success += 1
                            else:
                                failed += 1

                    except:
                        failed += 1
            except Exception as e:
                print(f"  HATA: {f.name} - {e}")

print(f"\n{'='*50}")
print(f"TOPLAM: {total} obje")
print(f"CIKARILAN: {success} dosya")
print(f"HATALI: {failed}")
print(f"CIKTI: {output_dir}")
