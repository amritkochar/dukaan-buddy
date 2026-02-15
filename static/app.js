let isRecording = false;
let audioContext = null;
let sourceNode = null;
let processorNode = null;
let mediaStream = null;
let recordedChunks = [];
let currentLang = 'hi';
let messageCount = 0;
let detectedLanguage = 'hi-IN'; // Stores STT-detected language for dynamic TTS

const micButton = document.getElementById('micButton');
const micRing = document.getElementById('micRing');
const micLabel = document.getElementById('micLabel');
const statusText = document.getElementById('status');
const conversationArea = document.getElementById('conversation');
const soundWave = document.getElementById('soundWave');
const drawer = document.getElementById('drawer');
const drawerOverlay = document.getElementById('drawerOverlay');
const drawerToggle = document.getElementById('drawerToggle');
const drawerClose = document.getElementById('drawerClose');
const drawerHandleArea = document.getElementById('drawerHandleArea');
const msgBadge = document.getElementById('msgBadge');

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
        defaultStatus: '',
        responseError: 'समझ नहीं आया',
        micLabel: 'छोटू से बात करें',
        drawerEmpty: 'आपकी बातचीत यहाँ दिखेगी...'
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
        defaultStatus: '',
        responseError: 'Could not understand',
        micLabel: 'Talk to Chhotu',
        drawerEmpty: 'Your conversation will appear here...'
    }
};

window.setLanguage = function (lang) {
    currentLang = lang;

    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${lang}`).classList.add('active');

    document.documentElement.lang = lang;
    document.body.className = `grammar-${lang}`;

    document.querySelectorAll(`[data-${lang}]`).forEach(el => {
        el.textContent = el.getAttribute(`data-${lang}`);
    });

    conversationArea.setAttribute('data-empty', TRANSLATIONS[lang].drawerEmpty);

    if (!isRecording) {
        statusText.innerHTML = '&nbsp;';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    setLanguage('hi');
});

function getTrans(key) {
    return TRANSLATIONS[currentLang][key];
}

function openDrawer() {
    drawer.classList.add('open');
    drawerOverlay.classList.add('open');
    msgBadge.classList.remove('visible');
    messageCount = 0;
}

function closeDrawer() {
    drawer.classList.remove('open');
    drawerOverlay.classList.remove('open');
}

drawerToggle.addEventListener('click', () => {
    if (drawer.classList.contains('open')) {
        closeDrawer();
    } else {
        openDrawer();
    }
});
drawerOverlay.addEventListener('click', closeDrawer);
drawerClose.addEventListener('click', closeDrawer);
drawerHandleArea.addEventListener('click', closeDrawer);

function showSoundWave(type) {
    soundWave.classList.add('active');
    soundWave.classList.remove('speaking');
    if (type === 'speaking') {
        soundWave.classList.add('speaking');
    }
}

function hideSoundWave() {
    soundWave.classList.remove('active', 'speaking');
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
        statusText.className = 'processing';

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
        micRing.classList.add('recording');
        statusText.textContent = getTrans('recording');
        statusText.className = 'processing';
        micLabel.style.display = 'none';
        showSoundWave('recording');
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
    micRing.classList.remove('recording');
    micLabel.style.display = '';
    statusText.textContent = getTrans('processing');
    statusText.className = 'processing';
    hideSoundWave();

    const wavBlob = buildWav(recordedChunks, 16000);
    sendToSarvam(wavBlob);
}

function buildWav(chunks, sampleRate) {
    let totalLength = 0;
    for (const c of chunks) totalLength += c.length;
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const c of chunks) {
        merged.set(c, offset);
        offset += c.length;
    }

    const int16 = new Int16Array(merged.length);
    for (let i = 0; i < merged.length; i++) {
        const s = Math.max(-1, Math.min(1, merged[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

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
        detectedLanguage = data.language_code || 'hi-IN'; // Capture detected language, fallback to Hindi
        console.log('Detected language:', detectedLanguage);

        if (!transcript) {
            statusText.textContent = getTrans('noInput');
            statusText.className = '';
            return;
        }

        addMessage('user', transcript);

        statusText.textContent = getTrans('understanding');
        showSoundWave('processing');

        const ackPromise = fetch('/quick-ack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: transcript,
                language: detectedLanguage  // Use STT-detected language
            })
        });

        const processPromise = fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: transcript,
                language: detectedLanguage  // Use STT-detected language
            })
        });

        const ackRes = await ackPromise;
        if (ackRes.ok) {
            const ackData = await ackRes.json();
            if (ackData.ack_text) {
                statusText.textContent = getTrans('speaking');
                showSoundWave('speaking');
                await speakText(ackData.ack_text);
            }
        }

        statusText.textContent = getTrans('generating');
        const processRes = await processPromise;

        if (!processRes.ok) {
            const errText = await processRes.text();
            throw new Error(`Process API ${processRes.status}: ${errText}`);
        }

        const processData = await processRes.json();
        console.log('Process response:', processData);

        const responseText = processData.response_text || getTrans('responseError');

        addMessage('buddy', responseText);

        statusText.textContent = getTrans('speaking');
        showSoundWave('speaking');
        await speakText(responseText);

        statusText.innerHTML = '&nbsp;';
        statusText.className = '';
        hideSoundWave();

    } catch (err) {
        statusText.textContent = getTrans('error') + err.message;
        statusText.className = '';
        hideSoundWave();
        console.error('Pipeline error:', err);
    }
}

async function speakText(text, languageCode = null) {
    const targetLang = languageCode || detectedLanguage || 'hi-IN';

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
            target_language_code: targetLang,  // Dynamic language
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

    conversationArea.scrollTop = conversationArea.scrollHeight;

    if (!drawer.classList.contains('open')) {
        messageCount++;
        msgBadge.textContent = messageCount;
        msgBadge.classList.add('visible');
    }
}

const demoToast = document.getElementById('demoToast');
const demoReset = document.getElementById('demoReset');
const demoSeed = document.getElementById('demoSeed');

function showToast(msg) {
    demoToast.textContent = msg;
    demoToast.classList.add('show');
    setTimeout(() => demoToast.classList.remove('show'), 2500);
}

demoReset.addEventListener('click', async () => {
    demoReset.disabled = true;
    demoReset.textContent = '...';
    try {
        const res = await fetch('/demo/reset', { method: 'POST' });
        if (res.ok) {
            showToast('All data cleared');
        } else {
            showToast('Failed to clear data');
        }
    } catch (e) {
        showToast('Error: ' + e.message);
    }
    demoReset.textContent = 'Clear All';
    demoReset.disabled = false;
});

demoSeed.addEventListener('click', async () => {
    demoSeed.disabled = true;
    demoSeed.textContent = '...';
    try {
        const res = await fetch('/demo/seed', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message + ' to inventory');
        } else {
            showToast('Failed to load items');
        }
    } catch (e) {
        showToast('Error: ' + e.message);
    }
    demoSeed.textContent = 'Load Kirana Store';
    demoSeed.disabled = false;
});
