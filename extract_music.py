#!/usr/bin/env python3
import UnityPy
import os
from pathlib import Path

bundle_dir = Path("/home/yunustas/ULTRAKILL/game/ULTRAKILL_Data/StreamingAssets/aa/StandaloneWindows64")
output_dir = Path("/home/yunustas/ultrakill_extracted/audio")
output_dir.mkdir(parents=True, exist_ok=True)

count = 0
errors = 0

for f in sorted(bundle_dir.glob("music_*")):
    print(f"\n--- {f.name} ---")
    try:
        env = UnityPy.load(str(f))
        for obj in env.objects:
            if obj.type.name == "AudioClip":
                try:
                    data = obj.read()
                    name = data.m_Name or f"audio_{obj.path_id}"

                    if hasattr(data, "samples") and data.samples:
                        for clip_name, clip_data in data.samples.items():
                            out = output_dir / f"{name}.wav"
                            with open(str(out), "wb") as fw:
                                fw.write(clip_data)
                            count += 1
                            print(f"  [OK] {name}.wav ({len(clip_data)//1024}KB)")
                    else:
                        print(f"  [SKIP] {name}: no samples")
                except Exception as e:
                    errors += 1
                    print(f"  [ERR] {e}")
    except Exception as e:
        print(f"  [ERR] bundle: {e}")

# Also check other bundles with audio
for f in sorted(bundle_dir.glob("*.bundle")):
    if "music_" not in f.name:
        try:
            env = UnityPy.load(str(f))
            for obj in env.objects:
                if obj.type.name == "AudioClip":
                    try:
                        data = obj.read()
                        name = data.m_Name or f"audio_{obj.path_id}"
                        if hasattr(data, "samples") and data.samples:
                            for clip_name, clip_data in data.samples.items():
                                out = output_dir / f"{name}.wav"
                                with open(str(out), "wb") as fw:
                                    fw.write(clip_data)
                                count += 1
                                print(f"  [OK] {f.name}/{name}.wav ({len(clip_data)//1024}KB)")
                    except:
                        pass
        except:
            pass

# Also check main assets for audio
print("\n--- Main Assets ---")
for ext in ["*.assets"]:
    for f in Path("/home/yunustas/ULTRAKILL/game/ULTRAKILL_Data").glob(ext):
        try:
            env = UnityPy.load(str(f))
            for obj in env.objects:
                if obj.type.name == "AudioClip":
                    try:
                        data = obj.read()
                        name = data.m_Name or f"audio_{obj.path_id}"
                        if hasattr(data, "samples") and data.samples:
                            for clip_name, clip_data in data.samples.items():
                                out = output_dir / f"{name}.wav"
                                with open(str(out), "wb") as fw:
                                    fw.write(clip_data)
                                count += 1
                                print(f"  [OK] {f.name}/{name}.wav ({len(clip_data)//1024}KB)")
                    except:
                        pass
        except:
            pass

print(f"\n{'='*40}")
print(f"Toplam: {count} ses dosyasi cikarildi")
print(f"Hata: {errors}")
print(f"Klasor: {output_dir}")
