"""cy install — install Cy skill for agentic tools."""

import shutil
import sys
from pathlib import Path

import typer

_BUNDLED_SKILLS_DIR = Path(__file__).parent.parent / "bundled_skills"


def install(
    target: str = typer.Argument(
        ..., help="Target tool to install for (claude-code, codex)."
    ),
    project: bool = typer.Option(
        False,
        "--project",
        help="Install to the current project (.claude/skills/) instead of globally (~/.claude/skills/).",
    ),
) -> None:
    """Install Cy as a skill for an agentic tool."""
    if target == "claude-code":
        _install_claude_code(project)
    elif target == "codex":
        print(
            "Codex skill installation is not yet supported. "
            "Check back in a future release.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)
    else:
        print(
            f"Unknown target: {target}. Supported targets: claude-code, codex",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)


def _install_claude_code(project: bool) -> None:
    """Copy bundled skill files to the Claude Code skills directory."""
    skill_src = _BUNDLED_SKILLS_DIR / "cy-language-programming"
    if not skill_src.exists():
        print(
            "Error: Bundled skill files not found. "
            "Your cy-language installation may be corrupted.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    if project:
        dest = Path.cwd() / ".claude" / "skills" / "cy-language-programming"
    else:
        dest = Path.home() / ".claude" / "skills" / "cy-language-programming"

    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(skill_src, dest)

    location = "project" if project else "global"
    print(f"Installed Cy skill for Claude Code ({location}): {dest}")
