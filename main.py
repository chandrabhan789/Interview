import streamlit as st
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI PROVIDER — currently OpenAI (GPT-4o).
# To switch to Claude later, change these 2 lines + update requirements.txt:
#   AI_MODEL     = "claude-opus-4-5"
#   ENV_KEY_NAME = "ANTHROPIC_API_KEY"
# Then in the JS inside MAIN_APP, uncomment the "FUTURE: Claude" fetch block
# and comment out the OpenAI block.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI_MODEL     = "gpt-4o"
ENV_KEY_NAME = "OPENAI_API_KEY"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Outer Streamlit CSS (wrapper only) ───────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');
  html, body, [class*="css"] { background: #0d0f14 !important; color: #e2e8f0; font-family: 'DM Sans', sans-serif; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0.6rem 1rem 0 1rem !important; max-width: 100% !important; }
  section[data-testid="stSidebar"] { display: none; }
  /* Remove iframe chrome — kills the black boxes */
  iframe { border: none !important; background: transparent !important; display: block !important; }
  /* Header */
  .mm-hdr {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 16px;
    background: linear-gradient(135deg, #1a1d27, #12151e);
    border: 1px solid #1e2435; border-radius: 10px;
    margin-bottom: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }
  .mm-hdr h1 { font-family: 'Space Mono', monospace; font-size: 1.1rem; color: #7dd3fc; margin: 0; }
  .mm-badge  { background:#1e3a5f; color:#7dd3fc; font-size:0.65rem; padding:2px 9px; border-radius:20px; font-family:'Space Mono',monospace; border:1px solid #2563eb44; }
  .mm-prov   { font-size:0.68rem; color:#475569; font-family:'Space Mono',monospace; }
  /* Expander & inputs */
  .stExpander { background:#12151e !important; border:1px solid #1e2435 !important; border-radius:8px !important; margin-bottom:8px !important; }
  .stTextInput > div > div > input { background:#1a1d27 !important; border:1px solid #2a2f3e !important; color:#e2e8f0 !important; border-radius:7px !important; }
  .stButton > button { background:#1e3a5f !important; color:#7dd3fc !important; border:1px solid #2563eb44 !important; border-radius:7px !important; font-family:'Space Mono',monospace !important; font-size:0.75rem !important; }
  .stButton > button:hover { background:#1d4ed8 !important; color:#fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get(ENV_KEY_NAME, "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-hdr">
  <h1>🧠 MeetingMind AI</h1>
  <div style="display:flex;gap:12px;align-items:center;">
    <span class="mm-prov">Powered by GPT-4o Vision</span>
    <span class="mm-badge">BETA v2.0</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
with st.expander("⚙️ OpenAI API Key", expanded=not st.session_state.api_key):
    c1, c2 = st.columns([5, 1])
    with c1:
        key_val = st.text_input("key", value=st.session_state.api_key, type="password",
                                placeholder="sk-...", label_visibility="collapsed")
    with c2:
        if st.button("Save"):
            st.session_state.api_key = key_val
            st.rerun()
    st.caption("🔑 Stored in browser session only. Sent directly to OpenAI — never to any other server.")

# ── Gate ──────────────────────────────────────────────────────────────────────
api_key = st.session_state.api_key
if not api_key:
    st.info("👆 Enter your OpenAI API key above to launch the app.", icon="🔑")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN APP — one single HTML component (fixes all 4 UI observations):
#
#  ✅ Fix #2 — No extra black boxes: previously 2 separate st.components calls
#              created 2 iframes each with a black background. Now it's 1 iframe.
#
#  ✅ Fix #3 — Resizable left panel: pure JS drag handle on the #resizer div
#              lets user drag to any width between 260px and 78% of total.
#
#  ✅ Fix #4 — Chat stays in panel: #chat-msgs uses flex:1 + min-height:0
#              (critical CSS trick) so it shrinks to fit and scrolls internally,
#              never overflowing the panel.
#
#  ℹ️  Fix #1 — "Sharing to github.com": this is a Chrome browser notification
#              (the tab bar shows what you're sharing to). It cannot be hidden
#              from within the web app — it's a browser-level security feature.
#              Workaround: open the app in a separate Chrome window, then share
#              only the meeting tab from the picker.
#
#  API calls go directly from JS → OpenAI (no Python round-trip).
#  API key is injected via Python f-string into a JS const.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAIN_APP = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'DM Sans', 'Segoe UI', sans-serif; overflow: hidden; }}

  /* ── Root layout ─────────────────────────────────────── */
  #app {{
    display: flex; width: 100%; height: 680px;
    background: #0d0f14;
    border: 1px solid #1e2435; border-radius: 12px;
    overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.6);
  }}

  /* ── Left panel ──────────────────────────────────────── */
  #LP {{
    width: 55%; min-width: 260px; max-width: 78%;
    display: flex; flex-direction: column;
    background: #0f1117;
    border-right: 1px solid #1e2435;
    overflow: hidden;
  }}

  /* ── Drag handle ─────────────────────────────────────── */
  #RZ {{
    width: 5px; flex-shrink: 0;
    background: #12151e; cursor: col-resize;
    position: relative; transition: background 0.2s; z-index: 10;
  }}
  #RZ::after {{
    content: '⠿'; position: absolute;
    top: 50%; left: 50%; transform: translate(-50%,-50%);
    color: #1e2435; font-size: 13px;
    writing-mode: vertical-rl; letter-spacing: -2px;
    transition: color 0.2s;
  }}
  #RZ:hover, #RZ.on {{ background: #1d4ed833; }}
  #RZ:hover::after, #RZ.on::after {{ color: #3b82f6; }}

  /* ── Right panel ─────────────────────────────────────── */
  #RP {{
    flex: 1; min-width: 260px;
    display: flex; flex-direction: column;
    background: #0f1117; overflow: hidden;
  }}

  /* ── Panel header ────────────────────────────────────── */
  .ph {{
    display: flex; align-items: center; gap: 7px;
    padding: 9px 13px;
    background: #12151e; border-bottom: 1px solid #1e2435;
    flex-shrink: 0;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: #475569;
    font-family: 'Space Mono', monospace;
  }}
  .dot {{
    width: 7px; height: 7px; border-radius: 50%;
    animation: blink 2.4s ease-in-out infinite;
    flex-shrink: 0;
  }}
  @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}
  #spill {{
    margin-left: auto; font-size: 0.62rem; padding: 2px 8px;
    border-radius: 10px; font-family: 'Space Mono', monospace;
    transition: all 0.3s;
    background:#1c1917; color:#78716c; border:1px solid #44403c44;
  }}

  /* ── Left: controls bar ──────────────────────────────── */
  #ctrl {{
    display: flex; gap: 5px; flex-wrap: wrap; align-items: center;
    padding: 8px 11px;
    background: #0d0f14; border-bottom: 1px solid #1e2435;
    flex-shrink: 0;
  }}

  /* ── Left: video area ────────────────────────────────── */
  #vw {{
    flex: 1; background: #060810;
    position: relative; overflow: hidden; min-height: 0;
  }}
  #vid {{ width:100%; height:100%; object-fit:contain; display:none; }}
  #vph {{
    position: absolute; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 10px;
  }}
  #vph .ico {{ font-size: 3rem; opacity: 0.15; }}
  #vph .hint {{
    font-size: 0.72rem; color: #1e3a5f; text-align: center;
    max-width: 185px; line-height: 1.75; font-family: 'Space Mono', monospace;
  }}

  /* ── Left: screenshot strip ──────────────────────────── */
  #sstrip {{
    display: none; padding: 7px 11px;
    border-top: 1px solid #1e2435;
    background: #0d0f14; flex-shrink: 0;
  }}
  #sstrip img {{ width:100%; max-height:78px; object-fit:cover; border-radius:6px; border:1px solid #1e2435; }}
  .slbl {{ font-size: 0.6rem; color:#22d3ee; font-family:'Space Mono',monospace; margin-bottom:4px; }}

  /* ── Left: audio strip ───────────────────────────────── */
  #astrip {{
    padding: 7px 11px; border-top: 1px solid #1e2435;
    background: #0d0f14; flex-shrink: 0;
  }}
  .arow {{ display:flex; gap:5px; align-items:center; margin-bottom:5px; }}
  #tbox {{
    background: #12151e; border: 1px solid #1e2435;
    border-radius: 6px; padding: 6px 9px;
    font-size: 0.72rem; color: #64748b;
    min-height: 32px; max-height: 52px;
    overflow-y: auto; font-style: italic; line-height: 1.4;
    scrollbar-width: thin;
  }}

  /* ── Right: chat messages (KEY FIX) ─────────────────── */
  /* flex:1 + min-height:0 = shrinks to fit, scrolls inside */
  #msgs {{
    flex: 1; min-height: 0;
    overflow-y: auto; padding: 12px;
    display: flex; flex-direction: column; gap: 9px;
    scrollbar-width: thin; scrollbar-color: #1e2435 transparent;
  }}
  .mu {{
    align-self: flex-end;
    background: #1e3a5f; border: 1px solid #2563eb33;
    color: #e2e8f0; padding: 9px 12px;
    border-radius: 14px 14px 3px 14px;
    max-width: 84%; font-size: 0.8rem; line-height: 1.5; word-break: break-word;
  }}
  .ma {{
    align-self: flex-start;
    background: #1a1d27; border: 1px solid #2a2f3e;
    color: #cbd5e1; padding: 9px 12px;
    border-radius: 14px 14px 14px 3px;
    max-width: 88%; font-size: 0.8rem; line-height: 1.6; word-break: break-word;
  }}
  .mm {{ font-size: 0.6rem; color: #475569; margin-top: 5px; }}
  .sbadge {{
    display: inline-block; background:#164e63; color:#67e8f9;
    font-size: 0.6rem; padding: 1px 7px; border-radius: 5px;
    margin-bottom: 5px; font-family: 'Space Mono', monospace;
  }}
  .tw {{ display:flex; gap:4px; align-items:center; }}
  .td {{
    width:6px; height:6px; border-radius:50%; background:#475569;
    animation: td 1.3s ease-in-out infinite;
  }}
  .td:nth-child(2){{animation-delay:.15s}} .td:nth-child(3){{animation-delay:.3s}}
  @keyframes td {{ 0%,100%{{opacity:.2;transform:translateY(0)}} 50%{{opacity:1;transform:translateY(-4px)}} }}
  .empty {{
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; height:100%; gap:10px;
  }}
  .empty .ei {{ font-size:2rem; opacity:0.15; }}
  .empty p {{ font-size:0.74rem; color:#334155; text-align:center; max-width:190px; line-height:1.65; }}

  /* ── Right: quick actions ────────────────────────────── */
  #qbar {{
    display:flex; gap:5px; flex-wrap:wrap;
    padding: 7px 11px; border-top: 1px solid #1e2435;
    background: #0d0f14; flex-shrink: 0;
  }}

  /* ── Right: input bar ────────────────────────────────── */
  #ibar {{
    display:flex; gap:6px; align-items:flex-end;
    padding: 9px 11px; border-top: 1px solid #1e2435;
    background: #0d0f14; flex-shrink: 0;
  }}
  #inp {{
    flex:1; background:#12151e; border:1px solid #2a2f3e;
    color:#e2e8f0; border-radius:8px; padding:8px 11px;
    font-size:0.8rem; font-family:'DM Sans','Segoe UI',sans-serif;
    resize:none; min-height:36px; max-height:96px;
    outline:none; line-height:1.45; transition:border-color 0.2s;
  }}
  #inp:focus {{ border-color: #2563eb55; }}
  #inp::placeholder {{ color: #334155; }}

  /* ── Buttons ─────────────────────────────────────────── */
  .btn {{ padding:6px 11px; border-radius:7px; border:1px solid transparent; cursor:pointer; font-size:0.68rem; font-family:'Space Mono',monospace; transition:all 0.15s; white-space:nowrap; line-height:1; }}
  .bb {{ background:#1e3a5f; color:#7dd3fc; border-color:#2563eb44; }}
  .bb:hover {{ background:#1d4ed8; color:#fff; border-color:#3b82f6; }}
  .bg {{ background:#1c1917; color:#78716c; border-color:#44403c44; }}
  .bg:hover {{ background:#292524; color:#a8a29e; }}
  .bg:disabled {{ opacity:.35; cursor:not-allowed; }}
  .bgr {{ background:#14532d; color:#4ade80; border-color:#16a34a44; cursor:default; }}
  .bp {{ background:#1e1b4b; color:#a5b4fc; border-color:#6366f144; }}
  .bp:hover {{ background:#312e81; color:#c7d2fe; }}
  .bs {{ background:#1d4ed8; color:#fff; border-color:#3b82f6; padding:8px 15px; font-size:0.74rem; }}
  .bs:hover {{ background:#2563eb; }}
  .bs:disabled {{ background:#1e2435; color:#475569; border-color:#1e2435; cursor:not-allowed; }}

  /* ── Toast ───────────────────────────────────────────── */
  .tst {{
    position:fixed; bottom:14px; right:14px;
    padding:7px 13px; border-radius:8px;
    font-size:0.68rem; font-family:'Space Mono',monospace;
    z-index:9999; pointer-events:none;
    animation: fin .28s ease;
    transition: opacity .4s;
  }}
  @keyframes fin {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1}} }}
</style>
</head>
<body>
<div id="app">

  <!-- ══════════ LEFT PANEL ══════════ -->
  <div id="LP">
    <div class="ph">
      <div class="dot" style="background:#3b82f6;box-shadow:0 0 5px #3b82f690;"></div>
      Meeting View
      <span id="spill">● IDLE</span>
    </div>

    <div id="ctrl">
      <button class="btn bb" id="bsh" onclick="startCap()">📺 Share Tab</button>
      <button class="btn bg" id="bst" onclick="stopCap()" disabled>⏹ Stop</button>
      <button class="btn bb" id="bsc" onclick="takeShot()" disabled>📸 Screenshot</button>
      <button class="btn bp" id="bmic" onclick="toggleMic()">🎙 Listen</button>
    </div>

    <div id="vw">
      <video id="vid" autoplay muted playsinline></video>
      <canvas id="cv" style="display:none;"></canvas>
      <div id="vph">
        <div class="ico">📺</div>
        <div class="hint">Click <strong>Share Tab</strong> and choose your meeting tab from the browser picker.<br><br>Best on <strong>Chrome</strong>.</div>
      </div>
    </div>

    <div id="sstrip">
      <div class="slbl">📸 SCREENSHOT ATTACHED — SENDS WITH NEXT MESSAGE</div>
      <img id="simg" src="" alt="screenshot"/>
    </div>

    <div id="astrip">
      <div class="arow">
        <span style="font-size:0.6rem;color:#334155;font-family:'Space Mono',monospace;">TRANSCRIPT</span>
        <button class="btn bg" onclick="useTx()" style="padding:2px 8px;font-size:0.6rem;">↗ Ask AI</button>
        <button class="btn bg" onclick="clearTx()" style="padding:2px 8px;font-size:0.6rem;">✕ Clear</button>
      </div>
      <div id="tbox">Transcribed speech appears here…</div>
    </div>
  </div>

  <!-- ══════════ DRAG HANDLE ══════════ -->
  <div id="RZ" title="Drag to resize"></div>

  <!-- ══════════ RIGHT PANEL ══════════ -->
  <div id="RP">
    <div class="ph">
      <div class="dot" style="background:#a78bfa;box-shadow:0 0 5px #a78bfa90;"></div>
      AI Assistant · GPT-4o Vision
      <button class="btn bg" onclick="clearChat()" style="margin-left:auto;padding:2px 8px;font-size:0.6rem;">🗑 Clear</button>
    </div>

    <div id="msgs">
      <div class="empty" id="emp">
        <div class="ei">🧠</div>
        <p>Share your meeting tab, take a screenshot, then ask me anything about what's on screen.</p>
      </div>
    </div>

    <div id="qbar">
      <button class="btn bb" onclick="qa('sum')">🗒 Summarise Screen</button>
      <button class="btn bb" onclick="qa('act')">✅ Action Items</button>
      <button class="btn bb" onclick="qa('rep')">💡 Help Me Reply</button>
    </div>

    <div id="ibar">
      <textarea id="inp" rows="1"
        placeholder="Ask about your meeting… (Enter = send · Shift+Enter = newline)"
        onkeydown="onK(event)" oninput="grow(this)"></textarea>
      <button class="btn bs" id="bsnd" onclick="send()">Send ↑</button>
    </div>
  </div>

</div><!-- /app -->

<script>
// ━━━ Config ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const K  = "{api_key}";
const M  = "{AI_MODEL}";
const SY = "You are MeetingMind AI — a smart, concise assistant alongside a live video meeting. When given a screenshot, read and describe what you see accurately. Help with summaries, action items, questions, drafting replies, or any task. Be direct and practical.";

// ━━━ State ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
let MS=null, REC=null, LIS=false, TX='', SHOT=null, HIST=[];

// ━━━ Fix #3: Drag resizer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(()=>{{
  const rz=g('RZ'), lp=g('LP'), ap=g('app');
  let on=false, sx=0, sw=0;
  rz.onmousedown = e=>{{ on=true; sx=e.clientX; sw=lp.offsetWidth; rz.classList.add('on'); document.body.style.cssText='cursor:col-resize;user-select:none'; e.preventDefault(); }};
  document.addEventListener('mousemove', e=>{{
    if(!on) return;
    const nw=Math.max(260, Math.min(sw+e.clientX-sx, ap.offsetWidth-280));
    lp.style.width=nw+'px'; lp.style.maxWidth='none';
  }});
  document.addEventListener('mouseup', ()=>{{ if(!on)return; on=false; rz.classList.remove('on'); document.body.style.cssText=''; }});
}})();

// ━━━ Screen capture ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function startCap(){{
  try{{
    MS=await navigator.mediaDevices.getDisplayMedia({{video:{{frameRate:15}},audio:true}});
    const v=g('vid'); v.srcObject=MS; v.style.display='block';
    g('vph').style.display='none';
    sb('bsh',true,'✅ Sharing','btn bgr');
    sb('bst',false,'⏹ Stop','btn bg');
    sb('bsc',false,'📸 Screenshot','btn bb');
    ssp('● LIVE','#14532d','#4ade80');
    MS.getTracks().forEach(t=>t.addEventListener('ended',stopCap));
  }}catch(e){{
    ssp('✖ Denied','#450a0a','#f87171');
    setTimeout(()=>ssp('● IDLE','#1c1917','#78716c'),2200);
  }}
}}
function stopCap(){{
  if(MS){{MS.getTracks().forEach(t=>t.stop());MS=null;}}
  const v=g('vid'); v.srcObject=null; v.style.display='none';
  g('vph').style.display='flex';
  sb('bsh',false,'📺 Share Tab','btn bb');
  sb('bst',true,'⏹ Stop','btn bg');
  sb('bsc',true,'📸 Screenshot','btn bb');
  ssp('● IDLE','#1c1917','#78716c');
}}

// ━━━ Screenshot ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function takeShot(){{
  const v=g('vid'),cv=g('cv');
  cv.width=v.videoWidth||1280; cv.height=v.videoHeight||720;
  cv.getContext('2d').drawImage(v,0,0,cv.width,cv.height);
  const du=cv.toDataURL('image/jpeg',0.85);
  SHOT=du.split(',')[1];
  g('simg').src=du; g('sstrip').style.display='block';
  toast('📸 Screenshot attached — it will send with your next message','#164e63','#67e8f9');
}}

// ━━━ Speech ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function toggleMic(){{
  if(!('webkitSpeechRecognition'in window||'SpeechRecognition'in window)){{
    g('tbox').textContent='⚠ Requires Chrome.'; return;
  }}
  if(LIS){{REC.stop();return;}}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  REC=new SR(); REC.continuous=true; REC.interimResults=true; REC.lang='en-US';
  REC.onstart=()=>{{ LIS=true; g('bmic').textContent='⏹ Stop Listen'; g('bmic').className='btn bp'; ssp('🎙 LISTENING','#1e1b4b','#a5b4fc'); }};
  REC.onresult=e=>{{
    let ii='';
    for(let i=e.resultIndex;i<e.results.length;i++){{
      const t=e.results[i][0].transcript;
      if(e.results[i].isFinal) TX+=t+' '; else ii=t;
    }}
    g('tbox').textContent=TX+(ii?'…'+ii:'');
  }};
  REC.onerror=e=>{{ g('tbox').textContent='⚠ '+e.error; }};
  REC.onend=()=>{{ LIS=false; g('bmic').textContent='🎙 Listen'; g('bmic').className='btn bp'; ssp(MS?'● LIVE':'● IDLE',MS?'#14532d':'#1c1917',MS?'#4ade80':'#78716c'); }};
  REC.start();
}}
function useTx(){{
  const t=g('tbox').textContent.trim();
  if(!t||t.startsWith('Transcribed'))return;
  g('inp').value=t; grow(g('inp')); g('inp').focus();
}}
function clearTx(){{ TX=''; g('tbox').textContent='Transcribed speech appears here…'; }}

// ━━━ Chat ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function onK(e){{ if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();send();}} }}
function grow(el){{ el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,96)+'px'; }}

async function send(ov){{
  const i=g('inp'), txt=(ov||i.value).trim();
  if(!txt)return;
  i.value=''; grow(i); g('bsnd').disabled=true;
  g('emp')?.remove();

  const hs=!!SHOT, sb64=SHOT;
  SHOT=null; g('sstrip').style.display='none';

  addBub('u',txt,hs);

  const uc=[];
  if(sb64) uc.push({{type:'image_url',image_url:{{url:'data:image/jpeg;base64,'+sb64,detail:'high'}}}});
  uc.push({{type:'text',text:txt}});
  HIST.push({{role:'user',content:uc}});

  const tid='t'+Date.now();
  addTyp(tid);

  try{{
    // ── ✅ CURRENT: OpenAI GPT-4o ─────────────────────────────────
    const r=await fetch('https://api.openai.com/v1/chat/completions',{{
      method:'POST',
      headers:{{'Content-Type':'application/json','Authorization':'Bearer '+K}},
      body:JSON.stringify({{model:M,max_tokens:1500,messages:[{{role:'system',content:SY}},...HIST]}})
    }});
    const d=await r.json();
    g(tid)?.remove();
    if(d.error) throw new Error(d.error.message);
    const rep=d.choices[0].message.content;
    HIST.push({{role:'assistant',content:rep}});
    if(HIST.length>20) HIST=HIST.slice(HIST.length-20);
    addBub('a',rep);

    // ── 🔮 FUTURE: Anthropic Claude (swap the block above for this) ──
    // const r=await fetch('https://api.anthropic.com/v1/messages',{{
    //   method:'POST',
    //   headers:{{'Content-Type':'application/json','x-api-key':K,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'}},
    //   body:JSON.stringify({{model:'claude-opus-4-5',max_tokens:1500,system:SY,messages:HIST}})
    // }});
    // const d=await r.json(); g(tid)?.remove();
    // const rep=d.content[0].text;
    // HIST.push({{role:'assistant',content:rep}}); addBub('a',rep);
    // ──────────────────────────────────────────────────────────────────

  }}catch(e){{ g(tid)?.remove(); addBub('a','⚠️ Error: '+e.message); }}
  g('bsnd').disabled=false;
}}

function qa(t){{
  const p={{sum:'Summarise what you can see on my meeting screen.',act:'List the key action items or decisions from this meeting.',rep:"Help me draft a smart reply to what's being discussed."}};
  if(t==='sum'&&!SHOT){{toast('Take a 📸 screenshot first so I can see the screen','#1e3a5f','#7dd3fc');return;}}
  send(p[t]);
}}
function clearChat(){{ HIST=[]; g('msgs').innerHTML='<div class="empty" id="emp"><div class="ei">🧠</div><p>Chat cleared — ready for a fresh start!</p></div>'; }}

// ━━━ DOM helpers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function g(id){{return document.getElementById(id);}}

function addBub(role,text,hs){{
  const c=g('msgs'), d=document.createElement('div');
  d.className=role==='u'?'mu':'ma';
  const tm=new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});
  const bge=(role==='u'&&hs)?'<div class="sbadge">📸 Screenshot attached</div>':'';
  const safe=text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  d.innerHTML=bge+safe.replace(/\n/g,'<br>')+'<div class="mm">'+(role==='u'?'You':'🧠 GPT-4o')+'&nbsp;·&nbsp;'+tm+'</div>';
  c.appendChild(d); c.scrollTop=c.scrollHeight;
}}

function addTyp(id){{
  const c=g('msgs'), d=document.createElement('div');
  d.className='ma'; d.id=id;
  d.innerHTML='<div class="tw"><div class="td"></div><div class="td"></div><div class="td"></div></div>';
  c.appendChild(d); c.scrollTop=c.scrollHeight;
}}

function ssp(t,bg,cl){{const e=g('spill');e.textContent=t;e.style.background=bg;e.style.color=cl;}}
function sb(id,dis,txt,cls){{const e=g(id);e.disabled=dis;e.textContent=txt;e.className=cls;}}

function toast(msg,bg,cl){{
  const e=document.createElement('div');
  e.className='tst'; e.textContent=msg;
  e.style.background=bg; e.style.color=cl; e.style.border='1px solid '+cl+'44';
  document.body.appendChild(e);
  setTimeout(()=>e.style.opacity='0',2500);
  setTimeout(()=>e.remove(),2900);
}}
</script>
</body>
</html>"""

# One clean component — no extra iframes, no black boxes
st.components.v1.html(MAIN_APP, height=690, scrolling=False)

