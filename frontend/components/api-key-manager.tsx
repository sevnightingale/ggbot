'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Trash2, Plus, Eye, EyeOff, Check, AlertTriangle } from 'lucide-react'

interface Credential {
  id: string
  provider: string
  credential_name: string
  created_at: string
  updated_at: string
}

interface ApiKeyManagerProps {
  onCredentialChange?: () => void
  className?: string
}

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', description: 'GPT models' },
  { id: 'deepseek', name: 'DeepSeek', description: 'Reasoning models' },
  { id: 'anthropic', name: 'Anthropic', description: 'Claude models' },
  { id: 'xai', name: 'XAI', description: 'Grok models' }
]

export function ApiKeyManager({ onCredentialChange, className = '' }: ApiKeyManagerProps) {
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newCredential, setNewCredential] = useState({
    provider: '',
    credential_name: '',
    api_key: ''
  })
  const [showKey, setShowKey] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Load existing credentials
  useEffect(() => {
    loadCredentials()
  }, [])

  const loadCredentials = async () => {
    try {
      const response = await fetch('/api/v2/user/llm-credentials', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setCredentials(data.credentials || [])
      } else {
        console.error('Failed to load credentials')
      }
    } catch (error) {
      console.error('Error loading credentials:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddCredential = async () => {
    if (!newCredential.provider || !newCredential.credential_name || !newCredential.api_key) {
      setError('All fields are required')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await fetch('/api/v2/user/llm-credentials', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newCredential)
      })

      if (response.ok) {
        setSuccess('API key added successfully!')
        setNewCredential({ provider: '', credential_name: '', api_key: '' })
        setShowAddForm(false)
        await loadCredentials()
        onCredentialChange?.()
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to add API key')
      }
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCredential = async (credentialName: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) {
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`/api/v2/user/llm-credentials/${encodeURIComponent(credentialName)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      })

      if (response.ok) {
        setSuccess('API key deleted successfully!')
        await loadCredentials()
        onCredentialChange?.()
      } else {
        setError('Failed to delete API key')
      }
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getProviderName = (providerId: string) => {
    return PROVIDERS.find(p => p.id === providerId)?.name || providerId
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Personal API Keys
          </h3>
          <p className="text-sm text-[var(--text-muted)]">
            Use your own API keys to access premium models
          </p>
        </div>
        <Button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2"
          variant="outline"
        >
          <Plus className="h-4 w-4" />
          Add API Key
        </Button>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
          <Check className="h-4 w-4 text-emerald-500" />
          <span className="text-sm text-emerald-600">{success}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <AlertTriangle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}

      {/* Add New Credential Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Add New API Key</CardTitle>
            <CardDescription>
              Your API key will be encrypted and stored securely
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-primary)]">
                Provider
              </label>
              <select
                value={newCredential.provider}
                onChange={(e) => setNewCredential({ ...newCredential, provider: e.target.value })}
                className="w-full mt-1 p-2 border border-[var(--border)] bg-[var(--bg-primary)] text-[var(--text-primary)] rounded-lg"
              >
                <option value="">Select a provider</option>
                {PROVIDERS.map(provider => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name} - {provider.description}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-[var(--text-primary)]">
                Credential Name
              </label>
              <Input
                placeholder="e.g., GPT-4 Production, DeepSeek Dev"
                value={newCredential.credential_name}
                onChange={(e) => setNewCredential({ ...newCredential, credential_name: e.target.value })}
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-[var(--text-primary)]">
                API Key
              </label>
              <div className="relative">
                <Input
                  type={showKey ? "text" : "password"}
                  placeholder="sk-..."
                  value={newCredential.api_key}
                  onChange={(e) => setNewCredential({ ...newCredential, api_key: e.target.value })}
                  className="mt-1 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleAddCredential}
                disabled={loading}
                className="flex-1"
              >
                {loading ? 'Adding...' : 'Add API Key'}
              </Button>
              <Button
                onClick={() => setShowAddForm(false)}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Existing Credentials */}
      <div className="space-y-3">
        {loading && credentials.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-muted)]">
            Loading credentials...
          </div>
        ) : credentials.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-[var(--text-muted)] mb-4">No API keys added yet</p>
            <Button
              onClick={() => setShowAddForm(true)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Your First API Key
            </Button>
          </div>
        ) : (
          credentials.map(credential => (
            <Card key={credential.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <Badge variant="secondary">
                    {getProviderName(credential.provider)}
                  </Badge>
                  <div>
                    <h4 className="font-medium text-[var(--text-primary)]">
                      {credential.credential_name}
                    </h4>
                    <p className="text-xs text-[var(--text-muted)]">
                      Added {formatDate(credential.created_at)}
                    </p>
                  </div>
                </div>

                <Button
                  onClick={() => handleDeleteCredential(credential.credential_name)}
                  variant="ghost"
                  size="sm"
                  className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}