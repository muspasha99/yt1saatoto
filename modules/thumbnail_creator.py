"""
Thumbnail oluşturur.
- Videodan rastgele bir kare alır, yüksek kalitede işler (2K upscale).
- Kanal stiline göre yazı ekler (thumbnail_style: "text" veya "clean").
- Font, kanal config'inden alınır (fonts/ klasöründen yüklenir).
"""
import os
import random
import subprocess
from PIL import Image, ImageDraw, ImageFont


THUMBNAIL_SIZE = (1280, 720)
FONTS_DIR = "fonts"


def _extract_random_frame(video_path, output_path):
    """
    Videodan rastgele bir kare çıkarır (orta bölümden, 30-70%).
    YÜKSEK KALİTE: 2K'ya upscale + kalite filtreleri uygular.
    """
    # Video süresini öğren
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
    duration = float(result.stdout.strip())
    time_offset = random.uniform(duration * 0.3, duration * 0.7)

    # Geçici yüksek kaliteli frame
    temp_hq_frame = output_path.replace(".jpg", "_hq_temp.png")

    try:
        # ADIM 1: Frame yakala + 2K'ya büyüt (en yüksek kalite)
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(time_offset),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "1",                                    # En yüksek kalite
            "-vf", "scale=2560:1440:flags=lanczos",        # 2K + lanczos filtre
            temp_hq_frame,
        ], check=True, capture_output=True)

        # ADIM 2: Kalite artırma filtreleri uygula
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_hq_frame,
            "-vf", (
                "unsharp=5:5:1.5:5:5:0.0,"                 # Netlik artır
                "eq=contrast=1.1:brightness=0.02:saturation=1.15,"  # Kontrast/renk
                "nlmeans=s=1.5"                            # Gürültü azalt
            ),
            "-q:v", "2",                                   # Yüksek kalite
            output_path,
        ], check=True, capture_output=True)

        print(f"   ✨ Yüksek kaliteli frame alındı (2K upscale)")

    except subprocess.CalledProcessError:
        # Gelişmiş filtreler başarısız olursa basit yönteme geri dön
        print(f"   ⚠️ Gelişmiş filtreler çalışmadı, basit yöntem kullanılıyor...")
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(time_offset),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ], check=True, capture_output=True)

    finally:
        # Geçici dosyayı temizle
        if os.path.exists(temp_hq_frame):
            os.remove(temp_hq_frame)

    return output_path


def _resize_and_crop(image, target_size):
    """Resmi 16:9 oranına kırparak hedef boyuta getirir."""
    target_ratio = target_size[0] / target_size[1]
    img_ratio = image.width / image.height

    if img_ratio > target_ratio:
        new_width = int(image.height * target_ratio)
        offset = (image.width - new_width) // 2
        image = image.crop((offset, 0, offset + new_width, image.height))
    else:
        new_height = int(image.width / target_ratio)
        offset = (image.height - new_height) // 2
        image = image.crop((0, offset, image.width, offset + new_height))

    return image.resize(target_size, Image.LANCZOS)


def _load_font(font_filename, size):
    """Fontu fonts/ klasöründen yükler. Başarısız olursa varsayılan."""
    font_path = os.path.join(FONTS_DIR, font_filename)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"   ⚠️ Font yüklenemedi ({font_filename}): {e}")

    # Fallback: sistem fontu
    fallback_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in fallback_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    return ImageFont.load_default()


def _draw_text_on_image(img, text, font_filename):
    """
    Resme merkezi, gölgeli yazı çizer.
    Font boyutunu metnin uzunluğuna göre otomatik ayarlar.
    """
    draw = ImageDraw.Draw(img)
    max_width = int(THUMBNAIL_SIZE[0] * 0.85)  # Kenardan %7.5 boşluk

    # Font boyutunu otomatik hesapla (büyükten küçüğe dene)
    font = None
    chosen_size = 180
    for size in range(180, 40, -8):
        candidate = _load_font(font_filename, size)
        bbox = draw.textbbox((0, 0), text, font=candidate)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            font = candidate
            chosen_size = size
            break

    if font is None:
        font = _load_font(font_filename, 60)

    # Metin boyutlarını hesapla
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Merkez pozisyon (dikey olarak biraz yukarıda)
    x = (THUMBNAIL_SIZE[0] - text_w) // 2
    y = (THUMBNAIL_SIZE[1] - text_h) // 2 - 10

    # Gölge (siyah, 4px aşağı-sağ)
    shadow = 4
    draw.text((x + shadow, y + shadow), text, font=font, fill=(0, 0, 0, 220))

    # Ana yazı (beyaz)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return img


def create_thumbnail(background_video_path, output_path, channel_config=None):
    """
    Videodan rastgele kare alır. Kanal stiline göre yazı ekler.
    channel_config: CHANNELS dict'inden gelen kanal ayarları.
    """
    thumbnail_style = "clean"
    thumbnail_font = ""
    thumbnail_texts = []

    if channel_config:
        thumbnail_style = channel_config.get("thumbnail_style", "clean")
        thumbnail_font = channel_config.get("thumbnail_font", "")
        thumbnail_texts = channel_config.get("thumbnail_texts", [])

    style_label = "yazılı" if thumbnail_style == "text" else "yazısız"
    print(f"🎨 Thumbnail oluşturuluyor ({style_label})...")

    # 1. Videodan rastgele kare çıkar (YÜKSEK KALİTE)
    temp_frame = output_path.replace(".jpg", "_frame.jpg")
    _extract_random_frame(background_video_path, temp_frame)

    # 2. Aç ve 1280x720'ye getir
    img = Image.open(temp_frame)
    img = _resize_and_crop(img, THUMBNAIL_SIZE)

    # 3. Yazılı stil: overlay + metin
    if thumbnail_style == "text" and thumbnail_font and thumbnail_texts:
        text = random.choice(thumbnail_texts)

        # Yarı saydam koyu overlay (yazı okunabilsin)
        img = img.convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * 0.42)))
        img = Image.alpha_composite(img, overlay).convert("RGB")

        # Yazı çiz
        img = _draw_text_on_image(img, text, thumbnail_font)
        print(f"   Yazı: '{text}' ({thumbnail_font})")

    # 4. Kaydet
    img.save(output_path, "JPEG", quality=95)

    if os.path.exists(temp_frame):
        os.remove(temp_frame)

    print(f"✅ Thumbnail hazır: {output_path}")
    return output_path
