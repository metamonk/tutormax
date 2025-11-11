/**
 * Skeleton Pattern Components
 *
 * Pre-built skeleton loading patterns for common UI components
 */

import * as React from "react"
import { Skeleton } from "./skeleton"
import { cn } from "@/lib/utils"

/**
 * Skeleton for text content with multiple lines
 */
export function TextSkeleton({
  lines = 3,
  className,
}: {
  lines?: number
  className?: string
}) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-4",
            i === lines - 1 ? "w-4/5" : "w-full" // Last line is shorter
          )}
        />
      ))}
    </div>
  )
}

/**
 * Skeleton for a card with title and description
 */
export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border p-6 space-y-4", className)}>
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-5 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      {/* Content */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      {/* Footer */}
      <div className="flex gap-2">
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  )
}

/**
 * Skeleton for a user profile with avatar and text
 */
export function ProfileSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-4", className)}>
      <Skeleton circle className="h-12 w-12" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  )
}

/**
 * Skeleton for a table with rows and columns
 */
export function TableSkeleton({
  rows = 5,
  columns = 4,
  className,
}: {
  rows?: number
  columns?: number
  className?: string
}) {
  return (
    <div className={cn("space-y-3", className)}>
      {/* Header */}
      <div className="flex gap-4 pb-3 border-b">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton for a list item
 */
export function ListItemSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-3 py-3", className)}>
      <Skeleton circle className="h-10 w-10 shrink-0" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
      <Skeleton className="h-8 w-20 shrink-0" />
    </div>
  )
}

/**
 * Skeleton for multiple list items
 */
export function ListSkeleton({
  items = 5,
  className,
}: {
  items?: number
  className?: string
}) {
  return (
    <div className={cn("divide-y", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <ListItemSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * Skeleton for a form with fields
 */
export function FormSkeleton({
  fields = 4,
  className,
}: {
  fields?: number
  className?: string
}) {
  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" /> {/* Label */}
          <Skeleton className="h-9 w-full" /> {/* Input */}
        </div>
      ))}
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
  )
}

/**
 * Skeleton for a chart or data visualization
 */
export function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      {/* Chart title */}
      <Skeleton className="h-5 w-48" />
      {/* Chart area */}
      <div className="flex items-end gap-2 h-48">
        {Array.from({ length: 12 }).map((_, i) => {
          // Random heights for visual variety
          const heights = ["h-20", "h-32", "h-40", "h-24", "h-36", "h-28"];
          const height = heights[i % heights.length];
          return <Skeleton key={i} className={cn("flex-1", height)} />;
        })}
      </div>
      {/* Legend */}
      <div className="flex gap-4">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  )
}

/**
 * Skeleton for dashboard metrics grid
 */
export function MetricsGridSkeleton({
  metrics = 4,
  className,
}: {
  metrics?: number
  className?: string
}) {
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-4", className)}>
      {Array.from({ length: metrics }).map((_, i) => (
        <div key={i} className="rounded-xl border p-6 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton for a complete dashboard page
 */
export function DashboardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Page title */}
      <Skeleton className="h-8 w-64" />

      {/* Metrics grid */}
      <MetricsGridSkeleton />

      {/* Charts row */}
      <div className="grid gap-6 md:grid-cols-2">
        <CardSkeleton />
        <CardSkeleton />
      </div>

      {/* Table */}
      <div className="rounded-xl border p-6">
        <Skeleton className="h-6 w-48 mb-4" />
        <TableSkeleton />
      </div>
    </div>
  )
}
