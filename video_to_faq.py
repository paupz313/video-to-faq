# @title 🎬 Video → FAQ article generator
# @markdown Turn a screen-recording (MP4) of a product walkthrough into a help-center FAQ article, with GIFs cut at the key steps.
# @markdown
# @markdown **How to use:** fill in the fields below, then click ▶️. You'll be asked to upload an MP4, and a ZIP (HTML article + GIFs) downloads at the end.
# @markdown
# @markdown **API key:** add a Colab secret named `GEMINI_API_KEY` (🔑 icon in the left sidebar), or paste it when prompted.

COMPANY_NAME = "Acme"  # @param {type:"string"}
LANGUAGE = "English"  # @param ["English", "French", "Spanish", "German", "Italian", "Dutch"]
ADDRESS_READER_FORMALLY = True  # @param {type:"boolean"}
MODEL = "gemini-3.5-flash"  # @param {type:"string"}
GIF_WIDTH_PX = 600  # @param {type:"integer"}

import getpass
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata

print("🔄 Installing dependencies...")
subprocess.run(["pip", "install", "-q", "-U", "google-genai"], check=False)
if shutil.which("ffmpeg") is None:
    subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=False)

from google import genai
from google.genai import types
from google.colab import files, userdata

TIMESTAMP_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?(\.\d+)?$")


def slugify(text, max_len=50):
    """Lowercase ASCII slug, safe for file names."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return text[:max_len] or "faq"


def get_api_key():
    for name in ("GEMINI_API_KEY",):
        try:
            key = userdata.get(name)
            if key:
                print("✅ API key found in Colab secrets.")
                return key
        except Exception:
            pass
    print("🔑 No GEMINI_API_KEY secret found.")
    return getpass.getpass("Paste your Gemini API key: ").strip()


def build_prompt():
    register = "formal (e.g. 'vous' in French)" if ADDRESS_READER_FORMALLY else "informal and friendly"
    return f"""
You are a customer support expert at {COMPANY_NAME}.
Task: turn this product walkthrough video into a help-center FAQ article written in {LANGUAGE}.

Two goals:
1. Human readability: reassuring, clear tone, {register} register.
2. Machine readability (chatbots, AI search): strict, predictable structure.

Writing rules:
- Short, direct sentences (subject + verb + object).
- Always use the exact same name for each interface element (e.g. always "Save button").
- No ambiguity.
- Strict hierarchy: H1 > H2 > UL > LI.

HTML rules:
- No CSS, no <html> or <body> tags.
- Only <h1>, <h2>, <p>, <ul>, <li>, <strong>.
- Insert GIF placeholders as [[GIF_1]], [[GIF_2]], ...

GIF rules:
- Pick the visually complex actions worth showing.
- Give each a precise slug (e.g. "click_export_menu").
- Timestamps in MM:SS.

Return JSON only:
{{
  "html_content": "<h1>Title</h1><p>Short context...</p><h2>Step 1: Action</h2><ul><li>Click...</li></ul><p>[[GIF_1]]</p>...",
  "gifs": [{{"id": "[[GIF_1]]", "start": "00:00", "end": "00:05", "slug": "precise_action"}}]
}}
"""


def make_gif(video_path, start, end, output_path):
    vf = f"fps=10,scale={GIF_WIDTH_PX}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", video_path, "-ss", start, "-to", end, "-vf", vf, output_path],
        check=True,
    )


def run_tool():
    key = get_api_key()
    if not key:
        print("❌ No API key, stopping.")
        return
    client = genai.Client(api_key=key)

    print("\n⬇️ Choose your MP4 file:")
    uploaded = files.upload()
    if not uploaded:
        print("No file received.")
        return

    original_name = next(iter(uploaded))
    video_path = "video_input.mp4"
    os.replace(original_name, video_path)
    base_name = slugify(os.path.splitext(original_name)[0])

    work_dir = "faq_export"
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir)

    video_file = None
    try:
        print("☁️ Uploading video to Gemini", end="")
        video_file = client.files.upload(file=video_path)
        while video_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)
        if video_file.state.name == "FAILED":
            print("\n❌ Gemini could not process the video.")
            return
        print(" ready.")

        print(f"✍️  Writing the article with {MODEL}...")
        response = client.models.generate_content(
            model=MODEL,
            contents=[video_file, build_prompt()],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(response.text)
        html_content = data["html_content"]
        gifs = data.get("gifs", [])

        print(f"\n🎬 Cutting {len(gifs)} GIF(s)...")
        for i, gif in enumerate(gifs, start=1):
            start, end = str(gif.get("start", "")), str(gif.get("end", ""))
            if not (TIMESTAMP_RE.match(start) and TIMESTAMP_RE.match(end)):
                print(f"   ⚠️ Skipping GIF {i}: invalid timestamps {start!r} → {end!r}")
                continue
            gif_name = f"{i}_{slugify(gif.get('slug', 'step'))}.gif"
            print(f"   -> {gif_name}")
            make_gif(video_path, start, end, os.path.join(work_dir, gif_name))
            placeholder = (
                '<div style="background:#fff3cd;border:1px solid #ffeeba;color:#856404;'
                'padding:15px;margin:15px 0;border-radius:4px;font-weight:bold;text-align:center;">'
                f"📥 DROP GIF HERE: {gif_name}</div>"
            )
            html_content = html_content.replace(gif.get("id", f"[[GIF_{i}]]"), placeholder)

        html_path = os.path.join(work_dir, f"{base_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(
                "<html><head><meta charset='utf-8'><style>"
                "body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6;color:#333}"
                "img{max-width:100%;border:1px solid #ddd}</style></head><body>"
                f"{html_content}</body></html>"
            )

        zip_path = shutil.make_archive(f"{base_name}_faq", "zip", work_dir)
        files.download(zip_path)
        print("\n✅ Done! Your ZIP is downloading.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if video_file is not None:
            try:
                client.files.delete(name=video_file.name)
            except Exception:
                pass
        for path in (video_path,):
            if os.path.exists(path):
                os.remove(path)
        shutil.rmtree(work_dir, ignore_errors=True)


run_tool()
