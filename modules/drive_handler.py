"""
Google Drive'dan müzik dosyalarını indirir.
Her kanal için Drive klasöründen rastgele parçalar seçer.
"""
import os
import io
import json
import random
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def _get_drive_service(token_json_str):
    creds = service_account.Credentials.from_service_account_info(
        json.loads(token_json_str),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def list_audio_files(drive_token_json, folder_id):
    """Klasördeki tüm ses dosyalarını listeler."""
    service = _get_drive_service(drive_token_json)
    query = f"'{folder_id}' in parents and trashed = false"
    
    files = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageToken=page_token,
            pageSize=200,
        ).execute()
        
        for f in response.get("files", []):
            # Sadece ses dosyalarını al
            if f.get("mimeType", "").startswith("audio/") or \
               f["name"].lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
                files.append(f)
        
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    
    return files


def download_file(drive_token_json, file_id, file_name, output_dir):
    """Bir dosyayı Drive'dan indirir."""
    service = _get_drive_service(drive_token_json)
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, file_name)
    
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(output_path, mode="wb")
    downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.close()
    return output_path


def select_random_tracks(files, count):
    """Listeden rastgele 'count' kadar dosya seçer."""
    if len(files) <= count:
        return files.copy()
    return random.sample(files, count)


def download_random_tracks(drive_token_json, folder_id, output_dir, track_count=20):
    """
    Drive klasöründen rastgele parçalar indirir.
    track_count: indirilecek parça sayısı (1 saatlik video için 20-25 parça yeterli)
    Returns: indirilen dosya yollarının listesi
    """
    print(f"📁 Drive klasöründen dosyalar listeleniyor...")
    files = list_audio_files(drive_token_json, folder_id)
    print(f"   Toplam {len(files)} müzik dosyası bulundu")
    
    if not files:
        raise Exception(f"Klasör boş! folder_id: {folder_id}")
    
    selected = select_random_tracks(files, track_count)
    print(f"   {len(selected)} parça rastgele seçildi")
    
    downloaded_paths = []
    for i, f in enumerate(selected, 1):
        print(f"   [{i}/{len(selected)}] İndiriliyor: {f['name']}")
        path = download_file(drive_token_json, f["id"], f["name"], output_dir)
        downloaded_paths.append(path)
    
    return downloaded_paths

def list_video_files(drive_token_json, folder_id):
    """Drive klasöründen video dosyalarını listeler."""
    service = _get_drive_service(drive_token_json)
    
    files = []
    page_token = None
    
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces="drive",
            fields="nextPageToken, files(id, name, size)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        
        for f in response.get("files", []):
            if f["name"].lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                files.append(f)
        
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    
    return files


def download_random_video(drive_token_json, folder_id, output_path):
    """
    Drive klasöründen rastgele bir video indirir.
    output_path: tam dosya yolu (örn. /tmp/youtube-bot/coding/background.mp4)
    Returns: indirilen dosya yolu
    """
    print(f"📂 Drive'dan klip listesi alınıyor...")
    files = list_video_files(drive_token_json, folder_id)
    print(f"   Toplam {len(files)} klip bulundu")
    
    if not files:
        raise Exception("Drive klasöründe klip bulunamadı")
    
    # Rastgele bir tane seç
    selected = random.choice(files)
    file_size_mb = int(selected.get("size", 0)) / (1024 * 1024)
    print(f"   Seçilen: {selected['name']} ({file_size_mb:.1f} MB)")
    
    # Output dizinini garanti et
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Drive'dan indir
    service = _get_drive_service(drive_token_json)
    request = service.files().get_media(fileId=selected["id"])
    fh = io.FileIO(output_path, mode="wb")
    downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.close()
    
    print(f"✅ Klip indirildi: {output_path}")
    return output_path
