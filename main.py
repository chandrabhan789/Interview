component_value = st.components.v1.html("""
<div style="color:white; display:flex; flex-direction:column; gap:10px; height:100%;">

<!-- Buttons -->
<div>
<button onclick="startCapture()">📺 Share Tab</button>
<button onclick="startSpeech()">🎙 Start Transcript</button>
<button onclick="takeShot()">📸 Screenshot</button>
</div>

<!-- Video (FIXED HEIGHT) -->
<div style="flex:0 0 auto;">
<video id="video" autoplay 
    style="
    width:100%;
    height:260px;   /* ✅ FIX: fixed height */
    object-fit:contain;
    border-radius:10px;
    background:black;">
</video>
</div>

<!-- Transcript (ALWAYS VISIBLE) -->
<div style="flex:1 1 auto; display:flex; flex-direction:column;">
<h4 style="margin:4px 0;">🎙 Live Transcript</h4>

<div id="transcript" 
    style="
    background:#111;
    padding:12px;
    border-radius:8px;
    min-height:80px;   /* ✅ Always 2–3 lines */
    max-height:120px;  /* ✅ Prevent overflow */
    font-size:14px;
    line-height:1.6;
    overflow-y:auto;
    color:#e2e8f0;">
</div>
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
