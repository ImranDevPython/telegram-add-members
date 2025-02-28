from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantRequest
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError, PeerFloodError, SessionPasswordNeededError
import time
import sys
import platform

def password_input(prompt='Password: '):
    """Cross-platform password input with asterisks"""
    if platform.system() == 'Windows':
        import msvcrt
        print(prompt, end='', flush=True)
        buf = []
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):  # Enter pressed
                print('')
                return ''.join(buf)
            elif ch == '\b':  # Backspace pressed
                if buf:
                    buf.pop()
                    sys.stdout.write('\b \b')  # Erase asterisk
                    sys.stdout.flush()
            elif ch == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                buf.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
    else:
        import termios
        import tty
        print(prompt, end='', flush=True)
        buf = []
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ('\r', '\n'):  # Enter
                    print('')
                    return ''.join(buf)
                elif ch == '\x7f':  # Backspace
                    if buf:
                        buf.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ch == '\x03':  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    buf.append(ch)
                    sys.stdout.write('*')
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def validate_config():
    """Validate the configuration values from config.py"""
    try:
        from config import API_ID, API_HASH, PHONE
    except ImportError:
        print("\nError: config.py not found!")
        print("Make sure config.py exists in the same directory as this script")
        sys.exit(1)

    errors = []
    
    # Validate API_ID
    if not API_ID:
        errors.append("API_ID is empty")
    else:
        try:
            int(API_ID)
        except ValueError:
            errors.append("API_ID should only contain numbers")
    
    # Validate API_HASH
    if not API_HASH:
        errors.append("API_HASH is empty")
    elif len(API_HASH) < 32:
        errors.append("API_HASH seems invalid (too short)")
    
    # Validate PHONE
    if not PHONE:
        errors.append("PHONE is empty")
    elif not (PHONE.startswith('+') and PHONE[1:].replace(' ', '').isdigit()):
        errors.append("PHONE should start with '+' followed by country code and number")

    if errors:
        print("\nConfiguration Error(s):")
        for error in errors:
            print(f"❌ {error}")
        print("\nPlease follow these steps:")
        print("1. Open config.py in a text editor")
        print("2. Get your API credentials from https://my.telegram.org/apps")
        print("3. Fill in proper values")
        sys.exit(1)

    return API_ID, API_HASH, PHONE

API_ID, API_HASH, PHONE = validate_config()

def parse_member_selection(selection_str, max_members):
    """Parse member selection string that supports both individual numbers and ranges."""
    selected = set()
    parts = selection_str.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            # Handle range (e.g., "1-5")
            try:
                start, end = map(int, part.split('-'))
                if start < 1 or end > max_members:
                    print(f"Invalid range {start}-{end}. Valid range is 1-{max_members}")
                    continue
                selected.update(range(start, end + 1))
            except ValueError:
                print(f"Invalid range format: {part}")
        else:
            # Handle individual number
            try:
                num = int(part)
                if 1 <= num <= max_members:
                    selected.add(num)
                else:
                    print(f"Invalid number {num}. Valid range is 1-{max_members}")
            except ValueError:
                print(f"Invalid number: {part}")
    
    return sorted(list(selected))

async def main():
    client = TelegramClient('session_name', API_ID, API_HASH)
    
    # Connect without starting the default interactive flow
    await client.connect()
    
    if not await client.is_user_authorized():
        # Use your own phone number from config
        phone = PHONE
        print(f"Using phone number from config: {phone}")
        
        # Send code request
        await client.send_code_request(phone)
        
        # Use custom code input with asterisks
        verification_code = password_input("Enter the code you received(in Telegram): ")
        
        try:
            # Sign in with code
            await client.sign_in(phone, code=verification_code)
        except SessionPasswordNeededError:
            # Handle 2FA password with asterisks
            password = password_input("Enter your 2FA password: ")
            await client.sign_in(password=password)
    

    try:
        # Original group handling logic remains unchanged
        print("\nFor group usernames, enter without 'https://t.me/'")
        source_group = input("\nEnter source group username(to scrape): ").replace('https://t.me/', '')
        target_group = input("\nEnter target group username: (to add)").replace('https://t.me/', '')

        print("\nScraping members...")
        source_group_entity = await client.get_entity(source_group)
        members = []
        
        async for user in client.iter_participants(source_group_entity):
            if not user.bot and user.username:
                members.append({
                    'username': user.username,
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name or ''}"
                })
                print(f"Found member: {user.username}")

        print("\nScraped Members:")
        for i, member in enumerate(members):
            print(f"{i+1}. {member['name']} (@{member['username']})")

        print("\nYou can enter:")
        print("- Individual numbers (e.g., 1,3,5)")
        print("- Ranges (e.g., 1-5)")
        print("- Or combine both (e.g., 1-5,8,11-13)")
        selection = input("\nEnter members to add: ")
        
        selected_indices = parse_member_selection(selection, len(members))
        if not selected_indices:
            print("No valid members selected. Operation cancelled.")
            return
            
        selected_members = [members[i-1] for i in selected_indices]

        print("\nSAFETY LIMITS:")
        print(f"Selected {len(selected_members)} members")
        if len(selected_members) > 35:
            proceed = input("\nWARNING: >35 members might trigger restrictions. Proceed? (y/n): ")
            if proceed.lower() != 'y':
                print("Operation cancelled.")
                return

        print("\nVerifying admin rights...")
        target_entity = await client.get_entity(target_group)
        me = await client.get_me()
        
        try:
            participant = await client(GetParticipantRequest(target_entity, me.id))
            is_admin = hasattr(participant.participant, 'admin_rights')
            can_invite = is_admin and participant.participant.admin_rights.invite_users
            
            if not is_admin or not can_invite:
                print("\nERROR: No permission to add members!")
                return
                
            print("\nAdding members...")
            successful_adds = 0
            privacy_restricted = 0
            other_errors = 0
            
            # Initial delay before adding members
            initial_delay = 20  # seconds
            print(f"Waiting for an initial delay of {initial_delay} seconds...")
            time.sleep(initial_delay)

            for i, member in enumerate(selected_members, 1):
                try:
                    user_to_add = await client.get_entity(member['username'])
                    await client(InviteToChannelRequest(target_entity, [user_to_add]))
                    successful_adds += 1
                    print(f"✓ Added {member['username']} ({i}/{len(selected_members)})")

                    delay = 20 # Increased delay
                    print(f"Waiting {delay} seconds...")
                    time.sleep(delay)

                except UserPrivacyRestrictedError:
                    privacy_restricted += 1
                    print(f"× Privacy restricted: {member['username']}")
                except (FloodWaitError, PeerFloodError) as e:
                    wait_time = e.seconds if isinstance(e, FloodWaitError) else 600  # Keep 600 as default for PeerFloodError
                    print(f"! Flood wait: {wait_time} seconds")
                    for remaining in range(wait_time, 0, -1):
                        print(f"Time remaining: {remaining//60:02d}:{remaining%60:02d}", end='\r')
                        time.sleep(1)
                    print("\nResuming...")
                    selected_members.insert(i, member)  # Re-insert at the current position
                except Exception as e:
                    other_errors += 1
                    print(f"× Error: {str(e)}")

            print(f"\nResults:")
            print(f"✓ Success: {successful_adds}")
            print(f"× Privacy blocks: {privacy_restricted}")
            print(f"× Other errors: {other_errors}")

        except Exception as e:
            print(f"\nPermissions error: {str(e)}")

    except Exception as e:
        print(f"General error: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())