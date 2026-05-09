"""
Kanal ayarları - tüm 8 kanalın yapılandırması burada.
"""

CHANNELS = {
    "coding": {
        "display_name": "Music for Coding and Focus",
        "channel_id": "UCkVKKmob42pgVahy7iN8dJg",
        "drive_folder_id": "1ZGDsj91rLyAn53QADHF-XB4nk63_VWYL",
        "clips_folder_id": "1WS1MCEihIQXlhldY2-CYodDpu2ls5hBb",
        "drive_account": "hesap98",
        "youtube_account": "hesap98",
        "concept": "lofi hip hop study music",
        "crossfade_seconds": 4,
        "video_keywords": ["lofi", "study music", "chill beats", "coding music", "focus music"],
    },
    "zen": {
        "display_name": "Zen Yoga Music",
        "channel_id": "UCwCgjS5hnrIcnbgDTT6w59Q",
        "drive_folder_id": "1bk6DFdWy0s_WCoIMBN_wfotFeBpTM9_2",
        "clips_folder_id": "12bTsKRMLJxQrF0XpvXL7gBpc8q3QJZ7d",
        "drive_account": "hesap98",
        "youtube_account": "hesap98",
        "concept": "zen meditation tibetan ambient",
        "crossfade_seconds": 8,
        "video_keywords": ["yoga music", "meditation", "zen", "tibetan", "peaceful music"],
    },
    "vault": {
        "display_name": "Millionaire Vault",
        "channel_id": "UCpMMN35Cp_DBCyoVJY1R3tw",
        "drive_folder_id": "1ysfqX-UsbTOqX8jE9AZJ1HEb0NNWMSOM",
        "clips_folder_id": "1CJWOvaDl4W-RH0sQBPJXvQ2kgi_iBwZT",
        "drive_account": "hesap97",
        "youtube_account": "hesap97",
        "concept": "dark cinematic trap motivational",
        "crossfade_seconds": 3,
        "video_keywords": ["motivation music", "dark trap", "sigma", "grindset", "hustle"],
    },
    "chakra": {
        "display_name": "Chakra Healing Meditation",
        "channel_id": "UCVnJG9DB4jYpv4PMSJvkuIA",
        "drive_folder_id": "1P7O2FBPApSXNjn3JjWzi_GlFDdAoDhYq",
        "clips_folder_id": "1y22dntgRRAtzwt5TP0Ag-w9knmlrmL2n",
        "drive_account": "hesap97",
        "youtube_account": "hesap97",
        "concept": "chakra healing solfeggio frequency",
        "crossfade_seconds": 10,
        "video_keywords": ["chakra healing", "432hz", "528hz", "meditation music", "sound healing"],
    },
    "beach": {
        "display_name": "Beach Club Beats",
        "channel_id": "UC9AcTTuosbZ17P0F0tfMg3g",
        "drive_folder_id": "1S0f5ojyNWHSb8K7RGkwBrcn1vxn1Jnco",
        "clips_folder_id": "1c11dVr0S_cEK5hlxIIQlf_fzor03Mq0O",
        "drive_account": "hesap99",
        "youtube_account": "hesap99",
        "concept": "tropical house beach club",
        "crossfade_seconds": 4,
        "video_keywords": ["beach music", "tropical house", "summer vibes", "ibiza", "deep house"],
    },
    "summer": {
        "display_name": "Summer House Music",
        "channel_id": "UC1w2S1apy3UK-pRaIEJBavA",
        "drive_folder_id": "15jR06ZQXUbUb3uk08BHEhwfsLrpr2yEh",
        "clips_folder_id": "1LiywuL07wnWcXM-C0vIwixnV5ztFfBsz",
        "drive_account": "hesap99",
        "youtube_account": "hesap99",
        "concept": "deep house summer mediterranean",
        "crossfade_seconds": 4,
        "video_keywords": ["deep house", "summer house", "mediterranean", "lounge", "chillout"],
    },
    "pets": {
        "display_name": "Relaxing Dogs and Cats",
        "channel_id": "UCyYCN2hqzJBSA9XNes1Shig",
        "drive_folder_id": "1eY8y0RDewp0lA5fjLuDuvZErOxUnUIW-",
        "clips_folder_id": "1r5YJxeY2s81BZJ-dAqbe8Y-0hgCFh_jf",
        "drive_account": "hesap87",
        "youtube_account": "hesap87",
        "concept": "soft acoustic for pets calm",
        "crossfade_seconds": 6,
        "video_keywords": ["dog music", "cat music", "pet relaxation", "calm pets", "anxiety music"],
    },
    "breathe": {
        "display_name": "Breathe and Chill",
        "channel_id": "UCqBZrQuzsfp8_sTRu97T3VA",
        "drive_folder_id": "1ivZr7goxS7VJpMwyLqwCkP1hcezievW-",
        "clips_folder_id": "17pRNXvwn2NXYHf9zX-g6fxRrwpSesO_N",
        "drive_account": "hesap87",
        "youtube_account": "hesap87",
        "concept": "breathing meditation 4-7-8",
        "crossfade_seconds": 8,
        "video_keywords": ["breathing exercise", "4-7-8 breathing", "meditation", "calm music", "anxiety relief"],
    },
}

