import logging
from sarvamai import SarvamAI
from bot.config import BotConfig
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SarvamClient:
    """Client for interacting with Sarvam API"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = SarvamAI(api_subscription_key=config.sarvam_api_key)

    async def generate_response(
        self,
        messages: List[Dict[str, str]]
    ) -> Optional[str]:
        try:
            if not messages or messages[0].get("role") != "user":
                messages.insert(0, {
                    "role": "user",
                    "content": self.config.system_prompt
                })

            logger.info("Sending request to Sarvam API")
            # Ensure the API call is awaited if it's async, else run in executor
            import asyncio
            if asyncio.iscoroutinefunction(self.client.chat.completions):
                response = await self.client.chat.completions(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=self.config.max_response_length
                )
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions(
                        messages=messages,
                        temperature=0.7,
                        max_tokens=self.config.max_response_length
                    )
                )
            logger.debug(f"Sarvam raw response: {response}")

            # Try to support both dict and object response
            choices = None
            if isinstance(response, dict):
                choices = response.get("choices")
            elif hasattr(response, "choices"):
                choices = getattr(response, "choices")
            if choices and len(choices) > 0:
                # Try to support both dict and object message
                message = choices[0].get("message") if isinstance(choices[0], dict) else getattr(choices[0], "message", None)
                if message:
                    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
                    if content:
                        return content.strip()
            logger.warning("No response choices from Sarvam")
            return "Sorry, I couldn't generate a response."

        except Exception as e:
            logger.error(f"Sarvam API Error: {e}")
            return "Sorry, I encountered an error while generating a response."
