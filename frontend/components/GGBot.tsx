import React from 'react'

interface GGBotProps {
  name: string
  message?: string
  onClick?: () => void
  disabled?: boolean
  className?: string
}

const GGBot: React.FC<GGBotProps> = ({ 
  name, 
  message = '',
  onClick,
  disabled = false,
  className = ''
}) => {
  return (
    <div className={`ggbot-container ${className}`}>
      <button
        className={`ggbot-circle ${disabled ? 'ggbot-disabled' : ''}`}
        onClick={onClick}
        disabled={disabled}
        aria-label={`${name} bot`}
      >
        <div className="ggbot-inner">
          <div className="ggbot-name">{name}</div>
        </div>
      </button>
      {message && (
        <div className="ggbot-message">
          <span className="ggbot-message-text">{message}</span>
        </div>
      )}
    </div>
  )
}

export default GGBot