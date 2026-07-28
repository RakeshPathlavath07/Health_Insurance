"""
Streamlit Web Application — Indian Health Insurance Assistant
Provides a modern chat interface with tool badges, confidence evaluation badges,
dynamic randomized example queries, Unified Capsule Dock, Instant Two-Stage Chat Streamer
(User question renders IMMEDIATELY before backend query begins), Voice Output (TTS via gTTS),
transparent audio status indicators, session persistence, and web fallback alerts.
"""
import sys
import os

# Add root project directory to sys.path so 'backend' imports work seamlessly on Streamlit Cloud
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import re
import uuid
import random
from io import BytesIO
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

load_dotenv()

st.set_page_config(
    page_title="Indian Health Insurance AI Assistant",
    page_icon="🏥",
    layout="wide"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #546E7A;
        margin-bottom: 1.5rem;
    }
    .tool-badge {
        font-size: 0.85rem;
        color: #1976D2;
        background-color: #E3F2FD;
        padding: 6px 12px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 10px;
        font-weight: 500;
    }
    .fallback-badge {
        font-size: 0.85rem;
        color: #D84315;
        background-color: #FBE9E7;
        border: 1px solid #FFAB91;
        padding: 6px 12px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 10px;
        font-weight: 500;
    }
    .confidence-badge {
        font-size: 0.85rem;
        color: #2E7D32;
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        padding: 6px 12px;
        border-radius: 12px;
        display: inline-block;
        margin-top: 10px;
        margin-left: 8px;
        font-weight: 500;
    }
    .audio-status-badge {
        font-size: 0.85rem;
        color: #33691E;
        background-color: #F1F8E9;
        border: 1px solid #DCEDC8;
        padding: 6px 12px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 14px;
        margin-bottom: 6px;
        font-weight: 500;
    }
    .audio-fail-badge {
        font-size: 0.85rem;
        color: #C62828;
        background-color: #FFEBEE;
        border: 1px solid #FFCDD2;
        padding: 6px 12px;
        border-radius: 10px;
        display: inline-block;
        margin-top: 14px;
        margin-bottom: 6px;
        font-weight: 500;
    }

    /* Animated Recording Banner Above Bottom Dock */
    @keyframes pulse-ring {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.15); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }
    .pulse-dot {
        display: inline-block;
        animation: pulse-ring 1.2s infinite ease-in-out;
        color: #FF1744;
        margin-right: 6px;
        font-size: 1rem;
    }
    /* Banner starts hidden. A tiny JS watcher (injected below the mic button)
       toggles this to display:flex only while the mic is actively recording. */
    .recording-banner {
        position: fixed !important;
        bottom: 84px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background-color: #2D1517 !important;
        border: 1px solid #FF1744 !important;
        color: #FF8A80 !important;
        padding: 8px 18px !important;
        border-radius: 20px !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        z-index: 999999 !important;
        box-shadow: 0 4px 15px rgba(255, 23, 68, 0.3) !important;
        align-items: center !important;
        display: none;
    }

    /* Center Main Chat Column & Add Bottom Padding for Dock */
    .main .block-container {
        max-width: 900px !important;
        padding-bottom: 140px !important;
        margin: 0 auto !important;
    }

    /* Single Capsule Input Box Container (Mic + Prompt in one row) */
    div[data-testid="stHorizontalBlock"] {
        position: fixed !important;
        bottom: 24px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 40px) !important;
        max-width: 800px !important;
        background-color: #212121 !important;
        border: 1px solid #383838 !important;
        padding: 4px 14px !important;
        border-radius: 28px !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.35) !important;
        z-index: 99999 !important;
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px !important;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        display: flex !important;
        align-items: center !important;
    }

    /* Column 1: Floating Mic Icon Container */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
        flex: 0 0 36px !important;
        width: 36px !important;
        min-width: 36px !important;
        max-width: 36px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Column 2: Text Input INSIDE filling the remaining width of the input box */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        flex: 1 1 auto !important;
        width: calc(100% - 42px) !important;
        display: inline-flex !important;
        align-items: center !important;
        background: transparent !important;
        background-color: transparent !important;
    }

    /* USE MIX-BLEND-MODE TO STRIP ANY DARK/BLACK IFRAME BACKGROUND BOX AROUND MIC */
    div[data-testid="stHorizontalBlock"] iframe,
    iframe[title*="mic_recorder"],
    iframe[title*="streamlit_mic_recorder"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        mix-blend-mode: screen !important;
        height: 38px !important;
        width: 36px !important;
    }

    div[data-testid="stHorizontalBlock"] button,
    div[data-testid="stHorizontalBlock"] button * {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
        font-size: 1.35rem !important;
        padding: 0px !important;
        margin: 0px !important;
    }

    /* Force full input chain to 100% width */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="element-container"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stTextInput"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stTextInput"] > div,
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-baseweb="base-input"],
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-baseweb="base-input"] > div {
        width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 auto !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        overflow: visible !important;
        margin: 0 !important;
    }

    /* --- FIX: typed text was invisible inside the dark capsule ---
       Some browsers/Streamlit themes render input text color via
       -webkit-text-fill-color, which silently overrides `color`.
       We force both, plus the caret and placeholder colors, with a
       selector specific enough to win the cascade. */
    div[data-testid="stHorizontalBlock"] div[data-testid="stTextInput"] input,
    div[data-baseweb="base-input"] input {
        height: 44px !important;
        width: 100% !important;
        font-size: 1.02rem !important;
        padding-left: 4px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #FFFFFF !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stTextInput"] input::placeholder,
    div[data-baseweb="base-input"] input::placeholder {
        color: #9E9E9E !important;
        -webkit-text-fill-color: #9E9E9E !important;
        opacity: 1 !important;
    }
    /* Autofill sometimes forces a light background + dark text via
       browser UA styles; neutralize that too. */
    div[data-testid="stHorizontalBlock"] input:-webkit-autofill {
        -webkit-text-fill-color: #FFFFFF !important;
        -webkit-box-shadow: 0 0 0px 1000px #212121 inset !important;
        transition: background-color 9999s ease-in-out 0s;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏥 Health Insurance Recommendation Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-agent GenAI Assistant for Indian Health Insurance Policies & Risk Assessment</div>', unsafe_allow_html=True)

EXAMPLE_QUERY_POOL = [
    "Which policies offer zero room rent capping?",
    "Check risk metrics for ICICI Lombard",
    "Compare waiting periods of Niva Bupa ReAssure and Care Supreme",
    "What is the pre-existing disease waiting period in Tata AIG MediCare policy?",
    "Which policies include maternity coverage?",
    "Compare claim settlement ratios of Star Health, ICICI Lombard, and Niva Bupa",
    "Does Star Cardiac Care policy cover pre-existing heart conditions?",
    "Which policies have zero co-payment?",
    "What expenses are excluded under organ donor cover in ManipalCigna ProHealth?",
    "Nivabupa re-assure policy me waiting period kitna h?",
    "Which insurer has a solvency ratio above 2.5?",
    "Are modern treatments like robotic surgery covered in HDFC Ergo Optima Secure?"
]

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "sidebar_examples" not in st.session_state:
    st.session_state.sidebar_examples = random.sample(EXAMPLE_QUERY_POOL, 4)

if "last_processed_query" not in st.session_state:
    st.session_state.last_processed_query = ""

if "submitted_text" not in st.session_state:
    st.session_state.submitted_text = ""

def clear_text_input():
    st.session_state.submitted_text = st.session_state.get("text_prompt_input", "")
    st.session_state["text_prompt_input"] = ""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI Health Insurance Advisor. Ask me to compare policies, check claim settlement ratios (CSR), or analyze policy coverage terms.",
            "tools_used": [],
            "confidence_score": 98,
            "confidence_level": "High Precision",
            "audio_bytes": None,
            "audio_status": None
        }
    ]

