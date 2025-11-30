"""Cloud Asset Intelligence - Forensic discovery and analysis of cloud resources."""

__version__ = "0.1.0"
__author__ = "Stephen Abbott"
__license__ = "MIT"

from .fingerprint import extract_key_fingerprint, extract_keyvalue_fingerprint
from .matcher import calculate_match_confidence, match_resource_to_projects

__all__ = [
    "extract_key_fingerprint",
    "extract_keyvalue_fingerprint",
    "calculate_match_confidence",
    "match_resource_to_projects",
]
