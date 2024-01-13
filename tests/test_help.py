import inspect
import sys
from enum import Enum
from textwrap import dedent
from typing import List, Literal, Optional, Union

import attrs
import pytest

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

from cyclopts import App, Group, Parameter
from cyclopts.help import (
    HelpEntry,
    HelpPanel,
    create_parameter_help_panel,
    format_command_entries,
    format_doc,
    format_usage,
)
from cyclopts.resolve import ResolvedCommand


@pytest.fixture
def app():
    return App(
        name="app",
        help="App Help String Line 1.",
    )


def test_help_default_action(app, console):
    """No command should default to help."""
    with console.capture() as capture:
        app([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_default_help_flags(console):
    """Standard help flags."""
    app = App(name="app", help="App Help String Line 1.")
    with console.capture() as capture:
        app(["--help"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_format_usage_empty(console):
    app = App(
        name="app",
        help="App Help String Line 1.",
        help_flags=[],
        version_flags=[],
    )

    with console.capture() as capture:
        console.print(format_usage(app, []))
    actual = capture.get()
    assert actual == "Usage: app\n\n"


def test_help_format_usage_command(app, console):
    @app.command
    def foo():
        pass

    with console.capture() as capture:
        console.print(format_usage(app, []))
    actual = capture.get()
    assert actual == "Usage: app COMMAND\n\n"


def test_format_doc_function(app, console):
    def foo():
        """Foo Doc String Line 1.

        Foo Doc String Line 3.
        """

    with console.capture() as capture:
        console.print(format_doc(app, foo))

    actual = capture.get()
    assert actual == "Foo Doc String Line 1.\n\nFoo Doc String Line 3.\n\n"


def test_format_commands_docstring(app, console):
    @app.command
    def foo():
        """Docstring for foo.

        This should not be shown.
        """
        pass

    panel = HelpPanel(title="Commands", format="command")
    panel.entries.extend(format_command_entries((app["foo"],)))
    with console.capture() as capture:
        console.print(panel)

    actual = capture.get()
    assert actual == (
        "╭─ Commands ─────────────────────────────────────────────────────────╮\n"
        "│ foo  Docstring for foo.                                            │\n"
        "╰────────────────────────────────────────────────────────────────────╯\n"
    )


def test_format_commands_no_show(app, console):
    @app.command
    def foo():
        """Docstring for foo."""
        pass

    @app.command(show=False)
    def bar():
        """Should not be shown."""
        pass

    panel = HelpPanel(title="Commands", format="command")
    panel.entries.extend(format_command_entries((app,)))

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ foo        Docstring for foo.                                      │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_format_commands_explicit_help(app, console):
    @app.command(help="Docstring for foo.")
    def foo():
        """Should not be shown."""
        pass

    panel = HelpPanel(title="Commands", format="command")
    panel.entries.extend(format_command_entries((app["foo"],)))
    with console.capture() as capture:
        console.print(panel)

    actual = capture.get()
    assert actual == (
        "╭─ Commands ─────────────────────────────────────────────────────────╮\n"
        "│ foo  Docstring for foo.                                            │\n"
        "╰────────────────────────────────────────────────────────────────────╯\n"
    )


def test_format_commands_explicit_name(app, console):
    @app.command(name="bar")
    def foo():
        """Docstring for bar.

        This should not be shown.
        """
        pass

    panel = HelpPanel(title="Commands", format="command")
    panel.entries.extend(format_command_entries((app["bar"],)))
    with console.capture() as capture:
        console.print(panel)

    actual = capture.get()
    assert actual == (
        "╭─ Commands ─────────────────────────────────────────────────────────╮\n"
        "│ bar  Docstring for bar.                                            │\n"
        "╰────────────────────────────────────────────────────────────────────╯\n"
    )


def test_help_empty(console):
    app = App(name="foo", version_flags=[], help_flags=[])

    with console.capture() as capture:
        app.help_print(console=console)
    actual = capture.get()

    assert actual == "Usage: foo\n\n"


@pytest.fixture
def capture_format_group_parameters(console, default_function_groups):
    def inner(cmd):
        command = ResolvedCommand(cmd, *default_function_groups)
        with console.capture() as capture:
            group, iparams = command.groups_iparams[0]
            cparams = [command.iparam_to_cparam[x] for x in iparams]
            console.print(create_parameter_help_panel(group, iparams, cparams))

        return capture.get()

    return inner


def test_help_format_group_parameters(capture_format_group_parameters):
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        bar: Annotated[str, Parameter(help="Docstring for bar.")],
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        │ *  BAR,--bar  Docstring for bar. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_short_name(capture_format_group_parameters):
    def cmd(
        foo: Annotated[str, Parameter(name=["--foo", "-f"], help="Docstring for foo.")],
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  -f  Docstring for foo. [required]                    │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_from_docstring(capture_format_group_parameters):
    def cmd(foo: str, bar: str):
        """

        Parameters
        ----------
        foo: str
            Docstring for foo.
        bar: str
            Docstring for bar.
        """
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        │ *  BAR,--bar  Docstring for bar. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_bool_flag(capture_format_group_parameters):
    def cmd(
        foo: Annotated[bool, Parameter(help="Docstring for foo.")] = True,
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo,--no-foo  Docstring for foo. [default: True]             │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_bool_flag_custom_negative(capture_format_group_parameters):
    def cmd(
        foo: Annotated[bool, Parameter(negative="--yesnt-foo", help="Docstring for foo.")] = True,
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo,--yesnt-foo  Docstring for foo. [default: True]          │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_list_flag(capture_format_group_parameters):
    def cmd(
        foo: Annotated[Optional[List[int]], Parameter(help="Docstring for foo.")] = None,
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo,--empty-foo  Docstring for foo.                          │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_defaults(capture_format_group_parameters):
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")] = "fizz",
        bar: Annotated[str, Parameter(help="Docstring for bar.")] = "buzz",
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo. [default: fizz]                      │
        │ BAR,--bar  Docstring for bar. [default: buzz]                      │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_defaults_no_show(capture_format_group_parameters):
    def cmd(
        foo: Annotated[str, Parameter(show_default=False, help="Docstring for foo.")] = "fizz",
        bar: Annotated[str, Parameter(help="Docstring for bar.")] = "buzz",
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo.                                      │
        │ BAR,--bar  Docstring for bar. [default: buzz]                      │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_choices_literal_no_show(capture_format_group_parameters):
    def cmd(
        foo: Annotated[Literal["fizz", "buzz"], Parameter(show_choices=False, help="Docstring for foo.")] = "fizz",
        bar: Annotated[Literal["fizz", "buzz"], Parameter(help="Docstring for bar.")] = "buzz",
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo. [default: fizz]                      │
        │ BAR,--bar  Docstring for bar. [choices: fizz,buzz] [default: buzz] │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_choices_literal_union(capture_format_group_parameters):
    def cmd(
        foo: Annotated[
            Union[int, Literal["fizz", "buzz"], Literal["bar"]], Parameter(help="Docstring for foo.")
        ] = "fizz",
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo. [choices: fizz,buzz,bar] [default:   │
        │            fizz]                                                   │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_choices_enum(capture_format_group_parameters):
    class CompSciProblem(Enum):
        fizz = "bleep bloop blop"
        buzz = "blop bleep bloop"

    def cmd(
        foo: Annotated[CompSciProblem, Parameter(help="Docstring for foo.")] = CompSciProblem.fizz,
        bar: Annotated[CompSciProblem, Parameter(help="Docstring for bar.")] = CompSciProblem.buzz,
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo. [choices: fizz,buzz] [default: fizz] │
        │ BAR,--bar  Docstring for bar. [choices: fizz,buzz] [default: buzz] │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_format_group_parameters_env_var(capture_format_group_parameters):
    def cmd(
        foo: Annotated[int, Parameter(env_var=["FOO", "BAR"], help="Docstring for foo.")] = 123,
    ):
        pass

    actual = capture_format_group_parameters(cmd)
    expected = dedent(
        """\
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ FOO,--foo  Docstring for foo. [env var: FOO BAR] [default: 123]    │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_function(app, console):
    @app.command(help="Cmd help string.")
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        *,
        bar: Annotated[str, Parameter(help="Docstring for bar.")],
    ):
        pass

    with console.capture() as capture:
        app.help_print(["cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app cmd [ARGS] [OPTIONS]

        Cmd help string.

        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        │ *  --bar      Docstring for bar. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_function_defaults(app, console):
    @app.command(help="Cmd help string.")
    def cmd(
        *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
        bar: Annotated[str, Parameter(help="Docstring for bar.")] = "bar-value",
        baz: Annotated[str, Parameter(help="Docstring for bar.", env_var="BAZ")] = "baz-value",
    ):
        pass

    with console.capture() as capture:
        app.help_print(["cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app cmd [ARGS] [OPTIONS]

        Cmd help string.

        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ --bar  Docstring for bar. [default: bar-value]                     │
        │ --baz  Docstring for bar. [env var: BAZ] [default: baz-value]      │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_function_no_parse(app, console):
    @app.command(help="Cmd help string.")
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        *,
        bar: Annotated[str, Parameter(parse=False)],
    ):
        pass

    with console.capture() as capture:
        app.help_print(["cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app cmd [ARGS] [OPTIONS]

        Cmd help string.

        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_parameter_group_description(app, console):
    @app.command(group_parameters=Group("Custom Title", help="Parameter description."))
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        *,
        bar: Annotated[str, Parameter(parse=False)],
    ):
        pass

    with console.capture() as capture:
        app.help_print(["cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app cmd [ARGS] [OPTIONS]

        ╭─ Custom Title ─────────────────────────────────────────────────────╮
        │ Parameter description.                                             │
        │                                                                    │
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_print_parameter_group_no_show(app, console):
    no_show_group = Group("Custom Title", help="Parameter description.", show=False)

    @app.command
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        bar: Annotated[str, Parameter(help="Docstring for foo.", group=no_show_group)],
    ):
        pass

    with console.capture() as capture:
        app.help_print(["cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app cmd [ARGS] [OPTIONS]

        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_print_command_group_description(app, console):
    @app.command(group=Group("Custom Title", help="Command description."))
    def cmd(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        *,
        bar: Annotated[str, Parameter(parse=False)],
    ):
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Custom Title ─────────────────────────────────────────────────────╮
        │ Command description.                                               │
        │                                                                    │
        │ cmd                                                                │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_print_command_group_no_show(app, console):
    no_show_group = Group("Custom Title", show=False)

    @app.command(group=no_show_group)
    def cmd1():
        pass

    @app.command()
    def cmd2():
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd2                                                               │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_print_combined_parameter_command_group(app, console):
    group = Group("Custom Title")

    app["--help"].group = group

    @app.default
    def default(value1: Annotated[int, Parameter(group=group)]):
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND [ARGS] [OPTIONS]

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Custom Title ─────────────────────────────────────────────────────╮
        │ *  VALUE1,--value1      [required]                                 │
        │    --help           -h  Display this message and exit.             │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )

    assert actual == expected


def test_help_print_commands(app, console):
    @app.command(help="Cmd1 help string.")
    def cmd1():
        pass

    @app.command(help="Cmd2 help string.")
    def cmd2():
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd1       Cmd1 help string.                                       │
        │ cmd2       Cmd2 help string.                                       │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_commands_sort_key(app, console):
    @app.command(group=Group("B", sort_key=5))
    def cmd1():
        pass

    @app.command(group=Group("A", sort_key=lambda x: 10))
    def cmd2():
        pass

    @app.command(group=Group("C"))
    def cmd3():
        pass

    @app.command(group=Group("D", sort_key=lambda x: None))
    def cmd4():
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ B ────────────────────────────────────────────────────────────────╮
        │ cmd1                                                               │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ A ────────────────────────────────────────────────────────────────╮
        │ cmd2                                                               │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ C ────────────────────────────────────────────────────────────────╮
        │ cmd3                                                               │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ D ────────────────────────────────────────────────────────────────╮
        │ cmd4                                                               │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_commands_and_function(app, console):
    @app.command(help="Cmd1 help string.")
    def cmd1():
        pass

    @app.command(help="Cmd2 help string.")
    def cmd2():
        pass

    @app.default()
    def default(
        foo: Annotated[str, Parameter(help="Docstring for foo.")],
        *,
        bar: Annotated[str, Parameter(help="Docstring for bar.")],
    ):
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND [ARGS] [OPTIONS]

        App Help String Line 1.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd1       Cmd1 help string.                                       │
        │ cmd2       Cmd2 help string.                                       │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  FOO,--foo  Docstring for foo. [required]                        │
        │ *  --bar      Docstring for bar. [required]                        │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_commands_special_flag_reassign(app, console):
    app["--help"].group = "Admin"
    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Admin ────────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_commands_plus_meta(app, console):
    app = App(
        name="app",
        help_flags=[],
        version_flags=[],
        help="App Help String Line 1.",
    )

    @app.command(help="Cmd1 help string.")
    def cmd1():
        pass

    @app.meta.command(help="Meta cmd help string.")
    def meta_cmd():
        pass

    @app.command(help="Cmd2 help string.")
    def cmd2():
        pass

    @app.meta.default
    def main(
        *tokens: Annotated[str, Parameter(show=False)],
        hostname: Annotated[str, Parameter(help="Hostname to connect to.")],
    ):
        pass

    app.meta["--help"].group = "Admin"

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1.

        ╭─ Admin ────────────────────────────────────────────────────────────╮
        │ --help,-h  Display this message and exit.                          │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd1       Cmd1 help string.                                       │
        │ cmd2       Cmd2 help string.                                       │
        │ meta-cmd   Meta cmd help string.                                   │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Session Parameters ───────────────────────────────────────────────╮
        │ *  --hostname  Hostname to connect to. [required]                  │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected


def test_help_print_commands_plus_meta_short(app, console):
    app.help = None

    @app.command(help="Cmd1 help string.")
    def cmd1():
        pass

    @app.meta.command(help="Meta cmd help string.")
    def meta_cmd(a: int):
        """

        Parameters
        ----------
        a
            Some value.
        """
        pass

    @app.command(help="Cmd2 help string.")
    def cmd2():
        pass

    @app.meta.default
    def main(
        *tokens: str,
        hostname: Annotated[str, Parameter(name=["--hostname", "-n"], help="Hostname to connect to.")],
    ):
        """App Help String Line 1 from meta."""
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND

        App Help String Line 1 from meta.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd1       Cmd1 help string.                                       │
        │ cmd2       Cmd2 help string.                                       │
        │ meta-cmd   Meta cmd help string.                                   │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Session Parameters ───────────────────────────────────────────────╮
        │ *  TOKENS          [required]                                      │
        │ *  --hostname  -n  Hostname to connect to. [required]              │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected

    # Add in a default root app.
    @app.default
    def root_default_cmd(rdp):
        """Root Default Command Short Description.

        Parameters
        ----------
        rdp:
            RDP description.
        """
        pass

    with console.capture() as capture:
        app.help_print([], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app COMMAND [ARGS] [OPTIONS]

        Root Default Command Short Description.

        ╭─ Commands ─────────────────────────────────────────────────────────╮
        │ cmd1       Cmd1 help string.                                       │
        │ cmd2       Cmd2 help string.                                       │
        │ meta-cmd   Meta cmd help string.                                   │
        │ --help,-h  Display this message and exit.                          │
        │ --version  Display application version.                            │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  RDP,--rdp  RDP description. [required]                          │
        ╰────────────────────────────────────────────────────────────────────╯
        ╭─ Session Parameters ───────────────────────────────────────────────╮
        │ *  TOKENS          [required]                                      │
        │ *  --hostname  -n  Hostname to connect to. [required]              │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected

    # Test that the meta command help parsing is correct.
    with console.capture() as capture:
        app.help_print(["meta-cmd"], console=console)

    actual = capture.get()
    expected = dedent(
        """\
        Usage: app meta-cmd [ARGS] [OPTIONS]

        Meta cmd help string.

        ╭─ Parameters ───────────────────────────────────────────────────────╮
        │ *  A,--a  Some value. [required]                                   │
        ╰────────────────────────────────────────────────────────────────────╯
        """
    )
    assert actual == expected
