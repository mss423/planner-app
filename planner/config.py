from __future__ import annotations
from pathlib import Path
import yaml

_CONFIG_PATH = Path.home() / ".planner" / "config.yaml"
_DEFAULT_RESEARCH_DIR = Path.home() / "Documents" / "research"


def config_path() -> Path:
    return _CONFIG_PATH


def load() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data
    return {}


def save(data: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def research_dir() -> Path:
    cfg = load()
    raw = cfg.get("research_dir", str(_DEFAULT_RESEARCH_DIR))
    return Path(raw).expanduser()


def editor() -> str:
    import os
    cfg = load()
    return cfg.get("editor") or os.environ.get("EDITOR") or "nano"


def default_hours() -> float:
    cfg = load()
    return float(cfg.get("default_hours", 8.0))


def set_value(key: str, value) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)


def is_configured() -> bool:
    return _CONFIG_PATH.exists()


def initialize(research_dir_path: Path) -> None:
    cfg = load()
    cfg["research_dir"] = str(research_dir_path)
    if "default_hours" not in cfg:
        cfg["default_hours"] = 8.0
    save(cfg)
    projects_dir = research_dir_path / "projects"
    planning_dir = research_dir_path / "planning" / "days"
    projects_dir.mkdir(parents=True, exist_ok=True)
    planning_dir.mkdir(parents=True, exist_ok=True)
