
import json
from pathlib import Path
from typing import Optional

from src.config.settings import LOG_ROOT
from src.models.shadow_trace import ShadowTrace
from src.utils.ids import build_id


class ShadowTracer:
    def __init__(self, shadow_file: Optional[Path] = None) -> None:
        LOG_ROOT.mkdir(parents=True, exist_ok=True)
        self.shadow_file = shadow_file or (LOG_ROOT / "shadow_traces.jsonl")

    def start_trace(self, *, case_id: str, trace_id: str) -> ShadowTrace:
        return ShadowTrace(
            record_id=build_id("shadowrec"),
            record_type="ShadowTrace",
            shadow_id=build_id("shadow"),
            case_id=case_id,
            trace_id=trace_id,
        )

    def append(
        self,
        trace: ShadowTrace,
        *,
        module: str,
        note: str = "",
        block_code: Optional[str] = None,
    ) -> ShadowTrace:
        trace.executed_modules.append(module)
        if note:
            trace.technical_notes.append(note)
        if block_code:
            trace.blocks.append(block_code)
        with self.shadow_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(trace.to_dict(), ensure_ascii=False) + "\n")
        return trace