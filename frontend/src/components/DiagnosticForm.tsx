import { useState, useEffect } from 'react';
import { DiagnosticRequest } from '../lib/types';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, Database, BrainCircuit, BarChart3, Sparkles } from 'lucide-react';

interface DiagnosticFormProps {
  onSubmit: (req: DiagnosticRequest) => void;
  isLoading: boolean;
}

const STEPS = [
  { id: 0, label: 'Querying AI models in parallel...', icon: BrainCircuit },
  { id: 1, label: 'Searching Google organic index...', icon: Search },
  { id: 2, label: 'Extracting and segmenting brand entities...', icon: Database },
  { id: 3, label: 'Applying exponential scoring and validation...', icon: BarChart3 },
];

const PRESETS = [
  { label: 'Magnesium for Seniors', query: 'best magnesium supplement for seniors', brand: 'Nature Made' },
  { label: 'Running Shoes', query: 'best running shoes for marathon training', brand: 'Nike' },
  { label: 'CRM for Startups', query: 'best crm software for startups', brand: 'HubSpot' },
  { label: 'Whey Protein', query: 'best whey protein powder for muscle growth', brand: 'Optimum Nutrition' },
];

export default function DiagnosticForm({ onSubmit, isLoading }: DiagnosticFormProps) {
  const [query, setQuery] = useState('');
  const [brand, setBrand] = useState('');
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isLoading) {
      setCurrentStep(0);
      interval = setInterval(() => {
        setCurrentStep((prev) => (prev < 3 ? prev + 1 : prev));
      }, 2400);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit({ query: query.trim(), your_brand: brand.trim() || undefined });
    }
  };

  const handleSelectPreset = (preset: typeof PRESETS[0]) => {
    setQuery(preset.query);
    setBrand(preset.brand);
  };

  return (
    <div className="w-full max-w-3xl mx-auto border rounded-2xl p-6 sm:p-8 bg-card shadow-sm flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="query" className="text-sm font-semibold text-foreground flex items-center justify-between">
            <span>Product Search Query <span className="text-rose-500">*</span></span>
            <span className="text-xs text-muted-foreground font-normal">What buyers ask AI engines</span>
          </label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3 h-5 w-5 text-muted-foreground" />
            <input
              id="query"
              type="text"
              required
              disabled={isLoading}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. best magnesium supplement for seniors"
              className="flex h-11 w-full rounded-xl border border-input bg-background pl-11 pr-4 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>
        
        <div className="flex flex-col gap-2">
          <label htmlFor="brand" className="text-sm font-semibold text-foreground flex items-center justify-between">
            <span>Your Brand <span className="text-muted-foreground text-xs font-normal">(Optional)</span></span>
            <span className="text-xs text-muted-foreground font-normal">For head-to-head gap analysis</span>
          </label>
          <input
            id="brand"
            type="text"
            disabled={isLoading}
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            placeholder="e.g. Nature Made"
            className="flex h-11 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              Presets:
            </span>
            {PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                disabled={isLoading}
                onClick={() => handleSelectPreset(p)}
                className="text-xs px-2.5 py-1 rounded-lg bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/50 transition-colors"
              >
                {p.label}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-8 py-2 w-full sm:w-auto shadow-sm"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Diagnostic...
              </>
            ) : (
              'Run Diagnostic'
            )}
          </button>
        </div>
      </form>

      <AnimatePresence>
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-4 pt-6 border-t">
              <div className="flex flex-col gap-3">
                {STEPS.map((step, idx) => {
                  const Icon = step.icon;
                  const isActive = currentStep === idx;
                  const isPast = currentStep > idx;
                  
                  return (
                    <motion.div 
                      key={step.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ 
                        opacity: isPast || isActive ? 1 : 0.35,
                        x: 0,
                      }}
                      className="flex items-center gap-3 text-sm font-medium"
                    >
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                        isActive ? 'bg-primary text-primary-foreground animate-pulse' : 
                        isPast ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 
                        'bg-muted text-muted-foreground'
                      }`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className={isActive ? 'text-foreground font-semibold' : 'text-muted-foreground'}>
                        {step.label}
                      </span>
                    </motion.div>
                  );
                })}
              </div>

              <div className="w-full bg-muted/60 h-2 rounded-full overflow-hidden mt-3">
                <motion.div 
                  className="bg-primary h-full rounded-full"
                  initial={{ width: '5%' }}
                  animate={{ width: `${Math.min(100, (currentStep + 1) * 25)}%` }}
                  transition={{ duration: 0.6 }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
