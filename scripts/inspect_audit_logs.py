#!/usr/bin/env python3
"""Audit Log Inspector - Browse GitHub webhook audit logs with rich formatting.

Usage:
    # List all webhooks from today
    python scripts/inspect_audit_logs.py

    # List webhooks from specific date
    python scripts/inspect_audit_logs.py --date 2025-11-17

    # Show details for specific delivery
    python scripts/inspect_audit_logs.py --delivery-id 500551c0-c3dd-11f0-8823-a64aea91a0b5

    # Filter by event type
    python scripts/inspect_audit_logs.py --event pull_request

    # Filter by repository
    python scripts/inspect_audit_logs.py --repo silverbeer/missing-table

    # Show full payload (verbose)
    python scripts/inspect_audit_logs.py --delivery-id <id> --verbose
"""

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def load_audit_logs(date_str: str) -> list[dict[str, Any]]:
    """Load audit logs for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        List of audit log entries
    """
    log_file = Path(f"logs/webhooks/webhooks-{date_str}.jsonl")

    if not log_file.exists():
        console.print(f"[yellow]No audit logs found for {date_str}[/yellow]")
        console.print(f"[dim]Looking for: {log_file}[/dim]")
        return []

    entries = []
    with open(log_file) as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    console.print(
                        f"[red]Error parsing line {line_num}: {e}[/red]", style="dim"
                    )
                    continue

    return entries


def create_summary_table(entries: list[dict[str, Any]]) -> Table:
    """Create a summary table of webhook entries.

    Args:
        entries: List of audit log entries

    Returns:
        Rich Table object
    """
    table = Table(title=f"GitHub Webhook Audit Log ({len(entries)} entries)")

    table.add_column("Time", style="cyan", no_wrap=True)
    table.add_column("Event", style="magenta")
    table.add_column("Action", style="yellow")
    table.add_column("Repository", style="green")
    table.add_column("PR/Ref", style="blue")
    table.add_column("Delivery ID", style="dim", no_wrap=True)

    for entry in entries:
        timestamp = entry.get("metadata", {}).get("timestamp", "N/A")
        # Parse and format timestamp
        if timestamp != "N/A":
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%H:%M:%S")
            except (ValueError, AttributeError):
                pass

        event_type = entry.get("event_type", "N/A")
        payload = entry.get("payload", {})
        action = payload.get("action", "N/A")
        repo = payload.get("repository", {}).get("full_name", "N/A")

        # Get PR number or ref depending on event type
        if event_type == "pull_request":
            pr_ref = f"#{payload.get('number', '?')}"
        elif event_type == "push":
            ref = payload.get("ref", "N/A")
            pr_ref = ref.replace("refs/heads/", "")
        else:
            pr_ref = "N/A"

        delivery_id = entry.get("delivery_id", "N/A")
        # Truncate delivery ID for display
        if len(delivery_id) > 36:
            delivery_id = delivery_id[:8] + "..."

        table.add_row(timestamp, event_type, action, repo, pr_ref, delivery_id)

    return table


