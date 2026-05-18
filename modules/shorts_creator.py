"""
YouTube Shorts videosu oluşturur.
- Drive'dan klip + müzik alır
- 25-30 saniye keser
- Dikey (9:16) formata çevirir
- Arka planı analiz edip yazı rengini otomatik belirler
- Typewriter animasyonu ile yazıyı yazar (Vault için Zoom Punch + Glitch)
- Uzun videoya yönlendirme linki ekler
"""
import os
import subprocess
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

SHORTS_DIR = "fonts"
SHORTS_DURATION = 28  # saniye
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
FPS = 30

# Kanal bazlı font eşleşmesi
CHANNEL_FONTS = {
    "coding":        "SpaceGrotesk-Bold.ttf",
    "vault":         "BebasNeue-Regular.ttf",
    "zen":           "CormorantGaramond-Bold.ttf",
    "chakra":        "Marcellus-Regular.ttf",
    "beach":         "Quicksand-Bold.ttf",
    "summer":        "CormorantGaramond-Bold.ttf",
    "pets":          "Nunito-ExtraBold.ttf",
    "breathe":       "Quicksand-Bold.ttf",
    "cosmic":        "SpaceGrotesk-Bold.ttf",
    "ocean":         "Marcellus-Regular.ttf",
    "mediterranean": "CormorantGaramond-Bold.ttf",
    "rain":          "SpaceGrotesk-Bold.ttf",
}

# Kanal bazlı typewriter hızı (saniye/karakter)
CHANNEL_TYPEWRITER_SPEED = {
    "coding":        0.06,
    "vault":         0.04,  # hızlı ve sert
    "zen":           0.12,  # yavaş ve sakin
    "chakra":        0.10,
    "beach":         0.06,
    "summer":        0.09,
    "pets":          0.13,  # çok yavaş, sakin
    "breathe":       0.14,  # en yavaş
    "cosmic":        0.08,
    "ocean":         0.10,
    "mediterranean": 0.08,
    "rain":          0.07,
}


def _get_font(channel_code, size):
    """Kanal için doğru fontu yükler."""
    font_file = CHANNEL_FONTS.get(channel_code, "SpaceGrotesk-Bold.ttf")
    font_path = os.path.join(SHORTS_DIR, font_file)

    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"   ⚠️ Font yüklenemedi: {e}")

    # Fallback
    for fallback in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(fallback):
            return ImageFont.truetype(fallback, size)

    return ImageFont.load_default()


def _analyze_background_color(frame_path, text_region_y_ratio=0.5):
    """
    Frame'in yazı yazılacak bölgesini analiz eder.
    Arka plan açık mı koyu mu? Buna göre yazı rengi döner.
    Returns: (text_color, shadow_color, overlay_alpha)
    """
    img = Image.open(frame_path).convert("RGB")
    w, h = img.size

    # Yazı bölgesi: ortanın %20'si (dikey)
    region_top = int(h * (text_region_y_ratio - 0.10))
    region_bot = int(h * (text_region_y_ratio + 0.10))
    region = img.crop((int(w * 0.1), region_top, int(w * 0.9), region_bot))

    # Ortalama parlaklık hesapla
    pixels = np.array(region)
    avg_r = pixels[:, :, 0].mean()
    avg_g = pixels[:, :, 1].mean()
    avg_b = pixels[:, :, 2].mean()

    # Luminance (insan gözü ağırlıklı)
    luminance = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b

    if luminance > 128:
        # Açık arka plan → koyu yazı
        text_color = (20, 20, 20, 255)
        shadow_color = (200, 200, 200, 180)
        overlay_alpha = 40
    else:
        # Koyu arka plan → beyaz yazı
        text_color = (255, 255, 255, 255)
        shadow_color = (0, 0, 0, 200)
        overlay_alpha = 60

    print(f"   🎨 Arka plan luminance: {luminance:.0f} → {'koyu yazı' if luminance > 128 else 'beyaz yazı'}")
    return text_color, shadow_color, overlay_alpha


