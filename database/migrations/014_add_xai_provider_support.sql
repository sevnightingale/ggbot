-- Migration: Add XAI provider support to user_llm_credentials table
-- Date: 2025-01-21
-- Description: Updates provider constraint to include 'xai' for Grok API support

-- Drop the existing constraint
ALTER TABLE public.user_llm_credentials
DROP CONSTRAINT IF EXISTS user_llm_credentials_provider_check;

-- Add new constraint including XAI
ALTER TABLE public.user_llm_credentials
ADD CONSTRAINT user_llm_credentials_provider_check
CHECK (provider = ANY (ARRAY['openai'::text, 'deepseek'::text, 'anthropic'::text, 'xai'::text]));

-- Add comment for documentation
COMMENT ON CONSTRAINT user_llm_credentials_provider_check
ON public.user_llm_credentials
IS 'Ensures provider is one of: openai, deepseek, anthropic, xai';