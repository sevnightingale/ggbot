"""
OAuth token generation script for @ggbots_ai X account.

This script generates bot-specific Access Token and Access Secret
for the @ggbots_ai account using the OAuth 1.0a PIN-based flow.

Run this once to get the tokens, then add them to .env file.
"""

import tweepy
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def generate_bot_tokens():
    """
    Generate Access Token and Secret for @ggbots_ai account.

    Steps:
    1. Prints an authorization URL
    2. User opens URL in browser and signs in as @ggbots_ai
    3. User authorizes the app and gets a PIN
    4. User pastes PIN back here
    5. Script outputs the Access Token and Secret
    """

    # Get consumer keys from .env
    consumer_key = os.getenv('X_API_KEY')
    consumer_secret = os.getenv('X_API_SECRET')

    if not consumer_key or not consumer_secret:
        print("ERROR: X_API_KEY and X_API_SECRET must be set in .env file")
        sys.exit(1)

    print("=" * 60)
    print("X Bot Token Generator for @ggbots_ai")
    print("=" * 60)
    print()

    try:
        # Initialize OAuth handler with 'oob' (out-of-band) for PIN-based auth
        oauth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback='oob')

        # Get authorization URL
        auth_url = oauth.get_authorization_url(signin_with_twitter=True)

        print("Step 1: Open this URL in a browser (use incognito/private mode):")
        print()
        print(auth_url)
        print()
        print("Step 2: Sign in as @ggbots_ai (NOT @sevnightingale)")
        print()
        print("Step 3: Authorize the app when prompted")
        print()
        print("Step 4: Copy the PIN displayed on screen")
        print()

        # Get PIN from user
        verifier = input("Paste the PIN here and press Enter: ").strip()

        if not verifier:
            print("ERROR: No PIN provided")
            sys.exit(1)

        # Exchange PIN for access tokens
        access_token, access_secret = oauth.get_access_token(verifier)

        print()
        print("=" * 60)
        print("SUCCESS! Tokens generated for @ggbots_ai:")
        print("=" * 60)
        print()
        print(f"X_ACCESS_TOKEN={access_token}")
        print(f"X_ACCESS_SECRET={access_secret}")
        print()
        print("=" * 60)
        print("Next steps:")
        print("1. Copy the two lines above")
        print("2. Replace the placeholder values in your .env file")
        print("3. Secure your .env file: chmod 600 .env")
        print("=" * 60)

    except tweepy.TweepyException as e:
        print(f"ERROR: {e}")
        print()
        print("Common issues:")
        print("- Make sure X_API_KEY and X_API_SECRET are correct in .env")
        print("- Ensure your app has OAuth 1.0a enabled in developer portal")
        print("- Check that app permissions are set to 'Read and Write'")
        sys.exit(1)

if __name__ == "__main__":
    generate_bot_tokens()
