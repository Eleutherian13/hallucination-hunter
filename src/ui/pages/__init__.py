"""
UI Pages module
"""

from src.ui.pages.home import render_home
from src.ui.pages.audit import render_audit_page
from src.ui.pages.results import render_results_page
from src.ui.pages.settings import render_settings_page

__all__ = [
    "render_home",
    "render_audit_page",
    "render_results_page",
    "render_settings_page"
]
