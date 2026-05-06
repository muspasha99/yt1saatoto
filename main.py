"""
Ana pipeline — komut satırından kanal kodu alır ve tüm adımları çalıştırır.
Kullanım: python main.py <kanal_kodu>
Örnek: python main.py coding
"""
import os
import sys
import shutil
import traceback
from datetime import datetime

from config import CHANNELS, CHANNEL_PROMPTS, MIN_VIDEO_DURATION_SECONDS, TEMP_DIR
from modules import drive_handler
from modules import audio_processor
from modules import pixabay_handler
from modules import thumbnail_creator
from modules import gemini_handler
from modules import video_creator
from modules import youtube_uploader


def _get_env(key):
    """Ortam değişkenini al, yoksa hata ver."""
    val = os.environ.get(key)
    if not val:
        raise Exception(f"Ortam değişkeni eksik: {key}")
    return val


def run_pipeline(channel_code):
    """
    Bir kanal için tüm pipeline'ı çalıştırır.
    """
    if channel_code not in CHANNELS:
        raise Exception(f"Bilinmeyen kanal: {channel_code}")
    
    channel = CHANNELS[channel_code]
    prompts = CHANNEL_PROMPTS[channel_code]
    
    print("=" * 60)
    print(f"🚀 PIPELINE BAŞLIYOR: {channel['display_name']}")
    print(f"   Zaman: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Çalışma klasörü
    work_dir = os.path.join(TEMP_DIR, channel_code)
    music_dir = os.path.join(work_dir, "music")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(music_dir, exist_ok=True)
    
    audio_output = os.path.join(work_dir, "audio_full.wav")
    bg_video = os.path.join(work_dir, "background.mp4")
    bg_image = os.path.join(work_dir, "thumb_bg.jpg")
    thumbnail = os.path.join(work_dir, "thumbnail.jpg")
    final_video = os.path.join(work_dir, "final.mp4")
    
    try:
        # API key'leri ve token'ları çevre değişkenlerinden al
        gemini_key = _get_env("GEMINI_API_KEY")
        pixabay_key = _get_env("PIXABAY_API_KEY")
        
        drive_account = channel["drive_account"]
        yt_account = channel["youtube_account"]
        
        drive_token = _get_env(f"DRIVE_TOKEN_{drive_account.upper()}")
        yt_token = _get_env(f"YT_TOKEN_{channel_code.upper()}")
        
        # 1. ADIM: Müziği Drive'dan indir
        print("\n[1/6] 📁 Müzik dosyaları indiriliyor...")
        track_paths = drive_handler.download_random_tracks(
            drive_token,
            channel["drive_folder_id"],
            music_dir,
            track_count=25,  # 25 parça indir, ihtiyaç olduğu kadar kullanılacak
        )
        
        # 2. ADIM: Müziği crossfade ile birleştir
        print("\n[2/6] 🎵 Müzik birleştiriliyor...")
        audio_processor.create_long_audio(
            track_paths,
            audio_output,
            min_duration_seconds=MIN_VIDEO_DURATION_SECONDS,
            crossfade_seconds=channel["crossfade_seconds"],
        )
        
        # Audio süresini al (video bu kadar olacak)
        audio_duration = audio_processor.get_audio_duration(audio_output)
        
        # 3. ADIM: Pixabay'den arka plan video ve thumbnail resmi indir
        print("\n[3/6] 🎬 Arka plan içerikleri indiriliyor...")
        pixabay_handler.get_random_background_video(
            pixabay_key,
            channel["pixabay_query"],
            bg_video,
        )
        
        pixabay_handler.get_random_thumbnail_image(
            pixabay_key,
            channel["pixabay_query"],
            bg_image,
        )
        
        # 4. ADIM: Thumbnail oluştur
        print("\n[4/6] 🎨 Thumbnail oluşturuluyor...")
        thumbnail_creator.create_thumbnail(
            bg_image,
            channel["thumbnail_text"],
            thumbnail,
            duration_text="1 HOUR",
        )
        
        # 5. ADIM: Gemini ile metadata + Final videoyu oluştur (paralel olabilir ama sıralı yapıyoruz)
        print("\n[5/6] 🤖 Metadata üretiliyor + 🎥 Video birleştiriliyor...")
        metadata = gemini_handler.generate_metadata(
            gemini_key,
            channel,
            prompts,
        )
        
        video_creator.create_video(
            audio_output,
            bg_video,
            final_video,
            target_duration_seconds=audio_duration,
        )
        
        # 6. ADIM: YouTube'a yükle
        print("\n[6/6] 📤 YouTube'a yükleniyor...")
        result = youtube_uploader.upload_complete(
            yt_token,
            final_video,
            thumbnail,
            metadata["title"],
            metadata["description"],
            metadata["tags"],
            expected_channel_id=channel["channel_id"],
        )
        
        print("\n" + "=" * 60)
        print(f"🎉 BAŞARILI: {channel['display_name']}")
        print(f"   Video: {result['url']}")
        print(f"   Süre: {audio_duration/60:.1f} dakika")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        print(traceback.format_exc())
        raise
    
    finally:
        # Geçici dosyaları temizle (GitHub Actions storage için)
        try:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
                print(f"\n🧹 Geçici dosyalar temizlendi")
        except Exception as e:
            print(f"⚠️  Temizleme hatası: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python main.py <kanal_kodu>")
        print(f"Mevcut kanallar: {', '.join(CHANNELS.keys())}")
        sys.exit(1)
    
    channel_code = sys.argv[1].lower().strip()
    run_pipeline(channel_code)
