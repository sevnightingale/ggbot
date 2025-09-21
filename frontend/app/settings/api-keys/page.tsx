'use client'

import React from 'react'
import { ApiKeyManager } from '@/components/api-key-manager'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Shield, Key, Lock, AlertTriangle } from 'lucide-react'

export default function ApiKeysPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
          API Key Management
        </h1>
        <p className="text-[var(--text-muted)]">
          Manage your personal AI provider API keys for enhanced trading analysis
        </p>
      </div>

      {/* Security Notice */}
      <Card className="mb-6 border-amber-500/20 bg-amber-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-600">
            <Shield className="h-5 w-5" />
            Security & Privacy
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <Lock className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <strong>Encrypted Storage:</strong> All API keys are encrypted using Supabase Vault and never stored in plaintext.
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Key className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <strong>Secure Access:</strong> Keys are decrypted only when needed for AI requests and isolated to your account.
            </div>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <strong>Your Responsibility:</strong> Keep your API keys secure and monitor usage through your provider dashboards.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Benefits */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Why Use Personal API Keys?</CardTitle>
          <CardDescription>
            Adding your own API keys unlocks additional capabilities
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="font-medium text-[var(--text-primary)]">🔓 Unlock All Providers</h4>
            <p className="text-sm text-[var(--text-muted)]">
              Access OpenAI, DeepSeek, Anthropic, and XAI models with your own keys
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-[var(--text-primary)]">⚡ No Rate Limits</h4>
            <p className="text-sm text-[var(--text-muted)]">
              Bypass platform rate limits and use your full API quota
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-[var(--text-primary)]">📊 Direct Billing</h4>
            <p className="text-sm text-[var(--text-muted)]">
              AI usage charges directly to your provider account
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-[var(--text-primary)]">🎯 Custom Models</h4>
            <p className="text-sm text-[var(--text-muted)]">
              Access latest models and features as soon as they&apos;re released
            </p>
          </div>
        </CardContent>
      </Card>

      {/* API Key Manager */}
      <Card>
        <CardHeader>
          <CardTitle>Your API Keys</CardTitle>
          <CardDescription>
            Add and manage your personal AI provider API keys
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ApiKeyManager />
        </CardContent>
      </Card>

      {/* Provider Information */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Getting API Keys</CardTitle>
          <CardDescription>
            Where to obtain API keys from each provider
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]">
              <h4 className="font-medium text-[var(--text-primary)] mb-2">OpenAI</h4>
              <p className="text-sm text-[var(--text-muted)] mb-2">
                Get your API key from the OpenAI platform dashboard
              </p>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-500 hover:underline"
              >
                platform.openai.com/api-keys →
              </a>
            </div>

            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]">
              <h4 className="font-medium text-[var(--text-primary)] mb-2">DeepSeek</h4>
              <p className="text-sm text-[var(--text-muted)] mb-2">
                Create an API key from your DeepSeek console
              </p>
              <a
                href="https://platform.deepseek.com/api_keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-500 hover:underline"
              >
                platform.deepseek.com/api_keys →
              </a>
            </div>

            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]">
              <h4 className="font-medium text-[var(--text-primary)] mb-2">Anthropic</h4>
              <p className="text-sm text-[var(--text-muted)] mb-2">
                Get Claude API access from Anthropic console
              </p>
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-500 hover:underline"
              >
                console.anthropic.com/settings/keys →
              </a>
            </div>

            <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]">
              <h4 className="font-medium text-[var(--text-primary)] mb-2">XAI (Grok)</h4>
              <p className="text-sm text-[var(--text-muted)] mb-2">
                Access Grok models through XAI console
              </p>
              <a
                href="https://console.x.ai/settings/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-500 hover:underline"
              >
                console.x.ai/settings/api-keys →
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}