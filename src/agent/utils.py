import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
from langchain_core.language_models.chat_models import BaseChatModel

def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Get the standard LLM configured for this project."""
    # Try getting the API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        # Let's fallback to a fake or throw. We need real keys for evaluation.
        # But we'll allow it to instantiate so we can mock/test.
        print("Warning: OPENAI_API_KEY is not set correctly. Calls to OpenAI will fail.")
        api_key = "dummy_key"
        
    return ChatOpenAI(model="gpt-4o-mini", temperature=temperature, api_key=api_key)
