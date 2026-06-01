const session = '978b3cc62963487ab7a0f57ab6be012a6d6d246bccc687eb4fa0644798d948e6';
const candidates = [
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
  'bbb{lui_and_branch_delay_slots}',
  'bbb{lui_branch_delay_slot}',
  'bbb{lui_branch_likely}',
  'bbb{lui_branch_likely_delay_slot}',
];
async function post(flag) {
  const r = await fetch('https://bbbctf.com/api/flag', {
    method: 'POST',
    headers: {'Content-Type':'application/json', 'Cookie': `session=${session}`},
    body: JSON.stringify({flag}),
  });
  const text = await r.text();
  let obj;
  try { obj = JSON.parse(text); } catch { obj = {raw:text}; }
  return {status:r.status, obj, text};
}
(async()=>{
  const self = await fetch('https://bbbctf.com/api/team/self', {headers:{Cookie:`session=${session}`}});
  console.log('self', self.status, (await self.text()).slice(0,200));
  for (const flag of candidates) {
    const res = await post(flag);
    const kind = res.obj.kind || res.obj.message || res.text;
    console.log(`${flag} => ${res.status} ${kind}`);
    if (res.obj.kind === 'Correct' || res.obj.kind === 'AlreadySolved') {
      console.log('FOUND ' + flag);
      process.exit(0);
    }
    await new Promise(r => setTimeout(r, 300));
  }
  process.exit(2);
})().catch(e => { console.error(e); process.exit(1); });
