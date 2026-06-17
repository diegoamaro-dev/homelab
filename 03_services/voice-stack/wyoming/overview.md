# Wyoming Protocol — Overview

- **Scope:** AURORA's voice stack uses Wyoming as the
  spine. This page explains what Wyoming is, why it
  was chosen, and the rules AURORA's voice
  containers follow.
- **Status:** D-1.1 skeleton.

---

## 1. What Wyoming is

Wyoming is a small line-delimited JSON protocol
designed by the Home Assistant / Rhasspy team to
chain voice components (wake-word, STT, conversation,
TTS, satellites) over TCP.

Key properties:

- Transport: plain TCP, line-delimited JSON header +
  optional binary payload (audio frames).
- Stateless framing per request.
- Same protocol whether the endpoint runs on the same
  host or across a network.
- First-class integration with Home Assistant via the
  built-in "Wyoming Protocol" integration.

---

## 2. Why AURORA uses Wyoming (and not a custom REST
   protocol)

| Reason | Detail |
|---|---|
| HA-native | HA Assist's STT / TTS / wake-word slots accept Wyoming endpoints out of the box. No custom HA integration to maintain. |
| Location-agnostic | The same `host:port` works on Docker network, LAN, or Tailscale. Enables the future RTX node migration. |
| Multi-consumer-friendly | A single Wyoming endpoint can serve HA and a Wyoming satellite simultaneously. |
| Future hardware | All shipping voice satellites in the HA ecosystem speak Wyoming (HA Voice PE, M5 ATOM Echo with `wyoming-satellite`, ESP32-S3-BOX-3). |
| OpenAI gap covered by HTTP shims | Open WebUI does not speak Wyoming; the HTTP shims (faster-whisper-server, Piper OpenAI-compatible mode) handle that without duplicating the underlying model. |

---

## 3. Wyoming endpoints used by AURORA

| Component | Container | Wyoming port |
|---|---|---|
| STT | `aurora-whisper` | `10300/tcp` |
| TTS | `aurora-piper` | `10200/tcp` |
| Wake word | `aurora-wakeword` | `10400/tcp` |
| Satellite (D-2 hardware) | per-device | `10700/tcp` (typical) |

All ports are **internal** to `ai-local_default`. They
are not published to the host.

---

## 4. HA-side configuration

In HA Settings → Devices & Services → Add Integration →
**Wyoming Protocol**, one entry per endpoint:

| Name | Host | Port |
|---|---|---|
| AURORA Whisper | `aurora-whisper` | `10300` |
| AURORA Piper | `aurora-piper` | `10200` |
| AURORA Wake | `aurora-wakeword` | `10400` |

Pipeline assembly is documented in
[`../ha-assist/pipeline-spec.md`](../ha-assist/pipeline-spec.md).

---

## 5. Validation

Each Wyoming endpoint must respond to a minimal probe
before being added to the HA pipeline:

```bash
# Conceptual — exact commands captured in each
# component's deployment doc.
wyoming-cli describe tcp://aurora-whisper:10300
wyoming-cli describe tcp://aurora-piper:10200
wyoming-cli describe tcp://aurora-wakeword:10400
```

Expected: each endpoint returns its `info` payload
listing supported models / voices / wake-words.

---

## 6. Reference

- Wyoming protocol spec: <https://github.com/rhasspy/wyoming> (upstream)
- HA Wyoming Protocol integration:
  documentation lives in HA's own docs; do not embed
  links to non-pinned external content here.
- AURORA components consuming Wyoming:
  - [`../whisper/faster-whisper-deployment.md`](../whisper/faster-whisper-deployment.md)
  - [`../piper/piper-deployment.md`](../piper/piper-deployment.md)
  - [`../wakeword/openwakeword-deployment.md`](../wakeword/openwakeword-deployment.md)
  - [`../ha-assist/pipeline-spec.md`](../ha-assist/pipeline-spec.md)
