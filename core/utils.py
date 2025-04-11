# core/utils.py
import io
import asyncio
import logging
import os
import sys
from azure.core.exceptions import ServiceRequestError

# Add the parent directory to the path to allow imports from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.azure_client import analyze_image
except ImportError:
    # Fallback for direct execution
    logger = logging.getLogger(__name__)
    logger.warning("Could not import analyze_image from core.azure_client")

logger = logging.getLogger(__name__)

async def analyze_image_with_retry(img_stream: io.BytesIO, language_hints=["en", "ru"], max_retries=3, retry_delay=2):
    """Analyzes the image with retry logic using asyncio."""
    try:
        # Read bytes once to avoid stream issues in to_thread
        image_bytes_data = img_stream.getvalue()
        if not image_bytes_data:
            raise ValueError("Empty image data received")

        for attempt in range(max_retries):
            try:
                # Create a new stream for each attempt and seek to start
                current_stream = io.BytesIO(image_bytes_data)
                current_stream.seek(0)

                # Call analyze_image and await its result
                read_response = await analyze_image(
                    current_stream,
                    language_hints=language_hints
                )

                if not read_response:
                    raise ValueError("Empty response from Azure API")

                return read_response
            except ServiceRequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Temporary connection error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Error after {max_retries} retries: {e}")
                    raise
            except Exception as e:
                logger.exception(f"An unexpected error occurred during image analysis: {e}")
                raise
    except Exception as e:
        logger.exception(f"Failed to process image: {e}")
        raise
    finally:
        try:
            img_stream.close()
        except:
            pass

def split_long_message(text: str, chunk_size: int = 4000):
    """Splits a long text into chunks of a specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# For testing when run directly
if __name__ == "__main__":
    print("Utils module loaded successfully")