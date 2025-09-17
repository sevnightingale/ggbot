interface FlowLineProps {
  from: { x: number; y: number }
  to: { x: number; y: number }
  color: string
  isActive: boolean
}

export function FlowLine({ from, to, color, isActive }: FlowLineProps) {
  // Create a smooth curve path
  const midX = (from.x + to.x) / 2
  const midY = (from.y + to.y) / 2 + 20 // Add some curve
  
  const pathData = `M ${from.x} ${from.y} Q ${midX} ${midY} ${to.x} ${to.y}`

  return (
    <g>
      {/* Base line */}
      <path
        d={pathData}
        fill="none"
        stroke={isActive ? color : 'var(--bone-200)'}
        strokeWidth="2"
        opacity={isActive ? 0.6 : 0.2}
        className="transition-all duration-500"
      />
      
      {/* Animated flow line - only visible when active */}
      {isActive && (
        <path
          d={pathData}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeDasharray="5 10"
          opacity="0.8"
          className="animate-flow"
        />
      )}
      
      {/* Arrow at the end */}
      <defs>
        <marker
          id={`arrow-${color.replace(/[^a-zA-Z0-9]/g, '')}`}
          markerWidth="10"
          markerHeight="10"
          refX="8"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path
            d="M0,0 L0,6 L9,3 z"
            fill={isActive ? color : 'var(--bone-200)'}
            opacity={isActive ? 0.8 : 0.3}
          />
        </marker>
      </defs>
      
      {/* Apply arrow to main path */}
      <path
        d={pathData}
        fill="none"
        stroke="transparent"
        strokeWidth="2"
        markerEnd={`url(#arrow-${color.replace(/[^a-zA-Z0-9]/g, '')})`}
      />
    </g>
  )
}