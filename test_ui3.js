const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('response', async res => {
    if (res.url().includes('/api/chat')) {
      const json = await res.json();
      console.log('API /api/chat RESPONSE:', JSON.stringify(json, null, 2));
    }
  });

  await page.goto('http://localhost:8000');
  
  await page.waitForTimeout(1000);
  
  await page.fill('#chatInput', 'I want to write a LinkedIn post about AI evaluation methods and best practices.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(5000);
  
  await page.fill('#chatInput', 'Target audience is AI engineers. Tone should be professional, focus on model interpretability.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(5000);

  await page.fill('#chatInput', 'My primary goal is establishing thought leadership. I lean towards professional engaging expert-level discussion with practical takeaways.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();
