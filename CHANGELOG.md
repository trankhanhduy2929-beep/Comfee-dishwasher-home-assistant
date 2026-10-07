# Changelog

## 0.7.0 — 2026-10-06

- Fix the Hassfest failure reported for `5b64875`: require `midea-local>=11.0.1`
  instead of pinning `midea-local==10.1.0`. Home Assistant now ships an
  official `midea` integration that depends on the same library
  (`11.0.1` on master, `12.2.0` on dev), so an exact pin was rejected as
  incompatible and would have downgraded core's copy.
- Re-verify all 36 appliance drivers, the E1 attribute table and the whole test
  suite against both `midea-local` 11.0.1 and 12.2.0; the local control surface
  is unchanged.
- Add **OS Comfort** and **Toshiba Iolife** to the app/cloud selector, matching
  the clouds supported by the current library.
- Map every cloud API failure to its own Vietnamese/English message: expired
  session, locked account, too many logged-in devices, device registered in
  another account, wrong app selection and a generic retry fallback, instead of
  one opaque "setup failed".
- Document that Home Assistant now ships an official `midea` integration and
  that an appliance must never be configured in both at the same time.
- Add contract tests that keep the requirement free of an exact pin, accept
  every version Home Assistant pins, and prove each library cloud error code
  resolves to a translated setup message.

## 0.6.0 — 2026-09-04

- Expand discovery and local state support from E1 dishwashers to all 36
  appliance drivers shipped by `midea-local 10.1.0`.
- Add generic Vietnamese sensor and binary-sensor entities for air
  conditioners, laundry appliances, refrigerators, fans, air/water treatment,
  water heaters, cooking appliances, robot vacuums and other supported types.
- Add conservative per-device-type switch allow-lists; unfamiliar controls are
  disabled by default and no command is sent during setup or validation.
- Add account setup for SmartHome/MSmartHome, NetHome Plus, Midea Air, Ariston
  Clima and Midea Meiju, while continuing to store only LAN credentials.
- Preserve the existing `comfee_dishwasher` domain and all verified E1 entities,
  usage estimates and safety guards.
- Keep E1-only program/start/usage behavior away from sink dishwasher type
  `0x34` and every non-E1 device.
- Improve brand detection from textual cloud/device metadata without guessing
  unstable manufacturer codes, including Arctic King metadata, without letting
  the selected cloud/app name override the appliance's actual brand; preserve
  valid explicit OEM brand names even when they are not yet in the alias table.
- Upgrade `midea-local` to `10.1.0` for current reconnect and protocol fixes.
- Add multi-device contract tests and retain the flat HACS release ZIP layout.

## 0.5.1 — 2026-09-04

- Fix the HACS release ZIP layout so files are extracted directly into
  `/config/custom_components/comfee_dishwasher` instead of creating a second
  nested `comfee_dishwasher` directory.
- Add an archive installation test that reproduces the HACS extraction target
  and rejects nested component layouts.
- Correct the manual installation instructions for the flat HACS archive.

## 0.5.0 — 2026-09-04

- Add estimated energy and water sensors for the last completed cycle, today
  and the current month.
- Count a cycle once on the local E1 `complete` transition and ignore cancel
  and error states.
- Persist usage totals across Home Assistant restarts and reset daily/monthly
  totals in the Home Assistant local timezone.
- Clearly mark values as fixed-program estimates because this E1 firmware does
  not expose an actual energy or water meter.

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
