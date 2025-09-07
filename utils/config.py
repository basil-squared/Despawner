import json
import os
from pathlib import Path
from typing import Dict, Any

DEFAULT_CONFIG = {
    "keyword_ban_behavior": "auto",  # auto, notify, ignore
    "id_ban_behavior": "auto",       # auto, notify, ignore
    "dm_on_ban": True,              # whether to send DMs to banned users
    "log_bans": True,               # whether to log bans in channel
    "notify_staff": True            # whether to notify staff of matches
}

class ConfigManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.CONFIG_FILE = self.root_dir / "guild_configs.json"
        self.configs = self._load_configs()

    def _load_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load configs from file or create new if missing"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    loaded_configs = json.load(f)
                    for guild_id in list(loaded_configs.keys()):
                        self._validate_guild_config(loaded_configs, guild_id)
                    return loaded_configs
            else:
                print(f"Creating new config file at {self.CONFIG_FILE}")
                empty_config = {}
                self._save_configs(empty_config)  # Pass empty dict
                return empty_config
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error loading config file: {e}. Creating new config.")
            empty_config = {}
            self._save_configs(empty_config)  # Pass empty dict
            return empty_config

    def _validate_guild_config(self, configs: Dict[str, Dict[str, Any]], guild_id: str) -> None:
        """Ensure all default settings exist in guild config"""
        if guild_id not in configs:
            configs[guild_id] = DEFAULT_CONFIG.copy()
        else:
            # Add any missing default settings
            for key, default_value in DEFAULT_CONFIG.items():
                if key not in configs[guild_id]:
                    configs[guild_id][key] = default_value
            
            # Remove any invalid settings
            invalid_keys = [k for k in configs[guild_id] if k not in DEFAULT_CONFIG]
            for k in invalid_keys:
                del configs[guild_id][k]

    def _save_configs(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """Save configs to file with error handling"""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(configs, f, indent=2)
            self.configs = configs
        except (IOError, OSError) as e:
            print(f"Error saving config file: {e}")
            raise

    def get_guild_config(self, guild_id: str) -> Dict[str, Any]:
        """Get guild config, creating default if needed"""
        guild_id = str(guild_id)  # Ensure guild_id is string
        self._validate_guild_config(self.configs, guild_id)
        return self.configs[guild_id]

    def update_guild_config(self, guild_id: str, setting: str, value: Any) -> bool:
        """Update guild config with validation"""
        guild_id = str(guild_id)
        
        # Validate setting exists in DEFAULT_CONFIG
        if setting not in DEFAULT_CONFIG:
            return False
        
        # Validate value type matches default
        default_type = type(DEFAULT_CONFIG[setting])
        if not isinstance(value, default_type):
            try:
                # Attempt type conversion
                value = default_type(value)
            except (ValueError, TypeError):
                return False

        # Special validation for enum-like settings
        if setting in ['keyword_ban_behavior', 'id_ban_behavior']:
            if value not in ['auto', 'notify', 'ignore']:
                return False

        # Update config
        self._validate_guild_config(self.configs, guild_id)
        self.configs[guild_id][setting] = value
        self._save_configs(self.configs)
        return True