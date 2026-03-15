export function TableSkeleton({ rows = 10 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-10 rounded bg-gray-200 dark:bg-gray-700" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-14 rounded bg-gray-100 dark:bg-gray-600/50" />
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-80 rounded-lg bg-gray-100 dark:bg-gray-600/50" />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse rounded-lg border border-gray-200 p-6 dark:border-gray-800">
      <div className="mb-4 h-6 w-1/3 rounded bg-gray-200 dark:bg-gray-700" />
      <div className="space-y-2">
        <div className="h-4 w-2/3 rounded bg-gray-100 dark:bg-gray-600/50" />
        <div className="h-4 w-1/2 rounded bg-gray-100 dark:bg-gray-600/50" />
      </div>
    </div>
  );
}
