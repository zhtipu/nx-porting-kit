"""The step vocabulary. A port's port.json is a list of these; the core never knows a game by name.

To add a new kind of step: write a function, decorate it with @step("name"), import its module at the bottom.
Ports that name a step the running app lacks are shown as "needs update" instead of failing half way.
"""
REGISTRY: dict = {}


def step(name: str):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


class StepError(RuntimeError):
    """A failure with a message fit to show the user."""


class Skip(Exception):
    """The step had nothing to do."""


from . import context  # noqa: E402,F401
from . import fetch, filesystem, tool, nsp_pack  # noqa: E402,F401  (register themselves)

KNOWN_STEPS = frozenset(REGISTRY)
