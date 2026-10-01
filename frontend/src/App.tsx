// App.tsx
import { useEffect, useRef } from "react";
import Header from "./components/Header";
import DiagnosticForm from "./components/DiagnosticForm";
import { useDiagnostic } from "./hooks/useDiagnostic";
import { AnimatePresence, motion } from "framer-motion";
import ScoreCard from "./components/ScoreCard";
import InsightsPanel from "./components/InsightsPanel";
import BrandTable from "./components/BrandTable";
import RankingChart from "./components/RankingChart";
import GapAnalysis from "./components/GapAnalysis";
import GoogleResults from "./components/GoogleResults";
import RawResponses from "./components/RawResponses";
import { Brain, Layers, SearchCheck, Info } from "lucide-react";

function App() {
  const diagnostic = useDiagnostic();
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (diagnostic.data && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, [diagnostic.data]);

  return (
    <div className="min-h-screen flex flex-col font-sans bg-background text-foreground">
      <Header />

      <main className="flex-1 container max-w-6xl mx-auto py-10 px-4 sm:px-6 flex flex-col gap-10">
        <section className="flex flex-col items-center text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
            <span>Production Answer Engine Optimization Diagnostic</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            AI Visibility and Recommendation Audit
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
            Evaluate brand positioning across GPT-5-mini, Claude Sonnet 4, and Gemini 2.5 Flash, cross-referenced with independent Google search corroboration.
          </p>
        </section>

        <DiagnosticForm
          onSubmit={(req) => diagnostic.mutate(req)}
          isLoading={diagnostic.isPending}
        />

        {diagnostic.error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-2xl border border-rose-500/20 mx-auto w-full max-w-3xl text-sm"
          >
            <strong>Diagnostic Error:</strong> {diagnostic.error.message}
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {!diagnostic.data && !diagnostic.isPending && !diagnostic.error && (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-8 pt-4 pb-12"
            >
              <div className="text-center">
                <h3 className="text-lg font-bold text-foreground">What this diagnostic reveals</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Enter a query above or click a preset to inspect AI recommendations
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Brain className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Deterministic Visibility Scoring</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Evaluates recommendations across frontier LLMs with linear position weights (Rank 1 = 1.00 down to Rank 5 = 0.20) normalized strictly from 0 to 100.
                  </p>
                </div>

                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Entity and Product Separation</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Separates brand entities from product evidence. Only the best rank per engine contributes to the brand score, while all product models are preserved.
                  </p>
                </div>

                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <SearchCheck className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Independent Search Corroboration</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Evaluates organic Google SERP listings as an independent benchmark to verify whether AI engine prominence correlates with real search presence.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {diagnostic.data && (
            <motion.div
              key="results"
              ref={resultsRef}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="flex flex-col gap-10 pb-16"
            >
              {/* Section 1: Engine Breakdown & Primary Score */}
              <section aria-label="Engine Breakdown and Primary Score">
                <ScoreCard
                  score={diagnostic.data.ai_visibility_score}
                  visibilityLabel={diagnostic.data.visibility_label}
                  supportingMetrics={diagnostic.data.supporting_metrics}
                  targetBrand={diagnostic.data.target_brand}
                />
              </section>

              {/* Section 2: Competitive Landscape */}
              <section className="space-y-6" aria-label="Competitive Landscape">
                <RankingChart
                  brands={diagnostic.data.all_brands}
                  engineSummaries={diagnostic.data.engine_summaries}
                />

                {diagnostic.data.gap_analysis && diagnostic.data.gap_analysis.length > 0 && (
                  <GapAnalysis
                    gaps={diagnostic.data.gap_analysis}
                    targetBrandName={diagnostic.data.metadata.target_brand || undefined}
                  />
                )}
              </section>

              {/* Section 3: Product Evidence and Brand Hierarchy */}
              <section aria-label="Brand Ranking and Product Evidence">
                <BrandTable
                  brands={diagnostic.data.all_brands}
                  targetBrand={diagnostic.data.target_brand}
                  engineSummaries={diagnostic.data.engine_summaries}
                />
              </section>

              {/* Section 4: Search Corroboration */}
              <section aria-label="Search Corroboration">
                <GoogleResults
                  summary={diagnostic.data.google_corroboration}
                  targetBrandName={diagnostic.data.metadata.target_brand || undefined}
                />
              </section>

              {/* Section 5: Actionable Findings */}
              {diagnostic.data.insights && diagnostic.data.insights.length > 0 && (
                <section aria-label="Actionable Findings">
                  <InsightsPanel insights={diagnostic.data.insights} />
                </section>
              )}

              {/* Section 6: Raw Evidence and Telemetry */}
              <section aria-label="Raw Evidence and Telemetry">
                <RawResponses evidence={diagnostic.data.raw_evidence} />
              </section>

              {/* Mandatory Query-Specific Diagnostic Disclaimer */}
              <div className="p-4 rounded-xl bg-muted/40 border border-border/60 text-xs text-muted-foreground flex items-start gap-2.5">
                <Info className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                <p>
                  <strong>Diagnostic Disclaimer:</strong> These diagnostic results reflect a query-specific snapshot across selected AI models and search engines at execution time. They are not general brand endorsements or guarantees of future model responses.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
