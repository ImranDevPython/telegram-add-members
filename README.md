# Telegram Add Members Project

## Description
This project is a Telegram member scraper and adder. It allows you to scrape members from a source Telegram group and add them to a target group where you have administrative rights. The script is built using the Telethon library, which is a Python wrapper around the Telegram API.

## Features
- Scrape members from a source Telegram group.
- Add selected members to a target Telegram group.
- Safety checks to prevent adding too many members at once and triggering Telegram's anti-spam restrictions.

## Prerequisites
- Python 3.7+
- Telethon library
- A Telegram account
- Admin rights in the target group to add members

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/ImranDevJourneyYoutube/telegram-add-members.git
   ```
2. Navigate to the project directory:
   ```bash
   cd telegram_add_members
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Replace the `API_ID`, `API_HASH`, and `PHONE` in `telegram_member_scraper.py` with your own credentials from [my.telegram.org](https://my.telegram.org/apps).

## Usage
1. Run the script:
   ```bash
   python telegram_member_scraper.py
   ```
2. Follow the on-screen instructions to enter the source and target group usernames.
3. Select the members you wish to add.
4. Confirm the operation and monitor the progress.

## Safety Guidelines
- It is recommended to add no more than 50 members per day and no more than 35 members per hour to avoid triggering Telegram's restrictions.
- Ensure you have the necessary permissions in the target group to add members.

## Troubleshooting
- If you encounter a `FloodWaitError` or `PeerFloodError`, the script will automatically handle the waiting period before continuing.
- Ensure your account is not restricted by Telegram for previous violations.

## Disclaimer
Use this script responsibly and in compliance with Telegram's terms of service. The author is not responsible for any misuse or violations of Telegram's policies.
