interface ScoreBadgeProps {
  score: number;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300";
  if (score >= 60)
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300";
  if (score >= 40)
    return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300";
  if (score >= 20)
    return "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300";
  return "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300";
}

function getBarWidth(score: number): string {
  return `${Math.min(100, Math.max(0, score))}%`;
}

export function ScoreBadge({ score }: ScoreBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-flex min-w-[3rem] items-center justify-center rounded-full px-2.5 py-0.5 text-sm font-bold ${getScoreColor(score)}`}
      >
        {score.toFixed(1)}
      </span>
      <div className="hidden h-2 w-16 overflow-hidden rounded-full bg-gray-200 sm:block dark:bg-gray-700">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all"
          style={{ width: getBarWidth(score) }}
        />
      </div>
    </div>
  );
}
