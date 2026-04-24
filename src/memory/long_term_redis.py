import os
import json
import redis
from typing import Optional, Dict, Any

class LongTermMemoryRedis:
    """
    Manages long-term memory using Redis.
    Suitable for storing user profiles, preferences, and long-term facts.
    """
    
    def __init__(self, user_id: str = "default_user", redis_url: Optional[str] = None):
        if redis_url is None:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        
        self.user_id = user_id
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
        except redis.ConnectionError:
            print(f"Warning: Could not connect to Redis at {redis_url}. Running in mock mode.")
            self.client = None
            self.mock_db = {}
            
    def get_namespace_key(self, key: str) -> str:
        return f"memory:{self.user_id}:{key}"
        
    def set(self, key: str, value: Any) -> None:
        """Store a value in Redis."""
        namespaced_key = self.get_namespace_key(key)
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
            
        if self.client:
            self.client.set(namespaced_key, value_str)
        else:
            self.mock_db[namespaced_key] = value_str
            
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis."""
        namespaced_key = self.get_namespace_key(key)
        
        if self.client:
            value_str = self.client.get(namespaced_key)
        else:
            value_str = self.mock_db.get(namespaced_key)
            
        if value_str is None:
            return None
            
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            return value_str
            
    def get_all(self) -> Dict[str, Any]:
        """Retrieve all long-term memory for the user."""
        pattern = f"memory:{self.user_id}:*"
        results = {}
        
        if self.client:
            keys = self.client.keys(pattern)
            for k in keys:
                # Strip namespace
                simple_key = k.split(":")[-1]
                value_str = self.client.get(k)
                try:
                    results[simple_key] = json.loads(value_str)
                except json.JSONDecodeError:
                    results[simple_key] = value_str
        else:
            for k, v in self.mock_db.items():
                if k.startswith(f"memory:{self.user_id}:"):
                    simple_key = k.split(":")[-1]
                    try:
                        results[simple_key] = json.loads(v)
                    except json.JSONDecodeError:
                        results[simple_key] = v
                        
        return results

    def clear(self) -> None:
        """Clear all memory for the user."""
        pattern = f"memory:{self.user_id}:*"
        if self.client:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        else:
            self.mock_db = {k: v for k, v in self.mock_db.items() if not k.startswith(f"memory:{self.user_id}:")}
