import { useMemo, useState, useEffect } from "react"
import { Slider } from "@/components/ui/slider"
import { useDebounce } from "@/hooks/useDebounce"
import { cn } from "@/lib/utils"

const EPS_MIN = 0.01
const EPS_MAX = 10
const LOG_MIN = Math.log10(EPS_MIN)
const LOG_MAX = Math.log10(EPS_MAX)

function posToEpsilon(pos: number): number {
  const log = LOG_MIN + (pos / 100) * (LOG_MAX - LOG_MIN)
  return Math.pow(10, log)
}

function epsilonToPos(epsilon: number): number {
  const clamped = Math.min(Math.max(epsilon, EPS_MIN), EPS_MAX)
  return ((Math.log10(clamped) - LOG_MIN) / (LOG_MAX - LOG_MIN)) * 100
}

function formatEpsilon(epsilon: number): string {
  if (epsilon < 0.1) return epsilon.toFixed(3)
  if (epsilon < 1) return epsilon.toFixed(2)
  return epsilon.toFixed(1)
}

/** Nivel de privacidad percibido: 0 (epsilon alto, poco privado) a 1 (epsilon bajo, muy privado). */
function privacyLevel(epsilon: number): number {
  return 1 - epsilonToPos(epsilon) / 100
}

interface EpsilonControlProps {
  value: number
  onChange: (epsilon: number) => void
  onDebouncedChange?: (epsilon: number) => void
  debounceMs?: number
  presets?: number[]
}

export function EpsilonControl({
  value,
  onChange,
  onDebouncedChange,
  debounceMs = 300,
  presets = [0.1, 0.5, 1, 2, 5, 10],
}: EpsilonControlProps) {
  const [pos, setPos] = useState(() => epsilonToPos(value))
  const debouncedPos = useDebounce(pos, debounceMs)

  useEffect(() => {
    setPos(epsilonToPos(value))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (onDebouncedChange) onDebouncedChange(posToEpsilon(debouncedPos))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedPos])

  const epsilon = useMemo(() => posToEpsilon(pos), [pos])
  const level = privacyLevel(epsilon)

  const handlePosChange = (values: number[]) => {
    const next = values[0]
    setPos(next)
    onChange(posToEpsilon(next))
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          Presupuesto de privacidad (ε)
        </span>
        <span className="rounded-md bg-surface-muted px-2.5 py-1 font-mono text-sm font-semibold tabular-nums text-primary">
          ε = {formatEpsilon(epsilon)}
        </span>
      </div>

      <Slider
        value={[pos]}
        onValueChange={handlePosChange}
        min={0}
        max={100}
        step={0.1}
        aria-label="Presupuesto de privacidad epsilon, escala logarítmica"
      />

      <div className="flex justify-between font-mono text-[11px] text-muted-foreground">
        {presets.map((p) => (
          <button
            key={p}
            onClick={() => {
              const newPos = epsilonToPos(p)
              setPos(newPos)
              onChange(p)
            }}
            className="cursor-pointer rounded px-1 py-0.5 tabular-nums transition-colors hover:bg-surface-muted hover:text-foreground"
          >
            {p}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>Más privado</span>
          <span>Más preciso</span>
        </div>
        <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-surface-muted">
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-secondary to-accent transition-all duration-200 ease-out"
            style={{ width: `${(1 - level) * 100}%` }}
          />
        </div>
        <p className="text-center text-[11px] text-muted-foreground">
          {level > 0.66
            ? "Régimen conservador — mucho ruido, alta protección"
            : level > 0.33
              ? "Régimen intermedio — balance privacidad/utilidad"
              : "Régimen permisivo — poco ruido, baja protección"}
        </p>
      </div>
    </div>
  )
}

export function PrivacyBadge({ epsilon, className }: { epsilon: number; className?: string }) {
  const level = privacyLevel(epsilon)
  const label = level > 0.66 ? "Alta privacidad" : level > 0.33 ? "Privacidad media" : "Privacidad baja"
  const color =
    level > 0.66
      ? "bg-secondary/15 text-secondary"
      : level > 0.33
        ? "bg-accent-soft text-accent-foreground"
        : "bg-destructive/10 text-destructive"
  return (
    <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", color, className)}>
      {label}
    </span>
  )
}
