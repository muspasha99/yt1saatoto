"""
Pixabay'den arka plan videosu indirir.
Kanal konseptine uygun döngü video çeker.
"""
import os
import random
import requests


PIXABAY_VIDEO_API = "https://pixabay.com/api/videos/"
PIXABAY_IMAGE_API = "https://pixabay.com/api/"


def search_videos(api_key, query, per_page=50, min_width=1920, min_height=1080):
    """Pixabay'de gerçek 1080p+ video ara."""
    params = {
        "key": api_key,
        "q": query,
        "per_page": per_page,
        "min_width": min_width,    # API tarafında filtre
        "min_height": min_height,
        "video_type": "all",
        "safesearch": "true",
    }
    response = requests.get(PIXABAY_VIDEO_API, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Client-side ek doğrulama: "large" versiyonu gerçekten 1080p mi?
    hits = data.get("hits", [])
    quality_hits = []
    for v in hits:
        large = v.get("videos", {}).get("large", {})
        if (large.get("url") 
            and large.get("width", 0) >= 1920 
            and large.get("height", 0) >= 1080):
            quality_hits.append(v)
    
    return quality_hits


def download_video(video_url, output_path):
    """Video URL'sini dosyaya indirir."""
    response = requests.get(video_url, stream=True, timeout=120)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    
    return output_path


def get_random_background_video(api_key, query, output_path):
    """Pixabay'den 1080p+ HD arka plan videosu indirir."""
    print(f"📽 Pixabay'de aranıyor (1080p+): '{query}'")
    
    videos = search_videos(api_key, query, per_page=50)
    
    if not videos:
        fallback_query = query.split()[0]
        print(f"   1080p+ sonuç yok, '{fallback_query}' ile deneniyor...")
        videos = search_videos(api_key, fallback_query, per_page=50)
    
    if not videos:
        raise Exception(f"Pixabay'de '{query}' için 1080p+ video bulunamadı")
    
    print(f"   {len(videos)} HD (1080p+) video bulundu, rastgele seçiliyor")
    
    selected = random.choice(videos)
    
    # Direkt large kullan, alt kalite fallback YOK
    large = selected["videos"]["large"]
    download_url = large["url"]
    width = large.get("width", 0)
    height = large.get("height", 0)
    print(f"   Seçilen kaynak: {width}x{height}")
    
    print(f"   Video indiriliyor...")
    download_video(download_url, output_path)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Arka plan videosu hazır: {file_size_mb:.1f} MB")
    
    return output_path


def search_images(api_key, query, per_page=20, min_width=1920):
    """Pixabay'de yüksek kaliteli resim arar (thumbnail için)."""
    params = {
        "key": api_key,
        "q": query,
        "per_page": per_page,
        "min_width": min_width,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
    }
    
    response = requests.get(PIXABAY_IMAGE_API, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    return data.get("hits", [])


def get_random_thumbnail_image(api_key, query, output_path):
    """
    Pixabay'den thumbnail için yüksek kaliteli resim indirir.
    Returns: indirilen dosya yolu
    """
    print(f"🖼️  Thumbnail için resim aranıyor: '{query}'")
    
    images = search_images(api_key, query, per_page=20)
    
    if not images:
        fallback_query = query.split()[0]
        print(f"   Sonuç yok, '{fallback_query}' ile tekrar deneniyor...")
        images = search_images(api_key, fallback_query, per_page=20)
    
    if not images:
        raise Exception(f"Pixabay'de '{query}' için resim bulunamadı")
    
    selected = random.choice(images)
    
    # En yüksek kaliteli URL'yi al
    image_url = selected.get("largeImageURL") or selected.get("webformatURL")
    
    if not image_url:
        raise Exception("İndirilebilir resim URL'si bulunamadı")
    
    response = requests.get(image_url, timeout=60)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    print(f"✅ Thumbnail resmi hazır")
    return output_path
