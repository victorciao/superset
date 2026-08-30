# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Regression tests for the removal of the end-of-life deprecated
``BaseEngineSpec.normalize_indexes``, deprecated in Superset 3.0.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import superset
from superset.db_engine_specs import load_engine_specs
from superset.db_engine_specs.base import BaseEngineSpec

SYMBOL = "normalize_indexes"


def _all_engine_spec_classes() -> Iterator[type[BaseEngineSpec]]:
    """
    Every engine spec shipped in the package, plus every class in their MROs.
    """
    seen: set[type] = set()
    for spec in load_engine_specs():
        for klass in spec.__mro__:
            if klass not in seen:
                seen.add(klass)
                yield klass


def _package_python_files() -> Iterator[Path]:
    root = Path(superset.__file__).parent
    for path in sorted(root.rglob("*.py")):
        if "migrations/versions" in path.as_posix():
            continue
        yield path


def test_normalize_indexes_removed_from_base_engine_spec() -> None:
    """
    The EOL deprecated method must no longer be part of ``BaseEngineSpec``.
    """
    assert not hasattr(BaseEngineSpec, SYMBOL), (
        f"BaseEngineSpec.{SYMBOL} is deprecated since 3.0 and must be removed"
    )
    assert SYMBOL not in vars(BaseEngineSpec)


def test_normalize_indexes_not_defined_by_any_engine_spec() -> None:
    """
    No shipped engine spec may define or inherit the removed method, otherwise
    the removal would be partial and callers could still reach it.
    """
    offenders = sorted(
        f"{klass.__module__}.{klass.__qualname__}"
        for klass in _all_engine_spec_classes()
        if SYMBOL in vars(klass)
    )
    assert offenders == [], f"{SYMBOL} still defined by: {', '.join(offenders)}"


def test_no_references_to_normalize_indexes_in_package() -> None:
    """
    The removal must be complete: no caller, override or docs reference to the
    symbol may survive anywhere in the ``superset`` package.
    """
    pattern = re.compile(rf"\b{SYMBOL}\b")
    hits = [
        f"{path}:{lineno}"
        for path in _package_python_files()
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if pattern.search(line)
    ]
    assert hits == [], f"dangling references to {SYMBOL}: {', '.join(hits)}"


def test_no_eol_deprecated_3_0_marker_left_in_base_module() -> None:
    """
    ``superset/db_engine_specs/base.py`` must carry no ``deprecated_in="3.0"``
    decorator, the marker that made this method end-of-life.
    """
    source = Path(BaseEngineSpec.__module__.replace(".", "/") + ".py")
    text = (Path(superset.__file__).parent.parent / source).read_text(encoding="utf-8")
    assert 'deprecated_in="3.0"' not in text
