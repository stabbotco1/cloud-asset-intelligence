"""Command-line interface for Cloud Asset Intelligence."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .scanner import scan_aws_resources
from .fingerprint import generate_fingerprint_clusters
from .matcher import identify_orphans
from .registry import register_project_fingerprint

app = typer.Typer(
    name="cloud-asset-intel",
    help="Forensic discovery and analysis of cloud resources",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"cloud-asset-intelligence version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Cloud Asset Intelligence - Identify orphaned cloud resources."""
    pass


@app.command()
def scan(
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region to scan"),
    output: Path = typer.Option(
        "output/resources.json", "--output", "-o", help="Output file path"
    ),
    all_regions: bool = typer.Option(False, "--all-regions", help="Scan all AWS regions"),
):
    """Scan AWS account for all tagged resources."""
    console.print("[bold blue]🔍 Scanning AWS resources...[/bold blue]")
    
    try:
        regions = [region] if not all_regions else None
        resources = scan_aws_resources(regions=regions)
        
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(output, "w") as f:
            json.dump(resources, f, indent=2)
        
        console.print(f"[green]✓[/green] Found {resources['total_resources']} resources")
        console.print(f"[green]✓[/green] Saved to: {output}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@app.command()
def fingerprint(
    resources: Path = typer.Option(
        "output/resources.json", "--resources", "-r", help="Resources JSON file"
    ),
    output: Path = typer.Option(
        "output/fingerprint-clusters.json", "--output", "-o", help="Output file path"
    ),
):
    """Generate fingerprint clusters from discovered resources."""
    console.print("[bold blue]🔬 Generating fingerprint clusters...[/bold blue]")
    
    try:
        # Load resources
        with open(resources) as f:
            resource_data = json.load(f)
        
        # Generate clusters
        clusters = generate_fingerprint_clusters(resource_data["resources"])
        
        # Save results
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(clusters, f, indent=2)
        
        console.print(f"[green]✓[/green] Generated {clusters['total_clusters']} clusters")
        console.print(f"[green]✓[/green] Saved to: {output}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@app.command()
def identify(
    resources: Path = typer.Option(
        "output/resources.json", "--resources", "-r", help="Resources JSON file"
    ),
    registry: Path = typer.Option(
        "examples/project-fingerprints", "--registry", help="Project fingerprints directory"
    ),
    threshold: float = typer.Option(
        0.6, "--threshold", "-t", help="Confidence threshold (0.0-1.0)"
    ),
    output: Path = typer.Option(
        "output/orphan-report.json", "--output", "-o", help="Output file path"
    ),
):
    """Identify orphaned resources by matching to known projects."""
    console.print("[bold blue]🔎 Identifying orphaned resources...[/bold blue]")
    
    try:
        # Load resources
        with open(resources) as f:
            resource_data = json.load(f)
        
        # Identify orphans
        report = identify_orphans(
            resource_data["resources"],
            registry_path=registry,
            threshold=threshold
        )
        
        # Save JSON report
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        
        # Display summary
        total = report["total_resources"]
        matched = report["matched_resources"]
        orphaned = report["orphaned_resources"]
        
        table = Table(title="Orphan Detection Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        
        table.add_row("Total Resources", str(total), "100%")
        table.add_row("Matched to Projects", str(matched), f"{matched/total*100:.1f}%")
        table.add_row("Orphaned Resources", str(orphaned), f"{orphaned/total*100:.1f}%")
        
        console.print(table)
        console.print(f"\n[green]✓[/green] Report saved to: {output}")
        
        # Save text report
        text_output = output.with_suffix(".txt")
        with open(text_output, "w") as f:
            f.write(format_text_report(report))
        console.print(f"[green]✓[/green] Text report saved to: {text_output}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


@app.command()
def register(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", "--description", "-d", help="Project description"),
    state_location: str = typer.Option("", "--state", "-s", help="Terraform state location"),
    repository: str = typer.Option("", "--repo", "-r", help="Repository URL"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive mode"),
):
    """Register a new project fingerprint."""
    console.print(f"[bold blue]📝 Registering project: {name}[/bold blue]")
    
    try:
        fingerprint = register_project_fingerprint(
            name=name,
            description=description,
            state_location=state_location,
            repository=repository,
            interactive=interactive,
        )
        
        output_path = Path(f"examples/project-fingerprints/{name}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(fingerprint, f, indent=2)
        
        console.print(f"[green]✓[/green] Project registered: {output_path}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


def format_text_report(report: dict) -> str:
    """Format JSON report as human-readable text."""
    lines = [
        "=" * 60,
        "Cloud Asset Intelligence - Orphan Report",
        "=" * 60,
        f"Generated: {report['report_date']}",
        f"Account: {report.get('account_id', 'N/A')}",
        "",
        "Summary:",
        "-" * 60,
        f"Total Resources: {report['total_resources']}",
        f"Matched to Projects: {report['matched_resources']} ({report['matched_resources']/report['total_resources']*100:.1f}%)",
        f"Orphaned Resources: {report['orphaned_resources']} ({report['orphaned_resources']/report['total_resources']*100:.1f}%)",
        "",
    ]
    
    if report["matched_projects"]:
        lines.extend([
            "Matched Projects:",
            "-" * 60,
            "",
        ])
        for project in report["matched_projects"]:
            lines.extend([
                f"Project: {project['project_name']}",
                f"Resources: {project['resource_count']} (confidence: {project['confidence']*100:.0f}%)",
                "",
            ])
    
    if report["orphan_clusters"]:
        lines.extend([
            "Orphaned Resources:",
            "-" * 60,
            "",
        ])
        for i, cluster in enumerate(report["orphan_clusters"], 1):
            lines.extend([
                f"Cluster #{i}: {cluster['resource_count']} resources",
                f"Fingerprint: {cluster['fingerprint']}",
                f"Recommendation: {cluster.get('recommendation', 'Review manually')}",
                "",
            ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    app()
