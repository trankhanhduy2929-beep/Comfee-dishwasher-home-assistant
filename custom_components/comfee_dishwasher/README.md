# Comfee Dishwasher

Home Assistant custom integration for MSmartHome/Midea local protocol device
type `0xE1`.

- Cloud is used only during setup to obtain the LAN token/key.
- Normal polling and commands go directly to the appliance over the local
  network, normally TCP port `6444`.
- The MSmartHome account password is never stored in the config entry.
- Program selection and the start button are disabled by default because E1
  program selection can start a real wash cycle immediately.

Install and usage documentation is available in the repository root README:

`https://github.com/trankhanhduy2929-beep/Comfee-dishwasher-home-assistant`

Do not configure the same appliance in both this integration and Home
Assistant's built-in Midea integration.
