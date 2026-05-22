from __future__ import annotations

import typing as t

from pytest import MonkeyPatch

import databind.core.union as union_module


def test_iter_entry_points_uses_select_api_without_call_arguments(monkeypatch: MonkeyPatch) -> None:
    result = [object(), object()]

    class EntryPoints:
        def __init__(self) -> None:
            self.selected_group: str | None = None

        def select(self, *, group: str) -> list[object]:
            self.selected_group = group
            return result

    eps = EntryPoints()

    def fake_entry_points(*args: object, **kwargs: object) -> object:
        assert args == ()
        assert kwargs == {}
        return eps

    monkeypatch.setattr(union_module, "entry_points", fake_entry_points)

    assert list(union_module.iter_entry_points("my.group")) == t.cast(t.Any, result)
    assert eps.selected_group == "my.group"


def test_iter_entry_points_falls_back_to_mapping_result(monkeypatch: MonkeyPatch) -> None:
    result = [object(), object()]

    def fake_entry_points(*args: object, **kwargs: object) -> object:
        assert args == ()
        assert kwargs == {}
        return {"my.group": result}

    monkeypatch.setattr(union_module, "entry_points", fake_entry_points)

    assert list(union_module.iter_entry_points("my.group")) == t.cast(t.Any, result)
    assert list(union_module.iter_entry_points("missing")) == []
