import streamlit as st
from dotenv import load_dotenv
import os
import re
import base64
import json
import time

load_dotenv()

from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

# ── PAGE CONFIG ─────────────────────────────────────
st.set_page_config(page_title="NoteTube AI", page_icon="🎬", layout="wide")

# ── LOAD BG IMAGE (with fallback) ───────────────────
def get_base64_image(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_path = "IMGs/BG.jpg"
b64 = get_base64_image(img_path)

# ── HANDLE PAGE NAVIGATION VIA QUERY PARAMS ──────────
if "page" not in st.session_state:
    query_params = st.query_params
    st.session_state.page = query_params.get("page", "home")

def set_page(page_name):
    st.session_state.page = page_name
    st.query_params["page"] = page_name
    st.rerun()

# ── CSS with HEADER NAVIGATION ───────────────────────
bg_style = f'url("data:image/png;base64,{b64}")' if b64 else "linear-gradient(135deg, #0f172a, #1e1b2e)"

st.markdown(f"""
<style>
/* Hide Streamlit's default top bar */
header[data-testid="stHeader"] {{
    display: none;
}}

/* BACKGROUND */
.stApp {{
    background: linear-gradient(rgba(2,8,20,0.78), rgba(2,8,20,0.85)),
                {bg_style};
    background-size: cover;
    background-position: center;
}}

[data-testid="stAppViewContainer"],
section.main > div {{
    background: transparent !important;
}}

/* FIXED GLASS HEADER with navigation */
.site-header {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 5%;
    background: rgba(2, 8, 20, 0.85);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255,255,255,0.2);
    box-shadow: 0 2px 12px rgba(0,0,0,0.6), 0 0 10px rgba(255,0,60,0.15);
    z-index: 999999;
}}

.logo {{
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}}

.logo span {{
    color: #ff2a3d;
}}

/* Navigation links container */
.nav-links {{
    display: flex;
    gap: 2rem;
}}

.nav-link {{
    color: rgba(255,255,255,0.8);
    text-decoration: none;
    font-size: 16px;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: 6px;
    transition: all 0.2s;
    cursor: pointer;
}}

.nav-link:hover {{
    background: rgba(255,255,255,0.1);
    color: #ff2a3d;
}}

.nav-link.active {{
    background: rgba(255,42,61,0.2);
    color: #ff2a3d;
    border-bottom: 2px solid #ff2a3d;
}}

/* Main content padding */
.block-container {{
    padding-top: 80px !important;
    padding-left: 5% !important;
    padding-right: 5% !important;
}}

/* VERTICAL DIVIDER between input and output columns (kept) */
[data-testid="column"]:first-child {{
    position: relative;
    padding-right: 2rem;
}}
[data-testid="column"]:first-child::after {{
    content: "";
    position: absolute;
    top: 5%;
    right: -1px;
    width: 3px;
    height: 90%;
    background: linear-gradient(to bottom, transparent, #ff2a3d, #ff2a3d, transparent);
    box-shadow: 0 0 8px #ff2a3d, 0 0 18px rgba(255,0,60,0.7);
    border-radius: 2px;
}}
[data-testid="column"]:last-child {{
    padding-left: 2rem;
}}

/* Glass cards for columns */
[data-testid="column"] {{
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 18px;
    backdrop-filter: blur(6px);
}}

/* Headings */
h1 {{
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #ffffff, #ff2a3d);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* Input */
input {{
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
}}

/* Buttons */
.stButton button {{
    background: linear-gradient(135deg,#0ea5e9,#0284c7);
    color: white;
    border-radius: 8px;
    border: none;
    padding: 0.5rem 1rem;
}}

/* Notes box */
.notes-box {{
    background: rgba(255,255,255,0.06);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-top: 1rem;
    white-space: pre-wrap;
}}

/* Action buttons (Copy/Download) */
.action-buttons {{
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
}}
.act-btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 1px solid rgba(255, 42, 61, 0.6);
    background: rgba(255, 42, 61, 0.15);
    color: white;
    padding: 8px 18px;
    border-radius: 8px;
    text-decoration: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all 0.25s ease;
    box-shadow: 0 0 8px rgba(255, 42, 61, 0.2);
    text-decoration: none !important;
    color: white !important;
}}
.act-btn:hover {{
    background: rgba(255, 42, 61, 0.35);
    border-color: #ff2a3d;
    box-shadow: 0 0 16px rgba(255, 42, 61, 0.5);
    transform: translateY(-1px);
    text-decoration: none !important;
    color: white !important;
}}
a.act-btn,
a.act-btn:hover,
a.act-btn:visited,
a.act-btn:active {{
    text-decoration: none !important;
    color: white !important;
}}
/* Footer */
.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    text-align: center;
    padding: 12px;
    color: rgba(255,255,255,0.6);
    font-size: 13px;
    background: rgba(2,8,20,0.7);
    backdrop-filter: blur(6px);
    border-top: 1px solid rgba(255,255,255,0.1);
    z-index: 9999;
}}
.nav-link,
.nav-link:hover,
.nav-link:visited,
.nav-link:active {{
    text-decoration: none !important;
    color: rgba(255,255,255,0.8) !important;
}}

.nav-link.active {{
    color: #ff2a3d !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="site-header">
    <div class="logo">Note<span>Tube</span></div>
    <div class="nav-links">
        <a class="nav-link {'active' if st.session_state.page == 'home' else ''}" onclick="setPage('home')">Home</a>
        <a class="nav-link {'active' if st.session_state.page == 'about' else ''}" onclick="setPage('about')">About</a>
        <a class="nav-link {'active' if st.session_state.page == 'contact' else ''}" onclick="setPage('contact')">Contact</a>
    </div>
</div>

<script>
function setPage(page) {{
    const url = new URL(window.location.href);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}}
</script>
""", unsafe_allow_html=True)

# ── API & MODEL SETUP ───────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")

# Fallback model chain if primary is overloaded
FALLBACK_MODELS = [
    MODEL_NAME,
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

if not GOOGLE_API_KEY:
    st.error("❌ Google API Key not found. Please set `GOOGLE_API_KEY` in your .env file.")
    st.stop()

client = genai.Client(api_key=GOOGLE_API_KEY)

# ── HELPERS ─────────────────────────────────────────
def get_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    return match.group(1) if match else None


def extract_transcript(url):
    try:
        vid = get_video_id(url)
        if not vid:
            return None, "Invalid YouTube URL. Please check the link and try again."

        transcript_list = YouTubeTranscriptApi().fetch(vid)
        full_text = " ".join([entry.text for entry in transcript_list])
        return full_text, None

    except Exception as e:
        err_msg = str(e)
        if "No transcript" in err_msg or "TranscriptsDisabled" in err_msg:
            return None, "This video has no captions/transcript available. Try a different video."
        return None, f"Transcript error: {err_msg}"


def generate_summary(text, retries=3, delay=4):
    """
    Generate structured notes from transcript text.
    Tries multiple models with retry logic on 503 errors.
    """
    max_chars = 50000
    if len(text) > max_chars:
        text = text[:max_chars] + "... (truncated)"

    prompt = f"""You are an expert note-taker. Based on the following YouTube video transcript, generate clean, well-structured notes.

Format the notes as:
## 📌 Key Topics
- Bullet points of main topics covered

## 📝 Summary
A concise 3–5 sentence summary of the video

## 🔑 Key Points
- Important points, facts, or insights (use bullet points)

## 💡 Takeaways
- Actionable takeaways or conclusions

Transcript:
{text}"""

    last_error = None

    for model in FALLBACK_MODELS:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return response.text, None

            except Exception as e:
                err_str = str(e)
                last_error = err_str

                # 503 overloaded → retry after delay
                if "503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower():
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    else:
                        # Move to next fallback model
                        break

                # 429 rate limit → wait longer then retry
                elif "429" in err_str or "quota" in err_str.lower():
                    time.sleep(10)
                    continue

                # Any other error → fail immediately
                else:
                    return None, f"AI error: {err_str}"

    return None, f"All models are currently unavailable. Please try again in a moment.\n\nLast error: {last_error}"


def download_link(text):
    b64_content = base64.b64encode(text.encode()).decode()
    return f'<a class="act-btn" href="data:text/plain;base64,{b64_content}" download="notes.txt">⬇ Download</a>'


# ── SESSION STATE FOR NOTES ─────────────────────────
if "summary" not in st.session_state:
    st.session_state.summary = ""

# ── PAGE RENDERING ──────────────────────────────────
page = st.session_state.page

if page == "home":
    st.title("🎬 NoteTube AI")
    st.caption("YouTube → Clean Notes")

    left, right = st.columns([3.5, 6.5])

    with left:
        st.markdown("### 📎 YouTube Link")
        url = st.text_input(
            "YouTube URL",
            label_visibility="collapsed",
            placeholder="https://www.youtube.com/watch?v=..."
        )

        if url:
            vid = get_video_id(url)
            if vid:
                st.image(f"https://img.youtube.com/vi/{vid}/0.jpg", use_container_width=True)

        if st.button(" Generate Notes", type="primary"):
            if not url:
                st.error("Please enter a YouTube URL.")
            else:
                with st.spinner("📥 Fetching transcript..."):
                    transcript, err = extract_transcript(url)

                if err:
                    st.error(f"❌ {err}")
                else:
                    with st.spinner("🤖 Generating notes (retrying if busy)..."):
                        summary, gen_err = generate_summary(transcript)

                    if gen_err:
                        st.error(f"❌ {gen_err}")
                    else:
                        st.session_state.summary = summary
                        st.success("✅ Notes generated!")

    with right:
        if st.session_state.summary:
            st.markdown("### 🧾 Generated Notes")
            summary = st.session_state.summary

            copy_js = f"""
            <script>
            function copyNotes() {{
                const text = {json.dumps(summary)};
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = document.getElementById('copy-btn');
                    const originalText = btn.innerText;
                    btn.innerText = '✅ Copied!';
                    setTimeout(() => {{ btn.innerText = originalText; }}, 2000);
                }});
            }}
            </script>
            <div class="action-buttons">
                <button id="copy-btn" class="act-btn" onclick="copyNotes()">📋 Copy</button>
                {download_link(summary)}
            </div>
            <div class="notes-box">
                {summary.replace(chr(10), "<br>")}
            </div>
            """
            st.markdown(copy_js, unsafe_allow_html=True)
            st.caption(f"📊 Word Count: {len(summary.split())}")
        else:
            st.info("✨ Your AI-generated notes will appear here after you click 'Generate Notes'.")

elif page == "about":
    st.title("ℹ️ About NoteTube AI")
    st.markdown("""
    **NoteTube AI** converts any YouTube video with captions into clean, structured notes using Google's Gemini AI.
    
    ### Features
    - 🎥 Extract transcripts from any public YouTube video
    - 🤖 AI-powered summarization into readable notes
    - 📋 Copy to clipboard or download as `.txt`
    - 🎨 Glassmorphism UI with dark theme
    
    ### How it works
    1. Paste a YouTube URL
    2. Click "Generate Notes"
    3. Get instant, concise notes
    
    ### Tech Stack
    - Streamlit (frontend)
    - YouTube Transcript API
    - Google Gemini AI
    """)
    st.image("https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg", width=300, caption="Example video")

elif page == "contact":
    st.title("📧 Contact Us")
    st.markdown("""
    Have questions, feedback, or issues? Reach out!
    
    - **Email**: support@notetube.ai  
    - **GitHub**: [github.com/notetube](https://github.com)  
    - **Twitter**: [@NoteTubeAI](https://twitter.com)
    
    ### Report a bug
    If you encounter any errors, please include:
    - The YouTube URL you tried
    - Any error message shown
    - Screenshot (if possible)
    
    We'll get back to you within 48 hours.
    """)

# ── FOOTER ──────────────────────────────────────────
st.markdown("""
<div class="footer">
    © 2026 NoteTube AI • Built with Streamlit • Designed with love
</div>
""", unsafe_allow_html=True)