def show_webhook_detail(entry: dict[str, Any], verbose: bool = False) -> None:
    """Show detailed view of a single webhook.

    Args:
        entry: Audit log entry
        verbose: If True, show full payload
    """
    payload = entry.get("payload", {})
    metadata = entry.get("metadata", {})
    headers = entry.get("headers", {})

    # Header panel
    delivery_id = entry.get("delivery_id", "N/A")
    event_type = entry.get("event_type", "N/A")
    timestamp = metadata.get("timestamp", "N/A")

    console.print()
    console.print(
        Panel(
            f"[bold cyan]Delivery ID:[/bold cyan] {delivery_id}\n"
            f"[bold magenta]Event Type:[/bold magenta] {event_type}\n"
            f"[bold yellow]Timestamp:[/bold yellow] {timestamp}",
            title="[bold]Webhook Details[/bold]",
            border_style="blue",
        )
    )

    # Payload summary
    console.print("\n[bold underline]Payload Summary:[/bold underline]")

    tree = Tree("📦 Webhook Payload")

    # Repository info
    repo_info = tree.add("[green]🏢 Repository[/green]")
    repo = payload.get("repository", {})
    repo_info.add(f"[dim]Name:[/dim] {repo.get('full_name', 'N/A')}")
    repo_info.add(f"[dim]Owner:[/dim] {repo.get('owner', {}).get('login', 'N/A')}")
    repo_info.add(f"[dim]Private:[/dim] {repo.get('private', False)}")
    repo_info.add(f"[dim]URL:[/dim] {repo.get('html_url', 'N/A')}")

    # Event-specific details
    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        pr_info = tree.add("[blue]🔀 Pull Request[/blue]")
        pr_info.add(f"[dim]Number:[/dim] #{payload.get('number', '?')}")
        pr_info.add(f"[dim]Title:[/dim] {pr.get('title', 'N/A')}")
        pr_info.add(f"[dim]State:[/dim] {pr.get('state', 'N/A')}")
        pr_info.add(f"[dim]Action:[/dim] {payload.get('action', 'N/A')}")
        pr_info.add(f"[dim]Author:[/dim] {pr.get('user', {}).get('login', 'N/A')}")
        pr_info.add(f"[dim]Base:[/dim] {pr.get('base', {}).get('ref', 'N/A')}")
        pr_info.add(f"[dim]Head:[/dim] {pr.get('head', {}).get('ref', 'N/A')}")
        pr_info.add(f"[dim]Commits:[/dim] {pr.get('commits', 0)}")
        pr_info.add(f"[dim]Files Changed:[/dim] {pr.get('changed_files', 0)}")
        pr_info.add(f"[dim]+{pr.get('additions', 0)} / -{pr.get('deletions', 0)} lines")
        pr_info.add(f"[dim]Merged:[/dim] {pr.get('merged', False)}")
        pr_info.add(f"[dim]URL:[/dim] {pr.get('html_url', 'N/A')}")

    elif event_type == "push":
        push_info = tree.add("[yellow]📤 Push[/yellow]")
        push_info.add(f"[dim]Ref:[/dim] {payload.get('ref', 'N/A')}")
        push_info.add(f"[dim]Before:[/dim] {payload.get('before', 'N/A')[:8]}")
        push_info.add(f"[dim]After:[/dim] {payload.get('after', 'N/A')[:8]}")
        commits = payload.get("commits", [])
        push_info.add(f"[dim]Commits:[/dim] {len(commits)}")

        if commits:
            commits_tree = push_info.add("[cyan]Commits[/cyan]")
            for commit in commits[:5]:  # Show first 5
                msg = commit.get("message", "N/A").split("\n")[0][:60]
                commits_tree.add(f"{commit.get('id', 'N/A')[:8]}: {msg}")
            if len(commits) > 5:
                commits_tree.add(f"[dim]... and {len(commits) - 5} more[/dim]")

    # Sender info
    sender = payload.get("sender", {})
    sender_info = tree.add("[magenta]👤 Sender[/magenta]")
    sender_info.add(f"[dim]Login:[/dim] {sender.get('login', 'N/A')}")
    sender_info.add(f"[dim]Type:[/dim] {sender.get('type', 'N/A')}")
    sender_info.add(f"[dim]URL:[/dim] {sender.get('html_url', 'N/A')}")

    # Metadata
    meta_info = tree.add("[white]📊 Metadata[/white]")
    meta_info.add(f"[dim]Payload Size:[/dim] {metadata.get('payload_size', 0)} bytes")
    meta_info.add(f"[dim]Timestamp:[/dim] {metadata.get('timestamp', 'N/A')}")

    console.print(tree)

    # Headers
    if headers:
        console.print("\n[bold underline]Headers:[/bold underline]")
        headers_table = Table(show_header=True, box=None)
        headers_table.add_column("Header", style="cyan")
        headers_table.add_column("Value", style="white")

        for key, value in sorted(headers.items()):
            # Truncate signature for display
            if "signature" in key.lower() and len(str(value)) > 50:
                value = str(value)[:50] + "..."
            headers_table.add_row(key, str(value))

        console.print(headers_table)

    # Full payload if verbose
    if verbose:
        console.print("\n[bold underline]Full Payload (JSON):[/bold underline]")
        console.print(
            Panel(
                JSON(json.dumps(payload, indent=2)),
                title="Full Webhook Payload",
                border_style="dim",
            )
        )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect GitHub webhook audit logs with rich formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Date to inspect (YYYY-MM-DD). Default: today",
    )

    parser.add_argument(
        "--delivery-id", help="Show details for specific delivery ID", metavar="ID"
    )

    parser.add_argument(
        "--event", choices=["pull_request", "push"], help="Filter by event type"
    )

    parser.add_argument("--repo", help="Filter by repository (e.g., owner/repo)")

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show full JSON payload"
    )

    args = parser.parse_args()

    # Load logs
    console.print(f"[dim]Loading audit logs for {args.date}...[/dim]")
    entries = load_audit_logs(args.date)

    if not entries:
        return

    # Filter entries
    if args.event:
        entries = [e for e in entries if e.get("event_type") == args.event]

    if args.repo:
        entries = [
            e
            for e in entries
            if e.get("payload", {}).get("repository", {}).get("full_name") == args.repo
        ]

    if args.delivery_id:
        # Show detail for specific delivery
        matching = [e for e in entries if e.get("delivery_id") == args.delivery_id]
        if not matching:
            console.print(
                f"[red]No webhook found with delivery ID: {args.delivery_id}[/red]"
            )
            return

        show_webhook_detail(matching[0], verbose=args.verbose)
    else:
        # Show summary table
        table = create_summary_table(entries)
        console.print(table)

        console.print(
            f"\n[dim]💡 Tip: Use --delivery-id <ID> to see full details for a webhook[/dim]"
        )


if __name__ == "__main__":
    main()
