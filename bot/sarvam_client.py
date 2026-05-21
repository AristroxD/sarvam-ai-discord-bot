import logging
import asyncio
import hashlib
import time
from functools import lru_cache
from sarvamai import SarvamAI
from bot.config import BotConfig
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    """Thinking mode enumeration"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    AUTO = "auto"  # Auto-detect based on query complexity


class ResponseType(Enum):
    """Response type enumeration"""
    QUICK = "quick"
    DETAILED = "detailed"
    STREAMING = "streaming"


@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    hit_count: int = 0
    ttl_seconds: int = 3600  # Default 1 hour
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)
    
    def touch(self) -> None:
        """Update hit count and timestamp"""
        self.hit_count += 1
        self.timestamp = datetime.now()


class SarvamClient:
    """Advanced Sarvam API Client with caching, retry logic, and thinking control"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = SarvamAI(api_subscription_key=config.sarvam_api_key)
        
        # Advanced features
        self.response_cache: Dict[str, CacheEntry] = {}
        self.thinking_mode = ThinkingMode.AUTO
        self.response_type = ResponseType.QUICK
        self.max_cache_size = 1000
        self.request_timeout = 30
        self.request_semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        
        # Stats tracking
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "retries": 0,
        }

    def _generate_cache_key(self, messages: List[Dict[str, str]], use_thinking: bool = False) -> str:
        """Generate deterministic cache key from messages"""
        msg_str = str(sorted([(m.get("role"), m.get("content")) for m in messages]))
        thinking_str = str(use_thinking)
        cache_input = f"{msg_str}:{thinking_str}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Retrieve response from cache if valid"""
        if cache_key in self.response_cache:
            entry = self.response_cache[cache_key]
            if not entry.is_expired():
                entry.touch()
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache HIT (count: {entry.hit_count}): {cache_key}")
                return entry.content
            else:
                # Remove expired entry
                del self.response_cache[cache_key]
        
        self.stats["cache_misses"] += 1
        return None

    def _cache_response(self, cache_key: str, content: str, ttl_seconds: int = 3600) -> None:
        """Store response in cache with TTL"""
        # Implement simple LRU eviction
        if len(self.response_cache) >= self.max_cache_size:
            # Remove least used entry
            least_used = min(
                self.response_cache.items(),
                key=lambda x: (x[1].hit_count, x[1].timestamp)
            )
            del self.response_cache[least_used[0]]
            logger.debug(f"Evicted cache entry: {least_used[0]}")
        
        self.response_cache[cache_key] = CacheEntry(content, ttl_seconds=ttl_seconds)
        logger.debug(f"Cached response: {cache_key}")

    def _is_complex_query(self, messages: List[Dict[str, str]]) -> bool:
        """Detect query complexity for AUTO thinking mode"""
        complexity_indicators = [
            "explain", "analyze", "compare", "contrast", "research",
            "solve", "calculate", "debug", "design", "architecture",
            "why", "how", "complex", "complicated"
        ]
        
        full_text = " ".join([m.get("content", "").lower() for m in messages])
        return any(indicator in full_text for indicator in complexity_indicators)

    def _get_thinking_config(self, use_thinking: Optional[bool] = None) -> Dict[str, Any]:
        """Get thinking configuration based on mode"""
        if use_thinking is None:
            # Use AUTO mode
            if self.thinking_mode == ThinkingMode.AUTO:
                # This will be determined per request
                return {}
            elif self.thinking_mode == ThinkingMode.ENABLED:
                use_thinking = True
            else:
                use_thinking = False
        
        if use_thinking:
            return {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2000  # Configurable thinking budget
                }
            }
        else:
            return {
                "thinking": {
                    "type": "disabled"
                }
            }

    def _build_request_params(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_thinking: Optional[bool] = None,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """Build comprehensive API request parameters"""
        if max_tokens is None:
            max_tokens = self.config.max_response_length
        
        params = {
            "model": self.config.sarvam_model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        
        # Add thinking configuration
        params.update(self._get_thinking_config(use_thinking))
        
        return params

    def _extract_content_from_response(self, response: Any) -> Optional[str]:
        """Robustly extract content from various response formats"""
        try:
            choices = None
            
            # Support dict and object responses
            if isinstance(response, dict):
                choices = response.get("choices")
            elif hasattr(response, "choices"):
                choices = getattr(response, "choices")
            
            if not choices or len(choices) == 0:
                logger.warning("No response choices from Sarvam")
                return None
            
            # Extract message from first choice
            choice = choices[0]
            message = None
            
            if isinstance(choice, dict):
                message = choice.get("message")
            elif hasattr(choice, "message"):
                message = getattr(choice, "message")
            
            if not message:
                logger.warning("No message in response choice")
                return None
            
            # Extract content from message
            content = None
            if isinstance(message, dict):
                content = message.get("content")
            elif hasattr(message, "content"):
                content = getattr(message, "content")
            
            if content:
                return content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting content from response: {e}")
            return None

    async def _call_api(self, request_params: Dict[str, Any]) -> Any:
        """Call Sarvam API with error handling"""
        try:
            import asyncio as aio
            
            if aio.iscoroutinefunction(self.client.chat.completions):
                response = await asyncio.wait_for(
                    self.client.chat.completions(**request_params),
                    timeout=self.request_timeout
                )
            else:
                loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self.client.chat.completions(**request_params)
                    ),
                    timeout=self.request_timeout
                )
            
            return response
            
        except asyncio.TimeoutError:
            logger.error("Sarvam API request timed out")
            raise
        except Exception as e:
            logger.error(f"Sarvam API call failed: {e}")
            raise

    async def _retry_with_backoff(
        self,
        request_params: Dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Optional[Any]:
        """Retry API call with exponential backoff"""
        for attempt in range(max_retries):
            try:
                response = await self._call_api(request_params)
                return response
            
            except Exception as e:
                self.stats["retries"] += 1
                
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached. Last error: {e}")
                    return None
                
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        return None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        use_thinking: Optional[bool] = None,
        response_type: ResponseType = ResponseType.QUICK,
        cache_ttl: int = 3600,
        use_cache: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate response from Sarvam API with advanced features.
        
        Args:
            messages: List of message dictionaries
            use_thinking: Enable/disable thinking. None = AUTO mode
            response_type: QUICK, DETAILED, or STREAMING
            cache_ttl: Cache TTL in seconds
            use_cache: Whether to use caching
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum response tokens
        
        Returns:
            Generated response string or None on error
        """
        try:
            self.stats["total_requests"] += 1
            
            # Validate and normalize messages
            if not messages or messages[0].get("role") != "user":
                messages.insert(0, {
                    "role": "user",
                    "content": self.config.system_prompt
                })
            
            # Generate cache key
            cache_key = self._generate_cache_key(messages, use_thinking or False)
            
            # Check cache
            if use_cache:
                cached = self._get_cached_response(cache_key)
                if cached:
                    return cached
            
            # Determine thinking mode for AUTO
            if use_thinking is None and self.thinking_mode == ThinkingMode.AUTO:
                use_thinking = self._is_complex_query(messages)
                logger.info(f"AUTO mode: Complex query detected = {use_thinking}")
            
            logger.info(f"Sending request to Sarvam API (thinking={use_thinking})")
            
            # Acquire semaphore to limit concurrent requests
            async with self.request_semaphore:
                # Build request parameters
                request_params = self._build_request_params(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    use_thinking=use_thinking,
                )
                
                # Call API with retries
                response = await self._retry_with_backoff(
                    request_params,
                    max_retries=self.config.max_retries,
                    base_delay=self.config.retry_delay_base
                )
                
                if response is None:
                    self.stats["errors"] += 1
                    return "Sorry, I encountered an error while generating a response."
                
                logger.debug(f"Sarvam raw response: {response}")
                
                # Extract content
                content = self._extract_content_from_response(response)
                
                if not content:
                    self.stats["errors"] += 1
                    return "Sorry, I couldn't generate a response."
                
                # Cache the response
                if use_cache:
                    self._cache_response(cache_key, content, cache_ttl)
                
                return content
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Sarvam API Error: {e}", exc_info=True)
            return "Sorry, I encountered an error while generating a response."

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        cache_hit_rate = (
            self.stats["cache_hits"] / 
            (self.stats["cache_hits"] + self.stats["cache_misses"])
            if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
            else 0
        )
        
        return {
            **self.stats,
            "cache_size": len(self.response_cache),
            "cache_hit_rate": f"{cache_hit_rate * 100:.2f}%",
            "thinking_mode": self.thinking_mode.value,
        }

    def set_thinking_mode(self, mode: ThinkingMode) -> None:
        """Set global thinking mode"""
        self.thinking_mode = mode
        logger.info(f"Thinking mode set to: {mode.value}")

    def clear_cache(self) -> None:
        """Clear response cache"""
        self.response_cache.clear()
        logger.info("Response cache cleared")
