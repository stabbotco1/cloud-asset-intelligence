# Implementation Guide for AI Agents

## Purpose

This document provides detailed instructions for AI agents (like Claude, ChatGPT, or Copilot) to implement Phase 1: Tag-Based Fingerprinting scripts.

## Target Environment

- **OS**: macOS (scripts should use bash)
- **AWS Authentication**: Assumes AWS CLI configured with valid credentials
- **Dependencies**: AWS CLI, jq, Python 3.8+
- **Output**: Bash scripts in `scripts/` directory

## Implementation Phases

### Phase 1A: Resource Discovery

**Script**: `scripts/scan-resources.sh`

**Purpose**: Discover all tagged resources in AWS account

**Requirements**:
1. Use AWS Resource Groups Tagging API
2. Scan all regions (or configurable region list)
3. Output JSON file with all resources and their tags
4. Handle pagination for large accounts
5. Include resource ARN, tags, and service type

**Expected Output**: `output/discovered-resources.json`
```json
{
  "scan_date": "2025-11-30T14:30:00Z",
  "account_id": "123456789012",
  "regions": ["us-east-1", "us-west-2"],
  "total_resources": 150,
  "resources": [
    {
      "arn": "arn:aws:s3:::bucket-name",
      "service": "s3",
      "region": "us-east-1",
      "tags": [
        {"Key": "Project", "Value": "webapp"},
        {"Key": "Environment", "Value": "prod"}
      ]
    }
  ]
}
```

**Implementation Hints**:
```bash
#!/bin/bash
set -euo pipefail

# Get all resources with tags
aws resourcegroupstaggingapi get-resources \
    --region us-east-1 \
    --output json \
    > output/discovered-resources.json

# Handle pagination if needed
# Use --pagination-token for large result sets
```

### Phase 1B: Fingerprint Extraction

**Script**: `scripts/generate-fingerprints.sh`

**Purpose**: Extract tag fingerprints from discovered resources

**Requirements**:
1. Read `output/discovered-resources.json`
2. Extract both key and key-value fingerprints
3. Cluster resources by fingerprint
4. Output fingerprint clusters

**Expected Output**: `output/fingerprint-clusters.json`
```json
{
  "generated_date": "2025-11-30T14:35:00Z",
  "total_clusters": 5,
  "clusters": [
    {
      "cluster_id": "cluster-1",
      "fingerprint_type": "key",
      "fingerprint": ["Environment", "ManagedBy", "Project"],
      "resource_count": 25,
      "resources": [
        "arn:aws:s3:::bucket1",
        "arn:aws:ec2:us-east-1:123456789012:instance/i-123"
      ]
    },
    {
      "cluster_id": "cluster-2",
      "fingerprint_type": "keyvalue",
      "fingerprint": [
        ["Environment", "prod"],
        ["ManagedBy", "terraform"],
        ["Project", "webapp"]
      ],
      "resource_count": 20,
      "resources": ["..."]
    }
  ]
}
```

**Implementation Hints**:
```python
#!/usr/bin/env python3
import json
from collections import defaultdict

def extract_key_fingerprint(tags):
    """Extract sorted tuple of tag keys"""
    return tuple(sorted([tag['Key'] for tag in tags]))

def extract_keyvalue_fingerprint(tags):
    """Extract sorted tuple of (key, value) pairs"""
    return tuple(sorted([(tag['Key'], tag['Value']) for tag in tags]))

def cluster_resources(resources):
    """Group resources by fingerprints"""
    key_clusters = defaultdict(list)
    keyvalue_clusters = defaultdict(list)
    
    for resource in resources:
        tags = resource.get('tags', [])
        
        key_fp = extract_key_fingerprint(tags)
        keyvalue_fp = extract_keyvalue_fingerprint(tags)
        
        key_clusters[key_fp].append(resource['arn'])
        keyvalue_clusters[keyvalue_fp].append(resource['arn'])
    
    return key_clusters, keyvalue_clusters
```

### Phase 1C: Project Registry

**Script**: `scripts/register-project.sh`

**Purpose**: Create fingerprint registry entry for a known project

**Requirements**:
1. Interactive or file-based input
2. Validate fingerprint format
3. Check for conflicts with existing projects
4. Save to `examples/project-fingerprints/<project-name>.json`

**Usage**:
```bash
# Interactive mode
./scripts/register-project.sh

# From existing project
./scripts/register-project.sh --from-state s3://bucket/terraform.tfstate

# From resource ARNs
./scripts/register-project.sh --from-resources arn1,arn2,arn3
```

