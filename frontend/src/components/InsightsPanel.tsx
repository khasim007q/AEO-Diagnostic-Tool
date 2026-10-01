// InsightsPanel.tsx
import { TypedInsight } from "../lib/types";
import { Lightbulb, AlertTriangle, CheckCircle, Info } from "lucide-react";

interface InsightsPanelProps {
  insights: TypedInsight[];
}

export default function InsightsPanel({ insights }: InsightsPanelProps) {
  if (!insights || insights.length === 0) {
    return null;
  }

  const getStyleForType = (type: string) => {
    switch (type) {
      case "warning":
        return {
          border: "border-l-amber-500",
          bg: "bg-amber-500/5",
          icon: <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />,
          titleColor: "text-amber-700 dark:text-amber-400",
        };
      case "positive":
        return {
          border: "border-l-emerald-500",
          bg: "bg-emerald-500/5",
          icon: <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />,
          titleColor: "text-emerald-700 dark:text-emerald-400",
        };
      default:
        return {
          border: "border-l-blue-500",
          bg: "bg-blue-500/5",
          icon: <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />,
          titleColor: "text-blue-700 dark:text-blue-400",
        };
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-500">
          <Lightbulb className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-foreground">Actionable Diagnostic Insights</h3>
          <p className="text-xs text-muted-foreground">
            Factual, evidence-based observations comparing consensus, distribution, and search presence.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, i) => {
          const style = getStyleForType(insight.type);
          return (
            <div
              key={`${insight.title}-${i}`}
              className={`flex items-start gap-3.5 p-4 border rounded-2xl border-l-4 ${style.border} ${style.bg} text-sm transition-all`}
            >
              {style.icon}
              <div className="flex flex-col gap-1">
                <h4 className={`font-semibold text-xs uppercase tracking-wider ${style.titleColor}`}>
                  {insight.title}
                </h4>
                <p className="text-xs text-foreground/90 leading-relaxed">
                  {insight.message}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
