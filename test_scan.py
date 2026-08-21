#!/usr/bin/env python3
import UnityPy
from pathlib import Path

game_path = Path("/home/yunustas/ULTRAKILL/game")
all_objects = []

for ext in ["*.assets", "*.resource", "*.resS"]:
    for f in game_path.rglob(ext):
        if f.is_file() and ".backup" not in str(f).lower():
            try:
                env = UnityPy.load(str(f))
                for obj in env.objects:
                    t = obj.type.name if hasattr(obj.type, "name") else str(obj.type)
                    name = ""
                    try:
                        data = obj.read()
                        if hasattr(data, "m_Name") and data.m_Name:
                            name = data.m_Name
                    except:
                        pass
                    all_objects.append({
                        "file": f.name,
                        "path_id": obj.path_id,
                        "type": t,
                        "name": name,
                    })
                print(f"  {f.name}: {len(env.objects)} obje")
            except Exception as e:
                print(f"  {f.name}: HATA - {e}")

print(f"\nTOPLAM: {len(all_objects)} obje\n")

types = {}
for o in all_objects:
    t = o["type"]
    types[t] = types.get(t, 0) + 1

print("TIP BAZINDA:")
for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t:<35} {c}")

print("\nORNEKLER:")
for t in ["Texture2D", "AudioClip", "Mesh", "Material", "GameObject", "Font", "VideoClip", "TextAsset"]:
    items = [o for o in all_objects if o["type"] == t]
    if items:
        print(f"\n  {t} ({len(items)}):")
        for item in items[:5]:
            n = item["name"] if item["name"] else "isimsiz"
            print(f"    {item['file']}:path_id={item['path_id']} -> {n}")
