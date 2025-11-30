# Fingerprint Specification

## Overview

This document defines the format and matching rules for resource fingerprints used in Cloud Asset Intelligence.

## Fingerprint Types

### 1. Tag Key Fingerprint

**Definition**: Ordered tuple of tag keys present on a resource.

**Format**:
```python
fingerprint = tuple(sorted(tag_keys))
```

**Example**:
```python
# Input tags
tags = [
    {'Key': 'Project', 'Value': 'webapp'},
    {'Key': 'Environment', 'Value': 'prod'},
    {'Key': 'ManagedBy', 'Value': 'terraform'}
]

# Output fingerprint
('Environment', 'ManagedBy', 'Project')
```

**Properties**:
- Immutable (tuple)
- Hashable (can be dict key)
- Sorted alphabetically
- Case-sensitive

### 2. Tag Key-Value Fingerprint

**Definition**: Ordered tuple of (key, value) pairs.

**Format**:
```python
fingerprint = tuple(sorted([(k, v) for k, v in tags]))
```

**Example**:
```python
# Input tags
tags = [
    {'Key': 'Project', 'Value': 'webapp'},
    {'Key': 'Environment', 'Value': 'prod'}
]

# Output fingerprint
(('Environment', 'prod'), ('Project', 'webapp'))
```

**Properties**:
- Immutable (tuple of tuples)
- Hashable
- Sorted alphabetically by key
- Case-sensitive for both keys and values

## Project Fingerprint Registry Format

### File Structure

**Location**: `examples/project-fingerprints/<project-name>.json`

**Schema**:
```json
{
  "project_name": "string (required)",
  "description": "string (optional)",
  "fingerprints": {
    "key_fingerprint": ["string"],
    "keyvalue_fingerprints": [
      {
        "TagKey": "TagValue"
      }
    ]
  },
  "state_file_location": "string (optional)",
  "repository": "string (optional)",
  "metadata": {
    "created": "ISO8601 timestamp",
    "last_updated": "ISO8601 timestamp",
    "version": "semver"
  }
}
```

### Example: Complete Project Fingerprint

```json
{
  "project_name": "aws-account-baseline",
  "description": "Account-level foundational infrastructure for personal AWS accounts",
  "fingerprints": {
    "key_fingerprint": [
      "Application",
      "Description",
      "Environment",
      "ManagedBy",
      "Name",
      "Project"
    ],
    "keyvalue_fingerprints": [
      {
        "Application": "aws-account-baseline",
        "Description": "Account-level foundational infrastructure",
        "Environment": "account",
        "ManagedBy": "opentofu",
        "Name": "aws-account-baseline-*",
        "Project": "aws-account-baseline"
      },
      {
        "Application": "aws-account-baseline",
        "Description": "Account-level foundational infrastructure",
        "Environment": "account",
        "ManagedBy": "bootstrap",
        "Name": "aws-account-baseline-*",
        "Project": "aws-account-baseline"
      }
    ]
  },
  "state_file_location": "s3://aws-account-baseline-123456789012-state/baseline/terraform.tfstate",
  "repository": "https://github.com/yourusername/aws-account-baseline",
  "metadata": {
    "created": "2025-11-30T00:00:00Z",
    "last_updated": "2025-11-30T00:00:00Z",
    "version": "1.0.0"
  }
}
```

## Matching Rules

### Exact Match

**Tag Key Fingerprint**:
```python
def exact_key_match(resource_fingerprint, project_fingerprint):
    """Exact match of tag keys"""
    return resource_fingerprint == tuple(sorted(project_fingerprint['key_fingerprint']))
```

**Tag Key-Value Fingerprint**:
```python
def exact_keyvalue_match(resource_fingerprint, project_keyvalue):
    """Exact match of tag key-value pairs"""
    project_fp = tuple(sorted(project_keyvalue.items()))
    return resource_fingerprint == project_fp
```

### Fuzzy Match (Subset)

**Definition**: Resource matches if it has at least N% of project's tags.

```python
def fuzzy_key_match(resource_tags, project_fingerprint, threshold=0.8):
    """Match if resource has at least threshold% of project tags"""
    resource_keys = set(tag['Key'] for tag in resource_tags)
    project_keys = set(project_fingerprint['key_fingerprint'])
    
    if len(project_keys) == 0:
        return False
    
    overlap = len(resource_keys & project_keys)
    match_ratio = overlap / len(project_keys)
    
    return match_ratio >= threshold
```

**Default Threshold**: 80% (configurable)

### Wildcard Match

**Definition**: Tag values can contain wildcards for pattern matching.

```python
import fnmatch

def wildcard_keyvalue_match(resource_tags, project_keyvalue):
    """Match with wildcard support in values"""
    resource_dict = {tag['Key']: tag['Value'] for tag in resource_tags}
    
    for key, pattern in project_keyvalue.items():
        if key not in resource_dict:
            return False
        
        if not fnmatch.fnmatch(resource_dict[key], pattern):
            return False
    
    return True
```

