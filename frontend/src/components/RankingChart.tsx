import { BrandResult } from '../lib/types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface RankingChartProps {
  brands: BrandResult[];
}

const RANK_POINTS: Record<number, number> = { 1: 10, 2: 6, 3: 4, 4: 2, 5: 1 };

export default function RankingChart({ brands }: RankingChartProps) {
  const getEngineScore = (brand: BrandResult, engine: string): number => {
    let score = 0;
    brand.products.forEach(p => {
      const match = Object.entries(p.ranks).find(([k]) => k.toLowerCase().includes(engine.toLowerCase()));
      if (match) {
        score += RANK_POINTS[match[1]] || 0;
      }
    });
    return score;
  };

  const data = brands.slice(0, 8).map(brand => {
    return {
      name: brand.name,
      'GPT': getEngineScore(brand, 'gpt'),
      'Claude': getEngineScore(brand, 'claude'),
      'Gemini': getEngineScore(brand, 'gemini'),
    };
  });

  return (
    <div className="w-full h-[400px] p-6 bg-card rounded-xl border shadow-sm flex flex-col">
      <h3 className="text-lg font-semibold mb-6">Cross-Engine Score Comparison</h3>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip 
              cursor={{ fill: 'hsl(var(--muted))', opacity: 0.2 }}
              contentStyle={{ 
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                color: 'hsl(var(--popover-foreground))'
              }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Bar dataKey="GPT" fill="#10a37f" radius={[4, 4, 0, 0]} maxBarSize={40} />
            <Bar dataKey="Claude" fill="#d97757" radius={[4, 4, 0, 0]} maxBarSize={40} />
            <Bar dataKey="Gemini" fill="#1a73e8" radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
