"""Tests for local MCP project management tools."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from memoryhub import db
from memoryhub.mcp.tools import create_memory_project, delete_project, list_memory_projects
from memoryhub.models.project import Project
from memoryhub.schemas.project_info import ProjectItem, ProjectList


def _make_project(
    name: str,
    path: str,
    *,
    id: int = 1,
    external_id: str = "00000000-0000-0000-0000-000000000001",
    is_default: bool = False,
    display_name: str | None = None,
    is_private: bool = False,
) -> ProjectItem:
    return ProjectItem(
        id=id,
        external_id=external_id,
        name=name,
        path=path,
        is_default=is_default,
        display_name=display_name,
        is_private=is_private,
    )


def _make_list(projects: list[ProjectItem], default: str | None = None) -> ProjectList:
    return ProjectList(projects=projects, default_project=default)


@pytest.mark.asyncio
async def test_list_memory_projects_unconstrained(app, test_project):
    result = await list_memory_projects()
    assert "Available projects:" in result
    assert f"• {test_project.name}" in result


@pytest.mark.asyncio
async def test_list_memory_projects_shows_display_name(app, client, test_project):
    mock_project = _make_project(
        "private-fb83af23",
        "/tmp/private",
        id=1,
        display_name="My Notes",
        is_private=True,
    )
    regular_project = _make_project(
        "main",
        "/tmp/main",
        id=2,
        external_id="00000000-0000-0000-0000-000000000002",
        is_default=True,
    )
    mock_list = _make_list([regular_project, mock_project], default="main")

    with patch(
        "memoryhub.mcp.clients.project.ProjectClient.list_projects",
        new_callable=AsyncMock,
        return_value=mock_list,
    ):
        result = await list_memory_projects()

    assert "• main (/tmp/main) [default]" in result
    assert "• private-fb83af23 (/tmp/private)" in result


@pytest.mark.asyncio
async def test_list_memory_projects_json_output(app):
    mock_list = _make_list(
        [
            _make_project("main", "/tmp/main", is_default=True),
            _make_project(
                "research",
                "/tmp/research",
                id=2,
                external_id="00000000-0000-0000-0000-000000000002",
            ),
        ],
        default="main",
    )

    with patch(
        "memoryhub.mcp.clients.project.ProjectClient.list_projects",
        new_callable=AsyncMock,
        return_value=mock_list,
    ):
        result = await list_memory_projects(output_format="json")

    assert isinstance(result, dict)
    assert result["default_project"] == "main"
    assert result["constrained_project"] is None
    assert len(result["projects"]) == 2
    assert result["projects"][0]["name"] == "main"


@pytest.mark.asyncio
async def test_list_memory_projects_constrained_env(monkeypatch, app, test_project):
    monkeypatch.setenv("BASIC_MEMORY_MCP_PROJECT", test_project.name)
    result = await list_memory_projects()
    assert f"Project: {test_project.name}" in result
    assert "constrained to a single project" in result


@pytest.mark.asyncio
async def test_create_and_delete_project_and_name_match_branch(
    app, tmp_path_factory, session_maker
):
    project_root = tmp_path_factory.mktemp("extra-project-home")
    result = await create_memory_project(
        project_name="My Project",
        project_path=str(project_root),
        set_default=False,
    )
    assert result.startswith("✓")
    assert "My Project" in result

    async with db.scoped_session(session_maker) as session:
        project = (
            await session.execute(select(Project).where(Project.name == "My Project"))
        ).scalar_one()
        project.permalink = "custom-permalink"
        await session.commit()

    delete_result = await delete_project("My Project")
    assert delete_result.startswith("✓")
