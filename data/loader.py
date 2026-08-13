# data/loader.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from config import constants, settings
from config.constants import RefSheets
from data.models import (
    Assessment,
    AssessmentMetadata,
    Dimension,
    DimensionMaturityLevel,
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
    group_records_by,
    open_workbook,
    safe_float,
    safe_int,
    safe_str,
    sheet_to_keyvalue,
    sheet_to_records,
)


def load_referentiel(
    file_path: Optional[Path] = None,
) -> Referentiel:
    """
    Load the complete referentiel from the Excel workbook.
    Uses settings.REFERENTIEL_FILE by default.
    """
    if file_path is None:
        file_path = settings.REFERENTIEL_FILE

    if not file_path.exists():
        raise FileNotFoundError(f"Referentiel file not found: {file_path}")

    wb = open_workbook(file_path)

    # ----------------------------------------------------------------
    # 1. Generic maturity scale
    # ----------------------------------------------------------------
    maturity_scale = _load_generic_maturity_scale(wb)

    # ----------------------------------------------------------------
    # 2. Hierarchy (pillars, dimensions, subdimensions)
    # ----------------------------------------------------------------
    pillars, dimensions, subdimensions = _load_hierarchy(wb)

    # ----------------------------------------------------------------
    # 3. Indicators (returns also the mapping subdim -> indicator ids)
    # ----------------------------------------------------------------
    indicators, subdim_to_indicators = _load_indicators(wb)

    # Update subdimensions with their indicator IDs
    for sub_id, ind_ids in subdim_to_indicators.items():
        if sub_id in subdimensions:
            subdimensions[sub_id] = Subdimension(
                id=subdimensions[sub_id].id,
                dimension_id=subdimensions[sub_id].dimension_id,
                name=subdimensions[sub_id].name,
                objective=subdimensions[sub_id].objective,
                industrial_capability=subdimensions[sub_id].industrial_capability,
                main_risks=subdimensions[sub_id].main_risks,
                indicator_ids=tuple(ind_ids),   # <-- on remplit enfin la liste
            )

    # ----------------------------------------------------------------
    # 4. Dimension maturity matrices
    # ----------------------------------------------------------------
    dimension_maturity_matrices = _load_dimension_maturity_matrices(wb)

    # ----------------------------------------------------------------
    # 5. Indicator scoring grids
    # ----------------------------------------------------------------
    indicator_scoring_grids = _load_indicator_scoring_grids(wb)

    # ----------------------------------------------------------------
    # 6. Weights configuration
    # ----------------------------------------------------------------
    weights = _load_weights(wb)

    # ----------------------------------------------------------------
    # 7. Target levels
    # ----------------------------------------------------------------
    target_levels = _load_target_levels(wb)

    # ----------------------------------------------------------------
    # 8. Assessment metadata (for reference version)
    # ----------------------------------------------------------------
    metadata = _load_ref_metadata(wb)

    return Referentiel(
        pillars=pillars,
        dimensions=dimensions,
        subdimensions=subdimensions,
        indicators=indicators,
        maturity_scale=maturity_scale,
        dimension_maturity_matrices=dimension_maturity_matrices,
        indicator_scoring_grids=indicator_scoring_grids,
        weights=weights,
        target_levels=target_levels,
        metadata=metadata,
    )


