"""
X API Client Wrapper
Handles authentication, error handling, and rate limit tracking for X API v2.
"""

import tweepy
import os
from dotenv import load_dotenv
from core.common.logger import logger

load_dotenv()


class XClient:
    """
    Wrapper around Tweepy for X API v2 interactions.
    Handles authentication, posting tweets, and error handling.
    """

    def __init__(self):
        self.logger = logger.bind(service="x-bot", module="x_client")

        # Load credentials from environment
        self.api_key = os.getenv('X_API_KEY')
        self.api_secret = os.getenv('X_API_SECRET')
        self.access_token = os.getenv('X_ACCESS_TOKEN')
        self.access_secret = os.getenv('X_ACCESS_SECRET')

        # Validate credentials
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            raise ValueError("Missing X API credentials in .env file")

        # Initialize Tweepy client
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret
        )

    def test_auth(self) -> bool:
        """
        Test authentication by fetching authenticated user info.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            me = self.client.get_me()
            if me and me.data:
                self.logger.info(f"Authentication successful: @{me.data.username}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Authentication test failed: {e}")
            return False

    def post_tweet(self, text: str) -> str | None:
        """
        Post a tweet to X.

        Args:
            text: Tweet content (max 280 characters)

        Returns:
            str: Tweet ID if successful, None if failed
        """
        if len(text) > 280:
            self.logger.error(f"Tweet too long: {len(text)} chars (max 280)")
            return None

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data['id']

            self.logger.info(f"Tweet posted successfully: {tweet_id}")
            self.logger.bind(tweet_id=tweet_id).debug(f"Content: {text[:50]}...")

            return tweet_id

        except tweepy.Unauthorized as e:
            self.logger.error(f"Unauthorized (401): {e} - Check credentials")
            return None

        except tweepy.Forbidden as e:
            self.logger.error(f"Forbidden (403): {e} - Check app permissions")
            return None

        except tweepy.TooManyRequests as e:
            self.logger.error(f"Rate limit exceeded (429): {e}")
            # Could add retry logic here with exponential backoff
            return None

        except tweepy.TwitterServerError as e:
            self.logger.error(f"X server error (5xx): {e}")
            return None

        except Exception as e:
            self.logger.error(f"Unexpected error posting tweet: {e}")
            return None

    def post_reply(self, text: str, in_reply_to_tweet_id: str) -> str | None:
        """
        Post a reply to an existing tweet.

        Args:
            text: Reply content (max 280 characters)
            in_reply_to_tweet_id: ID of tweet to reply to

        Returns:
            str: Tweet ID if successful, None if failed
        """
        if len(text) > 280:
            self.logger.error(f"Reply too long: {len(text)} chars (max 280)")
            return None

        try:
            response = self.client.create_tweet(
                text=text,
                in_reply_to_tweet_id=in_reply_to_tweet_id
            )
            tweet_id = response.data['id']

            self.logger.info(f"Reply posted: {tweet_id} (replying to {in_reply_to_tweet_id})")

            return tweet_id

        except Exception as e:
            self.logger.error(f"Error posting reply: {e}")
            return None

    def get_user_tweets(self, user_id: str, max_results: int = 5) -> list | None:
        """
        Fetch recent tweets from a specific user.

        Args:
            user_id: X user ID
            max_results: Number of tweets to fetch (5-100)

        Returns:
            list: List of tweets if successful, None if failed
        """
        try:
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'text']
            )

            if response.data:
                self.logger.debug(f"Fetched {len(response.data)} tweets from user {user_id}")
                return response.data

            return []

        except Exception as e:
            self.logger.error(f"Error fetching user tweets: {e}")
            return None
