"""
Pillow ile thumbnail oluşturur.
Pixabay resmi + gradient overlay + başlık metni + duration etiketi.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


THUMBNAIL_SIZE = (1280, 720)


def _resize_and_crop(image, target_size):
    """Resmi 16:9 oranına kırparak hedef boyuta getirir."""
    target_ratio = target_size[0] / target_size[1]
    img_ratio = image.width / image.height
    
    if img_ratio > target_ratio:
        # Resim çok geniş, yüksekliğe göre kırp
        new_width = int(image.height * target_ratio)
        offset = (image.width - new_width) // 2
        image = image.crop((offset, 0, offset + new_width, image.height))
    else:
        # Resim çok dar, genişliğe göre kırp
        new_height = int(image.width / target_ratio)
        offset = (image.height - new_height) // 2
        image = image.crop((0, offset, image.width, offset + new_height))
    
    return image.resize(target_size, Image.LANCZOS)


def _add_gradient_overlay(image, opacity=0.5):
    """Alttan üste doğru koyu gradient ekler (yazı okunsun diye)."""
    gradient = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    width, height = image.size
    for y in range(height):
        # Alt kısım koyu, üst kısım hafif şeffaf
        alpha = int(255 * opacity * (y / height) ** 1.5)
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    
    image = image.convert("RGBA")
    return Image.alpha_composite(image, gradient).convert("RGB")


def _add_vignette(image, strength=0.4):
    """Köşeleri hafif karartır (sinematik görünüm)."""
    width, height = image.size
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    
    cx, cy = width / 2, height / 2
    max_dist = (cx ** 2 + cy ** 2) ** 0.5
    
    # Radial gradient için bir overlay
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            ratio = dist / max_dist
            alpha = int(255 * strength * ratio ** 2)
            draw.rectangle([x, y, x + 4, y + 4], fill=(0, 0, 0, alpha))
    
    image = image.convert("RGBA")
    return Image.alpha_composite(image, vignette).convert("RGB")


def _get_font(size, bold=True):
    """Sistem fontunu yükler."""
    # GitHub Actions Linux için yaygın font yolları
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    
    # Fallback
    return ImageFont.load_default()


def _draw_text_with_shadow(draw, position, text, font, fill="white", shadow_offset=4):
    """Metni gölge ile çizer."""
    x, y = position
    # Gölge
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 200), font=font)
    # Asıl metin
    draw.text((x, y), text, fill=fill, font=font)


def create_thumbnail(background_image_path, title_text, output_path, duration_text="1 HOUR"):
    """
    Ana thumbnail oluşturma fonksiyonu.
    
    background_image_path: Pixabay'den indirilen resim
    title_text: Başlık (kanal adı gibi)
    output_path: Kaydedilecek thumbnail yolu
    duration_text: Süre etiketi (örn. "1 HOUR")
    """
    print(f"🎨 Thumbnail oluşturuluyor: '{title_text}'")
    
    # 1. Resmi aç ve 1280x720'ye getir
    img = Image.open(background_image_path)
    img = _resize_and_crop(img, THUMBNAIL_SIZE)
    
    # 2. Hafif blur (estetik için)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    
    # 3. Vignette efekti
    img = _add_vignette(img, strength=0.5)
    
    # 4. Gradient overlay (alttan koyu)
    img = _add_gradient_overlay(img, opacity=0.7)
    
    # 5. Başlık metni
    draw = ImageDraw.Draw(img)
    
    # Font boyutu metin uzunluğuna göre ayarla
    if len(title_text) <= 12:
        title_font_size = 130
    elif len(title_text) <= 18:
        title_font_size = 100
    else:
        title_font_size = 80
    
    title_font = _get_font(title_font_size, bold=True)
    duration_font = _get_font(50, bold=True)
    
    # Başlık metnini ortala (yatayda)
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_x = (THUMBNAIL_SIZE[0] - text_width) // 2
    text_y = THUMBNAIL_SIZE[1] - 280  # Alttan yukarıya konumla
    
    _draw_text_with_shadow(draw, (text_x, text_y), title_text, title_font)
    
    # 6. Süre etiketi (sağ üst köşe)
    duration_bbox = draw.textbbox((0, 0), duration_text, font=duration_font)
    dur_width = duration_bbox[2] - duration_bbox[0]
    dur_height = duration_bbox[3] - duration_bbox[1]
    
    # Sağ üst köşe arka planı
    padding = 20
    box_x = THUMBNAIL_SIZE[0] - dur_width - padding * 2 - 30
    box_y = 30
    box = [
        box_x, box_y,
        box_x + dur_width + padding * 2, box_y + dur_height + padding
    ]
    draw.rounded_rectangle(box, radius=12, fill=(255, 50, 50, 230))
    
    draw.text(
        (box_x + padding, box_y + padding // 2),
        duration_text,
        fill="white",
        font=duration_font,
    )
    
    # 7. Kaydet
    img.save(output_path, "JPEG", quality=92)
    print(f"✅ Thumbnail hazır: {output_path}")
    
    return output_path
