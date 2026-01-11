from pymongo import MongoClient
from datetime import datetime
import os

class Database:
    def __init__(self):
        # MongoDB connection string
        connection_string = "mongodb+srv://Anish_Gupta:Anish_Gupta@linkshortner.huk3frj.mongodb.net/?appName=LinkShortner"
        self.client = MongoClient(connection_string)
        self.db = self.client['link_shortener']
        self.links = self.db['links']
        
        # Create indexes
        self.links.create_index('short_code', unique=True)
        self.links.create_index('created_at')
    
    def save_link(self, link_data):
        """Save link to database"""
        return self.links.insert_one(link_data)
    
    def get_link(self, short_code):
        """Get link by short code"""
        return self.links.find_one({'short_code': short_code})
    
    def get_recent_links(self, limit=10):
        """Get recent shortened links"""
        cursor = self.links.find().sort('created_at', -1).limit(limit)
        links = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            doc['created_at'] = doc['created_at'].isoformat()
            links.append(doc)
        return links
    
    def increment_click(self, short_code):
        """Increment click count"""
        return self.links.update_one(
            {'short_code': short_code},
            {'$inc': {'click_count': 1}}
        )
