import discord
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class ActionLogger:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent / "logs"
        self.root_dir.mkdir(exist_ok=True)

    def _get_log_file(self, guild_id: str) -> Path:
        return self.root_dir / f"{guild_id}_actions.json"

    def _load_logs(self, guild_id: str) -> List[Dict[str, Any]]:
        log_file = self._get_log_file(guild_id)
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                return logs
            except json.JSONDecodeError:
                return []
        return []

    def _save_logs(self, guild_id: str, logs: List[Dict[str, Any]]) -> None:
        log_file = self._get_log_file(guild_id)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def log_action(self, guild_id: str, action_type: str, details: str, target_id: str = None) -> None:
        """Log an action with timestamp"""
        logs = self._load_logs(guild_id)
        
        # Add new log
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details,
            "target_id": target_id
        })
        
        # Remove logs older than 24 hours
        current_time = datetime.now()
        logs = [
            log for log in logs 
            if current_time - datetime.fromisoformat(log["timestamp"]) < timedelta(hours=24)
        ]
        
        self._save_logs(guild_id, logs)

    async def send_log_embed(self, channel: discord.TextChannel, action_type: str, 
                           details: str, target_id: str = None) -> None:
        """Send a log message to the specified channel and save it"""
        embed = discord.Embed(
            title=f"🔍 {action_type}",
            description=details,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if target_id:
            embed.add_field(name="Target ID", value=target_id, inline=False)
            
        embed.set_footer(text="This log will be archived after 24 hours")
        
        await channel.send(embed=embed)
        self.log_action(str(channel.guild.id), action_type, details, target_id)