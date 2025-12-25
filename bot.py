import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import sys
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'sticky_data.json'

class StickyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        super().__init__(command_prefix='!', intents=intents)
        self.sticky_data: Dict = {}
        
    async def setup_hook(self):
        self.load_data()
        await self.tree.sync()
        print(f"Commands synced!")
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.sticky_data = {int(k): v for k, v in data.items()}
                print(f"Loaded data for {len(self.sticky_data)} channels")
            except Exception as e:
                print(f"Error loading data: {e}")
                self.sticky_data = {}
        else:
            self.sticky_data = {}
    
    def save_data(self):
        try:
            data = {str(k): v for k, v in self.sticky_data.items()}
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved data for {len(self.sticky_data)} channels")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
    
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        await self.process_commands(message)
        
        channel_id = message.channel.id
        
        if channel_id in self.sticky_data:
            channel_data = self.sticky_data[channel_id]
            channel_data['message_count'] += 1
            
            if channel_data['message_count'] >= channel_data['msg_limit']:
                if channel_data['last_message_id'] is not None:
                    try:
                        old_message = await message.channel.fetch_message(channel_data['last_message_id'])
                        await old_message.delete()
                    except discord.NotFound:
                        pass
                    except Exception as e:
                        print(f"Error deleting old message: {e}")
                
                try:
                    new_message = await message.channel.send(channel_data['message'])
                    channel_data['last_message_id'] = new_message.id
                    channel_data['message_count'] = 0
                    self.save_data()
                except Exception as e:
                    print(f"Error sending sticky message: {e}")

bot = StickyBot()

@bot.tree.command(name="stick", description="Set a sticky message for this channel")
@app_commands.describe(message="The message to stick in this channel")
@app_commands.checks.has_permissions(manage_messages=True)
async def stick(interaction: discord.Interaction, message: str):
    channel_id = interaction.channel_id
    
    if channel_id not in bot.sticky_data:
        bot.sticky_data[channel_id] = {
            'message': message,
            'msg_limit': 10,
            'message_count': 0,
            'last_message_id': None
        }
    else:
        bot.sticky_data[channel_id]['message'] = message
        bot.sticky_data[channel_id]['message_count'] = 0
    
    bot.save_data()
    
    await interaction.response.send_message(
        f"✅ Sticky message set! It will be reposted every {bot.sticky_data[channel_id]['msg_limit']} messages.\n"
        f"Message: {message}",
        ephemeral=True
    )
    
    try:
        sticky_msg = await interaction.channel.send(message)
        bot.sticky_data[channel_id]['last_message_id'] = sticky_msg.id
        bot.save_data()
    except Exception as e:
        print(f"Error posting initial sticky message: {e}")

@bot.tree.command(name="unstick", description="Remove the sticky message from this channel")
@app_commands.checks.has_permissions(manage_messages=True)
async def unstick(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    
    if channel_id not in bot.sticky_data:
        await interaction.response.send_message(
            "❌ There is no sticky message set in this channel.",
            ephemeral=True
        )
        return
    
    if bot.sticky_data[channel_id]['last_message_id'] is not None:
        try:
            message = await interaction.channel.fetch_message(
                bot.sticky_data[channel_id]['last_message_id']
            )
            await message.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"Error deleting sticky message: {e}")
    
    del bot.sticky_data[channel_id]
    bot.save_data()
    
    await interaction.response.send_message(
        "✅ Sticky message removed from this channel.",
        ephemeral=True
    )

@bot.tree.command(name="msglimit", description="Set how many messages before the sticky message reposts")
@app_commands.describe(limit="Number of messages before reposting (minimum 1)")
@app_commands.checks.has_permissions(manage_messages=True)
async def msglimit(interaction: discord.Interaction, limit: int):
    channel_id = interaction.channel_id
    
    if limit < 1:
        await interaction.response.send_message(
            "❌ Message limit must be at least 1.",
            ephemeral=True
        )
        return
    
    if channel_id not in bot.sticky_data:
        await interaction.response.send_message(
            "❌ No sticky message is set in this channel. Use `/stick` first.",
            ephemeral=True
        )
        return
    
    bot.sticky_data[channel_id]['msg_limit'] = limit
    bot.sticky_data[channel_id]['message_count'] = 0
    bot.save_data()
    
    await interaction.response.send_message(
        f"✅ Message limit updated to {limit} messages.",
        ephemeral=True
    )

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "🚫 Sorry! You don't have the `Manage Messages` permission to use this command.",
            ephemeral=True
        )
    else:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        sys.exit(1)
    
    bot.run(TOKEN)