# Video süresi - minimum 1 saat, doğal bitiş için son şarkı tamamlanır
MIN_VIDEO_DURATION_SECONDS = 3600  # 60 dk minimum

# Geçici dosya klasörü
TEMP_DIR = "/tmp/youtube-bot"

# Kanal bazlı başlık ve açıklama stilleri (Gemini için)
CHANNEL_PROMPTS = {
    "coding": {
        "title_style": "Cozy, chill, study-focused. 50-70 characters. Use emojis like 🎵☕🌧️🌙. Examples: 'Lofi Hip Hop Radio 🎵 Beats to Study/Code/Relax', 'Rainy Coffee Shop ☕ Chill Lofi for Deep Focus', 'Late Night Study Session 🌙 1 Hour Lofi Mix'",
        "description_style": "Warm and inviting. Mention studying, coding, focus, productivity. Include 2-3 keywords naturally. 3-4 sentences."
    },
    "zen": {
        "title_style": "Spiritual, peaceful, descriptive. 70-90 characters. Use emojis like 🕉️🧘🌸. Examples: 'Tibetan Healing Sounds 🕉️ Deep Yoga Meditation Music for Inner Peace', 'Zen Garden Meditation 🧘 Calming Tibetan Bowls for Stress Relief'",
        "description_style": "Spiritual and grounding. Mention yoga, meditation, mindfulness, healing. 4-5 sentences with peaceful tone."
    },
    "vault": {
        "title_style": "Aggressive, short, hard-hitting, 30-50 characters. Minimal emojis (🔥💰⚡). Examples: 'The grind never stops 🔥', 'millionaire mindset | sigma grindset', 'the day that make you different'",
        "description_style": "Short, punchy, motivational. Sigma/grindset language. 2-3 short sentences. Direct and intense."
    },
    "chakra": {
        "title_style": "Spiritual, frequency-focused, descriptive. 70-90 characters. Emojis like ✨🔮💫. Examples: '528 Hz Heart Chakra Healing ✨ Solfeggio Frequencies for Love & Balance', '432 Hz Deep Healing Meditation | Manifest Abundance & Clarity'",
        "description_style": "Mystical and healing tone. Mention specific chakras, frequencies (Hz), benefits. 4-5 sentences."
    },
    "beach": {
        "title_style": "Fun, summery, party energy. 50-70 characters. Emojis like 🌴☀️🏖️🍹. Examples: 'Tropical House Mix 🌴 Summer Beach Vibes 2026', 'Ibiza Sunset Sessions ☀️ Best Tropical House Hits'",
        "description_style": "Energetic and bright. Mention summer, beach, vacation, party. 3-4 upbeat sentences."
    },
    "summer": {
        "title_style": "Smooth, sophisticated, lounge feel. 50-70 characters. Emojis like 🌅🍸🌊. Examples: 'Deep House Sunset 🌅 Mediterranean Lounge Vibes', 'Summer Rooftop Sessions | Smooth Deep House Mix'",
        "description_style": "Refined and chill. Mediterranean, lounge, sunset, rooftop. 3-4 sophisticated sentences."
    },
    "pets": {
        "title_style": "Warm, caring, problem-solving. 60-80 characters. Emojis like 🐾🐶🐱. Examples: 'Music for Anxious Dogs 🐾 Calm Pets Music Home Alone', 'Soothing Music for Cats 🐱 Reduce Stress & Anxiety'",
        "description_style": "Caring and helpful tone. Mention pet anxiety, separation, calming, vet-recommended. 4-5 warm sentences."
    },
    "breathe": {
        "title_style": "Calm, sleep-focused, healing. 60-80 characters. Emojis like 😴💤🌙. Examples: '4-7-8 Breathing Music 😴 Deep Sleep & Anxiety Relief', 'Calm Breathing Meditation 🌙 Fall Asleep Fast'",
        "description_style": "Soft and reassuring. Mention sleep, anxiety, breathing techniques, relaxation. 4-5 gentle sentences."
    },
}
