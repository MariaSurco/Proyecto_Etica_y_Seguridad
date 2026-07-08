import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatTileProps {
  label: string
  value: string
  hint?: string
  icon?: LucideIcon
  accent?: "primary" | "secondary" | "accent" | "destructive"
  className?: string
}

const ACCENT_STYLES: Record<NonNullable<StatTileProps["accent"]>, string> = {
  primary: "bg-primary/10 text-primary",
  secondary: "bg-secondary/15 text-secondary",
  accent: "bg-accent-soft text-accent-foreground",
  destructive: "bg-destructive/10 text-destructive",
}

export function StatTile({ label, value, hint, icon: Icon, accent = "primary", className }: StatTileProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(45,42,61,0.06)] transition-transform duration-200 hover:-translate-y-0.5",
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        {Icon && (
          <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", ACCENT_STYLES[accent])}>
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <span className="font-mono text-2xl font-semibold tabular-nums text-foreground">{value}</span>
      {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
    </div>
  )
}
