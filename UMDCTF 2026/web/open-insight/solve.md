Flag: `UMDCTF{r0ll_y0ur_0wn_s4nit1zat1on}`

Status: submitted successfully.

Exploit summary:
- The sheet runtime evaluates formulas with `Function(... with(S) ...)`.
- `document` is proxy-wrapped, but `document.all` escapes the proxy because `typeof document.all === "undefined"` in browsers.
- From `document.all[0].ownerDocument.defaultView`, the payload used:
  - synchronous `XMLHttpRequest` to fetch `/admin`
  - regex extraction of `UMDCTF{...}`
  - `navigator.sendBeacon()` to exfiltrate the result to a temporary `ntfy.sh` topic
- Workflow used:
  - create account
  - create workbook
  - call the `saveSheetAction` server action directly to store the malicious formula
  - submit the workbook id to `open-insight-bot`
  - poll the `ntfy.sh` topic for the admin-side flag
