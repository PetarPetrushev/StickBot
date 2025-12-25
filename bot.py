import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import sys
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'sticky_data.json'

# Data structure for storing sticky messages
# {
#   "channel_id": {
#     "message": "sticky message text",
#     "msg_limit": 10,
#     "message_count": 0,
#     "last_message_id": null
#   }
# }

class StickyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        super().__init__(command_prefix='!', intents=intents)
        self.sticky_data: Dict = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Load saved data
        self.load_data()
        # Sync commands with Discord
        await self.tree.sync()
        print(f"Commands synced!")
    
    def load_data(self):
        """Load sticky message data from file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert string keys to int
                    self.sticky_data = {int(k): v for k, v in data.items()}
                print(f"Loaded data for {len(self.sticky_data)} channels")
            except Exception as e:
                print(f"Error loading data: {e}")
                self.sticky_data = {}
        else:
            self.sticky_data = {}
    
    def save_data(self):
        """Save sticky message data to file"""
        try:
            # Convert int keys to string for JSON
            data = {str(k): v for k, v in self.sticky_data.items()}
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved data for {len(self.sticky_data)} channels")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands first
        await self.process_commands(message)
        
        channel_id = message.channel.id
        
        # Check if this channel has a sticky message
        if channel_id in self.sticky_data:
            channel_data = self.sticky_data[channel_id]
            
            # Increment message count
            channel_data['message_count'] += 1
            
            # Check if we need to repost the sticky message
            if channel_data['message_count'] >= channel_data['msg_limit']:
                # Delete old sticky message if it exists
                if channel_data['last_message_id'] is not None:
                    try:
                        old_message = await message.channel.fetch_message(channel_data['last_message_id'])
                        await old_message.delete()
                    except discord.NotFound:
                        pass  # Message already deleted
                    except Exception as e:
                        print(f"Error deleting old message: {e}")
                
                # Send new sticky message
                try:
                    new_message = await message.channel.send(channel_data['message'])
                    channel_data['last_message_id'] = new_message.id
                    channel_data['message_count'] = 0
                    self.save_data()
                except Exception as e:
                    print(f"Error sending sticky message: {e}")

# Create bot instance
bot = StickyBot()

@bot.tree.command(name="stick", description="Set a sticky message for this channel")
@app_commands.describe(message="The message to stick in this channel")
async def stick(interaction: discord.Interaction, message: str):
    """Set a sticky message for the channel"""
    channel_id = interaction.channel_id
    
    # Initialize channel data if it doesn't exist
    if channel_id not in bot.sticky_data:
        bot.sticky_data[channel_id] = {
            'message': message,
            'msg_limit': 10,  # Default limit
            'message_count': 0,
            'last_message_id': None
        }
    else:
        # Update existing message
        bot.sticky_data[channel_id]['message'] = message
        bot.sticky_data[channel_id]['message_count'] = 0
    
    # Save data
    bot.save_data()
    
    # Send confirmation
    await interaction.response.send_message(
        f"✅ Sticky message set! It will be reposted every {bot.sticky_data[channel_id]['msg_limit']} messages.\n"
        f"Message: {message}",
        ephemeral=True
    )
    
    # Post the sticky message immediately
    try:
        sticky_msg = await interaction.channel.send(message)
        bot.sticky_data[channel_id]['last_message_id'] = sticky_msg.id
        bot.save_data()
    except Exception as e:
        print(f"Error posting initial sticky message: {e}")

@bot.tree.command(name="unstick", description="Remove the sticky message from this channel")
async def unstick(interaction: discord.Interaction):
    """Remove sticky message from the channel"""
    channel_id = interaction.channel_id
    
    if channel_id not in bot.sticky_data:
        await interaction.response.send_message(
            "❌ There is no sticky message set in this channel.",
            ephemeral=True
        )
        return
    
    # Delete the last sticky message if it exists
    if bot.sticky_data[channel_id]['last_message_id'] is not None:
        try:
            message = await interaction.channel.fetch_message(
                bot.sticky_data[channel_id]['last_message_id']
            )
            await message.delete()
        except discord.NotFound:
            pass  # Message already deleted
        except Exception as e:
            print(f"Error deleting sticky message: {e}")
    
    # Remove from data
    del bot.sticky_data[channel_id]
    bot.save_data()
    
    await interaction.response.send_message(
        "✅ Sticky message removed from this channel.",
        ephemeral=True
    )

@bot.tree.command(name="msglimit", description="Set how many messages before the sticky message reposts")
@app_commands.describe(limit="Number of messages before reposting (minimum 1)")
async def msglimit(interaction: discord.Interaction, limit: int):
    """Set the message limit for sticky message reposting"""
    channel_id = interaction.channel_id
    
    # Validate limit
    if limit < 1:
        await interaction.response.send_message(
            "❌ Message limit must be at least 1.",
            ephemeral=True
        )
        return
    
    # Check if channel has a sticky message
    if channel_id not in bot.sticky_data:
        await interaction.response.send_message(
            "❌ No sticky message is set in this channel. Use `/stick` first.",
            ephemeral=True
        )
        return
    
    # Update limit
    bot.sticky_data[channel_id]['msg_limit'] = limit
    bot.sticky_data[channel_id]['message_count'] = 0  # Reset counter
    bot.save_data()
    
    await interaction.response.send_message(
        f"✅ Message limit updated to {limit} messages.",
        ephemeral=True
    )

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        sys.exit(1)
    
    bot.run(TOKEN)
