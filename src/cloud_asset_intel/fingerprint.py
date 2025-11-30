"""Fingerprint extraction and clustering for cloud resources."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple


def extract_key_fingerprint(tags: List[Dict[str, str]]) -> Tuple[str, ...]:
    """
    Extract tag key fingerprint from resource tags.
    
    Args:
        tags: List of tag dictionaries with 'Key' and 'Value'
        
    Returns:
        Sorted tuple of tag keys
    """
    return tuple(sorted(tag["Key"] for tag in tags))


def extract_keyvalue_fingerprint(tags: List[Dict[str, str]]) -> Tuple[Tuple[str, str], ...]:
    """
    Extract tag key-value fingerprint from resource tags.
    
    Args:
        tags: List of tag dictionaries with 'Key' and 'Value'
        
    Returns:
        Sorted tuple of (key, value) pairs
    """
    return tuple(sorted((tag["Key"], tag["Value"]) for tag in tags))


def generate_fingerprint_clusters(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate fingerprint clusters from discovered resources.
    
    Args:
        resources: List of resource dictionaries with 'arn' and 'tags'
        
    Returns:
        Dictionary with cluster information
    """
    key_clusters = defaultdict(list)
    keyvalue_clusters = defaultdict(list)
    
    for resource in resources:
        tags = resource.get("tags", [])
        if not tags:
            continue
        
        # Extract fingerprints
        key_fp = extract_key_fingerprint(tags)
        keyvalue_fp = extract_keyvalue_fingerprint(tags)
        
        # Add to clusters
        key_clusters[key_fp].append(resource["arn"])
        keyvalue_clusters[keyvalue_fp].append(resource["arn"])
    
    # Format output
    clusters = []
    cluster_id = 1
    
    # Add key-based clusters
    for fingerprint, arns in key_clusters.items():
        clusters.append({
            "cluster_id": f"key-{cluster_id}",
            "fingerprint_type": "key",
            "fingerprint": list(fingerprint),
            "resource_count": len(arns),
            "resources": arns,
        })
        cluster_id += 1
    
    # Add key-value clusters
    cluster_id = 1
    for fingerprint, arns in keyvalue_clusters.items():
        clusters.append({
            "cluster_id": f"keyvalue-{cluster_id}",
            "fingerprint_type": "keyvalue",
            "fingerprint": [list(pair) for pair in fingerprint],
            "resource_count": len(arns),
            "resources": arns,
        })
        cluster_id += 1
    
    return {
        "generated_date": datetime.utcnow().isoformat() + "Z",
        "total_clusters": len(clusters),
        "clusters": clusters,
    }
