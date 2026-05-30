#!/usr/bin/env python3
"""Nightly research scraper: webclaw → LM Studio → ideas/research_queue/.

Usage:
    python scripts/nightly_research_scrape.py
    python scripts/nightly_research_scrape.py --dry-run
    python scripts/nightly_research_scrape.py --config configs/research_sources.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

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


def classify(text: str, cfg: dict) -> dict | None:
    payload = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": CLASSIFY_PROMPT.format(text=text)}],
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
    }
    try:
        r = httpx.post(
            f"{cfg['base_url']}/chat/completions",
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
        # strip markdown code fences if model wraps output
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
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
    out_cfg = cfg["output"]
    min_conf = float(out_cfg.get("min_confidence", 0.5))
    output_dir = REPO_ROOT / out_cfg["research_queue_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    sources = [s for s in cfg["sources"] if s.get("enabled", True)]
    log.info("sources: %d enabled", len(sources))

    saved = rejected = failed = 0

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
            classification = classify(text, lm_cfg)
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

    log.info("done — saved=%d rejected=%d failed=%d", saved, rejected, failed)
    if failed == len(sources):
        sys.exit(1)


if __name__ == "__main__":
    main()
