# Architecture

## Single function, three layers

The public API is one function:

```python
charter_forge.check(content, auditor, charter_rules) -> AuditResult
```

Internally that one function passes through three layers — fencing, nonce, and a fail-CLOSED parser — with the auditor LLM as the only external boundary.

```
  content + auditor + rules
          |
          v
  fence(content)                # Layer A: strip pre-existing markers + wrap
          |
          v
  prompt + per-call nonce       # Layer B: secrets.token_urlsafe(8) directive
          |
          v
  auditor.audit(...)            # external boundary (LLM call)
          |
          v
  parse_verdict(raw, nonce)     # Layer C: fail-CLOSED parser
          |
          v
  AuditResult(passed, verdict, reason)
```

Implementation lives in `charter_forge/engine.py`. Each layer has its own small module: `fencing.py`, `nonce.py`, `parser.py`. None exceeds 400 LOC.

## Why Protocol-based auditor

The auditor contract is declared as a `typing.Protocol` (PEP 544) in `charter_forge/auditors/base.py`:

```python
class AuditorProtocol(Protocol):
    def audit(self, *, prompt: str, nonce: str) -> str: ...
```

Any class with a matching `audit()` method satisfies it — no inheritance required. This is structural typing (duck-typing checked statically by mypy) rather than nominal typing (inherit from an ABC).

Concrete implementations shipped with the library:

- `LLMAuditor` (`charter_forge/auditors/llm.py`) — LiteLLM-backed. Supports 100+ provider models (Anthropic, OpenAI, Groq, local Ollama, etc.) through a single interface. Default for production use.
- `MockAuditor` (`charter_forge/auditors/mock.py`) — deterministic reply template; used by tests and `examples/threat_demo.py`.

Downstream users can plug in their own — in-house inference server, custom local model, a recorded fixture — by writing a class with `audit(self, *, prompt, nonce) -> str`. No Charter Forge import required for the auditor; no base class to inherit.

Protocol vs ABC matters here because Charter Forge is a library, not a framework. We do not want to force users to inherit from our type just to plug in an auditor.

## Why fail-CLOSED

A categorical rule that opts to `PASS` during uncertainty is operationally not categorical. Per Kantian discipline: the rule must hold uniformly across cases, including the uncertain ones. If the auditor is unreachable, if the nonce is missing, if the parser sees an unknown VERDICT token — the verdict is NOT `PASS`. Anything else would be silent degradation and would defeat the entire defense, since the attacker's goal is precisely to produce conditions under which a permissive parser opts to pass.

Concretely:

- `AuditorProtocol.audit()` raising any exception -> `AUDITOR_UNAVAILABLE` (not `PASS`).
- Reply missing the END marker, or with no VERDICT after it -> `UNPARSEABLE` (not `PASS`).
- Reply missing or mismatching the per-call nonce -> `UNPARSEABLE` (not `PASS`).
- Two `VERDICT=` tokens on one line -> `VIOLATION` (not `PASS`).

Reference: CLAUDE.md §3 fail-CLOSED principle, which encodes the same discipline for Uriel's charter auditor cascade. Charter Forge is the same idea, extracted as a small reusable library.

## Performance characteristics

Structural overhead — everything except the auditor LLM call — is sub-millisecond on commodity hardware. Measured via `examples/benchmark.py` on Python 3.14, Windows 11, no GPU, with `MockAuditor` (zero-latency) to isolate Charter Forge's own cost:

```
Charter Forge: mean=0.004ms  median=0.003ms  n=300 samples
Naive regex:   mean=0.001ms  median=0.001ms
Overhead:      4.0x structural only
```

Real-world end-to-end latency is dominated by the auditor LLM round-trip (typically 200-2000ms depending on model and provider). At those latencies Charter Forge's structural overhead is negligible: 0.004ms on top of 500ms is a 0.0008% increase.

See `examples/benchmark.py` for the measurement harness; numbers above are reproducible by running it locally.