def _render_typewriter_frames(
    text, font, text_color, shadow_color, overlay_alpha,
    canvas_size, speed_per_char, start_frame, total_frames,
    channel_code
):
    """
    Typewriter animasyonu için frame listesi üretir.
    Her frame bir PIL Image döner.
    Vault için zoom_punch + glitch de eklenir.
    """
    frames = []
    w, h = canvas_size
    is_vault = channel_code == "vault"

    # Yazı pozisyonu — tam orta
    dummy = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (w - text_w) // 2
    text_y = int(h * 0.50) - text_h // 2  # tam orta

    chars_per_frame = 1
    typewriter_end = start_frame + int(len(text) / (FPS * speed_per_char))

    for frame_idx in range(total_frames):
        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base)

        if frame_idx < start_frame:
            frames.append(base)
            continue

        # Kaç karakter gösterilecek
        elapsed = frame_idx - start_frame
        chars_shown = min(
            len(text),
            int(elapsed * FPS * speed_per_char) + 1
        )
        visible_text = text[:chars_shown]

        if is_vault and frame_idx >= typewriter_end:
            # ZOOM PUNCH: typewriter bitti, zoom punch başlar
            zoom_start = typewriter_end
            zoom_duration = int(FPS * 0.3)  # 0.3 saniye
            zoom_progress = min(1.0, (frame_idx - zoom_start) / zoom_duration)

            # Ease out: büyükten küçüğe
            scale = 2.0 - (1.0 * zoom_progress)
            scale = max(1.0, scale)

            # Büyütülmüş font
            big_font = _get_font(channel_code, int(font.size * scale))
            bbox2 = draw.textbbox((0, 0), text, font=big_font)
            bw = bbox2[2] - bbox2[0]
            bh = bbox2[3] - bbox2[1]
            bx = (w - bw) // 2
            by = int(h * 0.50) - bh // 2

            # Gölge
            draw.text((bx + 4, by + 4), text, font=big_font, fill=shadow_color)
            draw.text((bx, by), text, font=big_font, fill=text_color)

            # GLITCH: zoom punch sonrası 2-3 frame
            glitch_start = zoom_start + zoom_duration
            if frame_idx >= glitch_start and frame_idx < glitch_start + 3:
                base = _apply_glitch(base, intensity=5)

        else:
            # Normal typewriter
            draw.text((text_x + 3, text_y + 3), visible_text, font=font, fill=shadow_color)
            draw.text((text_x, text_y), visible_text, font=font, fill=text_color)

        frames.append(base)

    return frames


def _apply_glitch(image, intensity=5):
    """RGB kanallarını kaydırarak glitch efekti uygular."""
    img_array = np.array(image)
    r = img_array[:, :, 0].copy()
    g = img_array[:, :, 1].copy()
    b = img_array[:, :, 2].copy()
    a = img_array[:, :, 3].copy()

    # R kanalını sağa, B kanalını sola kaydır
    r = np.roll(r, intensity, axis=1)
    b = np.roll(b, -intensity, axis=1)

    glitched = np.stack([r, g, b, a], axis=2).astype(np.uint8)
    return Image.fromarray(glitched, "RGBA")


def _extract_clip(source_video, output_path, duration=SHORTS_DURATION):
    """Videodan rastgele bir kısım keser."""
    # Video süresini öğren
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        source_video
    ], capture_output=True, text=True, check=True)

    total = float(probe.stdout.strip())
    # Başından ve sonundan 10s bırak
    start = random.uniform(10, max(10, total - duration - 10))

    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", source_video,
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        output_path
    ], check=True, capture_output=True)

    print(f"   ✂️  Klip kesildi: {start:.1f}s - {start+duration:.1f}s")
    return output_path


def _extract_frame_for_analysis(video_path, time_offset=5):
    """Arka plan analizi için frame çıkarır."""
    frame_path = video_path.replace(".mp4", "_analysis_frame.jpg")
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(time_offset),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        frame_path
    ], check=True, capture_output=True)
    return frame_path


