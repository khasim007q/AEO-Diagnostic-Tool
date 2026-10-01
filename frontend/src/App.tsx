import { useEffect, useRef } from 'react';
import Header from './components/Header';
import DiagnosticForm from './components/DiagnosticForm';
import { useDiagnostic } from './hooks/useDiagnostic';
import { AnimatePresence, motion } from 'framer-motion';
import ScoreCard from './components/ScoreCard';
import InsightsPanel from './components/InsightsPanel';
import BrandTable from './components/BrandTable';
import RankingChart from './components/RankingChart';
import GapAnalysis from './components/GapAnalysis';
import GoogleResults from './components/GoogleResults';
import RawResponses from './components/RawResponses';
import { Brain, Layers, SearchCheck } from 'lucide-react';

function App() {
  const diagnostic = useDiagnostic();
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (diagnostic.data && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [diagnostic.data]);

  return (
    <div className="min-h-screen flex flex-col font-sans bg-background text-foreground">
      <Header />
      
      <main className="flex-1 container max-w-6xl mx-auto py-10 px-4 sm:px-6 flex flex-col gap-10">
        <section className="flex flex-col items-center text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
            <span>Next-Gen Answer Engine Optimization</span>
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            See How AI Models Rank Your Brand
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
            Compare brand positioning across GPT-5, Claude Sonnet, and Gemini Flash, cross-referenced with organic Google Search results.
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
            className="p-4 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-xl border border-rose-500/20 mx-auto w-full max-w-3xl text-sm"
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
                <p className="text-sm text-muted-foreground mt-1">Enter a query above or click a preset to test the engine</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Brain className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Multi-Model Consensus</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Evaluates recommendations simultaneously across OpenAI, Anthropic, and Google with exponential rank weighting and consensus multipliers.
                  </p>
                </div>

                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Brand vs Product Separation</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Distinguishes parent brand visibility from individual product lines to show which specific products are driving AI recommendations.
                  </p>
                </div>

                <div className="flex flex-col gap-3 p-6 rounded-2xl border bg-card/60 backdrop-blur-sm shadow-sm hover:border-primary/40 transition-colors">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
                    <SearchCheck className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-semibold">Search Cross-Validation</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Compares AI brand prominence against actual Google Search organic snippets to score web authority and identify SEO gaps.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {diagnostic.data && (
            <motion.div 
              key="results"
              ref={resultsRef}
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, staggerChildren: 0.1 }}
              className="flex flex-col gap-12 pb-24"
            >
              <ScoreCard 
                data={diagnostic.data.grade} 
                yourBrand={diagnostic.data.your_brand} 
                totalEngines={diagnostic.data.llm_names?.length || 3}
              />

              <section className="space-y-4">
                <InsightsPanel insights={diagnostic.data.insights} />
              </section>
              
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold tracking-tight">Competitive Brand Hierarchy</h3>
                    <p className="text-sm text-muted-foreground">Click any brand to expand its specific product lines and rankings</p>
                  </div>
                </div>
                <BrandTable 
                  brands={diagnostic.data.all_brands} 
                  yourBrand={diagnostic.data.your_brand} 
                />
              </section>
              
              <section className="space-y-4">
                <div>
                  <h3 className="text-2xl font-bold tracking-tight">AI Engine Comparison</h3>
                  <p className="text-sm text-muted-foreground">Score breakdown across individual AI engines</p>
                </div>
                <RankingChart brands={diagnostic.data.all_brands} />
              </section>
              
              {diagnostic.data.gap_analysis && diagnostic.data.gap_analysis.length > 0 && (
                <section className="space-y-4">
                  <div>
                    <h3 className="text-2xl font-bold tracking-tight">Head-to-Head Gap Analysis</h3>
                    <p className="text-sm text-muted-foreground">Direct score comparison against your top market competitors</p>
                  </div>
                  <GapAnalysis gaps={diagnostic.data.gap_analysis} />
                </section>
              )}
              
              <section className="space-y-4 pt-8 border-t">
                <GoogleResults results={diagnostic.data.google_results} />
              </section>
              
              <section className="space-y-4 pt-8 border-t">
                <RawResponses responses={diagnostic.data.raw_llm_responses} />
              </section>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
