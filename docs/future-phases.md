# Future Phases Roadmap

## Phase 2: Multi-Signal Clustering

### Overview

Phase 2 addresses environments where tagging is inconsistent or absent by using multiple signals to identify resource relationships.

### Clustering Signals

#### 1. Temporal Clustering

**Concept**: Resources created within a narrow time window likely belong together.

**Implementation**:
- Query CloudTrail for resource creation events
- Group resources created within 5-minute windows
- Weight by same IAM principal (user/role)

**Example**:
```
2025-01-15 10:15:23 - EC2 instance created by jenkins-deploy
2025-01-15 10:15:45 - Security group created by jenkins-deploy
2025-01-15 10:16:12 - EBS volume created by jenkins-deploy
→ Likely same deployment
```

#### 2. Naming Convention Patterns

**Concept**: Resources follow naming patterns even without tags.

**Implementation**:
- Extract common prefixes/suffixes
- Identify delimiter patterns (-, _, .)
- Group by naming similarity

**Example**:
```
webapp-prod-ec2-1
webapp-prod-ec2-2
webapp-prod-rds-primary
→ Pattern: webapp-prod-*
```

#### 3. Network Topology

**Concept**: Resources in same VPC/subnet/security group are related.

**Implementation**:
- Build network relationship graph
- Identify connected components
- Weight by security group membership

**Example**:
```
VPC: vpc-abc123
├── Subnet: subnet-def456
│   ├── EC2: i-111
│   └── EC2: i-222
└── Security Group: sg-789
    ├── EC2: i-111
    └── RDS: db-333
→ All related via network topology
```

#### 4. IAM Relationships

**Concept**: Resources using same IAM roles/policies are related.

**Implementation**:
- Map resources to IAM roles
- Group by role usage
- Identify trust relationships

**Example**:
```
Lambda: function-a → Role: app-lambda-role
Lambda: function-b → Role: app-lambda-role
DynamoDB: table-x ← Policy: app-lambda-role
→ All related via IAM
```

#### 5. Resource Dependencies

**Concept**: Resources reference each other in configurations.

**Implementation**:
- Extract ARN references from resource configs
- Build dependency graph
- Identify connected components

**Example**:
```
Lambda env vars: DDB_TABLE=arn:aws:dynamodb:...:table/users
ALB target group: Targets=[i-111, i-222]
→ Direct dependencies
```

### Clustering Algorithm

```python
def multi_signal_clustering(resources):
    """Cluster resources using multiple signals"""
    
    # Calculate similarity matrix
    similarity = {}
    for r1 in resources:
        for r2 in resources:
            if r1 != r2:
                score = 0.0
                
                # Temporal similarity (0-0.3)
                if abs(r1.created_time - r2.created_time) < 300:  # 5 min
                    score += 0.3
                
                # Naming similarity (0-0.2)
                if naming_similarity(r1.name, r2.name) > 0.7:
                    score += 0.2
                
                # Network similarity (0-0.3)
                if same_vpc(r1, r2):
                    score += 0.1
                if same_security_group(r1, r2):
                    score += 0.2
                
                # IAM similarity (0-0.2)
                if same_iam_role(r1, r2):
                    score += 0.2
                
                similarity[(r1, r2)] = score
    
    # Cluster using threshold
    clusters = []
    threshold = 0.5
    
    # ... clustering algorithm (e.g., hierarchical clustering)
    
    return clusters
```

### Deliverables

- `scripts/multi-signal-clustering.py` - Clustering implementation
- `scripts/extract-signals.sh` - Signal extraction from AWS
- Documentation on signal weighting and tuning

## Phase 3: Risk Assessment

### Overview

Phase 3 analyzes discovered orphans to assess their risk and cost impact before cleanup.

### Risk Dimensions

#### 1. Usage Analysis

**Metrics**:
- Last accessed time (CloudWatch, CloudTrail)
- Request count (last 30/60/90 days)
- Data transfer volume
- Connection count

**Risk Levels**:
- **Active** (accessed < 7 days ago) - High risk to delete
- **Dormant** (7-90 days) - Medium risk
- **Inactive** (> 90 days) - Low risk

#### 2. Cost Impact

**Metrics**:
- Monthly cost (Cost Explorer)
- Projected annual cost
- Cost trend (increasing/decreasing)
- Cost per resource type

**Priority**:
- High cost (>$100/month) - High priority cleanup
- Medium cost ($10-100/month) - Medium priority
- Low cost (<$10/month) - Low priority

#### 3. Security Exposure

**Metrics**:
- Public accessibility (internet-facing)
- Security group rules (0.0.0.0/0)
- IAM policy permissions
- Encryption status
- Compliance violations

**Risk Levels**:
- **Critical** - Public + unencrypted + broad permissions
- **High** - Public or broad permissions
- **Medium** - Internal but unencrypted
- **Low** - Private and encrypted

#### 4. Business Criticality

**Metrics**:
- Connected to active resources
- Referenced by other resources
- Part of active VPC
- Has recent CloudTrail activity

**Assessment**:
- **Critical** - Many active dependencies
- **Important** - Some dependencies
- **Isolated** - No dependencies

