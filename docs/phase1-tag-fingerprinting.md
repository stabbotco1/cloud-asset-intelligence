# Phase 1: Tag-Based Fingerprinting

## Overview

Phase 1 implements orphan detection using **tag-based fingerprinting** - identifying resource groups by their tag patterns and matching them to known IaC projects.

## Core Concept

Resources deployed together from the same IaC project typically share consistent tag patterns:

**Example Project Tags**:
```json
{
  "Project": "web-application",
  "Environment": "production",
  "ManagedBy": "terraform",
  "CostCenter": "engineering",
  "Owner": "platform-team"
}
```

All resources from this project will have these same 5 tag keys (and often same values).

## Two Fingerprinting Approaches

### 1. Tag Key Fingerprints

**Definition**: The ordered set of tag keys present on a resource.

**Example**:
```
Resource A: {Project, Environment, ManagedBy, CostCenter, Owner}
Resource B: {Project, Environment, ManagedBy, CostCenter, Owner}
Resource C: {Project, Environment, ManagedBy}

Fingerprint 1: [CostCenter, Environment, ManagedBy, Owner, Project]
Fingerprint 2: [Environment, ManagedBy, Project]

Resources A & B match Fingerprint 1 (likely same project)
Resource C matches Fingerprint 2 (different project or incomplete tagging)
```

**Advantages**:
- Works even if tag values differ (e.g., different environments)
- Identifies project "families" (dev/staging/prod)
- Tolerant of value variations

**Disadvantages**:
- Lower confidence matching
- May group unrelated resources with similar tag strategies

### 2. Tag Key-Value Fingerprints

**Definition**: The complete set of tag key-value pairs on a resource.

**Example**:
```
Resource A: {Project=webapp, Environment=prod, ManagedBy=terraform}
Resource B: {Project=webapp, Environment=prod, ManagedBy=terraform}
Resource C: {Project=webapp, Environment=dev, ManagedBy=terraform}

Fingerprint 1: {Project=webapp, Environment=prod, ManagedBy=terraform}
Fingerprint 2: {Project=webapp, Environment=dev, ManagedBy=terraform}

Resources A & B match Fingerprint 1 (same deployment)
Resource C matches Fingerprint 2 (different deployment, same project)
```

**Advantages**:
- High confidence matching
- Distinguishes between environments
- Precise resource grouping

**Disadvantages**:
- Sensitive to tag value changes
- May split related resources into separate groups
- Requires exact value matching

## Implementation Strategy

### Step 1: Resource Discovery

Scan AWS account for all resources with tags:

```bash
# Use AWS Resource Groups Tagging API
aws resourcegroupstaggingapi get-resources \
    --region us-east-1 \
    --output json
```

**Output**: List of all tagged resources with their ARNs and tags

### Step 2: Fingerprint Extraction

For each resource, extract both fingerprint types:

**Tag Key Fingerprint**:
```python
def extract_key_fingerprint(tags):
    """Extract ordered set of tag keys"""
    keys = sorted([tag['Key'] for tag in tags])
    return tuple(keys)  # Immutable, hashable

# Example
tags = [
    {'Key': 'Project', 'Value': 'webapp'},
    {'Key': 'Environment', 'Value': 'prod'},
    {'Key': 'ManagedBy', 'Value': 'terraform'}
]
fingerprint = extract_key_fingerprint(tags)
# Result: ('Environment', 'ManagedBy', 'Project')
```

**Tag Key-Value Fingerprint**:
```python
def extract_keyvalue_fingerprint(tags):
    """Extract ordered set of tag key-value pairs"""
    pairs = sorted([(tag['Key'], tag['Value']) for tag in tags])
    return tuple(pairs)  # Immutable, hashable

# Example
fingerprint = extract_keyvalue_fingerprint(tags)
# Result: (('Environment', 'prod'), ('ManagedBy', 'terraform'), ('Project', 'webapp'))
```

### Step 3: Resource Clustering

Group resources by fingerprint:

```python
from collections import defaultdict

def cluster_by_fingerprint(resources, fingerprint_func):
    """Group resources by their fingerprint"""
    clusters = defaultdict(list)
    
    for resource in resources:
        fingerprint = fingerprint_func(resource['Tags'])
        clusters[fingerprint].append(resource)
    
    return dict(clusters)

# Example output
{
    ('Environment', 'ManagedBy', 'Project'): [
        {'ResourceARN': 'arn:aws:s3:::bucket1', 'Tags': [...]},
        {'ResourceARN': 'arn:aws:ec2:...:instance/i-123', 'Tags': [...]}
    ],
    ('CostCenter', 'Environment', 'Owner', 'Project'): [
        {'ResourceARN': 'arn:aws:rds:...:db:mydb', 'Tags': [...]}
    ]
}
```

