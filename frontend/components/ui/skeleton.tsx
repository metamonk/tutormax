import * as React from "react"
import { cn } from "@/lib/utils"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The variant of skeleton animation to use
   * @default "pulse"
   */
  variant?: "pulse" | "shimmer" | "wave"
  /**
   * Whether the skeleton should be circular
   * @default false
   */
  circle?: boolean
}

function Skeleton({
  className,
  variant = "pulse",
  circle = false,
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "bg-muted",
        variant === "pulse" && "animate-pulse",
        variant === "shimmer" && "shimmer",
        variant === "wave" && "skeleton",
        circle ? "rounded-full" : "rounded-md",
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
