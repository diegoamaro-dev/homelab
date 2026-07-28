# S-1 — LAN Trust Posture — Decision Record

**Date:** 2026-07-28
**Type:** Decision record. Operational remediation item, not a phase.
**Remediation item:** S-1 (Program C — security posture), from the 2026-07-28 infrastructure audit.
**Source finding:** H-8 — *No host firewall is enforcing; broad LAN service exposure.*
**Production changed:** **no.** Documentation and decision only. No service, binding, firewall rule or file outside the repository was touched.

> This is a dated record. It states what was decided and what was measured on 2026-07-28
> and is not rewritten as the situation advances (`PROJECT_RULES.md` → *Historical
> Documentation*). Corrections belong in later documents.

---

## 1. The decision

Ratified by the operator, 2026-07-28:

```text
The LAN is a trusted transport.
It is never a substitute for service authentication.
Every LAN-reachable service must either:
- authenticate,
- be explicitly justified,
- or remain closed.
```

Recorded in [`../06_security/security_posture.md`](../06_security/security_posture.md) →
*Network Security → Internal Network*, which is the authoritative statement of the posture.

### Why this and not the alternative

The audit offered two shapes: trust the LAN explicitly and fix only the unauthenticated
listeners, or stop trusting it and enforce default-deny.

Default-deny was rejected for now on three grounds, all measured rather than assumed:

1. **It would not achieve the closure it appears to.** Eight of the LAN-exposed ports are
   Docker-published; Docker's own `nat`/`DOCKER` rules mean `ufw enable` does not filter
   them. Closure requires re-binding publishes or `DOCKER-USER` rules — a different change
   with a different risk profile.
2. **It cannot be verified from here.** `iptables -S` and `nft list ruleset` both return
   permission denied without passwordless sudo, so neither this record nor the 2026-07-28
   audit has read the effective filter state. A control that cannot be verified should not
   be adopted as the primary control.
3. **It carries lockout risk** (SSH) and needs a maintenance window and operator hands
   throughout, which makes it a project rather than a decision.

The plain version of the decision — *"trust the LAN, fix H-5 and H-6"* — was also rejected,
because it leaves conforming and non-conforming listeners indistinguishable and re-opens
the argument at every future service. The **minimum bar** is what converts S-2…S-5 from
re-litigation into a checklist.

### What the decision is not

* It is **not** permission for a service to be unauthenticated.
* It is **not** segmentation. VLAN separation of user / IoT / server / guest devices is now
  a **decided non-goal at the current scale**, removed from the pending list rather than
  carried indefinitely. It returns only if the LAN stops being effectively single-user.
* It is **not** a trust-boundary change for compute. `PROJECT_RULES.md` →
  *Hardware-Agnostic Platform* rule 6 governs that axis and is untouched here.

---

## 2. Evidence — measured 2026-07-28

Read-only. Full conformance table in
[`../06_security/security_posture.md`](../06_security/security_posture.md); it is the live
record and is not duplicated here.

| Check | Result |
|---|---|
| `/etc/ufw/ufw.conf` | `ENABLED=no`; unit `active` + `enabled`, installs no rules — **H-8 reproduces** |
| `iptables -S` / `nft list ruleset` | permission denied — effective filter state **not readable** |
| Ollama `11434` | `HTTP 200` on `/api/tags` from `192.168.178.79` — **unauthenticated, H-5 live** |
| homelab-tools `5050` | answers, no auth challenge — **H-6 live** |
| Qdrant `6333` / WebDAV `8088` | `HTTP 401` — authentication enforced |
| SSH `22` | `PasswordAuthentication` unset in `sshd_config` + `sshd_config.d/` → OpenSSH default `yes` — **M-9 confirmed** |
| Mosquitto `1883` | authenticated + per-user ACLs, unchanged since 2026-06-17 |

Ten of fourteen LAN-reachable services meet the bar. Four do not.

---

