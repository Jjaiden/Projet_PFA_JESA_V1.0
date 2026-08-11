"""
app.py — JESA DMAT Frontend Entrypoint (Streamlit) & Backend CLI

This file serves two purposes:

1. When run with `streamlit run app.py`, it acts as the frontend
   router using Streamlit's multipage navigation.
2. When run with `python app.py`, it executes the original CLI
   backend pipeline.

The backend logic (AssessmentPipeline, CLI) is preserved.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from config import settings
from data.loader import load_referentiel, load_assessment
from data.models import Assessment, Referentiel
from engines.assessment.aggregation import AggregationEngine
from engines.assessment.validator import validate_assessment, ensure_valid
from engines.decision.gap import GapAnalysisEngine
from engines.decision.tpi import TPIEngine
from engines.decision.priority import PriorityEngine
from engines.decision.recommendation import RecommendationEngine
from engines.decision.roadmap import RoadmapEngine
from utils.file_manager import ensure_directory, build_output_path

logger = settings.get_logger(__name__)


# =============================================================================
# STREAMLIT FRONTEND SHELL
# =============================================================================

import streamlit as st


# 1. Page configuration
st.set_page_config(
    page_title="JESA Digital Maturity Assessment",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. Load global design system CSS
STYLES_DIR = Path(__file__).parent / "assets" / "styles"

CSS_FILES = [
    STYLES_DIR / "main.css",
    STYLES_DIR / "components.css",
    STYLES_DIR / "utilities.css",
]

for css_path in CSS_FILES:
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True,
            )
    else:
        logger.warning("CSS file not found: %s", css_path)

# 3. Session state initialization
if "assessment_id" not in st.session_state:
    st.session_state.assessment_id = None

if "assessment_results" not in st.session_state:
    st.session_state.assessment_results = None

for key in (
    "dashboard_data",
    "backend_results",
    "serialized_results",
    "roadmap_results",
    "decision_analysis_inputs",
):
    if key not in st.session_state:
        st.session_state[key] = None


# 4. Define navigation pages
pages = {
    "Assessment": [
        st.Page(
            "pages/1_Home.py",
            title="Home",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            "pages/2_New_Assessment.py",
            title="New Assessment",
            icon=":material/add_chart:",
        ),
    ],
    "Analysis": [
        st.Page(
            "pages/3_Dashboard.py",
            title="Dashboard",
            icon=":material/dashboard:",
        ),
        st.Page(
            "pages/4_Decision_analysis.py",
            title="Decision Analysis",
            icon=":material/analytics:",
        ),
        st.Page(
            "pages/5_Roadmap.py",
            title="Roadmap",
            icon=":material/route:",
        ),
    ],
    "Output": [
        st.Page(
            "pages/6_History.py",
            title="History",
            icon=":material/history:",
        ),
        st.Page(
            "pages/6_Export.py",
            title="Export",
            icon=":material/download:",
        ),
    ],
}


# Create navigation
pg = st.navigation(pages)


# =============================================================================
# ORIGINAL BACKEND CODE
# =============================================================================

class AssessmentPipeline:
    """
    Main pipeline for running the full JDMAF assessment.
    """

    def __init__(self):
        self.referentiel: Optional[Referentiel] = None

    def load_referentiel(self) -> Referentiel:
        """Load the referentiel once and cache it."""
        if self.referentiel is None:
            logger.info(
                "Loading referentiel from: %s",
                settings.REFERENTIEL_FILE,
            )

            self.referentiel = load_referentiel()

            logger.info(
                "Referentiel loaded: %d piliers, %d dimensions, "
                "%d sous-dimensions, %d indicateurs",
                len(self.referentiel.pillars),
                len(self.referentiel.dimensions),
                len(self.referentiel.subdimensions),
                len(self.referentiel.indicators),
            )

        return self.referentiel

    def run(
        self,
        assessment_file: Path,
        assessment_id: Optional[str] = None,
        include_gap_analysis: bool = True,
        include_tpi: bool = True,
        include_recommendations: bool = True,
        include_roadmap: bool = True,
        export_formats: List[str] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, any]:

        if export_formats is None:
            export_formats = ["json"]

        referentiel = self.load_referentiel()

        logger.info(
            "Loading assessment from: %s",
            assessment_file,
        )

        assessment = load_assessment(assessment_file)

        if assessment_id is None:
            assessment_id = assessment.metadata.assessment_id

            if assessment_id is None or assessment_id == "UNKNOWN":
                assessment_id = f"ASSESSMENT_{assessment_file.stem}"

        logger.info("Assessment ID: %s", assessment_id)

        logger.info("Validating assessment...")

        validation_report = validate_assessment(
            assessment,
            referentiel,
        )

        ensure_valid(validation_report)

        logger.info(
            "Validation passed: %s",
            validation_report.summary(),
        )

        # Aggregation
        logger.info("Running aggregation...")

        agg_engine = AggregationEngine(referentiel)

        aggregation_results = agg_engine.aggregate_scores(
            assessment
        )

        # Gap Analysis
        gap_results = None

        if include_gap_analysis:
            logger.info("Running gap analysis...")

            gap_engine = GapAnalysisEngine()

            target_levels = {}

            for dim_id, dimension in referentiel.dimensions.items():
                if dimension.effective_target_level is not None:
                    target_levels[dim_id] = (
                        dimension.effective_target_level
                    )

                elif dimension.target_level_default is not None:
                    target_levels[dim_id] = (
                        dimension.target_level_default
                    )

            gap_results = gap_engine.calculate_dimension_gaps(
                dimension_scores=aggregation_results.get(
                    "dimensions",
                    {},
                ),
                target_levels=target_levels,
            )

            logger.info(
                "Gap analysis completed: %d gaps found",
                len(gap_results),
            )

        # TPI
        tpi_results = None

        if include_tpi and gap_results:
            logger.info("Running TPI calculation...")

            tpi_engine = TPIEngine()

            decision_inputs = {}

            for dim_id in referentiel.dimensions:
                decision_inputs[dim_id] = {
                    "business_impact": 3,
                    "strategic_importance": 3,
                    "expected_roi": 3,
                    "implementation_cost": 3,
                    "implementation_difficulty": 3,
                }

            tpi_results = tpi_engine.calculate_tpi(
                gap_results=gap_results,
                decision_inputs=decision_inputs,
            )

            logger.info(
                "TPI calculation completed: "
                "%d dimensions prioritized",
                len(tpi_results),
            )

        # Recommendations
        recommendations = None

        if include_recommendations and gap_results:
            logger.info(
                "Loading recommendations knowledge base..."
            )

            import pandas as pd

            if settings.RECOMMENDATIONS_FILE.exists():
                knowledge_base = pd.read_excel(
                    settings.RECOMMENDATIONS_FILE,
                    sheet_name="RECOMMENDATIONS",
                )

                rec_engine = RecommendationEngine(
                    knowledge_base
                )

                recommendations = (
                    rec_engine.get_all_recommendations(
                        gap_results
                    )
                )

                logger.info(
                    "Recommendations generated: "
                    "%d dimensions have recommendations",
                    len(recommendations),
                )

            else:
                logger.warning(
                    "Recommendations file not found: %s",
                    settings.RECOMMENDATIONS_FILE,
                )

        # Priority
        priority_results = None

        if (
            include_gap_analysis
            and include_tpi
            and gap_results
            and tpi_results
        ):
            logger.info("Running priority analysis...")

            priority_engine = PriorityEngine()

            priority_results = (
                priority_engine.build_priority_analysis(
                    gap_results=gap_results,
                    tpi_results=tpi_results,
                    recommendations=recommendations,
                )
            )

            logger.info(
                "Priority analysis completed: "
                "%d dimensions prioritized",
                len(priority_results),
            )

        # Roadmap
        roadmap_results = None

        if include_roadmap and tpi_results:
            logger.info("Generating roadmap...")

            roadmap_engine = RoadmapEngine()

            roadmap_recommendations = {}

            if recommendations:
                for dim_id, recs in recommendations.items():
                    roadmap_recommendations[dim_id] = recs

            roadmap_results = roadmap_engine.build_roadmap(
                tpi_results=tpi_results,
                recommendations=roadmap_recommendations,
            )

            logger.info(
                "Roadmap generated: %d phases",
                len(roadmap_results),
            )

        # Export
        output_files = {}

        if export_formats:
            logger.info(
                "Exporting results to: %s",
                export_formats,
            )

            from exports.report import generate_report

            output_files = generate_report(
                aggregation_results=aggregation_results,
                gap_results=gap_results,
                tpi_results=tpi_results,
                priority_results=priority_results,
                roadmap=roadmap_results,
                output_dir=output_dir,
                assessment_id=assessment_id,
                formats=export_formats,
            )

            logger.info("Export completed")

        # Executive summary
        from exports.report import generate_executive_summary

        summary = generate_executive_summary(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
        )

        return {
            "assessment_id": assessment_id,
            "aggregation": aggregation_results,
            "gaps": gap_results,
            "tpi": tpi_results,
            "priorities": priority_results,
            "roadmap": roadmap_results,
            "summary": summary,
            "output_files": output_files,
        }


# =============================================================================
# COMMAND-LINE INTERFACE
# =============================================================================

def main() -> None:
    """Main entry point for the CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "JDMAF Assessment Backend - "
            "Run assessment and generate reports"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--assessment-file",
        type=Path,
        required=True,
        help="Path to the Assessment.xlsx file",
    )

    parser.add_argument(
        "--assessment-id",
        type=str,
        help="Identifier for the assessment",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.OUTPUT_DIR,
        help=(
            "Output directory for reports "
            f"(default: {settings.OUTPUT_DIR})"
        ),
    )

    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["json"],
        choices=["json", "excel", "pdf"],
        help="Export formats to generate",
    )

    parser.add_argument(
        "--no-gap",
        action="store_true",
        help="Skip gap analysis",
    )

    parser.add_argument(
        "--no-tpi",
        action="store_true",
        help="Skip TPI calculation",
    )

    parser.add_argument(
        "--no-recommendations",
        action="store_true",
        help="Skip recommendations generation",
    )

    parser.add_argument(
        "--no-roadmap",
        action="store_true",
        help="Skip roadmap generation",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    ensure_directory(args.output_dir)

    try:
        pipeline = AssessmentPipeline()

        results = pipeline.run(
            assessment_file=args.assessment_file,
            assessment_id=args.assessment_id,
            include_gap_analysis=not args.no_gap,
            include_tpi=not args.no_tpi,
            include_recommendations=not args.no_recommendations,
            include_roadmap=not args.no_roadmap,
            export_formats=args.formats,
            output_dir=args.output_dir,
        )

        summary = results["summary"]

        print("\n" + "=" * 60)
        print(
            f"ASSESSMENT COMPLETED: "
            f"{results['assessment_id']}"
        )
        print("=" * 60)

        print(
            f"DMI Score: {summary['dmi_score']:.1f}%"
            if summary["dmi_score"]
            else "DMI Score: N/A"
        )

        print(
            f"DMI Level: {summary['dmi_level']} - "
            f"{summary['dmi_level_name']}"
        )

        print(
            f"Critical Gaps: {summary['critical_gaps']}"
        )

        print(
            f"Priority Dimensions: "
            f"{summary['priority_dimensions']}"
        )

        if results["output_files"]:
            print("\nGenerated files:")

            for format_name, file_path in (
                results["output_files"].items()
            ):
                print(
                    f"  - {format_name.upper()}: "
                    f"{file_path}"
                )

        print("\n" + "=" * 60)

        summary_path = (
            args.output_dir
            / f"summary_{results['assessment_id']}.json"
        )

        with open(
            summary_path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                summary,
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Summary saved to: {summary_path}"
        )

    except Exception as e:
        logger.exception(
            "Error running assessment"
        )

        print(
            f"\n❌ ERROR: {e}",
            file=sys.stderr,
        )

        sys.exit(1)


# =============================================================================
# STREAMLIT PAGE EXECUTION
# =============================================================================

# IMPORTANT:
# st.navigation() returns the currently selected page.
# Streamlit requires that page to be executed with pg.run().
# This must happen exactly once per app rerun.
#
# Therefore, do NOT put pg.run() inside __main__.

pg.run()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # This block is reached by `python app.py`.
    # When Streamlit runs app.py, Streamlit controls execution
    # and pg.run() above has already rendered the selected page.
    if not st.runtime.exists():
        main()
