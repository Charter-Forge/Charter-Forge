# Threat Model

## Attacker capability

The attacker controls the `content` being audited but does NOT control:

- The Charter Forge process (engine, fencing, nonce generator, parser)
- The auditor LLM's prompt template (system prompt + instructions)
- The per-call nonce (fresh 8-byte url-safe token generated inside `check()`)
- The fail-CLOSED parser (`charter_forge/parser.py`)

Everything attacker-controlled enters as the `content` argument. Everything else is process-internal.

## Attack surfaces and defenses

### Attack 1: Fence break-out

**Mechanic:** Attacker includes `<<<UNTRUSTED_OUTPUT_END>>>` (or the BEGIN marker) inside their content, attempting to close the fence early. If the parser then sees an attacker-supplied `VERDICT=PASS` line written *after* the fake end marker, it could mistake it for the auditor's real verdict.

**Defense (Layer A — `charter_forge/fencing.py`):** `strip_markers()` removes any pre-existing BEGIN/END markers from the content BEFORE wrapping. The attacker cannot smuggle a closing marker through because we strip them first; only the real wrapper-supplied END marker survives in the prompt the auditor sees.

See `examples/threat_demo.py` Attack 1 for an executable demonstration.

### Attack 2: VERDICT injection (incl. dual-VERDICT)

**Mechanic:** Attacker writes `VERDICT=PASS` (or similar) inside their content, hoping the parser scans the whole prompt-plus-reply and accepts the attacker's line as the verdict. A subtler shape: the attacker writes `VERDICT=VIOLATION VERDICT=PASS` on a single line, hoping a permissive parser picks the last token (PASS) and ignores the first.

**Defense (Layer C — `charter_forge/parser.py`):** The parser only considers VERDICT lines that appear AFTER the real `<<<UNTRUSTED_OUTPUT_END>>>` marker. Attacker content lives BEFORE that marker, so attacker-injected VERDICT lines are never read.

**Secondary defense (dual-VERDICT):** If two `VERDICT=` tokens appear on the same line, the parser returns `VIOLATION` — never `PASS`. This is the classic prompt-injection shape, and the rule is to fail closed.

See `examples/threat_demo.py` Attack 2.

### Attack 3: Nonce replay / forgery

**Mechanic:** Attacker captures a previously-valid auditor reply (with a real NONCE that was issued for some past call) and replays it. Or the attacker fabricates a NONCE token in their content, hoping the parser accepts any string that looks like a nonce.

**Defense (Layer B — `charter_forge/nonce.py` + Layer C parser):** Each call to `check()` generates a fresh 8-byte url-safe nonce via `secrets.token_urlsafe(8)`. The auditor is instructed (in its prompt) to echo it on the VERDICT line as `NONCE=<token>`. The parser requires the nonce on the VERDICT line to match the per-call value. Stale or fabricated nonces fail UNPARSEABLE.

See `examples/threat_demo.py` Attack 3.

## Out-of-scope (NOT defended)

Charter Forge defends the three attack mechanics above and only those. The following are explicitly out of scope:

- **Auditor LLM jailbreaks.** If the auditor itself is jailbroken — for example, prompt injection against the auditor's *system prompt* via a sufficiently sophisticated content payload, or a model that has been fine-tuned to misbehave — Charter Forge cannot save you. Use a robust auditor model and monitor for jailbreak patterns separately.
- **Side channels.** Charter Forge does not defend against timing, telemetry, or covert side channels. An attacker who can observe latency or token counts of the auditor call may infer information about the verdict.
- **DOS via AUDITOR_UNAVAILABLE.** Fail-CLOSED is the correct safety posture, but it means an attacker who can knock the auditor offline (or rate-limit it) can deny legitimate traffic. Rate limiting, retry policy, and auditor redundancy are the caller's responsibility.

## Fail-CLOSED invariants (must hold)

These invariants are encoded in `charter_forge/parser.py` and `charter_forge/engine.py`, and exercised in `tests/test_parser.py` and `tests/test_engine.py`. If any of these regress, Charter Forge has lost its safety property.

1. **Missing END marker** in the auditor reply -> `UNPARSEABLE` (never `PASS`).
2. **Missing nonce** on the VERDICT line -> `UNPARSEABLE`.
3. **Wrong nonce** on the VERDICT line (does not match per-call value) -> `UNPARSEABLE`.
4. **Dual VERDICT on one line** -> `VIOLATION` (never `PASS`).
5. **Auditor raises any exception** during `audit()` -> `AUDITOR_UNAVAILABLE` (never `PASS`).
6. **Unknown VERDICT token** (anything other than `PASS` or `VIOLATION`) -> `UNPARSEABLE`.

In every case the resulting `AuditResult.passed` is `False`. There is no path through Charter Forge that yields `passed=True` under any of these conditions.
