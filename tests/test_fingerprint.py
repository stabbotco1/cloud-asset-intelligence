"""Tests for fingerprint extraction."""

import pytest

from cloud_asset_intel.fingerprint import (
    extract_key_fingerprint,
    extract_keyvalue_fingerprint,
)


def test_extract_key_fingerprint():
    """Test tag key fingerprint extraction."""
    tags = [
        {"Key": "Project", "Value": "webapp"},
        {"Key": "Environment", "Value": "prod"},
        {"Key": "ManagedBy", "Value": "terraform"},
    ]
    
    expected = ("Environment", "ManagedBy", "Project")
    actual = extract_key_fingerprint(tags)
    
    assert actual == expected


def test_extract_key_fingerprint_empty():
    """Test fingerprint extraction with no tags."""
    tags = []
    expected = ()
    actual = extract_key_fingerprint(tags)
    
    assert actual == expected


def test_extract_keyvalue_fingerprint():
    """Test tag key-value fingerprint extraction."""
    tags = [
        {"Key": "Project", "Value": "webapp"},
        {"Key": "Environment", "Value": "prod"},
    ]
    
    expected = (("Environment", "prod"), ("Project", "webapp"))
    actual = extract_keyvalue_fingerprint(tags)
    
    assert actual == expected


def test_fingerprint_ordering():
    """Test that fingerprints are consistently ordered."""
    tags1 = [
        {"Key": "Z", "Value": "last"},
        {"Key": "A", "Value": "first"},
        {"Key": "M", "Value": "middle"},
    ]
    
    tags2 = [
        {"Key": "M", "Value": "middle"},
        {"Key": "A", "Value": "first"},
        {"Key": "Z", "Value": "last"},
    ]
    
    fp1 = extract_key_fingerprint(tags1)
    fp2 = extract_key_fingerprint(tags2)
    
    assert fp1 == fp2
    assert fp1 == ("A", "M", "Z")
