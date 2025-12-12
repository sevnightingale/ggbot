import { useState, useEffect } from 'react'

export interface ValidationRule {
  min?: number
  max?: number
  warningThreshold?: number
  required?: boolean
  errorMessage?: string
  warningMessage?: string
}

export interface ValidationResult {
  error: string | null
  warning: string | null
  isValid: boolean
}

export function useFieldValidation(
  value: number | undefined,
  rules: ValidationRule
): ValidationResult {
  const [error, setError] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)

  useEffect(() => {
    // Reset
    setError(null)
    setWarning(null)

    // Check if value exists
    if (value === undefined || value === null || isNaN(value)) {
      if (rules.required) {
        setError(rules.errorMessage || 'This field is required')
      }
      return
    }

    // Check min
    if (rules.min !== undefined && value < rules.min) {
      setError(rules.errorMessage || `Value must be at least ${rules.min}`)
      return
    }

    // Check max
    if (rules.max !== undefined && value > rules.max) {
      setError(rules.errorMessage || `Value cannot exceed ${rules.max}`)
      return
    }

    // Check warning threshold
    if (rules.warningThreshold !== undefined && value > rules.warningThreshold) {
      setWarning(rules.warningMessage || `Warning: Value above ${rules.warningThreshold}`)
    }
  }, [value, rules.min, rules.max, rules.warningThreshold, rules.required, rules.errorMessage, rules.warningMessage])

  return {
    error,
    warning,
    isValid: error === null
  }
}

// Specific validation rules
export const ValidationRules = {
  leverage: {
    min: 1,
    max: 100,
    warningThreshold: 20,
    warningMessage: '⚠️ High risk: Leverage above 20x amplifies losses'
  },
  stopLoss: {
    min: 1,
    max: 50
  },
  takeProfit: {
    min: 1,
    max: 500
  },
  maxMarginPercent: {
    min: 1,
    max: 100,
    warningThreshold: 50,
    warningMessage: '⚠️ Warning: Max margin above 50% can be very risky even at high confidence'
  }
}
