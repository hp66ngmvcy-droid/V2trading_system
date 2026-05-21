Repository: nautilus_trader
URL: https://github.com/nautechsystems/nautilus_trader

Primary focus for review:
- High-performance architecture and how market data ingestion is handled
- Order execution simulation and latency modelling
- Any queue or orchestration primitives suitable for research pipelines

Questions for reviewer:
- Which components (C++/Rust) are relevant for TAR as design patterns only?
- Are there tested approaches to avoid duplicate work at ingestion or job scheduling?

Notes: Read design docs and architecture diagrams only. No build.