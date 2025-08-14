'use client'

interface CircularGGBotProps {
  botName: string
  status: 'inactive' | 'idle' | 'extracting' | 'deciding' | 'trading'
  message: string
  onClick: () => void
  isClickable?: boolean
}

export function CircularGGBot({ 
  botName, 
  status, 
  message, 
  onClick, 
  isClickable = true 
}: CircularGGBotProps) {
  const handleClick = () => {
    if (isClickable) {
      onClick()
    }
  }

  return (
    <div 
      className={`ggbot-circle ${status} ${isClickable ? 'clickable' : 'view-only'}`}
      onClick={handleClick}
    >
      <div className="ggbot-content">
        <h3 className="bot-name">{botName}</h3>
        <p className="status-message">{message}</p>
      </div>
    </div>
  )
}