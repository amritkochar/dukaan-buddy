let isRecording = false;
let audioContext = null;
let sourceNode = null;
let processorNode = null;
let mediaStream = null;
let recordedChunks = [];
let currentLang = 'hi';

const micButton = document.getElementById('micButton');
const statusText = document.getElementById('status');
const conversationArea = document.getElementById('conversation');

// Translations configuration
const TRANSLATIONS = {
    hi: {
        micStart: 'माइक शुरू हो रहा है...',
        recording: '🔴 रिकॉर्डिंग... बोलिए',
        processing: '⏳ प्रोसेस हो रहा है...',
        listening: '🎧 सुन रहा हूँ...',
        noInput: 'कुछ सुनाई नहीं दिया, फिर कोशिश करें',
        understanding: '💭 समझ रहा हूँ...',
        speaking: '🗣️ बोल रहा हूँ...',
        generating: '⏳ जवाब तैयार हो रहा है...',
        error: 'Error: ',
        defaultStatus: 'माइक दबाएं और बोलें',
        responseError: 'समझ नहीं आया'
    },
    en: {
        micStart: 'Starting microphone...',
        recording: '🔴 Recording... Speak now',
        processing: '⏳ Processing...',
        listening: '🎧 Listening...',
        noInput: 'Could not hear anything, please try again',
        understanding: '💭 Understanding...',
        speaking: '🗣️ Speaking...',
        generating: '⏳ Generating response...',
        error: 'Error: ',
        defaultStatus: 'Press mic and speak',
        responseError: 'Could not understand'
    }
};

