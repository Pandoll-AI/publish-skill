#!/usr/bin/env python3
"""Minimal test runner that does not require pytest."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "tests"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    failures = []
    count = 0
    for path in sorted(TEST_DIR.glob("test_*.py")):
        module = load_module(path)
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("test_"):
                count += 1
                try:
                    fn()
                except Exception as exc:  # noqa: BLE001
                    failures.append(f"{path.name}::{name}: {exc}")
    if failures:
        print(f"FAIL {len(failures)}/{count}")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PASS {count}/{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
