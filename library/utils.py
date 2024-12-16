import base64
import os
from dotenv import load_dotenv
from loguru import logger
from typing import Union


def encode_image_to_base64(file_path: Union[str, bytes]) -> str:
    """
    Convert image to base64

    Args:
        file_path (Union[str, bytes]): Path or bytes of image

    Returns:
        Base64 encoded string
    """
    if isinstance(file_path, str):
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    elif isinstance(file_path, bytes):
        return base64.b64encode(file_path).decode("utf-8")

    raise ValueError("Invalid image input")


def get_env_file():
    _ = load_dotenv(override=True)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    logger.info(f"Current environment: {ENVIRONMENT}")

    if ENVIRONMENT == "production":
        ENV_FILE = ".env"
    elif ENVIRONMENT == "development":
        ENV_FILE = ".env.dev"
    else:
        ENV_FILE = f".env.{ENVIRONMENT}" if ENVIRONMENT else ".env"

    logger.info(f"Using env file: {ENV_FILE}")

    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE, override=True)
        logger.info(f"Loaded environment variables from {ENV_FILE}")
    else:
        logger.info(
            f"Environment file {ENV_FILE} does not exist; using system environment variables."
        )

    return ENV_FILE
