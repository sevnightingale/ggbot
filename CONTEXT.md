[
  {
    "schemaname": "public",
    "tablename": "activities",
    "policyname": "activities_public_access",
    "permissive": "PERMISSIVE",
    "roles": "{public}",
    "cmd": "SELECT",
    "qual": "(EXISTS ( SELECT 1\n   FROM configurations c\n  WHERE ((c.config_id = activities.config_id) AND (c.is_public_performance = true))))",
    "with_check": null
  },
  {
    "schemaname": "public",
    "tablename": "activities",
    "policyname": "activities_user_access",
    "permissive": "PERMISSIVE",
    "roles": "{public}",
    "cmd": "SELECT",
    "qual": "(user_id = auth.uid())",
    "with_check": null
  },
  {
    "schemaname": "public",
    "tablename": "agent_sessions",
    "policyname": "agent_sessions_user_isolation",
    "permissive": "PERMISSIVE",
    "roles": "{public}",
    "cmd": "SELECT",
    "qual": "(EXISTS ( SELECT 1\n   FROM configurations c\n  WHERE ((c.config_id = agent_sessions.config_id) AND (c.user_id = auth.uid()))))",
    "with_check": null
  },
  {
    "schemaname": "public",
    "tablename": "llm_models",
    "policyname": "llm_models_public_read",
    "permissive": "PERMISSIVE",
    "roles": "{public}",
    "cmd": "SELECT",
    "qual": "true",
    "with_check": null
  }
]