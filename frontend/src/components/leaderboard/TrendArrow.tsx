interface TrendArrowProps {
  trend: "up" | "down" | "flat";
  rankChange?: number | null;
}

export function TrendArrow({ trend, rankChange }: TrendArrowProps) {
  if (trend === "up") {
    return (
      <span className="inline-flex items-center gap-1 text-sm font-medium text-green-600 dark:text-green-400">
        <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z"
            clipRule="evenodd"
          />
        </svg>
        {rankChange != null && Math.abs(rankChange) > 0 && <span>{Math.abs(rankChange)}</span>}
      </span>
    );
  }

  if (trend === "down") {
    return (
      <span className="inline-flex items-center gap-1 text-sm font-medium text-red-600 dark:text-red-400">
        <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z"
            clipRule="evenodd"
          />
        </svg>
        {rankChange != null && Math.abs(rankChange) > 0 && <span>{Math.abs(rankChange)}</span>}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center text-sm text-gray-400 dark:text-gray-400">
      <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path
          fillRule="evenodd"
          d="M4 10a.75.75 0 01.75-.75h10.5a.75.75 0 010 1.5H4.75A.75.75 0 014 10z"
          clipRule="evenodd"
        />
      </svg>
    </span>
  );
}
