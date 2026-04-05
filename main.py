import streamlit as st
import base64
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI PROVIDER — currently OpenAI (GPT-4o).
# To switch to Claude in the future:
#   1. pip install anthropic  (remove openai from requirements.txt)
#   2. Replace this block:     import anthropic
#   3. In get_ai_response():   swap the OpenAI call for the Anthropic one (see comments there)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from openai import OpenAI

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

  /* Global */
  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

  /* ── Header ── */
  .app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(135deg, #1a1d27 0%, #12151e 100%);
    border: 1px solid #2a2f3e;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  }
  .app-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem;
    color: #7dd3fc;
    margin: 0;
    letter-spacing: -0.5px;
  }
  .header-badge {
    background: #1e3a5f;
    color: #7dd3fc;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    border: 1px solid #2563eb44;
  }

  /* ── Panel Cards ── */
  .panel-card {
    background: #12151e;
    border: 1px solid #1e2435;
    border-radius: 14px;
    overflow: hidden;
    height: calc(100vh - 130px);
    display: flex;
    flex-direction: column;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }
  .panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.75rem 1rem;
    background: #1a1d27;
    border-bottom: 1px solid #1e2435;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #94a3b8;
  }
  .panel-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    box-shadow: 0 0 6px #3b82f6;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }

  /* ── Chat area ── */
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 12px;
    scrollbar-width: thin;
    scrollbar-color: #1e2435 transparent;
  }
  .msg-user {
    align-self: flex-end;
    background: #1e3a5f;
    border: 1px solid #2563eb44;
    color: #e2e8f0;
    padding: 10px 14px;
    border-radius: 14px 14px 2px 14px;
    max-width: 82%;
    font-size: 0.88rem;
    line-height: 1.55;
  }
  .msg-ai {
    align-self: flex-start;
    background: #1a1d27;
    border: 1px solid #2a2f3e;
    color: #cbd5e1;
    padding: 10px 14px;
    border-radius: 14px 14px 14px 2px;
    max-width: 88%;
    font-size: 0.88rem;
    line-height: 1.65;
  }
  .msg-meta {
    font-size: 0.68rem;
    color: #475569;
    margin-top: 4px;
  }
  .msg-screenshot-tag {
    display: inline-block;
    background: #164e63;
    color: #67e8f9;
    font-size: 0.68rem;
    padding: 2px 8px;
    border-radius: 6px;
    margin-bottom: 6px;
    font-family: 'Space Mono', monospace;
  }

  /* ── Sticker: no messages ── */
  .empty-chat {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 10px;
    color: #334155;
  }
  .empty-chat .icon { font-size: 2.5rem; }
  .empty-chat p { font-size: 0.83rem; text-align: center; max-width: 220px; line-height: 1.6; }

  /* ── Status pill ── */
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.72rem;
    padding: 3px 9px;
    border-radius: 12px;
    font-family: 'Space Mono', monospace;
  }
  .status-live   { background: #14532d; color: #4ade80; border: 1px solid #16a34a44; }
  .status-idle   { background: #1c1917; color: #78716c; border: 1px solid #44403c44; }
  .status-audio  { background: #1e1b4b; color: #a5b4fc; border: 1px solid #6366f144; }

  /* ── Streamlit widget overrides ── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: #1a1d27 !important;
    border: 1px solid #2a2f3e !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
  }
  .stButton > button {
    background: #1e3a5f !important;
    color: #7dd3fc !important;
    border: 1px solid #2563eb44 !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    background: #1d4ed8 !important;
    color: #fff !important;
    border-color: #3b82f6 !important;
  }
  div[data-testid="stHorizontalBlock"] { gap: 1rem !important; }

  /* ── Transcript box ── */
  .transcript-box {
    background: #0f1117;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.82rem;
    color: #94a3b8;
    min-height: 52px;
    font-style: italic;
    line-height: 1.5;
  }

  /* ── API key area ── */
  .api-section {
    background: #12151e;
    border: 1px solid #1e2435;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "screenshot_b64" not in st.session_state:
    st.session_state.screenshot_b64 = None
if "pending_screenshot" not in st.session_state:
    st.session_state.pending_screenshot = False
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
# ── AI provider config ─────────────────────────────────────────────────────
# CURRENT: OpenAI  |  FUTURE: swap env var to ANTHROPIC_API_KEY
AI_PROVIDER   = "openai"          # change to "anthropic" when switching
AI_MODEL      = "gpt-4o"          # change to "claude-opus-4-5" when switching
ENV_KEY_NAME  = "OPENAI_API_KEY"  # change to "ANTHROPIC_API_KEY" when switching

if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get(ENV_KEY_NAME, "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🧠 MeetingMind AI</h1>
  <span class="header-badge">BETA v1.0</span>
</div>
""", unsafe_allow_html=True)

# ── API Key (sidebar-style inline) ────────────────────────────────────────────
with st.expander("⚙️ API Configuration", expanded=(not st.session_state.api_key)):
    col_k1, col_k2 = st.columns([4, 1])
    with col_k1:
        key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-...",   # Claude keys start with sk-ant-...
            label_visibility="collapsed",
        )
    with col_k2:
        if st.button("Save Key"):
            st.session_state.api_key = key_input
            st.success("Saved!")
    st.caption("🔑 OpenAI key (sk-...) · stored in session only, never persisted.")

# ── Two-column layout ──────────────────────────────────────────────────────────
left_col, right_col = st.columns([1.1, 0.9], gap="small")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Screen Capture
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel-header">
      <div class="panel-dot"></div>
      MEETING VIEW &nbsp;·&nbsp; Browser Tab Capture
    </div>
    """, unsafe_allow_html=True)

    # ── Screen capture HTML+JS component ──────────────────────────────────────
    CAPTURE_COMPONENT = """
    <div id="capture-root" style="padding:14px; display:flex; flex-direction:column; gap:12px;">

      <!-- Controls row -->
      <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">

        <button id="btn-share" onclick="startCapture()"
          style="background:#1e3a5f; color:#7dd3fc; border:1px solid #2563eb55;
                 padding:7px 14px; border-radius:8px; cursor:pointer;
                 font-family:'Space Mono',monospace; font-size:0.75rem;">
          📺 Share Tab
        </button>

        <button id="btn-stop" onclick="stopCapture()" disabled
          style="background:#1c1917; color:#78716c; border:1px solid #44403c55;
                 padding:7px 14px; border-radius:8px; cursor:pointer;
                 font-family:'Space Mono',monospace; font-size:0.75rem;">
          ⏹ Stop
        </button>

        <button id="btn-shot" onclick="takeScreenshot()" disabled
          style="background:#1a2744; color:#7dd3fc; border:1px solid #3b82f655;
                 padding:7px 14px; border-radius:8px; cursor:pointer;
                 font-family:'Space Mono',monospace; font-size:0.75rem;">
          📸 Screenshot → AI
        </button>

        <span id="status-pill"
          style="font-size:0.7rem; background:#1c1917; color:#78716c;
                 border:1px solid #44403c55; padding:3px 10px;
                 border-radius:12px; font-family:'Space Mono',monospace;">
          ● IDLE
        </span>
      </div>

      <!-- Video display -->
      <div style="position:relative; background:#060810; border:1px solid #1e2435;
                  border-radius:10px; overflow:hidden; aspect-ratio:16/9;">
        <video id="meeting-video" autoplay muted playsinline
          style="width:100%; height:100%; object-fit:contain; display:none;"></video>
        <canvas id="hidden-canvas" style="display:none;"></canvas>
        <div id="video-placeholder"
          style="position:absolute; inset:0; display:flex; flex-direction:column;
                 align-items:center; justify-content:center; gap:10px; color:#334155;">
          <div style="font-size:2.5rem;">📺</div>
          <div style="font-size:0.8rem; font-family:'Space Mono',monospace;">
            Click "Share Tab" to capture your meeting
          </div>
          <div style="font-size:0.68rem; color:#1e3a5f; max-width:240px; text-align:center; line-height:1.6;">
            Works best with Chrome.<br>Select the tab running your meeting.
          </div>
        </div>
      </div>

      <!-- Screenshot preview -->
      <div id="shot-preview-wrap" style="display:none;">
        <div style="font-size:0.72rem; color:#475569; font-family:'Space Mono',monospace;
                    margin-bottom:5px;">LAST SCREENSHOT (sent to AI)</div>
        <img id="shot-preview"
          style="width:100%; border-radius:8px; border:1px solid #1e2435; max-height:140px; object-fit:cover;"/>
        <div id="shot-time" style="font-size:0.65rem; color:#334155; margin-top:3px;"></div>
      </div>

      <!-- Audio & Transcription -->
      <div style="border-top:1px solid #1e2435; padding-top:10px;">
        <div style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
          <button id="btn-audio" onclick="toggleAudio()"
            style="background:#1e1b4b; color:#a5b4fc; border:1px solid #6366f144;
                   padding:6px 12px; border-radius:8px; cursor:pointer;
                   font-family:'Space Mono',monospace; font-size:0.73rem;">
            🎙 Start Listening
          </button>
          <span style="font-size:0.7rem; color:#334155;">Web Speech API (Chrome)</span>
        </div>
        <div id="transcript-display"
          style="background:#0f1117; border:1px solid #1e293b; border-radius:8px;
                 padding:10px 12px; font-size:0.8rem; color:#64748b;
                 min-height:50px; font-style:italic; line-height:1.5;">
          Transcribed speech will appear here…
        </div>
        <button id="btn-use-transcript" onclick="sendTranscript()"
          style="margin-top:6px; background:#0f172a; color:#475569;
                 border:1px solid #1e2435; padding:5px 12px;
                 border-radius:7px; cursor:pointer;
                 font-family:'Space Mono',monospace; font-size:0.7rem;">
          ↗ Use as AI Question
        </button>
      </div>

      <!-- Hidden output fields that Streamlit reads via JS → Python -->
      <input type="hidden" id="screenshot-data" />
      <input type="hidden" id="transcript-data" />
    </div>

    <script>
      let mediaStream = null;
      let recognition   = null;
      let recognizing    = false;
      let fullTranscript = "";

      // ── Capture ────────────────────────────────────────────────────
      async function startCapture() {
        try {
          mediaStream = await navigator.mediaDevices.getDisplayMedia({
            video: { frameRate: 15 },
            audio: true
          });
          const video = document.getElementById('meeting-video');
          video.srcObject = mediaStream;
          video.style.display = 'block';
          document.getElementById('video-placeholder').style.display = 'none';
          document.getElementById('btn-share').disabled  = true;
          document.getElementById('btn-stop').disabled   = false;
          document.getElementById('btn-shot').disabled   = false;
          document.getElementById('btn-share').style.background = '#14532d';
          document.getElementById('btn-share').style.color      = '#4ade80';
          setStatus('● LIVE', '#14532d', '#4ade80', '#16a34a44');
          mediaStream.getTracks().forEach(t => t.addEventListener('ended', stopCapture));
        } catch(e) {
          setStatus('✖ DENIED', '#450a0a', '#f87171', '#dc262644');
          setTimeout(() => setStatus('● IDLE', '#1c1917', '#78716c', '#44403c55'), 2000);
        }
      }

      function stopCapture() {
        if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
        const video = document.getElementById('meeting-video');
        video.srcObject = null;
        video.style.display = 'none';
        document.getElementById('video-placeholder').style.display = 'flex';
        document.getElementById('btn-share').disabled  = false;
        document.getElementById('btn-share').style.background = '#1e3a5f';
        document.getElementById('btn-share').style.color      = '#7dd3fc';
        document.getElementById('btn-stop').disabled   = true;
        document.getElementById('btn-shot').disabled   = true;
        setStatus('● IDLE', '#1c1917', '#78716c', '#44403c55');
      }

      // ── Screenshot ────────────────────────────────────────────────
      function takeScreenshot() {
        const video  = document.getElementById('meeting-video');
        const canvas = document.getElementById('hidden-canvas');
        canvas.width  = video.videoWidth  || 1280;
        canvas.height = video.videoHeight || 720;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataURL = canvas.toDataURL('image/jpeg', 0.85);

        // Show preview
        document.getElementById('shot-preview').src = dataURL;
        document.getElementById('shot-preview-wrap').style.display = 'block';
        document.getElementById('shot-time').textContent =
          'Captured at ' + new Date().toLocaleTimeString();

        // Store for Streamlit to read
        document.getElementById('screenshot-data').value = dataURL;

        // Flash effect
        setStatus('📸 SNAP!', '#164e63', '#67e8f9', '#0891b244');
        setTimeout(() => setStatus('● LIVE', '#14532d', '#4ade80', '#16a34a44'), 1000);

        // Communicate to Streamlit
        notifyStreamlit('screenshot', dataURL);
      }

      // ── Audio / Speech ────────────────────────────────────────────
      function toggleAudio() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
          document.getElementById('transcript-display').textContent =
            '⚠ Speech API not supported. Use Chrome.';
          return;
        }
        if (recognizing) { recognition.stop(); return; }

        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous     = true;
        recognition.interimResults = true;
        recognition.lang           = 'en-US';

        recognition.onstart = () => {
          recognizing = true;
          document.getElementById('btn-audio').textContent  = '⏹ Stop Listening';
          document.getElementById('btn-audio').style.background = '#1e3a2f';
          document.getElementById('btn-audio').style.color      = '#4ade80';
          setStatus('🎙 LISTENING', '#1e1b4b', '#a5b4fc', '#6366f144');
        };

        recognition.onresult = (e) => {
          let interim = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const t = e.results[i][0].transcript;
            if (e.results[i].isFinal) { fullTranscript += t + " "; }
            else { interim = t; }
          }
          document.getElementById('transcript-display').textContent =
            fullTranscript + (interim ? '…' + interim : '');
          document.getElementById('transcript-data').value = fullTranscript;
        };

        recognition.onerror = (e) => {
          document.getElementById('transcript-display').textContent = '⚠ Error: ' + e.error;
        };

        recognition.onend = () => {
          recognizing = false;
          document.getElementById('btn-audio').textContent  = '🎙 Start Listening';
          document.getElementById('btn-audio').style.background = '#1e1b4b';
          document.getElementById('btn-audio').style.color      = '#a5b4fc';
          if (mediaStream) {
            setStatus('● LIVE', '#14532d', '#4ade80', '#16a34a44');
          } else {
            setStatus('● IDLE', '#1c1917', '#78716c', '#44403c55');
          }
        };

        recognition.start();
      }

      // ── Send transcript to AI question box ────────────────────────
      function sendTranscript() {
        const t = document.getElementById('transcript-data').value.trim();
        if (!t) return;
        notifyStreamlit('transcript', t);
      }

      // ── Helpers ───────────────────────────────────────────────────
      function setStatus(text, bg, color, border) {
        const el = document.getElementById('status-pill');
        el.textContent        = text;
        el.style.background   = bg;
        el.style.color        = color;
        el.style.borderColor  = border;
      }

      // Post message to Streamlit parent
      function notifyStreamlit(type, data) {
        window.parent.postMessage({ type: 'meetingmind_' + type, data: data }, '*');
      }
    </script>
    """

    st.components.v1.html(CAPTURE_COMPONENT, height=620, scrolling=False)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — AI Chat
# ══════════════════════════════════════════════════════════════════════════════
with right_col:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel-header">
      <div class="panel-dot" style="background:#a78bfa; box-shadow:0 0 6px #a78bfa;"></div>
      AI ASSISTANT &nbsp;·&nbsp; GPT-4o Vision
    </div>
    """, unsafe_allow_html=True)

    # ── Chat messages ──────────────────────────────────────────────────────
    st.markdown('<div class="chat-messages" id="chat-scroll">', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-chat">
          <div class="icon">🧠</div>
          <p>Share your meeting tab on the left, then ask me anything about what's on screen.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                screenshot_tag = ""
                if msg.get("has_screenshot"):
                    screenshot_tag = '<div class="msg-screenshot-tag">📸 Screenshot attached</div>'
                st.markdown(f"""
                <div class="msg-user">
                  {screenshot_tag}
                  {msg["text"]}
                  <div class="msg-meta">{msg["time"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-ai">
                  {msg["text"].replace(chr(10), "<br>")}
                  <div class="msg-meta">🧠 MeetingMind AI · {msg["time"]}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Screenshot injection listener ──────────────────────────────────────
    # JS bridge: capture postMessage from iframe component
    LISTENER_JS = """
    <script>
    window.addEventListener('message', function(e) {
      const d = e.data;
      if (!d || typeof d !== 'object') return;

      if (d.type === 'meetingmind_screenshot') {
        // Store in sessionStorage so Streamlit query_params trick can pick it up
        sessionStorage.setItem('mm_screenshot', d.data);
        sessionStorage.setItem('mm_has_screenshot', 'true');
        // Flash notice
        const notice = document.createElement('div');
        notice.textContent = '📸 Screenshot ready for AI';
        notice.style.cssText = `position:fixed;bottom:80px;right:24px;
          background:#164e63;color:#67e8f9;padding:8px 16px;
          border-radius:8px;font-size:0.78rem;z-index:9999;
          font-family:'Space Mono',monospace;
          border:1px solid #0891b2;`;
        document.body.appendChild(notice);
        setTimeout(() => notice.remove(), 2500);
      }

      if (d.type === 'meetingmind_transcript') {
        sessionStorage.setItem('mm_transcript', d.data);
        const notice = document.createElement('div');
        notice.textContent = '🎙 Transcript ready — paste into chat below';
        notice.style.cssText = `position:fixed;bottom:80px;right:24px;
          background:#1e1b4b;color:#a5b4fc;padding:8px 16px;
          border-radius:8px;font-size:0.78rem;z-index:9999;
          font-family:'Space Mono',monospace;
          border:1px solid #6366f1;`;
        document.body.appendChild(notice);
        setTimeout(() => notice.remove(), 3000);
      }
    });
    </script>
    """
    st.components.v1.html(LISTENER_JS, height=0)

    # ── Quick action buttons ────────────────────────────────────────────────
    st.markdown("---")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("📸 Attach screenshot", key="qa_shot"):
            st.session_state.pending_screenshot = True
            st.info("Next message will include the last screenshot.", icon="📸")
    with qa2:
        if st.button("🗒 Summarise screen", key="qa_sum"):
            st.session_state.pending_screenshot = True
            st.session_state["auto_prompt"] = "Please summarise what you see on my meeting screen."
    with qa3:
        if st.button("🗑 Clear chat", key="qa_clear"):
            st.session_state.messages = []
            st.rerun()

    # ── Screenshot upload fallback ──────────────────────────────────────────
    with st.expander("📁 Or upload a screenshot manually"):
        uploaded = st.file_uploader("Upload screenshot", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        if uploaded:
            img_bytes = uploaded.read()
            st.session_state.screenshot_b64 = base64.b64encode(img_bytes).decode("utf-8")
            st.session_state.pending_screenshot = True
            st.success("Screenshot loaded — will be sent with next message.")

    # ── Chat input ─────────────────────────────────────────────────────────
    auto_val = st.session_state.pop("auto_prompt", "")
    user_input = st.chat_input(
        placeholder="Ask about your meeting… (Ctrl+Enter to send)",
    )
    if auto_val and not user_input:
        user_input = auto_val

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # get_ai_response() — all provider logic is isolated here.
    # To switch to Claude: replace the function body with the Anthropic version
    # shown in the comments below.
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def get_ai_response(api_key: str, history: list, user_text: str, screenshot_b64: str | None) -> str:
        SYSTEM_PROMPT = (
            "You are MeetingMind AI — an intelligent assistant embedded "
            "alongside the user's live video meeting. You can see screenshots "
            "of the meeting when provided. Be concise, direct, and helpful. "
            "If given a screenshot, describe the key info you can see. "
            "Answer questions about meeting content, help draft responses, "
            "summarise what's on screen, or assist with any task."
        )

        # ── ✅ CURRENT: OpenAI GPT-4o ──────────────────────────────────────
        client = OpenAI(api_key=api_key)

        # Build the user content block (text + optional image)
        user_content = []
        if screenshot_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_b64}",
                    "detail": "high",   # "low" is cheaper; "high" reads fine text
                },
            })
        user_content.append({"type": "text", "text": user_text})

        # Build full message list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += history                                    # prior turns
        messages.append({"role": "user", "content": user_content})

        response = client.chat.completions.create(
            model=AI_MODEL,        # "gpt-4o"
            messages=messages,
            max_tokens=1500,
        )
        return response.choices[0].message.content

        # ── 🔮 FUTURE: Anthropic Claude (uncomment when ready) ────────────
        # import anthropic
        # client = anthropic.Anthropic(api_key=api_key)
        #
        # content = []
        # if screenshot_b64:
        #     content.append({
        #         "type": "image",
        #         "source": {"type": "base64", "media_type": "image/jpeg", "data": screenshot_b64},
        #     })
        # content.append({"type": "text", "text": user_text})
        #
        # response = client.messages.create(
        #     model="claude-opus-4-5",          # or claude-sonnet-4-6 for speed
        #     max_tokens=1500,
        #     system=SYSTEM_PROMPT,
        #     messages=history + [{"role": "user", "content": content}],
        # )
        # return response.content[0].text
        # ──────────────────────────────────────────────────────────────────

    # ── Send message ───────────────────────────────────────────────────────
    if user_input:
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your OpenAI API Key above.")
        else:
            now = datetime.now().strftime("%H:%M")
            has_shot = st.session_state.pending_screenshot and st.session_state.screenshot_b64

            # Save user message
            st.session_state.messages.append({
                "role": "user",
                "text": user_input,
                "time": now,
                "has_screenshot": bool(has_shot),
            })

            # Grab screenshot then clear
            shot_b64 = None
            if has_shot:
                shot_b64 = st.session_state.screenshot_b64
                st.session_state.pending_screenshot = False
                st.session_state.screenshot_b64 = None

            # Build prior-turn history (last 10, text only)
            history = [
                {"role": m["role"], "content": m["text"]}
                for m in st.session_state.messages[:-1][-10:]
            ]

            with st.spinner("Thinking…"):
                try:
                    ai_text = get_ai_response(
                        api_key=st.session_state.api_key,
                        history=history,
                        user_text=user_input,
                        screenshot_b64=shot_b64,
                    )
                except Exception as e:
                    ai_text = f"⚠️ Error: {str(e)}"

            st.session_state.messages.append({
                "role": "assistant",
                "text": ai_text,
                "time": datetime.now().strftime("%H:%M"),
            })
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

