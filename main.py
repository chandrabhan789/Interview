import streamlit as st
import streamlit.components.v1 as stcomp
import tempfile
import os
import base64
from datetime import datetime
from openai import OpenAI

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI PROVIDER
# To switch to Claude: change AI_MODEL + ENV_KEY_NAME, swap get_ai_response()
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI_MODEL     = "gpt-4o"
ENV_KEY_NAME = "OPENAI_API_KEY"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAPTURE COMPONENT HTML
#
# WHY declare_component instead of st.components.v1.html?
#   st.components.v1.html() is ONE-WAY: JS → (nothing) → Python.
#   st.components.v1.declare_component() is TWO-WAY:
#     Python → component → JS → stSend() → Python gets the return value.
#   This is the ONLY official Streamlit way to get data from JS back to Python.
#
# HOW screenshot gets to Python:
#   1. User clicks "📸 Screenshot → AI"
#   2. JS draws canvas, calls stSend({type:'screenshot', data:dataUrl, ts:...})
#   3. Streamlit receives this, triggers a rerun
#   4. capture_widget(key="cap") returns {type:'screenshot', data:...}
#   5. Python reads it, saves to session_state.screenshot_b64
#   6. Next chat message automatically attaches it to the OpenAI API call
#
# WHY getDisplayMedia works here:
#   declare_component with path= serves files from localhost:8501/component/...
#   This is SAME-ORIGIN as Streamlit, so Chrome allows getDisplayMedia.
#   (Same reason V1's st.components.v1.html worked — same sandbox flags.)
#
# WHY transcript was invisible before:
#   aspect-ratio:16/9 on a wide screen made the video ~600px tall,
#   pushing transcript below the iframe's bottom. Fixed: max-height:220px on video.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAPTURE_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    background: #0d0f14; color: #e2e8f0;
    font-family: 'Segoe UI', 'DM Sans', sans-serif;
    height: 100%; overflow-y: auto; overflow-x: hidden;
  }

  #root { display: flex; flex-direction: column; gap: 10px; padding: 12px; }

  /* Controls bar */
  #ctrl { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; }

  /* Status pill */
  #pill {
    font-size: 0.65rem; padding: 2px 9px; border-radius: 10px;
    font-family: monospace; margin-left: auto; transition: all 0.3s;
    background: #1c1917; color: #78716c; border: 1px solid #44403c55;
  }

  /* Video area — max-height capped so transcript always shows */
  #vwrap {
    position: relative; background: #060810;
    border: 1px solid #1e2435; border-radius: 10px;
    overflow: hidden;
    width: 100%;
    max-height: 220px;     /* FIXED: was aspect-ratio:16/9 which made it too tall */
    min-height: 130px;
  }
  #vid {
    width: 100%; height: 100%; max-height: 220px;
    object-fit: contain; display: none; background: #000;
  }
  #vph {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 10px;
    min-height: 130px;
  }
  .vph-icon { font-size: 2rem; opacity: 0.18; }
  .vph-hint {
    font-size: 0.72rem; color: #1e3a5f; text-align: center;
    max-width: 210px; line-height: 1.75; font-family: monospace;
  }

  /* Screenshot preview */
  #shot-wrap { display: none; }
  .shot-lbl {
    font-size: 0.6rem; color: #22d3ee; font-family: monospace;
    letter-spacing: 0.8px; margin-bottom: 4px; text-transform: uppercase;
  }
  #shot-img {
    width: 100%; max-height: 80px; object-fit: cover;
    border-radius: 6px; border: 1px solid #164e63;
  }

  /* Transcript section */
  #tx-section {
    border-top: 1px solid #1e2435; padding-top: 10px;
    display: flex; flex-direction: column; gap: 7px;
  }
  .tx-title {
    font-size: 0.62rem; color: #334155; font-family: monospace;
    letter-spacing: 1px; text-transform: uppercase;
  }
  .tx-btns { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  #tx-box {
    background: #0f1117; border: 1px solid #1e293b; border-radius: 8px;
    padding: 8px 10px; font-size: 0.78rem; color: #64748b;
    min-height: 72px;      /* 3 lines */
    max-height: 90px; overflow-y: auto;
    font-style: italic; line-height: 1.6;
    scrollbar-width: thin; scrollbar-color: #1e2435 transparent;
    word-break: break-word;
  }
  #tx-box.live { color: #94a3b8; font-style: normal; }

  /* Buttons */
  .btn {
    padding: 6px 11px; border-radius: 7px; border: 1px solid transparent;
    cursor: pointer; font-size: 0.7rem; font-family: monospace;
    transition: all 0.15s; white-space: nowrap; line-height: 1;
  }
  .bb { background: #1e3a5f; color: #7dd3fc; border-color: #2563eb44; }
  .bb:hover { background: #1d4ed8; color: #fff; border-color: #3b82f6; }
  .bb:disabled { background: #141720; color: #334155; cursor: not-allowed; }
  .bg { background: #1c1917; color: #78716c; border-color: #44403c55; }
  .bg:hover { background: #292524; color: #a8a29e; }
  .bgr { background: #14532d; color: #4ade80; border-color: #16a34a44; cursor: default; }
  .bp { background: #1e1b4b; color: #a5b4fc; border-color: #6366f144; }
  .bp:hover { background: #312e81; color: #c7d2fe; }
  .bc { background: #164e63; color: #67e8f9; border-color: #0891b244; }
  .bc:hover { background: #0e7490; color: #fff; }

  /* Sent flash badge */
  #sent-badge {
    display: none; position: fixed; bottom: 12px; right: 12px;
    background: #164e63; color: #67e8f9; border: 1px solid #0891b2;
    padding: 7px 13px; border-radius: 8px; font-size: 0.68rem;
    font-family: monospace; z-index: 999;
    animation: fadein 0.2s ease;
  }
  @keyframes fadein { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:none} }
</style>
</head>
<body>
<div id="root">

  <!-- Controls -->
  <div id="ctrl">
    <button class="btn bb" id="bShare" onclick="startCapture()">📺 Share Tab</button>
    <button class="btn bg" id="bStop"  onclick="stopCapture()" disabled>⏹ Stop</button>
    <button class="btn bb" id="bShot"  onclick="takeShot()"    disabled>📸 Screenshot → AI</button>
    <span id="pill">● IDLE</span>
  </div>

  <!-- Video -->
  <div id="vwrap">
    <video id="vid" autoplay muted playsinline></video>
    <canvas id="cv" style="display:none"></canvas>
    <div id="vph">
      <div class="vph-icon">📺</div>
      <div class="vph-hint">
        Click <strong style="color:#3b82f6">Share Tab</strong> and select your meeting tab.<br><br>
        <span style="color:#1e3a5f">Best on Chrome.</span>
      </div>
    </div>
  </div>

  <!-- Screenshot preview -->
  <div id="shot-wrap">
    <div class="shot-lbl">📸 Screenshot captured — sends with next message</div>
    <img id="shot-img" src="" alt="screenshot"/>
  </div>

  <!-- Transcript — always visible, 3-line min -->
  <div id="tx-section">
    <div class="tx-title">🎙 Live Transcript</div>
    <div class="tx-btns">
      <button class="btn bp" id="bMic" onclick="toggleMic()">🎙 Start Listening</button>
      <button class="btn bc" onclick="useTranscript()">↗ Use as AI Question</button>
      <button class="btn bg" onclick="clearTx()" style="padding:5px 8px;font-size:0.62rem;">✕</button>
    </div>
    <div id="tx-box">Transcribed speech will appear here…</div>
  </div>

</div>

<div id="sent-badge">📸 Screenshot sent to AI!</div>

<script>
var ms = null, rec = null, recognizing = false, txFull = '';

// ── Streamlit bidirectional communication ──────────────────────────────
// This is the official protocol for declare_component components.
// stReady() tells Streamlit the component is loaded.
// stSend(value) sends data back to Python — Python receives it as the
// return value of capture_widget(key="cap").
function stReady() {
  window.parent.postMessage({
    isStreamlitMessage: true,
    type: 'streamlit:componentReady',
    apiVersion: 1
  }, '*');
}

function stSend(val) {
  window.parent.postMessage({
    isStreamlitMessage: true,
    type: 'streamlit:setComponentValue',
    value: val,
    dataType: 'json'
  }, '*');
}

window.addEventListener('load', stReady);

// ── Screen capture ─────────────────────────────────────────────────────
async function startCapture() {
  try {
    ms = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: 15 },
      audio: true
    });
    var v = document.getElementById('vid');
    v.srcObject = ms;
    v.style.display = 'block';
    document.getElementById('vph').style.display = 'none';
    setBtn('bShare', true,  '✅ Sharing',         'btn bgr');
    setBtn('bStop',  false, '⏹ Stop',             'btn bg');
    setBtn('bShot',  false, '📸 Screenshot → AI', 'btn bb');
    setPill('● LIVE', '#14532d', '#4ade80');
    ms.getTracks().forEach(function(t) {
      t.addEventListener('ended', stopCapture);
    });
  } catch(e) {
    setPill('✖ DENIED', '#450a0a', '#f87171');
    setTimeout(function() { setPill('● IDLE', '#1c1917', '#78716c'); }, 2200);
  }
}

function stopCapture() {
  if (ms) { ms.getTracks().forEach(function(t) { t.stop(); }); ms = null; }
  var v = document.getElementById('vid');
  v.srcObject = null; v.style.display = 'none';
  document.getElementById('vph').style.display = 'flex';
  setBtn('bShare', false, '📺 Share Tab',       'btn bb');
  setBtn('bStop',  true,  '⏹ Stop',             'btn bg');
  setBtn('bShot',  true,  '📸 Screenshot → AI', 'btn bb');
  setPill('● IDLE', '#1c1917', '#78716c');
}

// ── Screenshot → sends to Python via stSend() ──────────────────────────
function takeShot() {
  var v = document.getElementById('vid');
  var cv = document.getElementById('cv');
  if (!v.srcObject || v.videoWidth === 0) {
    setPill('⚠ No video yet', '#2d1a00', '#fb923c');
    setTimeout(function() { setPill('● LIVE', '#14532d', '#4ade80'); }, 1500);
    return;
  }
  cv.width  = v.videoWidth;
  cv.height = v.videoHeight;
  cv.getContext('2d').drawImage(v, 0, 0, cv.width, cv.height);
  var dataUrl = cv.toDataURL('image/jpeg', 0.85);

  // Show preview in the panel
  document.getElementById('shot-img').src = dataUrl;
  document.getElementById('shot-wrap').style.display = 'block';

  // Flash confirmation badge
  var badge = document.getElementById('sent-badge');
  badge.style.display = 'block';
  setTimeout(function() { badge.style.display = 'none'; }, 2500);

  setPill('📸 SENT', '#164e63', '#67e8f9');
  setTimeout(function() { setPill('● LIVE', '#14532d', '#4ade80'); }, 1500);

  // ★ KEY: send base64 data to Python via Streamlit component protocol
  stSend({ type: 'screenshot', data: dataUrl, ts: Date.now() });
}

// ── Audio transcription ────────────────────────────────────────────────
function toggleMic() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    document.getElementById('tx-box').textContent = '⚠ Speech recognition requires Chrome.';
    return;
  }
  if (recognizing) { rec.stop(); return; }

  rec = new SR();
  rec.continuous     = true;
  rec.interimResults = true;
  rec.lang           = 'en-US';

  rec.onstart = function() {
    recognizing = true;
    setBtn('bMic', false, '⏹ Stop Listening', 'btn bp');
    setPill('🎙 LISTENING', '#1e1b4b', '#a5b4fc');
  };

  rec.onresult = function(e) {
    var interim = '';
    for (var i = e.resultIndex; i < e.results.length; i++) {
      var t = e.results[i][0].transcript;
      if (e.results[i].isFinal) { txFull += t + ' '; }
      else { interim = t; }
    }
    var el = document.getElementById('tx-box');
    el.textContent = txFull + (interim ? '…' + interim : '');
    el.classList.add('live');
    el.scrollTop = el.scrollHeight;
  };

  rec.onerror = function(e) {
    document.getElementById('tx-box').textContent = '⚠ Error: ' + e.error;
    document.getElementById('tx-box').classList.remove('live');
  };

  rec.onend = function() {
    recognizing = false;
    setBtn('bMic', false, '🎙 Start Listening', 'btn bp');
    setPill(ms ? '● LIVE' : '● IDLE',
            ms ? '#14532d' : '#1c1917',
            ms ? '#4ade80' : '#78716c');
  };

  rec.start();
}

// Send transcript text to Python as auto_prompt
function useTranscript() {
  var t = txFull.trim();
  if (!t) { t = document.getElementById('tx-box').textContent.trim(); }
  if (!t || t.indexOf('Transcribed') === 0) return;
  stSend({ type: 'transcript', data: t, ts: Date.now() });
}

function clearTx() {
  txFull = '';
  document.getElementById('tx-box').textContent = 'Transcribed speech will appear here…';
  document.getElementById('tx-box').classList.remove('live');
}

// ── DOM helpers ────────────────────────────────────────────────────────
function setPill(t, bg, c) {
  var el = document.getElementById('pill');
  el.textContent = t; el.style.background = bg; el.style.color = c;
}
function setBtn(id, dis, txt, cls) {
  var el = document.getElementById(id);
  el.disabled = dis; el.textContent = txt; el.className = cls;
}
</script>
</body>
</html>"""


# ── Register capture component (once, cached) ──────────────────────────────
@st.cache_resource
def _make_capture_component():
    """
    Write CAPTURE_HTML to a temp dir and register it as a proper
    Streamlit declare_component. This enables bidirectional communication:
    Python → renders component, JS → stSend() → Python receives return value.
    The iframe persists across Streamlit reruns (video stream stays alive).
    """
    d = tempfile.mkdtemp()
    with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(CAPTURE_HTML)
    return stcomp.declare_component("meeting_capture_v5", path=d)


capture_widget = _make_capture_component()


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }

  /* Hide ALL Streamlit UI chrome */
  #MainMenu, footer, header                { visibility: hidden !important; }
  [data-testid="manage-app-button"]        { display: none !important; }
  [data-testid="stToolbar"]               { display: none !important; }
  [data-testid="stDecoration"]            { display: none !important; }
  .viewerBadge_container__r5tak          { display: none !important; }
  .stDeployButton                         { display: none !important; }
  section[data-testid="stSidebar"]        { display: none !important; }

  .block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

  /* Transparent iframes — no black boxes */
  iframe { background: transparent !important; border: none !important; display: block !important; }

  /* ── App header ── */
  .app-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(135deg, #1a1d27 0%, #12151e 100%);
    border: 1px solid #2a2f3e; border-radius: 12px;
    margin-bottom: 1rem; box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  }
  .app-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem; color: #7dd3fc; margin: 0;
  }
  .header-badge {
    background: #1e3a5f; color: #7dd3fc; font-size: 0.72rem;
    padding: 3px 10px; border-radius: 20px;
    font-family: 'Space Mono', monospace; border: 1px solid #2563eb44;
  }

  /* ── Chat messages: fixed height, scroll inside ── */
  .chat-messages {
    height: 420px;
    overflow-y: auto;
    padding: 1rem;
    display: flex; flex-direction: column; gap: 12px;
    scrollbar-width: thin; scrollbar-color: #1e2435 transparent;
    background: #0d0f14;
    border: 1px solid #1e2435; border-radius: 10px;
    margin-bottom: 0.5rem;
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

  /* ── Screenshot pending badge ── */
  .shot-pending {
    background: #0e2e3b; border: 1px solid #0891b2;
    color: #67e8f9; padding: 6px 12px; border-radius: 8px;
    font-size: 0.76rem; font-family: 'Space Mono', monospace;
    margin-bottom: 8px; display: inline-block;
  }

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

  /* ── Chat input: 2× bigger send button ── */
  [data-testid="stChatInputTextArea"] { min-height: 50px !important; font-size: 0.88rem !important; }
  [data-testid="stChatInputSubmitButton"] { width: 50px !important; height: 50px !important; }
  [data-testid="stChatInputSubmitButton"] svg { width: 22px !important; height: 22px !important; }

  /* ── Panel section header ── */
  .section-hdr {
    display: flex; align-items: center; gap: 8px;
    padding: 0.5rem 0; margin-bottom: 0.5rem;
    font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.5px; text-transform: uppercase;
    color: #64748b; font-family: 'Space Mono', monospace;
    border-bottom: 1px solid #1e2435; padding-bottom: 8px;
  }
  .section-dot {
    width: 7px; height: 7px; border-radius: 50%;
    box-shadow: 0 0 5px currentColor;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"          not in st.session_state: st.session_state.messages          = []
if "screenshot_b64"    not in st.session_state: st.session_state.screenshot_b64    = None
if "pending_screenshot" not in st.session_state: st.session_state.pending_screenshot = False
if "last_result_ts"    not in st.session_state: st.session_state.last_result_ts    = 0
if "api_key"           not in st.session_state: st.session_state.api_key           = os.environ.get(ENV_KEY_NAME, "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🧠 MeetingMind AI</h1>
  <span class="header-badge">GPT-4o Vision · v5.0</span>
</div>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
with st.expander("⚙️ OpenAI API Key", expanded=(not st.session_state.api_key)):
    col_k1, col_k2 = st.columns([4, 1])
    with col_k1:
        key_input = st.text_input(
            "key", value=st.session_state.api_key, type="password",
            placeholder="sk-...", label_visibility="collapsed",
        )
    with col_k2:
        if st.button("Save Key"):
            st.session_state.api_key = key_input
            st.success("Saved!")
    st.caption("🔑 Stored in session only — sent directly to OpenAI, never persisted.")

# ── Two-column layout ─────────────────────────────────────────────────────────
left_col, right_col = st.columns([1.1, 0.9], gap="small")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Capture component (bidirectional)
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div class="section-hdr">
      <div class="section-dot" style="color:#3b82f6;"></div>
      MEETING VIEW · Browser Tab Capture
    </div>
    """, unsafe_allow_html=True)

    # Render the capture component and receive its return value.
    # result is None normally; becomes a dict when user takes screenshot or
    # clicks "Use as AI Question" in the component.
    result = capture_widget(key="cap", default=None)

    # ── Handle component return value ──────────────────────────────────────
    if result is not None:
        result_ts = result.get("ts", 0)

        # Only process each event once (by timestamp)
        if result_ts > st.session_state.last_result_ts:
            st.session_state.last_result_ts = result_ts

            if result.get("type") == "screenshot":
                # Strip the data:image/jpeg;base64, prefix, keep only base64
                data_url = result.get("data", "")
                if "," in data_url:
                    st.session_state.screenshot_b64    = data_url.split(",", 1)[1]
                    st.session_state.pending_screenshot = True

            elif result.get("type") == "transcript":
                # Use transcript text as the next chat question
                st.session_state["auto_prompt"] = result.get("data", "")

    # Show "screenshot pending" indicator above the AI panel
    if st.session_state.pending_screenshot and st.session_state.screenshot_b64:
        st.markdown('<div class="shot-pending">📸 Screenshot attached — sends with next message</div>',
                    unsafe_allow_html=True)

    # Manual screenshot upload (fallback for non-Chrome or any issues)
    with st.expander("📁 Or upload a screenshot manually"):
        uploaded = st.file_uploader(
            "Upload screenshot", type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )
        if uploaded:
            img_bytes = uploaded.read()
            st.session_state.screenshot_b64    = base64.b64encode(img_bytes).decode("utf-8")
            st.session_state.pending_screenshot = True
            st.success("Screenshot loaded — will send with next message.")

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — AI Chat
# ══════════════════════════════════════════════════════════════════════════════
with right_col:
    st.markdown("""
    <div class="section-hdr">
      <div class="section-dot" style="color:#a78bfa;"></div>
      AI ASSISTANT · GPT-4o Vision
    </div>
    """, unsafe_allow_html=True)

    # ── Render ALL messages as ONE html block (keeps them in fixed-height box) ──
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
                safe = msg["text"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                msgs_html += f'<div class="msg-user">{badge}{safe}<div class="msg-meta">{msg["time"]}</div></div>'
            else:
                safe = (msg["text"]
                        .replace("&","&amp;")
                        .replace("<","&lt;")
                        .replace(">","&gt;")
                        .replace("\n","<br>"))
                msgs_html += f'<div class="msg-ai">{safe}<div class="msg-meta">🧠 MeetingMind AI · {msg["time"]}</div></div>'
    msgs_html += "</div>"
    # Auto-scroll to bottom
    msgs_html += "<script>(function(){var e=document.getElementById('chat-scroll');if(e)e.scrollTop=e.scrollHeight;})();</script>"
    st.markdown(msgs_html, unsafe_allow_html=True)

    # ── Quick action buttons ───────────────────────────────────────────────
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("📸 Attach screenshot", key="qa_shot"):
            if st.session_state.screenshot_b64:
                st.session_state.pending_screenshot = True
                st.success("Screenshot will attach to next message.")
            else:
                st.warning("Take a screenshot first (left panel).")
    with qa2:
        if st.button("🗒 Summarise screen", key="qa_sum"):
            if st.session_state.screenshot_b64:
                st.session_state.pending_screenshot = True
                st.session_state["auto_prompt"] = "Please summarise everything you can see on my meeting screen."
            else:
                st.warning("Take a screenshot first (left panel).")
    with qa3:
        if st.button("🗑 Clear chat", key="qa_clear"):
            st.session_state.messages = []
            st.rerun()

    # ── Chat input ─────────────────────────────────────────────────────────
    auto_val   = st.session_state.pop("auto_prompt", "")
    user_input = st.chat_input(placeholder="Ask about your meeting… (Enter to send)")
    if auto_val and not user_input:
        user_input = auto_val

    # ── AI response function ───────────────────────────────────────────────
    def get_ai_response(api_key, history, user_text, screenshot_b64):
        SYSTEM = (
            "You are MeetingMind AI — a smart assistant embedded alongside a live "
            "video meeting. When given a screenshot, read it carefully and describe "
            "the key information. Help with summaries, action items, answering "
            "questions about the meeting, drafting replies, or any other task. "
            "Be concise and direct."
        )
        # ── ✅ CURRENT: OpenAI GPT-4o ─────────────────────────────────────
        client   = OpenAI(api_key=api_key)
        content  = []
        if screenshot_b64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_b64}",
                    "detail": "high",
                },
            })
        content.append({"type": "text", "text": user_text})
        messages = [{"role": "system", "content": SYSTEM}] + history
        messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model=AI_MODEL, messages=messages, max_tokens=1500
        )
        return response.choices[0].message.content

        # ── 🔮 FUTURE: Claude — replace block above with this ─────────────
        # import anthropic
        # client = anthropic.Anthropic(api_key=api_key)
        # content = []
        # if screenshot_b64:
        #     content.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":screenshot_b64}})
        # content.append({"type":"text","text":user_text})
        # response = client.messages.create(
        #     model="claude-opus-4-5", max_tokens=1500, system=SYSTEM,
        #     messages=history + [{"role":"user","content":content}]
        # )
        # return response.content[0].text

    # ── Send message ───────────────────────────────────────────────────────
    if user_input:
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your OpenAI API Key above.")
        else:
            now      = datetime.now().strftime("%H:%M")
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
