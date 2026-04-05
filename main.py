import streamlit as st
import base64
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide")

# ── Session ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "screenshot" not in st.session_state:
    st.session_state.screenshot = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.title("🧠 MeetingMind AI")

st.session_state.api_key = st.text_input("OpenAI API Key", type="password")

left, right = st.columns([1.2, 1])

# ═══════════════════════════════════
# LEFT PANEL (LIVE + TRANSCRIPT)
# ═══════════════════════════════════
with left:
    component_value = st.components.v1.html("""
    <div style="color:white">

    <button onclick="startCapture()">📺 Share Tab</button>
    <button onclick="startSpeech()">🎙 Start Transcript</button>
    <button onclick="takeShot()">📸 Screenshot</button>

    <br><br>

    <video id="video" autoplay style="width:100%;border-radius:10px;"></video>

    <h4>🎙 Live Transcript</h4>
    <div id="transcript" 
        style="background:#111;
               padding:12px;
               border-radius:8px;
               height:80px;
               font-size:14px;
               line-height:1.6;
               overflow-y:auto;
               color:#e2e8f0;">
    </div>

    </div>

    <script>
    let stream = null;
    let fullText = "";

    function sendData(type, data){
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: {type:type, data:data}
        }, "*");
    }

    async function startCapture(){
        stream = await navigator.mediaDevices.getDisplayMedia({
            video:true,
            audio:true
        });
        document.getElementById("video").srcObject = stream;
    }

    function takeShot(){
        const video = document.getElementById("video");
        const canvas = document.createElement("canvas");

        canvas.width = 800;
        canvas.height = 450;

        canvas.getContext("2d").drawImage(video,0,0,800,450);

        const data = canvas.toDataURL("image/jpeg",0.6);

        sendData("screenshot", data);
    }

    function startSpeech(){
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

        if(!SR){
            alert("Use Chrome browser");
            return;
        }

        const rec = new SR();
        rec.continuous = true;
        rec.interimResults = true;

        rec.onresult = function(e){
            let interim = "";
            for(let i=e.resultIndex;i<e.results.length;i++){
                let txt = e.results[i][0].transcript;
                if(e.results[i].isFinal){
                    fullText += " " + txt;
                } else {
                    interim += txt;
                }
            }

            document.getElementById("transcript").innerText = fullText + " " + interim;

            sendData("transcript", fullText);
        }

        rec.start();
    }

    </script>
    """, height=520)

    # SAFE HANDLING
    if component_value and isinstance(component_value, dict):

        if component_value.get("type") == "screenshot":
            st.session_state.screenshot = component_value["data"].split(",")[1]
            st.success("📸 Screenshot captured")

        if component_value.get("type") == "transcript":
            st.session_state["auto_prompt"] = component_value["data"]

# ═══════════════════════════════════
# RIGHT PANEL (AI CHAT FIXED UI)
# ═══════════════════════════════════
with right:

    # 🔥 FIX: Scrollable chat container
    chat_html = """
    <div style="
        height:400px;
        overflow-y:auto;
        padding:10px;
        border:1px solid #ddd;
        border-radius:10px;
        background:#0e1117;
        color:white;
        display:flex;
        flex-direction:column;
        gap:10px;
    " id="chat-box">
    """

    for m in st.session_state.messages:
        if m["role"] == "user":
            chat_html += f"""
            <div style="align-self:flex-end;background:#1e3a5f;padding:8px 12px;border-radius:10px;">
            {m['text']}
            </div>
            """
        else:
            chat_html += f"""
            <div style="align-self:flex-start;background:#222;padding:8px 12px;border-radius:10px;">
            {m['text']}
            </div>
            """

    chat_html += "</div>"

    # Auto-scroll
    chat_html += """
    <script>
    var box = document.getElementById('chat-box');
    if(box){ box.scrollTop = box.scrollHeight; }
    </script>
    """

    st.markdown(chat_html, unsafe_allow_html=True)

    user_input = st.chat_input("Ask about meeting...")

    if "auto_prompt" in st.session_state:
        user_input = st.session_state.pop("auto_prompt")

    def ask_ai(api_key, history, text, img):
        client = OpenAI(api_key=api_key)

        content = []
        if img:
            content.append({
                "type":"image_url",
                "image_url":{"url":f"data:image/jpeg;base64,{img}"}
            })

        content.append({"type":"text","text":text})

        messages = [{"role":"system","content":"You are meeting assistant"}]

        for h in history:
            messages.append({
                "role":h["role"],
                "content":[{"type":"text","text":h["text"]}]
            })

        messages.append({"role":"user","content":content})

        res = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        return res.choices[0].message.content

    if user_input:
        if not st.session_state.api_key:
            st.error("Enter API key")
        else:
            st.session_state.messages.append({"role":"user","text":user_input})

            with st.spinner("🤖 Thinking..."):
                reply = ask_ai(
                    st.session_state.api_key,
                    st.session_state.messages[-5:],
                    user_input,
                    st.session_state.screenshot
                )

            st.session_state.messages.append({"role":"assistant","text":reply})
            st.session_state.screenshot = None

            st.rerun()
