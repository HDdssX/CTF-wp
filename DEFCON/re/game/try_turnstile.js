const { chromium } = require('./pw_tmp/node_modules/playwright-core');
(async () => {
  const browser = await chromium.launch({
    headless: false,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--disable-blink-features=AutomationControlled']
  });
  const page = await browser.newPage();
  await page.goto('https://bbbctf.com/register', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('text=Team Registration', { timeout: 30000 });
  const user = 'codex' + Math.random().toString(36).slice(2,10);
  const pass = 'Pw_' + Math.random().toString(36).slice(2) + 'A1!';
  await page.getByLabel('Team name').fill(user);
  await page.getByLabel('Username').fill(user);
  await page.getByLabel('Password').fill(pass);
  await page.getByLabel('Contact email').fill(user + '@example.com');
  console.log('filled user=' + user + ' pass=' + pass);
  let token = '';
  for (let i = 0; i < 90; i++) {
    token = await page.evaluate(() => {
      const t = document.querySelector('input[name="cf-turnstile-response"]');
      return t ? t.value : '';
    }).catch(() => '');
    if (token) break;
    await page.waitForTimeout(1000);
  }
  console.log('token length=' + (token ? token.length : 0));
  if (token) {
    const enabled = await page.getByRole('button', { name: 'Register' }).isEnabled().catch(e => false);
    console.log('register enabled=' + enabled);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
