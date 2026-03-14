"use client";

import { useState, useCallback } from "react";

interface EmbedCodeGeneratorProps {
  chartUrl: string;
  title: string;
  width?: number;
  height?: number;
}

export function EmbedCodeGenerator({
  chartUrl,
  title,
  width: initialWidth = 600,
  height: initialHeight = 400,
}: EmbedCodeGeneratorProps) {
  const [width, setWidth] = useState(initialWidth);
  const [height, setHeight] = useState(initialHeight);
  const [copied, setCopied] = useState(false);

  const embedCode = `<iframe src="${chartUrl}" width="${width}" height="${height}" frameborder="0" title="${title}" loading="lazy" style="border:1px solid #e5e7eb;border-radius:8px;"></iframe>`;

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(embedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [embedCode]);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Embed this chart
      </h3>

      <div className="mb-4 flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          Width
          <input
            type="number"
            value={width}
            onChange={(e) => setWidth(Number(e.target.value))}
            min={200}
            max={1200}
            className="w-20 rounded border border-gray-300 px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          Height
          <input
            type="number"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            min={200}
            max={800}
            className="w-20 rounded border border-gray-300 px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          />
        </label>
      </div>

      <div className="relative">
        <textarea
          readOnly
          value={embedCode}
          rows={3}
          className="w-full rounded-lg border border-gray-300 bg-gray-50 p-3 font-mono text-xs text-gray-700 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
        />
        <button
          onClick={handleCopy}
          className="absolute right-2 top-2 rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-indigo-700"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    </div>
  );
}
