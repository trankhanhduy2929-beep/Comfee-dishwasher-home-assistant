"""Compatibility helpers for threaded and asyncio midea-local releases."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import partial
from typing import Any, TypeVar

from homeassistant.core import HomeAssistant
from midealocal.device import MideaDevice
from midealocal.devices import device_selector

_T = TypeVar("_T")

ASYNC_LIBRARY = inspect.iscoroutinefunction(MideaDevice.connect)
SELECTOR_ACCEPTS_CUSTOMIZE = (
    "customize" in inspect.signature(device_selector).parameters
)


def selector_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Add the legacy customize argument only when the installed library needs it."""
    if SELECTOR_ACCEPTS_CUSTOMIZE:
        kwargs["customize"] = ""
    return kwargs


async def async_call(
    hass: HomeAssistant,
    func: Callable[..., _T],
    *args: Any,
    **kwargs: Any,
) -> _T:
    """Call a library function on the loop for asyncio releases, else in an executor."""
    if ASYNC_LIBRARY:
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
    return await hass.async_add_executor_job(partial(func, *args, **kwargs))
