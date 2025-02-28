import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNTS = []
i = 1
while True:
    api_id = os.getenv(f'ACCOUNT_{i}_API_ID')
    api_hash = os.getenv(f'ACCOUNT_{i}_API_HASH')
    phone = os.getenv(f'ACCOUNT_{i}_PHONE')

    if api_id is None or api_hash is None or phone is None:
        break 

    try:
        ACCOUNTS.append({
            'API_ID': int(api_id),
            'API_HASH': api_hash,
            'PHONE': phone
        })
    except ValueError:
        print(f"Error: Invalid API_ID for ACCOUNT_{i} in .env file.  Must be an integer.")
        import sys; sys.exit(1)

    i += 1

if not ACCOUNTS:
    print("Error: No accounts configured in .env file.")
    import sys; sys.exit(1)
