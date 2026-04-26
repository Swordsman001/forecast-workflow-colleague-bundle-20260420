# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pdfplumber


@dataclass
class ProviderResult:
    source_type: str
    source_ref: str
    content: str
    metadata: dict[str, Any]


class EvidenceProvider:
    source_type = "unknown"

    def fetch(self, query: str, **kwargs) -> ProviderResult:
        raise NotImplementedError


def read_supported_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)
        return "\n".join(pages)

    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml_bytes)
        paragraphs: list[str] = []
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        for paragraph in root.findall(".//w:p", namespace):
            texts = [
                node.text
                for node in paragraph.findall(".//w:t", namespace)
                if node.text
            ]
            if texts:
                paragraphs.append("".join(texts))
        return "\n".join(paragraphs)

    return path.read_text(encoding="utf-8", errors="ignore")


class UserSuppliedTextProvider(EvidenceProvider):
    source_type = "user_supplied_text"

    def __init__(self, path: Path):
        self.path = path

    def fetch(self, query: str) -> ProviderResult:
        content = read_supported_text(self.path)
        return ProviderResult(
            source_type=self.source_type,
            source_ref=str(self.path),
            content=content,
            metadata={"query": query},
        )


class LocalKBProvider(EvidenceProvider):
    source_type = "local_kb"

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.script_path = repo_root / "scripts" / "wiki_query.py"

    def fetch(self, query: str) -> ProviderResult:
        if not self.script_path.exists():
            return ProviderResult(
                source_type=self.source_type,
                source_ref=str(self.script_path),
                content="",
                metadata={"query": query, "error": "wiki_query.py not found"},
            )

        completed = subprocess.run(
            [sys.executable, str(self.script_path), query],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        return ProviderResult(
            source_type=self.source_type,
            source_ref=str(self.script_path),
            content=completed.stdout.strip(),
            metadata={
                "query": query,
                "returncode": completed.returncode,
                "stderr": completed.stderr.strip(),
            },
        )


class AlphaPaiProvider(EvidenceProvider):
    source_type = "alpha_pai"

    CLIENT_PATH = Path(
        "C:/Users/26237/.claude/plugins/alphapai-research/alphapai-research/scripts/alphapai_client.py"
    )
    DEFAULT_RECALL_TYPES = ["roadShow", "roadShow_ir", "roadShow_us", "comment"]
    DEFAULT_TIMEOUT_SCHEDULE = (20, 45, 75)
    DEFAULT_LOOKBACK_DAYS = 365

    def _load_client(self):
        if not self.CLIENT_PATH.exists():
            return None
        client_dir = str(self.CLIENT_PATH.parent)
        if client_dir not in sys.path:
            sys.path.insert(0, client_dir)
        try:
            from alphapai_client import AlphaPaiClient, load_config  # type: ignore
        except Exception:
            return None
        config = load_config()
        if not config:
            return None
        return AlphaPaiClient(config)

    def _recall_records(
        self,
        query: str,
        *,
        recall_types: list[str] | None = None,
        timeout: int = 45,
        lookback_days: int | None = None,
    ) -> list[dict[str, Any]]:
        client = self._load_client()
        if client is None:
            raise RuntimeError("alphapai client not configured")
        end_time = datetime.now().strftime("%Y-%m-%d")
        start_time = (datetime.now() - timedelta(days=int(lookback_days or self.DEFAULT_LOOKBACK_DAYS))).strftime("%Y-%m-%d")
        payload = {
            "query": query,
            "isCutOff": False,
            "recallType": list(recall_types or self.DEFAULT_RECALL_TYPES),
            "startTime": start_time,
            "endTime": end_time,
        }
        result = client._post("/alpha/open-api/v1/paipai/recall-data", payload, timeout=timeout)
        if not isinstance(result, dict):
            raise RuntimeError("alphapai recall returned non-dict response")
        if result.get("code") != 200000:
            raise RuntimeError(
                f"alphapai recall failed: code={result.get('code')} message={result.get('message') or result.get('msg') or 'unknown'}"
            )
        data = result.get("data", [])
        return data if isinstance(data, list) else []

    def _record_snippet(self, record: dict[str, Any]) -> str:
        context = str(record.get("contextInfo") or "").strip()
        title = ""
        for part in context.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            if key.strip() in {"标题", "鏍囬"}:
                title = value.strip()
                break
        chunks = record.get("chunks") or []
        if isinstance(chunks, list):
            body = " ".join(str(item).strip() for item in chunks if str(item).strip())
        else:
            body = str(chunks).strip()
        body = body[:240]
        parts = [part for part in [title, context, body] if part]
        return " | ".join(parts)

    def fetch(
        self,
        query: str,
        *,
        recall_types: list[str] | None = None,
        timeout_schedule: tuple[int, ...] | list[int] | None = None,
        lookback_days: int | None = None,
    ) -> ProviderResult:
        effective_recall_types = list(recall_types or self.DEFAULT_RECALL_TYPES)
        attempts: list[dict[str, Any]] = []
        records: list[dict[str, Any]] = []
        last_error: str | None = None
        for attempt, timeout in enumerate(tuple(timeout_schedule or self.DEFAULT_TIMEOUT_SCHEDULE), start=1):
            try:
                records = self._recall_records(
                    query,
                    recall_types=effective_recall_types,
                    timeout=int(timeout),
                    lookback_days=lookback_days,
                )
                attempts.append(
                    {
                        "attempt": attempt,
                        "timeout": int(timeout),
                        "status": "ok",
                        "record_count": len(records),
                    }
                )
                last_error = None
                break
            except Exception as exc:
                last_error = str(exc)
                attempts.append(
                    {
                        "attempt": attempt,
                        "timeout": int(timeout),
                        "status": "error",
                        "error": last_error,
                    }
                )
                continue

        if last_error is not None:
            return ProviderResult(
                source_type=self.source_type,
                source_ref="alphapai:error",
                content="",
                metadata={
                    "query": query,
                    "available": False,
                    "error": last_error,
                    "attempts": attempts,
                    "recall_type": effective_recall_types,
                    "lookback_days": int(lookback_days or self.DEFAULT_LOOKBACK_DAYS),
                },
            )

        if not records:
            return ProviderResult(
                source_type=self.source_type,
                source_ref=f"alphapai:{query}",
                content="",
                metadata={
                    "query": query,
                    "available": False,
                    "record_count": 0,
                    "attempts": attempts,
                    "recall_type": effective_recall_types,
                    "lookback_days": int(lookback_days or self.DEFAULT_LOOKBACK_DAYS),
                },
            )

        snippets = [self._record_snippet(item) for item in records[:5]]
        ids = [str(item.get("id")) for item in records[:5] if item.get("id")]
        return ProviderResult(
            source_type=self.source_type,
            source_ref=f"alphapai:{query}",
            content="\n".join(snippets),
            metadata={
                "query": query,
                "available": True,
                "record_count": len(records),
                "record_ids": ids,
                "attempts": attempts,
                "recall_type": effective_recall_types,
                "lookback_days": int(lookback_days or self.DEFAULT_LOOKBACK_DAYS),
            },
        )


class ReportDownloadProvider(EvidenceProvider):
    source_type = "report_download"

    def fetch(self, query: str) -> ProviderResult:
        return ProviderResult(
            source_type=self.source_type,
            source_ref="stub",
            content="",
            metadata={"query": query, "available": False},
        )
