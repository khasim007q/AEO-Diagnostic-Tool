import { GapEntry } from '../lib/types';

interface GapAnalysisProps {
  gaps: GapEntry[];
}

export default function GapAnalysis({ gaps }: GapAnalysisProps) {
  return (
    <div className="w-full rounded-md border bg-card overflow-hidden">
      <div className="p-4 border-b bg-muted/20">
        <h3 className="text-lg font-semibold">Gap Analysis</h3>
        <p className="text-sm text-muted-foreground">Compare your brand scores directly against top competitors.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground uppercase text-xs">
            <tr>
              <th className="px-4 py-3 font-medium">Competitor</th>
              <th className="px-4 py-3 font-medium">LLM Engine</th>
              <th className="px-4 py-3 font-medium text-right">Your Score</th>
              <th className="px-4 py-3 font-medium text-right">Their Score</th>
              <th className="px-4 py-3 font-medium text-right">Gap</th>
              <th className="px-4 py-3 font-medium text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {gaps.map((gap, i) => (
              <tr key={i} className="hover:bg-muted/50 transition-colors">
                <td className="px-4 py-3 font-medium text-foreground">{gap.competitor}</td>
                <td className="px-4 py-3">{gap.llm}</td>
                <td className="px-4 py-3 text-right">{gap.your_score}</td>
                <td className="px-4 py-3 text-right">{gap.their_score}</td>
                <td className="px-4 py-3 text-right font-medium">
                  <span className={gap.gap > 0 ? 'text-green-500' : gap.gap < 0 ? 'text-red-500' : 'text-muted-foreground'}>
                    {gap.gap > 0 ? '+' : ''}{gap.gap}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      gap.status === 'winning' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      gap.status === 'losing' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                    }`}>
                      {gap.status.charAt(0).toUpperCase() + gap.status.slice(1)}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