def generate_voice_output(text: str) -> tuple[bytes, str]:
    """Generates MP3 audio stream using gTTS for assistant responses."""
    try:
        clean_text = re.sub(r'[*#_~`•]', '', text)
        clean_text = clean_text.replace("🛠️", "").replace("🌐", "").replace("🎯", "")
        clean_text = clean_text[:350]

        is_hindi = any(w in clean_text.lower() for w in ["hai", "hoon", "kitna", "kya", "mein", "kaise", "bare", "batao"])
        tts = gTTS(text=clean_text, lang="hi" if is_hindi else "en", slow=False)

        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        if audio_bytes and len(audio_bytes) > 500:
            return audio_bytes, "success"
        return None, "empty_audio"
    except Exception as e:
        print(f"gTTS error: {e}")
        return None, f"error: {str(e)}"

def transcribe_audio_whisper(audio_bytes: bytes) -> str:
    """Transcribes user voice recording using Groq Whisper API (whisper-large-v3)."""
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {groq_key}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3"}
        res = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        if res.status_code == 200:
            return res.json().get("text", "").strip()
        print(f"Whisper STT HTTP Error: {res.status_code} - {res.text}")
        return ""
    except Exception as e:
        print(f"Whisper STT Exception: {e}")
        return ""

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Session Controls")
    st.write(f"**Session ID:** `{st.session_state.session_id}`")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI Health Insurance Advisor. Ask me to compare policies, check claim settlement ratios (CSR), or analyze policy coverage terms.",
                "tools_used": [],
                "confidence_score": 98,
                "confidence_level": "High Precision",
                "audio_bytes": None,
                "audio_status": None
            }
        ]
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.sidebar_examples = random.sample(EXAMPLE_QUERY_POOL, 4)
        st.session_state.last_processed_query = ""
        st.rerun()

    st.markdown("---")
    st.subheader("💡 Example Queries")

    selected_example = None
    for eq in st.session_state.sidebar_examples:
        if st.button(eq, use_container_width=True):
            selected_example = eq

