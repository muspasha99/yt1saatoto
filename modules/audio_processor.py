"""
Müzik dosyalarını crossfade ile birleştirir.
60 dakika geçince mevcut şarkıyı tamamlar ve durur (doğal bitiş).
"""
import os
import subprocess
import json
import random


def get_audio_duration(file_path):
    """Bir ses dosyasının süresini saniye cinsinden döndürür."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def select_tracks_for_duration(track_paths, min_duration_seconds):
    """
    Toplam süre min_duration'ı geçene kadar parça seçer.
    Son parça tam olarak çalınır (kesilmez), bu yüzden video genelde 60-65 dk arası olur.
    """
    random.shuffle(track_paths)
    
    selected = []
    total_duration = 0.0
    
    for path in track_paths:
        duration = get_audio_duration(path)
        selected.append((path, duration))
        total_duration += duration
        
        # Süre minimumu geçtiyse dur (son parça tamamlanacak)
        if total_duration >= min_duration_seconds:
            break
    
    # Eğer hala minimuma ulaşmadıysak (çok az parça varsa) baştan ekle
    if total_duration < min_duration_seconds:
        idx = 0
        while total_duration < min_duration_seconds and idx < len(track_paths) * 3:
            path = track_paths[idx % len(track_paths)]
            duration = get_audio_duration(path)
            selected.append((path, duration))
            total_duration += duration
            idx += 1
    
    return selected, total_duration


def crossfade_tracks(track_list, output_path, crossfade_seconds=4):
    """
    Parçaları crossfade ile birleştirir.
    track_list: [(path, duration), ...]
    """
    if len(track_list) == 0:
        raise Exception("Birleştirilecek parça yok!")
    
    if len(track_list) == 1:
        # Tek parça varsa kopyala
        cmd = [
            "ffmpeg", "-y", "-i", track_list[0][0],
            "-c:a", "pcm_s16le", output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return
    
    # FFmpeg complex filter ile crossfade
    inputs = []
    for path, _ in track_list:
        inputs.extend(["-i", path])
    
    # Filter graph oluştur: her parça arasında acrossfade
    filter_parts = []
    current_label = "[0:a]"
    
    for i in range(1, len(track_list)):
        next_label = f"[{i}:a]"
        if i == len(track_list) - 1:
            output_label = "[out]"
        else:
            output_label = f"[mix{i}]"
        
        filter_parts.append(
            f"{current_label}{next_label}acrossfade="
            f"d={crossfade_seconds}:c1=tri:c2=tri{output_label}"
        )
        current_label = output_label if i < len(track_list) - 1 else "[out]"
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        output_path,
    ]
    
    print(f"   FFmpeg crossfade çalışıyor ({len(track_list)} parça)...")
    subprocess.run(cmd, check=True, capture_output=True)


def normalize_audio(input_path, output_path):
    """Ses seviyesini normalize eder (loudnorm)."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "pcm_s16le",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def create_long_audio(track_paths, output_path, min_duration_seconds=3600, crossfade_seconds=4):
    """
    Ana fonksiyon: parçaları al, crossfade ile birleştir, normalize et.
    
    Returns: (output_path, total_duration) - oluşturulan dosya ve toplam süre
    """
    print(f"🎵 Müzik birleştirme başlıyor...")
    print(f"   Hedef minimum süre: {min_duration_seconds/60:.1f} dakika")
    print(f"   Crossfade: {crossfade_seconds} saniye")
    
    # Parçaları seç
    selected_tracks, total_duration = select_tracks_for_duration(
        track_paths, min_duration_seconds
    )
    
    print(f"   {len(selected_tracks)} parça seçildi")
    print(f"   Toplam ham süre: {total_duration/60:.1f} dakika")
    
    # Crossfade nedeniyle her birleşmede süre azalır
    actual_duration = total_duration - (crossfade_seconds * (len(selected_tracks) - 1))
    print(f"   Crossfade sonrası tahmini: {actual_duration/60:.1f} dakika")
    
    # Geçici dosya
    temp_combined = output_path.replace(".wav", "_combined.wav")
    
    # Birleştir
    crossfade_tracks(selected_tracks, temp_combined, crossfade_seconds)
    
    # Normalize et
    print(f"   Ses seviyesi normalize ediliyor...")
    normalize_audio(temp_combined, output_path)
    
    # Geçici dosyayı sil
    if os.path.exists(temp_combined):
        os.remove(temp_combined)
    
    # Gerçek süreyi al
    final_duration = get_audio_duration(output_path)
    print(f"✅ Müzik hazır: {final_duration/60:.1f} dakika ({final_duration:.0f} saniye)")
    
    return output_path, final_duration
