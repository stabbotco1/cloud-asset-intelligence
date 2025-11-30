# Cloud Asset Intelligence

**Forensic discovery and analysis of cloud resources to identify orphaned infrastructure.**

[![PyPI version](https://badge.fury.io/py/cloud-asset-intelligence.svg)](https://badge.fury.io/py/cloud-asset-intelligence)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Copyright (c) 2025 Stephen Abbott | MIT License

## Cloud Provider Support

**Current**: AWS (Amazon Web Services)  
**Planned**: Azure, Google Cloud Platform

> This tool currently targets AWS infrastructure. The orphan detection problem is cloud-provider agnostic, and support for Azure and GCP is planned for future releases.

## Installation

```bash
# Using pip
pip install cloud-asset-intelligence

# Using uv (recommended)
uv pip install cloud-asset-intelligence

# Using pipx (isolated environment)
pipx install cloud-asset-intelligence
```

## Quick Start

```bash
# Scan AWS account (requires AWS CLI configured)
cloud-asset-intel scan

# Identify orphans
cloud-asset-intel identify

# View results
cat output/orphan-report.txt
```

## The Problem

Orphaned cloud resources exist in AWS but aren't tracked in any IaC state file, creating:
- **Security risks** - Unmonitored resources with potential vulnerabilities
- **Cost waste** - Continuous billing for unused infrastructure
- **Compliance gaps** - Incomplete audit trails and resource inventory

This problem affects all cloud providers (AWS, Azure, GCP) where Infrastructure as Code is used.

## How It Works

Uses **tag-based fingerprinting** to match resources to known projects:
1. Scan AWS account for all tagged resources
2. Extract tag patterns (fingerprints) from resources
3. Match against known project fingerprints
4. Identify orphans with confidence scoring (0.6-1.0)
5. Generate actionable reports

**Partial Matching**: Handles incomplete tagging with weighted confidence scoring for critical tags (Project, ManagedBy, Application).

## Commands

```bash
# Scan resources
cloud-asset-intel scan                    # Single region (us-east-1)
cloud-asset-intel scan --all-regions      # All AWS regions
cloud-asset-intel scan --region us-west-2 # Specific region

# Generate fingerprints
cloud-asset-intel fingerprint

# Identify orphans
cloud-asset-intel identify                # Default threshold (0.6)
cloud-asset-intel identify --threshold 0.7 # Stricter matching

# Register project
cloud-asset-intel register my-project     # Interactive mode
```

## AWS Credentials

Uses boto3 credential discovery (same as AWS CLI):
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS credentials file (`~/.aws/credentials`)
- IAM roles (EC2, Lambda, ECS)
- AWS SSO sessions

If `aws sts get-caller-identity` works, this tool will work.

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/cloud-asset-intelligence.git
cd cloud-asset-intelligence

# Install with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## Documentation

- **[Problem Statement](docs/problem-statement.md)** - Enterprise orphan challenges
- **[Phase 1: Tag Fingerprinting](docs/phase1-tag-fingerprinting.md)** - Implementation details
- **[Partial Matching](docs/partial-matching.md)** - Confidence scoring algorithms
- **[Fingerprint Specification](docs/fingerprint-specification.md)** - Technical spec
- **[Future Phases](docs/future-phases.md)** - Multi-cloud roadmap

## Roadmap

- **Phase 1** (Current): AWS tag-based fingerprinting
- **Phase 2** (Planned): Multi-signal clustering (temporal, naming, network)
- **Phase 3** (Planned): Risk assessment (usage, cost, security)
- **Phase 4** (Planned): Azure and GCP support
- **Phase 5** (Planned): Automated cleanup with safety mechanisms

## Requirements

- Python 3.10+
- AWS CLI configured with valid credentials
- Appropriate AWS IAM permissions for resource scanning

## License

MIT License - Copyright (c) 2025 Stephen Abbott

See [LICENSE](LICENSE) file for details.
