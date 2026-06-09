#!/usr/bin/env python3
"""Nightly research scraper: webclaw + API sources → LM Studio → ideas/research_queue/.

Usage:
    python scripts/nightly_research_scrape.py
    python scripts/nightly_research_scrape.py --dry-run
    python scripts/nightly_research_scrape.py --config configs/research_sources.json

API keys (optional — set in .env or environment):
    FINNHUB_API_KEY   — from finnhub.io (free tier)
    TWELVE_DATA_KEY   — from twelvedata.com (free tier)
    NVIDIA_API_KEY    — from build.nvidia.com (free tier, fallback when LM Studio offline)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")
TWELVE_KEY = os.getenv("TWELVE_DATA_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG = REPO_ROOT / "configs" / "research_sources.json"

CLASSIFY_PROMPT = """\
You are a trading research classifier. Read the text below and classify it.

Categories (pick exactly one):
- strategy_idea   : describes a tradeable entry/exit rule or backtested approach
- indicator       : describes a new or improved technical/statistical indicator
- risk_update     : describes market risk, regime change, or volatility event
- loop_skill      : describes a process, tool, or workflow improvement for a trading system
- reject          : not relevant to systematic trading research

Reply with JSON only, no prose:
{{"category": "<category>", "confidence": <0.0-1.0>, "one_line_summary": "<max 120 chars>"}}

Text:
{text}
"""


def load_config(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def scrape(url: str, timeout: int, max_chars: int) -> str | None:
    try:
        result = subprocess.run(
            ["webclaw", "extract", url, "--format", "text"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            log.warning("webclaw failed for %s: %s", url, result.stderr[:200])
            return None
        return result.stdout[:max_chars].strip() or None
    except FileNotFoundError:
        log.error("webclaw not found — install from https://github.com/0xMassi/webclaw")
        return None
    except subprocess.TimeoutExpired:
        log.warning("webclaw timeout for %s", url)
        return None


def fetch_api(source: dict, max_chars: int) -> str | None:
    """Fetch text from a structured API source (Finnhub, Twelve Data)."""
    api_type = source.get("api_type")
    try:
        if api_type == "finnhub_news":
            if not FINNHUB_KEY:
                log.warning("FINNHUB_API_KEY not set — skipping %s", source["label"])
                return None
            category = source.get("category", "general")
            r = httpx.get(
                "https://finnhub.io/api/v1/news",
                params={"category": category, "token": FINNHUB_KEY},
                timeout=20,
            )
            r.raise_for_status()
            items = r.json()[:10]  # top 10 headlines
            lines = [f"{i['headline']}\n{i.get('summary','')}" for i in items if i.get("headline")]
            return "\n\n".join(lines)[:max_chars] or None

        if api_type == "twelve_data_quote":
            if not TWELVE_KEY:
                log.warning("TWELVE_DATA_KEY not set — skipping %s", source["label"])
                return None
            symbol = source.get("symbol", "XAU/USD")
            r = httpx.get(
                "https://api.twelvedata.com/quote",
                params={"symbol": symbol, "apikey": TWELVE_KEY},
                timeout=20,
            )
            r.raise_for_status()
            d = r.json()
            text = (
                f"Symbol: {d.get('symbol')} | Name: {d.get('name')}\n"
                f"Price: {d.get('close')} | Change: {d.get('percent_change')}%\n"
                f"52w high: {d.get('fifty_two_week',{}).get('high')} | "
                f"52w low: {d.get('fifty_two_week',{}).get('low')}\n"
                f"Volume: {d.get('volume')} | Exchange: {d.get('exchange')}\n"
                f"Timestamp: {d.get('datetime')}"
            )
            return text

    except Exception as e:
        log.warning("API fetch failed for %s: %s", source.get("label"), e)
    return None


def _call_llm(cfg: dict, payload: dict, headers: dict | None) -> dict | None:
    r = httpx.post(
        f"{cfg['base_url']}/chat/completions",
        json=payload,
        headers=headers or {},
        timeout=60,
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)


def classify(text: str, cfg: dict, fallback_cfg: dict | None = None, fallback_headers: dict | None = None) -> dict | None:
    payload = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": CLASSIFY_PROMPT.format(text=text)}],
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
    }
    try:
        return _call_llm(cfg, payload, None)
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        if fallback_cfg and fallback_headers:
            log.warning("LM Studio unreachable (%s) — trying NVIDIA NIM fallback", e)
            payload["model"] = fallback_cfg["model"]
            try:
                return _call_llm(fallback_cfg, payload, fallback_headers)
            except Exception as e2:
                log.warning("NVIDIA NIM classify failed: %s", e2)
        else:
            log.warning("LM Studio unreachable and no fallback configured: %s", e)
        return None
    except Exception as e:
        log.warning("LM Studio classify failed: %s", e)
        return None


def write_result(
    source: dict,
    classification: dict,
    text: str,
    output_dir: Path,
    date_str: str,
    dry_run: bool,
) -> None:
    category = classification.get("category", "reject")
    confidence = float(classification.get("confidence", 0.0))
    summary = classification.get("one_line_summary", "")
    url = source["url"]
    uid = hashlib.md5(url.encode()).hexdigest()[:10]
    slug = summary.lower()[:50].replace(" ", "-").replace("/", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    filename = f"nightly-{date_str}-{uid}-{slug}.md"

    content = f"""---
