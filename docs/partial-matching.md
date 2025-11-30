# Partial Tag Matching

## Overview

Partial tag matching handles real-world scenarios where resources have incomplete or inconsistent tagging. Instead of requiring exact matches, the system calculates confidence scores for partial matches.

## Why Partial Matches Occur

1. **Human error** - Tags forgotten during manual creation
2. **Phased deployment** - Tags added incrementally over time
3. **Tag policy evolution** - Project changed tagging strategy
4. **Console creation** - Engineers added minimal tags manually
5. **Related resources** - Same team, different project phase

## Confidence Scoring

### Base Algorithm

```python
def calculate_match_confidence(resource_tags, project_fingerprint):
    """Calculate confidence score (0.0 to 1.0)"""
    resource_keys = set(tag['Key'] for tag in resource_tags)
    project_keys = set(project_fingerprint['key_fingerprint'])
    
    # Base score: percentage of project tags present
    overlap = len(resource_keys & project_keys)
    base_score = overlap / len(project_keys)
    
    # Penalty for extra tags (max 20%)
    extra_tags = len(resource_keys - project_keys)
    extra_penalty = min(0.2, extra_tags * 0.05)
    
    # Bonus for critical tags (10% each)
    critical_tags = {'Project', 'ManagedBy', 'Application'}
    critical_overlap = len(resource_keys & critical_tags & project_keys)
    critical_bonus = critical_overlap * 0.1
    
    confidence = base_score - extra_penalty + critical_bonus
    return max(0.0, min(1.0, confidence))
```

### Weighted Algorithm

Assigns importance weights to different tags:

```python
CRITICAL_TAGS = {
    'Project': 0.3,      # Most important
    'ManagedBy': 0.2,    # Important
    'Application': 0.2,  # Important
    'Environment': 0.1,  # Useful
    'CostCenter': 0.1,   # Useful
}

def weighted_confidence(resource_tags, project_fingerprint):
    """Calculate confidence with tag importance weighting"""
    resource_keys = {tag['Key']: tag['Value'] for tag in resource_tags}
    project_keys = set(project_fingerprint['key_fingerprint'])
    
    total_weight = 0.0
    matched_weight = 0.0
    
    for tag_key in project_keys:
        weight = CRITICAL_TAGS.get(tag_key, 0.05)  # Default 5%
        total_weight += weight
        
        if tag_key in resource_keys:
            matched_weight += weight
    
    return matched_weight / total_weight
```

## Confidence Levels

| Score | Level | Meaning |
|-------|-------|---------|
| 1.0 | EXACT_MATCH | All tags match perfectly |
| 0.9+ | VERY_HIGH | 90%+ match, likely same project |
| 0.8-0.9 | HIGH | 80%+ match, probably same project |
| 0.7-0.8 | MEDIUM_HIGH | 70%+ match, investigate |
| 0.6-0.7 | MEDIUM | 60%+ match, possible relation |
| < 0.6 | LOW | Weak relation or different project |

## Examples

### Example 1: High Confidence (0.8)

**Project fingerprint**: `[Project, Environment, ManagedBy, CostCenter, Owner]`

**Resource tags** (3 of 5):
```json
[
  {"Key": "Project", "Value": "webapp"},
  {"Key": "Environment", "Value": "prod"},
  {"Key": "ManagedBy", "Value": "terraform"}
]
```

**Calculation**:
- Base score: 3/5 = 0.6
- Critical tags matched: Project, ManagedBy = +0.2
- No extra tags: 0 penalty
- **Final: 0.8 (HIGH confidence)**

**Recommendation**: HIGH_MATCH - Consider adding missing tags: [CostCenter, Owner]

### Example 2: Medium Confidence (0.7)

**Resource tags** (3 of 5 + 2 extra):
```json
[
  {"Key": "Project", "Value": "webapp"},
  {"Key": "Environment", "Value": "prod"},
  {"Key": "ManagedBy", "Value": "terraform"},
  {"Key": "Team", "Value": "platform"},
  {"Key": "CreatedBy", "Value": "jenkins"}
]
```

**Calculation**:
- Base score: 3/5 = 0.6
- Critical tags matched: Project, ManagedBy = +0.2
- Extra tags: 2 * 0.05 = -0.1 penalty
- **Final: 0.7 (MEDIUM_HIGH confidence)**

**Recommendation**: MEDIUM_MATCH - Review manually, extra tags suggest different project or manual creation

### Example 3: Low Confidence (0.5)

**Resource tags** (2 of 5, missing critical):
```json
[
  {"Key": "Environment", "Value": "prod"},
  {"Key": "CostCenter", "Value": "engineering"}
]
```

**Calculation**:
- Base score: 2/5 = 0.4
- Critical tags matched: 0 = +0.0
- No extra tags: 0 penalty
- **Final: 0.4 (LOW confidence)**

**Recommendation**: LOW_MATCH - Missing critical tags: [Project, ManagedBy] - likely different project

## Match Details Report

For each partial match, generate detailed analysis:

```json
{
  "resource_arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123",
  "matched_project": "aws-account-baseline",
  "confidence": 0.75,
  "level": "MEDIUM_HIGH",
  "matched_tags": ["Project", "Environment", "ManagedBy"],
  "missing_tags": ["CostCenter", "Owner"],
  "extra_tags": ["CreatedBy"],
  "recommendation": "MEDIUM_MATCH - Consider adding missing tags: [CostCenter, Owner]"
}
```

## Threshold Configuration

Default threshold: **0.6** (60% confidence)

**Adjust based on use case**:
- **Strict matching** (0.8+): Only high-confidence matches
- **Balanced** (0.6-0.7): Default, catches most related resources
- **Permissive** (0.5+): Includes weak matches for investigation

```bash
# CLI usage
cloud-asset-intel identify --threshold 0.7  # Stricter matching
cloud-asset-intel identify --threshold 0.5  # More permissive
```

## Handling Ambiguity

When multiple projects match with similar confidence:

```python
def resolve_collision(resource, matching_projects):
    """Resolve when resource matches multiple projects"""
    # Sort by confidence, then by last_updated
    sorted_matches = sorted(
        matching_projects,
        key=lambda p: (p['confidence'], p['metadata']['last_updated']),
        reverse=True
    )
    
    best_match = sorted_matches[0]
    
    # Flag if multiple high-confidence matches
    if len(sorted_matches) > 1 and sorted_matches[1]['confidence'] >= 0.9:
        best_match['ambiguous'] = True
        best_match['alternative_matches'] = sorted_matches[1:]
    
    return best_match
```

## Best Practices

1. **Start with default threshold (0.6)** - Adjust based on results
2. **Review medium-confidence matches** - May need manual classification
3. **Add missing tags** - Improve future matching accuracy
4. **Use critical tags consistently** - Project, ManagedBy, Application
5. **Document tag policy** - Ensure team follows consistent tagging

## Implementation

The partial matching algorithm is implemented in `src/cloud_asset_intel/matcher.py`:
- `calculate_match_confidence()` - Base algorithm
- `_weighted_confidence()` - Weighted algorithm
- `_generate_match_details()` - Detailed analysis
- `match_resource_to_projects()` - Main matching function
