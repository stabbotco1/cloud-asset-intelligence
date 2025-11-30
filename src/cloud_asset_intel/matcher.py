"""Resource matching and orphan identification."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .fingerprint import extract_key_fingerprint, extract_keyvalue_fingerprint


# Critical tags with importance weights
CRITICAL_TAGS = {
    "Project": 0.3,
    "ManagedBy": 0.2,
    "Application": 0.2,
    "Environment": 0.1,
    "CostCenter": 0.1,
}


def calculate_match_confidence(
    resource_tags: List[Dict[str, str]],
    project_fingerprint: Dict[str, Any],
    use_weighted: bool = True,
) -> float:
    """
    Calculate confidence score for resource matching project fingerprint.
    
    Args:
        resource_tags: List of tag dictionaries
        project_fingerprint: Project fingerprint dictionary
        use_weighted: Use weighted scoring based on critical tags
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    resource_keys = set(tag["Key"] for tag in resource_tags)
    project_keys = set(project_fingerprint["fingerprints"]["key_fingerprint"])
    
    if not project_keys:
        return 0.0
    
    # Calculate overlap
    overlap = len(resource_keys & project_keys)
    
    if use_weighted:
        return _weighted_confidence(resource_tags, project_fingerprint)
    
    # Base score: percentage of project tags present
    base_score = overlap / len(project_keys)
    
    # Penalty for extra tags
    extra_tags = len(resource_keys - project_keys)
    extra_penalty = min(0.2, extra_tags * 0.05)
    
    # Bonus for critical tag matches
    critical_overlap = len(resource_keys & set(CRITICAL_TAGS.keys()) & project_keys)
    critical_bonus = critical_overlap * 0.1
    
    confidence = base_score - extra_penalty + critical_bonus
    return max(0.0, min(1.0, confidence))


def _weighted_confidence(
    resource_tags: List[Dict[str, str]],
    project_fingerprint: Dict[str, Any],
) -> float:
    """Calculate confidence with tag importance weighting."""
    resource_keys = {tag["Key"]: tag["Value"] for tag in resource_tags}
    project_keys = set(project_fingerprint["fingerprints"]["key_fingerprint"])
    
    total_weight = 0.0
    matched_weight = 0.0
    
    for tag_key in project_keys:
        weight = CRITICAL_TAGS.get(tag_key, 0.05)
        total_weight += weight
        
        if tag_key in resource_keys:
            matched_weight += weight
    
    return matched_weight / total_weight if total_weight > 0 else 0.0


def match_resource_to_projects(
    resource: Dict[str, Any],
    projects: List[Dict[str, Any]],
    threshold: float = 0.6,
) -> Tuple[Optional[Dict[str, Any]], float, Dict[str, Any]]:
    """
    Match a resource to known projects.
    
    Args:
        resource: Resource dictionary with 'arn' and 'tags'
        projects: List of project fingerprint dictionaries
        threshold: Minimum confidence threshold
        
    Returns:
        Tuple of (best_match_project, confidence, match_details)
    """
    best_match = None
    best_confidence = 0.0
    best_details = {}
    
    resource_tags = resource.get("tags", [])
    if not resource_tags:
        return None, 0.0, {"reason": "no_tags"}
    
    for project in projects:
        confidence = calculate_match_confidence(resource_tags, project)
        
        if confidence > best_confidence:
            best_confidence = confidence
            best_match = project
            best_details = _generate_match_details(resource_tags, project, confidence)
    
    if best_confidence >= threshold:
        return best_match, best_confidence, best_details
    
    return None, best_confidence, best_details


