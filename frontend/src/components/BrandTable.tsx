// BrandTable.tsx
import React, { useState } from "react";
import { BrandResult, EngineSummary } from "../lib/types";
import { ChevronDown, ChevronRight, Package, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface BrandTableProps {
  brands: BrandResult[];
  targetBrand?: BrandResult | null;
  engineSummaries: EngineSummary[];
}

export default function BrandTable({
  brands,
  targetBrand,
  engineSummaries,
}: BrandTableProps) {
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

  const isTargetBrand = (brandName: string) => {
    return targetBrand?.name.toLowerCase() === brandName.toLowerCase();
  };

  const engineNames = engineSummaries.map((s) => s.engine);

  return (
    <div className="w-full rounded-2xl border bg-card overflow-hidden shadow-sm">
      <div className="p-4 sm:p-6 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-foreground">Brand Ranking Hierarchy</h3>
          <p className="text-xs text-muted-foreground">
            Brands are evaluated by their best rank per successful engine. Expand any brand to inspect returned product evidence.
          </p>
        </div>
        <div className="text-xs text-muted-foreground font-medium">
          {brands.length} brand{brands.length === 1 ? "" : "s"} indexed across {engineSummaries.length} engines
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 text-muted-foreground uppercase text-xs border-b">
            <tr>
              <th className="px-4 py-3 font-medium w-10"></th>
              <th className="px-4 py-3 font-medium">Brand Entity</th>
              <th className="px-4 py-3 font-medium text-right">Visibility Score</th>
              <th className="px-4 py-3 font-medium text-right">Coverage</th>
              {engineNames.map((engine) => (
                <th key={engine} className="px-4 py-3 font-medium text-center">
                  {engine}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {brands.map((brand) => {
              const isTarget = isTargetBrand(brand.name);
              const isExpanded = expandedBrands.has(brand.name);
              return (
                <React.Fragment key={brand.name}>
                  <tr
                    className={`group cursor-pointer hover:bg-muted/50 transition-colors ${
                      isTarget ? "bg-primary/5 font-medium" : ""
                    }`}
                    onClick={() => toggleBrand(brand.name)}
                  >
                    <td className="px-4 py-4 w-10 text-muted-foreground">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </td>
                    <td className="px-4 py-4 text-foreground">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{brand.name}</span>
                        {isTarget && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/20 text-primary text-xs font-semibold">
                            <ShieldCheck className="w-3 h-3" />
                            Target
                          </span>
                        )}
                        {brand.products.length > 0 && (
                          <span className="text-[11px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                            {brand.products.length} product{brand.products.length === 1 ? "" : "s"}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-right font-bold text-foreground">
                      {brand.ai_visibility_score.toFixed(1)} / 100
                    </td>
                    <td className="px-4 py-4 text-right text-muted-foreground">
                      {brand.supporting_metrics.mention_coverage_display}
                    </td>
                    {engineNames.map((engine) => {
                      const obs = brand.observations[engine];
                      if (!obs) {
                        return (
                          <td key={engine} className="px-4 py-4 text-center text-muted-foreground">
                            -
                          </td>
                        );
                      }
                      if (obs.status === "failed") {
                        return (
                          <td key={engine} className="px-4 py-4 text-center">
                            <span className="text-xs px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400">
                              Failed
                            </span>
                          </td>
                        );
                      }
                      if (!obs.mentioned || obs.best_rank === null || obs.best_rank === undefined) {
                        return (
                          <td key={engine} className="px-4 py-4 text-center text-muted-foreground">
                            -
                          </td>
                        );
                      }
                      return (
                        <td key={engine} className="px-4 py-4 text-center">
                          <span className="inline-block px-2.5 py-0.5 rounded-full font-semibold text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            #{obs.best_rank}
                          </span>
                        </td>
                      );
                    })}
                  </tr>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.tr
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-muted/15"
                      >
                        <td colSpan={4 + engineNames.length} className="p-0">
                          <div className="px-8 py-4 border-b">
                            <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                              <Package className="w-3.5 h-3.5 text-primary" />
                              Product Evidence for {brand.name}
                            </div>
                            {brand.products.length === 0 ? (
                              <p className="text-xs text-muted-foreground italic py-2">
                                No specific product models were extracted for this brand mention.
                              </p>
                            ) : (
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="text-muted-foreground border-b border-border/50 text-left">
                                    <th className="py-2 font-medium">Model / Product Name</th>
                                    <th className="py-2 font-medium">Observed Engine</th>
                                    <th className="py-2 font-medium text-right">Engine Rank</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-border/40">
                                  {brand.products.map((prod, idx) => (
                                    <tr key={`${prod.engine}-${prod.rank}-${idx}`}>
                                      <td className="py-2 font-medium text-foreground">
                                        {prod.product_name}
                                      </td>
                                      <td className="py-2 text-muted-foreground">
                                        {prod.engine}
                                      </td>
                                      <td className="py-2 text-right font-semibold text-foreground">
                                        #{prod.rank}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            )}
                          </div>
                        </td>
                      </motion.tr>
                    )}
                  </AnimatePresence>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
