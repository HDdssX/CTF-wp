Flag: `UMDCTF{cr1m3_p4ys_br34ch_m0re}`

Status: submitted successfully.

Exploit summary:
- The service on `challs.umdctf.io:31337` drops into an internal shell on `10.0.0.3`.
- From that shell, `arpspoof` + `tcpkill` + a fake HTTPS listener were enough to MITM the admin browser on `10.0.0.1`.
- The browser posted valid admin credentials to the fake `/login` endpoint:
  - user: `admin`
  - pass: `mkQH5DypUvbjGZK0aa44Fo1yhSPZdh25`
- Logging into the real server at `https://10.0.0.2` with those credentials exposed the dashboard flag.
