# Charter Forge

Three-layer nonce-anti-injection defense for LLM auditor patterns.

## Pitch

When you ask an LLM to evaluate another LLM's output for charter / policy compliance, the audited content can attempt to forge the auditor's reply. Charter Forge defends against three concrete attack classes:

1. **Fence break-out** — attacker injects a fake END marker into the audited content to escape the fence, then writes a fabricated VERDICT line that the parser will see as the auditor's.
2. **Dual-VERDICT injection** — attacker writes `VERDICT=PASS` on the same line where the real verdict appears, hoping a permissive parser picks the wrong one.
3. **Nonce replay / forgery** — attacker reuses a stale auditor reply, or fabricates a NONCE token that was never issued for this call.

The library FAILS-CLOSED. Anything uncertain — auditor unreachable, missing nonce, dual VERDICT on a line, no END marker, unknown verdict token — is NOT PASS. This is a categorical rule, not best-effort. A categorical rule that opts to PASS during outage is operationally not categorical.

## Install

```
pip install charter-forge
```

## Quick start

```python
from charter_forge import check
from charter_forge.auditors import LLMAuditor

auditor = LLMAuditor(model="claude-3-5-haiku-20241022")
result = check(
    content="The model achieved an unspecified accuracy improvement.",
    auditor=auditor,
    charter_rules="Rule 1: no fabricated quantitative claims.",
)
if result.passed:
    publish(content)
else:
    block(reason=result.reason)
```

## Architecture

```
                      content (untrusted)
                              |
                              v
   +----------------------------------------------------+
   |  LAYER A  fencing.py                               |
   |   strip pre-existing markers, then wrap in         |
   |   <<<UNTRUSTED_OUTPUT_BEGIN>>> ... END>>>          |
   |   Defeats: fence break-out                         |
   +----------------------------------------------------+
                              |
                              v
   +----------------------------------------------------+
   |  LAYER B  nonce.py                                 |
   |   per-call 8-byte url-safe token (token_urlsafe)   |
   |   directive tells auditor: echo NONCE=<token>      |
   |   Defeats: nonce replay / forgery                  |
   +----------------------------------------------------+
                              |
                              v
                  auditor LLM call (pluggable)
                              |
                              v
   +----------------------------------------------------+
   |  LAYER C  parser.py  (fail-CLOSED)                 |
   |   - no END marker            -> UNPARSEABLE        |
   |   - no VERDICT after end     -> UNPARSEABLE        |
   |   - dual VERDICT one line    -> VIOLATION          |
   |   - missing/wrong nonce      -> UNPARSEABLE        |
   |   - unknown VERDICT token    -> UNPARSEABLE        |
   +----------------------------------------------------+
                              |
                              v
                          AuditResult
```

## Examples

- [`examples/threat_demo.py`](examples/threat_demo.py) — runs all three attack classes against `MockAuditor` and shows each is blocked.
- [`examples/benchmark.py`](examples/benchmark.py) — measures structural overhead vs a naive regex baseline.

## Design principles

- **Fail-CLOSED on uncertainty.** Categorical rule, not "best effort." If we can't verify, we don't pass.
- **No silent degradation.** `AUDITOR_UNAVAILABLE` is its own verdict — never silently treated as PASS.
- **Pluggable auditor.** `Protocol`-based; bring your own LLM. Default `LLMAuditor` uses LiteLLM (100+ providers).
- **Small, typed, fast.** ~500 lines including tests. `mypy --strict` clean. Sub-millisecond structural overhead.

## Benchmarks

Measured on commodity hardware (Python 3.14, Windows 11, no GPU) via `examples/benchmark.py`:

```
Charter Forge: mean=0.004ms  median=0.003ms  n=300 samples
Naive regex:   mean=0.001ms  median=0.001ms
Overhead:      4.0x (structural only)
```

Real-world end-to-end latency is dominated by the auditor LLM round-trip (typically 200-2000ms depending on model and provider). Charter Forge's own structural overhead is sub-millisecond.

## License

MIT. See `LICENSE`.

## Author

Maintained by Austin Brunner (@JamesCrasher). Extracted from the Uriel personal-AGI research project.
