# Cloud Asset Intelligence

**Forensic discovery and analysis of cloud resources to identify orphaned infrastructure.**

[![PyPI version](https://badge.fury.io/py/cloud-asset-intelligence.svg)](https://badge.fury.io/py/cloud-asset-intelligence)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Copyright (c) 2025 Stephen Abbott | MIT License

## Installation

```bash
pip install cloud-asset-intelligence
```

## Quick Start

```bash
# Scan AWS account
cloud-asset-intel scan

# Identify orphans
cloud-asset-intel identify
```

## The Problem

Orphaned cloud resources exist in AWS but aren't tracked in any IaC state file, creating:
- **Security risks** - Unmonitored resources
- **Cost waste** - Continuous billing
- **Compliance gaps** - Incomplete audit trails

## How It Works

Uses **tag-based fingerprinting** to match resources to known projects:
- Extract tag patterns from resources
- Match against known project fingerprints
- Identify orphans with confidence scoring

## Commands

```bash
# Scan resources
cloud-asset-intel scan [--region REGION] [--all-regions]

# Generate fingerprints
cloud-asset-intel fingerprint

# Identify orphans
cloud-asset-intel identify [--threshold 0.6]

# Register project
cloud-asset-intel register PROJECT_NAME
```

## Documentation

See [docs/](docs/) for detailed documentation.

## License

MIT License - Copyright (c) 2025 Stephen Abbott
