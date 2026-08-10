"""
loader.py — Transforme les classeurs Excel en objets Python (models.py).

Deux points d'entrée publics :
    load_referentiel(path=None) -> Referentiel
    load_assessment(path=None)  -> Assessment

Ce module fait uniquement de la LECTURE + un casting de types sûr
(safe_int/safe_float/safe_str). Il ne valide PAS la cohérence métier des
données (poids qui somment à 1, scores hors bornes, etc.) — c'est le rôle
de engines/assessment/validator.py, à l'étape suivante du guide.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from config.constants import RefSheets
from data.models import (
    Assessment,
    AssessmentMetadata,
    Dimension,
    DimensionMaturityLevel,
    EvidenceCatalogEntry,
    Indicator,
    IndicatorScore,
    IndicatorScoringGridEntry,
    MaturityLevelDescription,
    Pillar,
    Referentiel,
    Subdimension,
    WeightEntry,
)
from utils.excel_utils import (
    open_workbook,
    safe_float,
    safe_int,
    safe_str,
    sheet_to_keyvalue,
    sheet_to_records,
)

logger = settings.get_logger(__name__)


# ---------------------------------------------------------------------------
# CHARGEMENT DU RÉFÉRENTIEL
# ---------------------------------------------------------------------------


def load_referentiel(path: str | Path | None = None) -> Referentiel:
    """
    Charge le classeur référentiel JESA complet et retourne un objet
    Referentiel prêt à être utilisé par les engines de calcul.
    """
    path = Path(path) if path else settings.REFERENTIEL_FILE
    logger.info("Chargement du référentiel : %s", path)
    wb = open_workbook(path)

    referentiel = Referentiel()

    _load_hierarchy(wb, referentiel)
    _load_target_levels(wb, referentiel)
    _load_weights(wb, referentiel)
    _load_indicators(wb, referentiel)
    _load_generic_maturity_scale(wb, referentiel)
    _load_dimension_maturity_matrices(wb, referentiel)
    _load_indicator_scoring_grids(wb, referentiel)
    _load_evidence_catalog(wb, referentiel)

    logger.info(
        "Référentiel chargé : %d piliers, %d dimensions, %d sous-dimensions, %d indicateurs",
        len(referentiel.pillars),
        len(referentiel.dimensions),
        len(referentiel.subdimensions),
        len(referentiel.indicators),
    )
    return referentiel


def _load_hierarchy(wb, ref: Referentiel) -> None:
    """Feuille HIERARCHY -> Pillar, Dimension (partiel), Subdimension."""
    records = sheet_to_records(wb, RefSheets.HIERARCHY)

    pillars: dict[str, Pillar] = {}
    dimensions: dict[str, Dimension] = {}
    subdimensions: dict[str, Subdimension] = {}

    # On construit d'abord les sous-dimensions et on regroupe au passage
    # les IDs enfants pour peupler dimension_ids / subdimension_ids.
    dimension_to_subdims: dict[str, list[str]] = {}
    pillar_to_dims: dict[str, list[str]] = {}

    for r in records:
        pillar_id = safe_str(r.get("Pillar_ID"))
        dimension_id = safe_str(r.get("Dimension_ID"))
        subdimension_id = safe_str(r.get("Subdimension_ID"))

        if pillar_id and pillar_id not in pillars:
            pillars[pillar_id] = Pillar(id=pillar_id, name=safe_str(r.get("Pillar_Name"), ""))

        if dimension_id and dimension_id not in dimensions:
            dimensions[dimension_id] = Dimension(
                id=dimension_id,
                pillar_id=pillar_id,
                name=safe_str(r.get("Dimension_Name"), ""),
                objective=safe_str(r.get("Dimension_Objective"), ""),
            )
            pillar_to_dims.setdefault(pillar_id, []).append(dimension_id)

        if subdimension_id:
            subdimensions[subdimension_id] = Subdimension(
                id=subdimension_id,
                dimension_id=dimension_id,
                name=safe_str(r.get("Subdimension_Name"), ""),
                objective=safe_str(r.get("Subdimension_Objective"), ""),
                industrial_capability=safe_str(r.get("Industrial_Capability"), ""),
                main_risks=safe_str(r.get("Main_Risks_If_Weak"), ""),
            )
            dimension_to_subdims.setdefault(dimension_id, []).append(subdimension_id)

    # Recréer les dimensions/piliers en y injectant les tuples d'IDs enfants
    # (les dataclasses sont frozen -> on reconstruit plutôt que de muter).
    for dim_id, dim in list(dimensions.items()):
        dimensions[dim_id] = Dimension(
            id=dim.id,
            pillar_id=dim.pillar_id,
            name=dim.name,
            objective=dim.objective,
            subdimension_ids=tuple(dimension_to_subdims.get(dim_id, [])),
        )
    for pil_id, pil in list(pillars.items()):
        pillars[pil_id] = Pillar(
            id=pil.id, name=pil.name, dimension_ids=tuple(pillar_to_dims.get(pil_id, []))
        )

    # Ajouter les indicator_ids aux sous-dimensions se fait dans _load_indicators
    # (appelé après), on les fusionne là-bas.
    ref.pillars = pillars
    ref.dimensions = dimensions
    ref.subdimensions = subdimensions


def _load_target_levels(wb, ref: Referentiel) -> None:
    """Feuille TARGET_LEVELS -> complète les Dimension déjà créées avec les cibles."""
    records = sheet_to_records(wb, RefSheets.TARGET_LEVELS)
    for r in records:
        dim_id = safe_str(r.get("Dimension_ID"))

        # La feuille peut contenir une ligne d'instruction destinée à
        # l'utilisateur. Ce n'est pas une donnée de niveau cible.
        if not dim_id or dim_id.startswith("⚠"):
            continue

        if dim_id not in ref.dimensions:
            logger.warning("TARGET_LEVELS référence une dimension inconnue : %s", dim_id)
            continue
        existing = ref.dimensions[dim_id]
        ref.dimensions[dim_id] = Dimension(
            id=existing.id,
            pillar_id=existing.pillar_id,
            name=existing.name,
            objective=existing.objective,
            subdimension_ids=existing.subdimension_ids,
            target_level_default=safe_int(r.get("Target_Level_Default")),
            target_level_user=safe_int(r.get("Target_Level_User")),
            effective_target_level=safe_int(r.get("Effective_Target_Level")),
            target_level_description=safe_str(r.get("Target_Level_Description"), ""),
        )


def _load_weights(wb, ref: Referentiel) -> None:
    """Feuille WEIGHTS_CONFIGURATION -> ref.weights[hierarchy_level][component_id]."""
    records = sheet_to_records(wb, RefSheets.WEIGHTS_CONFIGURATION)
    weights: dict[str, dict[str, WeightEntry]] = {}
    for r in records:
        level = safe_str(r.get("Hierarchy_Level"))
        component_id = safe_str(r.get("Component_ID"))
        if not level or not component_id:
            continue
        entry = WeightEntry(
            hierarchy_level=level,
            parent_id=safe_str(r.get("Parent_ID"), ""),
            component_id=component_id,
            component_name=safe_str(r.get("Component_Name"), ""),
            default_weight=safe_float(r.get("Default_Weight"), 0.0),
            user_defined_weight=safe_float(r.get("User_Defined_Weight")),
            effective_weight=safe_float(r.get("Effective_Weight")),
            weight_source=safe_str(r.get("Weight_Source"), ""),
            justification=safe_str(r.get("Justification"), ""),
            validation_status=safe_str(r.get("Validation_Status"), ""),
        )
        weights.setdefault(level, {})[component_id] = entry
    ref.weights = weights


def _load_indicators(wb, ref: Referentiel) -> None:
    """Feuille INDICATORS -> Indicator, et complète Subdimension.indicator_ids."""
    records = sheet_to_records(wb, RefSheets.INDICATORS)
    indicators: dict[str, Indicator] = {}
    subdim_to_indicators: dict[str, list[str]] = {}

    for r in records:
        indicator_id = safe_str(r.get("Indicator_ID"))
        if not indicator_id:
            continue
        subdimension_id = safe_str(r.get("Subdimension_ID"))
        indicators[indicator_id] = Indicator(
            id=indicator_id,
            pillar_id=safe_str(r.get("Pillar_ID"), ""),
            dimension_id=safe_str(r.get("Dimension_ID"), ""),
            subdimension_id=subdimension_id,
            name=safe_str(r.get("Indicator_Name"), ""),
            objective=safe_str(r.get("Indicator_Objective"), ""),
            question=safe_str(r.get("Assessment_Question"), ""),
            indicator_type=safe_str(r.get("Indicator_Type"), ""),
            measurement_mode=safe_str(r.get("Measurement_Mode"), ""),
            expected_respondent=safe_str(r.get("Expected_Respondent"), ""),
            perimeter=safe_str(r.get("Assessment_Perimeter"), ""),
            applicability_condition=safe_str(r.get("Applicability_Condition"), ""),
            evidence_category=safe_str(r.get("Required_Evidence_Category"), ""),
            gap_trigger_code=safe_str(r.get("Gap_Trigger_Code"), ""),
            source_reference=safe_str(r.get("Source_Reference"), ""),
            assumptions=safe_str(r.get("Assumptions"), ""),
            validation_status=safe_str(r.get("Expert_Validation_Status"), ""),
        )
        if subdimension_id:
            subdim_to_indicators.setdefault(subdimension_id, []).append(indicator_id)

    for sd_id, sd in list(ref.subdimensions.items()):
        ref.subdimensions[sd_id] = Subdimension(
            id=sd.id,
            dimension_id=sd.dimension_id,
            name=sd.name,
            objective=sd.objective,
            industrial_capability=sd.industrial_capability,
            main_risks=sd.main_risks,
            indicator_ids=tuple(subdim_to_indicators.get(sd_id, [])),
        )

    ref.indicators = indicators


def _load_generic_maturity_scale(wb, ref: Referentiel) -> None:
    records = sheet_to_records(wb, RefSheets.GENERIC_MATURITY_SCALE)
    scale: dict[int, MaturityLevelDescription] = {}
    for r in records:
        level = safe_int(r.get("Level"))
        if level is None:
            continue
        scale[level] = MaturityLevelDescription(
            level=level,
            name=safe_str(r.get("Level_Name"), ""),
            generic_description=safe_str(r.get("Generic_Description"), ""),
            generic_evaluation_principle=safe_str(r.get("Generic_Evaluation_Principle"), ""),
            minimum_evidence_principle=safe_str(r.get("Minimum_Evidence_Principle"), ""),
        )
    ref.maturity_scale = scale


def _load_dimension_maturity_matrices(wb, ref: Referentiel) -> None:
    records = sheet_to_records(wb, RefSheets.DIMENSION_MATURITY_MATRICES)
    matrices: dict[str, dict[int, DimensionMaturityLevel]] = {}
    for r in records:
        dim_id = safe_str(r.get("Dimension_ID"))
        level = safe_int(r.get("Level"))
        if not dim_id or level is None:
            continue
        entry = DimensionMaturityLevel(
            dimension_id=dim_id,
            level=level,
            level_name=safe_str(r.get("Level_Name"), ""),
            description=safe_str(r.get("Dimension_Level_Description"), ""),
            key_capabilities_expected=safe_str(r.get("Key_Capabilities_Expected"), ""),
            typical_observed_state=safe_str(r.get("Typical_Observed_State"), ""),
            minimum_conditions=safe_str(r.get("Minimum_Conditions"), ""),
            possible_evidence=safe_str(r.get("Possible_Evidence"), ""),
            main_limit_preventing_next_level=safe_str(
                r.get("Main_Limit_Preventing_Next_Level"), ""
            ),
            recommended_target_use=safe_str(r.get("Recommended_Target_Use"), ""),
        )
        matrices.setdefault(dim_id, {})[level] = entry
    ref.dimension_maturity_matrices = matrices


def _load_indicator_scoring_grids(wb, ref: Referentiel) -> None:
    records = sheet_to_records(wb, RefSheets.INDICATOR_SCORING_GRIDS)
    grids: dict[str, dict[int, IndicatorScoringGridEntry]] = {}
    for r in records:
        indicator_id = safe_str(r.get("Indicator_ID"))
        score = safe_int(r.get("Score"))
        if not indicator_id or score is None:
            continue
        entry = IndicatorScoringGridEntry(
            indicator_id=indicator_id,
            score=score,
            score_label=safe_str(r.get("Score_Label"), ""),
            observable_situation=safe_str(r.get("Observable_Situation"), ""),
            mandatory_criteria=safe_str(r.get("Mandatory_Criteria"), ""),
            possible_evidence=safe_str(r.get("Possible_Evidence"), ""),
            disqualifying_conditions=safe_str(r.get("Disqualifying_Conditions"), ""),
            evaluator_guidance=safe_str(r.get("Evaluator_Guidance"), ""),
            next_score_requirement=safe_str(r.get("Next_Score_Requirement"), ""),
        )
        grids.setdefault(indicator_id, {})[score] = entry
    ref.indicator_scoring_grids = grids


def _load_evidence_catalog(wb, ref: Referentiel) -> None:
    records = sheet_to_records(wb, RefSheets.EVIDENCE_CATALOG)
    catalog: dict[str, EvidenceCatalogEntry] = {}
    for r in records:
        evidence_id = safe_str(r.get("Evidence_ID"))
        if not evidence_id:
            continue
        catalog[evidence_id] = EvidenceCatalogEntry(
            id=evidence_id,
            category=safe_str(r.get("Evidence_Category"), ""),
            name=safe_str(r.get("Evidence_Name"), ""),
            description=safe_str(r.get("Evidence_Description"), ""),
            applicable_dimensions=safe_str(r.get("Applicable_Dimensions"), ""),
            reliability_level=safe_str(r.get("Reliability_Level"), ""),
            example=safe_str(r.get("Example"), ""),
            confidentiality_considerations=safe_str(
                r.get("Confidentiality_Considerations"), ""
            ),
        )
    ref.evidence_catalog = catalog


# ---------------------------------------------------------------------------
# CHARGEMENT D'UNE ÉVALUATION (Assessment.xlsx)
# ---------------------------------------------------------------------------


def load_assessment(path: str | Path | None = None) -> Assessment:
    """
    Charge un classeur Assessment.xlsx (structure ASSESSMENT_METADATA +
    QUESTIONNAIRE_TEMPLATE rempli par l'évaluateur) et retourne un objet
    Assessment prêt pour engines/assessment/validator.py.
    """
    path = Path(path) if path else settings.ASSESSMENT_FILE
    logger.info("Chargement de l'évaluation : %s", path)
    wb = open_workbook(path)

    metadata = _load_assessment_metadata(wb)
    indicator_scores = _load_indicator_scores(wb)

    assessment = Assessment(metadata=metadata, indicator_scores=indicator_scores)
    logger.info(
        "Évaluation chargée : %s indicateurs, %d notés",
        len(indicator_scores),
        sum(1 for s in indicator_scores.values() if s.is_scored),
    )
    return assessment


def _load_assessment_metadata(wb) -> AssessmentMetadata:
    kv = sheet_to_keyvalue(wb, RefSheets.ASSESSMENT_METADATA)
    return AssessmentMetadata(
        assessment_id=safe_str(kv.get("Assessment_ID"), "UNKNOWN"),
        site_id=safe_str(kv.get("Site_ID")),
        site_name=safe_str(kv.get("Site_Name")),
        industrial_sector=safe_str(kv.get("Industrial_Sector")),
        plant_unit=safe_str(kv.get("Plant_Unit")),
        location=safe_str(kv.get("Location")),
        assessment_date=safe_str(kv.get("Assessment_Date")),
        evaluator_name=safe_str(kv.get("Evaluator_Name")),
        evaluator_function=safe_str(kv.get("Evaluator_Function")),
        assessment_version=safe_str(kv.get("Assessment_Version")),
        reference_framework_version=safe_str(kv.get("Reference_Framework_Version")),
        general_comments=safe_str(kv.get("General_Comments")),
    )


def _load_indicator_scores(wb) -> dict[str, IndicatorScore]:
    records = sheet_to_records(wb, RefSheets.QUESTIONNAIRE_TEMPLATE)
    scores: dict[str, IndicatorScore] = {}
    for r in records:
        indicator_id = safe_str(r.get("Indicator_ID"))
        if not indicator_id:
            continue
        scores[indicator_id] = IndicatorScore(
            indicator_id=indicator_id,
            pillar_id=safe_str(r.get("Pillar_ID"), ""),
            dimension_id=safe_str(r.get("Dimension_ID"), ""),
            subdimension_id=safe_str(r.get("Subdimension_ID"), ""),
            question=safe_str(r.get("Assessment_Question"), ""),
            selected_score=safe_int(r.get("Selected_Score")),
            evidence_reference=safe_str(r.get("Evidence_Reference")),
            evaluator_comment=safe_str(r.get("Evaluator_Comment")),
            confidence_level=safe_str(r.get("Confidence_Level")),
            applicability=safe_str(r.get("Applicability"), "Applicable"),
            validation_status=safe_str(r.get("Validation_Status"), "Brouillon"),
        )
    return scores
