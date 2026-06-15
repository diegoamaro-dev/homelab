# 01 — Hardware

## Chassis / board

| Field | Value |
|-------|-------|
| Vendor | Micro Computer (HK) Tech Limited |
| Model | Venus series (Minisforum) |
| Chassis | Desktop (mini-PC) |
| Machine ID | `<REDACTED-MACHINE-ID>` |
| Firmware (BIOS) | 1.09 — built 2023-11-20 (~2 y 7 mo old) |

> `dmidecode` requires root and was not run; vendor/model/firmware values come
> from `hostnamectl`.

## CPU

| Field | Value |
|-------|-------|
| Model | AMD Ryzen 9 7940HS w/ Radeon 780M Graphics |
| Architecture | x86_64 (AMD Zen 4, family 25 model 116) |
| Cores / threads | 8 cores / 16 threads (1 socket, SMT on) |
| Max boost | 5263 MHz |
| Min freq | 403 MHz |
| Cache | L1d 256 KiB · L1i 256 KiB · L2 8 MiB · L3 16 MiB |
| Virtualization | AMD-V enabled |
| NUMA | Single node, CPUs 0–15 |

Notable instruction-set support: AVX-512 (`avx512f`, `avx512vnni`, `avx512_bf16`),
`sha_ni`, `aes`. Speculative-execution mitigations report "Not affected" for
Gather Data Sampling, Ghostwrite, and Indirect Target Selection.

## GPU

| Field | Value |
|-------|-------|
| Adapter | AMD Radeon 780M — Phoenix1 (integrated, rev c1, PCI `c4:00.0`) |
| Discrete GPU | None |

The Ollama container has `NVIDIA_VISIBLE_DEVICES=all` set, but the host has
**no NVIDIA hardware**. LLM inference is CPU-only, which matches the observed
`docker stats` numbers (Ollama idling at 0% CPU with ~120 MiB RSS, no model
currently loaded — `/api/ps` returns `{"models":[]}`).

## Memory

| Field | Value |
|-------|-------|
| Total RAM | 29 GiB (`MemTotal` 30 573 444 kB) |
| Used | 6.0 GiB |
| Available | 23 GiB |
| Cached | 9.7 GiB |
| Swap | 8.0 GiB (file `/swap.img`, 0 B used) |

## Storage devices

| Device | Size | Type | Notes |
|--------|------|------|-------|
| `/dev/nvme0n1` | 476.9 GB | NVMe SSD | Boot disk |
| ├── `nvme0n1p1` | 1 GB | vfat | `/boot/efi` (UUID `A0FE-2591`) |
| └── `nvme0n1p2` | 475.9 GB | ext4 | `/` (UUID `1bf79dc1-…cf789`) |
| `/dev/sda` | 1.8 TB | SATA HDD | Bulk storage |
| └── `sda1` | 1.8 TB | ext4 | `/mnt/storage` (UUID `2a351e9b-…27b08`) |

`smartctl` requires root and was not run, so wear levels and reallocated
sectors are unknown.

## Network interfaces

| Interface | Driver / chip | State | Address(es) |
|-----------|---------------|-------|-------------|
| `enp1s0` | Realtek RTL8125 2.5 GbE | UP | `192.168.178.79/24`, IPv6 ULAs |
| `wlp2s0` | MediaTek MT7922 (Wi-Fi 6E) | DOWN | — |
| `tailscale0` | Tailscale userspace | UNKNOWN | `100.68.180.69/32`, `fd7a:…:b4ab/128` |
| `lo` | loopback | UP | `127.0.0.1/8`, `::1` |

Plus a large set of `br-*` and `veth*` bridges created by Docker (see
[04-docker-networks.md](04-docker-networks.md)).

## Peripherals

- **Zigbee coordinator:** ITead Sonoff Zigbee 3.0 USB Dongle Plus
  (`usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_36eae92b…-if00-port0`),
  mapped into the `zigbee2mqtt` container as `/dev/ttyUSB0`.
- Bluetooth radio active (`bluetoothd` running, several HOG / HID errors in
  the journal from a previously-paired peripheral).

## Power / thermals

CPU scaling factor: 90 %. `power-profiles-daemon` and `upower` running. No
temperature sensors collected (would need `lm-sensors`).
