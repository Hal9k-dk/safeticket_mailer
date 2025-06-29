from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
  from .config_example import Config


def get_config(config_file_path: Path) -> "Config":
    config_file_path = Path(config_file_path)

    if not config_file_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

    if not config_file_path.suffix == '.py':
        raise ValueError("Configuration file must be a Python file with '.py' extension")

    spec = importlib.util.spec_from_file_location("module.config", config_file_path)
    _config = importlib.util.module_from_spec(spec)
    sys.modules["module.config"] = _config
    spec.loader.exec_module(_config)
    return _config.Config()
