"""Latency overhead of Charter Forge vs naive regex (structural only).

Run: python examples/benchmark.py

Uses MockAuditor (zero-latency) to isolate Charter Forge's own overhead.
Real-world adds 200-2000ms for the auditor LLM round-trip on top of these numbers.
"""

import re
import time
from statistics import mean, median

from charter_forge import check
from charter_forge.auditors import MockAuditor

REPLY = "<<<UNTRUSTED_OUTPUT_END>>>\nVERDICT=PASS NONCE={nonce}"
RULES = "Rule 1: no deceptive claims."

samples = ["the model achieved an unspecified accuracy improvement"] * 300

auditor = MockAuditor(reply_template=REPLY)
cf: list[float] = []
for c in samples:
    t = time.perf_counter()
    check(content=c, auditor=auditor, charter_rules=RULES)
    cf.append((time.perf_counter() - t) * 1000)

NAIVE = re.compile(r"\b\d+%")
naive: list[float] = []
for c in samples:
    t = time.perf_counter()
    NAIVE.search(c)
    naive.append((time.perf_counter() - t) * 1000)

print(f"Charter Forge: mean={mean(cf):.3f}ms  median={median(cf):.3f}ms  n={len(cf)}")
print(f"Naive regex:   mean={mean(naive):.3f}ms  median={median(naive):.3f}ms")
print(f"Overhead:      {mean(cf)/mean(naive):.1f}x structural only")
print("Real-world adds 200-2000ms auditor LLM round-trip on top of these numbers.")
