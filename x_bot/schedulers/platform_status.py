"""
Platform Status Scheduler
Posts daily platform activity tweet with aggregate metrics.
"""

from core.common.logger import logger
from core.common.db import get_db_connection


async def post_platform_status(x_client):
    """
    Post daily platform status tweet with aggregate metrics.

    Called daily at 9:00 AM UTC by APScheduler.

    Args:
        x_client: XClient instance for posting tweets
    """
    log = logger.bind(service="x-bot", scheduler="platform_status")

    try:
        # Query platform-level metrics
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM configurations WHERE state = 'active') as active_bots,
                        (SELECT COUNT(DISTINCT user_id) FROM configurations) as total_users,
                        (SELECT COUNT(*) FROM paper_trades WHERE opened_at::date = CURRENT_DATE) as trades_today,
                        (SELECT COUNT(DISTINCT symbol) FROM decisions WHERE created_at > NOW() - INTERVAL '24 hours') as symbols_monitored,
                        (SELECT COUNT(*) FROM paper_trades WHERE status = 'open') as open_positions
                """)

                data = cur.fetchone()

        # Extract metrics
        active_bots = data[0] or 0
        total_users = data[1] or 0
        trades_today = data[2] or 0
        symbols_monitored = data[3] or 0
        open_positions = data[4] or 0

        # Format tweet
        tweet = f"""📊 Status

{active_bots} bots active | {total_users} users
{trades_today} trades today | {symbols_monitored} symbols tracked
Open positions: {open_positions}"""

        # Verify length
        if len(tweet) > 280:
            log.warning(f"Tweet too long ({len(tweet)} chars), truncating...")
            tweet = tweet[:280]

        # Post tweet
        tweet_id = x_client.post_tweet(tweet)

        if tweet_id:
            log.info(f"Platform status tweet posted: {tweet_id}")

            # Log to database for tracking
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if x_bot_tweets table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'x_bot_tweets'
                        )
                    """)
                    table_exists = cur.fetchone()[0]

                    if table_exists:
                        cur.execute("""
                            INSERT INTO x_bot_tweets
                            (tweet_id, tweet_type, content)
                            VALUES (%s, %s, %s)
                        """, (tweet_id, 'platform_status', tweet))
                        conn.commit()
                        log.debug("Logged tweet to database")
                    else:
                        log.warning("x_bot_tweets table not created yet, skipping database log")

        else:
            log.error("Failed to post platform status tweet")

    except Exception as e:
        log.error(f"Error in platform status scheduler: {e}")
