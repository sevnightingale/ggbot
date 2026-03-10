-- ggArena Season 2: arena_registrations table
-- Run against Supabase PostgreSQL

CREATE TABLE IF NOT EXISTS arena_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id INT NOT NULL,                 -- plain integer tag (2 = Season 2), no FK
    config_id UUID REFERENCES configurations(config_id),
    user_id UUID NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    unregistered_at TIMESTAMPTZ,            -- NULL = still registered
    starting_balance NUMERIC DEFAULT 10000,
    final_balance NUMERIC,                  -- snapshot at competition end
    final_pnl NUMERIC,                      -- snapshot at competition end
    final_pnl_pct NUMERIC,                  -- (final - 10000) / 10000 * 100
    active_days INT,                        -- calculated at competition end
    eligible BOOLEAN DEFAULT TRUE,          -- false if < 18 active days
    rank INT,                               -- final leaderboard position
    UNIQUE(season_id, config_id)
);

CREATE INDEX IF NOT EXISTS idx_arena_reg_season ON arena_registrations(season_id);
CREATE INDEX IF NOT EXISTS idx_arena_reg_config ON arena_registrations(config_id);
CREATE INDEX IF NOT EXISTS idx_arena_reg_active ON arena_registrations(season_id, unregistered_at)
    WHERE unregistered_at IS NULL;
