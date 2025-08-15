import React from 'react'

interface GGBotProps {
  name: string
  message?: string
  onClick?: () => void
  disabled?: boolean
  status?: 'inactive' | 'idle' | 'extraction' | 'decision' | 'trading'
  showSpinner?: boolean
  className?: string
}

const GGBot: React.FC<GGBotProps> = ({ 
  name, 
  message = '',
  onClick,
  disabled = false,
  status = 'inactive',
  showSpinner = false,
  className = ''
}) => {
  const spinnerChars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
  const [spinnerIndex, setSpinnerIndex] = React.useState(0)

  React.useEffect(() => {
    if (showSpinner) {
      const interval = setInterval(() => {
        setSpinnerIndex((prev) => (prev + 1) % spinnerChars.length)
      }, 80)
      return () => clearInterval(interval)
    }
    return undefined
  }, [showSpinner, spinnerChars.length])

  return (
    <div className={`ggbot-container ggbot-${status} ${className}`}>
      <button
        className={`ggbot-circle ggbot-${status} ${disabled ? 'ggbot-disabled' : ''}`}
        onClick={onClick}
        disabled={disabled}
        aria-label={`${name} bot`}
      >
        <div className="ggbot-inner">
          <div className="ggbot-name">{name}</div>
          <div className="ggbot-status-label">
            <span className={`ggbot-status-indicator ${status === 'idle' ? 'ggbot-status-active' : `ggbot-status-${status}`}`}>
              {status === 'idle' ? '●' : status === 'inactive' ? '○' : '●'}
            </span>
            <span className="ggbot-status-text">
              {status === 'idle' ? 'active' : status}
            </span>
          </div>
          {message && (
            <div className="ggbot-message-inline">
              {showSpinner && status !== 'idle' && status !== 'inactive' && (
                <span className="ggbot-spinner-inline">{spinnerChars[spinnerIndex]}</span>
              )}
              <span className="ggbot-message-text-inline">{message}</span>
            </div>
          )}
        </div>
      </button>
    </div>
  )
}

export default GGBot