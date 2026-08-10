"""
exports
-------
Exportation des résultats d'évaluation et de décision.

Ce package contient :
- excel.py : Export des résultats au format Excel (classeur multi-feuilles)
- pdf.py   : Génération de rapports PDF professionnels (ReportLab)
- report.py: Coordination unifiée des exports (Excel, PDF, JSON)

Exports publics :
    ExcelExporter, export_to_excel, export_full_analysis
    PDFReportGenerator, generate_pdf_report
    ReportGenerator, generate_report, generate_executive_summary
"""

from __future__ import annotations

# Excel
from exports.excel import (
    ExcelExporter,
    export_to_excel,
    export_full_analysis,
)

# PDF
from exports.pdf import (
    PDFReportGenerator,
    generate_pdf_report,
)

# Rapport unifié
from exports.report import (
    ReportGenerator,
    generate_report,
    generate_executive_summary,
    ReportData,
    ExecutiveSummary,
)

__all__ = [
    # Excel
    "ExcelExporter",
    "export_to_excel",
    "export_full_analysis",
    # PDF
    "PDFReportGenerator",
    "generate_pdf_report",
    # Rapport
    "ReportGenerator",
    "generate_report",
    "generate_executive_summary",
    "ReportData",
    "ExecutiveSummary",
]