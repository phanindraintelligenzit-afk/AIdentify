import React from 'react'
import { cn } from '../../utils/helpers'
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'success' | 'warning' | 'info'
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      default: 'border-border bg-muted text-foreground',
      destructive: 'border-destructive/50 bg-destructive/10 text-destructive',
      success: 'border-green-500/50 bg-green-500/10 text-green-500',
      warning: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-500',
      info: 'border-blue-500/50 bg-blue-500/10 text-blue-500',
    }
    
    const icons = {
      default: <Info className="h-4 w-4" />,
      destructive: <AlertCircle className="h-4 w-4" />,
      success: <CheckCircle className="h-4 w-4" />,
      warning: <AlertCircle className="h-4 w-4" />,
      info: <Info className="h-4 w-4" />,
    }
    
    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          'relative w-full rounded-lg border p-4 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground',
          variants[variant],
          className
        )}
        {...props}
      >
        <div className="flex gap-3">
          <div className="shrink-0">{icons[variant]}</div>
          <div className="flex-1">{children}</div>
        </div>
      </div>
    )
  }
)
Alert.displayName = 'Alert'