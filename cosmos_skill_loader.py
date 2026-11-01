"""
cosmos_skill_loader.py - Root Bridge
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(BASE, "Jarvis_Setup_Package")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from cosmos_skill_loader import (
    CosmosSkillRegistry,
    match_and_inject_skill_context,
    _registry
)

