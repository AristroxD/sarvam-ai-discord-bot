import json
import os

MEMORY_FILE = "chat_channel_memory.json"

class ChatChannelMemory:
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                print("[ChatChannelMemory] Failed to load memory file.")
                self.data = {}
        else:
            self.data = {}

    def save(self):
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            print("[ChatChannelMemory] Failed to save memory file.")

    def set_channel(self, guild_id: int, channel_id: int):
        self.data[str(guild_id)] = channel_id
        self.save()

    def get_channel(self, guild_id: int):
        return self.data.get(str(guild_id))

    def remove_channel(self, guild_id: int):
        if str(guild_id) in self.data:
            del self.data[str(guild_id)]
            self.save()

    def all_channels(self):
        """Return all guild_id: channel_id pairs in memory."""
        return self.data.copy()

    def is_channel_allowed(self, channel_id: int) -> bool:
        """Check if a channel is in the memory-enabled list."""
        return str(channel_id) in self.data.values() or channel_id in self.data.values()