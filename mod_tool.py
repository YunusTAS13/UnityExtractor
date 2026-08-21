#!/usr/bin/env python3
"""
Game Modder v3.0 - HER ŞEY'i Çıkar, Değiştir, Geri Paketle
Derlenmiş Unity oyunlarının TAMAMINI modla.

Kullanim: python3 mod_tool.py
"""

import os
import sys
import json
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import UnityPy
    from UnityPy.enums import ClassIDType
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "UnityPy"])
    import UnityPy
    from UnityPy.enums import ClassIDType

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "Pillow"])
    from PIL import Image


class C:
    B = "\033[1m"
    D = "\033[2m"
    R = "\033[0m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YLW = "\033[93m"
    BLU = "\033[94m"
    CYN = "\033[96m"
    WHT = "\033[97m"

    @staticmethod
    def ok(m): print(f"  {C.GRN}✓{C.R} {m}")
    @staticmethod
    def err(m): print(f"  {C.RED}✗{C.R} {m}")
    @staticmethod
    def info(m): print(f"  {C.CYN}ℹ{C.R} {m}")
    @staticmethod
    def warn(m): print(f"  {C.YLW}⚠{C.R} {m}")
    @staticmethod
    def heading(m): print(f"\n{C.B}{C.CYN}{m}{C.R}")
    @staticmethod
    def dim(m): print(f"  {C.D}{m}{C.R}")


# ============================================================
# TÜM UNITY TIPLERI
# ============================================================
ALL_TYPES = {
    # Texture
    "Texture2D": "texture", "Sprite": "texture", "SpriteAtlas": "texture",
    # Audio
    "AudioClip": "audio", "AudioMixer": "audio", "AudioMixerGroup": "audio",
    "AudioMixerSnapshot": "audio",
    # Mesh/Model
    "Mesh": "mesh", "MeshFilter": "mesh", "MeshRenderer": "mesh",
    "SkinnedMeshRenderer": "mesh",
    # Material/Shader
    "Material": "material", "Shader": "material", "ShaderVariantCollection": "material",
    # Animation
    "AnimationClip": "animation", "AnimatorController": "animation",
    "AnimatorOverrideController": "animation", "RuntimeAnimatorController": "animation",
    # GameObject
    "GameObject": "gameobject", "Transform": "gameobject",
    "RectTransform": "gameobject", "MonoBehaviour": "gameobject",
    "ScriptableObject": "gameobject",
    # Light/Camera
    "Light": "render", "Camera": "render", "ReflectionProbe": "render",
    # Physics
    "Rigidbody": "physics", "BoxCollider": "physics", "SphereCollider": "physics",
    "CapsuleCollider": "physics", "MeshCollider": "physics",
    "CharacterController": "physics", "WheelCollider": "physics",
    # Terrain
    "TerrainData": "terrain", "Terrain": "terrain",
    # UI
    "Canvas": "ui", "CanvasRenderer": "ui", "Text": "ui",
    "Image": "ui", "Button": "ui", "Slider": "ui",
    # Font
    "Font": "font", "TextAsset": "text",
    # Video
    "VideoClip": "video",
    # Other
    "PlayerSettings": "settings", "QualitySettings": "settings",
    "PhysicsManager": "settings", "TagManager": "settings",
    "InputManager": "settings", "EditorSettings": "settings",
    "GraphicsSettings": "settings", "TimeManager": "settings",
    "AudioManager": "settings", "EditorBuildSettings": "settings",
    "ProjectSettings": "settings", "NavMeshSettings": "settings",
    "PreloadData": "internal", "AssetBundle": "internal",
    "AssetBundleManifest": "internal",
}

TYPE_CATEGORIES = {
    "texture": "Texture/Resimler",
    "audio": "Audio/Sesler",
    "mesh": "Mesh/Modeller",
    "material": "Material/Gorunum",
    "animation": "Animasyon",
    "gameobject": "GameObject/Varliklar",
    "render": "Render/Kamera/Işık",
    "physics": "Physics/Fizik",
    "terrain": "Terrain/Arazi",
    "ui": "UI/Arayuz",
    "font": "Font/Yazi",
    "text": "Text/Dosyalar",
    "video": "Video",
    "settings": "Settings/Ayarlar",
    "internal": "Internal/Sistem",
}


# ============================================================
# STEAM BULUCU
# ============================================================
class SteamFinder:
    @staticmethod
    def find_steam() -> Optional[Path]:
        for p in [
            Path.home() / ".steam" / "steam" / "steamapps" / "common",
            Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common",
        ]:
            if p.exists():
                return p
        return None

    @staticmethod
    def find_game(name: str) -> Optional[Path]:
        steam = SteamFinder.find_steam()
        if not steam:
            return None
        for f in steam.iterdir():
            if f.is_dir() and name.lower() in f.name.lower():
                return f
        return None

    @staticmethod
    def list_games() -> List[Path]:
        steam = SteamFinder.find_steam()
        if not steam:
            return []
        return sorted([f for f in steam.iterdir() if f.is_dir()])


# ============================================================
# ANA MOTOR
# ============================================================
class GameModder:
    def __init__(self, game_path: Path):
        self.game_path = game_path
        self.envs: Dict[str, Any] = {}
        self.all_objects: List[dict] = []
        self._loaded = False

    def scan(self) -> dict:
        self.all_objects.clear()
        self.envs.clear()

        asset_files = []
        for ext in ["*.assets", "*.resource", "*.resS", "*.bundle"]:
            for f in self.game_path.rglob(ext):
                if f.is_file() and ".backup" not in str(f).lower():
                    asset_files.append(f)

        for af in asset_files:
            self._load_file(af)

        self._loaded = True
        return self.get_stats()

    def _load_file(self, filepath: Path):
        try:
            env = UnityPy.load(str(filepath))
            self.envs[str(filepath)] = env

            for obj in env.objects:
                try:
                    type_name = obj.type.name if hasattr(obj.type, 'name') else str(obj.type)
                    container = obj.container if obj.container else ""

                    name = ""
                    try:
                        data = obj.read()
                        if hasattr(data, 'm_Name') and data.m_Name:
                            name = data.m_Name
                        elif hasattr(data, 'name') and data.name:
                            name = data.name
                        elif hasattr(data, 'm_PathID'):
                            name = f"id_{obj.path_id}"
                    except:
                        pass

                    category = ALL_TYPES.get(type_name, "other")

                    self.all_objects.append({
                        "file": str(filepath),
                        "file_name": filepath.name,
                        "path_id": obj.path_id,
                        "type": type_name,
                        "category": category,
                        "name": name,
                        "container": str(container),
                        "size": obj.byte_size if hasattr(obj, 'byte_size') else 0,
                    })
                except:
                    pass
        except:
            pass

    def get_stats(self) -> dict:
        stats = {"total": len(self.all_objects)}
        by_category = {}
        by_type = {}
        for o in self.all_objects:
            cat = o["category"]
            typ = o["type"]
            by_category[cat] = by_category.get(cat, 0) + 1
            by_type[typ] = by_type.get(typ, 0) + 1
        stats["by_category"] = by_category
        stats["by_type"] = by_type
        return stats

    def get_by_category(self, category: str) -> List[dict]:
        return [o for o in self.all_objects if o["category"] == category]

    def get_by_type(self, type_name: str) -> List[dict]:
        return [o for o in self.all_objects if o["type"] == type_name]

    def search(self, query: str) -> List[dict]:
        q = query.lower()
        return [o for o in self.all_objects if q in o["name"].lower() or q in o["type"].lower() or q in o["container"].lower()]

    def _get_env(self, file_path: str):
        return self.envs.get(file_path)

    def _get_obj(self, file_path: str, path_id: int):
        env = self._get_env(file_path)
        if env:
            for obj in env.objects:
                if obj.path_id == path_id:
                    return obj
        return None

    def extract_object(self, obj_info: dict, output_dir: str) -> Optional[str]:
        obj = self._get_obj(obj_info["file"], obj_info["path_id"])
        if not obj:
            return None

        try:
            data = obj.read()
            typ = obj_info["type"]

            # TEXTURE
            if typ == "Texture2D" and hasattr(data, 'image') and data.image:
                name = data.m_Name or f"texture_{obj_info['path_id']}"
                out = os.path.join(output_dir, "textures", f"{name}.png")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                data.image.save(out)
                return out

            # SPRITE
            if typ == "Sprite" and hasattr(data, 'image') and data.image:
                name = data.m_Name or f"sprite_{obj_info['path_id']}"
                out = os.path.join(output_dir, "sprites", f"{name}.png")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                data.image.save(out)
                return out

            # AUDIO
            if typ == "AudioClip" and hasattr(data, 'samples'):
                results = []
                for clip_name, clip_data in data.samples.items():
                    out = os.path.join(output_dir, "audio", f"{clip_name}.wav")
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    with open(out, "wb") as f:
                        f.write(clip_data)
                    results.append(out)
                return results[0] if results else None

            # MESH
            if typ == "Mesh":
                name = data.m_Name or f"mesh_{obj_info['path_id']}"
                mesh_data = {"name": name, "type": "Mesh"}
                try:
                    if hasattr(data, 'vertices') and data.vertices:
                        mesh_data["vertices"] = [[v.x, v.y, v.z] for v in data.vertices]
                    if hasattr(data, 'triangles') and data.triangles is not None:
                        mesh_data["triangles"] = list(data.triangles)
                    if hasattr(data, 'normals') and data.normals:
                        mesh_data["normals"] = [[n.x, n.y, n.z] for n in data.normals]
                    if hasattr(data, 'uv') and data.uv:
                        mesh_data["uv"] = [[u.x, u.y] for u in data.uv]
                    if hasattr(data, 'colors') and data.colors:
                        mesh_data["colors"] = [[c.r, c.g, c.b, c.a] for c in data.colors]
                except:
                    pass
                out = os.path.join(output_dir, "meshes", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(mesh_data, f, indent=2)
                return out

            # MATERIAL
            if typ == "Material":
                name = data.m_Name or f"material_{obj_info['path_id']}"
                mat_data = {"name": name, "type": "Material"}
                try:
                    if hasattr(data, 'm_SavedProperties'):
                        props = data.m_SavedProperties
                        if hasattr(props, 'm_Floats'):
                            mat_data["floats"] = dict(props.m_Floats)
                        if hasattr(props, 'm_Colors'):
                            mat_data["colors"] = {k: {"r": v.r, "g": v.g, "b": v.b, "a": v.a} for k, v in props.m_Colors}
                        if hasattr(props, 'm_TexEnvs'):
                            mat_data["textures"] = {}
                            for k, v in props.m_TexEnvos if hasattr(props, 'm_TexEnvos') else []:
                                mat_data["textures"][k] = str(v)
                except:
                    pass
                out = os.path.join(output_dir, "materials", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(mat_data, f, indent=2)
                return out

            # SHADER
            if typ == "Shader":
                name = data.m_Name or f"shader_{obj_info['path_id']}"
                out = os.path.join(output_dir, "shaders", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                shader_data = {"name": name, "type": "Shader"}
                try:
                    if hasattr(data, 'm_ParsedForm'):
                        parsed = data.m_ParsedForm
                        if hasattr(parsed, 'm_Name'):
                            shader_data["parsed_name"] = parsed.m_Name
                        if hasattr(parsed, 'm_SubPrograms'):
                            shader_data["sub_programs_count"] = len(parsed.m_SubPrograms)
                except:
                    pass
                with open(out, "w") as f:
                    json.dump(shader_data, f, indent=2)
                return out

            # ANIMATION CLIP
            if typ == "AnimationClip":
                name = data.m_Name or f"anim_{obj_info['path_id']}"
                anim_data = {"name": name, "type": "AnimationClip"}
                try:
                    if hasattr(data, 'm_ClipBindingConstant'):
                        bindings = data.m_ClipBindingConstant
                        if hasattr(bindings, 'genericBindings'):
                            anim_data["bindings_count"] = len(bindings.genericBindings)
                except:
                    pass
                out = os.path.join(output_dir, "animations", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(anim_data, f, indent=2)
                return out

            # FONT
            if typ == "Font":
                name = data.m_Name or f"font_{obj_info['path_id']}"
                font_data = {"name": name, "type": "Font"}
                try:
                    if hasattr(data, 'm_FontData') and data.m_FontData:
                        font_data["has_data"] = True
                        font_data["data_size"] = len(data.m_FontData)
                except:
                    pass
                out = os.path.join(output_dir, "fonts", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(font_data, f, indent=2)
                return out

            # TEXT ASSET
            if typ == "TextAsset":
                name = data.m_Name or f"text_{obj_info['path_id']}"
                try:
                    text_content = data.m_Script if hasattr(data, 'm_Script') else ""
                    if isinstance(text_content, bytes):
                        out = os.path.join(output_dir, "texts", f"{name}.bin")
                    else:
                        out = os.path.join(output_dir, "texts", f"{name}.txt")
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    mode = "wb" if isinstance(text_content, bytes) else "w"
                    with open(out, mode) as f:
                        f.write(text_content)
                    return out
                except:
                    pass

            # GAMEOBJECT
            if typ == "GameObject":
                name = data.m_Name or f"gameobject_{obj_info['path_id']}"
                go_data = {"name": name, "type": "GameObject"}
                try:
                    if hasattr(data, 'm_TagString'):
                        go_data["tag"] = data.m_TagString
                    if hasattr(data, 'm_Layer'):
                        go_data["layer"] = data.m_Layer
                    if hasattr(data, 'm_IsActive'):
                        go_data["active"] = bool(data.m_IsActive)
                    if hasattr(data, 'm_Component'):
                        go_data["components"] = len(data.m_Component)
                except:
                    pass
                out = os.path.join(output_dir, "gameobjects", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(go_data, f, indent=2)
                return out

            # MONOBEHAVIOUR
            if typ == "MonoBehaviour":
                name = data.m_Name or f"mono_{obj_info['path_id']}"
                mono_data = {"name": name, "type": "MonoBehaviour"}
                out = os.path.join(output_dir, "scripts", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(mono_data, f, indent=2)
                return out

            # TERRAIN DATA
            if typ == "TerrainData":
                name = data.m_Name or f"terrain_{obj_info['path_id']}"
                terrain_data = {"name": name, "type": "TerrainData"}
                try:
                    if hasattr(data, 'm_Heightmap'):
                        terrain_data["has_heightmap"] = True
                        hm = data.m_Heightmap
                        if hasattr(hm, 'm_Heights'):
                            terrain_data["heights_size"] = len(hm.m_Heights)
                except:
                    pass
                out = os.path.join(output_dir, "terrain", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(terrain_data, f, indent=2)
                return out

            # VIDEO CLIP
            if typ == "VideoClip":
                name = data.m_Name or f"video_{obj_info['path_id']}"
                video_data = {"name": name, "type": "VideoClip"}
                try:
                    if hasattr(data, 'm_OriginalPath'):
                        video_data["original_path"] = data.m_OriginalPath
                except:
                    pass
                out = os.path.join(output_dir, "videos", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(video_data, f, indent=2)
                return out

            # SETTINGS
            if typ.endswith("Settings") or typ in ("PlayerSettings", "QualitySettings", "PhysicsManager", "TagManager", "InputManager", "EditorSettings", "GraphicsSettings", "TimeManager", "AudioManager", "EditorBuildSettings", "NavMeshSettings"):
                name = typ
                settings_data = {"name": name, "type": typ}
                out = os.path.join(output_dir, "settings", f"{name}.json")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as f:
                    json.dump(settings_data, f, indent=2)
                return out

            # DIGERLERI
            name = obj_info["name"] or f"obj_{obj_info['path_id']}"
            other_data = {"name": name, "type": typ, "path_id": obj_info["path_id"]}
            category_dir = obj_info["category"] if obj_info["category"] != "other" else "other"
            out = os.path.join(output_dir, category_dir, f"{name}_{obj_info['path_id']}.json")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                json.dump(other_data, f, indent=2)
            return out

        except:
            return None

    def extract_all(self, output_dir: str, categories: List[str] = None) -> dict:
        results = {"success": 0, "failed": 0, "skipped": 0, "files": []}

        for obj_info in self.all_objects:
            if categories and obj_info["category"] not in categories:
                results["skipped"] += 1
                continue

            out = self.extract_object(obj_info, output_dir)
            if out:
                results["success"] += 1
                results["files"].append(out)
            else:
                results["failed"] += 1

        return results

    def extract_category(self, output_dir: str, category: str) -> dict:
        return self.extract_all(output_dir, [category])

    def replace_texture(self, file_path: str, path_id: int, new_image: str) -> bool:
        obj = self._get_obj(file_path, path_id)
        if not obj:
            return False
        data = obj.read()
        if hasattr(data, 'image'):
            data.image = Image.open(new_image)
            data.save()
            return True
        return False

    def replace_audio(self, file_path: str, path_id: int, new_audio: str) -> bool:
        obj = self._get_obj(file_path, path_id)
        if not obj:
            return False
        data = obj.read()
        if hasattr(data, 'samples'):
            with open(new_audio, "rb") as f:
                audio_data = f.read()
            clip_name = list(data.samples.keys())[0] if data.samples else "clip"
            data.samples = {clip_name: audio_data}
            data.save()
            return True
        return False

    def save_all(self):
        for file_path, env in self.envs.items():
            for obj in env.objects:
                try:
                    data = obj.read()
                    if hasattr(data, 'save'):
                        data.save()
                except:
                    pass

    def backup(self, output_dir: str) -> str:
        backup_path = Path(output_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        for file_path in self.envs:
            src = Path(file_path)
            dst = backup_path / src.name
            shutil.copy2(str(src), str(dst))

        return str(backup_path)

    def summary(self) -> str:
        stats = self.get_stats()
        lines = [f"\n  {C.B}TOPLEM: {stats['total']} OBJE{C.R}\n"]

        for cat, label in TYPE_CATEGORIES.items():
            count = stats["by_category"].get(cat, 0)
            if count > 0:
                lines.append(f"  {C.GRN}{label:<25}{C.R} {C.B}{count}{C.R}")

        return "\n".join(lines)


# ============================================================
# INTERAKTIF MENU
# ============================================================
def banner():
    print(f"""
{C.B}{C.CYN}╔════════════════════════════════════════════════════════════╗
║              GAME MODDER v3.0                             ║
║        HER SEYI Cikar, Degistir, Geri Paketle            ║
╚════════════════════════════════════════════════════════════╝{C.R}
""")


def main_menu():
    print(f"""
{C.B}  ANA MENU{C.R}
  {C.CYN}1{C.R} - Steam oyunu otomatik bul
  {C.CYN}2{C.R} - Oyun klasoru belirt (yol yaz)
  {C.CYN}3{C.R} - Cikis
""")


def game_menu(name: str, stats: dict):
    total = stats.get("total", 0)
    print(f"""
{C.B}  {name} - MODIFICATION PANELI{C.R}  ({C.GRN}{total} obje{C.R})
  {C.GRN}1{C.R}  - Tara ve ozet goster
  {C.GRN}2{C.R}  - HER SEYI CIKAR (tum kategoriler)
  {C.GRN}3{C.R}  - Sadece Texture'lari cikar
  {C.GRN}4{C.R}  - Sadece Ses dosyalarini cikar
  {C.GRN}5{C.R}  - Sadece Modelleri (Mesh) cikar
  {C.GRN}6{C.R}  - Sadece Material'lari cikar
  {C.GRN}7{C.R}  - Sadece Animasyonlari cikar
  {C.GRN}8{C.R}  - Sadece GameObject'leri cikar
  {C.GRN}9{C.R}  - Sadece Font/Text dosyalari cikar
  {C.GRN}10{C.R} - Sadece Settings/Ayarlar cikar
  {C.GRN}11{C.R} - Tumunu ayrintili listele
  {C.GRN}12{C.R} - Isim ile ara
  {C.GRN}13{C.R} - Texture degistir
  {C.GRN}14{C.R} - Ses degistir
  {C.GRN}15{C.R} - Degisiklikleri kaydet (geri paketle)
  {C.GRN}16{C.R} - Backup al
  {C.GRN}0{C.R}  - Ana menuye don
""")


def choose_steam_game():
    games = SteamFinder.list_games()
    if not games:
        C.warn("Steam bulunamadi")
        return None

    print(f"\n{C.B}  Steam Oyunlari:{C.R}")
    for i, g in enumerate(games, 1):
        print(f"  {C.CYN}{i:>3}{C.R} - {g.name}")
    print(f"  {C.CYN}  0{C.R} - Geri don")

    ch = input(f"\n  Secim (1-{len(games)}): ").strip()
    if ch == "0" or not ch:
        return None
    try:
        idx = int(ch) - 1
        if 0 <= idx < len(games):
            return games[idx]
    except:
        pass
    C.err("Gecersiz")
    return None


def choose_category(modder: GameModder, category: str, label: str):
    items = modder.get_by_category(category)
    if not items:
        C.warn(f"{label} bulunamadi")
        return

    print(f"\n{C.B}  {label} ({len(items)} adet):{C.R}")

    by_type = {}
    for item in items:
        t = item["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(item)

    idx = 1
    type_indices = {}
    for t, items_list in by_type.items():
        print(f"\n  {C.YLW}{t}{C.R} ({len(items_list)}):")
        for item in items_list[:10]:
            name = item["name"] if item["name"] else f"path_id={item['path_id']}"
            print(f"    {C.CYN}{idx:>4}{C.R} - {name}")
            type_indices[idx] = item
            idx += 1
        if len(items_list) > 10:
            print(f"    {C.D}... ve {len(items_list)-10} tane daha{C.R}")

    print(f"\n  {C.CYN}a{C.R} - HEPSINI CIKAR")
    print(f"  {C.CYN}0{C.R} - Geri don")

    ch = input("\n  Secim: ").strip()
    if ch == "0" or not ch:
        return

    output = input("  Cikti klasoru: ").strip() or f"./extracted_{category}"

    if ch.lower() == "a":
        C.info(f"Tum {label} cikariliyor...")
        result = modder.extract_category(output, category)
        C.ok(f"{result['success']} dosya cikarildi: {output}")
    else:
        try:
            idx = int(ch)
            if idx in type_indices:
                item = type_indices[idx]
                out = modder.extract_object(item, output)
                if out:
                    C.ok(f"Cikarildi: {out}")
                else:
                    C.err("Cikarilamadi")
        except:
            C.err("Gecersiz secim")


def search_assets(modder: GameModder):
    query = input("  Arama terimi: ").strip()
    if not query:
        return

    results = modder.search(query)
    if not results:
        C.warn("Sonuc bulunamadi")
        return

    print(f"\n{C.B}  '{query}' icin {len(results)} sonuc:{C.R}")
    for i, r in enumerate(results[:50], 1):
        name = r["name"] if r["name"] else f"path_id={r['path_id']}"
        print(f"  {C.CYN}{i:>4}{C.R} - [{r['type']}] {name}")
    if len(results) > 50:
        print(f"  {C.D}... ve {len(results)-50} tane daha{C.R}")

    ch = input("\n  Cikar? (numara veya 'a'=hepsi, Enter=geri don): ").strip()
    if not ch:
        return

    output = input("  Cikti klasoru: ").strip() or "./extracted_search"

    if ch.lower() == "a":
        count = 0
        for r in results:
            out = modder.extract_object(r, output)
            if out:
                count += 1
        C.ok(f"{count} dosya cikarildi")
    else:
        try:
            idx = int(ch) - 1
            if 0 <= idx < len(results):
                out = modder.extract_object(results[idx], output)
                if out:
                    C.ok(f"Cikarildi: {out}")
        except:
            C.err("Gecersiz")


def replace_tex(modder: GameModder):
    textures = modder.get_by_category("texture")
    if not textures:
        C.warn("Texture bulunamadi")
        return

    print(f"\n{C.B}  Texture Degistir ({len(textures)} adet):{C.R}")
    for i, t in enumerate(textures[:30], 1):
        name = t["name"] if t["name"] else f"path_id={t['path_id']}"
        print(f"  {C.CYN}{i:>3}{C.R} - {name}")
    if len(textures) > 30:
        print(f"  {C.D}... ve {len(textures)-30} tane daha{C.R}")

    print(f"  {C.CYN}  0{C.R} - Geri don")
    ch = input("\n  Secim: ").strip()
    if ch == "0" or not ch:
        return

    try:
        idx = int(ch) - 1
        if 0 <= idx < len(textures):
            t = textures[idx]
            new_img = input("  Yeni resim dosyasi: ").strip()
            if not os.path.exists(new_img):
                C.err("Dosya bulunamadi")
                return
            if modder.replace_texture(t["file"], t["path_id"], new_img):
                C.ok("Texture degistirildi (henuz kaydedilmedi)")
                C.info("Kaydetmek icin menu'den 'Degisiklikleri kaydet' secin")
            else:
                C.err("Degistirilemedi")
    except:
        C.err("Gecersiz")


def replace_aud(modder: GameModder):
    audios = modder.get_by_category("audio")
    if not audios:
        C.warn("Audio bulunamadi")
        return

    print(f"\n{C.B}  Ses Degistir ({len(audios)} adet):{C.R}")
    for i, a in enumerate(audios[:30], 1):
        name = a["name"] if a["name"] else f"path_id={a['path_id']}"
        print(f"  {C.CYN}{i:>3}{C.R} - {name}")
    if len(audios) > 30:
        print(f"  {C.D}... ve {len(audios)-30} tane daha{C.R}")

    print(f"  {C.CYN}  0{C.R} - Geri don")
    ch = input("\n  Secim: ").strip()
    if ch == "0" or not ch:
        return

    try:
        idx = int(ch) - 1
        if 0 <= idx < len(audios):
            a = audios[idx]
            new_aud = input("  Yeni ses dosyasi: ").strip()
            if not os.path.exists(new_aud):
                C.err("Dosya bulunamadi")
                return
            if modder.replace_audio(a["file"], a["path_id"], new_aud):
                C.ok("Ses degistirildi (henuz kaydedilmedi)")
            else:
                C.err("Degistirilemedi")
    except:
        C.err("Gecersiz")


def game_loop(modder: GameModder, game_name: str):
    stats = modder.scan()

    while True:
        game_menu(game_name, stats)
        ch = input("  Secim: ").strip()

        if ch == "0":
            break
        elif ch == "1":
            stats = modder.scan()
            print(modder.summary())
        elif ch == "2":
            out = input("  Cikti klasoru: ").strip() or "./extracted_all"
            C.info("HER SEY cikariliyor...")
            result = modder.extract_all(out)
            C.ok(f"{result['success']} dosya cikarildi: {out}")
            C.dim(f"Basarisiz: {result['failed']}, Atlanan: {result['skipped']}")
        elif ch == "3":
            choose_category(modder, "texture", "Texture/Resimler")
        elif ch == "4":
            choose_category(modder, "audio", "Audio/Sesler")
        elif ch == "5":
            choose_category(modder, "mesh", "Mesh/Modeller")
        elif ch == "6":
            choose_category(modder, "material", "Material/Gorunum")
        elif ch == "7":
            choose_category(modder, "animation", "Animasyon")
        elif ch == "8":
            choose_category(modder, "gameobject", "GameObject/Varliklar")
        elif ch == "9":
            choose_category(modder, "font", "Font/Text")
            choose_category(modder, "text", "Text/Dosyalar")
        elif ch == "10":
            choose_category(modder, "settings", "Settings/Ayarlar")
        elif ch == "11":
            print(modder.summary())
            by_type = modder.get_stats()["by_type"]
            print(f"\n{C.B}  Tip bazinda:{C.R}")
            for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
                print(f"    {t:<30} {C.B}{c}{C.R}")
        elif ch == "12":
            search_assets(modder)
        elif ch == "13":
            replace_tex(modder)
        elif ch == "14":
            replace_aud(modder)
        elif ch == "15":
            confirm = input("  Kaydet? (E/h): ").strip()
            if confirm.lower() == "e":
                C.info("Kaydediliyor...")
                modder.save_all()
                C.ok("Kaydedildi!")
        elif ch == "16":
            bdir = input("  Backup yolu: ").strip() or "./backup"
            C.info("Backup aliniyor...")
            result = modder.backup(bdir)
            C.ok(f"Backup: {result}")
        else:
            C.warn("Gecersiz secim")


def main():
    banner()

    while True:
        main_menu()
        ch = input("  Secim: ").strip()

        if ch == "1":
            selected = choose_steam_game()
            if selected:
                C.info(f"{selected.name} taraniyor...")
                modder = GameModder(selected)
                game_loop(modder, selected.name)

        elif ch == "2":
            path = input("  Oyun klasoru yolu: ").strip()
            if not path or not os.path.exists(path):
                C.err("Gecersiz yol")
                continue
            C.info(f"{Path(path).name} taraniyor...")
            modder = GameModder(Path(path))
            game_loop(modder, Path(path).name)

        elif ch == "3":
            C.info("Gule gule!")
            break

        else:
            C.warn("Gecersiz secim")


if __name__ == "__main__":
    main()
