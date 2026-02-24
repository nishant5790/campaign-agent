const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));

  await page.goto('http://localhost:8000');
  
  // Wait for the welcome message
  await page.waitForTimeout(1000);
  
  // Send 1st message
  await page.fill('#chatInput', 'I want to write a LinkedIn post about AI evaluation methods and best practices.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(10000);
  
  // Send 2nd message
  await page.fill('#chatInput', 'Target audience is AI engineers. Tone should be professional, focus on model interpretability.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(10000);

  // Send 3rd message
  await page.fill('#chatInput', 'My primary goal is establishing thought leadership. I lean towards professional engaging expert-level discussion with practical takeaways.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(15000);
  
  const html = await page.content();
  if (html.includes('Content Plan')) {
    console.log('SUCCESS: Content Plan found in HTML');
  } else {
    console.log('FAIL: Content Plan NOT found in HTML');
  }

  await browser.close();
})();
