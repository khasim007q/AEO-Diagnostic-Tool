# brand.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProductEvidence:
    """Evidence record for a product returned by an AI engine."""
    brand_name: str
    product_name: str
    full_name: str
    rank: int
    engine: str


@dataclass
class EngineObservation:
    """Scoring observation for a brand within a specific engine run."""
    engine: str
    status: str  # "success" | "failed" | "invalid"
    mentioned: bool = False
    best_rank: Optional[int] = None
    position_score: float = 0.0  # 1.00, 0.80, 0.60, 0.40, 0.20, 0.00
    products: List[ProductEvidence] = field(default_factory=list)
    latency_ms: float = 0.0
    error_type: Optional[str] = None


@dataclass
class Brand:
    """Brand domain model as a primary ranking entity."""
    name: str
    normalized_name: str
    domain: Optional[str] = None
    observations: Dict[str, EngineObservation] = field(default_factory=dict)
    products: List[ProductEvidence] = field(default_factory=list)
    ai_visibility_score: float = 0.0
    mention_coverage: float = 0.0
    engine_availability: float = 0.0
    median_rank: Optional[float] = None
    average_rank: Optional[float] = None
    best_rank: Optional[int] = None
    worst_rank: Optional[int] = None
    successful_engine_count: int = 0
    mentioned_engine_count: int = 0
    configured_engine_count: int = 0

    @property
    def best_product(self) -> Optional[ProductEvidence]:
        """Get the highest ranking product for this brand."""
        if not self.products:
            return None
        return min(self.products, key=lambda p: p.rank)