def load_assessment(file_path: Path) -> Assessment:
    """Load assessment data from the uploaded Excel file."""
    wb = open_workbook(file_path)

    # Metadata
    metadata_dict = sheet_to_keyvalue(wb, RefSheets.ASSESSMENT_METADATA)
    metadata = AssessmentMetadata(
        assessment_id=safe_str(metadata_dict.get("Assessment_ID"), "UNKNOWN"),
        site_id=safe_str(metadata_dict.get("Site_ID")),
        site_name=safe_str(metadata_dict.get("Site_Name")),
        industrial_sector=safe_str(metadata_dict.get("Industrial_Sector")),
        plant_unit=safe_str(metadata_dict.get("Plant_Unit")),
        location=safe_str(metadata_dict.get("Location")),
        assessment_date=safe_str(metadata_dict.get("Assessment_Date")),
        evaluator_name=safe_str(metadata_dict.get("Evaluator_Name")),
        evaluator_function=safe_str(metadata_dict.get("Evaluator_Function")),
        assessment_version=safe_str(metadata_dict.get("Assessment_Version")),
        reference_framework_version=safe_str(metadata_dict.get("Reference_Framework_Version")),
        general_comments=safe_str(metadata_dict.get("General_Comments")),
    )

    # Indicator scores from QUESTIONNAIRE_TEMPLATE
    records = sheet_to_records(wb, RefSheets.QUESTIONNAIRE_TEMPLATE)
    indicator_scores: Dict[str, IndicatorScore] = {}
    for rec in records:
        ind_id = safe_str(rec.get("Indicator_ID"))
        if not ind_id:
            continue
        score_val = rec.get("Selected_Score")
        # handle possible numeric or string
        selected_score = safe_int(score_val) if score_val is not None else None
        applicability = safe_str(rec.get("Applicability"), constants.APPLICABILITY_APPLICABLE)
        indicator_scores[ind_id] = IndicatorScore(
            indicator_id=ind_id,
            pillar_id=safe_str(rec.get("Pillar_ID")),
            dimension_id=safe_str(rec.get("Dimension_ID")),
            subdimension_id=safe_str(rec.get("Subdimension_ID")),
            selected_score=selected_score,
            applicability=applicability,
            evidence_reference=safe_str(rec.get("Evidence_Reference")),
            evaluator_comment=safe_str(rec.get("Evaluator_Comment")),
            confidence_level=safe_str(rec.get("Confidence_Level")),
            validation_status=safe_str(rec.get("Validation_Status")),
        )

    return Assessment(metadata=metadata, indicator_scores=indicator_scores)


# ------------------------------------------------------------------
# Internal loaders
# ------------------------------------------------------------------

def _load_generic_maturity_scale(wb) -> Dict[int, MaturityLevelDescription]:
    records = sheet_to_records(wb, RefSheets.GENERIC_MATURITY_SCALE)
    scale: Dict[int, MaturityLevelDescription] = {}
    for rec in records:
        level = safe_int(rec.get("Level"))
        if level is None:
            continue
        scale[level] = MaturityLevelDescription(
            level=level,
            name=safe_str(rec.get("Level_Name"), f"Level {level}"),
            generic_description=safe_str(rec.get("Generic_Description")),
            generic_evaluation_principle=safe_str(rec.get("Generic_Evaluation_Principle")),
            minimum_evidence_principle=safe_str(rec.get("Minimum_Evidence_Principle")),
        )
    return scale