### Risk Scoring

```python
def calculate_risk_score(resource):
    """Calculate composite risk score (0-100)"""
    
    # Usage score (0-25)
    days_since_access = (now - resource.last_accessed).days
    if days_since_access < 7:
        usage_score = 25
    elif days_since_access < 30:
        usage_score = 15
    elif days_since_access < 90:
        usage_score = 5
    else:
        usage_score = 0
    
    # Cost score (0-25)
    monthly_cost = resource.monthly_cost
    if monthly_cost > 100:
        cost_score = 25
    elif monthly_cost > 10:
        cost_score = 15
    elif monthly_cost > 1:
        cost_score = 5
    else:
        cost_score = 0
    
    # Security score (0-25)
    security_score = 0
    if resource.is_public:
        security_score += 10
    if not resource.is_encrypted:
        security_score += 10
    if resource.has_broad_permissions:
        security_score += 5
    
    # Criticality score (0-25)
    dependency_count = len(resource.dependencies)
    if dependency_count > 10:
        criticality_score = 25
    elif dependency_count > 5:
        criticality_score = 15
    elif dependency_count > 0:
        criticality_score = 5
    else:
        criticality_score = 0
    
    total_score = usage_score + cost_score + security_score + criticality_score
    
    return {
        'total': total_score,
        'usage': usage_score,
        'cost': cost_score,
        'security': security_score,
        'criticality': criticality_score,
        'recommendation': get_recommendation(total_score)
    }

def get_recommendation(score):
    """Get cleanup recommendation based on score"""
    if score < 10:
        return "SAFE_TO_DELETE"
    elif score < 30:
        return "REVIEW_BEFORE_DELETE"
    elif score < 60:
        return "INVESTIGATE_DEPENDENCIES"
    else:
        return "DO_NOT_DELETE"
```

### Report Format

```
=== Risk Assessment Report ===

Resource: arn:aws:ec2:us-east-1:123456789012:instance/i-abc123
Risk Score: 15/100 (Low Risk)

Usage Analysis:
  Last Accessed: 120 days ago
  Request Count (30d): 0
  Status: INACTIVE
  Score: 0/25

Cost Impact:
  Monthly Cost: $45.60
  Annual Projection: $547.20
  Trend: Stable
  Score: 15/25

Security Exposure:
  Public: No
  Encrypted: Yes
  Broad Permissions: No
  Score: 0/25

Business Criticality:
  Dependencies: 0
  Referenced By: 0
  Status: ISOLATED
  Score: 0/25

Recommendation: SAFE_TO_DELETE
Estimated Savings: $547.20/year

Actions:
  1. Create snapshot (if needed)
  2. Stop instance (test for 7 days)
  3. If no issues, terminate
  4. Monitor for unexpected impacts
```

### Deliverables

- `scripts/assess-risk.py` - Risk assessment implementation
- `scripts/generate-cleanup-plan.sh` - Safe cleanup recommendations
- Dashboard/report templates

## Phase 4: Automated Cleanup

### Overview

Phase 4 provides safe, automated cleanup of low-risk orphans.

### Safety Mechanisms

1. **Dry Run Mode** - Preview changes without executing
2. **Backup Creation** - Snapshot before deletion
3. **Gradual Rollout** - Delete in batches with monitoring
4. **Rollback Capability** - Restore from snapshots if needed
5. **Approval Workflow** - Require human approval for high-risk resources

### Cleanup Workflow

```
1. Identify orphans (Phase 1)
2. Assess risk (Phase 3)
3. Filter by risk threshold (e.g., score < 20)
4. Create backups/snapshots
5. Stop resources (test period)
6. Monitor for issues (7 days)
7. If no issues, delete
8. Generate cleanup report
```

### Deliverables

- `scripts/cleanup-orphans.sh` - Automated cleanup
- `scripts/rollback-cleanup.sh` - Restore deleted resources
- Approval workflow integration

## Phase 5: Continuous Monitoring

### Overview

Phase 5 provides ongoing orphan detection and alerting.

### Features

1. **Scheduled Scans** - Daily/weekly orphan detection
2. **Trend Analysis** - Track orphan creation over time
3. **Alerting** - Notify when new orphans detected
4. **Dashboard** - Visual representation of orphan landscape
5. **Cost Tracking** - Monitor savings from cleanup

### Deliverables

- CloudWatch Events integration
- SNS alerting
- Dashboard (CloudWatch/Grafana)
- Historical trend reports

## Implementation Timeline

**Phase 1** (Current): 2-4 weeks
- Tag-based fingerprinting
- Basic orphan identification

**Phase 2** (Future): 4-6 weeks
- Multi-signal clustering
- Handle untagged resources

**Phase 3** (Future): 3-4 weeks
- Risk assessment
- Cleanup recommendations

**Phase 4** (Future): 4-6 weeks
- Automated cleanup
- Safety mechanisms

**Phase 5** (Future): 2-3 weeks
- Continuous monitoring
- Alerting and dashboards

**Total**: 15-23 weeks (4-6 months)
