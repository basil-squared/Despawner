import discord
from typing import Optional

class ErrorHandler:
    @staticmethod
    async def send_error(interaction: discord.Interaction, 
                        title: str, 
                        description: str, 
                        error_type: Optional[str] = None,
                        show_help: bool = False) -> None:
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red()
        )
        
        if error_type:
            embed.add_field(
                name="Error Type",
                value=f"`{error_type}`",
                inline=False
            )
            
        if show_help:
            embed.add_field(
                name="Need Help?",
                value="Contact a server administrator if this issue persists.",
                inline=False
            )
            
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            if hasattr(interaction, 'channel'):
                await interaction.channel.send(embed=embed, delete_after=30)