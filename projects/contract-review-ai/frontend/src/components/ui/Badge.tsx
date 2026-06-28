import React from 'react'
import { cn } from '../../utils/helpers'
import { X } from 'lucide-react'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info'
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
      secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
      destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
      outline: 'text-foreground',
      success: 'border-transparent bg-green-500/10 text-green-500 hover:bg-green-500/20',
      warning: 'border-transparent bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20',
      info: 'border-transparent bg-blue-500/10 text-blue-500 hover:bg-blue-500/20',
    }
    
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
          variants[variant],
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)
Badge.displayName = 'Badge'

interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  onRemove?: () => void
}

export const Tag = React.forwardRef<HTMLSpanElement, TagProps>(
  ({ className, children, onRemove, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center gap-1 rounded-md border bg-secondary px-2 py-1 text-xs font-medium',
        onRemove && 'cursor-pointer pr-1',
        className
      )}
      {...props}
    >
      {children}
      {onRemove && (
        <button
          onClick={onRemove}
          className="p-0.5 hover:bg-accent rounded transition-colors"
          aria-label="Remove tag"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  )
)
Tag.displayName = 'Tag'