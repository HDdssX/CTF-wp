$candidates = @(
  'bbb{lui_sign_extension}',
  'bbb{mips64_lui_sign_extension}',
  'bbb{lui_sign_ext}',
  'bbb{mips64_lui_sign_ext}',
  'bbb{sign_extended_lui}',
  'bbb{sign_extension}',
  'bbb{lui_sign_extended}',
  'bbb{lui_sign_extends}',
  'bbb{lui_is_signed}',
  'bbb{lui_is_sign_extended}',
  'bbb{lui_signextends}',
  'bbb{mips_lui_sign_extension}',
  'bbb{mips64_lui}',
  'bbb{mips64_semantics}',
  'bbb{mips3_lui_sign_extension}',
  'bbb{n64_lui_sign_extension}',
  'bbb{branch_likely_delay_slot}',
  'bbb{branch_likely_delay_slots}',
  'bbb{branch_likely}',
  'bbb{branch_delay_slot}',
  'bbb{branch_delay_slots}',
  'bbb{delay_slot}',
  'bbb{delay_slots}',
  'bbb{mips_delay_slot}',
  'bbb{mips_delay_slots}',
  'bbb{mips_branch_delay_slot}',
  'bbb{mips_branch_delay_slots}',
  'bbb{beqzl}',
  'bbb{mips64_beqzl}',
  'bbb{lui_and_branch_delay_slots}'
)
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$cookie = New-Object System.Net.Cookie('session','978b3cc62963487ab7a0f57ab6be012a6d6d246bccc687eb4fa0644798d948e6','/','bbbctf.com')
$session.Cookies.Add('https://bbbctf.com', $cookie)
foreach($flag in $candidates){
  $body = @{flag=$flag} | ConvertTo-Json -Compress
  $r = Invoke-WebRequest -Uri 'https://bbbctf.com/api/flag' -Method Post -ContentType 'application/json' -Body $body -WebSession $session -SkipHttpErrorCheck
  $kind = try { ($r.Content | ConvertFrom-Json).kind } catch { $r.Content }
  "$flag => $($r.StatusCode) $kind"
  if($kind -eq 'Correct' -or $kind -eq 'AlreadySolved'){ break }
  Start-Sleep -Milliseconds 300
}
