// RankingChart.tsx
import { BrandResult, EngineSummary } from "../lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface RankingChartProps {
  brands: BrandResult[];
  engineSummaries: EngineSummary[];
}

const ENGINE_PALETTE = [
  "#10a37f", // Green
  "#d97757", // Terracotta
  "#1a73e8", // Blue
  "#8b5cf6", // Purple
  "#f59e0b", // Amber
];

export default function RankingChart({
  brands,
  engineSummaries,
}: RankingChartProps) {
  const engineNames = engineSummaries.map((s) => s.engine);

  // Take top 8 brands by AI Visibility Score
  const chartData = brands.slice(0, 8).map((brand) => {
    const item: Record<string, string | number | null> = {
      name: brand.name,
      Overall: brand.ai_visibility_score,
    };

    engineNames.forEach((engine) => {
      const obs = brand.observations[engine];
      if (obs && obs.status === "success") {
        item[engine] = obs.mentioned ? Math.round(obs.position_score * 100) : 0;
      } else {
        // Render failed, partial, or invalid engine runs as null (gap in chart)
        // rather than falsely asserting 0% visibility for an engine that failed
        item[engine] = null;
      }
    });

    return item;
  });

  return (
    <div className="w-full h-[420px] p-6 bg-card rounded-2xl border shadow-sm flex flex-col">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-foreground">Cross-Engine Visibility Benchmark</h3>
        <p className="text-xs text-muted-foreground">
          Deterministic position score (0 to 100) per engine based on highest observed brand rank. Non-successful engines appear as gaps.
        </p>
      </div>

      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 20, left: 0, bottom: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis
              domain={[0, 100]}
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              unit="%"
            />
            <Tooltip
              cursor={{ fill: "hsl(var(--muted))", opacity: 0.2 }}
              formatter={(value: unknown, name: unknown) => {
                if (value === null || value === undefined) {
                  return ["Unavailable / Not scored", String(name)];
                }
                return [`${value}%`, String(name)];
              }}
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                color: "hsl(var(--popover-foreground))",
              }}
            />
            <Legend wrapperStyle={{ paddingTop: "15px" }} />
            {engineNames.map((engine, idx) => (
              <Bar
                key={engine}
                dataKey={engine}
                fill={ENGINE_PALETTE[idx % ENGINE_PALETTE.length]}
                radius={[4, 4, 0, 0]}
                maxBarSize={30}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
