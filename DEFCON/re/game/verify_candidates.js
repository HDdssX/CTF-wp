const { chromium } = require('./pw_tmp/node_modules/playwright-core');
const candidates = [
  'bbb{lui_sign_extension}',
  'bbb{mips64_lui_sign_extension}',
  'bbb{lui_sign_ext}',
  'bbb{mips64_lui_sign_ext}',
  'bbb{sign_extended_lui}',
  'bbb{lui_is_signed}',
  'bbb{branch_likely_delay_slot}',
  'bbb{branch_delay_slot}',
  'bbb{delay_slot}',
  'bbb{mips64_semantics}',
  'bbb{accurate_emulation}',
  'bbb{ares_emulator}',
  'bbb{taste7}',
  'bbb{taste_7}',
];
(async () => {
  const browser = await chromium.launch({
    headless: false,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--disable-blink-features=AutomationControlled']
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('https://bbbctf.com/register', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('text=Team Registration', { timeout: 30000 });
  const user = 'codex' + Math.random().toString(36).slice(2,10);
  const pass = 'Pw_' + Math.random().toString(36).slice(2) + 'A1!';
  await page.getByLabel('Team name').fill(user);
  await page.getByLabel('Username').fill(user);
  await page.getByLabel('Password').fill(pass);
  await page.getByLabel('Contact email').fill(user + '@example.com');
  let token = '';
  for (let i = 0; i < 90; i++) {
    token = await page.evaluate(() => document.querySelector('input[name="cf-turnstile-response"]')?.value || '');
    if (token) break;
    await page.waitForTimeout(1000);
  }
  if (!token) throw new Error('no turnstile token');
  console.log('registering user=' + user);
  const reg = await page.evaluate(async ({user, pass, token}) => {
    const r = await fetch('/api/team/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name:user, username:user, password:pass, email:user+'@example.com', aiPolicy:'HumanLedAi', captcha:token})
    });
    return {status:r.status, text:await r.text()};
  }, {user, pass, token});
  console.log('register status=' + reg.status + ' body=' + reg.text.slice(0,500));
  const self = await page.evaluate(async () => {
    const r = await fetch('/api/team/self');
    return {status:r.status, text:await r.text()};
  });
  console.log('self status=' + self.status + ' body=' + self.text.slice(0,500));
  if (self.status !== 200) throw new Error('not logged in');
  for (const flag of candidates) {
    const res = await page.evaluate(async (flag) => {
      const r = await fetch('/api/flag', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({flag})});
      return {status:r.status, text:await r.text()};
    }, flag);
    console.log(flag + ' => status=' + res.status + ' body=' + res.text.slice(0,500));
    if (/Correct|AlreadySolved/i.test(res.text) || res.status === 200 && !/Incorrect/i.test(res.text)) {
      console.log('FOUND ' + flag);
      break;
    }
    await page.waitForTimeout(500);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
