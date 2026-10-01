// GapAnalysis.tsx
import { GapEntry } from "../lib/types";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface GapAnalysisProps {
  gaps: GapEntry[];
  targetBrandName?: string;
}

export default function GapAnalysis({
  gaps,
  targetBrandName,
}: GapAnalysisProps) {
  if (!gaps || gaps.length === 0) {
    return null;
  }

  return (
    <div className="w-full rounded-2xl border bg-card overflow-hidden shadow-sm">
      <div className="p-4 sm:p-6 border-b">
        <h3 className="text-lg font-bold text-foreground">
          Competitive Gap Analysis
        </h3>
        <p className="text-xs text-muted-foreground">
          Signed performance gap (Your Score minus Competitor Score). Positive indicates your brand leads; negative indicates competitor advantage.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground uppercase text-xs border-b">
            <tr>
              <th className="px-4 py-3 font-medium">Competitor</th>
              <th className="px-4 py-3 font-medium">Engine Scope</th>
              <th className="px-4 py-3 font-medium text-right">
                {targetBrandName || "Your Brand"}
              </th>
              <th className="px-4 py-3 font-medium text-right">Competitor</th>
              <th className="px-4 py-3 font-medium text-right">Signed Gap</th>
              <th className="px-4 py-3 font-medium text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {gaps.map((gap, i) => {
              const isAhead = gap.gap > 0;
              const isBehind = gap.gap < 0;

              return (
                <tr key={`${gap.competitor}-${gap.engine}-${i}`} className="hover:bg-muted/50 transition-colors">
                  <td className="px-4 py-3.5 font-semibold text-foreground">
                    {gap.competitor}
                  </td>
                  <td className="px-4 py-3.5 text-muted-foreground font-medium">
                    {gap.engine}
                  </td>
                  <td className="px-4 py-3.5 text-right font-medium text-foreground">
                    {gap.your_score.toFixed(1)}
                  </td>
                  <td className="px-4 py-3.5 text-right font-medium text-muted-foreground">
                    {gap.their_score.toFixed(1)}
                  </td>
                  <td className="px-4 py-3.5 text-right font-bold">
                    <span
                      className={`inline-flex items-center gap-1 ${
                        isAhead
                          ? "text-emerald-600 dark:text-emerald-400"
                          : isBehind
                          ? "text-rose-600 dark:text-rose-400"
                          : "text-zinc-500"
                      }`}
                    >
                      {isAhead ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : isBehind ? (
                        <ArrowDownRight className="w-4 h-4" />
                      ) : (
                        <Minus className="w-3.5 h-3.5" />
                      )}
                      {isAhead ? `+${gap.gap.toFixed(1)}` : gap.gap.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span
                      className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${
                        gap.status === "winning"
                          ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                          : gap.status === "losing"
                          ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20"
                          : "bg-muted text-muted-foreground border-border"
                      }`}
                    >
                      {gap.status === "winning"
                        ? "Leading"
                        : gap.status === "losing"
                        ? "Trailing"
                        : "Tied"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
