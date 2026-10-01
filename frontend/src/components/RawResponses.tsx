import { useState } from 'react';

interface RawResponsesProps {
  responses: Record<string, { raw: string; parsed_count: number }>;
}

export default function RawResponses({ responses }: RawResponsesProps) {
  const llms = Object.keys(responses);
  const [activeTab, setActiveTab] = useState(llms[0]);

  if (!llms.length) return null;

  return (
    <div className="flex flex-col gap-4 mt-8">
      <h3 className="text-xl font-bold">Raw LLM Responses</h3>
      
      <div className="border rounded-xl bg-card overflow-hidden flex flex-col">
        <div className="flex border-b bg-muted/20 overflow-x-auto">
          {llms.map(llm => (
            <button
              key={llm}
              onClick={() => setActiveTab(llm)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === llm 
                  ? 'border-b-2 border-primary text-primary bg-background' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              {llm}
            </button>
          ))}
        </div>
        
        <div className="p-4 bg-muted/10">
          <div className="mb-4 flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">
              Parsed Brands: <span className="text-foreground font-bold">{responses[activeTab]?.parsed_count || 0}</span>
            </span>
          </div>
          
          <pre className="p-4 rounded-lg bg-zinc-950 text-zinc-50 overflow-x-auto text-xs leading-relaxed max-h-[400px] overflow-y-auto">
            <code>{responses[activeTab]?.raw}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
