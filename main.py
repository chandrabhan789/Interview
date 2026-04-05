import streamlit as st
import base64
import os
from datetime import datetime
from openai import OpenAI

AI_MODEL = "gpt-4o"

st.set_page_config(layout="wide")

# ── CSS FIX (IMPORTANT) ─────────────────────────────────────
st.markdown("""
<style>
.chat-wrapper {
    height: 500px;
    overflow: hidden;
    border-radius: 12px;
    border: 1px solid #2a2f3e;
    background: #0d0f14;
    display: flex;
    flex-direction: column;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.msg-user {
    align-self: flex-end;
    background: #1e3a5f;
    padding: 8px 12px;
    border-radius: 10px;
    max-width: 80%;
}

.msg-ai {
    align-self: flex-start;
    background: #1a1d27;
    padding: 8px 12px;
    border-radius: 10px;
    max-width: 85%;
}

.transcript-box {
    min-height: 60px !important;
    max-height: 80px !important;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "screenshot_b64" not in st.session_state:
    st.session_state.screenshot_b64 = None

if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")

# ── LAYOUT FIX (LEFT BIGGER) ─────────────────────────────
left, right = st.columns([1.3, 0.7])

# ── LEFT PANEL ───────────────────────────────────────────
with left:
    st.subheader("📺 Meeting Capture")

    component = st.components.v1.html("""
    <div>
      <video id="video" autoplay style="width:100%;height:320px;"></video>
      <button onclick="start()">Start</button>
      <button onclick="shot()">Screenshot</button>

      <div id="transcript" class="transcript-box"
        style="background:#111;color:#fff;padding:10px;margin-top:10px;">
      </div>
    </div>

    <script>
    let stream;

    async function start(){
        stream = await navigator.mediaDevices.getDisplayMedia({video:true,audio:true});
        document.getElementById("video").srcObject = stream;
    }

    function shot(){
        let video = document.getElementById("video");
        let canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video,0,0);
        let data = canvas.toDataURL("image/jpeg",0.6); // optimized size
        window.parent.postMessage({type:"screenshot",data:data},"*");
    }

    // Speech Recognition
    let rec = new webkitSpeechRecognition();
    rec.continuous = true;

    rec.onresult = function(e){
        let text="";
        for(let i=e.resultIndex;i<e.results.length;i++){
            text += e.results[i][0].transcript;
        }
        document.getElementById("transcript").innerText = text;
    }

    rec.start();
    </script>
    """, height=450)

# ── RIGHT PANEL ──────────────────────────────────────────
with right:
    st.subheader("🧠 AI Chat")

    # Chat container FIX
    chat_html = '<div class="chat-wrapper"><div class="chat-messages">'

    for m in st.session_state.messages:
        if m["role"] == "user":
            chat_html += f'<div class="msg-user">{m["text"]}</div>'
        else:
            chat_html += f'<div class="msg-ai">{m["text"]}</div>'

    chat_html += "</div></div>"

    st.markdown(chat_html, unsafe_allow_html=True)

    # INPUT
    user_input = st.chat_input("Ask something...")

    def get_ai(text):
        client = OpenAI(api_key=st.session_state.api_key)
        res = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role":"user","content":text}]
        )
        return res.choices[0].message.content

    if user_input:
        st.session_state.messages.append({"role":"user","text":user_input})

        with st.spinner("Thinking..."):
            reply = get_ai(user_input)

        st.session_state.messages.append({"role":"assistant","text":reply})
        st.rerun()
