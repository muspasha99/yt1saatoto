"""
FFmpeg ile final videoyu oluşturur.
Arka plan videosunu loop'a alır, müzikle birleştirir.
"""
import os
import subprocess
import json


def get_video_duration(file_path):
    """Bir video dosyasının süresini saniye cinsinden döndürür."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def create_video(audio_path, background_video_path, output_path, target_duration_seconds):
    """
    Ses + arka plan videosunu birleştirir.
    
    audio_path: 1 saatlik birleşik müzik dosyası
    background_video_path: Pixabay'den indirilen kısa video (loop'a alınacak)
    output_path: Final MP4 yolu
    target_duration_seconds: Video süresi (audio'nun süresi)
    
    Returns: output_path
    """
    print(f"🎬 Video oluşturuluyor...")
    print(f"   Hedef süre: {target_duration_seconds/60:.1f} dakika")
    
    bg_duration = get_video_duration(background_video_path)
    print(f"   Arka plan video süresi: {bg_duration:.1f} saniye")
    print(f"   Loop sayısı: ~{int(target_duration_seconds / bg_duration) + 1}")
    
    # FFmpeg komutu:
    # -stream_loop -1: arka plan videosunu sonsuz loop'a al
    # -t: çıkış süresi (audio kadar)
    # -c:v libx264: H.264 codec
    # -preset veryfast: hızlı encoding (GitHub Actions süresini kısaltır)
    # -crf 23: kalite/boyut dengesi
    # -c:a aac -b:a 192k: ses codec
    # -shortest: en kısa stream'e göre kes
    # -pix_fmt yuv420p: maksimum uyumluluk
    # -movflags +faststart: YouTube için optimize
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", background_video_path,
        "-i", audio_path,
        "-t", str(target_duration_seconds),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-tune", "stillimage",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path,
    ]
    
    print(f"   FFmpeg encoding başlıyor (birkaç dakika sürebilir)...")
    
    # Stderr'i yakala ama hata olursa göster
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    
    stderr_output = []
    for line in process.stderr:
        stderr_output.append(line)
        # FFmpeg progress satırlarını yakala
        if "time=" in line:
            # Sadece son progress'i göster
            time_part = line.split("time=")[1].split()[0]
            print(f"      İşleniyor: {time_part}", end="\r")
    
    process.wait()
    
    if process.returncode != 0:
        print("\n⚠️  FFmpeg hata verdi:")
        print("".join(stderr_output[-30:]))
        raise Exception(f"FFmpeg encoding başarısız (kod: {process.returncode})")
    
    print()  # Progress satırından sonra newline
    
    if not os.path.exists(output_path):
        raise Exception("Çıkış dosyası oluşturulamadı")
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    actual_duration = get_video_duration(output_path)
    
    print(f"✅ Video hazır:")
    print(f"   Süre: {actual_duration/60:.2f} dakika")
    print(f"   Boyut: {file_size_mb:.1f} MB")
    
    return output_path
