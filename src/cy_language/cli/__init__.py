"""CLI for the Cy language interpreter.

Requires the `cli` extra: pip install cy-language[cli]
"""

import typer

from cy_language import __version__

app = typer.Typer(
    name="cy",
    help="Cy language interpreter — compile, check, and run .cy programs.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        print(f"cy {__version__}")
        raise typer.Exit()


@app.callback()
def _global_options(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Cy language interpreter."""


# Import and register subcommands
from cy_language.cli.check_cmd import check  # noqa: E402
from cy_language.cli.compile_cmd import compile  # noqa: E402
from cy_language.cli.install_cmd import install  # noqa: E402
from cy_language.cli.run_cmd import run  # noqa: E402
from cy_language.cli.visualize_cmd import visualize  # noqa: E402

app.command()(run)
app.command()(check)
app.command(name="compile")(compile)
app.command()(install)
app.command()(visualize)


def main() -> None:
    """Entry point for the `cy` console script."""
    app()


if __name__ == "__main__":
    main()
