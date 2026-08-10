"""
engines
-------
Moteurs de calcul et d'analyse du JDMAF.

Ce package contient deux sous-packages principaux :
- assessment : Calcul des scores, agrégation, maturité, validation
- decision   : Analyse des écarts, TPI, priorisation, recommandations, roadmap

Exports publics :
    - engines.assessment
    - engines.decision
"""

from __future__ import annotations

# Expose les sous-packages pour un import direct
# Exemple : from engines import assessment, decision

__all__ = [
    "assessment",
    "decision",
]