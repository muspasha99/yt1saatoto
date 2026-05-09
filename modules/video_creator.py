"""
FFmpeg ile final videoyu oluşturur.
Tek aşamada 1080p loop + scale + audio + encode.
"""
import os
import subprocess
import json


def get_video_duration(file_path):
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
    Tek aşamada 1080p video oluştur (hız öncelikli).
    """
    print(f"📽 Video oluşturuluyor (1080p, hızlı)...")
    print(f"   Hedef süre: {target_duration_seconds/60:.1f} dakika")
    
    bg_duration = get_video_duration(background_video_path)
    print(f"   Arka plan video: {bg_duration:.1f} saniye")
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", background_video_path,
        "-i", audio_path,
        "-t", str(target_duration_seconds),
        "-c:v", "libx264",
        "-preset", "superfast",          # veryfast → superfast (~%70 hız artışı)
        "-crf", "22",                     # 21 → 22 (gözle fark yok)
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r", "24",                       # 30 → 24 fps (cinematic, %20 az iş)
        "-threads", "0",                  # Tüm CPU çekirdekleri
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
    
    process = subprocess.Popen(
        cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
        universal_newlines=True, bufsize=1
    )
    
    stderr_lines = []
    last_shown = ""
    for line in process.stderr:
        stderr_lines.append(line)
        if "time=" in line:
            time_part = line.split("time=")[1].split(" ")[0]
            if time_part != last_shown:
                print(f"   Encoding: {time_part}", end="\r")
                last_shown = time_part
    
    process.wait()
    
    if process.returncode != 0:
        print("\n⚠ FFmpeg hata verdi:")
        print("".join(stderr_lines[-20:]))
        raise Exception(f"FFmpeg encoding başarısız (kod: {process.returncode})")
    
    print()
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    actual_duration = get_video_duration(output_path)
    
    print(f"✅ Video hazır:")
    print(f"   Süre: {actual_duration/60:.2f} dakika")
    print(f"   Boyut: {file_size_mb:.1f} MB")
    
    return output_path