**Example**:
```json
{
  "Name": "aws-account-baseline-*",
  "Project": "aws-account-baseline"
}
```

Matches:
- `Name=aws-account-baseline-state`
- `Name=aws-account-baseline-cloudtrail`

## Confidence Scoring

Assign confidence scores to matches:

```python
def calculate_confidence(resource_tags, project_fingerprint):
    """Calculate match confidence (0.0 to 1.0)"""
    
    # Exact key-value match = 1.0
    for kv_fp in project_fingerprint['keyvalue_fingerprints']:
        if exact_keyvalue_match(resource_tags, kv_fp):
            return 1.0
    
    # Exact key match = 0.9
    if exact_key_match(resource_tags, project_fingerprint):
        return 0.9
    
    # Fuzzy key match = 0.5 to 0.8 (based on overlap)
    resource_keys = set(tag['Key'] for tag in resource_tags)
    project_keys = set(project_fingerprint['key_fingerprint'])
    
    if len(project_keys) == 0:
        return 0.0
    
    overlap = len(resource_keys & project_keys)
    return 0.5 + (0.3 * overlap / len(project_keys))
```

**Confidence Levels**:
- `1.0` - Exact key-value match (highest confidence)
- `0.9` - Exact key match
- `0.8` - 80%+ key overlap
- `0.7` - 70%+ key overlap
- `0.6` - 60%+ key overlap
- `< 0.6` - Low confidence, flag for review

## Collision Handling

### Multiple Project Matches

**Problem**: Resource matches multiple projects

**Resolution**:
1. Choose highest confidence match
2. If tied, choose most recently updated project
3. Flag as ambiguous in report

```python
def resolve_collision(resource, matching_projects):
    """Resolve when resource matches multiple projects"""
    
    # Sort by confidence (descending), then by last_updated (descending)
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

### Fingerprint Conflicts

**Problem**: Two projects have identical fingerprints

**Prevention**: Validate fingerprint registry on load
```python
def validate_registry(projects):
    """Ensure no duplicate fingerprints across projects"""
    seen_fingerprints = {}
    
    for project in projects:
        fp = tuple(sorted(project['fingerprints']['key_fingerprint']))
        
        if fp in seen_fingerprints:
            raise ValueError(
                f"Duplicate fingerprint: {project['project_name']} "
                f"and {seen_fingerprints[fp]} have identical key fingerprints"
            )
        
        seen_fingerprints[fp] = project['project_name']
```

## Fingerprint Evolution

### Versioning

Projects may change their tagging strategy over time:

```json
{
  "project_name": "webapp",
  "fingerprints": {
    "key_fingerprint": ["Project", "Environment", "ManagedBy"],
    "historical_fingerprints": [
      {
        "version": "1.0.0",
        "valid_until": "2024-12-31",
        "key_fingerprint": ["Project", "Env"]
      }
    ]
  }
}
```

### Migration Support

```python
def match_with_history(resource_tags, project):
    """Match against current and historical fingerprints"""
    
    # Try current fingerprint first
    if matches_fingerprint(resource_tags, project['fingerprints']):
        return {'matched': True, 'version': 'current'}
    
    # Try historical fingerprints
    for historical in project['fingerprints'].get('historical_fingerprints', []):
        if matches_fingerprint(resource_tags, historical):
            return {
                'matched': True,
                'version': historical['version'],
                'deprecated': True
            }
    
    return {'matched': False}
```

## Output Format

### Matched Resource

```json
{
  "resource_arn": "arn:aws:s3:::bucket-name",
  "matched_project": "aws-account-baseline",
  "confidence": 1.0,
  "fingerprint_type": "keyvalue",
  "tags": [
    {"Key": "Project", "Value": "aws-account-baseline"},
    {"Key": "ManagedBy", "Value": "opentofu"}
  ]
}
```

### Orphaned Resource

```json
{
  "resource_arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123",
  "matched_project": null,
  "fingerprint": ["Environment", "Name", "Owner"],
  "cluster_id": "orphan-cluster-1",
  "cluster_size": 5,
  "tags": [
    {"Key": "Environment", "Value": "test"},
    {"Key": "Name", "Value": "test-instance"},
    {"Key": "Owner", "Value": "john.doe"}
  ]
}
```

## Implementation Notes

### Performance

- Use hash tables for O(1) fingerprint lookups
- Cache compiled wildcard patterns
- Batch resource processing

### Storage

- Store fingerprints as JSON files (human-readable)
- Consider SQLite for large registries (>100 projects)
- Index by fingerprint hash for fast lookups

### Extensibility

- Support custom matching functions
- Allow plugin-based fingerprint extractors
- Enable user-defined confidence scoring
