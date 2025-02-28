# Telegram Member Scraper and Adder (Multi-Account, Concurrent)

**GitHub Repository:** [https://github.com/ImranDevPythoon/telegram-add-members](https://github.com/ImranDevPythoon/telegram-add-members)

## Description

This project provides a Python script to scrape members from a source Telegram group and add them to a target group where you have administrative rights. It leverages multiple Telegram accounts to distribute the workload, uses `asyncio` for concurrent operations, and stores added member IDs in an SQLite database to prevent duplicate additions. This approach significantly improves efficiency and helps avoid Telegram's rate limits.

## Features

*   **Scrape Members:** Extracts members from any Telegram group (public or private, if you are a member).
*   **Add Members:** Adds scraped members to a target group where you have admin privileges (specifically, the "Add Users" permission).
*   **Multi-Account Support:** Uses multiple Telegram accounts to distribute the adding process, reducing the risk of hitting rate limits on any single account.
*   **Concurrency:** Employs `asyncio` to add members concurrently, dramatically speeding up the process compared to single-threaded scripts.
*   **Persistent Storage (SQLite):** Stores the IDs of added members in an SQLite database. This prevents duplicate additions, even if the script is interrupted and restarted.
*   **Rate Limit Handling:** Incorporates several strategies to avoid Telegram's rate limits:
    *   Initial delay before starting the adding process.
    *   Per-account delay between adding attempts.
    *   Small delay between concurrent task creation.
    *   Automatic handling of `FloodWaitError` exceptions (the script will wait the required time).
*   **Flexible Input:** Accepts both group usernames (e.g., `@mygroup`) and chat IDs (e.g., `-1001234567890`) for both source and target groups.
*   **User-Friendly Interface:** Provides clear prompts and informative output, making it easy to use.
*   **Secure Credential Management:** Uses a `.env` file to store sensitive account credentials, keeping them separate from the code and preventing accidental exposure.
*   **Member Selection:** Supports selecting members by individual numbers, ranges, or a combination of both.
* **Error Handling:** Includes robust error handling for various scenarios, such as invalid input, privacy restrictions, and API errors.

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ImranDevPythoon/telegram-add-members.git
    cd telegram-add-members
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate  # Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1.  **Obtain Telegram API Credentials:**
    *   Go to [https://my.telegram.org/apps](https://my.telegram.org/apps) and log in with your Telegram account.
    *   Create a new application (or use an existing one).
    *   Copy the `api_id` (integer) and `api_hash` (string) values.  You'll need these for *each* Telegram account you want to use.

2.  **Create a `.env` File:**
    *   Create a new file named `.env` in the root directory of the project (where `telegram_member_scraper.py` is located).
    *   Add your Telegram account credentials to the `.env` file in the following format:

        ```
        ACCOUNT_1_API_ID=your_api_id_1
        ACCOUNT_1_API_HASH=your_api_hash_1
        ACCOUNT_1_PHONE=+your_phone_number_1
        ACCOUNT_2_API_ID=your_api_id_2
        ACCOUNT_2_API_HASH=your_api_hash_2
        ACCOUNT_2_PHONE=+your_phone_number_2
        # ... add more accounts as needed
        ```

    *   **Replace Placeholders:** Replace `your_api_id_N`, `your_api_hash_N`, and `your_phone_number_N` with your *actual* credentials.
    *   **Format:**  Do *not* include any spaces around the `=` signs.  The `API_ID` must be an integer. Phone numbers *must* include the `+` and country code.
    *   **Security:** *Never* share your `.env` file or commit it to a public repository.  It contains sensitive information.

## Usage

1.  **Run the Script:**
    ```bash
    python telegram_member_scraper.py
    ```

2.  **Follow the Prompts:**
    *   The script will prompt you to enter the source group (username or chat ID).
    *   The script will prompt you to enter the target group (username or chat ID).
    *   The *first* time you run the script for *each* account, you'll need to authorize it:
        *   Enter the verification code sent to your Telegram account.
        *   If you have two-factor authentication (2FA) enabled, enter your 2FA password.
    *   Select members to add using any of these formats:
        *   Individual numbers: `1,3,5`
        *   Ranges: `1-10`
        *   Combined: `1-5,8,11-13`
    *   The script will then scrape members from the source group and add the selected members to the target group. It uses multiple accounts concurrently and handles rate limits automatically.

## Important Notes

*   **Security:** *Never* share your `.env` file, session files (`*.session`), or database file (`*.db`) with anyone. These files contain sensitive information that could be used to compromise your Telegram account(s).
*   **Rate Limits:** Even with multiple accounts and delays, Telegram may still impose rate limits. If you encounter a `FloodWaitError`, the script will automatically wait the required time before retrying. It's generally recommended to add members in smaller batches with longer intervals between batches to minimize the risk of triggering rate limits.
*   **Account Restrictions:** If your accounts repeatedly trigger flood errors or violate Telegram's terms of service, Telegram might impose temporary or permanent restrictions on your accounts. Use this script responsibly and ethically.
*   **Privacy Settings:** Some users have privacy settings that prevent them from being added to groups. The script will report these as "Privacy restricted" and skip those users.
*   **Database:** The script automatically creates and manages the SQLite database. You do not need to interact with the database directly.

## Troubleshooting

*   **`Error: No accounts configured in .env file.`:** Make sure you have created a `.env` file in the correct format and that it contains at least one set of account credentials.
*   **`Error: Invalid API_ID for ACCOUNT_N in .env file. Must be an integer.`:** Double-check that your `API_ID` values in the `.env` file are integers (numbers only, no quotes or spaces).
*   **`FloodWaitError`:** The script will automatically handle this. If you see this frequently, increase the `INITIAL_DELAY` and `DELAY_BETWEEN_ADDS` values in `telegram_member_scraper.py`, or add fewer members per batch.
*   **`UserPrivacyRestrictedError`:** This means the user has privacy settings that prevent you from adding them. There's nothing the script can do about this.
*   **`PeerFloodError`:** This often indicates you're adding members too quickly to a specific group, or adding users who have recently left the group. Increase delays.
*   **`SessionPasswordNeededError`:** You need to enter your 2FA password.
*   **`UserIdInvalidError`:** The user ID is invalid. The script will skip these users.
*   **Other Errors:** If you encounter any other errors, provide the *full* error message and the steps you took before the error occurred when reporting the issue.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository. If you'd like to contribute code, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. (You'll need to create a LICENSE file and choose the MIT License).

## Disclaimer

Use this script responsibly and in accordance with Telegram's terms of service. The author is not responsible for any misuse or violations of Telegram's policies. This tool is for educational and personal use only.
