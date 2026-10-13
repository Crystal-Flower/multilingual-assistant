const recordButton = document.getElementById('recordButton');
const statusText = document.getElementById('status');
const audioPlayback = document.getElementById('audioPlayback');

let recognition;
let isRecording = false;

// Check for Web Speech API browser compatibility
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US'; // You can change this dynamically
    recognition.interimResults = false;

    recognition.onstart = () => {
        isRecording = true;
        statusText.textContent = 'Status: Listening...';
        recordButton.textContent = 'Stop Recording';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        statusText.textContent = `You said: "${transcript}"`;
        isRecording = false;
        recordButton.textContent = 'Start Recording';
        sendTextToBackend(transcript);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        statusText.textContent = `Status: Error - ${event.error}`;
        isRecording = false;
        recordButton.textContent = 'Start Recording';
    };

    recognition.onend = () => {
        if (isRecording) {
            recognition.start(); // Restart if continuous is not enabled
        }
    };
} else {
    statusText.textContent = 'Status: Web Speech API not supported in this browser.';
    recordButton.disabled = true;
}

recordButton.addEventListener('click', () => {
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

function sendTextToBackend(text) {
    statusText.textContent = 'Status: Thinking...';

    // This is a placeholder. You need to create a backend to handle this.
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.audioUrl) {
            audioPlayback.src = data.audioUrl;
            audioPlayback.play();
            statusText.textContent = 'Status: Playing response...';
        } else {
            statusText.textContent = 'Status: No audio response.';
        }
    })
    .catch(error => {
        console.error('Error with backend call:', error);
        statusText.textContent = 'Status: Failed to get response.';
    });
}