import { useMemo } from 'react'

export function AnimateDigits({ value = '00:00', className = '' }) {
  const items = useMemo(
    () => String(value).split('').map((char, index) => ({ char, key: `${char}-${index}` })),
    [value],
  )

  return (
    <div className={`inline-flex items-baseline gap-1 ${className}`}>
      {items.map(({ char, key }) => {
        const isDigit = /\d/.test(char)
        return (
          <span
            key={key}
            className={isDigit ? 'inline-flex animate-pulse' : 'inline-flex'}
            aria-hidden="true"
          >
            {char}
          </span>
        )
      })}
    </div>
  )
}