**Implementation Hints**:
```bash
#!/bin/bash
set -euo pipefail

PROJECT_NAME=""
DESCRIPTION=""
STATE_LOCATION=""
REPO_URL=""

# Interactive prompts
read -p "Project name: " PROJECT_NAME
read -p "Description: " DESCRIPTION
read -p "State file location (optional): " STATE_LOCATION
read -p "Repository URL (optional): " REPO_URL

# Extract fingerprint from sample resources
echo "Provide sample resource ARNs (one per line, empty line to finish):"
SAMPLE_ARNS=()
while IFS= read -r line; do
    [[ -z "$line" ]] && break
    SAMPLE_ARNS+=("$line")
done

# Get tags for sample resources and extract fingerprint
# ... implementation ...

# Save to registry
cat > "examples/project-fingerprints/${PROJECT_NAME}.json" << EOF
{
  "project_name": "$PROJECT_NAME",
  "description": "$DESCRIPTION",
  "fingerprints": {
    "key_fingerprint": [...],
    "keyvalue_fingerprints": [...]
  },
  "state_file_location": "$STATE_LOCATION",
  "repository": "$REPO_URL",
  "metadata": {
    "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "1.0.0"
  }
}
EOF
```

### Phase 1D: Orphan Identification

**Script**: `scripts/identify-orphans.sh`

**Purpose**: Match discovered resources to known projects and identify orphans

**Requirements**:
1. Load all project fingerprints from registry
2. Load fingerprint clusters
3. Match clusters to projects using matching rules
4. Identify unmatched clusters (orphans)
5. Generate report

**Expected Output**: `output/orphan-report.json` and `output/orphan-report.txt`

**JSON Output**:
```json
{
  "report_date": "2025-11-30T14:40:00Z",
  "total_resources": 150,
  "matched_resources": 125,
  "orphaned_resources": 25,
  "matched_projects": [
    {
      "project_name": "aws-account-baseline",
      "resource_count": 11,
      "confidence": 1.0,
      "resources": ["arn:..."]
    }
  ],
  "orphan_clusters": [
    {
      "cluster_id": "orphan-1",
      "fingerprint": ["Environment", "Name", "Owner"],
      "resource_count": 5,
      "resources": ["arn:..."],
      "recommendation": "Investigate - may be manual console creations"
    }
  ]
}
```

**Text Output**:
```
=== Cloud Asset Intelligence - Orphan Report ===
Generated: 2025-11-30 14:40:00 UTC
Account: 123456789012

Summary:
--------
Total Resources: 150
Matched to Projects: 125 (83%)
Orphaned Resources: 25 (17%)

Matched Projects:
-----------------

Project: aws-account-baseline
Resources: 11 (confidence: 100%)
  ✓ arn:aws:s3:::aws-account-baseline-123456789012-state
  ✓ arn:aws:dynamodb:us-east-1:123456789012:table/aws-account-baseline-locks
  ...

Orphaned Resources:
-------------------

Cluster #1: 5 resources
Fingerprint: [Environment, Name, Owner]
  ⚠ arn:aws:ec2:us-east-1:123456789012:instance/i-abc123
  ⚠ arn:aws:ec2:us-east-1:123456789012:volume/vol-def456
  ...
Recommendation: Investigate - may be manual console creations

Cluster #2: 20 resources
Fingerprint: [Project=old-app, Team=legacy]
  ⚠ arn:aws:s3:::old-app-bucket
  ⚠ arn:aws:lambda:us-east-1:123456789012:function:old-function
  ...
Recommendation: Likely forgotten project - review for cleanup
```

**Implementation Hints**:
```python
#!/usr/bin/env python3
import json
from pathlib import Path

def load_project_registry():
    """Load all project fingerprints"""
    projects = []
    registry_dir = Path("examples/project-fingerprints")
    
    for fp_file in registry_dir.glob("*.json"):
        with open(fp_file) as f:
            projects.append(json.load(f))
    
    return projects

def match_cluster_to_project(cluster, projects):
    """Find best matching project for a cluster"""
    best_match = None
    best_confidence = 0.0
    
    for project in projects:
        confidence = calculate_confidence(cluster, project)
        if confidence > best_confidence:
            best_confidence = confidence
            best_match = project
    
    return best_match, best_confidence

def identify_orphans(clusters, projects):
    """Identify clusters not matching any project"""
    matched = []
    orphans = []
    
    for cluster in clusters:
        project, confidence = match_cluster_to_project(cluster, projects)
        
        if confidence >= 0.6:  # Threshold for match
            matched.append({
                'cluster': cluster,
                'project': project,
                'confidence': confidence
            })
        else:
            orphans.append(cluster)
    
    return matched, orphans
```

### Phase 1E: State File Verification

**Script**: `scripts/verify-state.sh`

**Purpose**: For matched projects, verify resources exist in their state files

**Requirements**:
1. For each matched project, load its state file
2. Extract resource ARNs from state
3. Compare with discovered resources
4. Flag resources in AWS but not in state (potential orphans within known projects)

**Expected Output**: `output/state-verification.json`
```json
{
  "verification_date": "2025-11-30T14:45:00Z",
  "projects": [
    {
      "project_name": "aws-account-baseline",
      "state_location": "s3://bucket/terraform.tfstate",
      "resources_in_state": 17,
      "resources_in_aws": 11,
      "matched": 11,
      "in_state_not_aws": [
        "aws_iam_role.deploy"
      ],
      "in_aws_not_state": []
    }
  ]
}
```

