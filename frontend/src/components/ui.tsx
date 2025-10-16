import { ComponentPropsWithoutRef, forwardRef } from "react";

function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export const Card = forwardRef<HTMLDivElement, ComponentPropsWithoutRef<"div">>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl border border-slate-800/60 bg-slate-900/50 shadow-xl shadow-slate-950/40 backdrop-blur",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

export const Badge = forwardRef<HTMLSpanElement, ComponentPropsWithoutRef<"span">>(
  ({ className, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border border-indigo-500/40 bg-indigo-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-200",
        className
      )}
      {...props}
    />
  )
);
Badge.displayName = "Badge";

export const Button = forwardRef<
  HTMLButtonElement,
  ComponentPropsWithoutRef<"button"> & { variant?: "solid" | "ghost" }
>(({ className, variant = "solid", disabled, ...props }, ref) => (
  <button
    ref={ref}
    type="button"
    disabled={disabled}
    className={cn(
      "inline-flex items-center justify-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-60",
      variant === "ghost"
        ? "border border-slate-700/60 bg-transparent text-slate-300 hover:bg-slate-800/60"
        : "bg-indigo-500/80 text-white shadow-lg shadow-indigo-900/30 hover:bg-indigo-500",
      className
    )}
    {...props}
  />
));
Button.displayName = "Button";

export const Input = forwardRef<HTMLInputElement, ComponentPropsWithoutRef<"input">>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-400/50",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

interface SwitchProps extends Omit<ComponentPropsWithoutRef<"button">, "onChange"> {
  checked: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export const Switch = ({ checked, onCheckedChange, className, disabled, ...props }: SwitchProps) => (
  <button
    type="button"
    role="switch"
    aria-checked={checked}
    disabled={disabled}
    onClick={() => onCheckedChange?.(!checked)}
    className={cn(
      "relative inline-flex h-7 w-12 items-center rounded-full border border-slate-700/60 bg-slate-800 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/80 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
      checked && "bg-indigo-500/80",
      disabled && "cursor-not-allowed opacity-60",
      className
    )}
    {...props}
  >
    <span
      className={cn(
        "inline-block h-5 w-5 translate-x-1 transform rounded-full bg-white transition",
        checked && "translate-x-6"
      )}
    />
  </button>
);

