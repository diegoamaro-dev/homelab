# Phase D — Security and Permissions

- **Assistant:** **AURORA** (Amarolab Personal AI
  Assistant).
- **Status:** D-1.1 skeleton. The voice-specific
  durable security reference is
  [`../../../06_security/voice_privacy.md`](../../../06_security/voice_privacy.md);
  this file describes the **Phase D security boundary
  changes** specifically.

---

## 1. Two boundaries, one entity layer

AURORA's chat path (Open WebUI) and voice path
(HA Assist) carry separate safety boundaries that
**both** terminate at HA's entity layer:

```
chat  → qwen2.5 + Tool layer → ha_call_service ──┐
                                                 │ Tool D-12 allowlist
                                                 ▼
voice → qwen2.5 + HA Ollama → HA intents  ──────►  HA entity layer  → device
                                                 ▲
                                                 │ HA "Expose to voice
                                                 │ assistants" toggle
```

| Boundary | Where enforced | Documented in |
|---|---|---|
| Tool D-12 allowlist | `ha_call_service` (Open WebUI tool) | [`../04-security-and-permissions.md`](../04-security-and-permissions.md) |
| HA voice exposure toggle | HA `expose_to: voice` per entity | this file + [`../../../03_services/voice-stack/ha-assist/pipeline-spec.md`](../../../03_services/voice-stack/ha-assist/pipeline-spec.md) |

---

## 2. Voice exposure ramp-up

| Phase | Exposed entities | Rationale |
|---|---|---|
| D-1.5 (G-D4) | `input_boolean.aurora_voice_canary` (new HA helper, no physical effect) | Pure pipeline validation |
| D-1.6 (G-D5) | `input_boolean.aurora_voice_canary` + `switch.impresora_3d` | Gate G-5 entity reused — comparable evidence |
| D-2+ | Ramp-up per documented change | One entity per documented apply log |

### 2.1 Always-denied (must never be exposed)

| Pattern | Reason |
|---|---|
| `homeassistant.*` | HA system services — same rule as the Tool D-12 allowlist |
| `hassio.*` | Supervisor surface |
| `recorder.*` | Storage layer |
| Any entity that can disable HA itself | Bricks the front door |
| Any Guardian Cloud-related entity (if it ever exists in HA) | Production rule from `06_security/security_posture.md` |

### 2.2 Allowed domains (echoed from Tool layer for symmetry)

`light`, `switch`, `scene`, `cover`, `climate`,
`media_player`, `script`, `automation`, `fan`,
`vacuum`, `input_boolean`, `input_select`,
`input_number`.

Within these domains, **only entities explicitly
toggled "Expose to voice assistants" in HA** are
reachable by voice.

---

## 3. Data paths and what crosses what

| Hop | Data | Crosses |
|---|---|---|
| PC mic → Browser → HA UI | Raw audio (PCM/Opus, browser-side encoded) | LAN, HTTPS/HTTP to HA. **Never WAN.** |
| HA → Whisper | Audio frames over Wyoming TCP | `ai-local_default` Docker network. Never published. |
| HA → Ollama (conversation) | Transcript text + context | Docker network. Never published. |
| Ollama → HA | Response text | Docker network. |
| HA → Piper | Response text | Docker network. |
| Piper → HA → Browser → PC speaker | Synthesised audio | Docker network → HA HTTP → browser. LAN only. |
| Voice exposure list | Plaintext entity IDs | HA configuration only; no copy to repo |

Nothing in this pipeline reaches WAN. Nothing reaches
Cloudflared. Nothing reaches a third-party API.

---

## 4. Secrets

Phase D introduces **zero** new secrets to the repo.

| Surface | Secret? | Handling |
|---|---|---|
| Wyoming endpoints | None | Localhost / Docker network only |
| HA Ollama integration | None | Uses existing `http://ollama:11434` |
| Open WebUI STT/TTS shims | None | Internal HTTP, no auth required inside Docker network |
| HA Voice exposure config | Not a secret | Lives in HA's storage; never in repo |
| ESPHome API key (D-2 hardware) | Yes | Per-device, generated at flash time, stored alongside existing operator secrets at `/home/diego/.secrets/` |

The repo policy from
[`../../../06_security/security_posture.md`](../../../06_security/security_posture.md)
applies unchanged: no passwords, tokens, API keys,
private keys, cookies, session data, or `.env` files
in Git.

---

## 5. Audit trail

| Source | Where it lands today | Phase D change |
|---|---|---|
| Tool layer (chat → `ha_call_service`) | `/srv/homelab/data/openwebui/amarolab-audit.log` | unchanged |
| HA Assist (voice pipeline events) | HA's voice pipeline log (in HA's storage) | available out of the box |
| Voice-originated entity action | HA logbook + state history | available out of the box |
| Cross-source correlation | n/a | **Open question Q-D-05.** D-1 documents the gap; D-2 may bridge HA voice events into `amarolab-audit.log` |

Open question Q-D-05 (also in
[`01-current-state-review.md`](01-current-state-review.md))
is **explicitly accepted as a gap for D-1** and tracked
forward.

---

## 6. Failure-mode safety

| Failure | Safety impact | Containment |
|---|---|---|
| Wake-word false-positive on hardware satellite (D-2+) | Ambient audio sent to Whisper | Wake-word runs on satellite; audio stays on LAN; D-1 not affected (push-to-talk only) |
| qwen2.5 misinterprets voice and emits a real intent | Unintended state change | Only HA-exposed entities are reachable; ramp-up policy limits blast radius |
| Voice request asks for a forbidden domain | HA's intent layer has no matching intent → refusal | Documented behaviour; matches Tool layer's refusal pattern |
| Pipeline timeout fires | User hears an error or silence | No safety impact; documented in G-D6 |
| Network partition (browser ↔ HA) | Browser shows connection error | No safety impact |

---

## 7. Production segregation

Per [`../../../06_security/security_posture.md`](../../../06_security/security_posture.md):

- **Guardian Cloud is production.** Phase D does not
  modify any Guardian Cloud surface. Whisper, Piper,
  openWakeWord, and the HA Assist pipeline are all
  net-new and do not share state with Guardian Cloud.
- **Backups before major changes.** Per Lesson 005,
  D-1 takes a Restic snapshot before container creates
  begin (D-1.2). Recorded in the corresponding apply
  log.

---

## 8. Related documents

- [`02-target-architecture.md`](02-target-architecture.md) — the broader architecture
- [`05-validation-gates.md`](05-validation-gates.md) — voice gates G-D1…G-D6
- [`../../../06_security/voice_privacy.md`](../../../06_security/voice_privacy.md) — durable voice privacy reference
- [`../../../03_services/voice-stack/ha-assist/pipeline-spec.md`](../../../03_services/voice-stack/ha-assist/pipeline-spec.md) — exposure list per gate
