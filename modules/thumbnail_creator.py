"""
Thumbnail oluşturur — videodan rastgele bir kare alır, 1280x720'ye getirir, kaydeder.
Üzerine yazı veya overlay YOK — temiz frame.
"""
import os
import subprocess
import random
from PIL import Image


THUMBNAIL_SIZE = (1280, 720)


def _extract_random_frame(video_path, output_path):
    """Videodan rastgele bir kare çıkarır (orta bölümden, 30-70% arası)."""
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
    duration = float(result.stdout.strip())
    
    time_offset = random.uniform(duration * 0.3, duration * 0.7)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_offset),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
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


def create_thumbnail(background_video_path, output_path):
    """
    Videodan rastgele bir kare çıkarır, 1280x720'ye getirir, kaydeder.
    Yazı yok, overlay yok — temiz thumbnail.
    """
    print(f"🎨 Thumbnail oluşturuluyor (yazısız)...")
    
    # 1. Videodan rastgele kare çıkar
    temp_frame = output_path.replace(".jpg", "_frame.jpg")
    _extract_random_frame(background_video_path, temp_frame)
    
    # 2. Aç ve 1280x720'ye getir
    img = Image.open(temp_frame)
    img = _resize_and_crop(img, THUMBNAIL_SIZE)
    
    # 3. Kaydet
    img.save(output_path, "JPEG", quality=95)
    
    # Geçici dosyayı sil
    if os.path.exists(temp_frame):
        os.remove(temp_frame)
    
    print(f"✅ Thumbnail hazır: {output_path}")
    return output_path
