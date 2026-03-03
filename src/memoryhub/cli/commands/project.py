"""Command module for local project management."""

import json
import os
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from memoryhub.cli.app import app
from memoryhub.cli.commands.command_utils import get_project_info, run_with_cleanup
from memoryhub.cli.commands.routing import force_routing
from memoryhub.config import ConfigManager
from memoryhub.mcp.async_client import get_client
from memoryhub.mcp.clients import ProjectClient
from memoryhub.utils import normalize_project_path

console = Console()

project_app = typer.Typer(help="Manage local MemoryHub projects")
app.add_typer(project_app, name="project")


def format_path(path: str) -> str:
    """Format a path for display, using ~ for home directory."""
    home = str(Path.home())
    if path.startswith(home):
        return path.replace(home, "~", 1)  # pragma: no cover
    return path


def make_bar(value: int, max_value: int, width: int = 40) -> Text:
    """Create a horizontal bar chart element using Unicode blocks."""
    if max_value == 0:
        return Text("░" * width, style="dim")
    filled = max(1, round(value / max_value * width)) if value > 0 else 0
    bar = Text()
    bar.append("█" * filled, style="cyan")
    bar.append("░" * (width - filled), style="dim")
    return bar


@project_app.command("list")
def list_projects(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """List configured local projects."""

    async def _list_projects():
        async with get_client() as client:
            return await ProjectClient(client).list_projects()

    try:
        with force_routing(local=True):
            result = run_with_cleanup(_list_projects())

        project_rows = [
            {
                "name": project.name,
                "path": normalize_project_path(project.path),
                "is_default": project.is_default,
            }
            for project in result.projects
        ]

        if json_output:
            print(json.dumps({"projects": project_rows}, indent=2, default=str))
            return

        table = Table(title="MemoryHub Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="yellow", no_wrap=True, overflow="fold")
        table.add_column("Default", style="magenta")

        for row in project_rows:
            table.add_row(
                row["name"],
                format_path(row["path"]),
                "[X]" if row["is_default"] else "",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing projects: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("add")
def add_project(
    name: str = typer.Argument(..., help="Name of the project"),
    path: str = typer.Argument(..., help="Path to the local project directory"),
    set_default: bool = typer.Option(False, "--default", help="Set as default project"),
) -> None:
    """Add a new local project."""
    resolved_path = Path(os.path.abspath(os.path.expanduser(path))).as_posix()

    async def _add_project():
        async with get_client() as client:
            data = {"name": name, "path": resolved_path, "set_default": set_default}
            return await ProjectClient(client).create_project(data)

    try:
        with force_routing(local=True):
            result = run_with_cleanup(_add_project())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error adding project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("remove")
def remove_project(
    name: str = typer.Argument(..., help="Name of the project to remove"),
    delete_notes: bool = typer.Option(
        False, "--delete-notes", help="Delete project files from disk"
    ),
) -> None:
    """Remove a local project."""

    async def _remove_project():
        async with get_client(project_name=name) as client:
            project_client = ProjectClient(client)
            target_project = await project_client.resolve_project(name)
            return await project_client.delete_project(
                target_project.external_id,
                delete_notes=delete_notes,
            )

    try:
        with force_routing(local=True):
            result = run_with_cleanup(_remove_project())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error removing project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("default")
def set_default_project(
    name: str = typer.Argument(..., help="Name of the project to set as default"),
) -> None:
    """Set the default project used when no project is specified."""

    async def _set_default():
        async with get_client(project_name=name) as client:
            project_client = ProjectClient(client)
            target_project = await project_client.resolve_project(name)
            return await project_client.set_default(target_project.external_id)

    try:
        with force_routing(local=True):
            result = run_with_cleanup(_set_default())
        console.print(f"[green]{result.message}[/green]")
    except Exception as e:
        console.print(f"[red]Error setting default project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("move")
def move_project(
    name: str = typer.Argument(..., help="Name of the project to move"),
    new_path: str = typer.Argument(..., help="New absolute path for the project"),
) -> None:
    """Move a local project to a new filesystem location."""
    resolved_path = Path(os.path.abspath(os.path.expanduser(new_path))).as_posix()

    async def _move_project():
        async with get_client(project_name=name) as client:
            project_client = ProjectClient(client)
            project_info = await project_client.resolve_project(name)
            return await project_client.update_project(
                project_info.external_id,
                {"path": resolved_path},
            )

    try:
        with force_routing(local=True):
            result = run_with_cleanup(_move_project())
        console.print(f"[green]{result.message}[/green]")
        console.print()
        console.print(
            Panel(
                "[bold red]IMPORTANT:[/bold red] Project configuration updated successfully.\n\n"
                "[yellow]You must manually move your project files from the old location to:[/yellow]\n"
                f"[cyan]{resolved_path}[/cyan]\n\n"
                "[dim]Only the configuration has been updated. Existing files stay in their old location until you move them.[/dim]",
                title="Manual File Movement Required",
                border_style="yellow",
                expand=False,
            )
        )
    except Exception as e:
        console.print(f"[red]Error moving project: {str(e)}[/red]")
        raise typer.Exit(1)


@project_app.command("ls")
def ls_project_command(
    name: str = typer.Option(..., "--name", help="Project name to list files from"),
    path: str = typer.Argument(None, help="Path within project (optional)"),
) -> None:
    """List files in a local project."""

    def _list_local_files(project_path: str, subpath: str | None = None) -> list[str]:
        project_root = Path(normalize_project_path(project_path)).expanduser().resolve()
        target_dir = project_root

        if subpath:
            requested = Path(subpath)
            if requested.is_absolute():
                raise ValueError("Path must be relative to the project root")
            target_dir = (project_root / requested).resolve()
            if not target_dir.is_relative_to(project_root):
                raise ValueError("Path must stay within the project root")

        if not target_dir.exists():
            raise ValueError(f"Path not found: {target_dir}")
        if not target_dir.is_dir():
            raise ValueError(f"Path is not a directory: {target_dir}")

        files: list[str] = []
        for file_path in sorted(target_dir.rglob("*")):
            if file_path.is_file():
                size = file_path.stat().st_size
                relative = file_path.relative_to(project_root).as_posix()
                files.append(f"{size:10d} {relative}")

        return files

    async def _resolve_project():
        async with get_client(project_name=name) as client:
            return await ProjectClient(client).resolve_project(name)

    try:
        with force_routing(local=True):
            project_data = run_with_cleanup(_resolve_project())
        files = _list_local_files(project_data.path, path)

        if files:
            heading = f"\n[bold]Files in {name}"
            if path:
                heading += f"/{path}"
            heading += ":[/bold]"
            console.print(heading)
            for file in files:
                console.print(f"  {file}")
            console.print(f"\n[dim]Total: {len(files)} files[/dim]")
        else:
            prefix = f"[yellow]No files found in {name}"
            console.print(prefix + (f"/{path}" if path else "") + "[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@project_app.command("info")
def display_project_info(
    name: str = typer.Argument(..., help="Name of the project"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display detailed information and statistics about a local project."""
    try:
        with force_routing(local=True):
            info = run_with_cleanup(get_project_info(name))

        if json_output:
            print(json.dumps(info.model_dump(), indent=2, default=str))
            return

        left = Table.grid(padding=(0, 2))
        left.add_column("metric", style="cyan")
        left.add_column("value", style="green", justify="right")

        left.add_row("[bold]Knowledge Graph[/bold]", "")
        left.add_row("Entities", str(info.statistics.total_entities))
        left.add_row("Observations", str(info.statistics.total_observations))
        left.add_row("Relations", str(info.statistics.total_relations))
        left.add_row("Unresolved", str(info.statistics.total_unresolved_relations))
        left.add_row("Isolated", str(info.statistics.isolated_entities))

        right = Table.grid(padding=(0, 2))
        right.add_column("property", style="cyan")
        right.add_column("value", style="green")

        right.add_row("[bold]Embeddings[/bold]", "")
        if info.embedding_status:
            es = info.embedding_status
            if not es.semantic_search_enabled:
                right.add_row("[green]●[/green] Semantic Search", "Disabled")
            else:
                right.add_row("[green]●[/green] Semantic Search", "Enabled")
                if es.embedding_provider:
                    right.add_row("  Provider", es.embedding_provider)
                if es.embedding_model:
                    right.add_row("  Model", es.embedding_model)
                if es.total_indexed_entities > 0:
                    coverage_bar = make_bar(
                        es.total_entities_with_chunks,
                        es.total_indexed_entities,
                        width=20,
                    )
                    count_text = Text(
                        f" {es.total_entities_with_chunks}/{es.total_indexed_entities}",
                        style="green",
                    )
                    bar_with_count = Text.assemble("  Indexed  ", coverage_bar, count_text)
                    right.add_row(bar_with_count, "")
                right.add_row("  Chunks", str(es.total_chunks))
                if es.reindex_recommended:
                    right.add_row(
                        "[yellow]●[/yellow] Status",
                        "[yellow]Reindex recommended[/yellow]",
                    )
                    if es.reindex_reason:
                        right.add_row("  Reason", f"[yellow]{es.reindex_reason}[/yellow]")
                else:
                    right.add_row("[green]●[/green] Status", "[green]Up to date[/green]")

        columns = Table.grid(padding=(0, 4), expand=False)
        columns.add_row(left, right)

        bars_section = None
        if info.statistics.note_types:
            sorted_types = sorted(
                info.statistics.note_types.items(), key=lambda x: x[1], reverse=True
            )
            top_types = sorted_types[:5]
            max_count = top_types[0][1] if top_types else 1

            bars = Table.grid(padding=(0, 2), expand=False)
            bars.add_column("type", style="cyan", width=16, justify="right")
            bars.add_column("bar")
            bars.add_column("count", style="green", justify="right")

            for note_type, count in top_types:
                bars.add_row(note_type, make_bar(count, max_count), str(count))

            remaining = len(sorted_types) - len(top_types)
            bars_section = Group(
                "[bold]Note Types[/bold]",
                bars,
                f"[dim]+{remaining} more types[/dim]" if remaining > 0 else "",
            )

        current_time = (
            datetime.fromisoformat(str(info.system.timestamp))
            if isinstance(info.system.timestamp, str)
            else info.system.timestamp
        )
        footer = (
            f"[dim]{format_path(info.project_path)}  "
            f"default: {info.default_project}  "
            f"{current_time.strftime('%Y-%m-%d %H:%M')}[/dim]"
        )

        parts: list = [columns, ""]
        if bars_section:
            parts.extend([bars_section, ""])
        parts.append(footer)
        body = Group(*parts)

        console.print(
            Panel(
                body,
                title=f"[bold]{info.project_name}[/bold]",
                subtitle=f"MemoryHub {info.system.version}",
                expand=False,
            )
        )
    except typer.Exit:
        raise
    except Exception as e:  # pragma: no cover
        typer.echo(f"Error getting project info: {e}", err=True)
        raise typer.Exit(1)
