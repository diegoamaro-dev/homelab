# Docker Environment Variables Reload Behavior

## Context

During Amarolab Phase C validation and Mosquitto hardening, Home Assistant authentication continued failing even after a new `HA_LLAT` token had been generated and written to `ai-stack/.env`.

The token appeared correct on disk, but Open WebUI kept using the previous value.

---

## Problem

After updating environment variables in `.env`, the following command was executed:

```bash
docker restart openwebui
```

The expectation was that the container would reload the updated environment variables.

This did not happen.

Authentication requests to Home Assistant continued using the old token and returned:

```txt
401 Unauthorized
```

---

## Root Cause

The Open WebUI container was originally created using:

```bash
docker run --env ...
```

Docker environment variables are loaded only when the container is created.

A container restart does **not** reload environment variables from `.env`.

The existing container continues using the values that were present during its creation.

---

## Verification

Comparison performed during troubleshooting:

### Host

```txt
HA_LLAT hash = c69e81f5
```

### Container

```txt
HA_LLAT hash = fd5b5c65
```

The hashes differed, proving that:

* `.env` had been updated correctly
* the container was still using the previous value

---

## Solution

The container must be recreated.

Restarting is insufficient.

Example:

```bash
docker rm -f openwebui

docker run ...
```

Or, when using Docker Compose:

```bash
docker compose up -d
```

after updating the environment configuration.

---

## Validation

After recreating the container:

* container environment matched disk configuration
* Home Assistant authentication succeeded
* `ha_get_state()` returned valid results
* Gate G-5 completed successfully
* Mosquitto hardening closeout was completed

---

## Operational Rule

**docker restart does not reload environment variables.**

When a container was created using environment variables and those values change:

1. Update the configuration file.
2. Recreate the container.
3. Validate that the new values are loaded.
4. Only then continue troubleshooting.

---

## Lessons Learned

Always verify:

* environment variable value on disk
* environment variable value inside the container

before assuming a service is using the updated configuration.