# Display ALL Conversation Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tools_used"):
            tools_list = msg["tools_used"]
            if "web_search_fallback" in tools_list:
                st.markdown(
                    '<div class="fallback-badge">🌐 <b>Live Web Ingestion Fallback</b>: Policy missing in database — fetched & ingested live brochure from web search!</div>',
                    unsafe_allow_html=True
                )
            base_tools = [t for t in tools_list if t != "web_search_fallback"]
            if base_tools:
                tools_str = ", ".join(base_tools)
                conf_score = msg.get("confidence_score", 95)
                conf_level = msg.get("confidence_level", "High Precision")
                st.markdown(f'<div class="tool-badge">🛠️ Tool Called: <b>{tools_str}</b></div><div class="confidence-badge">🎯 Confidence Score: <b>{conf_score}%</b> ({conf_level})</div>', unsafe_allow_html=True)

        # Audio voice playback for assistant responses
        if msg["role"] == "assistant" and msg.get("audio_bytes"):
            st.markdown('<div class="audio-status-badge">🔊 Voice audio ready for playback</div>', unsafe_allow_html=True)
            st.audio(msg["audio_bytes"], format="audio/mp3")
        elif msg["role"] == "assistant" and msg.get("audio_status") == "failed":
            st.markdown('<div class="audio-fail-badge">⚠️ Voice audio synthesis unavailable for this response</div>', unsafe_allow_html=True)

# Recording Status Banner — starts hidden (see CSS: display:none by default).
# The mic_recorder component does not expose a Python-visible "is recording"
# flag (it only returns audio data to Streamlit *after* you click stop), so
# this can't be driven by st.session_state / a rerun. Instead we watch the
# mic button's own label (🎙️ = idle, ⏹️ = recording) client-side.
st.markdown("""
<div class="recording-banner" id="recording-banner-el">
    <span class="pulse-dot">🔴</span> <b>Recording Audio... Speak now! Click ⏹️ when finished.</b>
</div>
""", unsafe_allow_html=True)

# Single Capsule Input Box Container: Clean Mic Icon at leftmost part INSIDE input box + Relevant Project Goal Placeholder Text
input_row = st.columns([1, 100])
with input_row[0]:
    audio_record = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        key="bottom_pinned_mic"
    )
with input_row[1]:
    text_entered = st.text_input(
        "Ask question",
        placeholder="Ask to compare policies, check claim settlement ratios (CSR), room rent capping, or coverage terms...",
        label_visibility="collapsed",
        key="text_prompt_input",
        on_change=clear_text_input
    )

