-- Arena Pledges Table
-- Records USX staking on ggArena bots for competition betting
-- Users stake USX → receive sUSX (yield), we record which bot they backed

CREATE TABLE IF NOT EXISTS arena_pledges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,                                    -- From Supabase auth
  wallet_address TEXT NOT NULL,                             -- Ethereum wallet that staked
  config_id UUID REFERENCES configurations(config_id),      -- Bot they're backing
  usx_amount DECIMAL(20, 6) NOT NULL,                       -- Amount of USX staked
  susx_amount DECIMAL(20, 6),                               -- Amount of sUSX received (optional)
  tx_hash TEXT NOT NULL UNIQUE,                             -- On-chain proof, prevents duplicates
  pledged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Future competition fields (nullable for now)
  competition_id UUID,                                      -- Link to competition when we add that
  prize_amount DECIMAL(20, 6),                              -- Filled after competition ends
  claimed_at TIMESTAMP WITH TIME ZONE,                      -- When user claimed prize
  unstaked_at TIMESTAMP WITH TIME ZONE                      -- If they unstake early
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_arena_pledges_user ON arena_pledges(user_id);
CREATE INDEX IF NOT EXISTS idx_arena_pledges_config ON arena_pledges(config_id);
CREATE INDEX IF NOT EXISTS idx_arena_pledges_wallet ON arena_pledges(wallet_address);
CREATE INDEX IF NOT EXISTS idx_arena_pledges_pledged_at ON arena_pledges(pledged_at);

-- Comments for documentation
COMMENT ON TABLE arena_pledges IS 'Records USX stakes on ggArena competition bots';
COMMENT ON COLUMN arena_pledges.tx_hash IS 'On-chain transaction hash, unique to prevent double-recording';
COMMENT ON COLUMN arena_pledges.susx_amount IS 'sUSX shares received, tracked for yield calculation';