def _load_hierarchy(wb) -> tuple[Dict[str, Pillar], Dict[str, Dimension], Dict[str, Subdimension]]:
    records = sheet_to_records(wb, RefSheets.HIERARCHY)
    # We'll group by pillar and dimension to build objects
    pillars: Dict[str, Pillar] = {}
    dimensions: Dict[str, Dimension] = {}
    subdimensions: Dict[str, Subdimension] = {}

    # First, collect unique pillars and dimensions
    pillar_names: Dict[str, str] = {}
    dimension_names: Dict[str, str] = {}
    dim_to_pillar: Dict[str, str] = {}
    subdim_to_dim: Dict[str, str] = {}
    subdim_names: Dict[str, str] = {}

    for rec in records:
        pillar_id = safe_str(rec.get("Pillar_ID"))
        pillar_name = safe_str(rec.get("Pillar_Name"))
        if pillar_id and pillar_name:
            pillar_names[pillar_id] = pillar_name

        dim_id = safe_str(rec.get("Dimension_ID"))
        dim_name = safe_str(rec.get("Dimension_Name"))
        if dim_id and dim_name:
            dimension_names[dim_id] = dim_name
            if pillar_id:
                dim_to_pillar[dim_id] = pillar_id

        sub_id = safe_str(rec.get("Subdimension_ID"))
        sub_name = safe_str(rec.get("Subdimension_Name"))
        if sub_id and sub_name:
            subdim_names[sub_id] = sub_name
            if dim_id:
                subdim_to_dim[sub_id] = dim_id

    # Build pillars with their dimension IDs
    for pid, pname in pillar_names.items():
        dim_ids = [did for did, pid2 in dim_to_pillar.items() if pid2 == pid]
        pillars[pid] = Pillar(id=pid, name=pname, dimension_ids=tuple(dim_ids))

    # Build dimensions with their subdimension IDs
    for did, dname in dimension_names.items():
        sub_ids = [sid for sid, pid2 in subdim_to_dim.items() if pid2 == did]
        dimensions[did] = Dimension(
            id=did,
            name=dname,
            pillar_id=dim_to_pillar.get(did),
            subdimension_ids=tuple(sub_ids),
            target_level_default=None,    # loaded later from TARGET_LEVELS
            target_level_user=None,
            effective_target_level=None,
        )

    # Build subdimensions with empty indicator_ids (will be populated later)
    for sid, sname in subdim_names.items():
        subdimensions[sid] = Subdimension(
            id=sid,
            name=sname,
            dimension_id=subdim_to_dim.get(sid),
            indicator_ids=tuple(),   # will be populated from INDICATORS sheet
        )

    return pillars, dimensions, subdimensions


def _load_indicators(wb) -> tuple[Dict[str, Indicator], Dict[str, List[str]]]:
    records = sheet_to_records(wb, RefSheets.INDICATORS)
    indicators: Dict[str, Indicator] = {}
    subdim_to_indicators: Dict[str, List[str]] = {}
    for rec in records:
        ind_id = safe_str(rec.get("Indicator_ID"))
        if not ind_id:
            continue
        sub_id = safe_str(rec.get("Subdimension_ID"))
        if sub_id:
            subdim_to_indicators.setdefault(sub_id, []).append(ind_id)
        indicators[ind_id] = Indicator(
            id=ind_id,
            name=safe_str(rec.get("Indicator_Name")),
            pillar_id=safe_str(rec.get("Pillar_ID")),
            dimension_id=safe_str(rec.get("Dimension_ID")),
            subdimension_id=sub_id,
            objective=safe_str(rec.get("Indicator_Objective")),
            question=safe_str(rec.get("Assessment_Question")),
            indicator_type=safe_str(rec.get("Indicator_Type")),
            measurement_mode=safe_str(rec.get("Measurement_Mode")),
            expected_respondent=safe_str(rec.get("Expected_Respondent")),
            perimeter=safe_str(rec.get("Assessment_Perimeter")),
            applicability_condition=safe_str(rec.get("Applicability_Condition")),
            evidence_category=safe_str(rec.get("Required_Evidence_Category")),
            gap_trigger_code=safe_str(rec.get("Gap_Trigger_Code")),
            source_reference=safe_str(rec.get("Source_Reference")),
            assumptions=safe_str(rec.get("Assumptions")),
            validation_status=safe_str(rec.get("Expert_Validation_Status")),
        )
    return indicators, subdim_to_indicators