def _make_vertical_with_overlay(clip_path, text, text_color, shadow_color,
                                  overlay_alpha, font, channel_code,
                                  output_path, total_frames):
    """
    Klibi dikey formata çevirir ve yazı overlay'i ekler.
    Frame-by-frame render: PIL ile her frame işlenir.
    """
    frames_dir = clip_path.replace(".mp4", "_frames")
    overlay_dir = clip_path.replace(".mp4", "_overlay")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(overlay_dir, exist_ok=True)

    # 1. Videodan frame'leri çıkar (dikey 1080x1920)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", (
            f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={SHORTS_WIDTH}:{SHORTS_HEIGHT},"
            f"fps={FPS}"
        ),
        "-q:v", "2",
        f"{frames_dir}/frame_%05d.jpg"
    ], check=True, capture_output=True)

    # 2. Her frame üzerine overlay ekle
    actual_frames = sorted(os.listdir(frames_dir))
    n_frames = len(actual_frames)

    # Yazı animasyonu: 1 saniye sonra başlar
    start_frame = FPS * 1
    overlay_frames = _render_typewriter_frames(
        text=text,
        font=font,
        text_color=text_color,
        shadow_color=shadow_color,
        overlay_alpha=overlay_alpha,
        canvas_size=(SHORTS_WIDTH, SHORTS_HEIGHT),
        speed_per_char=CHANNEL_TYPEWRITER_SPEED.get(channel_code, 0.08),
        start_frame=start_frame,
        total_frames=n_frames,
        channel_code=channel_code
    )

    for i, (frame_file, overlay) in enumerate(zip(actual_frames, overlay_frames)):
        bg = Image.open(os.path.join(frames_dir, frame_file)).convert("RGBA")
        bg = Image.alpha_composite(bg, overlay)
        bg.convert("RGB").save(os.path.join(overlay_dir, f"frame_{i:05d}.jpg"), quality=92)

    # 3. Frame'leri video olarak birleştir (ses ile)
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{overlay_dir}/frame_%05d.jpg",
        "-i", clip_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v",
        "-map", "1:a",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path
    ], check=True, capture_output=True)

    # Temizlik
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    shutil.rmtree(overlay_dir, ignore_errors=True)

    print(f"   ✅ Dikey video hazır: {output_path}")


def create_short(
    channel_code,
    bg_video_path,
    music_clip_path,
    text,
    output_path,
    work_dir
):
    """
    Ana fonksiyon. Shorts videosu oluşturur.

    Args:
        channel_code: Kanal kodu (vault, coding, vs)
        bg_video_path: Arka plan video dosyası
        music_clip_path: Müzik dosyası (kısa klip)
        text: Ekrana yazılacak cümle (max 30 karakter)
        output_path: Çıktı video dosyası
        work_dir: Geçici dosyalar için klasör
    """
    print(f"   🎬 Short oluşturuluyor: '{text}'")

    os.makedirs(work_dir, exist_ok=True)

    # 1. Arka plan klibinden kısa kesit al
    clip_path = os.path.join(work_dir, "bg_clip.mp4")
    _extract_clip(bg_video_path, clip_path, duration=SHORTS_DURATION)

    # 2. Müziği de kes (aynı süre)
    music_clip = os.path.join(work_dir, "music_clip.aac")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", music_clip_path,
        "-t", str(SHORTS_DURATION),
        "-c:a", "aac",
        "-b:a", "192k",
        music_clip
    ], check=True, capture_output=True)

    # 3. Arka planı analiz et
    analysis_frame = _extract_frame_for_analysis(clip_path, time_offset=3)
    text_color, shadow_color, overlay_alpha = _analyze_background_color(analysis_frame)
    if os.path.exists(analysis_frame):
        os.remove(analysis_frame)

    # 4. Font yükle
    font_size = 72  # Shorts için büyük font
    font = _get_font(channel_code, font_size)

    # 5. Ses + görüntü birleştirme
    mixed_clip = os.path.join(work_dir, "mixed_clip.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", clip_path,
        "-i", music_clip,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v",
        "-map", "1:a",
        "-shortest",
        mixed_clip
    ], check=True, capture_output=True)

    # 6. Overlay + dikey format + animasyon
    total_frames = SHORTS_DURATION * FPS
    _make_vertical_with_overlay(
        clip_path=mixed_clip,
        text=text,
        text_color=text_color,
        shadow_color=shadow_color,
        overlay_alpha=overlay_alpha,
        font=font,
        channel_code=channel_code,
        output_path=output_path,
        total_frames=total_frames
    )

    print(f"   🎉 Short tamamlandı: {output_path}")
    return output_path
