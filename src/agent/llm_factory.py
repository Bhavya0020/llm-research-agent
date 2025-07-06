import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

load_dotenv()


def get_llm() -> BaseChatModel:
    """Get the appropriate LLM based on environment variables."""
    
    # Try Google Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    # print(gemini_key, "Gemini key")
    if gemini_key:
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
            google_api_key=gemini_key
        )
    
    # Fallback to OpenAI with default key (for testing)
    print("Warning: No API key found. Using OpenAI with default configuration.")
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1
    ) 