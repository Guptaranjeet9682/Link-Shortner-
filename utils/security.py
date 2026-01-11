import secrets
import string
from datetime import datetime

class Security:
    @staticmethod
    def generate_short_code(length=6):
        """Generate random short code"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_url(url):
        """Basic URL validation"""
        return url.startswith(('http://', 'https://'))
