"""
app.py — Backend Entry Point for JDMAF (Command-Line Interface)

This module provides a command-line interface to:
- Load an assessment from an Excel file
- Run the full assessment pipeline (aggregation, gap analysis, TPI, roadmap)
- Generate reports (Excel, PDF, JSON)

Usage:
    # Run assessment and generate all reports
    python app.py --assessment-file path/to/Assessment.xlsx --output-dir outputs/

    # Run with specific assessment ID
    python app.py --assessment-file path/to/Assessment.xlsx --assessment-id SITE-001

    # Generate only JSON (no Excel/PDF)
    python app.py --assessment-file path/to/Assessment.xlsx --formats json

    # Generate all formats
    python app.py --assessment-file path/to/Assessment.xlsx --formats json excel pdf

    # Show help
    python app.py --help
"""

from __future__ import annotations

import argparse
import json
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
from exports.report import generate_report, generate_executive_summary

from utils.file_manager import ensure_directory, build_output_path

import logging

logger = settings.get_logger(__name__)


# ============================================================================
# Core Assessment Pipeline
# ============================================================================


class AssessmentPipeline:
    """
    Main pipeline for running the full JDMAF assessment.
    """

    def __init__(self):
        self.referentiel: Optional[Referentiel] = None

    def load_referentiel(self) -> Referentiel:
        """Load the referentiel once and cache it."""
        if self.referentiel is None:
            logger.info("Loading referentiel from: %s", settings.REFERENTIEL_FILE)
            self.referentiel = load_referentiel()
            logger.info(
                "Referentiel loaded: %d piliers, %d dimensions, %d sous-dimensions, %d indicateurs",
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
        """
        Run the complete assessment pipeline.

        Args:
            assessment_file: Path to the Assessment.xlsx file
            assessment_id: Identifier for the assessment (if None, uses metadata)
            include_gap_analysis: Whether to run gap analysis
            include_tpi: Whether to run TPI calculation
            include_recommendations: Whether to generate recommendations
            include_roadmap: Whether to generate roadmap
            export_formats: List of formats to export ("json", "excel", "pdf")
            output_dir: Directory to save output files

        Returns:
            Dictionary containing results and output file paths
        """
        if export_formats is None:
            export_formats = ["json"]

        # Load referentiel
        referentiel = self.load_referentiel()

        # Load assessment
        logger.info("Loading assessment from: %s", assessment_file)
        assessment = load_assessment(assessment_file)

        # Use provided assessment_id or from metadata
        if assessment_id is None:
            assessment_id = assessment.metadata.assessment_id
            if assessment_id is None or assessment_id == "UNKNOWN":
                assessment_id = f"ASSESSMENT_{assessment_file.stem}"

        logger.info("Assessment ID: %s", assessment_id)

        # Validate assessment
        logger.info("Validating assessment...")
        validation_report = validate_assessment(assessment, referentiel)
        ensure_valid(validation_report)
        logger.info("Validation passed: %s", validation_report.summary())

        # Aggregation
        logger.info("Running aggregation...")
        agg_engine = AggregationEngine(referentiel)
        aggregation_results = agg_engine.aggregate_scores(assessment)

        # Gap Analysis
        gap_results = None
        if include_gap_analysis:
            logger.info("Running gap analysis...")
            gap_engine = GapAnalysisEngine()
            # Get target levels from referentiel dimensions
            target_levels = {}
            for dim_id, dimension in referentiel.dimensions.items():
                if dimension.effective_target_level is not None:
                    target_levels[dim_id] = dimension.effective_target_level
                elif dimension.target_level_default is not None:
                    target_levels[dim_id] = dimension.target_level_default

            gap_results = gap_engine.calculate_dimension_gaps(
                dimension_scores=aggregation_results.get("dimensions", {}),
                target_levels=target_levels,
            )
            logger.info("Gap analysis completed: %d gaps found", len(gap_results))

        # TPI
        tpi_results = None
        if include_tpi and gap_results:
            logger.info("Running TPI calculation...")
            tpi_engine = TPIEngine()

            # Note: In a real implementation, decision_inputs would come from
            # user input or a separate configuration file.
            # Here we use default values (3 out of 5) as placeholders.
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
            logger.info("TPI calculation completed: %d dimensions prioritized", len(tpi_results))

        # Recommendations
        recommendations = None
        if include_recommendations and gap_results:
            logger.info("Loading recommendations knowledge base...")
            import pandas as pd

            if settings.RECOMMENDATIONS_FILE.exists():
                knowledge_base = pd.read_excel(
                    settings.RECOMMENDATIONS_FILE,
                    sheet_name="RECOMMENDATIONS",
                )
                rec_engine = RecommendationEngine(knowledge_base)
                recommendations = rec_engine.get_all_recommendations(gap_results)
                logger.info(
                    "Recommendations generated: %d dimensions have recommendations",
                    len(recommendations),
                )
            else:
                logger.warning(
                    "Recommendations file not found: %s",
                    settings.RECOMMENDATIONS_FILE,
                )

        # Priority
        priority_results = None
        if include_gap_analysis and include_tpi and gap_results and tpi_results:
            logger.info("Running priority analysis...")
            priority_engine = PriorityEngine()
            priority_results = priority_engine.build_priority_analysis(
                gap_results=gap_results,
                tpi_results=tpi_results,
                recommendations=recommendations,
            )
            logger.info("Priority analysis completed: %d dimensions prioritized", len(priority_results))

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
            logger.info("Roadmap generated: %d phases", len(roadmap_results))

        # Export results
        output_files = {}
        if export_formats:
            logger.info("Exporting results to: %s", export_formats)
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

        # Generate executive summary
        summary = generate_executive_summary(
            aggregation_results=aggregation_results,
            gap_results=gap_results,
        )

        # Return results
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


# ============================================================================
# Command-Line Interface
# ============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="JDMAF Assessment Backend - Run assessment and generate reports",
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
        help="Identifier for the assessment (default: from metadata)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.OUTPUT_DIR,
        help=f"Output directory for reports (default: {settings.OUTPUT_DIR})",
    )

    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["json"],
        choices=["json", "excel", "pdf"],
        help="Export formats to generate (default: json)",
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

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure output directory exists
    ensure_directory(args.output_dir)

    # Run the pipeline
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

        # Print results summary
        summary = results["summary"]
        print("\n" + "=" * 60)
        print(f"ASSESSMENT COMPLETED: {results['assessment_id']}")
        print("=" * 60)
        print(f"DMI Score: {summary['dmi_score']:.1f}%" if summary['dmi_score'] else "DMI Score: N/A")
        print(f"DMI Level: {summary['dmi_level']} - {summary['dmi_level_name']}")
        print(f"Critical Gaps: {summary['critical_gaps']}")
        print(f"Priority Dimensions: {summary['priority_dimensions']}")

        if results["output_files"]:
            print("\nGenerated files:")
            for format_name, file_path in results["output_files"].items():
                print(f"  - {format_name.upper()}: {file_path}")

        print("\n" + "=" * 60)

        # Save summary to JSON
        summary_path = args.output_dir / f"summary_{results['assessment_id']}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Summary saved to: {summary_path}")

    except Exception as e:
        logger.exception("Error running assessment")
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()