// RawResponses.tsx
import { useState } from "react";
import { RawEvidence } from "../lib/types";
import { Terminal, Clock, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react";

interface RawResponsesProps {
  evidence: Record<string, RawEvidence>;
}

export default function RawResponses({ evidence }: RawResponsesProps) {
  const engineNames = Object.keys(evidence);
  const [activeTab, setActiveTab] = useState(engineNames[0] || "");

  if (!engineNames.length) return null;

  const current = evidence[activeTab] || evidence[engineNames[0]];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
          <Terminal className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-foreground">Raw Engine Evidence and Telemetry</h3>
          <p className="text-xs text-muted-foreground">
            Audit trail of raw responses, response status, execution latency, and parsing diagnostics.
          </p>
        </div>
      </div>

      <div className="border rounded-2xl bg-card overflow-hidden shadow-sm flex flex-col">
        <div className="flex border-b bg-muted/30 overflow-x-auto">
          {engineNames.map((name) => {
            const ev = evidence[name];
            const isSelected = activeTab === name;
            return (
              <button
                key={name}
                onClick={() => setActiveTab(name)}
                className={`px-5 py-3.5 text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 border-b-2 ${
                  isSelected
                    ? "border-primary text-primary bg-background"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                {name}
                {ev.status === "success" && (
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                )}
                {ev.status === "failed" && (
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                )}
                {ev.status === "invalid" && (
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                )}
              </button>
            );
          })}
        </div>

        {current && (
          <div className="p-5 flex flex-col gap-4 bg-muted/10">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b pb-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5 font-medium">
                  {current.status === "success" ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" /> Success
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400">
                      <AlertCircle className="w-3 h-3" /> {current.status.toUpperCase()}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1 text-muted-foreground">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{Math.round(current.latency_ms)} ms</span>
                </div>

                <div className="flex items-center gap-1 text-muted-foreground">
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>
                    {current.attempts} attempt{current.attempts === 1 ? "" : "s"}
                  </span>
                </div>
              </div>

              <div className="text-muted-foreground">
                Parsed Recommendations:{" "}
                <span className="font-bold text-foreground">
                  {current.parsed_count}
                </span>
              </div>
            </div>

            {current.error && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs">
                <strong>Diagnostic Error:</strong> {current.error}
              </div>
            )}

            <pre className="p-4 rounded-xl bg-zinc-950 text-zinc-100 overflow-x-auto text-xs leading-relaxed max-h-[350px] overflow-y-auto font-mono">
              <code>{current.raw_content || "(No response content returned)"}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
