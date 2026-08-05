import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.config import get_settings
from src.llm.client import get_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_llm")


async def main():
    settings = get_settings()
    logger.info(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")

    if settings.LLM_PROVIDER == "groq":
        key_status = "Configured" if settings.GROQ_API_KEY else "MISSING / EMPTY"
        logger.info(f"GROQ_API_KEY: {key_status}")
        logger.info(f"GROQ_MODEL: {settings.GROQ_MODEL}")
    elif settings.LLM_PROVIDER == "openai":
        key_status = "Configured" if settings.OPENAI_API_KEY else "MISSING / EMPTY"
        logger.info(f"OPENAI_API_KEY: {key_status}")
        logger.info(f"OPENAI_MODEL: {settings.OPENAI_MODEL}")

    sys_prompt = "You are a helpful food critic. Output strictly valid JSON."
    user_prompt = (
        '{"message": "Hello! Recommend 1 dish for testing in JSON schema: '
        '{\\"dish\\": \\"string\\", \\"reason\\": \\"string\\"}"}'
    )

    client = get_llm_client()
    logger.info(f"Testing LLM Client: {type(client).__name__}...")

    try:
        response = await client.generate_completion(sys_prompt, user_prompt)
        print("\n--- LLM API Response ---")
        print(response)
        print("------------------------\n")
        logger.info("✅ LLM Connection test SUCCESSFUL!")
    except Exception as e:
        logger.error(f"❌ LLM Connection failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
