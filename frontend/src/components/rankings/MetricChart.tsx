"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RankingEntry } from "@/types/api";
interface MetricChartProps {
  entries: RankingEntry[];
  metricLabel: string;
}

const BAR_COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#a78bfa",
  "#c4b5fd",
  "#818cf8",
  "#6366f1",
  "#8b5cf6",
  "#a78bfa",
  "#c4b5fd",
  "#818cf8",
];

export function MetricChart({ entries, metricLabel }: MetricChartProps) {
  const chartData = entries.map((e) => ({
    name: e.company.ticker ?? e.company.name.slice(0, 10),
    value: e.metric_value,
    fullName: e.company.name,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={"#374151"} />
        <XAxis type="number" tick={{ fontSize: 12, fill: "#d1d5db" }} stroke={"#4b5563"} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#d1d5db" }} width={80} stroke={"#4b5563"} />
        <Tooltip
          formatter={(value) => [Number(value).toFixed(2), metricLabel]}
          labelFormatter={(_label, payload) => {
            const entry = payload?.[0]?.payload as { fullName?: string } | undefined;
            return entry?.fullName ?? "";
          }}
          contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #4b5563", borderRadius: "8px", color: "#f3f4f6" }}
          itemStyle={{ color: "#f3f4f6" }}
          labelStyle={{ color: "#ffffff", fontWeight: 600 }}
        />
        <Bar dataKey="value" name={metricLabel} radius={[0, 4, 4, 0]}>
          {chartData.map((_, index) => (
            <Cell key={index} fill={BAR_COLORS[index % BAR_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
