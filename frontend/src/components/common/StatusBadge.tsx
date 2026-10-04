import React from "react";
import { OrderStatus } from "@/types";
import { STATUS_CONFIG, cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: OrderStatus;
  className?: string;
  showDot?: boolean;
}

export function StatusBadge({ status, className, showDot = true }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.new;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-colors",
        config.bgClass,
        config.textClass,
        config.borderClass,
        className
      )}
      title={config.description}
    >
      {showDot && (
        <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", config.dotClass)} />
      )}
      <span>{config.label}</span>
    </span>
  );
}