def _load_dimension_maturity_matrices(wb) -> Dict[str, Dict[int, DimensionMaturityLevel]]:
    records = sheet_to_records(wb, RefSheets.DIMENSION_MATURITY_MATRICES)
    matrices: Dict[str, Dict[int, DimensionMaturityLevel]] = {}
    for rec in records:
        dim_id = safe_str(rec.get("Dimension_ID"))
        level = safe_int(rec.get("Level"))
        if not dim_id or level is None:
            continue
        if dim_id not in matrices:
            matrices[dim_id] = {}
        matrices[dim_id][level] = DimensionMaturityLevel(
            dimension_id=dim_id,
            level=level,
            level_name=safe_str(rec.get("Level_Name")),
            description=safe_str(rec.get("Dimension_Level_Description")),
            key_capabilities_expected=safe_str(rec.get("Key_Capabilities_Expected")),
            typical_observed_state=safe_str(rec.get("Typical_Observed_State")),
            minimum_conditions=safe_str(rec.get("Minimum_Conditions")),
            possible_evidence=safe_str(rec.get("Possible_Evidence")),
            main_limit_preventing_next_level=safe_str(rec.get("Main_Limit_Preventing_Next_Level")),
            recommended_target_use=safe_str(rec.get("Recommended_Target_Use")),
        )
    return matrices


def _load_indicator_scoring_grids(wb) -> Dict[str, Dict[int, IndicatorScoringGridEntry]]:
    records = sheet_to_records(wb, RefSheets.INDICATOR_SCORING_GRIDS)
    grids: Dict[str, Dict[int, IndicatorScoringGridEntry]] = {}
    for rec in records:
        ind_id = safe_str(rec.get("Indicator_ID"))
        score = safe_int(rec.get("Score"))
        if not ind_id or score is None:
            continue
        if ind_id not in grids:
            grids[ind_id] = {}
        grids[ind_id][score] = IndicatorScoringGridEntry(
            indicator_id=ind_id,
            score=score,
            score_label=safe_str(rec.get("Score_Label")),
            observable_situation=safe_str(rec.get("Observable_Situation")),
            mandatory_criteria=safe_str(rec.get("Mandatory_Criteria")),
            possible_evidence=safe_str(rec.get("Possible_Evidence")),
            disqualifying_conditions=safe_str(rec.get("Disqualifying_Conditions")),
            evaluator_guidance=safe_str(rec.get("Evaluator_Guidance")),
            next_score_requirement=safe_str(rec.get("Next_Score_Requirement")),
            source_reference=safe_str(rec.get("Source_Reference")),
            expert_validation_status=safe_str(rec.get("Expert_Validation_Status")),
        )
    return grids


def _load_weights(wb) -> Dict[str, Dict[str, WeightEntry]]:
    records = sheet_to_records(wb, RefSheets.WEIGHTS_CONFIGURATION)
    weights: Dict[str, Dict[str, WeightEntry]] = {}
    for rec in records:
        hierarchy_level = safe_str(rec.get("Hierarchy_Level"))
        component_id = safe_str(rec.get("Component_ID"))
        if not hierarchy_level or not component_id:
            continue
        if hierarchy_level not in weights:
            weights[hierarchy_level] = {}
        weights[hierarchy_level][component_id] = WeightEntry(
            hierarchy_level=hierarchy_level,
            parent_id=safe_str(rec.get("Parent_ID")),
            component_id=component_id,
            component_name=safe_str(rec.get("Component_Name")),
            default_weight=safe_float(rec.get("Default_Weight"), 0.0),
            user_defined_weight=safe_float(rec.get("User_Defined_Weight")),
            effective_weight=safe_float(rec.get("Effective_Weight"), 0.0),
            weight_source=safe_str(rec.get("Weight_Source")),
            justification=safe_str(rec.get("Justification")),
            validation_status=safe_str(rec.get("Validation_Status")),
        )
    return weights


def _load_target_levels(wb) -> Dict[str, int]:
    records = sheet_to_records(wb, RefSheets.TARGET_LEVELS)
    targets: Dict[str, int] = {}
    for rec in records:
        dim_id = safe_str(rec.get("Dimension_ID"))
        effective = safe_int(rec.get("Effective_Target_Level"))
        if dim_id and effective is not None:
            targets[dim_id] = effective
    return targets


def _load_ref_metadata(wb) -> Dict[str, Any]:
    metadata = sheet_to_keyvalue(wb, RefSheets.ASSESSMENT_METADATA)
    return {
        "reference_framework_version": safe_str(metadata.get("Reference_Framework_Version")),
    }