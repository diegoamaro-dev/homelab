# Daily Summary

Date: 2026-06-18

## Completed

- Dedicated Cloudflare tunnel for Amarolab deployed
  (`cloudflared-amarolab` on `ai-local_default`)
- `ha.amarolab.es` exposed through HTTPS
- Home Assistant trusted-proxy + `external_url`
  configuration applied
- Aurora v1 voice pipeline validated end-to-end
- Gate G-D4 passed (voice canary
  Read → Write → Verify → Restore)
- D-1.5 closed (AURORA v1 Assist pipeline + voice
  canary + voice-exposure lockdown)
- Documentation updated and D-1.5 apply log promoted
  from DRAFT
- Gate G-D5 passed (real-device voice round-trip on
  `switch.impresora_3d` via Mosquitto + Z2M; voice
  Write + voice Restore; baseline `off` restored)
- D-1.6 closed
- D-1.7 closed (Open WebUI Audio integration:
  `aurora-whisper-http` + `aurora-piper-http`;
  `webui.db.audio.*` patched; `ai.amarolab.es` now
  serves voice + chat; closes G-D1 HTTP-shim half,
  G-D2 HTTP-shim half, C-D-07, C-D-09)
- Gate G-D6 passed (failure-mode rehearsal — Whisper
  down, Piper down, Ollama unreachable; one
  acceptance partial on HA TTS-failure log
  granularity; functional behaviour PASS; canary
  baseline restored; printer untouched)
- D-1.8 closed
- D-1.9 Phase D-1 closeout authored
- Overview triad (`CURRENT_STATE.md`,
  `AMAROLAB_HANDOFF.md`, `ROADMAP.md`) reconciled
  with validated state
- Phase D-1 closeout document landed at
  `09_logs/2026-06-18_phaseD1_closeout.md`
- Phase RTX-1 (Torre GPU node) local validation
  recorded; overview triad + `lessons_learned.md`
  synchronized after review and committed
  (`d50aa207`, pushed to `origin/main`). Secrets
  review passed; private node IPs retained by
  decision — repo-wide IP-hygiene pass deferred to
  ROADMAP.

## Result

Aurora v1 voice operational on **both front doors**:

- **Home Assistant voice** —
  `https://ha.amarolab.es` (Assist pipeline
  `AURORA v1`, Wyoming chain Whisper + Piper +
  openWakeWord + HA Ollama integration).
- **Open WebUI voice + chat** —
  `https://ai.amarolab.es` (browser mic + OpenAI-
  API-compatible STT/TTS HTTP shims).

Voice → real Zigbee device round-trip proven through
Mosquitto + Z2M against the Sonoff S60ZBTPF plug;
failure-mode safety story complete; baseline restored
on every gate; Guardian Cloud untouched throughout.

Phase D-1 — Voice: **CLOSED.**

## Next

Phase RTX-1 (Torre GPU node) — local validation
complete; remote exposure (RTX-1.4) pending; node not
yet consumed by the UM790. Other pending post-D-1
follow-ups (documented in the closeout):

- RTX-1.4 — secure remote exposure (Tailscale-only)
  + UM790 endpoint swap (security delta doc required)
- STT model-size bump candidate
- Streaming TTS in Open WebUI
- System-prompt trim
- `cloudflared-amarolab` standalone apply log
- DNS / Cloudflare architecture doc amendments
- R-D-13 (Open WebUI STT HTTP shim migration)
- R-01 (Cloudflare Tunnel token rotation)
