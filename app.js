let isRecording = false;
let audioContext = null;
let sourceNode = null;
let processorNode = null;
let mediaStream = null;
let recordedChunks = [];

const micButton = document.getElementById('micButton');
const statusText = document.getElementById('status');
const transcriptArea = document.getElementById('transcript');

micButton.addEventListener('click', async () => {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
});

async function startRecording() {
    try {
        statusText.textContent = 'Requesting mic...';

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
        micButton.textContent = '⏹ Stop';
        micButton.classList.add('recording');
        statusText.textContent = 'Recording... click Stop when done';
    } catch (err) {
        statusText.textContent = 'Error: ' + err.message;
        console.error(err);
    }
}

function stopRecording() {
    isRecording = false;

    processorNode?.disconnect();
    sourceNode?.disconnect();
    mediaStream?.getTracks().forEach(t => t.stop());
    audioContext?.close();

    micButton.textContent = '🎤 Record';
    micButton.classList.remove('recording');
    statusText.textContent = 'Processing...';

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
        const res = await fetch(SARVAM_STT_URL, {
            method: 'POST',
            headers: {
                'api-subscription-key': SARVAM_API_KEY
            },
            body: formData
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`API ${res.status}: ${errText}`);
        }

        const data = await res.json();
        console.log('Sarvam response:', data);

        const text = data.transcript || JSON.stringify(data);
        const div = document.createElement('div');
        div.className = 'transcript-entry';
        div.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> <span class="text">${text}</span>`;
        transcriptArea.appendChild(div);
        transcriptArea.scrollTop = transcriptArea.scrollHeight;

        // Now send transcript to TTS
        if (data.transcript) {
            statusText.textContent = 'Generating speech...';
            await speakText(data.transcript);
        }

        statusText.textContent = 'Done! Click Record to go again.';
    } catch (err) {
        statusText.textContent = 'Error: ' + err.message;
        console.error('Sarvam API error:', err);
    }
}

async function speakText(text) {
    const res = await fetch(SARVAM_TTS_URL, {
        method: 'POST',
        headers: {
            'api-subscription-key': SARVAM_API_KEY,
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
    await audio.play();
}
