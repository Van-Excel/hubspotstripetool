import { cn } from '@/lib/utils'
import { forwardRef, type HTMLAttributes } from 'react'

export const Dialog = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement> & { open?: boolean; onClose?: () => void }>(
  ({ className, open, onClose, children, ...props }, ref) => {
    if (!open) return null
    return (
      <>
        <div className="fixed inset-0 z-50 bg-black/40" onClick={onClose} />
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
          <div
            ref={ref}
            className={cn('w-full max-w-md rounded-lg border bg-background p-6 shadow-lg', className)}
            onClick={(e) => e.stopPropagation()}
            {...props}
          >
            {children}
          </div>
        </div>
      </>
    )
  }
)
Dialog.displayName = 'Dialog'
