"""
Configuration management for the Discord AI bot
"""
import os
from typing import Optional

class BotConfig:
    """Configuration class for bot settings"""

    def __init__(self):
        # Discord settings
        self.discord_token: str = os.getenv("DISCORD_TOKEN", "")
        self.command_prefix: str = os.getenv("COMMAND_PREFIX", "!")
        self.chat_channel_id: Optional[int] = self._get_channel_id()

        # Admin settings
        self.admin_user_id: int = int(os.getenv("ADMIN_USER_ID", "782306059469193257"))
        self.help_server_invite: str = os.getenv("HELP_SERVER_INVITE", "https://discord.gg/k7Sss4yKj5")

        # Sarvam AI settings
        self.sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
        self.sarvam_base_url: str = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1/chat/completions")
        self.sarvam_model_name: str = os.getenv("SARVAM_MODEL_NAME", "sarvam-m")

        # Bot personality and behavior
        self.system_prompt: str = self._get_system_prompt()
        self.max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
        self.max_response_length: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))

        # Fun features
        self.enable_auto_reactions: bool = os.getenv("ENABLE_AUTO_REACTIONS", "true").lower() == "true"
        self.daily_greeting: bool = os.getenv("DAILY_GREETING", "false").lower() == "true"

        # Retry handling
        self.retry_delay_base: float = float(os.getenv("RETRY_DELAY_BASE", "1.0"))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

    def _get_channel_id(self) -> Optional[int]:
        """Get chat channel ID from environment"""
        channel_id = os.getenv("CHAT_CHANNEL_ID")
        if channel_id:
            try:
                return int(channel_id)
            except ValueError:
                return None
        return None

    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI"""
        default_prompt = """You are a friendly and helpful AI assistant on Discord. 
        You should be conversational, engaging, and provide useful responses. 
        Keep your messages concise but informative. Use Discord markdown when appropriate 
        (like **bold** for emphasis, `code` for code snippets, etc.). 
        Be respectful and maintain a positive tone in all interactions."""
        return os.getenv("SYSTEM_PROMPT", default_prompt)

    def validate(self) -> bool:
        """Validate that required configuration is present"""
        required_vars = [
            ("DISCORD_TOKEN", self.discord_token),
            ("SARVAM_API_KEY", self.sarvam_api_key)
        ]

        for var_name, var_value in required_vars:
            if not var_value:
                print(f"Error: {var_name} environment variable is required")
                return False

        return True
