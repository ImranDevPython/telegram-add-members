from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerChannel
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError
import time
import os
from typing import List
from telethon.tl.types import ChatAdminRights
from telethon.tl.functions.channels import GetParticipantRequest

# Replace these with your own values from https://my.telegram.org/apps
API_ID = ''
API_HASH = ''
PHONE = ''  # Include country code

async def main():
    # Connect to Telegram
    client = TelegramClient('session_name', API_ID, API_HASH)
    await client.start()
    
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        await client.sign_in(PHONE, input('Enter the code: '))

    try:
        # First get source and target groups
        print("\nFor group usernames, enter without 'https://t.me/'")
        print("Example: if group link is 'https://t.me/MyGroup', just enter 'MyGroup'")
        
        source_group = input("\nEnter the source group username (where to get members from): ")
        if source_group.startswith('https://t.me/'):
            source_group = source_group.replace('https://t.me/', '')
        
        target_group = input("\nEnter your admin group username (where to add members to): ")
        if target_group.startswith('https://t.me/'):
            target_group = target_group.replace('https://t.me/', '')

        # First scrape members
        print("\nScraping members...")
        source_group_entity = await client.get_entity(source_group)
        members = []
        
        async for user in client.iter_participants(source_group_entity):
            if not user.bot and user.username:  # Skip bots and users without username
                members.append({
                    'username': user.username,
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name if user.last_name else ''}"
                })
                print(f"Found member: {user.username}")

        # Display members and get selection
        print("\nScraped Members:")
        for i, member in enumerate(members):
            print(f"{i+1}. {member['name']} (@{member['username']})")

        # Get user selection
        selected_indices = input("\nEnter the numbers of members to add (comma-separated): ").split(',')
        selected_members = [members[int(i.strip())-1] for i in selected_indices]

        # Add safety warning
        print("\nSAFETY LIMITS:")
        print("- Maximum recommended: 50-100 members per day")
        print("- Maximum 35 members per hour")
        print(f"You have selected {len(selected_members)} members")
        
        if len(selected_members) > 35:
            proceed = input("\nWARNING: You have selected more than 35 members. This might trigger restrictions.\nDo you want to proceed? (y/n): ")
            if proceed.lower() != 'y':
                print("Operation cancelled.")
                return

        # Then verify admin rights
        print("\nVerifying admin rights...")
        target_entity = await client.get_entity(target_group)
        me = await client.get_me()
        
        try:
            participant = await client(GetParticipantRequest(
                channel=target_entity,
                participant=me.id
            ))
            
            is_admin = hasattr(participant.participant, 'admin_rights')
            can_invite = (is_admin and 
                         hasattr(participant.participant.admin_rights, 'invite_users') and 
                         participant.participant.admin_rights.invite_users)
            
            if not is_admin or not can_invite:
                print("\nERROR: You don't have permission to add members!")
                return
                
            print("\nAdding members...")
            
            successful_adds = 0
            privacy_restricted = 0
            other_errors = 0
            
            for i, member in enumerate(selected_members, 1):
                try:
                    user_to_add = await client.get_entity(member['username'])
                    await client(InviteToChannelRequest(
                        target_entity,
                        [user_to_add]
                    ))
                    successful_adds += 1
                    print(f"✓ Added {member['username']} ({i}/{len(selected_members)})")
                    
                    # Increase delay between adds to 30-60 seconds
                    delay = 10
                    print(f"Waiting {delay} seconds before next add...")
                    time.sleep(delay)
                    
                except UserPrivacyRestrictedError:
                    privacy_restricted += 1
                    print(f"× Couldn't add {member['username']} - privacy settings")
                except (FloodWaitError, PeerFloodError) as e:
                    if isinstance(e, FloodWaitError):
                        wait_time = e.seconds
                        print(f"! Hit flood limit. Waiting {wait_time} seconds...")
                    else:
                        # For PeerFloodError, take a longer break (10 minutes)
                        wait_time = 600
                        print("\n! Too many requests - Taking a 10 minute break...")
                    
                    # Countdown for either error
                    for remaining in range(wait_time, 0, -1):
                        minutes, seconds = divmod(remaining, 60)
                        print(f"Time remaining: {minutes:02d}:{seconds:02d}", end='\r')
                        time.sleep(1)
                    print("\nWait finished, continuing...         ")
                except Exception as e:
                    other_errors += 1
                    print(f"× Error adding {member['username']}: {str(e)}")
                    continue

            print(f"\nResults:")
            print(f"✓ Successfully added: {successful_adds}")
            print(f"× Privacy restricted: {privacy_restricted}")
            print(f"× Other errors: {other_errors}")

        except Exception as e:
            print(f"\nError checking permissions: {str(e)}")
            return

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        await client.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 