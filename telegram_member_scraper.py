import asyncio
import os
import platform
import sys
import time
import aiosqlite

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import (FloodWaitError, UserPrivacyRestrictedError,
                             PeerFloodError, SessionPasswordNeededError,
                             UserIdInvalidError)

from config import ACCOUNTS

DATABASE_FILE = "db/added_members.db"  # Path to the SQLite database
INITIAL_DELAY = 20  # Initial delay in seconds
DELAY_BETWEEN_ADDS = 20  # Delay between adds for a single client
DELAY_BETWEEN_CONCURRENT = 1  # Small delay between concurrent adds (in seconds)


def password_input(prompt='Password: '):
    """Cross-platform password input with asterisks."""
    if platform.system() == 'Windows':
        import msvcrt
        print(prompt, end='', flush=True)
        buf = []
        while True:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):  # Enter
                print('')
                return ''.join(buf)
            elif ch == '\b':  # Backspace
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


def parse_group_identifier(identifier):
    """Parses group identifier (username or chat ID)."""
    if identifier.startswith('@') or identifier.startswith('https://t.me/'):
        return identifier  # Let get_entity handle usernames
    try:
        chat_id = int(identifier)
        if chat_id >= 0:
            raise ValueError("Chat ID must be negative.")
        return chat_id
    except ValueError:
        raise ValueError("Invalid group identifier. Use @username or a negative integer chat ID.")


def parse_member_selection(selection_str, max_members):
    """Parses member selection string (individual numbers and ranges)."""
    selected = set()
    parts = selection_str.replace(' ', '').split(',')

    for part in parts:
        if '-' in part:  # Handle range
            try:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= end <= max_members):
                    raise ValueError
                selected.update(range(start, end + 1))
            except ValueError:
                print(f"Invalid range: {part}.  Must be within 1-{max_members}.")
        else:  # Handle individual number
            try:
                num = int(part)
                if not (1 <= num <= max_members):
                    raise ValueError
                selected.add(num)
            except ValueError:
                print(f"Invalid number: {part}. Must be within 1-{max_members}.")

    return sorted(list(selected))


async def add_member_to_db(db, member_id):
    """Adds a member ID to the database (handles duplicates)."""
    try:
        await db.execute("INSERT INTO added_members (member_id) VALUES (?)", (member_id,))
        await db.commit()
    except aiosqlite.IntegrityError:
        pass  # Ignore duplicate entries


async def check_if_member_added(db, member_id):
    """Checks if a member ID exists in the database."""
    async with db.execute("SELECT 1 FROM added_members WHERE member_id = ?", (member_id,)) as cursor:
        return await cursor.fetchone() is not None


async def add_members_with_client(client, target_group_id, members_to_add, db):
    """Adds members using a single client, handling errors."""
    for member in members_to_add:
        if await check_if_member_added(db, member['id']):
            continue  # Skip if already added

        try:
            user_to_add = await client.get_entity(member['username'])
            await client(InviteToChannelRequest(target_group_id, [user_to_add]))
            await add_member_to_db(db, member['id'])
            successful_adds += 1
            progress = (successful_adds / total_members) * 100
            print(f"✓ Added {member['username']} using {client.session.filename} ({successful_adds}/{total_members} - {progress:.1f}%)")
            await asyncio.sleep(DELAY_BETWEEN_ADDS)  # Delay after success
        except UserPrivacyRestrictedError:
            print(f"× Privacy restricted: {member['username']}")
        except UserIdInvalidError:
            print(f"x Invalid user ID: {member['username']}")
        except (FloodWaitError, PeerFloodError) as e:
            wait_time = e.seconds if isinstance(e, FloodWaitError) else 600
            print(f"! Flood wait ({client.session.filename}): {wait_time} seconds")
            return wait_time  # Return wait time
        except Exception as e:
            print(f"× Error ({client.session.filename}): {str(e)}")
    return 0  # Return 0 if no FloodWait


async def main():
    """Main function to scrape and add members."""
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)  # Ensure db directory exists

    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS added_members (member_id INTEGER PRIMARY KEY)")
        await db.commit()

        clients = []
        for account in ACCOUNTS:
            client = TelegramClient(f"session_{account['PHONE']}", account['API_ID'], account['API_HASH'])
            await client.connect()

            if not await client.is_user_authorized():
                phone = account['PHONE']
                print(f"Authorizing {phone}...")
                await client.send_code_request(phone)
                code = password_input(f"Enter code for {phone}: ")
                try:
                    await client.sign_in(phone, code=code)
                except SessionPasswordNeededError:
                    password = password_input(f"Enter 2FA password for {phone}: ")
                    await client.sign_in(password=password)
            clients.append(client)

        # Input: Source and Target Groups
        print("\nEnter group usernames (e.g., @mygroup) or IDs (e.g., -1001234567890).")
        while True:
            source_group_input = input("Enter source group: ").replace('https://t.me/', '')
            try:
                source_group_entity = await client.get_entity(parse_group_identifier(source_group_input))
                source_group_id = source_group_entity.id
                print(f"Source group: {source_group_entity.title} (ID: {source_group_id})")
                break
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Error getting source group: {e}")
                sys.exit(1)

        while True:
            target_group_input = input("Enter target group: ").replace('https://t.me/', '')
            try:
                target_group_entity = await client.get_entity(parse_group_identifier(target_group_input))
                target_group_id = target_group_entity.id
                print(f"Target group: {target_group_entity.title} (ID: {target_group_id})")
                break
            except ValueError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Error getting target group: {e}")
                sys.exit(1)

        # Scrape Members
        print("\nScraping members...")
        members = []
        async for user in client.iter_participants(source_group_entity):
            if user.bot or not user.username:
                continue
            members.append({
                'username': user.username,
                'id': user.id,
                'name': f"{user.first_name} {user.last_name or ''}"
            })

        # Member Selection
        print("\nScraped Members:")
        for i, member in enumerate(members):
            print(f"{i + 1}. {member['name']} (@{member['username']})")

        print("\nEnter members to add (e.g., 1,3,5 / 1-5 / 1-5,8,11-13):")
        while True:
            selection = input("Selection: ")
            selected_indices = parse_member_selection(selection, len(members))
            if selected_indices:
                break
            print("No valid members selected. Try again.")

        selected_members = [members[i - 1] for i in selected_indices]

        # Add Members (Concurrent)
        print("\nAdding members...")
        print(f"Waiting for an initial delay of {INITIAL_DELAY} seconds...")
        await asyncio.sleep(INITIAL_DELAY)

        wait_until = {client.session.filename: 0 for client in clients}
        members_per_batch = len(clients)  # Dynamic batch size

        total_members = len(selected_members)
        successful_adds = 0

        while selected_members:
            tasks = []
            now = time.time()

            for i, client in enumerate(clients):
                if now >= wait_until[client.session.filename]:
                    # Each client gets one member
                    if i < len(selected_members):
                        members_to_add = [selected_members[i]]
                        tasks.append(
                            asyncio.create_task(
                                add_members_with_client(client, target_group_id, members_to_add, db)
                            )
                        )
                        await asyncio.sleep(DELAY_BETWEEN_CONCURRENT)  # Small delay
                        wait_until[client.session.filename] = now + DELAY_BETWEEN_ADDS

            results = await asyncio.gather(*tasks)

            for client, wait_time in zip(clients, results):
                if wait_time > 0:
                    wait_until[client.session.filename] = now + wait_time

            selected_members = selected_members[len(tasks):]

        print("\nFinished adding members.")

        # Cleanup
        await db.close()
        for client in clients:
            await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())