// Check authentication on load
async function checkAuth() {
    const response = await fetch('/api/check-auth');
    const data = await response.json();
    
    if (!data.authenticated) {
        window.location.href = '/';
    } else {
        loadRecentLinks();
    }
}

// Shorten URL
async function shortenUrl() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('Please enter a URL');
        return;
    }
    
    try {
        const response = await fetch('/api/shorten', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show result
            document.getElementById('shortUrl').textContent = result.short_url;
            document.getElementById('resultContainer').style.display = 'block';
            urlInput.value = '';
            
            // Reload recent links
            loadRecentLinks();
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

// Load recent links
async function loadRecentLinks() {
    try {
        const response = await fetch('/api/links');
        const data = await response.json();
        
        const linksList = document.getElementById('linksList');
        linksList.innerHTML = '';
        
        data.links.forEach(link => {
            const linkItem = document.createElement('div');
            linkItem.className = 'link-item';
            
            const shortUrl = `${window.location.origin}/${link.short_code}`;
            
            linkItem.innerHTML = `
                <div class="link-info">
                    <div class="short-code">${link.short_code}</div>
                    <div class="original-url">${link.original_url.substring(0, 50)}...</div>
                    <div class="link-stats">
                        Clicks: ${link.click_count || 0} | 
                        Created: ${new Date(link.created_at).toLocaleDateString()}
                    </div>
                </div>
                <div class="link-actions">
                    <button class="copy-btn" onclick="copyLink('${shortUrl}')">Copy</button>
                    <button class="share-btn" onclick="shareSpecificLink('${shortUrl}')">Share</button>
                </div>
            `;
            
            linksList.appendChild(linkItem);
        });
    } catch (error) {
        console.error('Error loading links:', error);
    }
}

// Copy to clipboard
async function copyToClipboard() {
    const text = document.getElementById('shortUrl').textContent;
    await navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
}

function copyLink(url) {
    navigator.clipboard.writeText(url);
    alert('Copied to clipboard!');
}

// Share link
async function shareLink() {
    const url = document.getElementById('shortUrl').textContent;
    
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'Shortened Link',
                text: 'Check out this shortened link',
                url: url
            });
        } catch (error) {
            copyToClipboard();
        }
    } else {
        copyToClipboard();
    }
}

function shareSpecificLink(url) {
    if (navigator.share) {
        navigator.share({
            title: 'Shortened Link',
            text: 'Check out this shortened link',
            url: url
        });
    } else {
        copyLink(url);
    }
}

// Logout
function logout() {
    window.location.href = '/logout';
}

// Initialize
document.addEventListener('DOMContentLoaded', checkAuth);

// Enter key support
document.getElementById('urlInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        shortenUrl();
    }
});
