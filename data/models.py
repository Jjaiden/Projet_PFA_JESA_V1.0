"""
models.py — Data structures for the JDMAF referential and assessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# 1. REFERENTIAL MODELS (static)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Pillar:
    id: str
    name: str
    perimeter: str = ""
    dimension_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Dimension:
    id: str
    pillar_id: str
    name: str
    objective: str = ""
    subdimension_ids: tuple[str, ...] = field(default_factory=tuple)
    target_level_default: Optional[int] = None
    target_level_user: Optional[int] = None
    effective_target_level: Optional[int] = None
    target_level_description: str = ""


@dataclass(frozen=True)
class Subdimension:
    id: str
    dimension_id: str
    name: str
    objective: str = ""
    industrial_capability: str = ""
    main_risks: str = ""
    indicator_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Indicator:
    id: str
    pillar_id: str
    dimension_id: str
    subdimension_id: str
    name: str
    objective: str = ""
    question: str = ""
    indicator_type: str = ""
    measurement_mode: str = ""
    expected_respondent: str = ""
    perimeter: str = ""
    applicability_condition: str = ""
    evidence_category: str = ""
    gap_trigger_code: str = ""
    source_reference: str = ""
    assumptions: str = ""
    validation_status: str = ""


@dataclass(frozen=True)
class MaturityLevelDescription:
    level: int
    name: str
    generic_description: str = ""
    generic_evaluation_principle: str = ""
    minimum_evidence_principle: str = ""


@dataclass(frozen=True)
class DimensionMaturityLevel:
    dimension_id: str
    level: int
    level_name: str
    description: str = ""
    key_capabilities_expected: str = ""
    typical_observed_state: str = ""
    minimum_conditions: str = ""
    possible_evidence: str = ""
    main_limit_preventing_next_level: str = ""
    recommended_target_use: str = ""


@dataclass(frozen=True)
class IndicatorScoringGridEntry:
    indicator_id: str
    score: int
    score_label: str = ""
    observable_situation: str = ""
    mandatory_criteria: str = ""
    possible_evidence: str = ""
    disqualifying_conditions: str = ""
    evaluator_guidance: str = ""
    next_score_requirement: str = ""
    source_reference: str = ""               # <-- AJOUTÉ
    expert_validation_status: str = ""       # <-- AJOUTÉ


@dataclass(frozen=True)
class EvidenceCatalogEntry:
    id: str
    category: str
    name: str
    description: str = ""
    applicable_dimensions: str = ""
    reliability_level: str = ""
    example: str = ""
    confidentiality_considerations: str = ""


@dataclass
class WeightEntry:
    hierarchy_level: str
    parent_id: str
    component_id: str
    component_name: str
    default_weight: float
    user_defined_weight: Optional[float] = None
    effective_weight: Optional[float] = None
    weight_source: str = ""
    justification: str = ""
    validation_status: str = ""

    @property
    def resolved_weight(self) -> float:
        if self.effective_weight is not None:
            return self.effective_weight
        if self.user_defined_weight is not None:
            return self.user_defined_weight
        return self.default_weight


@dataclass
class Referentiel:
    version: str = ""
    pillars: dict[str, Pillar] = field(default_factory=dict)
    dimensions: dict[str, Dimension] = field(default_factory=dict)
    subdimensions: dict[str, Subdimension] = field(default_factory=dict)
    indicators: dict[str, Indicator] = field(default_factory=dict)
    maturity_scale: dict[int, MaturityLevelDescription] = field(default_factory=dict)
    dimension_maturity_matrices: dict[str, dict[int, DimensionMaturityLevel]] = field(default_factory=dict)
    indicator_scoring_grids: dict[str, dict[int, IndicatorScoringGridEntry]] = field(default_factory=dict)
    evidence_catalog: dict[str, EvidenceCatalogEntry] = field(default_factory=dict)
    weights: dict[str, dict[str, WeightEntry]] = field(default_factory=dict)
    target_levels: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_weight(self, hierarchy_level: str, component_id: str, default: float = 0.0) -> float:
        level_weights = self.weights.get(hierarchy_level, {})
        entry = level_weights.get(component_id)
        return entry.resolved_weight if entry else default


# ---------------------------------------------------------------------------
# 2. ASSESSMENT MODELS (dynamic)
# ---------------------------------------------------------------------------


@dataclass
class AssessmentMetadata:
    assessment_id: str
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    industrial_sector: Optional[str] = None
    plant_unit: Optional[str] = None
    location: Optional[str] = None
    assessment_date: Optional[str] = None
    evaluator_name: Optional[str] = None
    evaluator_function: Optional[str] = None
    assessment_version: Optional[str] = None
    reference_framework_version: Optional[str] = None
    general_comments: Optional[str] = None


@dataclass
class IndicatorScore:
    indicator_id: str
    pillar_id: str
    dimension_id: str
    subdimension_id: str
    question: str = ""
    selected_score: Optional[int] = None
    evidence_reference: Optional[str] = None
    evaluator_comment: Optional[str] = None
    confidence_level: Optional[str] = None
    applicability: str = "Applicable"
    validation_status: str = "Brouillon"

    @property
    def is_applicable(self) -> bool:
        return self.applicability == "Applicable"

    @property
    def is_scored(self) -> bool:
        return self.selected_score is not None


@dataclass
class Assessment:
    metadata: AssessmentMetadata
    indicator_scores: dict[str, IndicatorScore] = field(default_factory=dict)
    target_level_overrides: dict[str, int] = field(default_factory=dict)

    def scores_for_subdimension(self, subdimension_id: str) -> list[IndicatorScore]:
        return [s for s in self.indicator_scores.values() if s.subdimension_id == subdimension_id]

    def scores_for_dimension(self, dimension_id: str) -> list[IndicatorScore]:
        return [s for s in self.indicator_scores.values() if s.dimension_id == dimension_id]

    def scores_for_pillar(self, pillar_id: str) -> list[IndicatorScore]:
        return [s for s in self.indicator_scores.values() if s.pillar_id == pillar_id] 