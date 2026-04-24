import os
import json
from typing import List, Dict, Any

class EpisodicMemoryJSON:
    """
    Manages episodic memory using a JSON file.
    Logs interaction episodes, summaries, and past experiences.
    """
    
    def __init__(self, file_path: str = "data/episodic_memory.json"):
        self.file_path = file_path
        self._ensure_file_exists()
        
    def _ensure_file_exists(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
                
    def _load_episodes(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
            
    def _save_episodes(self, episodes: List[Dict[str, Any]]) -> None:
        with open(self.file_path, 'w') as f:
            json.dump(episodes, f, indent=2)
            
    def add_episode(self, user_id: str, episode: str, metadata: Dict[str, Any] = None) -> None:
        """Add a new episode to the log."""
        episodes = self._load_episodes()
        new_entry = {
            "user_id": user_id,
            "episode": episode,
            "metadata": metadata or {}
        }
        import datetime
        new_entry["timestamp"] = datetime.datetime.now().isoformat()
        
        episodes.append(new_entry)
        self._save_episodes(episodes)
        
    def get_episodes(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent episodes for a user."""
        episodes = self._load_episodes()
        user_episodes = [e for e in episodes if e.get("user_id") == user_id]
        
        # Return the most recent 'limit' episodes
        return user_episodes[-limit:] if limit > 0 else user_episodes
        
    def clear(self, user_id: str = None) -> None:
        """Clear episodes, optionally for a specific user."""
        if user_id:
            episodes = self._load_episodes()
            episodes = [e for e in episodes if e.get("user_id") != user_id]
            self._save_episodes(episodes)
        else:
            self._save_episodes([])