def _generate_match_details(
    resource_tags: List[Dict[str, str]],
    project: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    """Generate detailed match analysis."""
    resource_keys = set(tag["Key"] for tag in resource_tags)
    project_keys = set(project["fingerprints"]["key_fingerprint"])
    
    matched = resource_keys & project_keys
    missing = project_keys - resource_keys
    extra = resource_keys - project_keys
    
    # Determine confidence level
    if confidence >= 1.0:
        level = "EXACT_MATCH"
    elif confidence >= 0.9:
        level = "VERY_HIGH"
    elif confidence >= 0.8:
        level = "HIGH"
    elif confidence >= 0.7:
        level = "MEDIUM_HIGH"
    elif confidence >= 0.6:
        level = "MEDIUM"
    else:
        level = "LOW"
    
    # Generate recommendation
    if confidence >= 0.8:
        if missing:
            recommendation = f"HIGH_MATCH - Consider adding missing tags: {list(missing)}"
        else:
            recommendation = "HIGH_MATCH - Likely belongs to this project"
    elif confidence >= 0.6:
        critical_missing = missing & set(CRITICAL_TAGS.keys())
        if critical_missing:
            recommendation = f"MEDIUM_MATCH - Missing critical tags: {list(critical_missing)}"
        else:
            recommendation = "MEDIUM_MATCH - Review manually to confirm"
    else:
        recommendation = "LOW_MATCH - Likely different project or manual creation"
    
    return {
        "confidence": confidence,
        "level": level,
        "matched_tags": list(matched),
        "missing_tags": list(missing),
        "extra_tags": list(extra),
        "recommendation": recommendation,
    }


def identify_orphans(
    resources: List[Dict[str, Any]],
    registry_path: Path,
    threshold: float = 0.6,
) -> Dict[str, Any]:
    """
    Identify orphaned resources by matching to known projects.
    
    Args:
        resources: List of resource dictionaries
        registry_path: Path to project fingerprints directory
        threshold: Confidence threshold for matching
        
    Returns:
        Report dictionary with matched and orphaned resources
    """
    # Load project fingerprints
    projects = []
    for fp_file in Path(registry_path).glob("*.json"):
        with open(fp_file) as f:
            projects.append(json.load(f))
    
    matched_projects = defaultdict(list)
    orphaned_resources = []
    
    for resource in resources:
        project, confidence, details = match_resource_to_projects(
            resource, projects, threshold
        )
        
        if project:
            matched_projects[project["project_name"]].append({
                "arn": resource["arn"],
                "confidence": confidence,
                "details": details,
            })
        else:
            orphaned_resources.append({
                "arn": resource["arn"],
                "tags": resource.get("tags", []),
                "fingerprint": list(extract_key_fingerprint(resource.get("tags", []))),
            })
    
    # Format matched projects
    matched_list = []
    for project_name, resources_list in matched_projects.items():
        matched_list.append({
            "project_name": project_name,
            "resource_count": len(resources_list),
            "confidence": sum(r["confidence"] for r in resources_list) / len(resources_list),
            "resources": [r["arn"] for r in resources_list],
        })
    
    # Cluster orphans by fingerprint
    orphan_clusters = _cluster_orphans(orphaned_resources)
    
    total_matched = sum(p["resource_count"] for p in matched_list)
    
    return {
        "report_date": datetime.utcnow().isoformat() + "Z",
        "total_resources": len(resources),
        "matched_resources": total_matched,
        "orphaned_resources": len(orphaned_resources),
        "matched_projects": matched_list,
        "orphan_clusters": orphan_clusters,
    }


def _cluster_orphans(orphaned_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cluster orphaned resources by fingerprint."""
    from collections import defaultdict
    
    clusters = defaultdict(list)
    
    for resource in orphaned_resources:
        fp = tuple(resource["fingerprint"])
        clusters[fp].append(resource["arn"])
    
    cluster_list = []
    for i, (fingerprint, arns) in enumerate(clusters.items(), 1):
        cluster_list.append({
            "cluster_id": f"orphan-{i}",
            "fingerprint": list(fingerprint),
            "resource_count": len(arns),
            "resources": arns,
            "recommendation": _get_orphan_recommendation(len(arns), list(fingerprint)),
        })
    
    return cluster_list


def _get_orphan_recommendation(count: int, fingerprint: List[str]) -> str:
    """Generate recommendation for orphan cluster."""
    if count == 1:
        return "Single orphaned resource - likely manual console creation"
    elif count < 5:
        return "Small cluster - investigate for manual creations or incomplete tagging"
    else:
        return "Large cluster - likely forgotten project or separate deployment"
