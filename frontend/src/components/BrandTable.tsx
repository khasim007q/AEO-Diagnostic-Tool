import React, { useState } from 'react';
import { BrandResult } from '../lib/types';
import { ChevronDown, ChevronRight, CheckCircle2, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface BrandTableProps {
  brands: BrandResult[];
  yourBrand: BrandResult | null;
}

export default function BrandTable({ brands, yourBrand }: BrandTableProps) {
  const [expandedBrands, setExpandedBrands] = useState<Set<string>>(new Set());

  const toggleBrand = (brandName: string) => {
    const next = new Set(expandedBrands);
    if (next.has(brandName)) {
      next.delete(brandName);
    } else {
      next.add(brandName);
    }
    setExpandedBrands(next);
  };

  const isYourBrand = (brandName: string) => {
    return yourBrand?.name.toLowerCase() === brandName.toLowerCase();
  };

  const getRankDisplay = (ranks: Record<string, number>, engine: string): string => {
    const match = Object.entries(ranks).find(([k]) => k.toLowerCase().includes(engine.toLowerCase()));
    return match ? `#${match[1]}` : '-';
  };

  return (
    <div className="w-full rounded-md border bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground uppercase text-xs">
            <tr>
              <th className="px-4 py-3 font-medium w-10"></th>
              <th className="px-4 py-3 font-medium">Brand / Product</th>
              <th className="px-4 py-3 font-medium text-right">Total Score</th>
              <th className="px-4 py-3 font-medium text-right">Consensus</th>
              <th className="px-4 py-3 font-medium text-center">Web Validated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {brands.map((brand) => (
              <React.Fragment key={brand.name}>
                <tr 
                  className={`group cursor-pointer hover:bg-muted/50 transition-colors ${
                    isYourBrand(brand.name) ? 'bg-primary/5' : ''
                  }`}
                  onClick={() => toggleBrand(brand.name)}
                >
                  <td className="px-4 py-4 w-10 text-muted-foreground">
                    {expandedBrands.has(brand.name) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </td>
                  <td className="px-4 py-4 font-semibold text-foreground">
                    <div className="flex items-center gap-2">
                      {brand.name}
                      {isYourBrand(brand.name) && (
                        <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-xs font-normal">
                          Your Brand
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right font-medium">{brand.total_score}</td>
                  <td className="px-4 py-4 text-right">{brand.consensus_pct}%</td>
                  <td className="px-4 py-4 text-center">
                    <div className="flex justify-center">
                      <span className="text-xs px-2 py-1 bg-muted rounded-md border">
                        {brand.llm_coverage.length} / 3 LLMs
                      </span>
                    </div>
                  </td>
                </tr>
                <AnimatePresence>
                  {expandedBrands.has(brand.name) && (
                    <motion.tr
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-muted/10"
                    >
                      <td colSpan={5} className="p-0">
                        <div className="px-12 py-3 border-b">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="text-muted-foreground">
                                <th className="py-2 text-left font-medium">Product</th>
                                <th className="py-2 text-right font-medium">Score</th>
                                <th className="py-2 text-right font-medium">GPT Rank</th>
                                <th className="py-2 text-right font-medium">Claude Rank</th>
                                <th className="py-2 text-right font-medium">Gemini Rank</th>
                                <th className="py-2 text-center font-medium">Web</th>
                              </tr>
                            </thead>
                            <tbody>
                              {brand.products.map((product, idx) => (
                                <tr key={idx} className="border-t border-border/50">
                                  <td className="py-2 text-foreground font-medium">{product.product_name}</td>
                                  <td className="py-2 text-right font-medium">{product.score}</td>
                                  <td className="py-2 text-right text-muted-foreground">{getRankDisplay(product.ranks, 'gpt')}</td>
                                  <td className="py-2 text-right text-muted-foreground">{getRankDisplay(product.ranks, 'claude')}</td>
                                  <td className="py-2 text-right text-muted-foreground">{getRankDisplay(product.ranks, 'gemini')}</td>
                                  <td className="py-2 text-center">
                                    <div className="flex justify-center">
                                      {product.web_validated ? (
                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                                      ) : (
                                        <XCircle className="h-4 w-4 text-muted-foreground/30" />
                                      )}
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </motion.tr>
                  )}
                </AnimatePresence>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
