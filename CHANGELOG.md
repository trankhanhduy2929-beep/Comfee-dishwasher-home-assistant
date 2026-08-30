# Changelog

## 0.4.0 — 2026-08-29

- Keep one daemonized `midea-local` service thread as the only socket reader.
- Apply unsolicited LAN messages to all Home Assistant entities automatically.
- Coalesce callback bursts before notifying entities to reduce recorder and
  event-loop load.
- Keep the library's 30-second local query as a low-cost fallback for firmware
  that does not emit every state change.
- Run connect, refresh, reconnect, commands and teardown outside Home
  Assistant's event loop.
- Mark normal entities unavailable from the cached LAN state while leaving
  refresh, reconnect and connectivity diagnostics accessible.

## 0.3.0 — 2026-08-29

- Expose the remaining E1 read-only states: UV, drying, water inlet, option
  codes and operation warnings.
- Add derived error, operation-warning and local-LAN connectivity sensors.
- Add local-only refresh and reconnect buttons.
- Add redacted Home Assistant diagnostics.
- Translate entity names, program states and control errors into Vietnamese.
- Add entity icons and keep program controls disabled by default.

## 0.2.0 — 2026-08-29

- First public HACS release.
- Add MSmartHome-assisted setup that stores only LAN credentials.
- Add local polling and control for Comfee/Midea dishwasher type `0xE1`.
- Add status, diagnostic, switch, program select and start entities.
- Keep program select and start disabled by default for safety.
- Add bundled official Comfee brand icon and logo.
