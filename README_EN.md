# UnityExtractor

**A tool to extract, modify, and repack all assets from Unity games.**

## Features

- **Texture (PNG)** - Extract all textures in high quality
- **Sprite (PNG)** - Extract UI and character sprites
- **Audio (WAV)** - Extract all audio files and music
- **Font (TTF)** - Extract font files
- **Mesh (OBJ)** - Extract 3D models in Blender-compatible format
- **Material (MTL)** - Extract material information
- **Shader** - Extract shader bytecode
- **AnimationClip** - Extract animation files
- **GameObject** - Extract scene objects
- **MonoScript** - Extract C# code (DLL)

## Installation

```bash
# Install dependencies
pip install UnityPy Pillow

# Clone the repository
git clone https://github.com/yunustas/UnityExtractor.git
cd UnityExtractor
```

## Usage

### With GUI
```bash
python3 gui.py
```

1. Select game folder with **BROWSE** button
2. Scan assets with **SCAN** button
3. Select type from left panel
4. Select object from right list
5. Extract files with **EXTRACT** button

### Command Line
```bash
# Extract all assets
python3 extract_all.py

# Extract only music
python3 extract_music.py
```

## Supported Unity Versions

| Version | Status |
|---------|--------|
| Unity 5.x | ✅ Works |
| Unity 2017-2019 | ✅ Works |
| Unity 2020-2022 | ✅ Works |
| Unity 2023+ | ✅ Works |
| Unity 6 | ✅ Works |

## Tested Games

| Game | Status | Notes |
|------|--------|-------|
| ULTRAKILL | ✅ | 3146 objects, 164 music files |
| KAHRETSİN | ✅ | 2209 objects, 521 textures |
| Baldi's Basics | ✅ | Similar structure to KAHRETSİN |
| Indie games | ✅ | Most work |

## May Not Work

### 1. FMOD/Wwise Audio Systems
Some games store audio in FMOD or Wwise format:
- `.bank` files need separate tools
- Use `vgmstream` or `fsbank`

### 2. Secondary Encryption
Some games encrypt assets:
- Denuvo protected games
- Some AAA titles
- Games with custom DRM

### 3. Old Unity Versions
Unity 4 and earlier have limited support.

### 4. Obfuscated Code
Some games obfuscate MonoScript. Code cannot be read in this case.

### 5. Custom Formats
Some games use custom formats:
- Lua scripts
- Python scripts
- Custom binary formats

## Extracted File Formats

| Type | Format | Can be opened? |
|------|--------|---------------|
| Texture2D | `.png` | Yes (image editor) |
| Sprite | `.png` | Yes (image editor) |
| AudioClip | `.wav` | Yes (audio player) |
| Font | `.ttf` | Yes (font viewer) |
| Mesh | `.obj` | Yes (Blender) |
| Material | `.mtl` | Yes (Blender) |
| Shader | `.shader` | Yes (Unity) |
| GameObject | `.prefab` | Yes (Unity) |
| AnimationClip | `.anim` | Yes (Unity) |
| MonoScript | `.dll` | Yes (decompiler) |

## Example: ULTRAKILL Extraction

```bash
python3 extract_all.py
# Output: /home/user/ultrakill_extracted/
# - 28 Textures (PNG)
# - 16 Sprites (PNG)
# - 164 Audio (WAV)
# - 2 Fonts (TTF)
# - 8 Meshes (OBJ)
# - 27 Materials (MTL)
```

## Example: KAHRETSİN Extraction

```bash
python3 extract_kahretsin.py
# Output: /home/user/kahretsin_extracted/
# - 521 Textures (PNG)
# - 491 Sprites (PNG)
# - 9 Audio (WAV)
# - 8 Meshes (OBJ)
# - 114 Materials (MTL)
# - 21 Animations
```

## License

This project is licensed under the **GNU General Public License v3.0**.

## Contributing

1. Fork the project
2. Create a branch (`git checkout -b feature/feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/feature`)
5. Create a Pull Request

## Support

- Issue tracker: [GitHub Issues](https://github.com/yunustas/UnityExtractor/issues)
- Email: [your email]

## Acknowledgments

- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity asset parser
- [Pillow](https://python-pillow.org/) - Image processing
