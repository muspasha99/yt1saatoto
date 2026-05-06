"""
Pillow ile thumbnail oluşturur.
Video'dan bir kare çıkarır + üzerine basit yazı ekler.
"""
import os
import subprocess
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter


THUMBNAIL_SIZE = (1280, 720)


def extract_frame_from_video(video_path, output_path, time_offset=None):
    """
    Videodan rastgele bir kare çıkarır.
    Loop'lanmamış kısa videodan, ortalardan bir frame alıyoruz.
    """
    # Video süresinden orta bir nokta seç (rastgele 30%-70% arası)
    if time_offset is None:
        # Video süresini al
        cmd_probe = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        # Ortadaki bölümden rastgele bir nokta
        time_offset = random.uniform(duration * 0.3, duration * 0.7)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_offset),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",  # Yüksek kalite JPEG
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
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


def _add_subtle_overlay(image, opacity=0.35):
    """Hafif koyu overlay (yazı okunsun ama animasyon görünsün)."""
    overlay = Image.new("RGBA", image.size, (0, 0, 0, int(255 * opacity)))
    image = image.convert("RGBA")
    return Image.alpha_composite(image, overlay).convert("RGB")


def _get_font(size):
    """Sistem fontunu yükler."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_text_with_shadow(draw, position, text, font, fill="white", shadow_offset=5):
    """Metni gölge ile çizer."""
    x, y = position
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 220), font=font)
    draw.text((x, y), text, fill=fill, font=font)


def create_thumbnail(background_video_path, title_text, output_path):
    """
    Videodan bir kare çıkarır, üzerine basit yazı ekler.
    
    background_video_path: Pixabay'den indirilen kısa video
    title_text: Üzerine yazılacak kısa yazı (örn: "LOFI STUDY", "ZEN YOGA")
    output_path: Thumbnail kaydedileceği yer
    duration_text: Süre etiketi
    """
    print(f"🎨 Thumbnail oluşturuluyor: '{title_text}'")
    
    # 1. Videodan bir kare çıkar
    temp_frame = output_path.replace(".jpg", "_frame.jpg")
    extract_frame_from_video(background_video_path, temp_frame)
    
    # 2. Resmi aç ve 1280x720'ye getir
    img = Image.open(temp_frame)
    img = _resize_and_crop(img, THUMBNAIL_SIZE)
    
    # 3. Hafif overlay (yazı okunsun ama görüntü kaybolmasın)
    img = _add_subtle_overlay(img, opacity=0.35)
    
    # 4. Yazıyı yerleştir
    draw = ImageDraw.Draw(img)
    
    # Font boyutu metin uzunluğuna göre
    if len(title_text) <= 10:
        title_font_size = 160
    elif len(title_text) <= 15:
        title_font_size = 130
    else:
        title_font_size = 100
    
    title_font = _get_font(title_font_size)
    duration_font = _get_font(50)
    
    # Başlığı ortala (yatay + dikey)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (THUMBNAIL_SIZE[0] - text_width) // 2
    text_y = (THUMBNAIL_SIZE[1] - text_height) // 2 - 30
    
    _draw_text_with_shadow(draw, (text_x, text_y), title_text, title_font)
    
    
    # 6. Kaydet
    img.save(output_path, "JPEG", quality=95)
    
    # Geçici frame dosyasını sil
    if os.path.exists(temp_frame):
        os.remove(temp_frame)
    
    print(f"✅ Thumbnail hazır: {output_path}")
    return output_path
