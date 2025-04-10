# core/azure_client.py
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import asyncio
import os
import sys

# Add the parent directory to the path to allow imports from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.config import ENDPOINT, SUBSCRIPTION_KEY
except ImportError:
    # Fallback for direct execution
    from dotenv import load_dotenv
    load_dotenv()
    ENDPOINT = os.getenv("AiAzureEndPoint")
    SUBSCRIPTION_KEY = os.getenv("AiAzureToken")

# Initialize Computer Vision client
computervision_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

async def analyze_image(img_stream, language_hints=["en", "ru"]):
    """Analyzes the image using Azure Computer Vision."""
    # Run the blocking SDK call in a separate thread
    read_response = await asyncio.to_thread(
        computervision_client.recognize_printed_text_in_stream,
        img_stream,
        language_hints=language_hints
    )
    return read_response

# For testing when run directly
if __name__ == "__main__":
    print("Azure client module loaded successfully")
    print(f"ENDPOINT: {ENDPOINT}")
    print(f"SUBSCRIPTION_KEY: {'*' * len(SUBSCRIPTION_KEY) if SUBSCRIPTION_KEY else 'None'}")