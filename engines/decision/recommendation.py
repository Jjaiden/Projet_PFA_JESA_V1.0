"""JDMAF recommendation selection engine."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import pandas as pd

from config import constants
from engines.decision.gap import GapResult
from engines.decision.tpi import TPIResult


@dataclass
class RecommendationResult:
    recommendation_id: str
    title: str
    description: str
    dimension_id: str
    pillar_id: str
    current_maturity_band: str
    gap_trigger_code: str
    priority: str
    effort: str
    horizon: str
    detailed_actions: list[str]
    prerequisites: list[str]
    dependencies: list[str]
    completion_evidence: list[str]
    expected_impact: str
    source_reference: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class RecommendationEngine:
    """Selects recommendations compatible with identified maturity gaps."""

    REQUIRED_RECOMMENDATION_COLUMNS = {
        "Recommendation_ID",
        "Dimension_ID",
    }

    def __init__(
        self,
        knowledge_base: pd.DataFrame,
        trigger_mapping: Optional[pd.DataFrame] = None,
        config: Optional[Mapping[str, Any]] = None,
    ):
        if not isinstance(knowledge_base, pd.DataFrame):
            raise TypeError(
                "knowledge_base must be a pandas.DataFrame."
            )

        missing = (
            self.REQUIRED_RECOMMENDATION_COLUMNS
            - set(knowledge_base.columns)
        )

        if missing:
            raise ValueError(
                "Missing columns in knowledge_base: "
                f"{sorted(missing)}"
            )

        if (
            trigger_mapping is not None
            and not isinstance(trigger_mapping, pd.DataFrame)
        ):
            raise TypeError(
                "trigger_mapping must be a pandas.DataFrame "
                "or None."
            )

        self.knowledge_base = knowledge_base.copy()

        self.trigger_mapping = (
            trigger_mapping.copy()
            if trigger_mapping is not None
            else pd.DataFrame()
        )

        self.config = dict(config or {})
        self.context = self.config.get("context", {})

        self._build_indexes()

    # ========================================================================
    # RECOMMENDATION SELECTION
    # ========================================================================

    def get_recommendations_for_gap(
        self,
        gap_result: GapResult,
        tpi_result: Optional[TPIResult] = None,
    ) -> list[RecommendationResult]:
        """Returns recommendations applicable to a positive maturity gap."""

        if gap_result.gap <= 0:
            return []

        dimension_id = self._dimension_for_gap(gap_result)

        if dimension_id is None:
            return []

        details = gap_result.details or {}

        current_level = int(
            details.get(
                "current_level",
                0,
            )
        )

        target_level = float(
            details.get(
                "target_level",
                3,
            )
        )

        band = constants.get_maturity_band(
            current_level
        )

        trigger_codes = self._matching_trigger_codes(
            dimension_id,
            current_level,
            gap_result.gap,
            target_level,
        )

        recommendations: list[
            RecommendationResult
        ] = []

        for recommendation_id in self._find_candidates(
            dimension_id,
            band,
            gap_result.gap,
            target_level,
            trigger_codes,
        ):
            record = self._records_by_id[
                recommendation_id
            ]

            recommendations.append(
                self._create_recommendation_result(
                    record,
                    priority=self._determine_priority(
                        gap_result.gap,
                        tpi_result,
                    ),
                )
            )

        priority_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        return sorted(
            recommendations,
            key=lambda item: (
                priority_order.get(
                    item.priority,
                    4,
                ),
                item.effort,
                item.title,
            ),
        )

    def get_all_recommendations(
        self,
        gap_results: list[GapResult],
        tpi_results: Optional[
            list[TPIResult]
        ] = None,
    ) -> dict[
        str,
        list[RecommendationResult],
    ]:
        """Returns recommendations by dimension for positive maturity gaps."""

        tpi_by_dimension = {
            result.dimension_id: result
            for result in (
                tpi_results or []
            )
        }

        recommendations: dict[
            str,
            list[RecommendationResult],
        ] = {}

        for gap in gap_results:

            dimension_id = (
                self._dimension_for_gap(gap)
            )

            if (
                gap.gap <= 0
                or dimension_id is None
            ):
                continue

            selected = (
                self.get_recommendations_for_gap(
                    gap,
                    tpi_by_dimension.get(
                        dimension_id
                    ),
                )
            )

            if selected:
                recommendations[
                    dimension_id
                ] = selected

        return recommendations

    def get_recommendations_by_dimension(
        self,
        dimension_id: str,
    ) -> list[RecommendationResult]:
        """Returns all recommendations for a dimension without gap filtering."""

        return [
            self._create_recommendation_result(
                self._records_by_id[
                    recommendation_id
                ]
            )
            for recommendation_id
            in self.recommendations_by_dimension.get(
                dimension_id,
                [],
            )
        ]

    def get_recommendation_by_id(
        self,
        recommendation_id: str,
    ) -> Optional[RecommendationResult]:

        record = self._records_by_id.get(
            recommendation_id
        )

        return (
            self._create_recommendation_result(
                record
            )
            if record
            else None
        )

    # ========================================================================
    # INDEXES
    # ========================================================================

    def _build_indexes(self) -> None:

        self._records_by_id: dict[
            str,
            dict[str, Any],
        ] = {}

        self.recommendations_by_dimension: dict[
            str,
            list[str],
        ] = {}

        self.recommendations_by_trigger: dict[
            str,
            list[str],
        ] = {}

        self.recommendations_by_band: dict[
            str,
            list[str],
        ] = {}

        for _, row in self.knowledge_base.iterrows():

            record = self._row_to_record(row)

            recommendation_id = (
                record["recommendation_id"]
            )

            if not recommendation_id:
                continue

            if (
                recommendation_id
                in self._records_by_id
            ):
                raise ValueError(
                    "Duplicate Recommendation_ID: "
                    f"{recommendation_id}"
                )

            self._records_by_id[
                recommendation_id
            ] = record

            self.recommendations_by_dimension.setdefault(
                record["dimension_id"],
                [],
            ).append(
                recommendation_id
            )

            if record["gap_trigger_code"]:
                self.recommendations_by_trigger.setdefault(
                    record["gap_trigger_code"],
                    [],
                ).append(
                    recommendation_id
                )

            if record["current_maturity_band"]:
                self.recommendations_by_band.setdefault(
                    record["current_maturity_band"],
                    [],
                ).append(
                    recommendation_id
                )

    # ========================================================================
    # CANDIDATES
    # ========================================================================

    def _find_candidates(
        self,
        dimension_id: str,
        band: str,
        gap: float,
        target_level: float,
        allowed_trigger_codes: set[str],
    ) -> list[str]:

        candidates: list[str] = []

        for recommendation_id in (
            self.recommendations_by_dimension.get(
                dimension_id,
                [],
            )
        ):

            record = self._records_by_id[
                recommendation_id
            ]

            record_band = (
                record["current_maturity_band"]
            )

            if (
                record_band
                and record_band != band
            ):
                continue

            if (
                gap
                < record["minimum_gap"]
            ):
                continue

            if not (
                record["target_level_min"]
                <= target_level
                <= record["target_level_max"]
            ):
                continue

            if (
                allowed_trigger_codes
                and record["gap_trigger_code"]
                and record["gap_trigger_code"]
                not in allowed_trigger_codes
            ):
                continue

            if not self._check_applicability(
                record
            ):
                continue

            candidates.append(
                recommendation_id
            )

        return candidates

    def _matching_trigger_codes(
        self,
        dimension_id: str,
        current_level: int,
        gap: float,
        target_level: float,
    ) -> set[str]:
        """
        Filters triggers from the TRIGGER_MAPPING sheet
        when the mapping is provided.
        """

        if (
            self.trigger_mapping.empty
            or "Gap_Trigger_Code"
            not in self.trigger_mapping.columns
        ):
            return set()

        matches: set[str] = set()

        for _, row in self.trigger_mapping.iterrows():

            if (
                self._text(
                    row.get("Dimension_ID")
                )
                not in {
                    "",
                    dimension_id,
                }
            ):
                continue

            if (
                current_level
                < self._number(
                    row.get(
                        "Current_Score_Min"
                    ),
                    0,
                )
            ):
                continue

            if (
                current_level
                > self._number(
                    row.get(
                        "Current_Score_Max"
                    ),
                    constants.SCORE_MAX,
                )
            ):
                continue

            if (
                gap
                < self._number(
                    row.get("Minimum_Gap"),
                    0,
                )
            ):
                continue

            if (
                target_level
                < self._number(
                    row.get(
                        "Target_Level_Min"
                    ),
                    0,
                )
            ):
                continue

            code = self._text(
                row.get(
                    "Gap_Trigger_Code"
                )
            )

            if code:
                matches.add(code)

        return matches

    # ========================================================================
    # RECORD CONVERSION
    # ========================================================================

    def _row_to_record(
        self,
        row: pd.Series,
    ) -> dict[str, Any]:

        return {
            "recommendation_id": self._text(
                row.get("Recommendation_ID")
            ),
            "title": self._text(
                row.get("Recommendation_Title")
            ),
            "pillar_id": self._text(
                row.get("Pillar_ID")
            ),
            "dimension_id": self._text(
                row.get("Dimension_ID")
            ),
            "gap_trigger_code": self._text(
                row.get("Gap_Trigger_Code")
            ),
            "current_maturity_band": self._text(
                row.get("Current_Maturity_Band")
            ),
            "minimum_gap": self._number(
                row.get("Minimum_Gap"),
                0,
            ),
            "target_level_min": self._number(
                row.get("Target_Level_Min"),
                0,
            ),
            "target_level_max": self._number(
                row.get("Target_Level_Max"),
                constants.SCORE_MAX,
            ),
            "typical_diagnosis": self._text(
                row.get("Typical_Diagnosis")
            ),
            "detailed_actions": self._parse_list(
                row.get("Detailed_Actions")
            ),
            "prerequisites": self._parse_list(
                row.get("Prerequisites")
            ),
            "dependencies": self._parse_list(
                row.get("Dependencies")
            ),
            "applicability_conditions": self._text(
                row.get(
                    "Applicability_Conditions"
                )
            ),
            "non_applicability_conditions": self._text(
                row.get(
                    "Non_Applicability_Conditions"
                )
            ),
            "expected_qualitative_impact": self._text(
                row.get(
                    "Expected_Qualitative_Impact"
                )
            ),
            "generic_effort": self._text(
                row.get(
                    "Generic_Effort"
                ),
                "Moderate",
            ),
            "indicative_horizon": self._text(
                row.get(
                    "Indicative_Horizon"
                ),
                "Medium term",
            ),
            "completion_evidence": self._parse_list(
                row.get(
                    "Completion_Evidence"
                )
            ),
            "source_reference": self._text(
                row.get(
                    "Source_Reference"
                )
            ),
        }

    def _create_recommendation_result(
        self,
        record: dict[str, Any],
        priority: str = "medium",
    ) -> RecommendationResult:

        return RecommendationResult(
            recommendation_id=record[
                "recommendation_id"
            ],
            title=record[
                "title"
            ],
            description=record[
                "typical_diagnosis"
            ],
            dimension_id=record[
                "dimension_id"
            ],
            pillar_id=record[
                "pillar_id"
            ],
            current_maturity_band=record[
                "current_maturity_band"
            ],
            gap_trigger_code=record[
                "gap_trigger_code"
            ],
            priority=priority,
            effort=record[
                "generic_effort"
            ],
            horizon=record[
                "indicative_horizon"
            ],
            detailed_actions=record[
                "detailed_actions"
            ],
            prerequisites=record[
                "prerequisites"
            ],
            dependencies=record[
                "dependencies"
            ],
            completion_evidence=record[
                "completion_evidence"
            ],
            expected_impact=record[
                "expected_qualitative_impact"
            ],
            source_reference=record[
                "source_reference"
            ],
        )

    # ========================================================================
    # APPLICABILITY
    # ========================================================================

    def _check_applicability(
        self,
        record: dict[str, Any],
    ) -> bool:
        """
        Applies explicit exclusions defined in the optional context.
        """

        condition = record[
            "applicability_conditions"
        ]

        exclusions = record[
            "non_applicability_conditions"
        ]

        if not condition and not exclusions:
            return True

        # An explicit context may provide conditions
        # that are already satisfied.
        excluded_codes = set(
            self.context.get(
                "excluded_recommendation_ids",
                [],
            )
        )

        return (
            record["recommendation_id"]
            not in excluded_codes
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _dimension_for_gap(
        gap_result: GapResult,
    ) -> Optional[str]:

        if (
            gap_result.entity_type
            == "dimension"
        ):
            return gap_result.entity_id

        return (
            gap_result.details or {}
        ).get(
            "dimension_id"
        )

    @staticmethod
    def _get_maturity_band(
        level: int,
    ) -> str:

        return constants.get_maturity_band(
            level
        )

    @staticmethod
    def _determine_priority(
        gap: float,
        tpi_result: Optional[TPIResult],
    ) -> str:

        if tpi_result is not None:

            labels = {
                "critique": "critical",
                "haute": "high",
                "moyenne": "medium",
                "faible": "low",
                "très faible": "low",
                "tres faible": "low",
            }

            return labels.get(
                str(
                    tpi_result.priority_category
                ).lower(),
                "medium",
            )

        if gap >= 2.0:
            return "critical"

        if gap >= 1.5:
            return "high"

        if gap >= 1.0:
            return "medium"

        return "low"

    @staticmethod
    def _text(
        value: Any,
        default: str = "",
    ) -> str:

        if value is None or (
            isinstance(value, float)
            and math.isnan(value)
        ):
            return default

        text = str(value).strip()

        return text or default

    @staticmethod
    def _number(
        value: Any,
        default: float,
    ) -> float:

        if value is None or (
            isinstance(value, float)
            and math.isnan(value)
        ):
            return float(default)

        try:
            numeric = float(value)

        except (
            TypeError,
            ValueError,
        ):
            return float(default)

        return (
            numeric
            if math.isfinite(numeric)
            else float(default)
        )

    @staticmethod
    def _parse_list(
        value: Any,
    ) -> list[str]:

        if isinstance(value, list):

            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        text = RecommendationEngine._text(
            value
        )

        if not text:
            return []

        return [
            re.sub(
                r"^\d+[.)]\s*",
                "",
                line,
            ).strip()
            for line in text.splitlines()
            if line.strip()
        ]


RecommendationEngine = RecommendationEngine