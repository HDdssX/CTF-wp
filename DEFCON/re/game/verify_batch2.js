const session = '978b3cc62963487ab7a0f57ab6be012a6d6d246bccc687eb4fa0644798d948e6';
const candidates = [
'bbb{lui_sign_extends}',
'bbb{lui_sign_extends_on_mips64}',
'bbb{lui_sign_extends_on_mips}',
'bbb{lui_sign_extends_on_n64}',
'bbb{lui_sign_extends_to_64_bits}',
'bbb{lui_sign_extends_to_64_bit}',
'bbb{lui_sign_extends_64_bits}',
'bbb{lui_sign_extends_64_bit}',
'bbb{lui_sign_extension_to_64_bits}',
'bbb{lui_sign_extension_to_64_bit}',
'bbb{lui_sign_extension_on_mips64}',
'bbb{lui_sign_extension_on_n64}',
'bbb{mips64_lui_sign_extends}',
'bbb{mips_lui_sign_extends}',
'bbb{n64_lui_sign_extends}',
'bbb{mips64_lui_sign_extends_to_64_bits}',
'bbb{lui_is_sign_extended_on_mips64}',
'bbb{lui_is_sign_extended_on_n64}',
'bbb{lui_gets_sign_extended}',
'bbb{lui_gets_sign_extended_to_64_bits}',
'bbb{lui_sign_extension_is_weird}',
'bbb{mips64_lui_is_weird}',
'bbb{lui_is_weird_on_mips64}',
'bbb{lui_sign_extends_to_64}',
'bbb{lui_sign_extension_to_64}',
'bbb{sign_extend_lui}',
'bbb{sign_extend_lui_on_mips64}',
'bbb{sign_extend_lui_to_64_bits}',
'bbb{sign_extend_lui_to_64}',
'bbb{lui_sign_extend}',
'bbb{lui_sign_extend_64}',
'bbb{lui_sign_extend_64_bits}',
'bbb{mips64_lui_sign_extend}',
'bbb{n64_lui_sign_extend}',
'bbb{lui_64_bit_sign_extension}',
'bbb{64_bit_lui_sign_extension}',
'bbb{lui_64bit_sign_extension}',
'bbb{64bit_lui_sign_extension}',
'bbb{lui_is_64_bit}',
'bbb{mips64_lui_is_signed}',
'bbb{mips64_lui_is_sign_extended}',
'bbb{n64_lui_is_sign_extended}',
'bbb{n64_lui_is_signed}',
'bbb{mips64_sign_extension}',
'bbb{n64_sign_extension}',
'bbb{sign_extension_on_mips64}',
'bbb{sign_extension_on_n64}',
'bbb{lui_sets_the_upper_immediate}',
'bbb{load_upper_immediate}',
'bbb{load_upper_immediate_sign_extends}',
'bbb{load_upper_immediate_sign_extension}',
];
async function post(flag) {
  const r = await fetch('https://bbbctf.com/api/flag', {method:'POST',headers:{'Content-Type':'application/json',Cookie:`session=${session}`},body:JSON.stringify({flag})});
  const obj = await r.json().catch(async()=>({raw: await r.text()}));
  return {status:r.status,obj};
}
(async()=>{
 for (const flag of candidates) {
  const {status,obj}=await post(flag); const kind=obj.kind||obj.message||JSON.stringify(obj);
  console.log(`${flag} => ${status} ${kind}`);
  if(obj.kind==='Correct'||obj.kind==='AlreadySolved'){ console.log('FOUND '+flag); process.exit(0); }
  await new Promise(r=>setTimeout(r,250));
 }
 process.exit(2);
})().catch(e=>{console.error(e);process.exit(1)});