# JS watcher: polls the mic component's button label and toggles the banner's
# visibility purely in the DOM, with no Streamlit rerun involved. This keeps
# the banner in sync with the actual recording state instead of always-on.
components.html("""
<script>
(function () {
    function tryInit(retries) {
        var parentDoc = window.parent.document;
        var banner = parentDoc.getElementById('recording-banner-el');
        if (!banner) {
            if (retries > 0) setTimeout(function () { tryInit(retries - 1); }, 400);
            return;
        }
        banner.style.display = 'none';

        function checkMicState() {
            var iframes = parentDoc.querySelectorAll('iframe');
            var micIframe = null;
            for (var i = 0; i < iframes.length; i++) {
                var f = iframes[i];
                var title = (f.title || '') + ' ' + (f.getAttribute('title') || '');
                if (title.toLowerCase().indexOf('mic_recorder') !== -1) {
                    micIframe = f;
                    break;
                }
            }
            if (!micIframe) return;
            try {
                var micDoc = micIframe.contentDocument || micIframe.contentWindow.document;
                var btn = micDoc.querySelector('button');
                if (btn) {
                    var label = btn.innerText || btn.textContent || '';
                    if (label.indexOf('⏹') !== -1) {
                        banner.style.display = 'flex';
                    } else {
                        banner.style.display = 'none';
                    }
                }
            } catch (e) {
                // Cross-origin iframe (e.g. some hosting setups serve
                // components from a different origin) — can't read the
                // button label from here, so leave the banner hidden.
            }
        }
        setInterval(checkMicState, 300);
    }
    tryInit(10);
})();
</script>
""", height=0)

# Process Voice Audio Input if recorded
voice_query = ""
if audio_record and "bytes" in audio_record and len(audio_record["bytes"]) > 100:
    with st.spinner("🎙️ Transcribing your voice query via Groq Whisper AI..."):
        voice_query = transcribe_audio_whisper(audio_record["bytes"])

# Determine active user input
user_input = st.session_state.submitted_text or text_entered or voice_query or selected_example

# STAGE 1: Render User Question IMMEDIATELY on screen before backend API call
if user_input and user_input != st.session_state.last_processed_query:
    st.session_state.last_processed_query = user_input
    st.session_state.messages.append({"role": "user", "content": user_input, "tools_used": []})
    st.session_state.submitted_text = ""
    st.rerun()

# STAGE 2: If the last message is from the user, query backend API & render assistant answer
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_query = st.session_state.messages[-1]["content"]

    answer = ""
    tools_used = []
    confidence_score = 95
    confidence_level = "High Precision"

    with st.spinner("Analyzing policy data & querying multi-agent system..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": st.session_state.session_id, "query": last_user_query},
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No response received.")
                tools_used = data.get("tools_used", [])
                confidence_score = data.get("confidence_score", 95)
                confidence_level = data.get("confidence_level", "High Precision")
            else:
                raise Exception(f"Server returned HTTP {response.status_code}")
        except Exception:
            # Standalone Streamlit Cloud Fallback: Run multi-agent dispatcher directly in Python
            try:
                from backend.app.dispatcher import route_and_execute
                from backend.app.guardrails import validate_response
                res_dict = route_and_execute(last_user_query, session_id=st.session_state.session_id)
                raw_answer = res_dict.get("answer", "")
                tools_used = res_dict.get("tools_used", [])
                confidence_score = res_dict.get("confidence_score", 95)
                confidence_level = res_dict.get("confidence_level", "High Precision")
                answer = validate_response(last_user_query, raw_answer)
            except Exception as direct_e:
                answer = f"Error processing query: {direct_e}"

    # Voice Audio Synthesis
    audio_data = None
    audio_status = "pending"
    with st.spinner("🔊 Synthesizing voice audio response..."):
        audio_data, status_res = generate_voice_output(answer)
        if status_res == "success" and audio_data:
            audio_status = "success"
        else:
            audio_status = "failed"

    # Save Assistant Answer to chat history & Rerun
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "tools_used": tools_used,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "audio_bytes": audio_data,
        "audio_status": audio_status
    })

    st.rerun()