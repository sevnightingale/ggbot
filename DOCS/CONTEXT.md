
  1. Which notification events do you want to send automated emails for? For
  example:
    - Trade executions
    - Signal alerts
    - Position updates
    - Subscription changes
    - Daily/weekly summaries
    - Error alerts
  2. Initial sync: Should we sync all 261 existing users to Resend immediately, or
  just start syncing new users going forward?
  3. User data fields: Beyond email, what other data should we sync to Resend
  contacts? The user_profiles table doesn't have first_name/last_name fields.
  Should we:
    - Extract name from email?
    - Add first_name/last_name fields to user_profiles?
    - Just use email for now?
  4. Audience setup: Do you already have an audience created in Resend, or should I
   create one programmatically (e.g., "ggbots Users")?
