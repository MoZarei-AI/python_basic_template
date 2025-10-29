from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List, Optional

import logging
import logging.config
from logging.handlers import RotatingFileHandler


try:
    from rich.logging import RichHandler
    _RICH_AVAILABLE = True
except Exception:
    _RICH_AVAILABLE = False



class LoggingChannelFilter(logging.Filter):

    def __init__(self, project_name: str, channel_mapping: Optional[Dict[str, str]] = None) -> None:
        super().__init__()
        self.project_name = project_name
        self.channel_mapping = channel_mapping or {}

    def _alias_for(self, logger_name: str) -> str:
        if not logger_name or logger_name == "root":
            return self.project_name

        if self.channel_mapping:
            for lname, alias in sorted(self.channel_mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
                if logger_name == lname or logger_name.startswith(lname + "."):
                    return alias

        pn = self.project_name
        if logger_name == pn:
            return pn
        if logger_name.startswith(pn + "."):
            parts = logger_name.split(".")
            return parts[1] if len(parts) > 1 else pn

        return logger_name.split(".", 1)[0]

    def filter(self, record: logging.LogRecord) -> bool:
        record.logging_channel = self._alias_for(record.name)
        return True


class CallableHandler(logging.Handler):

    def __init__(self) -> None:
        super().__init__()
        self._callback = self._resolve_callback()

    def _resolve_callback(self):
        import importlib
        path = os.getenv("LOGGING_CUSTOM_CALLBACK", "").strip()
        if not path or "." not in path:
            return None
        mod_name, func_name = path.rsplit(".", 1)
        try:
            mod = importlib.import_module(mod_name)
            return getattr(mod, func_name, None)
        except Exception:
            return None

    def emit(self, record: logging.LogRecord) -> None:
        if self._callback:
            try:
                self._callback(record)
            except Exception:
                pass


class LoggingConfigProvider:

    _instance: Optional["LoggingConfigProvider"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_dir: Path,
        debug: bool,
        project_name: str = "my_project",
        use_rich: bool = True,
        max_bytes: int = 5 * 1024 * 1024,
        backups: int = 3,
    ) -> None:
        self.project_name = project_name
        self.debug = bool(debug)
        self.log_dir = Path(log_dir)
        self.use_rich = bool(use_rich and _RICH_AVAILABLE)
        self.max_bytes = int(max_bytes)
        self.backups = int(backups)

        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.__handlers: Dict[str, dict] = {}
        self.__loggers: Dict[str, dict] = {}
        self.__channel_mapping: Dict[str, str] = {}

        self._configure_root()


    def add_loggers(
        self,
        logger_names: Optional[List[str]],
        level: str = "INFO",
        handlers: Optional[List[str]] = None,
    ) -> "LoggingConfigProvider":

        for lname in logger_names:
            alias = self._alias_for(lname)

            handler_names: List[str] = []
            if handlers:
                if "console" in handlers:
                    handler_names.append("console")
                if "file" in handlers:
                    handler_names.append(self._ensure_file_handler(alias, level))
                if "custom" in handlers:
                    handler_names.append(self._ensure_custom_handler(alias, level))

            propagate = not bool(handler_names)  # only propagate if no handlers attached

            self.__channel_mapping[lname] = alias

            self.__loggers[lname] = dict(
                level=level,
                handlers=handler_names,
                propagate=propagate,
            )
        return self

    def get_logging_config(self) -> Dict[str, dict]:
        filters = dict(
            logging_channel=dict(
                **{"()": f"{__name__}.LoggingChannelFilter"},
                project_name=self.project_name,
                channel_mapping=self.__channel_mapping.copy(),
            )
        )

        config = dict(
            version=1,
            disable_existing_loggers=False,
            filters=filters,
            formatters=self._build_formatters(),
            handlers=self.__handlers.copy(),
            loggers=self.__loggers.copy(),
            root=dict(level=self._root_level(), handlers=self._root_handlers()),
        )
        return config


    def _root_level(self) -> str:
        return "DEBUG" if self.debug else "INFO"

    def _root_handlers(self) -> List[str]:
        return ["console", self._root_file_handler_name()]

    def _configure_root(self) -> None:

        if self.use_rich:
            self.__handlers["console"] = dict(
                **{"class": "rich.logging.RichHandler"},
                level=self._root_level(),
                formatter="rich",
                filters=["logging_channel"],
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
        else:
            self.__handlers["console"] = dict(
                **{"class": "logging.StreamHandler"},
                level=self._root_level(),
                formatter="verbose",
                filters=["logging_channel"],
            )

        self.__handlers[self._root_file_handler_name()] = self._build_file_handler(
            filename=self.log_dir / f"{self.project_name}.log",
            level=self._root_level(),
        )

        self.__channel_mapping[self.project_name] = self.project_name

    def _build_formatters(self) -> Dict[str, dict]:

        simple = dict(format="%(logging_channel)s | %(levelname)s: %(message)s")
        verbose = dict(format="%(asctime)s %(logging_channel)s | %(levelname)s: %(name)s:%(lineno)d: %(message)s")
        detailed = dict(format="%(asctime)s %(logging_channel)s | %(levelname)s: pid=%(process)d tid=%(thread)d %(name)s:%(lineno)d: %(message)s")

        rich_fmt = dict(format="%(logging_channel)s | %(message)s")

        return dict(simple=simple, verbose=verbose, detailed=detailed, rich=rich_fmt)

    def _build_file_handler(self, filename: Path, level: str) -> dict:
        return dict(
            **{"class": "logging.handlers.RotatingFileHandler"},
            level=level,
            filename=str(filename),
            maxBytes=self.max_bytes,
            backupCount=self.backups,
            encoding="utf-8",
            formatter="verbose",
            filters=["logging_channel"],
        )

    def _root_file_handler_name(self) -> str:
        return f"file__{self.project_name}"

    def _ensure_file_handler(self, alias: str, level: str) -> str:
        name = f"file__{alias}"
        if name not in self.__handlers:
            self.__handlers[name] = self._build_file_handler(
                filename=self.log_dir / f"{alias}.log",
                level=level,
            )
        return name

    def _ensure_custom_handler(self, alias: str, level: str) -> str:
        name = f"custom__{alias}"
        if name not in self.__handlers:
            self.__handlers[name] = dict(
                **{"class": f"{__name__}.CallableHandler"},
                level=level,
                formatter="verbose",
                filters=["logging_channel"],
            )
        return name

    def _alias_for(self, logger_name: str) -> str:
        if logger_name == self.project_name:
            return self.project_name
        if logger_name.startswith(self.project_name + "."):
            parts = logger_name.split(".")
            return parts[1] if len(parts) > 1 else self.project_name
        return logger_name.split(".", 1)[0]
