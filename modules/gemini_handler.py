"""
Gemini API ile başlık, açıklama ve etiket üretir.
SEO odaklı + thumbnail görsel analizi.
"""
import os
import time
import google.generativeai as genai
import PIL.Image
import json
import re
import random


def configure_gemini(api_key):
    genai.configure(api_key=api_key)


def _clean_json_response(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_gemini(model, content_parts, max_retries=3):
    """
    Gemini API çağrısı yapar. Rate limit (429) hatalarında bekleyip tekrar dener.
    """
    for attempt in range(max_retries):
        try:
            response = model.generate_content(content_parts)
            return response
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                print(f"   ⏳ Gemini rate limit, {wait} sn bekleniyor... (deneme {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                raise
    raise Exception("Gemini rate limit aşıldı, tüm denemeler başarısız")


def generate_metadata(api_key, channel_config, channel_prompts, thumbnail_path=None):
    """
    SEO odaklı metadata üretir. thumbnail_path verilirse
    Gemini görüntüyü de analiz eder, görsel uyumlu başlık yazar.
    """
    configure_gemini(api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    seo_keywords = channel_config.get("seo_keywords", [])

    if not seo_keywords:
        raise Exception(
            f"❌ '{display_name}' için seo_keywords boş. config.py'ı güncelle."
        )

    primary_keyword = random.choice(seo_keywords)
    title_style = channel_prompts["title_style"]
    description_style = channel_prompts["description_style"]

    has_image = thumbnail_path and os.path.exists(thumbnail_path)
    if has_image:
        image_instruction = """
You are also shown the thumbnail image for this video (see above).
Use the visual mood, setting, colors, and atmosphere you observe in the thumbnail
to make the title feel VISUALLY COHERENT.
The viewer should see the thumbnail and immediately feel the title matches it.
Do NOT describe the image literally — let the visual context inform the mood and
any descriptive modifiers you add (e.g., if it looks like deep ocean, "deep" feels natural).
"""
    else:
        image_instruction = ""

    prompt = f"""You are a YouTube SEO expert generating metadata for a 1-hour music video.
{image_instruction}
Channel: {display_name}
Concept: {concept}
PRIMARY SEO KEYWORD (optimize for this): "{primary_keyword}"

=== TITLE REQUIREMENTS (CRITICAL) ===
- PRIMARY KEYWORD must appear at the START of the title (front-loading)
- Add 1-2 modifier words after that naturally fit both the keyword AND the thumbnail visual
- ONE emoji near the end (optional)
- 50-90 characters total
- Must NOT be identical to the channel name
- Style/tone notes: {title_style}

=== DESCRIPTION REQUIREMENTS ===
- First sentence MUST contain the PRIMARY KEYWORD or close variant
- First 150 characters are most important (mobile preview)
- 3-5 sentences total
- NO "Subscribe!" calls, NO external links
- Style/tone notes: {description_style}
- At the very END of description, add exactly 3-5 hashtags like: #lofi #studymusic #relaxing
- Hashtags must match the primary keyword and niche
- Hashtags go on a new line at the end

=== TAGS REQUIREMENTS ===
- 12-15 tags total
- First tag = exact PRIMARY KEYWORD: "{primary_keyword}"
- Next 3-4 = close variations of primary keyword
- Then 4-5 long-tail related tags (3+ words each)
- Then 3-4 broad niche tags (2-3 words)
- All lowercase, no special characters
- NO single-word tags

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "title": "...",
  "description": "...",
  "tags": ["tag1", "tag2", ...]
}}
"""

    print(f"🤖 Gemini ile metadata üretiliyor: {display_name}")
    print(f"   🎯 SEO keyword: '{primary_keyword}'")
    if has_image:
        print(f"   🖼️  Thumbnail görsel analizi aktif")

    content_parts = []
    if has_image:
        img = PIL.Image.open(thumbnail_path)
        content_parts.append(img)
    content_parts.append(prompt)

    response = _call_gemini(model, content_parts)
    raw_text = response.text
    cleaned = _clean_json_response(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️  Gemini parse hatası:\n{raw_text}")
        raise Exception(f"Gemini JSON hatası: {e}")

    if not all(k in data for k in ["title", "description", "tags"]):
        raise Exception(f"Gemini eksik alan döndürdü: {data}")

    # YouTube limitleri
    if len(data["title"]) > 100:
        data["title"] = data["title"][:97] + "..."
    if len(data["description"]) > 5000:
        data["description"] = data["description"][:4997] + "..."

    # Hashtagler description'da yoksa otomatik ekle
    desc = data["description"]
    if "#" not in desc:
        hashtags = " ".join(f"#{tag.replace(' ', '')}" for tag in data["tags"][:5])
        data["description"] = desc.strip() + f"\n\n{hashtags}"

    tags = data["tags"]
    while len(",".join(tags)) > 500 and len(tags) > 5:
        tags.pop()
    data["tags"] = tags

    print(f"   ✓ Başlık: {data['title']}")
    print(f"   ✓ Açıklama: {len(data['description'])} karakter")
    print(f"   ✓ Etiket: {len(data['tags'])} adet")

    return data


def generate_short_text(api_key, channel_config, channel_prompts):
    """
    Shorts videosu için kısa, anlamlı bir cümle üretir.
    Max 30 karakter. Her seferinde farklı çıkar.
    """
    configure_gemini(api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    display_name = channel_config["display_name"]
    concept = channel_config["concept"]
    short_sentences = channel_config.get("short_sentences", [])
    short_quotes = channel_config.get("short_quotes", [])

    prompt = f"""You are writing overlay text for a YouTube Shorts video.

Channel: {display_name}
Concept: {concept}

Reference sentences for this channel's vibe:
{chr(10).join(f'- {s}' for s in short_sentences[:8])}

Reference quotes:
{chr(10).join(f'- {q}' for q in short_quotes[:4])}

Your task:
- Write ONE short text to display on screen
- MAX 30 characters (count carefully)
- Can be an original sentence OR a short famous quote
- Must match the channel's vibe and concept
- No hashtags, no emojis
- Every time you are called, produce something DIFFERENT
- Do NOT repeat the reference sentences word for word — draw inspiration

Respond ONLY with the text itself. No quotes, no explanation, nothing else.
Example good outputs:
- "Lock in. No excuses."
- "Breathe. Just breathe."
- "Stars made you. Relax."
- "Deep work. Deep life."
"""

    # Short'lar arası 15 saniye bekle (rate limit önlemi)
    print(f"   ⏳ Rate limit önlemi: 15 sn bekleniyor...")
    time.sleep(15)

    response = _call_gemini(model, [prompt])
    text = response.text.strip().strip('"').strip("'")

    if len(text) > 30:
        text = text[:30].rsplit(" ", 1)[0]

    print(f"   ✏️  Short text: '{text}' ({len(text)} karakter)")
    return text
