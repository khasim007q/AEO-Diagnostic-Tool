import { GradeResult, BrandResult } from "../lib/types";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Award, Cpu, Globe, TrendingUp } from "lucide-react";

interface ScoreCardProps {
  data: GradeResult;
  yourBrand?: BrandResult | null;
  totalEngines?: number;
}

export default function ScoreCard({ data, yourBrand, totalEngines = 3 }: ScoreCardProps) {
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'text-emerald-500 dark:text-emerald-400';
      case 'B': return 'text-blue-500 dark:text-blue-400';
      case 'C': return 'text-amber-500 dark:text-amber-400';
      case 'D': return 'text-orange-500 dark:text-orange-400';
      case 'F': return 'text-rose-600 dark:text-rose-500';
      default: return 'text-muted-foreground';
    }
  };

  const getRingColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'stroke-emerald-500 dark:stroke-emerald-400';
      case 'B': return 'stroke-blue-500 dark:stroke-blue-400';
      case 'C': return 'stroke-amber-500 dark:stroke-amber-400';
      case 'D': return 'stroke-orange-500 dark:stroke-orange-400';
      case 'F': return 'stroke-rose-600 dark:stroke-rose-500';
      default: return 'stroke-muted';
    }
  };

  const getBadgeStyle = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'B': return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
      case 'C': return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'D': return 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20';
      case 'F': return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
      default: return 'bg-muted text-muted-foreground border-border';
    }
  };

  const percentage = Math.min(100, Math.max(0, (data.score / (data.max_score || 50)) * 100));
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const hasWebValidation = yourBrand ? yourBrand.products.some(p => p.web_validated) : false;
  const mentionsCount = yourBrand ? yourBrand.llm_coverage.length : 0;
  const consensusPct = yourBrand ? yourBrand.consensus_pct : 0;

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
                className={`fill-none ${getRingColor(data.grade)}`}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <motion.span 
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3, type: "spring" }}
                className={`text-5xl font-black ${getGradeColor(data.grade)}`}
              >
                {data.grade}
              </motion.span>
            </div>
          </div>

          <div className="flex flex-col items-start gap-2">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${getBadgeStyle(data.grade)}`}>
              <Award className="w-3.5 h-3.5" />
              AEO Performance Grade
            </span>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">{data.label}</h2>
            <p className="text-sm text-muted-foreground">
              {yourBrand ? `Target evaluation for ${yourBrand.name}` : "Comprehensive visibility rating across indexed models"}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end justify-center">
          <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Total Composite Score</span>
          <span className="text-3xl font-extrabold tracking-tight">
            {data.score} / {data.max_score}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-muted/30 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
            <Cpu className="w-4 h-4 text-primary" />
            AI Visibility
          </div>
          <div className="text-2xl font-bold text-foreground">
            {mentionsCount} <span className="text-sm font-normal text-muted-foreground">/ {totalEngines} Engines</span>
          </div>
          <p className="text-xs text-muted-foreground">Models referencing brand</p>
        </div>

        <div className="p-4 rounded-xl bg-muted/30 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
            <TrendingUp className="w-4 h-4 text-primary" />
            Model Consensus
          </div>
          <div className="text-2xl font-bold text-foreground">
            {consensusPct}%
          </div>
          <p className="text-xs text-muted-foreground">Cross-model agreement</p>
        </div>

        <div className="p-4 rounded-xl bg-muted/30 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
            <Globe className="w-4 h-4 text-primary" />
            Search Validation
          </div>
          <div className="flex items-center gap-1.5 text-2xl font-bold">
            {hasWebValidation ? (
              <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-6 h-6" /> Verified
              </span>
            ) : (
              <span className="text-muted-foreground flex items-center gap-1">
                <XCircle className="w-6 h-6 text-muted-foreground/50" /> Unverified
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">Google Page 1 presence</p>
        </div>

        <div className="p-4 rounded-xl bg-muted/30 border border-border/50 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium uppercase tracking-wider">
            <Award className="w-4 h-4 text-primary" />
            Relative Score
          </div>
          <div className="text-2xl font-bold text-foreground">
            {percentage.toFixed(0)}%
          </div>
          <p className="text-xs text-muted-foreground">Of maximum possible visibility</p>
        </div>
      </div>
    </div>
  );
}
