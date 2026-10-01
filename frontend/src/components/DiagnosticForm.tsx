// DiagnosticForm.tsx
import { useState, useEffect } from "react";
import { DiagnosticRequest } from "../lib/types";
import { Search, Loader2, Sparkles, Globe, SlidersHorizontal } from "lucide-react";

interface DiagnosticFormProps {
  onSubmit: (req: DiagnosticRequest) => void;
  isLoading: boolean;
}

const PRESETS = [
  {
    label: "Running Shoes",
    query: "best running shoes for marathon training",
    brand: "Nike",
    domain: "nike.com",
    market: "US",
  },
  {
    label: "Whey Protein",
    query: "best whey protein powder for muscle growth",
    brand: "Optimum Nutrition",
    domain: "optimumnutrition.com",
    market: "US",
  },
  {
    label: "CRM for Startups",
    query: "best crm software for startups",
    brand: "HubSpot",
    domain: "hubspot.com",
    market: "US",
  },
  {
    label: "Magnesium for Seniors",
    query: "best magnesium supplement for seniors",
    brand: "Nature Made",
    domain: "naturemade.com",
    market: "US",
  },
];

const MARKETS = [
  { code: "US", name: "United States (google.com)", domain: "google.com", lang: "en" },
  { code: "UK", name: "United Kingdom (google.co.uk)", domain: "google.co.uk", lang: "en" },
  { code: "India", name: "India (google.co.in)", domain: "google.co.in", lang: "en" },
  { code: "Canada", name: "Canada (google.ca)", domain: "google.ca", lang: "en" },
  { code: "Australia", name: "Australia (google.com.au)", domain: "google.com.au", lang: "en" },
  { code: "Germany", name: "Germany (google.de)", domain: "google.de", lang: "de" },
];

export default function DiagnosticForm({
  onSubmit,
  isLoading,
}: DiagnosticFormProps) {
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [website, setWebsite] = useState("");
  const [market, setMarket] = useState("US");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (isLoading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const selectedMarketConfig = MARKETS.find((m) => m.code === market) || MARKETS[0];

    onSubmit({
      query: query.trim(),
      your_brand: brand.trim() || undefined,
      website_or_domain: website.trim() || undefined,
      market: selectedMarketConfig.code,
      google_domain: selectedMarketConfig.domain,
      language: selectedMarketConfig.lang,
    });
  };

  const handleSelectPreset = (preset: (typeof PRESETS)[0]) => {
    setQuery(preset.query);
    setBrand(preset.brand);
    setWebsite(preset.domain);
    setMarket(preset.market);
  };

  return (
    <div className="w-full max-w-3xl mx-auto border rounded-2xl p-6 sm:p-8 bg-card shadow-sm flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="query"
            className="text-sm font-semibold text-foreground flex items-center justify-between"
          >
            <span>
              Product Search Query <span className="text-rose-500">*</span>
            </span>
            <span className="text-xs text-muted-foreground font-normal">
              Prompt submitted to AI engines
            </span>
          </label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3 h-5 w-5 text-muted-foreground" />
            <input
              id="query"
              type="text"
              required
              disabled={isLoading}
              maxLength={300}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. best running shoes for marathon training"
              className="flex h-11 w-full rounded-xl border border-input bg-background pl-11 pr-4 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label
              htmlFor="brand"
              className="text-sm font-semibold text-foreground flex items-center justify-between"
            >
              <span>
                Target Brand{" "}
                <span className="text-muted-foreground text-xs font-normal">
                  (Optional)
                </span>
              </span>
            </label>
            <input
              id="brand"
              type="text"
              disabled={isLoading}
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="e.g. Nike"
              className="flex h-11 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label
              htmlFor="website"
              className="text-sm font-semibold text-foreground flex items-center justify-between"
            >
              <span>
                Brand Website / Domain{" "}
                <span className="text-muted-foreground text-xs font-normal">
                  (Optional)
                </span>
              </span>
            </label>
            <input
              id="website"
              type="text"
              disabled={isLoading}
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="e.g. nike.com"
              className="flex h-11 w-full rounded-xl border border-input bg-background px-4 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            {showAdvanced ? "Hide Search Localization" : "Configure Search Localization"}
          </button>
        </div>

        {showAdvanced && (
          <div className="p-4 rounded-xl bg-muted/40 border border-border/60 flex flex-col gap-3">
            <label htmlFor="market" className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-primary" />
              Target Market and Google Domain
            </label>
            <select
              id="market"
              disabled={isLoading}
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-1 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {MARKETS.map((m) => (
                <option key={m.code} value={m.code}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        )}

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
                className="text-xs px-2.5 py-1 rounded-lg border bg-muted/30 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
              >
                {p.label}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="w-full sm:w-auto h-11 px-6 rounded-xl bg-primary text-primary-foreground font-medium text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors shadow-sm disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Diagnostic ({elapsedSeconds}s)...</span>
              </>
            ) : (
              <span>Run Diagnostic</span>
            )}
          </button>
        </div>

        {isLoading && (
          <div className="mt-2 p-4 rounded-xl bg-primary/5 border border-primary/20 text-xs text-foreground flex items-center gap-3">
            <Loader2 className="w-4 h-4 text-primary animate-spin flex-shrink-0" />
            <div className="flex flex-col gap-0.5">
              <span className="font-semibold">Querying evaluation models in parallel...</span>
              <span className="text-muted-foreground">
                Executing queries across GPT-5-mini, Claude Sonnet 4, Gemini 2.5 Flash, and Google organic search.
              </span>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
