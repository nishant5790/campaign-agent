const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto('http://localhost:8000');
  
  // Wait for the welcome message
  await page.waitForTimeout(1000);
  
  // Send 1st message
  await page.fill('#chatInput', 'I want to write a LinkedIn post about AI evaluation methods and best practices.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(5000);
  
  // Send 2nd message
  await page.fill('#chatInput', 'Target audience is AI engineers. Tone should be professional, focus on model interpretability.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(5000);

  // Send 3rd message
  await page.fill('#chatInput', 'My primary goal is establishing thought leadership. I lean towards professional engaging expert-level discussion with practical takeaways.');
  await page.click('#chatSendBtn');
  await page.waitForTimeout(10000);
  
  const cardCount = await page.evaluate(() => document.querySelectorAll('.plan-card').length);
  const statusEl = await page.evaluate(() => document.querySelector('.plan-card') ? document.querySelector('.plan-card').innerText : 'NO CARD');
  const chatHtml = await page.evaluate(() => document.querySelector('#chatMessages').innerHTML);
  
  require('fs').writeFileSync('ui_test_out.txt', `CARD_COUNT: ${cardCount}\nSTATUS: ${statusEl}\nHTML: ${chatHtml}`);
  console.log('Done');
  await browser.close();
})();