### Step 4: Known Project Registry

Create fingerprint registry for known projects:

**File**: `examples/project-fingerprints/aws-account-baseline.json`
```json
{
  "project_name": "aws-account-baseline",
  "description": "Account-level foundational infrastructure",
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
        "Project": "aws-account-baseline"
      },
      {
        "Application": "aws-account-baseline",
        "Description": "Account-level foundational infrastructure",
        "Environment": "account",
        "ManagedBy": "bootstrap",
        "Project": "aws-account-baseline"
      }
    ]
  },
  "state_file_location": "s3://aws-account-baseline-123456789012-state/baseline/terraform.tfstate",
  "repository": "https://github.com/yourusername/aws-account-baseline"
}
```

### Step 5: Orphan Identification

Match discovered clusters to known projects:

```python
def identify_orphans(clusters, known_projects):
    """Identify resources not matching any known project"""
    
    matched = []
    orphans = []
    
    for fingerprint, resources in clusters.items():
        matched_project = None
        
        # Try to match against known projects
        for project in known_projects:
            if fingerprint_matches_project(fingerprint, project):
                matched_project = project
                break
        
        if matched_project:
            matched.append({
                'fingerprint': fingerprint,
                'project': matched_project['project_name'],
                'resources': resources
            })
        else:
            orphans.append({
                'fingerprint': fingerprint,
                'resource_count': len(resources),
                'resources': resources
            })
    
    return matched, orphans
```

### Step 6: Report Generation

Generate human-readable reports:

**Matched Resources Report**:
```
=== Matched Resources ===

Project: aws-account-baseline
Fingerprint: (Application, Description, Environment, ManagedBy, Name, Project)
Resources: 11
  - arn:aws:s3:::aws-account-baseline-123456789012-state
  - arn:aws:dynamodb:us-east-1:123456789012:table/aws-account-baseline-locks
  - arn:aws:sns:us-east-1:123456789012:aws-account-baseline-notifications
  ...
```

**Orphan Resources Report**:
```
=== Orphaned Resources ===

Unknown Fingerprint #1: (Environment, Name, Owner)
Resources: 5
  - arn:aws:ec2:us-east-1:123456789012:instance/i-abc123
  - arn:aws:ec2:us-east-1:123456789012:volume/vol-def456
  ...
Recommendation: Investigate - may be manual console creations

Unknown Fingerprint #2: (Project, Team)
Resources: 23
  - arn:aws:s3:::old-project-bucket
  - arn:aws:lambda:us-east-1:123456789012:function:old-function
  ...
Recommendation: Likely forgotten project - review for cleanup
```

## Verification Against State Files

For matched projects, verify resources exist in state:

```bash
# Extract resource ARNs from Terraform state
terraform state list | while read resource; do
    terraform state show "$resource" | grep "arn"
done

# Compare with discovered resources
# Resources in AWS but not in state = potential orphans
```

## Handling Edge Cases

### Partial Tagging

**Problem**: Some resources in a project have incomplete tags

**Solution**: Use "fuzzy matching" - match if subset of tags present
```python
def fuzzy_match(resource_tags, project_fingerprint):
    """Match if resource has at least 80% of project tags"""
    resource_keys = set(tag['Key'] for tag in resource_tags)
    project_keys = set(project_fingerprint['key_fingerprint'])
    
    overlap = len(resource_keys & project_keys)
    threshold = 0.8 * len(project_keys)
    
    return overlap >= threshold
```

### Multi-Environment Projects

**Problem**: Same project deployed to dev/staging/prod with different tag values

**Solution**: Use key fingerprints for project matching, key-value for environment distinction

### Untagged Resources

**Problem**: Resources with no tags at all

**Solution**: Phase 1 cannot handle - defer to Phase 2 (multi-signal clustering)

## Success Criteria

Phase 1 is successful if it can:
1. ✅ Discover all tagged resources in an account
2. ✅ Group resources by tag fingerprints
3. ✅ Match 90%+ of known project resources correctly
4. ✅ Identify unknown fingerprint patterns
5. ✅ Generate actionable reports

## Limitations

Phase 1 **cannot** handle:
- Untagged resources
- Inconsistently tagged resources
- Resources with no clear tag patterns
- Cross-project dependencies

These are addressed in Phase 2 (multi-signal clustering).

## Next Steps

See [Implementation Guide](implementation-guide.md) for detailed AI agent instructions to build Phase 1 scripts.
