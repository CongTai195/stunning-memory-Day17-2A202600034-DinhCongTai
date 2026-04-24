import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

class SemanticMemoryChroma:
    """
    Manages semantic memory using ChromaDB.
    Indexes conversation snippets and facts for semantic retrieval.
    """
    
    def __init__(self, collection_name: str = "memory_collection", persist_directory: str = "data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
    def add_memory(self, text: str, metadata: Dict[str, Any] = None, memory_id: str = None) -> None:
        """Add a text snippet to semantic memory."""
        import uuid
        if not memory_id:
            memory_id = str(uuid.uuid4())
            
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[memory_id]
        )
        
    def search(self, query: str, n_results: int = 3, filter_metadata: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Search for relevant memory snippets based on a query."""
        if self.collection.count() == 0:
            return []
            
        # Ensure we don't request more results than we have
        n_results = min(n_results, self.collection.count())
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i] if results.get("ids") else None,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
                
        return formatted_results
        
    def clear(self) -> None:
        """Clear all semantic memory."""
        # Simple way to clear is to delete the collection and recreate it
        collection_name = self.collection.name
        try:
            self.client.delete_collection(name=collection_name)
        except ValueError:
            pass # Ignore if it doesn't exist
            
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
