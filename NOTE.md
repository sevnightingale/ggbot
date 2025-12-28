SUPABASE errors, warnings, and suggestions:

[
  {
    "name": "rls_disabled_in_public",
    "title": "RLS Disabled in Public",
    "level": "ERROR",
    "facing": "EXTERNAL",
    "categories": [
      "SECURITY"
    ],
    "description": "Detects cases where row level security (RLS) has not been enabled on tables in schemas exposed to PostgREST",
    "detail": "Table \\`public.account_snapshots\\` is public, but RLS has not been enabled.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public",
    "metadata": {
      "name": "account_snapshots",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "rls_disabled_in_public_public_account_snapshots"
  }
]


[
  {
    "name": "auth_leaked_password_protection",
    "title": "Leaked Password Protection Disabled",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "SECURITY"
    ],
    "description": "Leaked password protection is currently disabled.",
    "detail": "Supabase Auth prevents the use of compromised passwords by checking against HaveIBeenPwned.org. Enable this feature to enhance security.",
    "cache_key": "auth_leaked_password_protection",
    "remediation": "https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection",
    "metadata": {
      "type": "auth",
      "entity": "Auth"
    }
  },
  {
    "name": "vulnerable_postgres_version",
    "title": "Current Postgres version has security patches available",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "SECURITY"
    ],
    "description": "Upgrade your postgres database to apply important security patches",
    "detail": "We have detected that the current version of postgres, supabase-postgres-17.4.1.074, has outstanding security patches available. Upgrade your database to receive the latest security patches.",
    "cache_key": "vulnerable_postgres_version",
    "remediation": "https://supabase.com/docs/guides/platform/upgrading",
    "metadata": {
      "type": "compliance",
      "entity": "Config"
    }
  }
]


[
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.data_sources\\` has a row level security policy \\`service_manages_data_sources\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_data_sources_service_manages_data_sources"
  },
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.data_points\\` has a row level security policy \\`service_manages_data_points\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_data_points_service_manages_data_points"
  },
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.live_trades\\` has a row level security policy \\`Users can view their own live trades\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "live_trades",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_live_trades_Users can view their own live trades"
  },
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.trade_observations\\` has a row level security policy \\`Users can only access their own trade observations\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "trade_observations",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_trade_observations_Users can only access their own trade observations"
  },
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.activities\\` has a row level security policy \\`activities_user_access\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_activities_activities_user_access"
  },
  {
    "name": "auth_rls_initplan",
    "title": "Auth RLS Initialization Plan",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if calls to \\`current_setting()\\` and \\`auth.<function>()\\` in RLS policies are being unnecessarily re-evaluated for each row",
    "detail": "Table \\`public.agent_sessions\\` has a row level security policy \\`agent_sessions_user_isolation\\` that re-evaluates current_setting() or auth.<function>() for each row. This produces suboptimal query performance at scale. Resolve the issue by replacing \\`auth.<function>()\\` with \\`(select auth.<function>())\\`. See [docs](https://supabase.com/docs/guides/database/postgres/row-level-security#call-functions-with-select) for more info.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0003_auth_rls_initplan",
    "metadata": {
      "name": "agent_sessions",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "auth_rls_init_plan_public_agent_sessions_agent_sessions_user_isolation"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.activities\\` has multiple permissive policies for role \\`anon\\` for action \\`SELECT\\`. Policies include \\`{activities_public_access,activities_user_access}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_activities_anon_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.activities\\` has multiple permissive policies for role \\`authenticated\\` for action \\`SELECT\\`. Policies include \\`{activities_public_access,activities_user_access}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_activities_authenticated_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.activities\\` has multiple permissive policies for role \\`authenticator\\` for action \\`SELECT\\`. Policies include \\`{activities_public_access,activities_user_access}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_activities_authenticator_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.activities\\` has multiple permissive policies for role \\`dashboard_user\\` for action \\`SELECT\\`. Policies include \\`{activities_public_access,activities_user_access}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_activities_dashboard_user_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_points\\` has multiple permissive policies for role \\`anon\\` for action \\`SELECT\\`. Policies include \\`{reference_data_points_read,service_manages_data_points}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_points_anon_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_points\\` has multiple permissive policies for role \\`authenticated\\` for action \\`SELECT\\`. Policies include \\`{reference_data_points_read,service_manages_data_points}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_points_authenticated_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_points\\` has multiple permissive policies for role \\`authenticator\\` for action \\`SELECT\\`. Policies include \\`{reference_data_points_read,service_manages_data_points}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_points_authenticator_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_points\\` has multiple permissive policies for role \\`dashboard_user\\` for action \\`SELECT\\`. Policies include \\`{reference_data_points_read,service_manages_data_points}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_points_dashboard_user_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_sources\\` has multiple permissive policies for role \\`anon\\` for action \\`SELECT\\`. Policies include \\`{reference_data_sources_read,service_manages_data_sources}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_sources_anon_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_sources\\` has multiple permissive policies for role \\`authenticated\\` for action \\`SELECT\\`. Policies include \\`{reference_data_sources_read,service_manages_data_sources}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_sources_authenticated_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_sources\\` has multiple permissive policies for role \\`authenticator\\` for action \\`SELECT\\`. Policies include \\`{reference_data_sources_read,service_manages_data_sources}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_sources_authenticator_SELECT"
  },
  {
    "name": "multiple_permissive_policies",
    "title": "Multiple Permissive Policies",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if multiple permissive row level security policies are present on a table for the same \\`role\\` and \\`action\\` (e.g. insert). Multiple permissive policies are suboptimal for performance as each policy must be executed for every relevant query.",
    "detail": "Table \\`public.data_sources\\` has multiple permissive policies for role \\`dashboard_user\\` for action \\`SELECT\\`. Policies include \\`{reference_data_sources_read,service_manages_data_sources}\\`",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0006_multiple_permissive_policies",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "multiple_permissive_policies_public_data_sources_dashboard_user_SELECT"
  },
  {
    "name": "duplicate_index",
    "title": "Duplicate Index",
    "level": "WARN",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects cases where two ore more identical indexes exist.",
    "detail": "Table \\`public.account_snapshots\\` has identical indexes {idx_snapshots_config_time,idx_snapshots_latest}. Drop all except one of them",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0009_duplicate_index",
    "metadata": {
      "name": "account_snapshots",
      "type": "table",
      "schema": "public",
      "indexes": [
        "idx_snapshots_config_time",
        "idx_snapshots_latest"
      ]
    },
    "cache_key": "duplicate_index_public_account_snapshots_{idx_snapshots_config_time,idx_snapshots_latest}"
  }
]

