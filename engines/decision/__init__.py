"""
engines.decision
----------------
Moteurs d'analyse décisionnelle et de priorisation.

Ce package contient :
- gap.py          : Analyse des écarts (Gap) entre scores actuels et cibles
- tpi.py          : Calcul du Transformation Priority Index (TPI)
- priority.py     : Orchestration de la priorisation (Gap + TPI + Recommandations)
- recommendation.py : Sélection des recommandations adaptées aux écarts
- roadmap.py      : Génération de la feuille de route (Roadmap) structurée

Exports publics :
    GapAnalysisEngine, GapResult
    TPIEngine, TPIResult
    PriorityEngine, PriorityResult
    RecommendationEngine, RecommendationResult
    RoadmapEngine, RoadmapPhase, RoadmapItem
"""

from __future__ import annotations

# Gap
from engines.decision.gap import GapAnalysisEngine, GapResult

# TPI
from engines.decision.tpi import TPIEngine, TPIResult

# Priorité
from engines.decision.priority import PriorityEngine, PriorityResult

# Recommandations
from engines.decision.recommendation import RecommendationEngine, RecommendationResult

# Roadmap
from engines.decision.roadmap import RoadmapEngine, RoadmapPhase, RoadmapItem

__all__ = [
    # Gap
    "GapAnalysisEngine",
    "GapResult",
    # TPI
    "TPIEngine",
    "TPIResult",
    # Priorité
    "PriorityEngine",
    "PriorityResult",
    # Recommandations
    "RecommendationEngine",
    "RecommendationResult",
    # Roadmap
    "RoadmapEngine",
    "RoadmapPhase",
    "RoadmapItem",
]