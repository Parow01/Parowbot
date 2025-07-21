#!/usr/bin/env python3
"""
Helper script to get your Telegram Chat ID
Run this after sending a message to your bot
"""

import asyncio
import aiohttp
import json

BOT_TOKEN = "7822484786:AAGkay-nm4CCIJizx7PAG58sp2ttiE46Q20"

async def get_chat_id():
    """Get the chat ID from recent messages to the bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('ok') and data.get('result'):
                        print("Recent messages to your bot:")
                        print("-" * 50)
                        
                        for update in data['result']:
                            if 'message' in update:
                                message = update['message']
                                chat = message.get('chat', {})
                                from_user = message.get('from', {})
                                text = message.get('text', '')
                                
                                print(f"Chat ID: {chat.get('id')}")
                                print(f"Chat Type: {chat.get('type')}")
                                print(f"User: {from_user.get('first_name', '')} {from_user.get('last_name', '')}")
                                print(f"Username: @{from_user.get('username', 'N/A')}")
                                print(f"Message: {text}")
                                print("-" * 30)
                        
                        if data['result']:
                            chat_id = data['result'][-1]['message']['chat']['id']
                            print(f"\nYour Chat ID is: {chat_id}")
                            print(f"Use this value for TELEGRAM_CHAT_ID")
                        else:
                            print("No messages found. Please send a message to your bot first!")
                    else:
                        print("No updates found. Make sure you've sent a message to your bot!")
                else:
                    print(f"Error: HTTP {response.status}")
                    print(await response.text())
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Getting your Telegram Chat ID...")
    print("Make sure you've sent at least one message to your bot first!")
    print()
    asyncio.run(get_chat_id())