idea_id: nightly-{date_str}-{uid}
title: {summary}
status: hypothesis_extracted
source_url: {url}
source_label: {source['label']}
category: {category}
confidence: {confidence}
tags: {json.dumps(source.get('tags', []))}
created_from: nightly_research_scrape
created_at: {datetime.now(timezone.utc).isoformat()}
---

# {summary}

## Classification
- Category: `{category}`
- Confidence: {confidence}
- Source: [{source['label']}]({url})

## Extracted Text (truncated)

{text[:2000]}
"""

    path = output_dir / filename
    if dry_run:
        log.info("[DRY RUN] would write: %s", path)
        print(content[:400])
    else:
        path.write_text(content)
        log.info("wrote: %s", path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    lm_cfg = cfg["lm_studio"]
    wc_cfg = cfg["webclaw"]
    nim_cfg = cfg.get("nvidia_nim")
    nim_headers = {"Authorization": f"Bearer {NVIDIA_KEY}"} if (nim_cfg and NVIDIA_KEY) else None
    if nim_cfg and not NVIDIA_KEY:
        log.warning("nvidia_nim configured but NVIDIA_API_KEY not set — fallback disabled")
    out_cfg = cfg["output"]
    min_conf = float(out_cfg.get("min_confidence", 0.5))
    output_dir = REPO_ROOT / out_cfg["research_queue_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    sources = [s for s in cfg["sources"] if s.get("enabled", True)]
    log.info("sources: %d enabled", len(sources))

    saved = rejected = failed = 0

    api_sources = [s for s in cfg.get("api_sources", []) if s.get("enabled", True)]
    log.info("api_sources: %d enabled", len(api_sources))

    for source in sources:
        url = source["url"]
        log.info("scraping: %s", url)

        text = scrape(url, wc_cfg["timeout_seconds"], wc_cfg["max_chars"])
        if not text:
            failed += 1
            continue

        if args.dry_run:
            log.info("[DRY RUN] scraped %d chars from %s", len(text), url)
            classification = {"category": "strategy_idea", "confidence": 0.9,
                              "one_line_summary": "dry-run placeholder"}
        else:
            classification = classify(text, lm_cfg, nim_cfg, nim_headers)
            if not classification:
                failed += 1
                continue

        category = classification.get("category", "reject")
        confidence = float(classification.get("confidence", 0.0))

        if category == "reject" or confidence < min_conf:
            log.info("rejected (%s conf=%.2f): %s", category, confidence, url)
            rejected += 1
            continue

        write_result(source, classification, text, output_dir, date_str, args.dry_run)
        saved += 1

    # API sources
    for source in api_sources:
        log.info("api fetch: %s", source["label"])
        text = fetch_api(source, wc_cfg["max_chars"])
        if not text:
            failed += 1
            continue

        source.setdefault("url", f"api://{source.get('api_type','unknown')}/{source.get('label','')}")

        if args.dry_run:
            log.info("[DRY RUN] api fetched %d chars from %s", len(text), source["label"])
            classification = {"category": "risk_update", "confidence": 0.9,
                              "one_line_summary": "dry-run api placeholder"}
        else:
            classification = classify(text, lm_cfg, nim_cfg, nim_headers)
            if not classification:
                failed += 1
                continue

        category = classification.get("category", "reject")
        confidence = float(classification.get("confidence", 0.0))

        if category == "reject" or confidence < min_conf:
            log.info("rejected (%s conf=%.2f): %s", category, confidence, source["label"])
            rejected += 1
            continue

        write_result(source, classification, text, output_dir, date_str, args.dry_run)
        saved += 1

    log.info("done — saved=%d rejected=%d failed=%d", saved, rejected, failed)
    total = len(sources) + len(api_sources)
    if total > 0 and failed == total:
        sys.exit(1)


if __name__ == "__main__":
    main()
