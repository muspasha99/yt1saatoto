"""
Gemini API ile başlık, açıklama ve etiket üretir.
SEO odaklı + thumbnail görsel analizi.
"""
import os
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

    # Thumbnail varsa görsel bağlam ekle
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

    # İçerik listesi oluştur (resim varsa başa ekle)
    content_parts = []
    if has_image:
        img = PIL.Image.open(thumbnail_path)
        content_parts.append(img)
    content_parts.append(prompt)

    response = model.generate_content(content_parts)
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
