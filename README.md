# Cloud Asset Intelligence

**Forensic discovery and analysis of cloud resources to identify, classify, and manage orphaned infrastructure.**

Copyright (c) 2025 Stephen Abbott  
MIT License

## Overview

Cloud Asset Intelligence addresses a critical problem in enterprise cloud environments: **orphaned resources** that exist in AWS but aren't tracked in any Infrastructure as Code (IaC) state file. These orphans create security risks, unnecessary costs, and operational complexity.

This project provides tools to:
- Discover all resources in an AWS account
- Identify resource groupings using tag-based fingerprinting
- Match resources to known IaC projects
- Detect true orphans (resources not managed by any project)
- Assess risk and cost impact of orphaned resources

## The Problem

### Why Orphans Exist

1. **Failed deployments** - Partial infrastructure creation before errors
2. **Manual console changes** - Resources created outside IaC workflows
3. **Deleted state files** - Lost Terraform/OpenTofu state
4. **Team turnover** - Knowledge loss about resource ownership
5. **Multiple IaC projects** - No central inventory across projects

### Business Impact

- **Security Risk**: Unmonitored resources may have vulnerabilities
- **Cost Waste**: Orphaned resources continue billing indefinitely
- **Compliance Gaps**: Audit trails incomplete without resource inventory
- **Operational Complexity**: Unknown dependencies block cleanup efforts

### Current Limitations

Most organizations lack:
- Comprehensive resource inventory across all projects
- Automated orphan detection mechanisms
- Risk assessment for discovered orphans
- Safe cleanup procedures for unmanaged resources

## Solution Approach

### Phase 1: Tag-Based Fingerprinting (Current)

**Core Concept**: Resources from the same IaC deployment share consistent tag patterns.

**Two Fingerprinting Methods**:

1. **Tag Key Fingerprints** - Match resources by tag key sets
   - Example: `{Project, Environment, ManagedBy, CostCenter}`
   - Resources with identical key sets likely related

2. **Tag Key-Value Fingerprints** - Match by specific tag values
   - Example: `Project=myapp, Environment=prod, ManagedBy=terraform`
   - Higher confidence matching than keys alone

**Deliverables**:
- Scripts to scan AWS account for all tagged resources
- Fingerprint extraction and clustering algorithms
- Known project fingerprint registry
- Orphan identification reports

### Phase 2: Multi-Signal Clustering (Future)

For environments without consistent tagging:
- Temporal clustering (creation time proximity)
- Naming convention pattern matching
- Network topology relationships (VPC/subnet/security groups)
- IAM role/policy relationships
- Resource dependency graphs
- CloudTrail event correlation

### Phase 3: Risk Assessment (Future)

Analyze discovered orphans for:
- Last access time (usage patterns)
- Cost impact (monthly spend)
- Security exposure (public access, vulnerabilities)
- Business criticality (connected to active resources)
- Cleanup safety (dependencies, blast radius)

## Quick Start

```bash
# Prerequisites: AWS CLI configured with credentials

# 1. Clone repository
git clone https://github.com/yourusername/cloud-asset-intelligence.git
cd cloud-asset-intelligence

# 2. Scan your AWS account
./scripts/scan-resources.sh

# 3. Generate fingerprint report
./scripts/generate-fingerprints.sh

# 4. Identify orphans
./scripts/identify-orphans.sh
```

## Project Structure

```
cloud-asset-intelligence/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── docs/                              # Comprehensive documentation
│   ├── problem-statement.md           # Detailed problem analysis
│   ├── phase1-tag-fingerprinting.md   # Tag-based implementation
│   ├── fingerprint-specification.md   # Fingerprint format spec
│   ├── implementation-guide.md        # AI agent implementation guide
│   └── future-phases.md               # Phases 2 & 3 roadmap
├── scripts/                           # Implementation scripts
│   ├── scan-resources.sh              # Discover all AWS resources
│   ├── generate-fingerprints.sh       # Extract tag fingerprints
│   ├── identify-orphans.sh            # Match resources to projects
│   └── lib/                           # Shared functions
└── examples/                          # Example fingerprints & reports
    ├── project-fingerprints/          # Known project fingerprints
    └── sample-reports/                # Example output reports
```

## Documentation

- **[Problem Statement](docs/problem-statement.md)** - Detailed analysis of orphan resource challenges
- **[Phase 1: Tag Fingerprinting](docs/phase1-tag-fingerprinting.md)** - Tag-based implementation details
- **[Fingerprint Specification](docs/fingerprint-specification.md)** - Fingerprint format and matching rules
- **[Implementation Guide](docs/implementation-guide.md)** - AI agent instructions for building Phase 1
- **[Future Phases](docs/future-phases.md)** - Roadmap for multi-signal clustering and risk assessment

## Current Status

**Phase 1: Tag-Based Fingerprinting** - In Development

- [x] Project documentation
- [ ] Resource scanning scripts
- [ ] Fingerprint extraction
- [ ] Known project registry
- [ ] Orphan identification
- [ ] Report generation

## Use Cases

### Portfolio/Resume
- Demonstrates cloud architecture expertise
- Shows understanding of enterprise IaC challenges
- Provides concrete examples of problem-solving

### Consulting/SaaS Potential
- Audit service for companies with orphan problems
- Automated cleanup recommendations
- Cost optimization through orphan removal
- Compliance reporting for resource inventory

### Open Source Contribution
- Fills gap in existing cloud management tools
- Reusable across organizations
- Community-driven feature development

## Contributing

This project is in early development. Contributions welcome once Phase 1 is complete.

## License

MIT License - See [LICENSE](LICENSE) file

Copyright (c) 2025 Stephen Abbott

## Author

**Stephen Abbott**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

## Acknowledgments

Inspired by real-world challenges in enterprise cloud resource management and the need for better IaC governance tools.