[
  {
    "name": "unindexed_foreign_keys",
    "title": "Unindexed foreign keys",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Identifies foreign key constraints without a covering index, which can impact database performance.",
    "detail": "Table \\`public.decisions\\` has a foreign key \\`decisions_config_fkey\\` without a covering index. This can lead to suboptimal query performance.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys",
    "metadata": {
      "name": "decisions",
      "type": "table",
      "schema": "public",
      "fkey_name": "decisions_config_fkey",
      "fkey_columns": [
        3
      ]
    },
    "cache_key": "unindexed_foreign_keys_public_decisions_decisions_config_fkey"
  },
  {
    "name": "unindexed_foreign_keys",
    "title": "Unindexed foreign keys",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Identifies foreign key constraints without a covering index, which can impact database performance.",
    "detail": "Table \\`public.paper_trades\\` has a foreign key \\`paper_trades_config_fkey\\` without a covering index. This can lead to suboptimal query performance.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys",
    "metadata": {
      "name": "paper_trades",
      "type": "table",
      "schema": "public",
      "fkey_name": "paper_trades_config_fkey",
      "fkey_columns": [
        4
      ]
    },
    "cache_key": "unindexed_foreign_keys_public_paper_trades_paper_trades_config_fkey"
  },
  {
    "name": "unindexed_foreign_keys",
    "title": "Unindexed foreign keys",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Identifies foreign key constraints without a covering index, which can impact database performance.",
    "detail": "Table \\`public.paper_trades\\` has a foreign key \\`paper_trades_decision_fkey\\` without a covering index. This can lead to suboptimal query performance.",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0001_unindexed_foreign_keys",
    "metadata": {
      "name": "paper_trades",
      "type": "table",
      "schema": "public",
      "fkey_name": "paper_trades_decision_fkey",
      "fkey_columns": [
        5
      ]
    },
    "cache_key": "unindexed_foreign_keys_public_paper_trades_paper_trades_decision_fkey"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_llm_models_enabled\\` on table \\`public.llm_models\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "llm_models",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_llm_models_idx_llm_models_enabled"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_llm_models_provider\\` on table \\`public.llm_models\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "llm_models",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_llm_models_idx_llm_models_provider"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_user_llm_credentials_user_id\\` on table \\`public.user_llm_credentials\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "user_llm_credentials",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_user_llm_credentials_idx_user_llm_credentials_user_id"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_bot_telegram_channels_enabled\\` on table \\`public.bot_telegram_channels\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "bot_telegram_channels",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_bot_telegram_channels_idx_bot_telegram_channels_enabled"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_bot_telegram_channels_chat_id\\` on table \\`public.bot_telegram_channels\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "bot_telegram_channels",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_bot_telegram_channels_idx_bot_telegram_channels_chat_id"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_decisions_confidence\\` on table \\`public.decisions\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "decisions",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_decisions_idx_decisions_confidence"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_paper_orders_filled_at\\` on table \\`public.paper_orders\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "paper_orders",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_paper_orders_idx_paper_orders_filled_at"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_event_id\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_event_id"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_logs_level_timestamp\\` on table \\`public.logs\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "logs",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_logs_idx_logs_level_timestamp"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_customer\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_customer"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_subscription\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_subscription"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_processed\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_processed"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_event_type\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_event_type"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_stripe_webhooks_retry\\` on table \\`public.stripe_webhooks\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "stripe_webhooks",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_stripe_webhooks_idx_stripe_webhooks_retry"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_data_sources_enabled\\` on table \\`public.data_sources\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_data_sources_idx_data_sources_enabled"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_data_sources_premium\\` on table \\`public.data_sources\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "data_sources",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_data_sources_idx_data_sources_premium"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_data_points_premium\\` on table \\`public.data_points\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "data_points",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_data_points_idx_data_points_premium"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_user_profiles_paid_data_points\\` on table \\`public.user_profiles\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "user_profiles",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_user_profiles_idx_user_profiles_paid_data_points"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_snapshots_heartbeat\\` on table \\`public.account_snapshots\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "account_snapshots",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_account_snapshots_idx_snapshots_heartbeat"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_live_trades_provider\\` on table \\`public.live_trades\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "live_trades",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_live_trades_idx_live_trades_provider"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_live_trades_provider_open\\` on table \\`public.live_trades\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "live_trades",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_live_trades_idx_live_trades_provider_open"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_trade_observations_config\\` on table \\`public.trade_observations\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "trade_observations",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_trade_observations_idx_trade_observations_config"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_trade_observations_user\\` on table \\`public.trade_observations\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "trade_observations",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_trade_observations_idx_trade_observations_user"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_trade_observations_type\\` on table \\`public.trade_observations\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "trade_observations",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_trade_observations_idx_trade_observations_type"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_trade_observations_importance\\` on table \\`public.trade_observations\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "trade_observations",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_trade_observations_idx_trade_observations_importance"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_activities_symbol\\` on table \\`public.activities\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "activities",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_activities_idx_activities_symbol"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_live_trades_symbol\\` on table \\`public.live_trades\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "live_trades",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_live_trades_idx_live_trades_symbol"
  },
  {
    "name": "unused_index",
    "title": "Unused Index",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Detects if an index has never been used and may be a candidate for removal.",
    "detail": "Index \\`idx_agent_sessions_session_id\\` on table \\`public.agent_sessions\\` has not been used",
    "remediation": "https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index",
    "metadata": {
      "name": "agent_sessions",
      "type": "table",
      "schema": "public"
    },
    "cache_key": "unused_index_public_agent_sessions_idx_agent_sessions_session_id"
  },
  {
    "name": "auth_db_connections_absolute",
    "title": "Auth DB Connection Strategy is not Percentage",
    "level": "INFO",
    "facing": "EXTERNAL",
    "categories": [
      "PERFORMANCE"
    ],
    "description": "Using a percentage based allocation connection strategy for Auth can help to improve the server's performance when increasing instance size.",
    "detail": "Your project's Auth server is configured to use at most 10 connections. Increasing the instance size without manually adjusting this number will not improve the performance of the Auth server. Switch to a percentage based connection allocation strategy instead.",
    "cache_key": "auth_db_connections_absolute",
    "remediation": "https://supabase.com/docs/guides/deployment/going-into-prod",
    "metadata": {
      "type": "auth",
      "entity": "Auth"
    }
  }
]