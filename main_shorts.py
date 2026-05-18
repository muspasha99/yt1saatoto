"""
Sadece shorts pipeline'ını çalıştırır.
Kullanım: python main_shorts.py <kanal_kodu> <adet>
Örnek: python main_shorts.py vault 3
"""
import os
import sys
import shutil
import traceback
from datetime import datetime

from config import CHANNELS, CHANNEL_PROMPTS, TEMP_DIR
from modules import drive_handler, gemini_handler, shorts_creator, youtube_uploader


def _get_env(key):
    val = os.environ.get(key)
    if not val:
        raise Exception(f"Ortam değişkeni eksik: {key}")
    return val


def run_shorts_pipeline(channel_code, count=3):
    if channel_code not in CHANNELS:
        raise Exception(f"Bilinmeyen kanal: {channel_code}")

    channel = CHANNELS[channel_code]
    prompts = CHANNEL_PROMPTS[channel_code]

    print("=" * 60)
    print(f"🎬 SHORTS PIPELINE: {channel['display_name']}")
    print(f"   Adet: {count}")
    print(f"   Zaman: {datetime.now().isoformat()}")
    print("=" * 60)

    work_dir = os.path.join(TEMP_DIR, f"{channel_code}_shorts")
    os.makedirs(work_dir, exist_ok=True)

    try:
        gemini_key = _get_env("GEMINI_API_KEY")
        drive_account = channel["drive_account"]
        drive_token = _get_env(f"DRIVE_TOKEN_{drive_account.upper()}")
        yt_token = _get_env(f"YT_TOKEN_{channel_code.upper()}")

        # 1. Drive'dan arka plan klibi indir
        print("\n[1/3] 🎞 Arka plan klibi indiriliyor...")
        bg_video = os.path.join(work_dir, "background.mp4")
        clips_folder_id = channel.get("clips_folder_id", "")
        if not clips_folder_id:
            raise Exception(f"clips_folder_id eksik: {channel_code}")

        drive_handler.download_random_video(drive_token, clips_folder_id, bg_video)

        # 2. Drive'dan müzik indir
        print("\n[2/3] 🎵 Müzik indiriliyor...")
        music_dir = os.path.join(work_dir, "music")
        os.makedirs(music_dir, exist_ok=True)
        track_paths = drive_handler.download_random_tracks(
            drive_token,
            channel["drive_folder_id"],
            music_dir,
            track_count=1,
        )
        music_path = track_paths[0]

        # 3. Her short için döngü
        print(f"\n[3/3] 🎬 {count} shorts oluşturuluyor...")
        success = 0

        for i in range(count):
            print(f"\n   --- Short {i+1}/{count} ---")
            try:
                # Gemini'dan kısa metin üret
                short_text = gemini_handler.generate_short_text(
                    gemini_key, channel, prompts
                )

                short_output = os.path.join(work_dir, f"short_{i}.mp4")
                short_work = os.path.join(work_dir, f"work_{i}")

                # Short video oluştur
                shorts_creator.create_short(
                    channel_code=channel_code,
                    bg_video_path=bg_video,
                    music_clip_path=music_path,
                    text=short_text,
                    output_path=short_output,
                    work_dir=short_work,
                )

                # YouTube'a yükle (long_video_id yok, description'a sadece kanal adı)
                short_title = f"{short_text} | {channel['display_name']} #Shorts"
                short_desc = (
                    f"{channel['concept'].capitalize()} — "
                    f"Full 1-hour mixes on our channel.\n\n"
                    f"#shorts #youtubeshorts"
                )

               youtube_uploader.upload_short(
                    youtube_token_json=yt_token,
                    video_path=short_output,
                    title=short_title,
                    description=None,
                    tags=channel.get("video_keywords", []),
                    long_video_id=None,
                    expected_channel_id=channel["channel_id"],
                    channel_config=channel,
                )
            
                success += 1
                print(f"   ✅ Short {i+1} tamamlandı")

            except Exception as e:
                print(f"   ❌ Short {i+1} başarısız: {e}")
                print(traceback.format_exc())
                continue

        print(f"\n🎉 Tamamlandı: {success}/{count} shorts yüklendi")

    except Exception as e:
        print(f"\n❌ HATA: {e}")
        print(traceback.format_exc())
        raise

    finally:
        try:
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
                print(f"🧹 Geçici dosyalar temizlendi")
        except Exception as e:
            print(f"⚠️ Temizleme hatası: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python main_shorts.py <kanal_kodu> [adet]")
        print(f"Kanallar: {', '.join(CHANNELS.keys())}")
        sys.exit(1)

    channel_code = sys.argv[1].lower().strip()
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    run_shorts_pipeline(channel_code, count)
