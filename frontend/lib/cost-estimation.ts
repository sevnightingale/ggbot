/**
 * Cost estimation utilities for bot LLM usage.
 *
 * Shared by UpgradeModal (paywall estimate) and ActivationBar (pre-activation estimate).
 * Costs include 70% platform markup, based on real production testing (2026-01-05).
 */

// Cost per decision by model and tier (with 70% markup already included)
export const MODEL_TIER_COSTS: Record<string, { economy: number; standard: number; premium: number }> = {
  'grok': { economy: 0.0014, standard: 0.0027, premium: 0.0264 },
  'deepseek': { economy: 0.0035, standard: 0.0034, premium: 0.0167 },
  'gemini': { economy: 0.0013, standard: 0.0448, premium: 0.0595 },
  'gpt': { economy: 0.0044, standard: 0.0504, premium: 1.2022 },
  'claude': { economy: 0.0275, standard: 0.0658, premium: 0.1452 },
  'kimi': { economy: 0.0076, standard: 0.0108, premium: 0.0164 },
  'qwen': { economy: 0.0007, standard: 0.0049, premium: 0.0152 },
  'default': { economy: 0.003, standard: 0.010, premium: 0.030 }
}

// Decisions per day by frequency
export const FREQUENCY_TO_DECISIONS: Record<string, number> = {
  '5m': 288,
  '15m': 96,
  '30m': 48,
  '1h': 24,
  '4h': 6,
  '1d': 1,
  '1w': 0.14,  // ~1 per week
  'signal_driven': 5  // estimate ~5 signals/day
}

/**
 * Estimate daily LLM cost for a bot based on its config.
 * Returns null if config doesn't have enough info to estimate.
 */
export function estimateDailyCost(configData: {
  llm_config?: { model?: string; reasoning_tier?: string; thinking_mode?: boolean }
  decision?: { analysis_frequency?: string | null }
}): number | null {
  const model = configData?.llm_config?.model?.toLowerCase() || 'default'
  const modelCosts = MODEL_TIER_COSTS[model] || MODEL_TIER_COSTS['default']

  // Determine reasoning tier
  let tier: 'economy' | 'standard' | 'premium' = 'standard'
  const configTier = configData?.llm_config?.reasoning_tier
  if (configTier === 'economy' || configTier === 'standard' || configTier === 'premium') {
    tier = configTier
  } else if (configData?.llm_config?.thinking_mode) {
    tier = 'premium'
  }

  const costPerDecision = modelCosts[tier]
  const frequency = configData?.decision?.analysis_frequency || '1h'
  const decisionsPerDay = FREQUENCY_TO_DECISIONS[frequency] || 24

  return decisionsPerDay * costPerDecision
}
