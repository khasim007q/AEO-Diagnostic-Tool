from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Product:
    """Product domain model."""
    brand_name: str
    product_name: str
    full_name: str
    ranks: Dict[str, int] = field(default_factory=dict)
    score: float = 0.0
    web_validated: bool = False
    web_rank: Optional[int] = None

@dataclass
class Brand:
    """Brand domain model containing products."""
    name: str
    products: List[Product] = field(default_factory=list)
    total_score: float = 0.0
    llm_coverage: List[str] = field(default_factory=list)
    consensus_pct: float = 0.0

    @property
    def best_product(self) -> Optional[Product]:
        """Get the highest scoring product for this brand."""
        if not self.products:
            return None
        return max(self.products, key=lambda p: p.score)
