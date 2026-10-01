// ScoreCard.tsx
import { SupportingMetrics, BrandResult } from "../lib/types";
import { motion } from "framer-motion";
import { Cpu, Award, TrendingUp, BarChart2 } from "lucide-react";

interface ScoreCardProps {
  score: number;
  visibilityLabel: string;
  supportingMetrics: SupportingMetrics;
  targetBrand?: BrandResult | null;
}

export default function ScoreCard({
  score,
  visibilityLabel,
  supportingMetrics,
  targetBrand,
}: ScoreCardProps) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  // Score is strictly 0 to 100
  const normalizedScore = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getScoreColor = (val: number) => {
    if (val >= 80) return "text-emerald-500 dark:text-emerald-400";
    if (val >= 60) return "text-blue-500 dark:text-blue-400";
    if (val >= 40) return "text-amber-500 dark:text-amber-400";
    if (val >= 20) return "text-orange-500 dark:text-orange-400";
    return "text-zinc-500 dark:text-zinc-400";
  };

  const getRingColor = (val: number) => {
    if (val >= 80) return "stroke-emerald-500 dark:stroke-emerald-400";
    if (val >= 60) return "stroke-blue-500 dark:stroke-blue-400";
    if (val >= 40) return "stroke-amber-500 dark:stroke-amber-400";
    if (val >= 20) return "stroke-orange-500 dark:stroke-orange-400";
    return "stroke-zinc-400 dark:stroke-zinc-600";
  };

  return (
    <div className="w-full bg-card rounded-2xl border p-6 sm:p-8 shadow-sm flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b">
        <div className="flex items-center gap-6">
          <div className="relative flex items-center justify-center w-36 h-36 flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 140 140">
              <circle
                cx="70"
                cy="70"
                r={radius}
                className="stroke-muted/40 fill-none"
                strokeWidth="10"
              />
              <motion.circle
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset }}
                transition={{ duration: 1.2, ease: "easeOut" }}
                cx="70"
                cy="70"
                r={radius}
                className={`fill-none ${getRingColor(normalizedScore)}`}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <motion.span
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3, type: "spring" }}
                className={`text-3xl font-black ${getScoreColor(normalizedScore)}`}
              >
                {Math.round(normalizedScore)}
              </motion.span>
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                / 100
              </span>
            </div>
          </div>

          <div className="flex flex-col items-start gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border bg-primary/10 text-primary border-primary/20">
              <Award className="w-3.5 h-3.5" />
              AI VISIBILITY
            </span>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              {visibilityLabel}
            </h2>
            <p className="text-sm text-muted-foreground">
              {targetBrand
                ? `Evaluation for target brand: ${targetBrand.name}`
                : "Category benchmark across verified AI responses"}
            </p>
          </div>
        </div>

        <div className="w-full sm:w-auto flex sm:flex-col justify-end items-end gap-1 text-right">
          <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
            Status
          </span>
          <span className="text-sm font-semibold text-foreground">
            {supportingMetrics.engine_availability_display}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-muted/40 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Cpu className="w-4 h-4 text-primary" />
            Engine Availability
          </div>
          <span className="text-xl font-bold text-foreground">
            {supportingMetrics.engine_availability_display}
          </span>
          <span className="text-xs text-muted-foreground">
            Successful / Configured
          </span>
        </div>

        <div className="p-4 rounded-xl bg-muted/40 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <BarChart2 className="w-4 h-4 text-emerald-500" />
            Mention Coverage
          </div>
          <span className="text-xl font-bold text-foreground">
            {supportingMetrics.mention_coverage_display}
          </span>
          <span className="text-xs text-muted-foreground">
            Mentioned / Successful
          </span>
        </div>

        <div className="p-4 rounded-xl bg-muted/40 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            Median Rank
          </div>
          <span className="text-xl font-bold text-foreground">
            {supportingMetrics.median_rank !== null && supportingMetrics.median_rank !== undefined
              ? `#${supportingMetrics.median_rank}`
              : "N/A"}
          </span>
          <span className="text-xs text-muted-foreground">
            Average: {supportingMetrics.average_rank !== null && supportingMetrics.average_rank !== undefined ? `#${supportingMetrics.average_rank}` : "N/A"}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-muted/40 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Award className="w-4 h-4 text-amber-500" />
            Best / Worst Rank
          </div>
          <span className="text-xl font-bold text-foreground">
            {supportingMetrics.best_rank ? `#${supportingMetrics.best_rank}` : "None"} / {supportingMetrics.worst_rank ? `#${supportingMetrics.worst_rank}` : "None"}
          </span>
          <span className="text-xs text-muted-foreground">
            Rank range across engines
          </span>
        </div>
      </div>
    </div>
  );
}
