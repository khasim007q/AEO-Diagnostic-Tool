// GoogleResults.tsx
import { GoogleCorroborationSummary } from "../lib/types";
import { ExternalLink, Globe, AlertCircle, Info, CheckCircle2 } from "lucide-react";

interface GoogleResultsProps {
  summary: GoogleCorroborationSummary;
  targetBrandName?: string;
}

export default function GoogleResults({
  summary,
  targetBrandName,
}: GoogleResultsProps) {
  if (summary.status === "not_configured") {
    return (
      <div className="w-full rounded-2xl border bg-card p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-xl bg-muted text-muted-foreground">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-foreground">
              Search Corroboration Not Configured
            </h4>
            <p className="text-xs text-muted-foreground mt-1">
              Google search corroboration is optional and disabled because no SerpApi key was configured. AI visibility scoring is fully active and independent of Google search signals.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (summary.status === "failed") {
    return (
      <div className="w-full rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-rose-700 dark:text-rose-300">
              Search Corroboration Engine Unavailable
            </h4>
            <p className="text-xs text-muted-foreground mt-1">
              {summary.error_message || "Google SERP request encountered a network or quota error. Note: this failure did not affect the AI Visibility Score."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">
              Google Search Corroboration
            </h3>
            <p className="text-xs text-muted-foreground">
              Independent organic search benchmark evaluating whether AI recommendations correlate with Google organic search presence.
            </p>
          </div>
        </div>

        {targetBrandName && (
          <div>
            {summary.brand_found && summary.best_google_rank ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Found at Organic #{summary.best_google_rank}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground border">
                Not found in top {summary.total_results} organic results
              </span>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {summary.results.map((result) => {
          const hasMatch = result.match_type !== "none";

          return (
            <div
              key={result.rank}
              className={`flex flex-col p-5 border rounded-2xl bg-card shadow-sm transition-shadow hover:shadow-md ${
                hasMatch ? "border-primary/30 bg-primary/[0.02]" : ""
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-xs font-bold text-muted-foreground">
                  #{result.rank}
                </span>

                {result.match_type === "domain" && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    Domain Match (100%)
                  </span>
                )}
                {result.match_type === "title" && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                    Title Match (85%)
                  </span>
                )}
                {result.match_type === "snippet" && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    Snippet Match (70%)
                  </span>
                )}
                {result.match_type === "none" && (
                  <span className="text-[10px] text-muted-foreground font-medium">
                    Organic Competitor
                  </span>
                )}
              </div>

              <h4 className="font-semibold text-foreground mb-2 line-clamp-2 text-sm leading-snug">
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline hover:text-primary flex items-center gap-1.5 group"
                >
                  {result.title}
                  <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                </a>
              </h4>

              <p className="text-xs text-muted-foreground line-clamp-3 mb-4 flex-1 leading-relaxed">
                {result.snippet}
              </p>

              <div className="text-[11px] text-muted-foreground/75 truncate border-t pt-2">
                {result.domain || result.url}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
