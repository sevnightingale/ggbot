import React from 'react'

interface GGBotProps {
  name: string
  message?: string
  onClick?: () => void
  disabled?: boolean
  status?: 'inactive' | 'idle' | 'extracting' | 'deciding' | 'trading'
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
    if (showSpinner && status !== 'inactive') {
      const interval = setInterval(() => {
        setSpinnerIndex((prev) => (prev + 1) % spinnerChars.length)
      }, 80)
      return () => clearInterval(interval)
    }
    return undefined
  }, [showSpinner, status, spinnerChars.length])

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
          {message && (
            <div className="ggbot-message-inline">
              {showSpinner && status !== 'inactive' && (
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