"""
cosmos_minicpm_agency_skills.py - Subpackage Bridge for OpenBMB/MiniCPM-V Multimodal Skills
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from cosmos_minicpm_agency_skills import (
    CosmosMiniCPMVSkillsEngine,
    minicpm_skills
)