**Implementation Hints**:
```bash
#!/bin/bash
set -euo pipefail

# Download state file
aws s3 cp s3://bucket/terraform.tfstate /tmp/state.json

# Extract ARNs from state
jq -r '.resources[].instances[].attributes.arn // empty' /tmp/state.json > /tmp/state-arns.txt

# Compare with discovered resources
# ... implementation ...
```

## Script Organization

### Directory Structure

```
scripts/
├── scan-resources.sh           # Phase 1A
├── generate-fingerprints.sh    # Phase 1B (Python)
├── register-project.sh         # Phase 1C
├── identify-orphans.sh         # Phase 1D (Python)
├── verify-state.sh             # Phase 1E
└── lib/
    ├── aws-utils.sh            # Shared AWS functions
    ├── fingerprint.py          # Fingerprint extraction library
    └── matching.py             # Matching algorithms library
```

### Shared Libraries

**lib/aws-utils.sh**:
```bash
#!/bin/bash

get_account_id() {
    aws sts get-caller-identity --query 'Account' --output text
}

get_all_regions() {
    aws ec2 describe-regions --query 'Regions[].RegionName' --output text
}

check_aws_auth() {
    if ! aws sts get-caller-identity &>/dev/null; then
        echo "ERROR: AWS credentials not configured"
        exit 1
    fi
}
```

**lib/fingerprint.py**:
```python
#!/usr/bin/env python3
"""Fingerprint extraction and matching library"""

def extract_key_fingerprint(tags):
    """Extract tag key fingerprint"""
    return tuple(sorted([tag['Key'] for tag in tags]))

def extract_keyvalue_fingerprint(tags):
    """Extract tag key-value fingerprint"""
    return tuple(sorted([(tag['Key'], tag['Value']) for tag in tags]))

def calculate_confidence(resource_tags, project_fingerprint):
    """Calculate match confidence (0.0 to 1.0)"""
    # Implementation from fingerprint-specification.md
    pass
```

## Testing Strategy

### Unit Tests

Create `tests/` directory with:
- `test_fingerprint.py` - Test fingerprint extraction
- `test_matching.py` - Test matching algorithms
- `test_clustering.py` - Test resource clustering

### Integration Tests

Create `tests/integration/` with:
- Sample AWS resource data
- Sample project fingerprints
- Expected output files
- Test runner script

### Example Test

```python
# tests/test_fingerprint.py
import unittest
from scripts.lib.fingerprint import extract_key_fingerprint

class TestFingerprint(unittest.TestCase):
    def test_key_fingerprint_extraction(self):
        tags = [
            {'Key': 'Project', 'Value': 'webapp'},
            {'Key': 'Environment', 'Value': 'prod'},
            {'Key': 'ManagedBy', 'Value': 'terraform'}
        ]
        
        expected = ('Environment', 'ManagedBy', 'Project')
        actual = extract_key_fingerprint(tags)
        
        self.assertEqual(expected, actual)
```

## Error Handling

All scripts should:
1. Check AWS authentication before running
2. Validate input files exist
3. Handle API rate limiting (exponential backoff)
4. Provide clear error messages
5. Exit with appropriate codes (0=success, 1=error)

**Example**:
```bash
#!/bin/bash
set -euo pipefail

# Check AWS auth
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

# Check dependencies
if ! command -v jq &>/dev/null; then
    echo "ERROR: jq not installed"
    echo "Install: brew install jq"
    exit 1
fi
```

## Output Directory Structure

```
output/
├── discovered-resources.json      # Phase 1A output
├── fingerprint-clusters.json      # Phase 1B output
├── orphan-report.json             # Phase 1D output
├── orphan-report.txt              # Phase 1D output (human-readable)
├── state-verification.json        # Phase 1E output
└── logs/
    ├── scan-resources.log
    ├── generate-fingerprints.log
    └── identify-orphans.log
```

## Success Criteria

Phase 1 implementation is complete when:
1. ✅ All 5 scripts are functional
2. ✅ Scripts run on macOS with AWS CLI configured
3. ✅ Output files match expected formats
4. ✅ Can successfully identify orphans in test account
5. ✅ Documentation is complete and accurate
6. ✅ Example project fingerprint exists (aws-account-baseline)

## Next Steps for AI Agent

1. Create `scripts/` directory structure
2. Implement Phase 1A (scan-resources.sh)
3. Implement Phase 1B (generate-fingerprints.sh)
4. Implement Phase 1C (register-project.sh)
5. Implement Phase 1D (identify-orphans.sh)
6. Implement Phase 1E (verify-state.sh)
7. Create shared libraries
8. Add example project fingerprint
9. Test end-to-end workflow
10. Document any deviations from this spec
