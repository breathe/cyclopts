import inspect

import pytest
from typing_extensions import Annotated

from cyclopts import Group, Parameter
from cyclopts.group_extractors import groups_from_commands, groups_from_function


def test_groups_unannotated_parameters_positional_or_keyword():
    """Simple, unannotated POSITIONAL_OR_KEYWORD should be assigned to "Parameters" group."""

    def foo(bar):
        pass

    bar_parameter = list(inspect.signature(foo).parameters.values())[0]
    actual_groups = groups_from_function(foo)
    assert actual_groups == [(Group("Parameters"), [bar_parameter])]


def test_groups_unannotated_parameters_positional_only():
    """Simple, unannotated KEYWORD_ONLY should be assigned to "Parameters" group."""

    def foo(*, bar):
        pass

    bar_parameter = list(inspect.signature(foo).parameters.values())[0]
    actual_groups = groups_from_function(foo)
    assert actual_groups == [(Group("Parameters"), [bar_parameter])]


def test_groups_unannotated_arguments():
    """Simple, unannotated POSITIONAL_ONLY should be assigned to "Arguments" group."""

    def foo(bar, /):
        pass

    bar_parameter = list(inspect.signature(foo).parameters.values())[0]
    actual_groups = groups_from_function(foo)
    assert actual_groups == [(Group("Arguments"), [bar_parameter])]


def test_groups_annotated_implicit():
    def foo(
        food1: Annotated[str, Parameter(group="Food")],
        drink1: Annotated[str, Parameter(group="Drink")],
        food2: Annotated[str, Parameter(group="Food")],
    ):
        pass

    parameters = list(inspect.signature(foo).parameters.values())
    actual_groups = groups_from_function(foo)
    assert actual_groups == [
        (Group("Food"), [parameters[0], parameters[2]]),
        (Group("Drink"), [parameters[1]]),
    ]


def test_groups_annotated_explicit():
    food_group = Group("Food")
    drink_group = Group("Drink")

    def foo(
        food1: Annotated[str, Parameter(group=food_group)],
        drink1: Annotated[str, Parameter(group=drink_group)],
        food2: Annotated[str, Parameter(group=food_group)],
    ):
        pass

    parameters = list(inspect.signature(foo).parameters.values())
    actual_groups = groups_from_function(foo)
    assert actual_groups == [
        (food_group, [parameters[0], parameters[2]]),
        (drink_group, [parameters[1]]),
    ]


def test_groups_annotated_invalid_recursive_definition():
    """A default_parameter isn't allowed to have a group set, as it would introduce a paradox."""
    default_parameter = Parameter(group="Drink")
    with pytest.raises(ValueError):
        Group("Food", default_parameter=default_parameter)