// Language switching function
window.setLanguage = function (lang) {
    currentLang = lang;

    // Update active button state
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${lang}`).classList.add('active');

    // Update HTML lang attribute and body class for CSS
    document.documentElement.lang = lang;
    document.body.className = `grammar-${lang}`; // For empty state CSS

    // Update static text elements
    document.querySelectorAll(`[data-${lang}]`).forEach(el => {
        el.textContent = el.getAttribute(`data-${lang}`);
    });

    // Update current status text if it matches one of our known states/defaults
    // Or just reset to default state to be safe/clean
    if (!isRecording) {
        statusText.textContent = TRANSLATIONS[lang].defaultStatus;
    }
}

// Initialize - set default to Hindi explicitly to trigger CSS classes
window.addEventListener('DOMContentLoaded', () => {
    setLanguage('hi');
});

function getTrans(key) {
    return TRANSLATIONS[currentLang][key];
}

micButton.addEventListener('click', async () => {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
});

async function startRecording() {
    try {
        statusText.textContent = getTrans('micStart');
        statusText.className = '';

        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: { channelCount: 1, sampleRate: 16000 }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000
        });

        sourceNode = audioContext.createMediaStreamSource(mediaStream);
        processorNode = audioContext.createScriptProcessor(4096, 1, 1);
        recordedChunks = [];

        processorNode.onaudioprocess = (e) => {
            if (isRecording) {
                const samples = new Float32Array(e.inputBuffer.getChannelData(0));
                recordedChunks.push(samples);
            }
        };

        sourceNode.connect(processorNode);
        processorNode.connect(audioContext.destination);

        isRecording = true;
        micButton.textContent = '⏹';
        micButton.classList.add('recording');
        statusText.textContent = getTrans('recording');
        statusText.className = 'processing';
    } catch (err) {
        statusText.textContent = getTrans('error') + err.message;
        console.error(err);
    }
}

function stopRecording() {
    isRecording = false;

    processorNode?.disconnect();
    sourceNode?.disconnect();
    mediaStream?.getTracks().forEach(t => t.stop());
    audioContext?.close();

    micButton.textContent = '🎤';
    micButton.classList.remove('recording');
    statusText.textContent = getTrans('processing');
    statusText.className = 'processing';

    const wavBlob = buildWav(recordedChunks, 16000);
    sendToSarvam(wavBlob);
}

function buildWav(chunks, sampleRate) {
    // Merge all chunks
    let totalLength = 0;
    for (const c of chunks) totalLength += c.length;
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const c of chunks) {
        merged.set(c, offset);
        offset += c.length;
    }

    // Float32 -> Int16
    const int16 = new Int16Array(merged.length);
    for (let i = 0; i < merged.length; i++) {
        const s = Math.max(-1, Math.min(1, merged[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // WAV header + data
    const dataSize = int16.length * 2;
    const buffer = new ArrayBuffer(44 + dataSize);
    const v = new DataView(buffer);

    writeStr(v, 0, 'RIFF');
    v.setUint32(4, 36 + dataSize, true);
    writeStr(v, 8, 'WAVE');
    writeStr(v, 12, 'fmt ');
    v.setUint32(16, 16, true);
    v.setUint16(20, 1, true);
    v.setUint16(22, 1, true);
    v.setUint32(24, sampleRate, true);
    v.setUint32(28, sampleRate * 2, true);
    v.setUint16(32, 2, true);
    v.setUint16(34, 16, true);
    writeStr(v, 36, 'data');
    v.setUint32(40, dataSize, true);

    new Int16Array(buffer, 44).set(int16);

    return new Blob([buffer], { type: 'audio/wav' });
}

function writeStr(view, offset, str) {
    for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
    }
}

async function sendToSarvam(wavBlob) {
    const formData = new FormData();
    formData.append('file', wavBlob, 'recording.wav');
    formData.append('model', SARVAM_STT_MODEL);
    formData.append('mode', 'transcribe');
    formData.append('language_code', 'unknown');

    try {
        statusText.textContent = getTrans('listening');

        const res = await fetch(SARVAM_STT_URL, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`STT API ${res.status}: ${errText}`);
        }

        const data = await res.json();
        console.log('Sarvam STT response:', data);

        const transcript = data.transcript || '';
        if (!transcript) {
            statusText.textContent = getTrans('noInput');
            statusText.className = '';
            return;
        }

        // Add user message to conversation
        addMessage('user', transcript);

        // Fire both endpoints in parallel
        statusText.textContent = getTrans('understanding');

        const ackPromise = fetch('/quick-ack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript })
        });

        const processPromise = fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript, language: currentLang === 'hi' ? 'hi-IN' : 'en-US' })
        });

        // Wait for ack and play it immediately
        const ackRes = await ackPromise;
        if (ackRes.ok) {
            const ackData = await ackRes.json();
            if (ackData.ack_text) {
                statusText.textContent = getTrans('speaking');
                await speakText(ackData.ack_text);
            }
        }

        // Wait for full response
        statusText.textContent = getTrans('generating');
        const processRes = await processPromise;

        if (!processRes.ok) {
            const errText = await processRes.text();
            throw new Error(`Process API ${processRes.status}: ${errText}`);
        }

        const processData = await processRes.json();
        console.log('Process response:', processData);

        const responseText = processData.response_text || getTrans('responseError');

        // Add buddy response to conversation
        addMessage('buddy', responseText);

        // Speak the response
        statusText.textContent = getTrans('speaking');
        await speakText(responseText);

        statusText.textContent = getTrans('defaultStatus');
        statusText.className = '';

    } catch (err) {
        statusText.textContent = getTrans('error') + err.message;
        statusText.className = '';
        console.error('Pipeline error:', err);
    }
}

async function speakText(text) {
    const res = await fetch(SARVAM_TTS_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text,
            model: SARVAM_TTS_MODEL,
            speaker: SARVAM_TTS_SPEAKER,
            pace: SARVAM_TTS_PACE,
            target_language_code: SARVAM_TTS_LANG,
            speech_sample_rate: 24000
        })
    });

    if (!res.ok) {
        const errText = await res.text();
        throw new Error(`TTS API ${res.status}: ${errText}`);
    }

    const data = await res.json();
    const audioBase64 = data.audios[0];
    const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
    const blob = new Blob([audioBytes], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);

    const audio = new Audio(url);

    // Return promise that resolves when audio finishes playing
    return new Promise((resolve, reject) => {
        audio.onended = resolve;
        audio.onerror = reject;
        audio.play().catch(reject);
    });
}

function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'bubble';
    bubbleDiv.textContent = text;

    messageDiv.appendChild(bubbleDiv);
    conversationArea.appendChild(messageDiv);

    // Scroll to bottom
    conversationArea.scrollTop = conversationArea.scrollHeight;
}
