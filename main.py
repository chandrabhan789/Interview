import streamlit as st
import base64
from datetime import datetime
from openai import OpenAI

st.set_page_config(page_title="MeetingMind AI", layout="wide")

# ── Session State ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "screenshot_b64" not in st.session_state:
    st.session_state.screenshot_b64 = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ── Header ──
st.title("🧠 MeetingMind AI (Fixed Version)")

# ── API Key ──
st.session_state.api_key = st.text_input("OpenAI API Key", type="password")

# ── Layout ──
left, right = st.columns(2)

# ═══════════════════════════════════
# LEFT: Capture + Transcript
# ═══════════════════════════════════
with left:
    st.subheader("📺 Capture + Transcript")

    component_value = st.components.v1.html("""
    <script>
    let fullTranscript = "";

    function sendData(type, data) {
        const streamlitMsg = {
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: {type: type, data: data}
        };
        window.parent.postMessage(streamlitMsg, "*");
    }

    async function takeScreenshot() {
        const stream = await navigator.mediaDevices.getDisplayMedia({video:true});
        const video = document.createElement('video');
        video.srcObject = stream;
        await video.play();

        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 450;
        canvas.getContext('2d').drawImage(video, 0, 0, 800, 450);

        const data = canvas.toDataURL('image/jpeg', 0.6);
        sendData('screenshot', data);

        stream.getTracks().forEach(t => t.stop());
    }

    function startSpeech() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            alert("Speech Recognition not supported. Use Chrome.");
            return;
        }

        const rec = new SR();
        rec.continuous = true;

        rec.onresult = (e) => {
            let text = "";
            for (let i = e.resultIndex; i < e.results.length; i++) {
                text += e.results[i][0].transcript;
            }
            fullTranscript += " " + text;
            document.getElementById("transcript").innerText = fullTranscript;

            sendData('transcript', fullTranscript);
        };

        rec.start();
    }
    </script>

    <button onclick="takeScreenshot()">📸 Take Screenshot</button>
    <button onclick="startSpeech()">🎙 Start Speech</button>

    <div id="transcript" style="margin-top:10px;color:white;"></div>
    """, height=300)

    # ✅ FIXED SAFE HANDLING
    if component_value and isinstance(component_value, dict):

        if component_value.get("type") == "screenshot":
            try:
                st.session_state.screenshot_b64 = component_value["data"].split(",")[1]
                st.success("✅ Screenshot captured & ready")
            except:
                st.error("❌ Screenshot processing failed")

        elif component_value.get("type") == "transcript":
            st.session_state["auto_prompt"] = component_value["data"]
            st.info("🎙 Transcript updated")

# ═══════════════════════════════════
# RIGHT: Chat
# ═══════════════════════════════════
with right:
    st.subheader("💬 AI Chat")

    # Show chat
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**AI:** {msg['text']}")

    user_input = st.chat_input("Ask something...")

    # Auto transcript injection
    if "auto_prompt" in st.session_state:
        user_input = st.session_state.pop("auto_prompt")

    def get_ai_response(api_key, history, user_text, screenshot_b64):
        client = OpenAI(api_key=api_key)

        content = []

        if screenshot_b64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{screenshot_b64}"
                }
            })

        content.append({"type": "text", "text": user_text})

        messages = [
            {"role": "system", "content": "You are a helpful meeting assistant."}
        ]

        # ✅ FIXED FORMAT
        for h in history:
            messages.append({
                "role": h["role"],
                "content": [{"type": "text", "text": h["text"]}]
            })

        messages.append({"role": "user", "content": content})

        try:
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=800
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    if user_input:
        if not st.session_state.api_key:
            st.error("⚠️ Enter API key")
        else:
            st.session_state.messages.append({
                "role": "user",
                "text": user_input
            })

            # ✅ LOADING INDICATOR
            with st.spinner("🤖 AI is analyzing..."):
                ai_text = get_ai_response(
                    st.session_state.api_key,
                    st.session_state.messages[-5:],
                    user_input,
                    st.session_state.screenshot_b64
                )

            st.session_state.messages.append({
                "role": "assistant",
                "text": ai_text
            })

            # clear screenshot after use
            st.session_state.screenshot_b64 = None

            st.rerun()
