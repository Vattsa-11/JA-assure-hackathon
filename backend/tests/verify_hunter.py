import sys

backend_dir = r"c:\Users\sharv\Downloads\hackthon\ja-assure-marketing-agent\backend"
sys.path.append(backend_dir)

from app.core.config import settings
from app.services.hunter_client import hunter_client


def prove_hunter():
    print("\n--- HUNTER.IO VERIFICATION ---")

    if not settings.HUNTER_API_KEY:
        print("HUNTER_API_KEY is missing from backend/.env")
        print("Please add your key and run this script again.")
        return

    print(f"Hunter API Key detected (starts with {settings.HUNTER_API_KEY[:4]}...)")

    # We use 'michaeltrio.com', one of our valid OSM leads, to test email discovery
    test_domain = "michaeltrio.com"
    print(f"\nSearching for emails associated with domain: {test_domain}")

    emails = hunter_client.find_emails(test_domain)

    if emails:
        print(f"\nSuccess! Found {len(emails)} emails:")
        for email in emails:
            print(f" - {email}")
    else:
        print(f"\nNo emails found for {test_domain}. The key works, but no data exists for this specific domain.")

if __name__ == "__main__":
    prove_hunter()
