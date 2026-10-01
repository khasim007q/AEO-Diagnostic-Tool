import { GoogleResult } from '../lib/types';
import { ExternalLink, CheckCircle2 } from 'lucide-react';

interface GoogleResultsProps {
  results: GoogleResult[];
}

export default function GoogleResults({ results }: GoogleResultsProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <h3 className="text-xl font-bold">Google Search Results</h3>
        <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 text-xs font-medium">
          Top 5
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((result, i) => {
          // Fake AI validated logic for mockup since we don't have direct mapping in this prop
          const isAiValidated = i < 2; 

          return (
            <div key={i} className="flex flex-col p-5 border rounded-xl bg-card shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-xs font-bold text-muted-foreground">
                  {result.rank}
                </span>
                {isAiValidated && (
                  <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-[10px] uppercase font-bold rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> AI Validated
                  </span>
                )}
              </div>
              <h4 className="font-semibold text-primary mb-2 line-clamp-2">
                <a href={result.url} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1 group">
                  {result.title}
                  <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </a>
              </h4>
              <p className="text-sm text-muted-foreground line-clamp-3 mb-4 flex-1">
                {result.snippet}
              </p>
              <div className="text-xs text-muted-foreground truncate opacity-70">
                {result.url}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
