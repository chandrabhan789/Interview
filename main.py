import streamlit as st
import urllib.parse
import os

# ── Provider config (swap these 2 lines when moving to Claude) ──────────────
AI_MODEL     = "gpt-4o"
ENV_KEY_NAME = "OPENAI_API_KEY"

st.set_page_config(
    page_title="MeetingMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Outer Streamlit CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
  html, body, [class*="css"] { background:#0d0f14!important; font-family:'DM Sans',sans-serif; color:#e2e8f0; }
  #MainMenu, footer, header                  { visibility:hidden!important; }
  [data-testid="manage-app-button"]          { display:none!important; }
  [data-testid="stToolbar"]                  { display:none!important; }
  .viewerBadge_container__r5tak             { display:none!important; }
  .stDeployButton                            { display:none!important; }
  section[data-testid="stSidebar"]           { display:none!important; }
  .block-container { padding:0.5rem 0.9rem 0!important; max-width:100%!important; }
  iframe { border:none!important; background:transparent!important; display:block!important; }
  .mm-hdr {
    display:flex; align-items:center; justify-content:space-between;
    padding:7px 14px; background:linear-gradient(135deg,#1a1d27,#12151e);
    border:1px solid #1e2435; border-radius:10px; margin-bottom:6px;
    box-shadow:0 4px 20px rgba(0,0,0,.5);
  }
  .mm-hdr h1 { font-family:'Space Mono',monospace; font-size:1.05rem; color:#7dd3fc; margin:0; }
  .mm-badge  { background:#1e3a5f; color:#7dd3fc; font-size:.62rem; padding:2px 9px; border-radius:20px; font-family:'Space Mono',monospace; border:1px solid #2563eb44; }
  .stExpander { background:#12151e!important; border:1px solid #1e2435!important; border-radius:8px!important; margin-bottom:6px!important; }
  .stTextInput>div>div>input { background:#1a1d27!important; border:1px solid #2a2f3e!important; color:#e2e8f0!important; border-radius:7px!important; }
  .stButton>button { background:#1e3a5f!important; color:#7dd3fc!important; border:1px solid #2563eb44!important; border-radius:7px!important; font-family:'Space Mono',monospace!important; font-size:.74rem!important; }
  .stButton>button:hover { background:#1d4ed8!important; color:#fff!important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get(ENV_KEY_NAME, "")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mm-hdr">
  <h1>🧠 MeetingMind AI</h1>
  <div style="display:flex;gap:10px;align-items:center;">
    <span style="font-size:.65rem;color:#475569;font-family:'Space Mono',monospace;">GPT-4o Vision</span>
    <span class="mm-badge">v3.1</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API Key expander ─────────────────────────────────────────────────────────
with st.expander("⚙️ OpenAI API Key", expanded=not st.session_state.api_key):
    c1, c2 = st.columns([5, 1])
    with c1:
        key_val = st.text_input("key", value=st.session_state.api_key,
                                type="password", placeholder="sk-...",
                                label_visibility="collapsed")
    with c2:
        if st.button("Save"):
            st.session_state.api_key = key_val
            st.rerun()
    st.caption("🔑 Session only — sent directly to OpenAI, never stored elsewhere.")

api_key = st.session_state.api_key
if not api_key:
    st.info("👆 Enter your OpenAI API key above to start.", icon="🔑")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CAPTURE POPUP HTML
#
#  Why a popup?  Streamlit renders st.components.v1.html() via srcdoc="..."
#  Chrome gives srcdoc iframes an OPAQUE (null) origin — this blocks
#  getDisplayMedia() no matter what we do inside the iframe.
#
#  window.open() is allowed by Streamlit's sandbox:
#    sandbox="... allow-popups allow-popups-to-escape-sandbox ..."
#  The "escape-sandbox" flag means the popup is a REAL top-level window —
#  no sandbox at all — so getDisplayMedia() works perfectly there.
#
#  The popup sends screenshots back via postMessage(). Our main app
#  listens and stores them for the next chat message.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POPUP_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>MeetingMind — Capture</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#06080f;color:#e2e8f0;font-family:'Segoe UI',sans-serif;display:flex;flex-direction:column;height:100vh;overflow:hidden}
  #bar{display:flex;gap:8px;align-items:center;padding:10px 14px;background:#0f1117;border-bottom:1px solid #1e2435;flex-shrink:0}
  #bar h2{font-size:.88rem;color:#7dd3fc;font-family:monospace;margin-right:auto}
  #status{font-size:.7rem;color:#475569;font-family:monospace}
  #vwrap{flex:1;background:#000;position:relative;overflow:hidden;min-height:0}
  #vid{width:100%;height:100%;object-fit:contain}
  #ph{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:#1e3a5f}
  #ph .pi{font-size:3rem;opacity:.3}
  #ph p{font-size:.78rem;font-family:monospace;text-align:center;max-width:220px;line-height:1.7}
  #shot-prev{display:none;padding:6px 14px;background:#0a0c12;border-top:1px solid #1e2435;flex-shrink:0}
  #shot-prev img{width:100%;max-height:80px;object-fit:cover;border-radius:5px;border:1px solid #164e63}
  .p-lbl{font-size:.6rem;color:#22d3ee;font-family:monospace;margin-bottom:3px;letter-spacing:.8px}
  .ok{color:#4ade80}
  btn,button{padding:7px 13px;border-radius:7px;border:1px solid transparent;cursor:pointer;font-size:.72rem;font-family:monospace;transition:all .15s;white-space:nowrap}
  .b1{background:#1e3a5f;color:#7dd3fc;border-color:#2563eb44}
  .b1:hover{background:#1d4ed8;color:#fff}
  .b1:disabled{background:#141720;color:#334155;cursor:not-allowed}
  .b2{background:#14532d;color:#4ade80;border-color:#16a34a44;cursor:default}
  .b3{background:#1e1b4b;color:#a5b4fc;border-color:#6366f144}
  .b3:hover{background:#312e81;color:#c7d2fe}
  .b3:disabled{background:#141720;color:#334155;cursor:not-allowed}
  .b4{background:#7c3aed;color:#fff;border-color:#8b5cf6;font-weight:700;padding:8px 18px;font-size:.78rem}
  .b4:hover{background:#6d28d9}
  .b4:disabled{background:#1e2435;color:#475569;cursor:not-allowed}
</style>
</head>
<body>
<div id="bar">
  <h2>📺 MeetingMind — Tab Capture</h2>
  <span id="status">Ready</span>
  <button class="b1" id="bShare">📺 Share Tab</button>
  <button class="b1" id="bStop" disabled>⏹ Stop</button>
  <button class="b4" id="bShot" disabled>📸 Send Screenshot to App</button>
</div>
<div id="vwrap">
  <video id="vid" autoplay muted playsinline></video>
  <canvas id="cv" style="display:none"></canvas>
  <div id="ph">
    <div class="pi">📺</div>
    <p>Click <strong style="color:#3b82f6">Share Tab</strong> then select your meeting tab from the browser picker.</p>
  </div>
</div>
<div id="shot-prev">
  <div class="p-lbl">LAST SCREENSHOT SENT</div>
  <img id="shot-img" src="" alt=""/>
</div>
<script>
var ms = null;

document.getElementById('bShare').addEventListener('click', async function() {
  try {
    document.getElementById('status').textContent = 'Requesting…';
    ms = await navigator.mediaDevices.getDisplayMedia({video:{frameRate:15}, audio:true});
    var vid = document.getElementById('vid');
    vid.srcObject = ms;
    vid.style.display = 'block';
    document.getElementById('ph').style.display = 'none';
    document.getElementById('bShare').disabled = true;
    document.getElementById('bShare').className = 'b2';
    document.getElementById('bShare').textContent = '✅ Sharing';
    document.getElementById('bStop').disabled = false;
    document.getElementById('bShot').disabled = false;
    document.getElementById('status').textContent = '● LIVE';
    document.getElementById('status').style.color = '#4ade80';
    ms.getTracks().forEach(function(t){ t.addEventListener('ended', stopShare); });
  } catch(e) {
    document.getElementById('status').textContent = '✖ ' + e.message;
    document.getElementById('status').style.color = '#f87171';
  }
});

document.getElementById('bStop').addEventListener('click', stopShare);

function stopShare() {
  if (ms) { ms.getTracks().forEach(function(t){t.stop();}); ms = null; }
  var vid = document.getElementById('vid');
  vid.srcObject = null;
  document.getElementById('ph').style.display = 'flex';
  document.getElementById('bShare').disabled = false;
  document.getElementById('bShare').className = 'b1';
  document.getElementById('bShare').textContent = '📺 Share Tab';
  document.getElementById('bStop').disabled = true;
  document.getElementById('bShot').disabled = true;
  document.getElementById('status').textContent = 'Stopped';
  document.getElementById('status').style.color = '';
}

document.getElementById('bShot').addEventListener('click', function() {
  var vid = document.getElementById('vid');
  if (!vid.srcObject || vid.videoWidth === 0) {
    document.getElementById('status').textContent = 'No video yet';
    return;
  }
  var cv = document.getElementById('cv');
  cv.width = vid.videoWidth; cv.height = vid.videoHeight;
  cv.getContext('2d').drawImage(vid, 0, 0, cv.width, cv.height);
  var dataUrl = cv.toDataURL('image/jpeg', 0.85);
  var b64 = dataUrl.split(',')[1];

  // Send to parent app window
  if (window.opener) {
    window.opener.postMessage({type:'mm-screenshot', data:b64}, '*');
    document.getElementById('status').textContent = '✅ Sent to app!';
    document.getElementById('status').style.color = '#4ade80';
    document.getElementById('shot-img').src = dataUrl;
    document.getElementById('shot-prev').style.display = 'block';
  } else {
    document.getElementById('status').textContent = '⚠ No parent window found';
  }
});
</script>
</body>
</html>"""

# URL-encode the popup HTML so it can be safely embedded in a JS string literal
# (no escaping issues with backticks, quotes, backslashes, dollar signs)
POPUP_HTML_ENCODED = urllib.parse.quote(POPUP_HTML)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN APP HTML
#
#  Send button / AI chat:
#    Direct fetch from JS → api.openai.com works because:
#    • OpenAI sets Access-Control-Allow-Origin: * (CORS open)
#    • null-origin srcdoc iframes are allowed by CORS * responses
#    • All errors are shown in the chat UI, never hidden
#
#  All buttons use addEventListener (NOT onclick=) bound in DOMContentLoaded.
#  No IIFEs that could crash before the DOM is set up.
#  Every catch() block writes a visible red error into the chat.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAIN_APP = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
  html, body {{ height:100%; overflow:hidden; background:transparent; font-family:'DM Sans','Segoe UI',sans-serif; color:#e2e8f0; }}

  /* ── Root layout ──────────────────────────────── */
  #app {{
    display:flex; width:100%; height:100%;
    background:#0d0f14; border:1px solid #1e2435;
    border-radius:10px; overflow:hidden;
    box-shadow:0 6px 32px rgba(0,0,0,.6);
  }}

  /* ── Left panel ───────────────────────────────── */
  #LP {{
    width:52%; min-width:230px; max-width:74%;
    display:flex; flex-direction:column;
    background:#0c0e15; border-right:1px solid #1e2435;
    overflow:hidden; flex-shrink:0;
  }}

  /* ── Drag handle ──────────────────────────────── */
  #RZ {{
    width:6px; flex-shrink:0;
    background:#0d0f14; cursor:col-resize;
    position:relative; z-index:20; transition:background .2s;
  }}
  #RZ:hover, #RZ.on {{ background:#1d4ed833; }}
  #RZ::after {{
    content:''; position:absolute; top:50%; left:50%;
    transform:translate(-50%,-50%);
    width:2px; height:36px; background:#1e2435; border-radius:2px; transition:background .2s;
  }}
  #RZ:hover::after, #RZ.on::after {{ background:#3b82f6; }}

  /* ── Right panel ──────────────────────────────── */
  #RP {{
    flex:1; min-width:230px;
    display:flex; flex-direction:column;
    background:#0c0e15; overflow:hidden;
  }}

  /* ── Panel header ─────────────────────────────── */
  .ph {{
    display:flex; align-items:center; gap:7px;
    padding:9px 13px; background:#101318;
    border-bottom:1px solid #1a1f2e; flex-shrink:0;
    font-size:.64rem; font-weight:700; letter-spacing:1.2px;
    text-transform:uppercase; color:#3d4f6e;
    font-family:'Space Mono',monospace;
  }}
  .dot {{ width:7px; height:7px; border-radius:50%; flex-shrink:0; animation:blink 2.5s ease-in-out infinite; }}
  @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:.15}} }}

  /* ── Status chip ──────────────────────────────── */
  #chip {{
    margin-left:auto; font-size:.59rem; padding:2px 9px;
    border-radius:10px; font-family:'Space Mono',monospace;
    transition:all .3s; background:#161a24; color:#3d4f6e; border:1px solid #1e2435;
  }}

  /* ── Controls ─────────────────────────────────── */
  #ctrl {{
    display:flex; gap:5px; flex-wrap:wrap; align-items:center;
    padding:8px 10px; background:#09090f; border-bottom:1px solid #1a1f2e; flex-shrink:0;
  }}

  /* ── Screenshot preview (left panel) ─────────── */
  #shot-area {{
    flex-shrink:0; background:#09090f;
    border-bottom:1px solid #1a1f2e;
    display:none;
  }}
  #shot-area .sa-lbl {{
    font-size:.58rem; color:#22d3ee; font-family:'Space Mono',monospace;
    padding:5px 10px 3px; letter-spacing:.8px;
  }}
  #shot-area img {{ width:100%; max-height:90px; object-fit:cover; display:block; }}

  /* ── Transcript (3-line panel) ────────────────── */
  #txpanel {{
    flex-shrink:0; background:#09090f; border-bottom:1px solid #1a1f2e;
  }}
  .tx-hdr {{
    display:flex; align-items:center; gap:6px;
    padding:5px 10px; background:#101318; border-bottom:1px solid #1a1f2e;
  }}
  .tx-lbl {{ font-size:.58rem; color:#2d3d55; font-family:'Space Mono',monospace; letter-spacing:1px; }}
  .tx-btns {{ display:flex; gap:4px; margin-left:auto; }}
  #tbox {{
    padding:7px 10px;
    font-size:.75rem; color:#475569; font-style:italic; line-height:1.6;
    min-height:72px;   /* ← exactly 3 lines */
    max-height:92px; overflow-y:auto;
    scrollbar-width:thin; scrollbar-color:#1a1f2e transparent;
    word-break:break-word;
  }}
  #tbox.live {{ color:#94a3b8; font-style:normal; }}

  /* ── Spacer (left bottom filler) ─────────────── */
  #lspacer {{ flex:1; background:#06080f; min-height:0; }}

  /* ── RIGHT: chat messages ─────────────────────── */
  /* flex:1 + min-height:0 → scrolls internally, NEVER overflows */
  #msgs {{
    flex:1; min-height:0; overflow-y:auto; padding:12px;
    display:flex; flex-direction:column; gap:9px;
    scrollbar-width:thin; scrollbar-color:#1a1f2e transparent;
  }}
  .mu {{
    align-self:flex-end; background:#1a3254; border:1px solid #2563eb2a;
    color:#e2e8f0; padding:9px 13px;
    border-radius:14px 14px 3px 14px;
    max-width:84%; font-size:.79rem; line-height:1.52; word-break:break-word;
  }}
  .ma {{
    align-self:flex-start; background:#131620; border:1px solid #222840;
    color:#c4cedf; padding:9px 13px;
    border-radius:14px 14px 14px 3px;
    max-width:88%; font-size:.79rem; line-height:1.62; word-break:break-word;
  }}
  .merr {{
    align-self:flex-start; background:#2d0a0a; border:1px solid #dc262644;
    color:#f87171; padding:8px 12px; border-radius:10px;
    max-width:88%; font-size:.76rem; line-height:1.5;
    font-family:'Space Mono',monospace;
  }}
  .mm {{ font-size:.59rem; color:#2d3d55; margin-top:5px; }}
  .sbadge {{
    display:inline-block; background:#0e2e3b; color:#67e8f9;
    font-size:.57rem; padding:1px 7px; border-radius:4px;
    margin-bottom:5px; font-family:'Space Mono',monospace; letter-spacing:.5px;
  }}
  .tw {{ display:flex; gap:5px; align-items:center; }}
  .td {{ width:6px; height:6px; border-radius:50%; background:#2d3d55; animation:tda 1.4s ease-in-out infinite; }}
  .td:nth-child(2){{animation-delay:.18s}} .td:nth-child(3){{animation-delay:.36s}}
  @keyframes tda {{ 0%,100%{{opacity:.15;transform:translateY(0)}} 50%{{opacity:1;transform:translateY(-4px)}} }}
  .emp {{
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; height:100%; gap:10px;
  }}
  .ei {{ font-size:2rem; opacity:.08; }}
  .ep {{ font-size:.72rem; color:#1a2535; text-align:center; max-width:180px; line-height:1.75; }}

  /* ── Quick actions ────────────────────────────── */
  #qbar {{
    display:flex; gap:5px; flex-wrap:wrap;
    padding:6px 10px; border-top:1px solid #1a1f2e;
    background:#09090f; flex-shrink:0;
  }}

  /* ── Input bar ────────────────────────────────── */
  #ibar {{
    display:flex; gap:7px; align-items:flex-end;
    padding:9px 10px; border-top:1px solid #1a1f2e;
    background:#09090f; flex-shrink:0;
  }}
  #inp {{
    flex:1; background:#101318; border:1px solid #1e2a3a;
    color:#e2e8f0; border-radius:8px; padding:9px 12px;
    font-size:.81rem; font-family:'DM Sans','Segoe UI',sans-serif;
    resize:none; min-height:40px; max-height:100px; outline:none;
    line-height:1.5; transition:border-color .2s;
  }}
  #inp:focus {{ border-color:#2563eb55; }}
  #inp::placeholder {{ color:#1e2a3a; }}

  /* ── Buttons ──────────────────────────────────── */
  .btn {{
    padding:7px 11px; border-radius:7px; border:1px solid transparent;
    cursor:pointer; font-size:.65rem; font-family:'Space Mono',monospace;
    transition:all .15s; white-space:nowrap; line-height:1; outline:none;
  }}
  .bb {{ background:#1a3254; color:#7dd3fc; border-color:#2563eb33; }}
  .bb:hover {{ background:#1d4ed8; color:#fff; border-color:#3b82f6; }}
  .bg {{ background:#0f1117; color:#3d4f6e; border-color:#1a1f2e; }}
  .bg:hover {{ background:#141720; color:#64748b; }}
  .bg:disabled {{ opacity:.3; cursor:not-allowed; }}
  .bgr {{ background:#0d2a1a; color:#4ade80; border-color:#16a34a33; cursor:default; }}
  .bp {{ background:#1a1740; color:#a5b4fc; border-color:#6366f133; }}
  .bp:hover {{ background:#2d2a6e; color:#c7d2fe; }}
  .bred {{ background:#2d0a0a; color:#f87171; border-color:#dc262633; }}

  /* Send button — 2× size */
  #bsnd {{
    background:#1d4ed8; color:#fff; border:1px solid #3b82f6;
    border-radius:9px; padding:0 28px; height:52px;
    font-size:.84rem; font-family:'Space Mono',monospace; font-weight:700;
    cursor:pointer; flex-shrink:0; transition:all .15s; outline:none; letter-spacing:.4px;
  }}
  #bsnd:hover {{ background:#2563eb; box-shadow:0 0 14px #3b82f633; }}
  #bsnd:disabled {{ background:#101318; color:#2d3d55; border-color:#1a1f2e; cursor:not-allowed; box-shadow:none; }}

  /* ── Toast ────────────────────────────────────── */
  .tst {{
    position:fixed; bottom:12px; right:12px;
    padding:8px 13px; border-radius:8px; font-size:.66rem;
    font-family:'Space Mono',monospace; z-index:9999;
    pointer-events:none; animation:tfade .25s ease; transition:opacity .4s;
    max-width:270px; line-height:1.4;
  }}
  @keyframes tfade {{ from{{opacity:0;transform:translateY(5px)}} to{{opacity:1;transform:none}} }}
</style>
</head>
<body>
<div id="app">

  <!-- ══════════ LEFT PANEL ══════════ -->
  <div id="LP">
    <div class="ph">
      <div class="dot" style="background:#3b82f6;box-shadow:0 0 5px #3b82f680;"></div>
      Meeting View
      <span id="chip">⬤ IDLE</span>
    </div>

    <div id="ctrl">
      <button class="btn bb" id="bOpen">📺 Open Capture Window</button>
      <button class="btn bg" id="bMic">🎙 Listen</button>
      <button class="btn bg" id="bTxUse" style="margin-left:auto;">↗ Ask AI</button>
    </div>

    <!-- Screenshot preview from popup -->
    <div id="shot-area">
      <div class="sa-lbl">📸 SCREENSHOT — WILL ATTACH TO NEXT MESSAGE</div>
      <img id="shot-img" src="" alt="screenshot"/>
    </div>

    <!-- Transcript panel — 3-line min height -->
    <div id="txpanel">
      <div class="tx-hdr">
        <span class="tx-lbl">🎙 Live Transcript</span>
        <div class="tx-btns">
          <button class="btn bg" id="bTxClr" style="padding:2px 8px;font-size:.58rem;">✕ Clear</button>
        </div>
      </div>
      <div id="tbox">Transcribed speech will appear here…</div>
    </div>

    <!-- Fills remaining left height -->
    <div id="lspacer"></div>
  </div>

  <!-- ══════════ DRAG HANDLE ══════════ -->
  <div id="RZ" title="↔ Drag to resize"></div>

  <!-- ══════════ RIGHT PANEL ══════════ -->
  <div id="RP">
    <div class="ph">
      <div class="dot" style="background:#a78bfa;box-shadow:0 0 5px #a78bfa80;"></div>
      AI Assistant · GPT-4o Vision
      <button class="btn bg" id="bClr" style="margin-left:auto;padding:3px 8px;font-size:.58rem;">🗑 Clear</button>
    </div>

    <div id="msgs">
      <div class="emp" id="emp">
        <div class="ei">🧠</div>
        <p class="ep">Open the Capture Window, share your meeting tab, take a screenshot, then ask anything.</p>
      </div>
    </div>

    <div id="qbar">
      <button class="btn bb" id="q-sum">🗒 Summarise</button>
      <button class="btn bb" id="q-act">✅ Action Items</button>
      <button class="btn bb" id="q-rep">💡 Draft Reply</button>
      <button class="btn bb" id="q-key">🔑 Key Points</button>
    </div>

    <div id="ibar">
      <textarea id="inp" rows="1" placeholder="Type your question… (Enter = send · Shift+Enter = new line)"></textarea>
      <button id="bsnd">Send ↑</button>
    </div>
  </div>

</div><!-- /app -->

<script>
// ═══════════════════════════════════════════════════════════
//  CONFIG  (injected from Python)
// ═══════════════════════════════════════════════════════════
var APIKEY  = "{api_key}";
var MODEL   = "{AI_MODEL}";
var SYSPMT  = "You are MeetingMind AI, a sharp and concise assistant sitting alongside a live video meeting. When shown a screenshot, read it carefully. Help with summaries, action items, key decisions, drafting replies, answering questions about what is shown. Be direct and practical.";
var POPUP_ENCODED = "{POPUP_HTML_ENCODED}";
var POPUP_HTML  = decodeURIComponent(POPUP_ENCODED);

// ═══════════════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════════════
var captureWin  = null;
var recognition = null;
var listening   = false;
var txBuffer    = "";
var pendingShot = null;   // base64 jpeg from popup
var chatHistory = [];     // {{role, content}}

// ═══════════════════════════════════════════════════════════
//  INITIALISE — bind all events in DOMContentLoaded
//  (This avoids any race between DOM parse and script execution)
// ═══════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", function() {{

  // ── Confirm JS is alive ──────────────────────────────────
  setChip("✅ READY", "#0d2a1a", "#4ade80");
  setTimeout(function(){{ setChip("⬤ IDLE", "#161a24", "#3d4f6e"); }}, 1500);

  // ── Bind buttons ────────────────────────────────────────
  document.getElementById("bOpen").addEventListener("click",  openCapture);
  document.getElementById("bMic").addEventListener("click",   toggleMic);
  document.getElementById("bTxUse").addEventListener("click", useTranscript);
  document.getElementById("bTxClr").addEventListener("click", clearTranscript);
  document.getElementById("bsnd").addEventListener("click",   sendMsg);
  document.getElementById("bClr").addEventListener("click",   clearChat);
  document.getElementById("q-sum").addEventListener("click", function(){{ qa("sum"); }});
  document.getElementById("q-act").addEventListener("click", function(){{ qa("act"); }});
  document.getElementById("q-rep").addEventListener("click", function(){{ qa("rep"); }});
  document.getElementById("q-key").addEventListener("click", function(){{ qa("key"); }});

  // ── Enter key in textarea ────────────────────────────────
  document.getElementById("inp").addEventListener("keydown", function(e) {{
    if (e.key === "Enter" && !e.shiftKey) {{ e.preventDefault(); sendMsg(); }}
  }});

  // ── Auto-grow textarea ───────────────────────────────────
  document.getElementById("inp").addEventListener("input", function() {{ growInp(); }});

  // ── Drag-to-resize ───────────────────────────────────────
  initResize();

  // ── Listen for screenshots from popup ───────────────────
  window.addEventListener("message", function(e) {{
    if (!e.data || e.data.type !== "mm-screenshot") return;
    pendingShot = e.data.data;
    document.getElementById("shot-img").src = "data:image/jpeg;base64," + pendingShot;
    document.getElementById("shot-area").style.display = "block";
    toast("📸 Screenshot received — sends with next message", "#0e2e3b", "#67e8f9");
  }});

}});

// ═══════════════════════════════════════════════════════════
//  CAPTURE WINDOW
//  Opens a real top-level popup — getDisplayMedia() works there
//  Sandbox allows popups (allow-popups-to-escape-sandbox)
// ═══════════════════════════════════════════════════════════
function openCapture() {{
  if (captureWin && !captureWin.closed) {{
    captureWin.focus(); return;
  }}
  captureWin = window.open(
    "", "mm-capture",
    "width=1000,height=660,resizable=yes,scrollbars=no,toolbar=no,menubar=no"
  );
  if (!captureWin) {{
    toast("⚠ Popup blocked — please allow popups for this site", "#2d1a00", "#fb923c");
    return;
  }}
  captureWin.document.open();
  captureWin.document.write(POPUP_HTML);
  captureWin.document.close();
  setChip("📺 CAPTURE OPEN", "#0c1a2e", "#7dd3fc");
  toast("📺 Capture window opened — Share Tab there, then 📸 to send here", "#0c1a2e", "#7dd3fc");
}}

// ═══════════════════════════════════════════════════════════
//  SPEECH RECOGNITION  (Web Speech API — Chrome)
// ═══════════════════════════════════════════════════════════
function toggleMic() {{
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{
    addError("Speech recognition requires Chrome. Please use Chrome browser.");
    return;
  }}
  if (listening) {{ recognition.stop(); return; }}

  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = function() {{
    listening = true;
    document.getElementById("bMic").textContent = "⏹ Stop";
    document.getElementById("bMic").className = "btn bp";
    setChip("🎙 LISTENING", "#1e1b4b", "#a5b4fc");
  }};

  recognition.onresult = function(e) {{
    var interim = "";
    for (var i = e.resultIndex; i < e.results.length; i++) {{
      var t = e.results[i][0].transcript;
      if (e.results[i].isFinal) {{ txBuffer += t + " "; }}
      else {{ interim = t; }}
    }}
    var el = document.getElementById("tbox");
    el.textContent = txBuffer + (interim ? "…" + interim : "");
    el.classList.add("live");
    el.scrollTop = el.scrollHeight;
  }};

  recognition.onerror = function(e) {{
    document.getElementById("tbox").textContent = "⚠ Speech error: " + e.error;
    document.getElementById("tbox").classList.remove("live");
  }};

  recognition.onend = function() {{
    listening = false;
    document.getElementById("bMic").textContent = "🎙 Listen";
    document.getElementById("bMic").className = "btn bg";
    setChip("⬤ IDLE", "#161a24", "#3d4f6e");
  }};

  recognition.start();
}}

function useTranscript() {{
  var t = txBuffer.trim();
  if (!t) t = document.getElementById("tbox").textContent.trim();
  if (!t || t.indexOf("Transcribed") === 0) return;
  document.getElementById("inp").value = t;
  growInp();
  document.getElementById("inp").focus();
}}

function clearTranscript() {{
  txBuffer = "";
  document.getElementById("tbox").textContent = "Transcribed speech will appear here…";
  document.getElementById("tbox").classList.remove("live");
}}

// ═══════════════════════════════════════════════════════════
//  SEND MESSAGE  →  OpenAI
//
//  Why fetch works here:
//    OpenAI sets:  Access-Control-Allow-Origin: *
//    This allows requests from ANY origin, including null-origin
//    srcdoc iframes like Streamlit components.
//    All errors are shown in the chat — nothing is hidden.
// ═══════════════════════════════════════════════════════════
function sendMsg(overrideText) {{
  var inp  = document.getElementById("inp");
  var text = typeof overrideText === "string" ? overrideText.trim() : inp.value.trim();
  if (!text) return;

  inp.value = "";
  growInp();

  var bsnd = document.getElementById("bsnd");
  bsnd.disabled = true;

  // Remove empty state
  var emp = document.getElementById("emp");
  if (emp) emp.remove();

  // Screenshot
  var hasShot = !!pendingShot;
  var shot64  = pendingShot;
  pendingShot = null;
  document.getElementById("shot-area").style.display = "none";

  // User bubble
  addBubble("u", text, hasShot);

  // Build content array for OpenAI
  var userContent = [];
  if (shot64) {{
    userContent.push({{
      type: "image_url",
      image_url: {{ url: "data:image/jpeg;base64," + shot64, detail: "high" }}
    }});
  }}
  userContent.push({{ type: "text", text: text }});
  chatHistory.push({{ role: "user", content: userContent }});

  // Typing indicator
  var tid = "ty" + Date.now();
  addTyping(tid);

  // ── Fetch → OpenAI ──────────────────────────────────────
  // Using var for compatibility — async/await is fine in modern browsers
  fetch("https://api.openai.com/v1/chat/completions", {{
    method:  "POST",
    headers: {{
      "Content-Type":  "application/json",
      "Authorization": "Bearer " + APIKEY
    }},
    body: JSON.stringify({{
      model:      MODEL,
      max_tokens: 1500,
      messages:   [{{ role: "system", content: SYSPMT }}].concat(chatHistory)
    }})
  }})
  .then(function(res) {{ return res.json(); }})
  .then(function(data) {{
    var el = document.getElementById(tid);
    if (el) el.remove();

    if (data.error) {{
      addError("OpenAI error: " + data.error.message +
               (data.error.code ? " (code: " + data.error.code + ")" : ""));
      return;
    }}
    var reply = data.choices[0].message.content;
    chatHistory.push({{ role: "assistant", content: reply }});
    // Keep last 20 turns to avoid token overflow
    if (chatHistory.length > 20) {{
      chatHistory = chatHistory.slice(chatHistory.length - 20);
    }}
    addBubble("a", reply);
  }})
  .catch(function(err) {{
    var el = document.getElementById(tid);
    if (el) el.remove();
    addError("Network error: " + err.message +
             ". Check your internet connection and API key.");
  }})
  .finally(function() {{
    bsnd.disabled = false;
  }});

  // ── 🔮 FUTURE Claude swap: replace the fetch block above ──
  // fetch("https://api.anthropic.com/v1/messages", {{
  //   method: "POST",
  //   headers: {{
  //     "Content-Type":      "application/json",
  //     "x-api-key":         APIKEY,
  //     "anthropic-version": "2023-06-01",
  //     "anthropic-dangerous-direct-browser-access": "true"
  //   }},
  //   body: JSON.stringify({{
  //     model: "claude-opus-4-5", max_tokens: 1500,
  //     system: SYSPMT, messages: chatHistory
  //   }})
  // }})
  // .then(r => r.json())
  // .then(d => {{ ... d.content[0].text ... }})
  // ──────────────────────────────────────────────────────────
}}

// ═══════════════════════════════════════════════════════════
//  QUICK ACTIONS
// ═══════════════════════════════════════════════════════════
function qa(type) {{
  var prompts = {{
    sum: "Please summarise everything visible on my meeting screen.",
    act: "List all action items and decisions from this meeting.",
    rep: "Help me draft a smart response to what is being discussed.",
    key: "What are the key points and important figures from this meeting?"
  }};
  if ((type === "sum" || type === "key") && !pendingShot) {{
    toast("📸 Open the Capture Window and send a screenshot first", "#1a1a2e", "#818cf8");
    return;
  }}
  sendMsg(prompts[type]);
}}

function clearChat() {{
  chatHistory = [];
  document.getElementById("msgs").innerHTML =
    '<div class="emp" id="emp"><div class="ei">🧠</div><p class="ep">Chat cleared — ready for a fresh start!</p></div>';
}}

// ═══════════════════════════════════════════════════════════
//  RESIZE
// ═══════════════════════════════════════════════════════════
function initResize() {{
  var rz = document.getElementById("RZ");
  var lp = document.getElementById("LP");
  var ap = document.getElementById("app");
  var dragging = false, startX = 0, startW = 0;

  rz.addEventListener("mousedown", function(e) {{
    dragging = true; startX = e.clientX; startW = lp.offsetWidth;
    rz.classList.add("on");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    e.preventDefault();
  }});
  document.addEventListener("mousemove", function(e) {{
    if (!dragging) return;
    var newW = Math.max(230, Math.min(startW + e.clientX - startX, ap.offsetWidth - 240));
    lp.style.width = newW + "px";
    lp.style.maxWidth = "none";
  }});
  document.addEventListener("mouseup", function() {{
    if (!dragging) return;
    dragging = false; rz.classList.remove("on");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }});
}}

// ═══════════════════════════════════════════════════════════
//  DOM HELPERS
// ═══════════════════════════════════════════════════════════
function addBubble(role, text, hasShot) {{
  var msgs = document.getElementById("msgs");
  var div  = document.createElement("div");
  div.className = (role === "u") ? "mu" : "ma";
  var now = new Date().toLocaleTimeString([], {{hour:"2-digit", minute:"2-digit"}});
  var badge = (role === "u" && hasShot)
    ? '<div class="sbadge">📸 Screenshot attached</div>' : "";
  var safe = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
  div.innerHTML = badge + safe +
    '<div class="mm">' + (role === "u" ? "You" : "🧠 GPT-4o") +
    " &middot; " + now + "</div>";
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}}

function addTyping(id) {{
  var msgs = document.getElementById("msgs");
  var div  = document.createElement("div");
  div.className = "ma"; div.id = id;
  div.innerHTML = '<div class="tw"><div class="td"></div><div class="td"></div><div class="td"></div></div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}}

function addError(msg) {{
  var msgs = document.getElementById("msgs");
  var div  = document.createElement("div");
  div.className = "merr";
  div.textContent = "⚠ " + msg;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  document.getElementById("bsnd").disabled = false;
}}

function setChip(text, bg, color) {{
  var el = document.getElementById("chip");
  el.textContent = text; el.style.background = bg; el.style.color = color;
}}

function growInp() {{
  var el = document.getElementById("inp");
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 100) + "px";
}}

function toast(msg, bg, color) {{
  var el = document.createElement("div");
  el.className = "tst"; el.textContent = msg;
  el.style.background = bg; el.style.color = color;
  el.style.border = "1px solid " + color + "44";
  document.body.appendChild(el);
  setTimeout(function(){{ el.style.opacity = "0"; }}, 2700);
  setTimeout(function(){{ el.remove(); }}, 3200);
}}
</script>
</body>
</html>"""

st.components.v1.html(MAIN_APP, height=720, scrolling=False)
