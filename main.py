import streamlit as st
import base64
import os
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI PROVIDER — currently OpenAI (GPT-4o).
# To switch to Claude in the future:
#   1. pip install anthropic  (remove openai from requirements.txt)
#   2. Replace:  from openai import OpenAI  →  import anthropic
#   3. In get_ai_response(): swap the OpenAI block for the Claude block (see comments)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from openai import OpenAI

AI_MODEL     = "gpt-4o"           # change to "claude-opus-4-5" when switching
ENV_KEY_NAME = "OPENAI_API_KEY"   # change to "ANTHROPIC_API_KEY" when switching

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }

  /* ── Hide ALL Streamlit chrome ── */
  #MainMenu, footer, header                 { visibility: hidden !important; }
  [data-testid="manage-app-button"]         { display: none !important; }
  [data-testid="stToolbar"]                 { display: none !important; }
  [data-testid="stDecoration"]              { display: none !important; }
  .viewerBadge_container__r5tak            { display: none !important; }
  .stDeployButton                           { display: none !important; }
  section[data-testid="stSidebar"]          { display: none !important; }

  .block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

  /* FIX: Make iframes transparent so no black boxes appear */
  iframe { background: transparent !important; border: none !important; display: block !important; }

  /* ── Header ── */
  .app-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(135deg, #1a1d27 0%, #12151e 100%);
    border: 1px solid #2a2f3e; border-radius: 12px;
    margin-bottom: 1rem; box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  }
  .app-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem; color: #7dd3fc; margin: 0; letter-spacing: -0.5px;
  }
  .header-badge {
    background: #1e3a5f; color: #7dd3fc; font-size: 0.72rem;
    padding: 3px 10px; border-radius: 20px;
    font-family: 'Space Mono', monospace; border: 1px solid #2563eb44;
  }

  /* ── Panel cards ── */
  .panel-card {
    background: #12151e; border: 1px solid #1e2435;
    border-radius: 14px; overflow: hidden;
    display: flex; flex-direction: column;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  }
  .panel-header {
    display: flex; align-items: center; gap: 8px;
    padding: 0.75rem 1rem; background: #1a1d27;
    border-bottom: 1px solid #1e2435;
    font-size: 0.82rem; font-weight: 600;
    letter-spacing: 0.5px; text-transform: uppercase; color: #94a3b8;
  }
  .panel-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #3b82f6; box-shadow: 0 0 6px #3b82f6;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── Chat messages (FIX: fixed height + scroll) ── */
  .chat-messages {
    height: 420px;          /* fixed so messages scroll INSIDE the panel */
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 12px;
    scrollbar-width: thin;
    scrollbar-color: #1e2435 transparent;
    background: #0d0f14;
  }
  .msg-user {
    align-self: flex-end;
    background: #1e3a5f; border: 1px solid #2563eb44;
    color: #e2e8f0; padding: 10px 14px;
    border-radius: 14px 14px 2px 14px;
    max-width: 82%; font-size: 0.88rem; line-height: 1.55;
  }
  .msg-ai {
    align-self: flex-start;
    background: #1a1d27; border: 1px solid #2a2f3e;
    color: #cbd5e1; padding: 10px 14px;
    border-radius: 14px 14px 14px 2px;
    max-width: 88%; font-size: 0.88rem; line-height: 1.65;
  }
  .msg-meta { font-size: 0.68rem; color: #475569; margin-top: 4px; }
  .msg-screenshot-tag {
    display: inline-block; background: #164e63; color: #67e8f9;
    font-size: 0.68rem; padding: 2px 8px; border-radius: 6px;
    margin-bottom: 6px; font-family: 'Space Mono', monospace;
  }
  .empty-chat {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100%; gap: 10px; color: #334155;
  }
  .empty-chat .icon { font-size: 2.5rem; }
  .empty-chat p { font-size: 0.83rem; text-align: center; max-width: 220px; line-height: 1.6; }

  /* ── Streamlit widget overrides ── */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: #1a1d27 !important; border: 1px solid #2a2f3e !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
  }
  .stButton > button {
    background: #1e3a5f !important; color: #7dd3fc !important;
    border: 1px solid #2563eb44 !important; border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.78rem !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    background: #1d4ed8 !important; color: #fff !important; border-color: #3b82f6 !important;
  }
  div[data-testid="stHorizontalBlock"] { gap: 1rem !important; }

  /* ── Chat input sizing (FIX: give it more room, avoid Manage App overlap) ── */
  [data-testid="stChatInput"] {
    background: #1a1d27 !important;
    border: 1px solid #2a2f3e !important;
    border-radius: 10px !important;
  }
  [data-testid="stChatInputTextArea"] {
    font-size: 0.88rem !important;
    min-height: 52px !important;    /* 2× taller input area */
  }
  [data-testid="stChatInputSubmitButton"] {
    width: 52px !important;         /* 2× wider send button */
    height: 52px !important;        /* 2× taller send button */
  }
  [data-testid="stChatInputSubmitButton"] svg {
    width: 24px !important; height: 24px !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "screenshot_b64" not in st.session_state:
    st.session_state.screenshot_b64 = None
if "pending_screenshot" not in st.session_state:
    st.session_state.pending_screenshot = False
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get(ENV_KEY_NAME, "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🧠 MeetingMind AI</h1>
  <span class="header-badge">GPT-4o Vision · v4.0</span>
</div>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
with st.expander("⚙️ OpenAI API Key", expanded=(not st.session_state.api_key)):
    col_k1, col_k2 = st.columns([4, 1])
    with col_k1:
        key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-...",
            label_visibility="collapsed",
        )
    with col_k2:
        if st.button("Save Key"):
            st.session_state.api_key = key_input
            st.success("Saved!")
    st.caption("🔑 OpenAI key (sk-...) · stored in session only, never persisted.")

# ── Two-column layout ─────────────────────────────────────────────────────────
left_col, right_col = st.columns([1.15, 0.85], gap="small")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — Screen Capture  (V1 CAPTURE_COMPONENT — UNCHANGED, buttons work)
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div class="panel-card">
      <div class="panel-header">
        <div class="panel-dot"></div>
        MEETING VIEW &nbsp;·&nbsp; Browser Tab Capture
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── This is V1's exact CAPTURE_COMPONENT — only change is transcript min-height ──
    CAPTURE_COMPONENT = """
    <div id="capture-root" style="padding:14px; display:flex; flex-direction:column; gap:12px; background:#0d0f14;">

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
          <div style="font-size:0.8rem; font-family:'Space Mono',monospace; text-align:center;">
            Click "Share Tab" to capture your meeting
          </div>
          <div style="font-size:0.68rem; color:#1e3a5f; max-width:240px; text-align:center; line-height:1.6;">
            Works best with Chrome.<br>Select the tab running your meeting.
          </div>
        </div>
      </div>

      <!-- Screenshot preview -->
      <div id="shot-preview-wrap" style="display:none;">
        <div style="font-size:0.72rem; color:#475569; font-family:'Space Mono',monospace; margin-bottom:5px;">
          LAST SCREENSHOT (sent to AI)
        </div>
        <img id="shot-preview"
          style="width:100%; border-radius:8px; border:1px solid #1e2435; max-height:120px; object-fit:cover;"/>
        <div id="shot-time" style="font-size:0.65rem; color:#334155; margin-top:3px;"></div>
      </div>

      <!-- Audio & Transcription (FIX #3: min-height:72px = 3 lines) -->
      <div style="border-top:1px solid #1e2435; padding-top:10px;">
        <div style="font-size:0.7rem; color:#475569; font-family:'Space Mono',monospace;
                    letter-spacing:0.8px; text-transform:uppercase; margin-bottom:6px;">
          🎙 Live Transcript
        </div>
        <div style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
          <button id="btn-audio" onclick="toggleAudio()"
            style="background:#1e1b4b; color:#a5b4fc; border:1px solid #6366f144;
                   padding:6px 12px; border-radius:8px; cursor:pointer;
                   font-family:'Space Mono',monospace; font-size:0.73rem;">
            🎙 Start Listening
          </button>
          <button id="btn-use-transcript" onclick="sendTranscript()"
            style="background:#0f172a; color:#475569; border:1px solid #1e2435;
                   padding:5px 12px; border-radius:7px; cursor:pointer;
                   font-family:'Space Mono',monospace; font-size:0.7rem;">
            ↗ Use as AI Question
          </button>
        </div>
        <div id="transcript-display"
          style="background:#0f1117; border:1px solid #1e293b; border-radius:8px;
                 padding:10px 12px; font-size:0.8rem; color:#64748b;
                 min-height:72px;
                 max-height:100px; overflow-y:auto;
                 font-style:italic; line-height:1.6;
                 scrollbar-width:thin;">
          Transcribed speech will appear here…
        </div>
      </div>

      <input type="hidden" id="screenshot-data" />
      <input type="hidden" id="transcript-data" />
    </div>

    <script>
      let mediaStream  = null;
      let recognition  = null;
      let recognizing  = false;
      let fullTranscript = "";

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
          document.getElementById('btn-share').disabled = true;
          document.getElementById('btn-stop').disabled  = false;
          document.getElementById('btn-shot').disabled  = false;
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
        document.getElementById('btn-share').disabled = false;
        document.getElementById('btn-share').style.background = '#1e3a5f';
        document.getElementById('btn-share').style.color      = '#7dd3fc';
        document.getElementById('btn-stop').disabled = true;
        document.getElementById('btn-shot').disabled = true;
        setStatus('● IDLE', '#1c1917', '#78716c', '#44403c55');
      }

      function takeScreenshot() {
        const video  = document.getElementById('meeting-video');
        const canvas = document.getElementById('hidden-canvas');
        canvas.width  = video.videoWidth  || 1280;
        canvas.height = video.videoHeight || 720;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataURL = canvas.toDataURL('image/jpeg', 0.85);
        document.getElementById('shot-preview').src = dataURL;
        document.getElementById('shot-preview-wrap').style.display = 'block';
        document.getElementById('shot-time').textContent =
          'Captured at ' + new Date().toLocaleTimeString();
        document.getElementById('screenshot-data').value = dataURL;
        setStatus('📸 SNAP!', '#164e63', '#67e8f9', '#0891b244');
        setTimeout(() => setStatus('● LIVE', '#14532d', '#4ade80', '#16a34a44'), 1000);
        notifyStreamlit('screenshot', dataURL);
      }

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
          document.getElementById('btn-audio').textContent = '⏹ Stop Listening';
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
          const el = document.getElementById('transcript-display');
          el.textContent = fullTranscript + (interim ? '…' + interim : '');
          el.style.fontStyle = 'normal';
          el.style.color = '#94a3b8';
          el.scrollTop = el.scrollHeight;
          document.getElementById('transcript-data').value = fullTranscript;
        };
        recognition.onerror = (e) => {
          document.getElementById('transcript-display').textContent = '⚠ Error: ' + e.error;
        };
        recognition.onend = () => {
          recognizing = false;
          document.getElementById('btn-audio').textContent = '🎙 Start Listening';
          document.getElementById('btn-audio').style.background = '#1e1b4b';
          document.getElementById('btn-audio').style.color      = '#a5b4fc';
          setStatus(mediaStream ? '● LIVE' : '● IDLE',
                    mediaStream ? '#14532d' : '#1c1917',
                    mediaStream ? '#4ade80' : '#78716c',
                    mediaStream ? '#16a34a44' : '#44403c55');
        };
        recognition.start();
      }

      function sendTranscript() {
        const t = document.getElementById('transcript-data').value.trim();
        if (!t) return;
        notifyStreamlit('transcript', t);
      }

      function setStatus(text, bg, color, border) {
        const el = document.getElementById('status-pill');
        el.textContent = text;
        el.style.background  = bg;
        el.style.color       = color;
        el.style.borderColor = border;
      }

      function notifyStreamlit(type, data) {
        window.parent.postMessage({ type: 'meetingmind_' + type, data: data }, '*');
      }
    </script>
    """

    st.components.v1.html(CAPTURE_COMPONENT, height=640, scrolling=False)

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — AI Chat
# ══════════════════════════════════════════════════════════════════════════════
with right_col:
    st.markdown("""
    <div class="panel-card">
      <div class="panel-header">
        <div class="panel-dot" style="background:#a78bfa; box-shadow:0 0 6px #a78bfa;"></div>
        AI ASSISTANT &nbsp;·&nbsp; GPT-4o Vision
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FIX #4: Render ALL messages as ONE html block so they stay inside panel ──
    msgs_html = '<div class="chat-messages" id="chat-scroll">'
    if not st.session_state.messages:
        msgs_html += """
        <div class="empty-chat">
          <div class="icon">🧠</div>
          <p>Share your meeting tab on the left, take a screenshot, then ask me anything.</p>
        </div>"""
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                badge = ""
                if msg.get("has_screenshot"):
                    badge = '<div class="msg-screenshot-tag">📸 Screenshot attached</div>'
                safe_text = msg["text"].replace("<", "&lt;").replace(">", "&gt;")
                msgs_html += f"""
                <div class="msg-user">
                  {badge}{safe_text}
                  <div class="msg-meta">{msg["time"]}</div>
                </div>"""
            else:
                safe_text = msg["text"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                msgs_html += f"""
                <div class="msg-ai">
                  {safe_text}
                  <div class="msg-meta">🧠 MeetingMind AI · {msg["time"]}</div>
                </div>"""
    msgs_html += "</div>"

    # Auto-scroll to bottom after new message
    msgs_html += """
    <script>
      (function() {
        var el = document.getElementById('chat-scroll');
        if (el) el.scrollTop = el.scrollHeight;
      })();
    </script>
    """

    st.markdown(msgs_html, unsafe_allow_html=True)

    # ── Screenshot listener (height=0, transparent) ────────────────────────
    LISTENER_JS = """
    <script>
    window.addEventListener('message', function(e) {
      const d = e.data;
      if (!d || typeof d !== 'object') return;
      if (d.type === 'meetingmind_screenshot') {
        sessionStorage.setItem('mm_screenshot', d.data);
        sessionStorage.setItem('mm_has_screenshot', 'true');
        const n = document.createElement('div');
        n.textContent = '📸 Screenshot ready — send next message to attach it';
        n.style.cssText = 'position:fixed;bottom:80px;right:24px;background:#164e63;color:#67e8f9;padding:8px 16px;border-radius:8px;font-size:0.76rem;z-index:9999;font-family:monospace;border:1px solid #0891b2;';
        document.body.appendChild(n);
        setTimeout(() => n.remove(), 3000);
      }
      if (d.type === 'meetingmind_transcript') {
        sessionStorage.setItem('mm_transcript', d.data);
        const n = document.createElement('div');
        n.textContent = '🎙 Transcript ready — paste into chat below';
        n.style.cssText = 'position:fixed;bottom:80px;right:24px;background:#1e1b4b;color:#a5b4fc;padding:8px 16px;border-radius:8px;font-size:0.76rem;z-index:9999;font-family:monospace;border:1px solid #6366f1;';
        document.body.appendChild(n);
        setTimeout(() => n.remove(), 3000);
      }
    });
    </script>
    """
    st.components.v1.html(LISTENER_JS, height=0)

    # ── Quick action buttons ───────────────────────────────────────────────
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

    # ── Manual screenshot upload ───────────────────────────────────────────
    with st.expander("📁 Upload screenshot manually"):
        uploaded = st.file_uploader(
            "Upload screenshot", type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        if uploaded:
            img_bytes = uploaded.read()
            st.session_state.screenshot_b64 = base64.b64encode(img_bytes).decode("utf-8")
            st.session_state.pending_screenshot = True
            st.success("Screenshot loaded — will send with next message.")

    # ── Chat input (native Streamlit — works reliably) ─────────────────────
    auto_val   = st.session_state.pop("auto_prompt", "")
    user_input = st.chat_input(placeholder="Ask about your meeting… (Enter to send)")
    if auto_val and not user_input:
        user_input = auto_val

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # get_ai_response() — swap provider here when moving to Claude
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    def get_ai_response(api_key, history, user_text, screenshot_b64):
        SYSTEM = (
            "You are MeetingMind AI — an intelligent assistant embedded alongside "
            "the user's live video meeting. Be concise, direct, and helpful. "
            "When given a screenshot, describe the key information you can see. "
            "Help with meeting summaries, action items, drafting replies, or any task."
        )

        # ── ✅ CURRENT: OpenAI GPT-4o ─────────────────────────────────────
        client = OpenAI(api_key=api_key)
        content = []
        if screenshot_b64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_b64}",
                    "detail": "high",
                },
            })
        content.append({"type": "text", "text": user_text})
        messages = [{"role": "system", "content": SYSTEM}]
        messages += history
        messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model=AI_MODEL, messages=messages, max_tokens=1500
        )
        return response.choices[0].message.content

        # ── 🔮 FUTURE: Claude (uncomment, remove OpenAI block above) ──────
        # import anthropic
        # client = anthropic.Anthropic(api_key=api_key)
        # content = []
        # if screenshot_b64:
        #     content.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":screenshot_b64}})
        # content.append({"type": "text", "text": user_text})
        # response = client.messages.create(
        #     model="claude-opus-4-5", max_tokens=1500, system=SYSTEM,
        #     messages=history + [{"role": "user", "content": content}]
        # )
        # return response.content[0].text

    # ── Send ──────────────────────────────────────────────────────────────
    if user_input:
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your OpenAI API Key above.")
        else:
            now     = datetime.now().strftime("%H:%M")
            has_shot = st.session_state.pending_screenshot and st.session_state.screenshot_b64

            st.session_state.messages.append({
                "role": "user",
                "text": user_input,
                "time": now,
                "has_screenshot": bool(has_shot),
            })

            shot_b64 = None
            if has_shot:
                shot_b64 = st.session_state.screenshot_b64
                st.session_state.pending_screenshot = False
                st.session_state.screenshot_b64     = None

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
