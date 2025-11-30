"""AWS resource scanning and discovery."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def scan_aws_resources(
    regions: Optional[List[str]] = None,
    resource_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Scan AWS account for all tagged resources.
    
    Args:
        regions: List of regions to scan (None = all regions)
        resource_types: List of resource types to filter (None = all types)
        
    Returns:
        Dictionary with scan results
    """
    try:
        session = boto3.Session()
        
        # Get account ID
        sts = session.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        
        # Get regions to scan
        if regions is None:
            ec2 = session.client("ec2")
            regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
        
        all_resources = []
        
        for region in regions:
            try:
                resources = _scan_region(session, region, resource_types)
                all_resources.extend(resources)
            except ClientError as e:
                # Skip regions where we don't have access
                if e.response["Error"]["Code"] != "UnauthorizedOperation":
                    raise
        
        return {
            "scan_date": datetime.utcnow().isoformat() + "Z",
            "account_id": account_id,
            "regions": regions,
            "total_resources": len(all_resources),
            "resources": all_resources,
        }
        
    except NoCredentialsError:
        raise RuntimeError(
            "AWS credentials not found. "
            "Configure credentials using 'aws configure' or environment variables."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to scan AWS resources: {e}")


def _scan_region(
    session: boto3.Session,
    region: str,
    resource_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Scan a single AWS region for tagged resources."""
    client = session.client("resourcegroupstaggingapi", region_name=region)
    
    resources = []
    pagination_token = None
    
    while True:
        kwargs = {"ResourcesPerPage": 100}
        
        if resource_types:
            kwargs["ResourceTypeFilters"] = resource_types
        
        if pagination_token:
            kwargs["PaginationToken"] = pagination_token
        
        try:
            response = client.get_resources(**kwargs)
            
            for resource in response.get("ResourceTagMappingList", []):
                resources.append({
                    "arn": resource["ResourceARN"],
                    "service": _extract_service_from_arn(resource["ResourceARN"]),
                    "region": region,
                    "tags": [
                        {"Key": tag["Key"], "Value": tag["Value"]}
                        for tag in resource.get("Tags", [])
                    ],
                })
            
            pagination_token = response.get("PaginationToken")
            if not pagination_token:
                break
                
        except ClientError as e:
            # Skip if we don't have permission in this region
            if e.response["Error"]["Code"] in ["AccessDeniedException", "UnauthorizedOperation"]:
                break
            raise
    
    return resources


def _extract_service_from_arn(arn: str) -> str:
    """Extract service name from ARN."""
    # ARN format: arn:partition:service:region:account-id:resource
    parts = arn.split(":")
    if len(parts) >= 3:
        return parts[2]
    return "unknown"
