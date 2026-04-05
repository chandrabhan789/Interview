import streamlit as st
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI PROVIDER CONFIG
# To switch to Claude later — only change these 2 lines + requirements.txt:
#   AI_MODEL     = "claude-opus-4-5"
#   ENV_KEY_NAME = "ANTHROPIC_API_KEY"
# Then swap the JS fetch block (see comments inside MAIN_APP).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI_MODEL     = "gpt-4o"
ENV_KEY_NAME = "OPENAI_API_KEY"

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Outer Streamlit CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    background: #0d0f14 !important;
    color: #e2e8f0;
    font-family: 'DM Sans', sans-serif;
  }
  /* Hide Streamlit chrome */
  #MainMenu, footer, header           { visibility: hidden !important; }
  [data-testid="manage-app-button"]   { display: none !important; }
  [data-testid="stToolbar"]           { display: none !important; }
  .viewerBadge_container__r5tak       { display: none !important; }
  .stDeployButton                     { display: none !important; }
  section[data-testid="stSidebar"]    { display: none !important; }

  .block-container {
    padding: 0.5rem 0.9rem 0 0.9rem !important;
    max-width: 100% !important;
  }
  /* Kill iframe default styling so no black boxes appear */
  iframe {
    border: none !important;
    background: transparent !important;
    display: block !important;
  }

  /* ── Header ── */
  .mm-hdr {
    display: flex; align-items: center; justify-content: space-between;
    padding: 7px 14px;
    background: linear-gradient(135deg, #1a1d27, #12151e);
    border: 1px solid #1e2435; border-radius: 10px;
    margin-bottom: 6px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }
  .mm-hdr h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.05rem; color: #7dd3fc; margin: 0;
  }
  .mm-badge {
    background: #1e3a5f; color: #7dd3fc;
    font-size: 0.62rem; padding: 2px 9px;
    border-radius: 20px; font-family: 'Space Mono', monospace;
    border: 1px solid #2563eb44;
  }
  .mm-prov { font-size: 0.65rem; color: #475569; font-family: 'Space Mono', monospace; }

  /* ── Expander & inputs ── */
  .stExpander {
    background: #12151e !important;
    border: 1px solid #1e2435 !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
  }
  .stTextInput > div > div > input {
    background: #1a1d27 !important; border: 1px solid #2a2f3e !important;
    color: #e2e8f0 !important; border-radius: 7px !important;
  }
  .stButton > button {
    background: #1e3a5f !important; color: #7dd3fc !important;
    border: 1px solid #2563eb44 !important; border-radius: 7px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.74rem !important;
  }
  .stButton > button:hover { background: #1d4ed8 !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get(ENV_KEY_NAME, "")

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-hdr">
  <h1>🧠 MeetingMind AI</h1>
  <div style="display:flex;gap:10px;align-items:center;">
    <span class="mm-prov">Powered by GPT-4o Vision</span>
    <span class="mm-badge">BETA v3.0</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────
with st.expander("⚙️ OpenAI API Key", expanded=not st.session_state.api_key):
    c1, c2 = st.columns([5, 1])
    with c1:
        key_val = st.text_input(
            "key", value=st.session_state.api_key,
            type="password", placeholder="sk-...",
            label_visibility="collapsed"
        )
    with c2:
        if st.button("Save"):
            st.session_state.api_key = key_val
            st.rerun()
    st.caption("🔑 Stored in session memory only — sent directly to OpenAI, never to any other server.")

# ── Gate: require key ─────────────────────────────────────────────────────
api_key = st.session_state.api_key
if not api_key:
    st.info("👆 Enter your OpenAI API key above to launch the app.", icon="🔑")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN APP — single HTML/JS component
#
# FIX #1 — Buttons (Share Tab / Send) not working:
#   • getDisplayMedia() is BLOCKED inside iframes unless the iframe has
#     allow="display-capture" — which Streamlit does NOT set.
#   • Fix: on startup, we inject a tiny bridge script into window.PARENT
#     (allowed because Streamlit iframes are same-origin).
#     The bridge function lives in the top-level page context and calls
#     navigator.mediaDevices.getDisplayMedia() there — which works.
#     The returned MediaStream is passed back and used directly in the
#     iframe's <video> element (cross-frame stream works in same-origin).
#   • Send button: OpenAI fetch goes directly from JS → api.openai.com
#     (CORS is allowed by OpenAI for browser clients). No Python round-trip.
#
# FIX #2 — Send button under "Manage App" badge:
#   • Streamlit's badge is hidden via CSS in the outer wrapper above.
#   • The send button is 2× larger (padding + font size doubled).
#   • Component height is tuned so the input bar is not cut off.
#
# FIX #3 — Transcript panel too small (1 line):
#   • #tbox now has min-height: 68px which comfortably shows 3 lines of text.
#   • Added a dedicated "TRANSCRIPT" sub-panel header with its own border.
#
# FIX (bonus) — No extra black boxes:
#   • Only ONE st.components.v1.html() call = only ONE iframe = no gaps.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAIN_APP = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  /* ── Reset ─────────────────────────────────────────── */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; overflow: hidden; background: transparent; }}
  body {{ font-family: 'DM Sans', 'Segoe UI', sans-serif; color: #e2e8f0; }}

  /* ── Root two-panel layout ─────────────────────────── */
  #app {{
    display: flex;
    width: 100%;
    height: 100%;
    background: #0d0f14;
    border: 1px solid #1e2435;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 6px 32px rgba(0,0,0,0.6);
  }}

  /* ── Left panel ────────────────────────────────────── */
  #LP {{
    width: 56%;
    min-width: 240px;
    max-width: 75%;
    display: flex;
    flex-direction: column;
    background: #0c0e15;
    border-right: 1px solid #1e2435;
    overflow: hidden;
    flex-shrink: 0;
  }}

  /* ── Drag handle ────────────────────────────────────── */
  #RZ {{
    width: 6px;
    flex-shrink: 0;
    background: #12151e;
    cursor: col-resize;
    position: relative;
    z-index: 20;
    transition: background 0.2s;
  }}
  #RZ:hover, #RZ.active {{ background: #1d4ed855; }}
  #RZ::after {{
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 2px;
    height: 40px;
    background: #1e2435;
    border-radius: 2px;
    transition: background 0.2s;
  }}
  #RZ:hover::after, #RZ.active::after {{ background: #3b82f6; }}

  /* ── Right panel ────────────────────────────────────── */
  #RP {{
    flex: 1;
    min-width: 240px;
    display: flex;
    flex-direction: column;
    background: #0c0e15;
    overflow: hidden;
  }}

  /* ── Panel header bar ───────────────────────────────── */
  .ph {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 13px;
    background: #12151e;
    border-bottom: 1px solid #1e2435;
    flex-shrink: 0;
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #475569;
    font-family: 'Space Mono', monospace;
  }}
  .dot {{
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
    animation: pulse 2.5s ease-in-out infinite;
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}

  /* ── Status chip ────────────────────────────────────── */
  #chip {{
    margin-left: auto;
    font-size: 0.6rem;
    padding: 2px 9px;
    border-radius: 10px;
    font-family: 'Space Mono', monospace;
    transition: all 0.3s;
    background: #1c1917;
    color: #78716c;
    border: 1px solid #44403c55;
  }}

  /* ── Control buttons row ────────────────────────────── */
  #ctrl {{
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    align-items: center;
    padding: 7px 10px;
    background: #0d0f14;
    border-bottom: 1px solid #1e2435;
    flex-shrink: 0;
  }}

  /* ── Video area (fills remaining left space) ────────── */
  #vw {{
    flex: 1;
    min-height: 0;
    background: #06080f;
    position: relative;
    overflow: hidden;
  }}
  #vid {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: none;
    background: #000;
  }}
  #vph {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    pointer-events: none;
  }}
  #vph .vico {{ font-size: 2.8rem; opacity: 0.12; }}
  #vph .vhint {{
    font-size: 0.7rem;
    color: #1d2d44;
    text-align: center;
    max-width: 200px;
    line-height: 1.8;
    font-family: 'Space Mono', monospace;
  }}

  /* ── Screenshot preview strip ───────────────────────── */
  #sstrip {{
    display: none;
    padding: 6px 10px;
    border-top: 1px solid #1e2435;
    background: #0a0c12;
    flex-shrink: 0;
  }}
  .slbl {{
    font-size: 0.58rem;
    color: #22d3ee;
    font-family: 'Space Mono', monospace;
    margin-bottom: 4px;
    letter-spacing: 0.8px;
  }}
  #simg {{
    width: 100%;
    max-height: 72px;
    object-fit: cover;
    border-radius: 5px;
    border: 1px solid #164e63;
  }}

  /* ── Transcript panel (FIX #3 — 3-line min height) ── */
  #txpanel {{
    flex-shrink: 0;
    background: #0a0c12;
    border-top: 1px solid #1e2435;
  }}
  .txhdr {{
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-bottom: 1px solid #1e2435;
    background: #0f1117;
  }}
  .txlbl {{
    font-size: 0.58rem;
    color: #334155;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .txbtns {{
    display: flex;
    gap: 4px;
    margin-left: auto;
  }}
  #tbox {{
    padding: 7px 10px;
    font-size: 0.74rem;
    color: #64748b;
    min-height: 68px;       /* ← exactly 3 lines of text */
    max-height: 90px;
    overflow-y: auto;
    font-style: italic;
    line-height: 1.55;
    scrollbar-width: thin;
    scrollbar-color: #1e2435 transparent;
    word-break: break-word;
  }}
  #tbox.active {{ color: #94a3b8; font-style: normal; }}

  /* ── RIGHT: Chat messages area (scrollable, fixed) ──── */
  /* KEY: flex:1 + min-height:0 = grows to fill but NEVER overflows panel */
  #msgs {{
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 9px;
    scrollbar-width: thin;
    scrollbar-color: #1e2435 transparent;
  }}
  .mu {{
    align-self: flex-end;
    background: #1e3a5f;
    border: 1px solid #2563eb33;
    color: #e2e8f0;
    padding: 9px 13px;
    border-radius: 14px 14px 3px 14px;
    max-width: 83%;
    font-size: 0.8rem;
    line-height: 1.5;
    word-break: break-word;
  }}
  .ma {{
    align-self: flex-start;
    background: #151823;
    border: 1px solid #252b3b;
    color: #cbd5e1;
    padding: 9px 13px;
    border-radius: 14px 14px 14px 3px;
    max-width: 88%;
    font-size: 0.8rem;
    line-height: 1.62;
    word-break: break-word;
  }}
  .mm {{ font-size: 0.6rem; color: #334155; margin-top: 5px; }}
  .sbadge {{
    display: inline-block;
    background: #164e63; color: #67e8f9;
    font-size: 0.58rem; padding: 1px 7px;
    border-radius: 4px; margin-bottom: 5px;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.5px;
  }}

  /* Typing dots */
  .tw {{ display: flex; gap: 5px; align-items: center; padding: 2px 0; }}
  .td {{
    width: 6px; height: 6px; border-radius: 50%; background: #334155;
    animation: tda 1.4s ease-in-out infinite;
  }}
  .td:nth-child(2) {{ animation-delay: .18s; }}
  .td:nth-child(3) {{ animation-delay: .36s; }}
  @keyframes tda {{ 0%,100%{{opacity:.2;transform:translateY(0)}} 50%{{opacity:1;transform:translateY(-4px)}} }}

  /* Empty state */
  .emp {{
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100%; gap: 10px;
  }}
  .ei {{ font-size: 2rem; opacity: 0.1; }}
  .ep {{
    font-size: 0.74rem; color: #1e2a3a;
    text-align: center; max-width: 185px;
    line-height: 1.7;
  }}

  /* ── Quick actions ──────────────────────────────────── */
  #qbar {{
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    padding: 6px 10px;
    border-top: 1px solid #1e2435;
    background: #0a0c12;
    flex-shrink: 0;
  }}

  /* ── Input bar (FIX #2 — send button 2× bigger) ────── */
  #ibar {{
    display: flex;
    gap: 7px;
    align-items: flex-end;
    padding: 8px 10px;
    border-top: 1px solid #1e2435;
    background: #0a0c12;
    flex-shrink: 0;
  }}
  #inp {{
    flex: 1;
    background: #12151e;
    border: 1px solid #252b3b;
    color: #e2e8f0;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 0.82rem;
    font-family: 'DM Sans', 'Segoe UI', sans-serif;
    resize: none;
    min-height: 40px;
    max-height: 100px;
    outline: none;
    line-height: 1.5;
    transition: border-color 0.2s;
  }}
  #inp:focus {{ border-color: #2563eb66; }}
  #inp::placeholder {{ color: #1e2a3a; }}

  /* ── Buttons ─────────────────────────────────────────── */
  .btn {{
    padding: 7px 12px;
    border-radius: 7px;
    border: 1px solid transparent;
    cursor: pointer;
    font-size: 0.66rem;
    font-family: 'Space Mono', monospace;
    transition: all 0.15s;
    white-space: nowrap;
    line-height: 1;
    outline: none;
  }}
  .bb  {{ background:#1e3a5f; color:#7dd3fc; border-color:#2563eb44; }}
  .bb:hover  {{ background:#1d4ed8; color:#fff; border-color:#3b82f6; }}
  .bg  {{ background:#141720; color:#475569; border-color:#1e2435; }}
  .bg:hover  {{ background:#1a1d27; color:#94a3b8; }}
  .bg:disabled {{ opacity:.35; cursor:not-allowed; }}
  .bgr {{ background:#14532d; color:#4ade80; border-color:#16a34a44; cursor:default; }}
  .bp  {{ background:#1e1b4b; color:#a5b4fc; border-color:#6366f144; }}
  .bp:hover  {{ background:#312e81; color:#c7d2fe; }}

  /* ── Send button — 2× size (FIX #2) ─────────────────── */
  #bsnd {{
    background: #1d4ed8;
    color: #fff;
    border: 1px solid #3b82f6;
    border-radius: 9px;
    padding: 0 26px;         /* wider */
    height: 52px;            /* taller — 2× of original ~26px */
    font-size: 0.84rem;      /* bigger text */
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: all 0.15s;
    letter-spacing: 0.5px;
    outline: none;
  }}
  #bsnd:hover  {{ background: #2563eb; box-shadow: 0 0 12px #3b82f644; }}
  #bsnd:disabled {{ background: #1e2435; color: #334155; border-color: #1e2435; cursor: not-allowed; box-shadow: none; }}

  /* ── Toast notification ─────────────────────────────── */
  .tst {{
    position: fixed; bottom: 14px; right: 14px;
    padding: 8px 14px; border-radius: 8px;
    font-size: 0.68rem; font-family: 'Space Mono', monospace;
    z-index: 9999; pointer-events: none;
    animation: tfade 0.25s ease;
    transition: opacity 0.4s;
    max-width: 280px; line-height: 1.4;
  }}
  @keyframes tfade {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1;transform:none}} }}
</style>
</head>
<body>
<div id="app">

  <!-- ═══════════════ LEFT PANEL ═══════════════ -->
  <div id="LP">

    <!-- Panel header -->
    <div class="ph">
      <div class="dot" style="background:#3b82f6;box-shadow:0 0 6px #3b82f699;"></div>
      Meeting View
      <span id="chip">● IDLE</span>
    </div>

    <!-- Controls -->
    <div id="ctrl">
      <button class="btn bb" id="bsh"  onclick="startCap()">📺 Share Tab</button>
      <button class="btn bg" id="bst"  onclick="stopCap()"  disabled>⏹ Stop</button>
      <button class="btn bb" id="bsc"  onclick="takeShot()" disabled>📸 Screenshot</button>
      <button class="btn bp" id="bmic" onclick="toggleMic()">🎙 Listen</button>
    </div>

    <!-- Video display -->
    <div id="vw">
      <video id="vid" autoplay muted playsinline></video>
      <canvas id="cv" style="display:none;"></canvas>
      <div id="vph">
        <div class="vico">📺</div>
        <div class="vhint">
          Click <strong style="color:#1d4ed8;">Share Tab</strong><br>
          then pick your meeting tab<br>from the browser picker.<br><br>
          <span style="color:#0f1729;">Best results on Chrome.</span>
        </div>
      </div>
    </div>

    <!-- Screenshot preview -->
    <div id="sstrip">
      <div class="slbl">📸 SCREENSHOT — WILL ATTACH TO NEXT MESSAGE</div>
      <img id="simg" src="" alt="screenshot preview"/>
    </div>

    <!-- Transcript panel (FIX #3 — dedicated panel, 3-line min height) -->
    <div id="txpanel">
      <div class="txhdr">
        <span class="txlbl">🎙 Live Transcript</span>
        <div class="txbtns">
          <button class="btn bg" onclick="useTx()"   style="padding:2px 8px;font-size:0.58rem;">↗ Ask AI</button>
          <button class="btn bg" onclick="clearTx()" style="padding:2px 8px;font-size:0.58rem;">✕</button>
        </div>
      </div>
      <div id="tbox">Transcribed meeting speech will appear here…</div>
    </div>

  </div><!-- /LP -->

  <!-- ═══════════════ DRAG HANDLE ═══════════════ -->
  <div id="RZ" title="↔ Drag to resize panels"></div>

  <!-- ═══════════════ RIGHT PANEL ═══════════════ -->
  <div id="RP">

    <!-- Panel header -->
    <div class="ph">
      <div class="dot" style="background:#a78bfa;box-shadow:0 0 6px #a78bfa99;"></div>
      AI Assistant · GPT-4o Vision
      <button class="btn bg" onclick="clearChat()"
        style="margin-left:auto;padding:3px 9px;font-size:0.58rem;">🗑 Clear</button>
    </div>

    <!-- Chat messages — scrolls internally, NEVER overflows panel -->
    <div id="msgs">
      <div class="emp" id="empstate">
        <div class="ei">🧠</div>
        <p class="ep">Share your meeting tab on the left, take a screenshot, then ask anything about what's on screen.</p>
      </div>
    </div>

    <!-- Quick actions -->
    <div id="qbar">
      <button class="btn bb" onclick="qa('sum')">🗒 Summarise</button>
      <button class="btn bb" onclick="qa('act')">✅ Action Items</button>
      <button class="btn bb" onclick="qa('rep')">💡 Draft Reply</button>
      <button class="btn bb" onclick="qa('key')">🔑 Key Points</button>
    </div>

    <!-- Input bar with big Send button -->
    <div id="ibar">
      <textarea id="inp" rows="1"
        placeholder="Ask about your meeting… (Enter to send · Shift+Enter for new line)"
        onkeydown="onK(event)"
        oninput="grow(this)"></textarea>
      <button id="bsnd" onclick="doSend()">Send ↑</button>
    </div>

  </div><!-- /RP -->

</div><!-- /app -->

<script>
// ═══════════════════════════════════════════════════════════════
// CONFIG — injected from Python session
// ═══════════════════════════════════════════════════════════════
const APIKEY = "{api_key}";
const MODEL  = "{AI_MODEL}";
const SYSPMT = "You are MeetingMind AI, a concise and smart assistant embedded alongside a live video meeting. When shown a screenshot, read it carefully and describe what you see. Help the user with summaries, action items, key decisions, drafting replies, answering questions, or any other task. Be direct and practical.";

// ═══════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════
var mediaStream = null;
var recognition = null;
var isListening = false;
var txBuffer    = "";
var pendingShot = null;   // base64 jpeg string (no prefix)
var chatHistory = [];     // {{role, content}} for API

// ═══════════════════════════════════════════════════════════════
// FIX #1 — getDisplayMedia BRIDGE
//
// Problem: Streamlit's iframe does NOT have allow="display-capture"
//   so calling navigator.mediaDevices.getDisplayMedia() inside the
//   iframe throws NotAllowedError in Chrome.
//
// Solution: Inject a tiny bridge function into window.PARENT.
//   Since the Streamlit iframe is same-origin (allow-same-origin is
//   set in sandbox), we can write to window.parent.document freely.
//   The bridge calls getDisplayMedia() in the TOP-LEVEL context
//   where it is allowed. The returned MediaStream is a JS object
//   that crosses same-origin frames without any restriction.
// ═══════════════════════════════════════════════════════════════
(function injectBridge() {{
  try {{
    if (window.parent === window) return; // not in iframe
    if (window.parent._mmBridgeReady) return; // already injected
    var s = window.parent.document.createElement('script');
    s.textContent = [
      "window._mmBridgeReady = true;",
      "window._mmGetDisplay = function(opts) {{",
      "  return navigator.mediaDevices.getDisplayMedia(opts);",
      "}};"
    ].join('\\n');
    window.parent.document.head.appendChild(s);
    console.log('[MeetingMind] capture bridge injected into parent');
  }} catch(e) {{
    console.warn('[MeetingMind] bridge inject failed — falling back to direct', e);
  }}
}})();

// Wrapper: use bridge if available, otherwise direct
async function getDisplayMedia(opts) {{
  if (window.parent && window.parent._mmGetDisplay) {{
    return await window.parent._mmGetDisplay(opts);
  }}
  // Fallback (works if app is opened directly, not in iframe)
  return await navigator.mediaDevices.getDisplayMedia(opts);
}}

// ═══════════════════════════════════════════════════════════════
// FIX #3 — DRAG-TO-RESIZE (left panel)
// ═══════════════════════════════════════════════════════════════
(function setupResize() {{
  var rz = g('RZ'), lp = g('LP'), ap = g('app');
  var dragging = false, startX = 0, startW = 0;

  rz.addEventListener('mousedown', function(e) {{
    dragging = true;
    startX   = e.clientX;
    startW   = lp.offsetWidth;
    rz.classList.add('active');
    document.body.style.cursor     = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  }});

  document.addEventListener('mousemove', function(e) {{
    if (!dragging) return;
    var appW = ap.offsetWidth;
    var newW = Math.max(240, Math.min(startW + e.clientX - startX, appW - 250));
    lp.style.width    = newW + 'px';
    lp.style.maxWidth = 'none';
  }});

  document.addEventListener('mouseup', function() {{
    if (!dragging) return;
    dragging = false;
    rz.classList.remove('active');
    document.body.style.cursor     = '';
    document.body.style.userSelect = '';
  }});
}})();

// ═══════════════════════════════════════════════════════════════
// SCREEN CAPTURE
// ═══════════════════════════════════════════════════════════════
async function startCap() {{
  try {{
    setChip('⏳ STARTING…', '#0c1a2e', '#3b82f6');
    mediaStream = await getDisplayMedia({{ video: {{ frameRate: 15 }}, audio: true }});
    var vid = g('vid');
    vid.srcObject = mediaStream;
    vid.style.display = 'block';
    g('vph').style.display = 'none';
    setBtn('bsh',  true,  '✅ Sharing',    'btn bgr');
    setBtn('bst',  false, '⏹ Stop',        'btn bg');
    setBtn('bsc',  false, '📸 Screenshot', 'btn bb');
    setChip('● LIVE', '#0d2a1a', '#4ade80');
    mediaStream.getTracks().forEach(function(t) {{
      t.addEventListener('ended', stopCap);
    }});
  }} catch(e) {{
    setChip('✖ DENIED', '#2d0a0a', '#f87171');
    setTimeout(function() {{ setChip('● IDLE', '#1c1917', '#78716c'); }}, 2500);
  }}
}}

function stopCap() {{
  if (mediaStream) {{
    mediaStream.getTracks().forEach(function(t) {{ t.stop(); }});
    mediaStream = null;
  }}
  var vid = g('vid');
  vid.srcObject = null;
  vid.style.display = 'none';
  g('vph').style.display = 'flex';
  setBtn('bsh',  false, '📺 Share Tab',  'btn bb');
  setBtn('bst',  true,  '⏹ Stop',        'btn bg');
  setBtn('bsc',  true,  '📸 Screenshot', 'btn bb');
  setChip('● IDLE', '#1c1917', '#78716c');
}}

// ═══════════════════════════════════════════════════════════════
// SCREENSHOT
// ═══════════════════════════════════════════════════════════════
function takeShot() {{
  var vid = g('vid'), cv = g('cv');
  if (!vid.srcObject || vid.videoWidth === 0) {{
    toast('⚠ Start sharing your tab first', '#2d1a00', '#fb923c'); return;
  }}
  cv.width  = vid.videoWidth  || 1280;
  cv.height = vid.videoHeight || 720;
  cv.getContext('2d').drawImage(vid, 0, 0, cv.width, cv.height);
  var dataUrl  = cv.toDataURL('image/jpeg', 0.85);
  pendingShot  = dataUrl.split(',')[1];
  g('simg').src = dataUrl;
  g('sstrip').style.display = 'block';
  toast('📸 Screenshot captured — will attach to your next message', '#0e2a33', '#67e8f9');
}}

// ═══════════════════════════════════════════════════════════════
// SPEECH RECOGNITION (Chrome Web Speech API)
// ═══════════════════════════════════════════════════════════════
function toggleMic() {{
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{
    g('tbox').textContent = '⚠ Speech API requires Chrome browser.'; return;
  }}
  if (isListening) {{ recognition.stop(); return; }}

  recognition = new SR();
  recognition.continuous     = true;
  recognition.interimResults = true;
  recognition.lang           = 'en-US';

  recognition.onstart = function() {{
    isListening = true;
    g('bmic').textContent = '⏹ Stop';
    g('bmic').className   = 'btn bp';
    setChip('🎙 LISTENING', '#1e1b4b', '#a5b4fc');
  }};

  recognition.onresult = function(e) {{
    var interim = '';
    for (var i = e.resultIndex; i < e.results.length; i++) {{
      var t = e.results[i][0].transcript;
      if (e.results[i].isFinal) {{ txBuffer += t + ' '; }}
      else {{ interim = t; }}
    }}
    var el = g('tbox');
    el.textContent = txBuffer + (interim ? '…' + interim : '');
    el.classList.add('active');
    el.scrollTop = el.scrollHeight;
  }};

  recognition.onerror = function(e) {{
    g('tbox').textContent = '⚠ Error: ' + e.error;
    g('tbox').classList.remove('active');
  }};

  recognition.onend = function() {{
    isListening = false;
    g('bmic').textContent = '🎙 Listen';
    g('bmic').className   = 'btn bp';
    setChip(mediaStream ? '● LIVE' : '● IDLE',
            mediaStream ? '#0d2a1a' : '#1c1917',
            mediaStream ? '#4ade80' : '#78716c');
  }};

  recognition.start();
}}

function useTx() {{
  var t = txBuffer.trim() || g('tbox').textContent.trim();
  if (!t || t.startsWith('Transcribed')) return;
  g('inp').value = t; grow(g('inp')); g('inp').focus();
}}

function clearTx() {{
  txBuffer = '';
  g('tbox').textContent = 'Transcribed meeting speech will appear here…';
  g('tbox').classList.remove('active');
}}

// ═══════════════════════════════════════════════════════════════
// CHAT — INPUT HELPERS
// ═══════════════════════════════════════════════════════════════
function onK(e) {{
  if (e.key === 'Enter' && !e.shiftKey) {{ e.preventDefault(); doSend(); }}
}}

function grow(el) {{
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}}

// ═══════════════════════════════════════════════════════════════
// CHAT — SEND MESSAGE  (FIX #1 — fetch to OpenAI works in browser)
// ═══════════════════════════════════════════════════════════════
async function doSend(overrideText) {{
  var inp  = g('inp');
  var text = (overrideText || inp.value).trim();
  if (!text) return;

  inp.value = '';
  grow(inp);
  g('bsnd').disabled = true;
  g('empstate') && g('empstate').remove();

  // Grab and reset screenshot
  var hasShot = !!pendingShot;
  var shot64  = pendingShot;
  pendingShot = null;
  g('sstrip').style.display = 'none';

  // Render user bubble
  addBubble('u', text, hasShot);

  // Build OpenAI content array
  var userContent = [];
  if (shot64) {{
    userContent.push({{
      type: 'image_url',
      image_url: {{ url: 'data:image/jpeg;base64,' + shot64, detail: 'high' }}
    }});
  }}
  userContent.push({{ type: 'text', text: text }});
  chatHistory.push({{ role: 'user', content: userContent }});

  // Typing indicator
  var tid = 'ty' + Date.now();
  addTyping(tid);
  g('msgs').scrollTop = g('msgs').scrollHeight;

  try {{
    // ── ✅ CURRENT: OpenAI GPT-4o ─────────────────────────────────────────
    var res = await fetch('https://api.openai.com/v1/chat/completions', {{
      method : 'POST',
      headers: {{
        'Content-Type' : 'application/json',
        'Authorization': 'Bearer ' + APIKEY
      }},
      body: JSON.stringify({{
        model      : MODEL,
        max_tokens : 1500,
        messages   : [{{ role: 'system', content: SYSPMT }}].concat(chatHistory)
      }})
    }});
    var data = await res.json();
    var el = g(tid); if (el) el.remove();

    if (data.error) throw new Error(data.error.message);
    var reply = data.choices[0].message.content;
    chatHistory.push({{ role: 'assistant', content: reply }});
    if (chatHistory.length > 24) chatHistory = chatHistory.slice(chatHistory.length - 24);
    addBubble('a', reply);

    // ── 🔮 FUTURE: Anthropic Claude — swap the block above for this ────────
    // var res = await fetch('https://api.anthropic.com/v1/messages', {{
    //   method : 'POST',
    //   headers: {{
    //     'Content-Type'      : 'application/json',
    //     'x-api-key'         : APIKEY,
    //     'anthropic-version' : '2023-06-01',
    //     'anthropic-dangerous-direct-browser-access': 'true'
    //   }},
    //   body: JSON.stringify({{
    //     model     : 'claude-opus-4-5',
    //     max_tokens: 1500,
    //     system    : SYSPMT,
    //     messages  : chatHistory
    //   }})
    // }});
    // var data  = await res.json();
    // var el = g(tid); if (el) el.remove();
    // var reply = data.content[0].text;
    // chatHistory.push({{ role: 'assistant', content: reply }});
    // addBubble('a', reply);
    // ──────────────────────────────────────────────────────────────────────

  }} catch(err) {{
    var el = g(tid); if (el) el.remove();
    addBubble('a', '⚠️ ' + err.message);
  }}

  g('bsnd').disabled = false;
}}

// ═══════════════════════════════════════════════════════════════
// QUICK ACTIONS
// ═══════════════════════════════════════════════════════════════
function qa(type) {{
  var prompts = {{
    sum: 'Please summarise everything visible on my meeting screen.',
    act: 'List all action items and decisions from this meeting so far.',
    rep: 'Based on what is being discussed, help me draft a smart response.',
    key: 'What are the key points and important numbers from this meeting?'
  }};
  if ((type === 'sum' || type === 'key') && !pendingShot) {{
    toast('📸 Take a screenshot first so I can see the screen', '#1a1a2e', '#818cf8');
    return;
  }}
  doSend(prompts[type]);
}}

function clearChat() {{
  chatHistory = [];
  g('msgs').innerHTML = '<div class="emp" id="empstate"><div class="ei">🧠</div><p class="ep">Chat cleared. Ready for a fresh start!</p></div>';
}}

// ═══════════════════════════════════════════════════════════════
// DOM HELPERS
// ═══════════════════════════════════════════════════════════════
function g(id) {{ return document.getElementById(id); }}

function addBubble(role, text, hasShot) {{
  var msgs = g('msgs');
  var div  = document.createElement('div');
  div.className = (role === 'u') ? 'mu' : 'ma';
  var now = new Date().toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
  var badge = (role === 'u' && hasShot) ? '<div class="sbadge">📸 Screenshot attached</div>' : '';
  // Safely escape HTML then restore line breaks
  var safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
  div.innerHTML = badge + safe + '<div class="mm">' + (role === 'u' ? 'You' : '🧠 GPT-4o') + ' &middot; ' + now + '</div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}}

function addTyping(id) {{
  var msgs = g('msgs');
  var div  = document.createElement('div');
  div.className = 'ma';
  div.id        = id;
  div.innerHTML = '<div class="tw"><div class="td"></div><div class="td"></div><div class="td"></div></div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}}

function setChip(text, bg, color) {{
  var el = g('chip');
  el.textContent    = text;
  el.style.background = bg;
  el.style.color    = color;
}}

function setBtn(id, disabled, text, cls) {{
  var el = g(id);
  el.disabled   = disabled;
  el.textContent = text;
  el.className  = cls;
}}

function toast(msg, bg, color) {{
  var el = document.createElement('div');
  el.className = 'tst';
  el.textContent = msg;
  el.style.background = bg;
  el.style.color      = color;
  el.style.border     = '1px solid ' + color + '55';
  document.body.appendChild(el);
  setTimeout(function() {{ el.style.opacity = '0'; }}, 2600);
  setTimeout(function() {{ el.remove(); }}, 3100);
}}
</script>
</body>
</html>"""

# Single component render — no extra iframes, no black boxes
st.components.v1.html(MAIN_APP, height=730, scrolling=False)

