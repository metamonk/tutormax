import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const spinnerVariants = cva("animate-spin", {
  variants: {
    size: {
      sm: "h-4 w-4",
      default: "h-6 w-6",
      lg: "h-8 w-8",
      xl: "h-12 w-12",
    },
    variant: {
      default: "text-primary",
      muted: "text-muted-foreground",
      success: "text-success",
      warning: "text-warning",
      destructive: "text-destructive",
    },
  },
  defaultVariants: {
    size: "default",
    variant: "default",
  },
})

export interface SpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  /**
   * Optional label for screen readers
   */
  label?: string
}

function Spinner({
  className,
  size,
  variant,
  label = "Loading...",
  ...props
}: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn("inline-flex items-center justify-center", className)}
      {...props}
    >
      <Loader2 className={cn(spinnerVariants({ size, variant }))} />
      <span className="sr-only">{label}</span>
    </div>
  )
}

/**
 * Full-screen loading spinner
 */
function LoadingScreen({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="xl" label={label} />
        <p className="text-sm text-muted-foreground animate-pulse">{label}</p>
      </div>
    </div>
  )
}

/**
 * Centered loading spinner for containers
 */
function LoadingContainer({
  label = "Loading...",
  className,
}: {
  label?: string
  className?: string
}) {
  return (
    <div className={cn("flex items-center justify-center py-8", className)}>
      <Spinner label={label} />
    </div>
  )
}

export { Spinner, LoadingScreen, LoadingContainer, spinnerVariants }
