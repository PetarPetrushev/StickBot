# StickBot
A discord StickyBot type bot which allows you to set up a sticky message to auto send after X amount of messages.

## Features

- **Sticky Messages**: Set a message that automatically reposts after a configurable number of messages
- **Per-Channel Configuration**: Each channel can have its own sticky message and message limit
- **Persistent Storage**: Configuration is saved and loaded automatically
- **Slash Commands**: Easy-to-use Discord slash commands

## Commands

- `/stick <message>` - Set a sticky message for the current channel (max 1 per channel)
- `/unstick` - Remove the sticky message from the current channel
- `/msglimit <num>` - Configure how many messages can be sent before the bot reposts the sticky message

## Setup

### Prerequisites

- Python 3.8 or higher
- A Discord bot token (get one from [Discord Developer Portal](https://discord.com/developers/applications))

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/PetarPetrushev/StickBot.git
   cd StickBot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## Bot Permissions

Your bot needs the following permissions:
- Read Messages/View Channels
- Send Messages
- Manage Messages (to delete old sticky messages)
- Use Slash Commands

## How It Works

1. Use `/stick` to set a sticky message in a channel
2. The bot posts the message immediately
3. After users send the configured number of messages (default: 10), the bot deletes the old sticky message and reposts it
4. Use `/msglimit` to change how many messages trigger a repost
5. Use `/unstick` to remove the sticky message from a channel

All configuration is automatically saved to `sticky_data.json` and loaded when the bot restarts. 
