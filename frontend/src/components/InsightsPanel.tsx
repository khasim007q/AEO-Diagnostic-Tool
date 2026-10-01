import { Lightbulb, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface InsightsPanelProps {
  insights: string[];
}

export default function InsightsPanel({ insights }: InsightsPanelProps) {
  const getInsightStyle = (text: string) => {
    const lower = text.toLowerCase();
    if (lower.includes('not') || lower.includes("doesn't") || lower.includes('missing') || lower.includes('low')) {
      return {
        border: 'border-l-amber-500',
        bg: 'bg-amber-50 dark:bg-amber-950/20',
        icon: <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
      };
    }
    if (lower.includes('outscore') || lower.includes('validated') || lower.includes('high') || lower.includes('strong')) {
      return {
        border: 'border-l-green-500',
        bg: 'bg-green-50 dark:bg-green-950/20',
        icon: <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
      };
    }
    return {
      border: 'border-l-blue-500',
      bg: 'bg-blue-50 dark:bg-blue-950/20',
      icon: <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
    };
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-5 h-5 text-amber-500" />
        <h3 className="text-xl font-bold">Actionable Insights</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, i) => {
          const style = getInsightStyle(insight);
          return (
            <div 
              key={i} 
              className={`flex items-start gap-3 p-4 border rounded-r-xl border-l-4 ${style.border} ${style.bg} text-sm`}
            >
              {style.icon}
              <p className="leading-relaxed text-foreground/90">{insight}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
