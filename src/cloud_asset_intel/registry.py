"""Project fingerprint registry management."""

from datetime import datetime
from typing import Any, Dict, List

import boto3
from rich.console import Console
from rich.prompt import Prompt

from .fingerprint import extract_key_fingerprint, extract_keyvalue_fingerprint


console = Console()


def register_project_fingerprint(
    name: str,
    description: str = "",
    state_location: str = "",
    repository: str = "",
    interactive: bool = True,
) -> Dict[str, Any]:
    """
    Register a new project fingerprint.
    
    Args:
        name: Project name
        description: Project description
        state_location: Terraform state file location
        repository: Repository URL
        interactive: Enable interactive mode for sample resource collection
        
    Returns:
        Project fingerprint dictionary
    """
    if interactive:
        console.print(f"\n[bold]Registering project: {name}[/bold]\n")
        
        if not description:
            description = Prompt.ask("Project description")
        
        if not state_location:
            state_location = Prompt.ask(
                "Terraform state location (optional)",
                default=""
            )
        
        if not repository:
            repository = Prompt.ask(
                "Repository URL (optional)",
                default=""
            )
        
        # Collect sample resources
        console.print("\n[bold]Provide sample resource ARNs to extract fingerprint:[/bold]")
        console.print("Enter ARNs one per line, empty line to finish:\n")
        
        sample_arns = []
        while True:
            arn = Prompt.ask("ARN", default="")
            if not arn:
                break
            sample_arns.append(arn)
        
        if not sample_arns:
            raise ValueError("At least one sample resource ARN is required")
        
        # Extract fingerprint from sample resources
        fingerprints = _extract_fingerprints_from_arns(sample_arns)
    else:
        # Non-interactive mode - create empty fingerprint template
        fingerprints = {
            "key_fingerprint": [],
            "keyvalue_fingerprints": [],
        }
    
    return {
        "project_name": name,
        "description": description,
        "fingerprints": fingerprints,
        "state_file_location": state_location,
        "repository": repository,
        "metadata": {
            "created": datetime.utcnow().isoformat() + "Z",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
        },
    }


def _extract_fingerprints_from_arns(arns: List[str]) -> Dict[str, Any]:
    """Extract fingerprints from sample resource ARNs."""
    session = boto3.Session()
    client = session.client("resourcegroupstaggingapi")
    
    # Get tags for each ARN
    all_tags = []
    for arn in arns:
        try:
            response = client.get_resources(ResourceARNList=[arn])
            for resource in response.get("ResourceTagMappingList", []):
                tags = [
                    {"Key": tag["Key"], "Value": tag["Value"]}
                    for tag in resource.get("Tags", [])
                ]
                if tags:
                    all_tags.append(tags)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get tags for {arn}: {e}[/yellow]")
    
    if not all_tags:
        raise ValueError("No tags found on sample resources")
    
    # Extract common key fingerprint
    key_fingerprints = [extract_key_fingerprint(tags) for tags in all_tags]
    common_keys = set(key_fingerprints[0])
    for fp in key_fingerprints[1:]:
        common_keys &= set(fp)
    
    # Extract key-value fingerprints (unique combinations)
    keyvalue_fingerprints = []
    seen = set()
    for tags in all_tags:
        kv_fp = extract_keyvalue_fingerprint(tags)
        if kv_fp not in seen:
            seen.add(kv_fp)
            keyvalue_fingerprints.append(dict(kv_fp))
    
    return {
        "key_fingerprint": sorted(common_keys),
        "keyvalue_fingerprints": keyvalue_fingerprints,
    }