## 3. Findings raised by this audit

Both are **new** — neither appears in the 2026-07-28 audit's H-8 table. Both are
**recorded and deliberately unimplemented**, on the **R-I3-1…7** precedent: S-1 decides the
posture and changes no running service.

**No remediation identifier has been assigned to either. That assignment is an operator
decision, deliberately not self-approved.**

### F-S1-1 — `rpcbind` is listening on the LAN with no NFS behind it

`111/tcp` and `111/udp`, IPv4 and IPv6, confirmed reachable from `192.168.178.79`. There is
no `/etc/exports` and `nfs-server` is `inactive`. It therefore fails the bar on all three
branches: it does not authenticate, has no written justification, and is not closed.
`rpcbind` is additionally a well-known UDP reflector. Candidate action: disable the socket
and unit, after confirming no consumer.

### F-S1-2 — one LAN-reachable listener cannot be attributed

`*:18555` (with a loopback sibling on `127.0.0.1:18554`) is confirmed open from the LAN.
The owning process cannot be identified without root. This is recorded as a finding in its
own right: **an inventory that cannot be fully attributed is a posture defect**, because the
bar cannot be applied to a service nobody can name. Candidate action: attribute it with
root, then apply the bar.

### Backup adjacency — recorded, not a finding

The sole restic repository and a LAN-writable Samba share share a filesystem, and the
repository's parent directory is owned by the SMB principal with no sticky bit. The
repository itself is `root`-owned at mode `0700`, and the `[projects]` share is path-scoped
with `wide links` unset, so **no access path is demonstrated**. Detail and the precise
limits of that claim are in `security_posture.md` → *Backup adjacency*. It is recorded
because it sets the stakes of the decision, not because it is exploitable today.

---

## 4. Validation

S-1 is a decision and a document. There is no production change to validate, so validation
is that every claim is a real measurement and that stated limits are stated in place.

| Check | Result |
|---|---|
| Every conformance-table row backed by a live observation | PASS |
| Unverifiable claims marked as such, next to the claim | PASS — filter state, Docker rule behaviour, `18555` attribution |
| Hypotheses separated from facts (`PROJECT_RULES.md` → *AI Assistant Behaviour*) | PASS — F-S1-1/F-S1-2 candidate actions are labelled candidates |
| Reality → document direction preserved | PASS — the document was changed to match measurement; nothing was changed to match the document |
| No production change | PASS — no service, binding, firewall rule or host file touched |
| Secrets | PASS — no tokens, keys or credentials; the LAN address `192.168.178.79` is already committed repo-wide and carried under the standing *Documentation Hygiene* IP-sanitization item |

---

## 5. Rollback

Documentation only. Rollback is `git revert` of the commit carrying this change; nothing
outside the repository was modified, so there is no operational state to restore.

Reverting restores the previous text (`Trusted LAN`, segmentation listed as pending) — but
it does **not** restore the previous *situation*, because the previous situation was that no
decision existed. Re-opening the question is the real undo.

---

## 6. Consequences

* **S-2, S-3, S-4, S-5 are unblocked.** Each becomes a conformance action against a written
  bar rather than a fresh argument about whether the LAN is trusted.
* **S-2 and S-3 gain a concrete definition of done:** the listener authenticates, is
  justified in writing, or is closed.
* **F-S1-1 and F-S1-2 need remediation identifiers** — operator decision, see §3.
* **Segmentation is closed as a pending item** and reopens only on a change of LAN
  population.
* **`ufw` remains off, now by decision rather than by accident.** If it is ever enabled, the
  Docker-publish caveat in §1 applies and must be verified with root.

---

## 7. Git gate

Documentation-only. **Not committed, not pushed** — each requires explicit operator
approval immediately before the command (`PROJECT_RULES.md` → *Operator Git Approval*).
No tag: tags in this repository mark phase closeouts, and S-1 is a remediation item.

**STOP at git gate.**
