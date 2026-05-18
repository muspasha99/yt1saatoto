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
    """Bir kanal için tüm pipeline'ı çalıştırır."""
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
    thumbnail = os.path.join(work_dir, "thumbnail.jpg")
    final_video = os.path.join(work_dir, "final.mp4")
    
    try:
        # API key'leri ve token'ları çevre değişkenlerinden al
        gemini_key = _get_env("GEMINI_API_KEY")
        
        drive_account = channel["drive_account"]
        drive_token = _get_env(f"DRIVE_TOKEN_{drive_account.upper()}")
        yt_token = _get_env(f"YT_TOKEN_{channel_code.upper()}")
        
        # 1. ADIM: Müziği Drive'dan indir
        print("\n[1/6] 📁 Müzik dosyaları indiriliyor...")
        track_paths = drive_handler.download_random_tracks(
            drive_token,
            channel["drive_folder_id"],
            music_dir,
            track_count=25,
        )
        
        # 2. ADIM: Müziği crossfade ile birleştir
        print("\n[2/6] 🎵 Müzik birleştiriliyor...")
        audio_processor.create_long_audio(
            track_paths,
            audio_output,
            min_duration_seconds=MIN_VIDEO_DURATION_SECONDS,
            crossfade_seconds=channel["crossfade_seconds"],
        )
        audio_duration = audio_processor.get_audio_duration(audio_output)
        
        # 3. ADIM: Drive'dan arka plan klibi indir
        print("\n[3/6] 🎞 Arka plan klibi alınıyor...")
        clips_folder_id = channel.get("clips_folder_id", "")
        if not clips_folder_id:
            raise Exception(
                f"❌ Kanal '{channel_code}' için clips_folder_id tanımlı değil. "
                f"config.py'da bu alanı doldur."
            )
        drive_handler.download_random_video(
            drive_token,
            clips_folder_id,
            bg_video,
        )
        
        # 4. ADIM: Thumbnail oluştur (videodan rastgele kare, yazısız)
        print("\n[4/6] 🎨 Thumbnail oluşturuluyor...")
        thumbnail_creator.create_thumbnail(bg_video, thumbnail, channel_config=channel)
        
        # 5. ADIM: Gemini ile metadata + Final videoyu oluştur
        print("\n[5/6] 🤖 Metadata üretiliyor + 🎥 Video birleştiriliyor...")
        metadata = gemini_handler.generate_metadata(gemini_key, channel, prompts, thumbnail_path=thumbnail,)
        
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

        # 7. ADIM: Günde 3 Short oluştur ve yükle
        print("\n[7/7] 🎬 Shorts oluşturuluyor (3 adet)...")
        long_video_id = result["video_id"]

        for short_idx in range(3):
            try:
                # Gemini'dan kısa metin üret
                short_text = gemini_handler.generate_short_text(
                    gemini_key, channel, prompts
                )

                short_video_path = os.path.join(work_dir, f"short_{short_idx}.mp4")
                short_work_dir = os.path.join(work_dir, f"short_work_{short_idx}")

                # Short video oluştur
                from modules import shorts_creator
                shorts_creator.create_short(
                    channel_code=channel_code,
                    bg_video_path=bg_video,
                    music_clip_path=audio_output,
                    text=short_text,
                    output_path=short_video_path,
                    work_dir=short_work_dir,
                )

                # YouTube'a yükle
                short_title = f"{short_text} | {channel['display_name']}"
                short_description = (
                    f"{channel['concept'].capitalize()} — "
                    f"Full 1-hour mix in our channel."
                )

                youtube_uploader.upload_short(
                    youtube_token_json=yt_token,
                    video_path=short_video_path,
                    title=short_title,
                    description=short_description,
                    tags=channel.get("video_keywords", []),
                    long_video_id=long_video_id,
                    expected_channel_id=channel["channel_id"],
                )

                print(f"   ✅ Short {short_idx + 1}/3 yüklendi")

            except Exception as e:
                print(f"   ⚠️ Short {short_idx + 1} başarısız: {e}")
                continue  # 1 short başarısız olsa bile devam et
    
    finally:
        # Geçici dosyaları temizle
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
