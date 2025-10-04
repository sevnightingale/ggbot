"""
Quick authentication test for @ggbots_ai X account.

Posts a simple test tweet to verify credentials work.
"""

import tweepy
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

def test_authentication():
    """Test X API authentication by posting a test tweet."""

    # Get credentials from .env
    api_key = os.getenv('X_API_KEY')
    api_secret = os.getenv('X_API_SECRET')
    access_token = os.getenv('X_ACCESS_TOKEN')
    access_secret = os.getenv('X_ACCESS_SECRET')

    # Validate all credentials are present
    if not all([api_key, api_secret, access_token, access_secret]):
        print("ERROR: Missing credentials in .env file")
        print("Required: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET")
        sys.exit(1)

    print("=" * 60)
    print("Testing X API Authentication for @ggbots_ai")
    print("=" * 60)
    print()

    try:
        # Initialize Tweepy client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )

        # Verify credentials by getting authenticated user info
        print("Step 1: Verifying credentials...")
        me = client.get_me()
        print(f"✓ Authenticated as: @{me.data.username}")
        print(f"✓ Account name: {me.data.name}")
        print()

        # Post test tweet
        print("Step 2: Posting test tweet...")
        test_tweet = "📊 Market analysis systems activated. Beginning real-time monitoring."

        response = client.create_tweet(text=test_tweet)
        tweet_id = response.data['id']

        print(f"✓ Tweet posted successfully!")
        print(f"✓ Tweet ID: {tweet_id}")
        print(f"✓ View at: https://twitter.com/{me.data.username}/status/{tweet_id}")
        print()
        print("=" * 60)
        print("SUCCESS! All authentication working correctly.")
        print("=" * 60)

    except tweepy.Unauthorized as e:
        print(f"✗ Authentication failed: {e}")
        print()
        print("Troubleshooting:")
        print("- Double-check X_ACCESS_TOKEN and X_ACCESS_SECRET in .env")
        print("- Verify app has 'Read and Write' permissions in developer portal")
        print("- Try regenerating tokens with generate_tokens.py")
        sys.exit(1)

    except tweepy.Forbidden as e:
        print(f"✗ Permission denied: {e}")
        print()
        print("Your app may not have Write permissions.")
        print("Check app settings in developer portal: Settings > App permissions")
        sys.exit(1)

    except tweepy.TweepyException as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_authentication()
