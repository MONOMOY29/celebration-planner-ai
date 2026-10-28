"""Gemini connection for the Celebration Planner."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-flash-lite-latest"


def get_client() -> genai.Client:
    """Create a Gemini client using the key from the environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")
    return genai.Client(api_key=api_key)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text reply."""
    client = get_client()
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


def ask_gemini_json(prompt: str) -> str:
    """Send a prompt to Gemini and ask for a JSON reply."""
    client = get_client()
    config = types.GenerateContentConfig(response_mime_type="application/json")
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )
    return response.text