"""
Kanal ayarları - tüm 8 kanalın yapılandırması burada.
"""

CHANNELS = {
    "coding": {
        "display_name": "Music for Coding and Focus",
        "channel_id": "UCkVKKmob42pgVahy7iN8dJg",
        "drive_folder_id": "1ZGDsj91rLyAn53QADHF-XB4nk63_VWYL",
        "drive_account": "hesap98",
        "youtube_account": "hesap98",
        "concept": "lofi hip hop study music",
        "pixabay_query": "rainy night window cozy",
        "crossfade_seconds": 4,
        "thumbnail_text": "LOFI STUDY",
        "video_keywords": ["lofi", "study music", "chill beats", "coding music", "focus music"],
    },
    "zen": {
        "display_name": "Zen Yoga Music",
        "channel_id": "UCwCgjS5hnrIcnbgDTT6w59Q",
        "drive_folder_id": "1bk6DFdWy0s_WCoIMBN_wfotFeBpTM9_2",
        "drive_account": "hesap98",
        "youtube_account": "hesap98",
        "concept": "zen meditation tibetan ambient",
        "pixabay_query": "zen garden japanese peaceful",
        "crossfade_seconds": 8,
        "thumbnail_text": "ZEN YOGA",
        "video_keywords": ["yoga music", "meditation", "zen", "tibetan", "peaceful music"],
    },
    "vault": {
        "display_name": "Millionaire Vault",
        "channel_id": "UCpMMN35Cp_DBCyoVJY1R3tw",
        "drive_folder_id": "1ysfqX-UsbTOqX8jE9AZJ1HEb0NNWMSOM",
        "drive_account": "hesap97",
        "youtube_account": "hesap97",
        "concept": "dark cinematic trap motivational",
        "pixabay_query": "luxury city night skyline",
        "crossfade_seconds": 3,
        "thumbnail_text": "MILLIONAIRE",
        "video_keywords": ["motivation music", "dark trap", "sigma", "grindset", "hustle"],
    },
    "chakra": {
        "display_name": "Chakra Healing Meditation",
        "channel_id": "UCVnJG9DB4jYpv4PMSJvkuIA",
        "drive_folder_id": "1P7O2FBPApSXNjn3JjWzi_GlFDdAoDhYq",
        "drive_account": "hesap97",
        "youtube_account": "hesap97",
        "concept": "chakra healing solfeggio frequency",
        "pixabay_query": "spiritual energy crystal mandala",
        "crossfade_seconds": 10,
        "thumbnail_text": "CHAKRA HEALING",
        "video_keywords": ["chakra healing", "432hz", "528hz", "meditation music", "sound healing"],
    },
    "beach": {
        "display_name": "Beach Club Beats",
        "channel_id": "UC9AcTTuosbZ17P0F0tfMg3g",
        "drive_folder_id": "1S0f5ojyNWHSb8K7RGkwBrcn1vxn1Jnco",
        "drive_account": "hesap99",
        "youtube_account": "hesap99",
        "concept": "tropical house beach club",
        "pixabay_query": "tropical beach palm sunset",
        "crossfade_seconds": 4,
        "thumbnail_text": "BEACH CLUB",
        "video_keywords": ["beach music", "tropical house", "summer vibes", "ibiza", "deep house"],
    },
    "summer": {
        "display_name": "Summer House Music",
        "channel_id": "UC1w2S1apy3UK-pRaIEJBavA",
        "drive_folder_id": "15jR06ZQXUbUb3uk08BHEhwfsLrpr2yEh",
        "drive_account": "hesap99",
        "youtube_account": "hesap99",
        "concept": "deep house summer mediterranean",
        "pixabay_query": "mediterranean sunset coast",
        "crossfade_seconds": 4,
        "thumbnail_text": "SUMMER HOUSE",
        "video_keywords": ["deep house", "summer house", "mediterranean", "lounge", "chillout"],
    },
    "pets": {
        "display_name": "Relaxing Dogs and Cats",
        "channel_id": "UCyYCN2hqzJBSA9XNes1Shig",
        "drive_folder_id": "1eY8y0RDewp0lA5fjLuDuvZErOxUnUIW-",
        "drive_account": "hesap87",
        "youtube_account": "hesap87",
        "concept": "soft acoustic for pets calm",
        "pixabay_query": "cozy home cat dog window",
        "crossfade_seconds": 6,
        "thumbnail_text": "PET RELAX",
        "video_keywords": ["dog music", "cat music", "pet relaxation", "calm pets", "anxiety music"],
    },
    "breathe": {
        "display_name": "Breathe and Chill",
        "channel_id": "UCqBZrQuzsfp8_sTRu97T3VA",
        "drive_folder_id": "1ivZr7goxS7VJpMwyLqwCkP1hcezievW-",
        "drive_account": "hesap87",
        "youtube_account": "hesap87",
        "concept": "breathing meditation 4-7-8",
        "pixabay_query": "calm ocean waves gentle",
        "crossfade_seconds": 8,
        "thumbnail_text": "BREATHE",
        "video_keywords": ["breathing exercise", "4-7-8 breathing", "meditation", "calm music", "anxiety relief"],
    },
}

# Video süresi - minimum 1 saat, doğal bitiş için son şarkı tamamlanır
MIN_VIDEO_DURATION_SECONDS = 3600  # 60 dk minimum
# Pipeline kuralı: süre 60 dk'yi geçtiğinde mevcut şarkı tamamlanır,
# sonra video biter. Böylece her video doğal bir noktada sonlanır.
# Tipik sonuç: 60-65 dk arası, her video farklı.

# Geçici dosya klasörü
TEMP_DIR = "/tmp/youtube-bot"
