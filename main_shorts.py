"""
Bağımsız Shorts pipeline.
- Drive'dan klip + müzik çeker
- 3 short oluşturur
- Kanalın en son uzun videosunu description'a ekler
- 8 saat arayla scheduled yayınlar
Kullanım: python main_shorts.py <kanal_kodu> <adet>
Örnek: python main_shorts.py vault 3
"""
import os
import sys
import shutil
import traceback
from datetime import datetime, timezone, timedelta

from config import CHANNELS, CHANNEL_PROMPTS, TEMP_DIR
from modules import drive_handler, gemini_handler, shorts_creator, youtube_uploader


def _get_env(key):
    val = os.environ.get(key)
    if not val:
        raise Exception(f"Ortam değişkeni eksik: {key}")
    return val


def _scheduled_times(count, interval_hours=8):
    """
    Şu andan itibaren count adet yayın zamanı üretir.
    İlk video 10 dakika sonra, sonraki her video 8 saat sonra.
    """
    now = datetime.now(timezone.utc)
    times = []
    for i in range(count):
        publish_at = now + timedelta(minutes=10) + timedelta(hours=i * interval_hours)
        times.append(publish_at)
    return times


def run_shorts_pipeline(channel_code, count=3):
    if channel_code not in CHANNELS:
        raise Exception(f"Bilinmeyen kanal: {channel_code}")

    channel = CHANNELS[channel_code]
    prompts = CHANNEL_PROMPTS[channel_code]

    print("=" * 60)
    print(f"🎬 SHORTS PIPELINE: {channel['display_name']}")
    print(f"   Adet: {count} | Aralık: 8 saat")
    print(f"   Zaman: {datetime.now().isoformat()}")
    print("=" * 60)

    publish_times = _scheduled_times(count, interval_hours=8)
    for i, t in enumerate(publish_times):
        print(f"   Short {i+1} → {t.strftime('%Y-%m-%d %H:%M UTC')}")

    work_dir = os.path.join(TEMP_DIR, f"{channel_code}_shorts")
    os.makedirs(work_dir, exist_ok=True)

    try:
        gemini_key = _get_env("GEMINI_API_KEY")
        drive_account = channel["drive_account"]
        drive_token = _get_env(f"DRIVE_TOKEN_{drive_account.upper()}")
        yt_token = _get_env(f"YT_TOKEN_{channel_code.upper()}")

        clips_folder_id = channel.get("clips_folder_id", "")
        if not clips_folder_id:
            raise Exception(f"clips_folder_id eksik: {channel_code}")

        # Kanalın en son uzun videosunu al
        print("\n[1/3] 📺 Son uzun video aranıyor...")
        try:
            long_video_id = youtube_uploader.get_latest_video_id(
                yt_token,
                expected_channel_id=channel["channel_id"],
            )
            if long_video_id:
                print(f"   ✅ Uzun video bulundu: https://youtu.be/{long_video_id}")
            else:
                print(f"   ⚠️ Uzun video bulunamadı, link eklenmeyecek")
        except Exception as e:
            print(f"   ⚠️ Uzun video alınamadı: {e}")
            long_video_id = None

        # Müzik indir
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

        print(f"\n[3/3] 🎞 Klipler + videolar oluşturuluyor ({count} adet)...")
        success = 0

        for i in range(count):
            print(f"\n   --- Short {i+1}/{count} ---")
            try:
                # Her short için farklı klip indir
                short_bg = os.path.join(work_dir, f"bg_{i}.mp4")
                print(f"   📥 Klip indiriliyor...")
                drive_handler.download_random_video(
                    drive_token,
                    clips_folder_id,
                    short_bg,
                )

                # Gemini'dan kısa metin üret
                short_text = gemini_handler.generate_short_text(
                    gemini_key, channel, prompts
                )

                short_output = os.path.join(work_dir, f"short_{i}.mp4")
                short_work = os.path.join(work_dir, f"work_{i}")

                # Short video oluştur
                shorts_creator.create_short(
                    channel_code=channel_code,
                    bg_video_path=short_bg,
                    music_clip_path=music_path,
                    text=short_text,
                    output_path=short_output,
                    work_dir=short_work,
                )

                # YouTube'a scheduled olarak yükle
                short_title = f"{short_text} | {channel['display_name']}"
                publish_at = publish_times[i]

                print(f"   📤 Yükleniyor → yayın: {publish_at.strftime('%Y-%m-%d %H:%M UTC')}")

                youtube_uploader.upload_short(
                    youtube_token_json=yt_token,
                    video_path=short_output,
                    title=short_title,
                    description=None,
                    tags=channel.get("video_keywords", []),
                    long_video_id=long_video_id,
                    expected_channel_id=channel["channel_id"],
                    channel_config=channel,
                    scheduled_at=publish_at,
                )

                success += 1
                print(f"   ✅ Short {i+1} yüklendi → {publish_at.strftime('%Y-%m-%d %H:%M UTC')}")

            except Exception as e:
                print(f"   ❌ Short {i+1} başarısız: {e}")
                print(traceback.format_exc())
                continue

        print(f"\n🎉 Tamamlandı: {success}/{count} shorts zamanlandı")

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
