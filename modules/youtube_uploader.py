"""
YouTube Data API v3 ile video yükler.
Token JSON kullanarak ilgili kanala yükleme yapar.
"""
import os
import json
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def _get_youtube_service(token_json_str):
    """YouTube token'ı kullanarak YouTube servisini başlatır."""
    token_data = json.loads(token_json_str)
    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data["refresh_token"],
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(youtube_token_json, video_path, title, description, tags, expected_channel_id=None):
    """
    Bir videoyu YouTube'a yükler.
    
    Returns: {"video_id": "xxx", "url": "https://youtu.be/xxx"}
    """
    service = _get_youtube_service(youtube_token_json)
    
    # Doğrulama: token doğru kanal için mi?
    if expected_channel_id:
        channels = service.channels().list(part="id", mine=True).execute()
        actual_id = channels["items"][0]["id"]
        if actual_id != expected_channel_id:
            raise Exception(
                f"Token yanlış kanala ait! Beklenen: {expected_channel_id}, gelen: {actual_id}"
            )
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "10",  # Music kategorisi
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    
    media = MediaFileUpload(
        video_path,
        chunksize=10 * 1024 * 1024,
        resumable=True,
        mimetype="video/mp4",
    )
    
    print(f"📤 YouTube'a yükleniyor: {title}")
    print(f"   Dosya boyutu: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    
    request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )
    
    response = None
    last_progress = -1
    retry_count = 0
    max_retries = 3
    
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                if progress != last_progress:
                    print(f"   Yükleniyor: %{progress}", end="\r")
                    last_progress = progress
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                retry_count += 1
                wait = 2 ** retry_count
                print(f"\n   Geçici hata, {wait} sn sonra tekrar... ({retry_count}/{max_retries})")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if retry_count < max_retries:
                retry_count += 1
                wait = 2 ** retry_count
                print(f"\n   Hata oldu, {wait} sn sonra tekrar... ({retry_count}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    
    print()  # progress satırından sonra newline
    
    video_id = response["id"]
    print(f"✅ Video yüklendi: https://youtu.be/{video_id}")
    
    return {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}",
    }


def upload_thumbnail(youtube_token_json, video_id, thumbnail_path):
    """Yüklenmiş videoya thumbnail ekler."""
    service = _get_youtube_service(youtube_token_json)
    
    print(f"🖼️  Thumbnail yükleniyor...")
    
    media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
    
    request = service.thumbnails().set(
        videoId=video_id,
        media_body=media,
    )
    
    request.execute()
    print(f"✅ Thumbnail eklendi")


def upload_complete(youtube_token_json, video_path, thumbnail_path, title, description, tags, expected_channel_id=None):
    """
    Video + thumbnail'i tek seferde yükler.
    Returns: {"video_id": "...", "url": "..."}
    """
    result = upload_video(
        youtube_token_json,
        video_path,
        title,
        description,
        tags,
        expected_channel_id,
    )
    
    # Thumbnail yüklemeden önce kısa bekle (YouTube hazır olsun)
    time.sleep(3)
    
    try:
        upload_thumbnail(youtube_token_json, result["video_id"], thumbnail_path)
    except Exception as e:
        print(f"⚠️  Thumbnail yüklenemedi (video yüklendi ama): {e}")

def upload_short(youtube_token_json, video_path, title, description,
                 tags, long_video_id=None, expected_channel_id=None,
                 channel_config=None, scheduled_at=None):

    # Açıklama oluştur
    desc_parts = []

    if long_video_id:
        long_video_url = f"https://youtube.com/watch?v={long_video_id}"
        desc_parts.append(f"🎵 Full 1-Hour Version ↓\n{long_video_url}")

    if channel_config:
        display_name = channel_config.get("display_name", "")
        concept = channel_config.get("concept", "")
        desc_parts.append(
            f"🎧 {display_name}\n"
            f"{concept.capitalize()} — full 1-hour mixes on our channel.\n"
            f"Subscribe for daily music."
        )
    elif description:
        desc_parts.append(description)

    video_keywords = channel_config.get("video_keywords", []) if channel_config else []
    hashtags = " ".join(f"#{kw.replace(' ', '')}" for kw in video_keywords[:5])
    desc_parts.append(f"#shorts #youtubeshorts {hashtags}")

    full_description = "\n\n".join(desc_parts)

    if "#Shorts" not in title and "#shorts" not in title:
        title = title + " #Shorts"

    shorts_tags = ["shorts", "youtubeshorts"] + (tags or [])

    # Scheduled mi yoksa hemen mi?
    if scheduled_at:
        privacy_status = "private"
        publish_at = scheduled_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        privacy_status = "public"
        publish_at = None

    service = _get_youtube_service(youtube_token_json)

    body = {
        "snippet": {
            "title": title,
            "description": full_description,
            "tags": shorts_tags,
            "categoryId": "10",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Scheduled ise publishAt ekle
    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(
        video_path,
        chunksize=10 * 1024 * 1024,
        resumable=True,
        mimetype="video/mp4",
    )

    print(f"📤 Short yükleniyor: {title}")
    request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    last_progress = -1
    retry_count = 0
    max_retries = 3

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                if progress != last_progress:
                    print(f"   Yükleniyor: %{progress}", end="\r")
                    last_progress = progress
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504] and retry_count < max_retries:
                retry_count += 1
                wait = 2 ** retry_count
                print(f"\n   Geçici hata, {wait} sn sonra tekrar...")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if retry_count < max_retries:
                retry_count += 1
                wait = 2 ** retry_count
                time.sleep(wait)
                continue
            raise

    print()
    video_id = response["id"]
    print(f"✅ Short yüklendi: https://youtu.be/{video_id}")

    return {"video_id": video_id, "url": f"https://youtu.be/{video_id}"}
    
    return result
