# UnityExtractor

**Unity oyunlarından tüm asset'leri çıkaran, değiştiren ve geri yazan araç.**

## Özellikler

- **Texture (PNG)** - Tüm texture'ları yüksek kalitede çıkarır
- **Sprite (PNG)** - UI ve karakter sprite'larını çıkarır
- **Audio (WAV)** - Tüm ses dosyalarını ve müzikleri çıkarır
- **Font (TTF)** - Font dosyalarını çıkarır
- **Mesh (OBJ)** - 3D modelleri Blender'a uyumlu formatta çıkarır
- **Material (MTL)** - Material bilgilerini çıkarır
- **Shader** - Shader bytecode'larını çıkarır
- **AnimationClip** - Animasyon dosyalarını çıkarır
- **GameObject** - Sahne objelerini çıkarır
- **MonoScript** - C# kodlarını (DLL) çıkarır

## Kurulum

```bash
# Bağımlılıkları kur
pip install UnityPy Pillow

# Depoyu klonla
git clone https://github.com/yunustas/UnityExtractor.git
cd UnityExtractor
```

## Kullanım

### GUI ile
```bash
python3 gui.py
```

1. **BUL** butonu ile oyun klasörünü seçin
2. **TARA** butonuna basarak asset'leri taratın
3. Sol panelden tip seçin
4. Sağ listeden obje seçin
5. **ÇIKAR** butonu ile dosyaları kaydedin

### Komut Satırı ile
```bash
# Tüm asset'leri çıkar
python3 extract_all.py

# Sadece müzikleri çıkar
python3 extract_music.py
```

## Desteklenen Unity Sürümleri

| Sürüm | Durum |
|-------|-------|
| Unity 5.x | ✅ Çalışıyor |
| Unity 2017-2019 | ✅ Çalışıyor |
| Unity 2020-2022 | ✅ Çalışıyor |
| Unity 2023+ | ✅ Çalışıyor |
| Unity 6 | ✅ Çalışıyor |

## Test Edilen Oyunlar

| Oyun | Durum | Notlar |
|------|-------|--------|
| ULTRAKILL | ✅ | 3146 obje, 164 müzik |
| KAHRETSİN | ✅ | 2209 obje, 521 texture |
| Baldi's Basics | ✅ | KAHRETSİN ile benzer yapı |
| Indie oyunlar | ✅ | Çoğu çalışıyor |

## Çalışmayabilir Durumlar

### 1. FMOD/Wwise Ses Sistemleri
Bazı oyunlar sesleri FMOD veya Wwise ile saklar. Bu durumda:
- `.bank` dosyaları ayrı araçlarla açılmalı
- `vgmstream` veya `fsbank` kullanılabilir

### 2. İkincil Şifreleme
Bazı oyunlar asset'leri şifreler:
- Denuvo korumalı oyunlar
- Bazı AAA yapımlar
- Özel DRM kullanan oyunlar

### 3. Eski Unity Sürümleri
Unity 4 ve öncesi için tam destek yoktur.

### 4. Obfuscated Kodlar
Bazı oyunlar MonoScript'leri karışık hale getirir. Bu durumda kodlar okunamaz.

### 5. Özel Formatlar
Bazı oyunlar kendi formatlarını kullanır:
- Lua scriptleri
- Python scriptleri
- Özel binary formatları

## Çıkarılan Dosya Formatları

| Tip | Format | Açılabilir mi? |
|-----|--------|---------------|
| Texture2D | `.png` | Evet (resim editörü) |
| Sprite | `.png` | Evet (resim editörü) |
| AudioClip | `.wav` | Evet (ses oynatıcı) |
| Font | `.ttf` | Evet (font oynatıcı) |
| Mesh | `.obj` | Evet (Blender) |
| Material | `.mtl` | Evet (Blender) |
| Shader | `.shader` | Evet (Unity) |
| GameObject | `.prefab` | Evet (Unity) |
| AnimationClip | `.anim` | Evet (Unity) |
| MonoScript | `.dll` | Evet (decompiler) |

## Örnek: ULTRAKILL Çıkarımı

```bash
python3 extract_all.py
# Çıktı: /home/user/ultrakill_extracted/
# - 28 Texture (PNG)
# - 16 Sprite (PNG)
# - 164 Audio (WAV)
# - 2 Font (TTF)
# - 8 Mesh (OBJ)
# - 27 Material (MTL)
```

## Örnek: KAHRETSİN Çıkarımı

```bash
python3 extract_kahretsin.py
# Çıktı: /home/user/kahretsin_extracted/
# - 521 Texture (PNG)
# - 491 Sprite (PNG)
# - 9 Audio (WAV)
# - 8 Mesh (OBJ)
# - 114 Material (MTL)
# - 21 Animation
```

## Lisans

Bu proje **GNU General Public License v3.0** altında lisanslanmıştır.

## Katkıda Bulunma

1. Fork yapın
2. Branch oluşturun (`git checkout -b feature/ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Özellik ekle'`)
4. Push yapın (`git push origin feature/ozellik`)
5. Pull Request oluşturun

## Destek

- Sorun bildirimi: [GitHub Issues](https://github.com/yunustas/UnityExtractor/issues)
-.email: [e-posta adresiniz]

## Teşekkürler

- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity asset parser
- [Pillow](https://python-pillow.org/) - Resim işleme
