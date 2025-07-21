#!/usr/bin/env python3
"""
Test bot connection and find Chat ID
"""

import asyncio
import aiohttp

BOT_TOKEN = "7822484786:AAGkay-nm4CCIJizx7PAG58sp2ttiE46Q20"

async def test_bot():
    """Test bot and get chat info."""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test bot info
            async with session.get(f"{base_url}/getMe") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"Bot Name: {bot_info.get('first_name')}")
                        print(f"Bot Username: @{bot_info.get('username')}")
                        print(f"Bot ID: {bot_info.get('id')}")
                        print()
                        
                        # Show direct link to bot
                        username = bot_info.get('username')
                        if username:
                            print(f"Direct link to your bot: https://t.me/{username}")
                            print()
                    else:
                        print("Bot token is invalid!")
                        return
                else:
                    print(f"Error testing bot: {response.status}")
                    return
            
            # Get updates
            async with session.get(f"{base_url}/getUpdates") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        updates = data.get('result', [])
                        if updates:
                            print("Found messages:")
                            for update in updates:
                                if 'message' in update:
                                    msg = update['message']
                                    chat = msg.get('chat', {})
                                    user = msg.get('from', {})
                                    
                                    print(f"Chat ID: {chat.get('id')}")
                                    print(f"User: {user.get('first_name', '')} {user.get('last_name', '')}")
                                    print(f"Message: {msg.get('text', '')}")
                                    print("---")
                            
                            # Get the latest chat ID
                            latest_chat_id = updates[-1]['message']['chat']['id']
                            print(f"Your Chat ID: {latest_chat_id}")
                        else:
                            print("No messages found yet.")
                            print("Please:")
                            print("1. Go to the bot link above")
                            print("2. Send any message (like 'hello')")
                            print("3. Run this script again")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())