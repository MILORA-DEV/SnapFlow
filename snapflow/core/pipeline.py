"""Screenshot capture and action pipeline."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from dataclasses import dataclass
from functools import partial
from typing import Callable, Optional

from snapflow.core.actions import ActionError, execute_action
from snapflow.core.analyzer import AnalyzerError, AnalysisResult, analyze_screenshot
from snapflow.core.capture import Region, SelectionOverlay, capture_region, image_to_base64

logger = logging.getLogger(__name__)


@dataclass
class CaptureResult:
    message: str
    success: bool
    action_type: str = ""
    data_preview: str = ""


class CapturePipeline:
    """Hotkey -> selection overlay -> analyze -> execute action."""

    def __init__(
        self,
        root: tk.Misc,
        *,
        on_status: Callable[[str], None],
        on_finished: Callable[[CaptureResult], None],
    ) -> None:
        self._root = root
        self._on_status = on_status
        self._on_finished = on_finished
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def request_capture(self) -> None:
        if self._busy:
            self._emit_finished(
                CaptureResult(
                    message="Already processing a capture.",
                    success=False,
                )
            )
            return

        self._busy = True
        self._on_status("Selecting…")

        def on_region_selected(region: Optional[Region]) -> None:
            if region is None:
                self._emit_finished(
                    CaptureResult(message="Selection cancelled.", success=False)
                )
                return
            threading.Thread(
                target=self._process_capture,
                args=(region,),
                daemon=True,
            ).start()

        SelectionOverlay(self._root, on_region_selected)

    def _process_capture(self, region: Region) -> None:
        try:
            self._schedule_status("Capturing…")
            image = capture_region(region)
            image_b64 = image_to_base64(image)

            self._schedule_status("Analyzing…")
            result: AnalysisResult = analyze_screenshot(image_b64)

            self._schedule_status("Executing…")
            message = execute_action(result.type, result.data)
            self._emit_finished(
                CaptureResult(
                    message=message,
                    success=True,
                    action_type=result.type,
                    data_preview=result.data,
                )
            )
        except (AnalyzerError, ActionError) as exc:
            self._emit_finished(
                CaptureResult(message=str(exc), success=False)
            )
        except Exception as exc:
            logger.exception("Unexpected error during capture pipeline")
            self._emit_finished(
                CaptureResult(
                    message=f"Unexpected error: {exc}",
                    success=False,
                )
            )

    def _schedule_status(self, status: str) -> None:
        self._root.after(0, partial(self._on_status, status))

    def _emit_finished(self, result: CaptureResult) -> None:
        def finish() -> None:
            self._busy = False
            self._on_status("Ready")
            self._on_finished(result)

        self._root.after(0, finish)
