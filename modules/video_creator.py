"""
FFmpeg ile final videoyu oluşturur (optimize edilmiş 2-aşamalı yöntem).
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


def _create_looped_background(background_video_path, target_duration, output_path):
    """
    Aşama 1: Arka plan videosunu hedef süreye kadar loop'la (codec değişmeden, hızlı).
    """
    print(f"   Aşama 1: Arka plan loop'lanıyor (~{target_duration/60:.1f} dk)...")
    
    bg_duration = get_video_duration(background_video_path)
    loop_count = int(target_duration / bg_duration) + 2
    
    # Concat dosyası oluştur (FFmpeg bu yolla çok hızlı loop yapar)
    concat_list = output_path + ".txt"
    with open(concat_list, "w") as f:
        for _ in range(loop_count):
            f.write(f"file '{os.path.abspath(background_video_path)}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",  # Codec değiştirme - çok hızlı
        "-t", str(target_duration + 5),
        output_path,
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    if os.path.exists(concat_list):
        os.remove(concat_list)
    
    return output_path


def _scale_and_combine(looped_bg, audio_path, output_path, target_duration):
    """
    Aşama 2: Loop'lanmış videoyu 1080p'ye scale et + ses ile birleştir.
    """
    print(f"   Aşama 2: Video encoding ve ses birleştirme...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", looped_bg,
        "-i", audio_path,
        "-t", str(target_duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "26",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24",
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
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    
    stderr_lines = []
    last_shown = ""
    for line in process.stderr:
        stderr_lines.append(line)
        if "time=" in line:
            time_part = line.split("time=")[1].split()[0]
            if time_part != last_shown:
                print(f"      Encoding: {time_part}", end="\r")
                last_shown = time_part
    
    process.wait()
    
    if process.returncode != 0:
        print("\n⚠️  FFmpeg hata verdi:")
        print("".join(stderr_lines[-20:]))
        raise Exception(f"FFmpeg encoding başarısız (kod: {process.returncode})")
    
    print()


def create_video(audio_path, background_video_path, output_path, target_duration_seconds):
    """
    Ses + arka plan videosunu 2-aşamalı yöntemle hızlıca birleştirir.
    """
    print(f"🎬 Video oluşturuluyor (optimize edilmiş)...")
    print(f"   Hedef süre: {target_duration_seconds/60:.1f} dakika")
    
    bg_duration = get_video_duration(background_video_path)
    print(f"   Arka plan video: {bg_duration:.1f} saniye")
    
    # Aşama 1: Hızlı loop
    looped_bg = output_path.replace(".mp4", "_looped.mp4")
    _create_looped_background(background_video_path, target_duration_seconds, looped_bg)
    
    # Aşama 2: Scale + ses
    _scale_and_combine(looped_bg, audio_path, output_path, target_duration_seconds)
    
    # Geçici dosyayı sil
    if os.path.exists(looped_bg):
        os.remove(looped_bg)
    
    if not os.path.exists(output_path):
        raise Exception("Çıkış dosyası oluşturulamadı")
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    actual_duration = get_video_duration(output_path)
    
    print(f"✅ Video hazır:")
    print(f"   Süre: {actual_duration/60:.2f} dakika")
    print(f"   Boyut: {file_size_mb:.1f} MB")
    
    return output_path
