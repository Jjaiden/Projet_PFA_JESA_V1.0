"""JDMAF maturity gap analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from config import constants
from engines.assessment.scoring import ScoreResult


@dataclass
class GapResult:
    """Gap result for a hierarchy entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    current_score: float
    target_score: float
    gap: float
    gap_percent: float
    priority: str
    details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "current_score": round(self.current_score, 2),
            "target_score": round(self.target_score, 2),
            "gap": round(self.gap, 2),
            "gap_percent": round(self.gap_percent, 1),
            "priority": self.priority,
            "details": self.details,
        }


class GapAnalysisEngine:
    """Calculate gaps between current scores and target maturity levels."""

    def __init__(self, config: Optional[Mapping[str, Any]] = None):
        self.config = dict(config or {})

        self.default_target_level = self._validate_target(
            self.config.get("default_target_level", 3)
        )

        self.gap_thresholds = self._validate_thresholds(
            self.config.get(
                "gap_thresholds",
                constants.GAP_THRESHOLDS,
            )
        )

    def calculate_dimension_gaps(
        self,
        dimension_scores: Mapping[str, ScoreResult],
        target_levels: Mapping[str, int],
    ) -> list[GapResult]:
        """Calculate gaps for applicable dimensions."""

        return self._calculate_gaps(
            scores=dimension_scores,
            entity_type="dimension",
            target_resolver=lambda entity_id, _: self._target_for_dimension(
                entity_id,
                target_levels,
            ),
        )

    def calculate_subdimension_gaps(
        self,
        subdimension_scores: Mapping[str, ScoreResult],
        target_levels: Mapping[str, int],
    ) -> list[GapResult]:
        """Calculate subdimension gaps based on their dimension target."""

        return self._calculate_gaps(
            scores=subdimension_scores,
            entity_type="subdimension",
            target_resolver=lambda entity_id, result: self._target_for_dimension(
                self._dimension_for_subdimension(
                    entity_id,
                    result,
                ),
                target_levels,
            ),
        )

    def calculate_indicator_gaps(
        self,
        indicator_scores: Mapping[str, ScoreResult],
        target_levels: Mapping[str, int],
    ) -> list[GapResult]:
        """Calculate indicator gaps based on their dimension target."""

        return self._calculate_gaps(
            scores=indicator_scores,
            entity_type="indicator",
            target_resolver=lambda entity_id, result: self._target_for_dimension(
                self._dimension_for_indicator(
                    entity_id,
                    result,
                ),
                target_levels,
            ),
        )

    def calculate_pillar_gaps(
        self,
        pillar_scores: Mapping[str, ScoreResult],
        target_levels: Mapping[str, int],
    ) -> list[GapResult]:
        """Calculate pillar gaps using the average target of their dimensions."""

        pillar_targets = self._calculate_pillar_targets(
            target_levels
        )

        return self._calculate_gaps(
            scores=pillar_scores,
            entity_type="pillar",
            target_resolver=lambda entity_id, _: pillar_targets.get(
                entity_id,
                float(self.default_target_level),
            ),
        )

    def _calculate_gaps(
        self,
        scores,
        entity_type,
        target_resolver,
    ) -> list[GapResult]:
        """Calculate maturity gaps for the provided entities."""

        results: list[GapResult] = []

        for entity_id, score_result in scores.items():

            if (
                score_result.applicability
                == constants.APPLICABILITY_NOT_APPLICABLE
            ):
                continue

            target = float(
                target_resolver(
                    entity_id,
                    score_result,
                )
            )

            current = float(
                score_result.score
            )

            gap = max(
                0.0,
                target - current,
            )

            results.append(
                GapResult(
                    entity_id=entity_id,
                    entity_name=score_result.entity_name,
                    entity_type=entity_type,
                    current_score=current,
                    target_score=target,
                    gap=gap,
                    gap_percent=(
                        gap
                        / constants.SCORE_MAX
                    )
                    * 100,
                    priority=self._determine_priority(
                        gap
                    ),
                    details={
                        "current_level": score_result.level,
                        "target_level": target,
                        "dimension_id": self._dimension_for_result(
                            entity_id,
                            score_result,
                            entity_type,
                        ),
                        "current_level_name": score_result.level_name,
                        "target_level_name": self._get_level_name(
                            target
                        ),
                        "children_scores": score_result.children_scores,
                    },
                )
            )

        return sorted(
            results,
            key=lambda result: result.gap,
            reverse=True,
        )

    def get_critical_gaps(
        self,
        gap_results: list[GapResult],
    ) -> list[GapResult]:
        """Return critical and high-priority gaps."""

        return [
            gap
            for gap in gap_results
            if gap.priority
            in {
                "critical",
                "high",
            }
        ]

    def get_gap_summary(
        self,
        gap_results: list[GapResult],
    ) -> dict[str, Any]:
        """Return a summary of maturity gaps by priority."""

        counts = {
            priority: sum(
                1
                for gap in gap_results
                if gap.priority == priority
            )
            for priority in (
                "critical",
                "high",
                "medium",
                "low",
                "none",
            )
        }

        return {
            "total_gaps": len(gap_results),
            "critical_count": counts["critical"],
            "high_count": counts["high"],
            "medium_count": counts["medium"],
            "low_count": counts["low"],
            "no_gap_count": counts["none"],
            "average_gap": (
                round(
                    sum(
                        gap.gap
                        for gap in gap_results
                    )
                    / len(gap_results),
                    2,
                )
                if gap_results
                else 0.0
            ),
            "max_gap": round(
                max(
                    (
                        gap.gap
                        for gap in gap_results
                    ),
                    default=0.0,
                ),
                2,
            ),
            "gaps_by_priority": counts,
        }

    def _target_for_dimension(
        self,
        dimension_id: Optional[str],
        targets: Mapping[str, int],
    ) -> int:
        """Resolve the target maturity level for a dimension."""

        return self._validate_target(
            targets.get(
                dimension_id,
                self.default_target_level,
            )
        )

    def _dimension_for_subdimension(
        self,
        subdimension_id: str,
        result: ScoreResult,
    ) -> Optional[str]:
        """Resolve the parent dimension of a subdimension."""

        return (
            result.parent_id
            or constants.SUBDIMENSION_TO_DIMENSION.get(
                subdimension_id
            )
        )

    def _dimension_for_indicator(
        self,
        indicator_id: str,
        result: ScoreResult,
    ) -> Optional[str]:
        """Resolve the parent dimension of an indicator."""

        subdimension_id = result.parent_id

        if subdimension_id:
            return constants.SUBDIMENSION_TO_DIMENSION.get(
                subdimension_id
            )

        # Indicator IDs follow the I-D{n}-{nn} format.
        parts = indicator_id.split("-")

        return (
            parts[1]
            if len(parts) >= 3
            and parts[1] in constants.DIMENSIONS
            else None
        )

    def _dimension_for_result(
        self,
        entity_id: str,
        result: ScoreResult,
        entity_type: str,
    ) -> Optional[str]:
        """Resolve the dimension associated with an entity."""

        if entity_type == "dimension":
            return entity_id

        if entity_type == "subdimension":
            return self._dimension_for_subdimension(
                entity_id,
                result,
            )

        if entity_type == "indicator":
            return self._dimension_for_indicator(
                entity_id,
                result,
            )

        return None

    def _calculate_pillar_targets(
        self,
        targets: Mapping[str, int],
    ) -> dict[str, float]:
        """Calculate pillar target levels from their dimension targets."""

        pillar_targets: dict[str, float] = {}

        for (
            pillar_id,
            dimension_ids,
        ) in constants.PILLAR_TO_DIMENSIONS.items():

            values = [
                self._target_for_dimension(
                    dimension_id,
                    targets,
                )
                for dimension_id in dimension_ids
            ]

            pillar_targets[pillar_id] = (
                sum(values) / len(values)
            )

        return pillar_targets

    def _determine_priority(
        self,
        gap: float,
    ) -> str:
        """Determine the priority level associated with a maturity gap."""

        if gap <= 0:
            return "none"

        for priority in (
            "critical",
            "high",
            "medium",
            "low",
        ):
            if gap >= self.gap_thresholds[priority]:
                return priority

        return "low"

    @staticmethod
    def _validate_target(
        target: Any,
    ) -> int:
        """Validate a target maturity level."""

        if (
            isinstance(target, bool)
            or not isinstance(
                target,
                (int, float),
            )
        ):
            raise ValueError(
                f"Invalid target maturity level: {target!r}"
            )

        if (
            isinstance(target, float)
            and not target.is_integer()
        ):
            raise ValueError(
                f"Target maturity level must be an integer: {target!r}"
            )

        target = int(target)

        if (
            target
            not in constants.VALID_INDICATOR_SCORES
        ):
            raise ValueError(
                f"Target maturity level out of range: {target}"
            )

        return target

    @staticmethod
    def _validate_thresholds(
        values: Mapping[str, Any],
    ) -> dict[str, float]:
        """Validate maturity gap priority thresholds."""

        required = (
            "critical",
            "high",
            "medium",
            "low",
        )

        if any(
            key not in values
            for key in required
        ):
            raise ValueError(
                "Gap thresholds must contain "
                "critical, high, medium, and low."
            )

        thresholds = {
            key: float(values[key])
            for key in required
        }

        if not (
            thresholds["critical"]
            >= thresholds["high"]
            >= thresholds["medium"]
            >= thresholds["low"]
            > 0
        ):
            raise ValueError(
                "Gap thresholds must be in descending order "
                "and strictly positive."
            )

        return thresholds

    @staticmethod
    def _get_level_name(
        level: float,
    ) -> str:
        """Return the display name of a maturity level."""

        if float(level).is_integer():
            return constants.MATURITY_LEVELS.get(
                int(level),
                f"Level {int(level)}",
            )

        return (
            f"Average target level {level:.2f}"
        )


GapEngine = GapAnalysisEngine