"""Chế độ bảo trì: trong lúc restore, middleware (main.py) chặn mọi ghi từ các route khác.

Cờ nằm trong bộ nhớ của tiến trình này (chạy một tiến trình uvicorn; nhiều worker thì mỗi worker một cờ riêng)."""
from __future__ import annotations

import threading


class MaintenanceState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def begin(self) -> bool:
        """Bật chế độ bảo trì; False nếu đã đang bật (người khác đang restore)."""
        with self._lock:
            if self._active:
                return False
            self._active = True
            return True

    def end(self) -> None:
        with self._lock:
            self._active = False
