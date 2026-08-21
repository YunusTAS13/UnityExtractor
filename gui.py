#!/usr/bin/env python3
"""
Game Modder GUI - Steam Oyunlarini Modlama Araci
Derlenmiş Unity oyunlarının asset'lerini görsel olarak keşfet, çıkar, değiştir.
"""

import os
import sys
import json
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, List, Optional

try:
    import UnityPy
except ImportError:
    os.system(f"{sys.executable} -m pip install --break-system-packages UnityPy")
    import UnityPy

try:
    from PIL import Image, ImageTk
except ImportError:
    os.system(f"{sys.executable} -m pip install --break-system-packages Pillow")
    from PIL import Image, ImageTk


# ============================================================
# RENKLER & TEMALAR
# ============================================================
THEME = {
    "bg": "#1a1a2e",
    "bg2": "#16213e",
    "bg3": "#0f3460",
    "fg": "#e8e8e8",
    "accent": "#e94560",
    "accent2": "#533483",
    "green": "#00b894",
    "yellow": "#fdcb6e",
    "dim": "#636e72",
    "entry_bg": "#2d3436",
    "button_bg": "#e94560",
    "button_fg": "#ffffff",
}


# ============================================================
# ANA MOTOR
# ============================================================
class GameModderEngine:
    def __init__(self):
        self.envs: Dict[str, object] = {}
        self.all_objects: List[dict] = []
        self.game_path: Optional[Path] = None

    def scan(self, game_path: str) -> dict:
        self.game_path = Path(game_path)
        self.all_objects.clear()
        self.envs.clear()

        asset_files = []
        # Main assets
        for ext in ["*.assets", "*.resource", "*.resS"]:
            for f in self.game_path.rglob(ext):
                if f.is_file() and ".backup" not in str(f).lower():
                    asset_files.append(f)

        # Streaming assets bundles (music, scenes, etc.)
        for f in self.game_path.rglob("*.bundle"):
            if f.is_file():
                asset_files.append(f)

        for af in asset_files:
            self._load_file(af)

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
                    except:
                        pass

                    self.all_objects.append({
                        "file": str(filepath),
                        "file_name": filepath.name,
                        "path_id": obj.path_id,
                        "type": type_name,
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
        by_type = {}
        for o in self.all_objects:
            t = o["type"]
            by_type[t] = by_type.get(t, 0) + 1
        stats["by_type"] = by_type
        return stats

    def get_by_type(self, type_name: str) -> List[dict]:
        return [o for o in self.all_objects if o["type"] == type_name]

    def search(self, query: str) -> List[dict]:
        q = query.lower()
        return [o for o in self.all_objects if q in o["name"].lower() or q in o["type"].lower()]

    def _save_as_obj(self, data, name, out_path):
        try:
            with open(out_path, "w") as f:
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
        except:
            return False

    def _save_as_mtl(self, data, name, out_path):
        try:
            with open(out_path, "w") as f:
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
        except:
            return False

    def _get_raw_bytes(self, obj):
        try:
            obj.reset()
            return obj.get_raw_data()
        except:
            try:
                return bytes(obj.raw_data)
            except:
                return None

    def extract_object(self, obj_info: dict, output_dir: str) -> Optional[str]:
        env = self.envs.get(obj_info["file"])
        if not env:
            return None

        for obj in env.objects:
            if obj.path_id == obj_info["path_id"]:
                try:
                    data = obj.read()
                    typ = obj_info["type"]

                    if typ == "Texture2D" and hasattr(data, 'image') and data.image:
                        name = data.m_Name or f"texture_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "textures", f"{name}.png")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        data.image.save(out)
                        return out

                    elif typ == "Sprite" and hasattr(data, 'image') and data.image:
                        name = data.m_Name or f"sprite_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "sprites", f"{name}.png")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        data.image.save(out)
                        return out

                    elif typ == "AudioClip" and hasattr(data, 'samples') and data.samples:
                        for clip_name, clip_data in data.samples.items():
                            out = os.path.join(output_dir, "audio", f"{clip_name}.wav")
                            os.makedirs(os.path.dirname(out), exist_ok=True)
                            with open(out, "wb") as f:
                                f.write(clip_data)
                        return out

                    elif typ == "Font":
                        name = data.m_Name or f"font_{obj_info['path_id']}"
                        if hasattr(data, 'm_FontData') and data.m_FontData:
                            out = os.path.join(output_dir, "fonts", f"{name}.ttf")
                            os.makedirs(os.path.dirname(out), exist_ok=True)
                            with open(out, "wb") as f:
                                f.write(bytes(data.m_FontData))
                            return out
                        return None

                    elif typ == "Mesh":
                        name = data.m_Name or f"mesh_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "meshes", f"{name}.obj")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        self._save_as_obj(data, name, out)
                        return out

                    elif typ == "Material":
                        name = data.m_Name or f"mat_{obj_info['path_id']}"
                        out_dir = os.path.join(output_dir, "materials")
                        os.makedirs(out_dir, exist_ok=True)
                        out_mtl = os.path.join(out_dir, f"{name}.mtl")
                        self._save_as_mtl(data, name, out_mtl)
                        return out_mtl

                    elif typ == "Shader":
                        name = data.m_Name or f"shader_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "shaders", f"{name}.shader")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        raw = self._get_raw_bytes(obj)
                        if raw:
                            with open(out, "wb") as f:
                                f.write(raw)
                            return out
                        return None

                    elif typ == "GameObject":
                        name = data.m_Name or f"go_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "gameobjects", f"{name}.prefab")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        raw = self._get_raw_bytes(obj)
                        if raw:
                            with open(out, "wb") as f:
                                f.write(raw)
                            return out
                        return None

                    elif typ == "AnimationClip":
                        name = data.m_Name or f"anim_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "animations", f"{name}.anim")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        raw = self._get_raw_bytes(obj)
                        if raw:
                            with open(out, "wb") as f:
                                f.write(raw)
                            return out
                        return None

                    elif typ == "TextAsset":
                        name = data.m_Name or f"text_{obj_info['path_id']}"
                        content = data.m_Script if hasattr(data, "m_Script") else ""
                        if isinstance(content, bytes):
                            out = os.path.join(output_dir, "texts", f"{name}.bin")
                            os.makedirs(os.path.dirname(out), exist_ok=True)
                            with open(out, "wb") as f:
                                f.write(content)
                        else:
                            out = os.path.join(output_dir, "texts", f"{name}.txt")
                            os.makedirs(os.path.dirname(out), exist_ok=True)
                            with open(out, "w") as f:
                                f.write(content)
                        return out

                    else:
                        name = data.m_Name if hasattr(data, 'm_Name') and data.m_Name else f"obj_{obj_info['path_id']}"
                        out = os.path.join(output_dir, "other", f"{typ}_{name}_{obj_info['path_id']}.bin")
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        raw = self._get_raw_bytes(obj)
                        if raw:
                            with open(out, "wb") as f:
                                f.write(raw)
                            return out
                        return None

                except:
                    pass
        return None

    def extract_all(self, output_dir: str, type_filter: str = None) -> int:
        count = 0
        for obj_info in self.all_objects:
            if type_filter and obj_info["type"] != type_filter:
                continue
            out = self.extract_object(obj_info, output_dir)
            if out:
                count += 1
        return count

    def replace_texture(self, file_path: str, path_id: int, new_image: str) -> bool:
        env = self.envs.get(file_path)
        if not env:
            return False
        for obj in env.objects:
            if obj.path_id == path_id:
                data = obj.read()
                if hasattr(data, 'image'):
                    data.image = Image.open(new_image)
                    data.save()
                    return True
        return False

    def replace_audio(self, file_path: str, path_id: int, new_audio: str) -> bool:
        env = self.envs.get(file_path)
        if not env:
            return False
        for obj in env.objects:
            if obj.path_id == path_id:
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


# ============================================================
# GUI
# ============================================================
class GameModderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Modder v3.0 - Steam Oyun Modlama Araci")
        self.root.geometry("1200x800")
        self.root.configure(bg=THEME["bg"])

        self.engine = GameModderEngine()
        self.current_game = None

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Custom.TFrame", background=THEME["bg"])
        style.configure("Header.TLabel", background=THEME["bg"], foreground=THEME["accent"], font=("Helvetica", 20, "bold"))
        style.configure("Sub.TLabel", background=THEME["bg"], foreground=THEME["fg"], font=("Helvetica", 12))
        style.configure("Stats.TLabel", background=THEME["bg2"], foreground=THEME["fg"], font=("Consolas", 11))

        style.configure("Accent.TButton", background=THEME["accent"], foreground=THEME["button_fg"], font=("Helvetica", 11, "bold"))
        style.map("Accent.TButton", background=[("active", THEME["accent2"])])

        style.configure("Treeview", background=THEME["entry_bg"], foreground=THEME["fg"], fieldbackground=THEME["entry_bg"], font=("Consolas", 10))
        style.configure("Treeview.Heading", background=THEME["bg3"], foreground=THEME["fg"], font=("Helvetica", 10, "bold"))
        style.map("Treeview", background=[("selected", THEME["accent2"])])

    def create_widgets(self):
        # HEADER
        header = ttk.Frame(self.root, style="Custom.TFrame")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ttk.Label(header, text="GAME MODDER", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="Steam Oyunlarini Modlama Araci", style="Sub.TLabel").pack(side="left", padx=(15, 0))

        # TOP BAR - Game Selection
        topbar = ttk.Frame(self.root, style="Custom.TFrame")
        topbar.pack(fill="x", padx=20, pady=10)

        self.game_path_var = tk.StringVar()
        self.game_path_entry = tk.Entry(topbar, textvariable=self.game_path_var, bg=THEME["entry_bg"], fg=THEME["fg"],
                                         insertbackground=THEME["fg"], font=("Consolas", 11), relief="flat", bd=5)
        self.game_path_entry.pack(side="left", fill="x", expand=True, ipady=5)

        btn_frame = ttk.Frame(topbar, style="Custom.TFrame")
        btn_frame.pack(side="right", padx=(10, 0))

        tk.Button(btn_frame, text="BUL", command=self.browse_game, bg=THEME["accent2"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=5).pack(side="left", padx=2)

        tk.Button(btn_frame, text="TARA", command=self.scan_game, bg=THEME["green"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=5).pack(side="left", padx=2)

        # STATS BAR
        self.stats_frame = tk.Frame(self.root, bg=THEME["bg2"], relief="flat")
        self.stats_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.stats_label = tk.Label(self.stats_frame, text="Oyun secilmedi", bg=THEME["bg2"],
                                     fg=THEME["fg"], font=("Consolas", 11), anchor="w")
        self.stats_label.pack(fill="x", padx=10, pady=8)

        # MAIN CONTENT - PANED
        main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # LEFT PANEL - Type List
        left_frame = tk.Frame(main_pane, bg=THEME["bg"], relief="flat")
        main_pane.add(left_frame, weight=1)

        tk.Label(left_frame, text="TIPLER", bg=THEME["bg"], fg=THEME["accent"],
                 font=("Helvetica", 12, "bold")).pack(pady=(5, 10))

        self.type_listbox = tk.Listbox(left_frame, bg=THEME["entry_bg"], fg=THEME["fg"],
                                        selectbackground=THEME["accent2"], selectforeground="white",
                                        font=("Consolas", 11), relief="flat", bd=0, highlightthickness=0)
        self.type_listbox.pack(fill="both", expand=True, padx=5)
        self.type_listbox.bind("<<ListboxSelect>>", self.on_type_select)

        # RIGHT PANEL - Objects + Preview
        right_frame = tk.Frame(main_pane, bg=THEME["bg"], relief="flat")
        main_pane.add(right_frame, weight=3)

        # Search
        search_frame = tk.Frame(right_frame, bg=THEME["bg"])
        search_frame.pack(fill="x", padx=5, pady=(5, 5))

        tk.Label(search_frame, text="ARA:", bg=THEME["bg"], fg=THEME["fg"],
                 font=("Helvetica", 10)).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.filter_objects())
        tk.Entry(search_frame, textvariable=self.search_var, bg=THEME["entry_bg"], fg=THEME["fg"],
                 insertbackground=THEME["fg"], font=("Consolas", 10), relief="flat", bd=3).pack(
            side="left", fill="x", expand=True, padx=5, ipady=3)

        # Object Tree
        tree_frame = tk.Frame(right_frame, bg=THEME["bg"])
        tree_frame.pack(fill="both", expand=True, padx=5)

        columns = ("name", "type", "file", "size")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Isim")
        self.tree.heading("type", text="Tip")
        self.tree.heading("file", text="Dosya")
        self.tree.heading("size", text="Boyut")
        self.tree.column("name", width=250)
        self.tree.column("type", width=150)
        self.tree.column("file", width=150)
        self.tree.column("size", width=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_object_select)

        # BOTTOM - Preview + Actions
        bottom_frame = tk.Frame(self.root, bg=THEME["bg"])
        bottom_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Preview
        self.preview_frame = tk.Frame(bottom_frame, bg=THEME["bg2"], relief="flat")
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.preview_label = tk.Label(self.preview_frame, text="Onizleme", bg=THEME["bg2"],
                                       fg=THEME["dim"], font=("Helvetica", 10))
        self.preview_label.pack(pady=5)

        self.preview_image = tk.Label(self.preview_frame, bg=THEME["bg2"])
        self.preview_image.pack(pady=5)

        self.preview_info = tk.Label(self.preview_frame, text="", bg=THEME["bg2"],
                                      fg=THEME["fg"], font=("Consolas", 10), justify="left")
        self.preview_info.pack(pady=5, anchor="w", padx=10)

        # Action Buttons
        action_frame = tk.Frame(bottom_frame, bg=THEME["bg"])
        action_frame.pack(side="right", fill="y")

        actions = [
            ("SEÇİLENİ ÇIKAR", THEME["green"], self.extract_selected),
            ("TİPİ ÇIKAR", THEME["accent2"], self.extract_type),
            ("HER ŞEYİ ÇIKAR", THEME["accent"], self.extract_all),
            ("TEXTURE DEĞİŞTİR", THEME["yellow"], self.replace_texture),
            ("SESTEĞİŞTİR", "#6c5ce7", self.replace_audio),
            ("KAYDET", THEME["green"], self.save_changes),
            ("BACKUP AL", THEME["accent2"], self.backup_game),
        ]

        for text, color, cmd in actions:
            tk.Button(action_frame, text=text, command=cmd, bg=color, fg="white",
                      font=("Helvetica", 9, "bold"), relief="flat", padx=10, pady=6,
                      width=18).pack(pady=3)

        # Status Bar
        self.status_var = tk.StringVar(value="Hazır")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg=THEME["bg3"],
                               fg=THEME["fg"], font=("Consolas", 9), anchor="w")
        status_bar.pack(fill="x", padx=0, pady=0, side="bottom")

    def browse_game(self):
        path = filedialog.askdirectory(title="Oyun Klasorunu Sec")
        if path:
            self.game_path_var.set(path)

    def scan_game(self):
        path = self.game_path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Hata", "Gecersiz oyun yolu!")
            return

        self.status_var.set("Taranıyor...")
        self.root.update()

        stats = self.engine.scan(path)
        self.current_game = path

        # Update stats
        total = stats["total"]
        by_type = stats["by_type"]
        stats_text = f"Toplam: {total} obje"
        for t, c in sorted(by_type.items(), key=lambda x: -x[1])[:8]:
            stats_text += f"  |  {t}: {c}"
        if len(by_type) > 8:
            stats_text += f"  |  +{len(by_type)-8} tip daha"
        self.stats_label.config(text=stats_text)

        # Update type list
        self.type_listbox.delete(0, tk.END)
        for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
            self.type_listbox.insert(tk.END, f"{t} ({c})")

        self.status_var.set(f"Tarama tamamlandi: {total} obje bulundu")

    def on_type_select(self, event):
        selection = self.type_listbox.curselection()
        if not selection:
            return

        item = self.type_listbox.get(selection[0])
        type_name = item.rsplit(" (", 1)[0]

        self.current_type_filter = type_name
        self.filter_objects()

    def filter_objects(self):
        query = self.search_var.get().lower()

        if hasattr(self, 'current_type_filter'):
            objects = self.engine.get_by_type(self.current_type_filter)
        else:
            objects = self.engine.all_objects

        if query:
            objects = [o for o in objects if query in o["name"].lower() or query in o["type"].lower()]

        self.tree.delete(*self.tree.get_children())
        for obj in objects[:500]:
            name = obj["name"] if obj["name"] else f"path_id={obj['path_id']}"
            size = f"{obj['size']/1024:.1f}KB" if obj['size'] > 0 else "-"
            self.tree.insert("", "end", values=(name, obj["type"], obj["file_name"], size))

        self.status_var.set(f"{len(objects)} obje gosteriliyor")

    def on_object_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        name = item["values"][0]
        type_name = item["values"][1]

        self.preview_info.config(text=f"Isim: {name}\nTip: {type_name}")

        # Preview texture
        if type_name in ("Texture2D", "Sprite"):
            self.preview_label.config(text="Onizleme: Texture")
            self.preview_image.config(image="")
            self._show_texture_preview(name)
        else:
            self.preview_label.config(text=f"Tip: {type_name}")
            self.preview_image.config(image="")

    def _show_texture_preview(self, name):
        try:
            for obj_info in self.engine.all_objects:
                if obj_info["name"] == name and obj_info["type"] in ("Texture2D", "Sprite"):
                    env = self.engine.envs.get(obj_info["file"])
                    if env:
                        for obj in env.objects:
                            if obj.path_id == obj_info["path_id"]:
                                data = obj.read()
                                if hasattr(data, 'image') and data.image:
                                    img = data.image
                                    img.thumbnail((300, 300))
                                    photo = ImageTk.PhotoImage(img)
                                    self.preview_image.config(image=photo)
                                    self.preview_image.image = photo
                                    self.preview_info.config(
                                        text=f"Isim: {name}\nBoyut: {img.width}x{img.height}\nTip: {obj_info['type']}")
                                return
        except:
            pass

    def extract_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uyari", "Once bir obje secin!")
            return

        output_dir = filedialog.askdirectory(title="Cikti Klasorunu Sec")
        if not output_dir:
            return

        self.status_var.set("Cikariliyor...")
        self.root.update()

        count = 0
        for sel in selection:
            item = self.tree.item(sel)
            name = item["values"][0]
            type_name = item["values"][1]

            for obj_info in self.engine.all_objects:
                if obj_info["name"] == name and obj_info["type"] == type_name:
                    out = self.engine.extract_object(obj_info, output_dir)
                    if out:
                        count += 1
                    break

        self.status_var.set(f"{count} dosya cikarildi: {output_dir}")
        messagebox.showinfo("Tamamlandi", f"{count} dosya cikarildi!\n{output_dir}")

    def extract_type(self):
        if not hasattr(self, 'current_type_filter'):
            messagebox.showwarning("Uyari", "Once soldan bir tip secin!")
            return

        output_dir = filedialog.askdirectory(title="Cikti Klasorunu Sec")
        if not output_dir:
            return

        self.status_var.set(f"{self.current_type_filter} cikariliyor...")
        self.root.update()

        count = self.engine.extract_all(output_dir, self.current_type_filter)
        self.status_var.set(f"{count} dosya cikarildi: {output_dir}")
        messagebox.showinfo("Tamamlandi", f"{count} {self.current_type_filter} cikarildi!\n{output_dir}")

    def extract_all(self):
        output_dir = filedialog.askdirectory(title="Cikti Klasorunu Sec")
        if not output_dir:
            return

        self.status_var.set("HER SEY cikariliyor...")
        self.root.update()

        count = self.engine.extract_all(output_dir)
        self.status_var.set(f"{count} dosya cikarildi: {output_dir}")
        messagebox.showinfo("Tamamlandi", f"{count} dosya cikarildi!\n{output_dir}")

    def replace_texture(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uyari", "Once bir texture secin!")
            return

        item = self.tree.item(selection[0])
        type_name = item["values"][1]
        if type_name != "Texture2D":
            messagebox.showwarning("Uyari", "Sadece Texture2D degistirilebilir!")
            return

        new_image = filedialog.askopenfilename(title="Yeni Resim Sec",
                                                filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("Tum Dosyalar", "*.*")])
        if not new_image:
            return

        name = item["values"][0]
        for obj_info in self.engine.all_objects:
            if obj_info["name"] == name and obj_info["type"] == "Texture2D":
                if self.engine.replace_texture(obj_info["file"], obj_info["path_id"], new_image):
                    self.status_var.set(f"Texture degistirildi: {name}")
                    messagebox.showinfo("Tamam", f"Texture degistirildi!\nHenuz kaydedilmedi.\nKaydetmek icin 'KAYDET' butonuna basin.")
                else:
                    messagebox.showerror("Hata", "Texture degistirilemedi!")
                return

    def replace_audio(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uyari", "Once bir ses dosyasi secin!")
            return

        item = self.tree.item(selection[0])
        type_name = item["values"][1]
        if type_name != "AudioClip":
            messagebox.showwarning("Uyari", "Sadece AudioClip degistirilebilir!")
            return

        new_audio = filedialog.askopenfilename(title="Yeni Ses Sec",
                                                filetypes=[("WAV", "*.wav"), ("MP3", "*.mp3"), ("Tum Dosyalar", "*.*")])
        if not new_audio:
            return

        name = item["values"][0]
        for obj_info in self.engine.all_objects:
            if obj_info["name"] == name and obj_info["type"] == "AudioClip":
                if self.engine.replace_audio(obj_info["file"], obj_info["path_id"], new_audio):
                    self.status_var.set(f"Ses degistirildi: {name}")
                    messagebox.showinfo("Tamam", f"Ses degistirildi!\nHenuz kaydedilmedi.")
                else:
                    messagebox.showerror("Hata", "Ses degistirilemedi!")
                return

    def save_changes(self):
        if not messagebox.askyesno("Onay", "Degisiklikleri kaydetmek istediginize emin misiniz?\nBu islem orijinal dosyalari degistirecek!"):
            return

        self.status_var.set("Kaydediliyor...")
        self.root.update()

        self.engine.save_all()
        self.status_var.set("Tum degisiklikler kaydedildi!")
        messagebox.showinfo("Tamam", "Tum degisiklikler kaydedildi!")

    def backup_game(self):
        output_dir = filedialog.askdirectory(title="Backup Klasorunu Sec")
        if not output_dir:
            return

        self.status_var.set("Backup aliniyor...")
        self.root.update()

        result = self.engine.backup(output_dir)
        self.status_var.set(f"Backup alindi: {result}")
        messagebox.showinfo("Tamam", f"Backup alindi!\n{result}")

    def run(self):
        self.root.mainloop()


# ============================================================
# CLI YERINE GUI CALISTIR
# ============================================================
if __name__ == "__main__":
    app = GameModderGUI()
    app.run()
