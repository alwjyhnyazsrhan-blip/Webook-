/**
 * index.js
 * نموذج أتمتة الويب وإدارة الجلسات باستخدام Puppeteer
 * يوضح كيفية تسجيل الدخول التجريبي، استخراج ملفات الكوكيز، وحفظها وإعادة استخدامها.
 */

const puppeteer = require('puppeteer');
const { saveSessionCookies, loadSessionCookies } = require('./sessionManager');

// إعدادات بيئة الاختبار التجريبية العامة
const CONFIG = {
  loginUrl: 'https://the-internet.herokuapp.com/login',
  secureUrl: 'https://the-internet.herokuapp.com/secure',
  username: 'tomsmith',
  password: 'SuperSecretPassword!',
  accountIdentifier: 'user_dev_01',
};

async function executeAutomation() {
  console.log('====================================================');
  console.log('[RUNNER] بدء تشغيل جلسة فحص واستخراج الجلسات...');
  console.log('====================================================');

  let browser = null;

  try {
    // 1. تشغيل المتصفح
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(25000);

    // 2. التحقق من وجود جلسة سابقة صالحة
    const existingCookies = loadSessionCookies(CONFIG.accountIdentifier);
    let sessionRestored = false;

    if (existingCookies && existingCookies.length > 0) {
      console.log('[AUTH] جاري تطبيق الكوكيز السابقة على الصفحة...');
      await page.setCookie(...existingCookies);

      console.log('[AUTH] محاولة التحقق من صلاحية الجلسة عبر زيارة الصفحة المحمية مباشرة...');
      await page.goto(CONFIG.secureUrl, { waitUntil: 'networkidle2' });

      // التحقق من النجاح
      if (page.url().includes('/secure')) {
        console.log('[AUTH SUCCESS] الجلسة المخزنة صالحة تماماً! تم تخطي إدخال البيانات.');
        sessionRestored = true;
      } else {
        console.log('[AUTH NOTICE] الجلسة المخزنة منتهية الصلاحية. جاري الانتقال لتسجيل الدخول مجدداً.');
      }
    }

    // 3. في حال عدم وجود جلسة صالحة، نبدأ تدفق تسجيل الدخول
    if (!sessionRestored) {
      console.log(`[LOGIN] الانتقال إلى صفحة تسجيل الدخول: ${CONFIG.loginUrl}`);
      await page.goto(CONFIG.loginUrl, { waitUntil: 'networkidle2' });

      const usernameField = '#username';
      const passwordField = '#password';
      const submitButton = 'button[type="submit"]';

      await page.waitForSelector(usernameField, { timeout: 10000 });

      console.log('[LOGIN] إدخال بيانات الاعتماد...');
      await page.type(usernameField, CONFIG.username, { delay: 30 });
      await page.type(passwordField, CONFIG.password, { delay: 30 });

      console.log('[LOGIN] إرسال النموذج وانتظار التحويل...');
      await Promise.all([
        page.click(submitButton),
        page.waitForNavigation({ waitUntil: 'networkidle2' }),
      ]);

      // 4. التحقق من نجاح العملية
      const currentUrl = page.url();
      if (currentUrl.includes('/secure')) {
        console.log('[LOGIN SUCCESS] تم تسجيل الدخول بنجاح والوصول للمنطقة المحمية.');

        // 5. استخراج الكوكيز وتخزينها
        const sessionCookies = await page.cookies();
        console.log(`[COOKIES] تم استخراج ${sessionCookies.length} كوكيز من الجلسة الحالية.`);

        sessionCookies.forEach((c) => {
          console.log(`  - Cookie: ${c.name} | Domain: ${c.domain} | Secure: ${c.secure}`);
        });

        // حفظ الكوكيز لإعادة استخدامها
        saveSessionCookies(sessionCookies, CONFIG.accountIdentifier);
      } else {
        const errorAlert = await page.$('.flash.error');
        let errorMsg = 'فشل تسجيل الدخول لسبب غير معروف';
        if (errorAlert) {
          errorMsg = await page.evaluate((el) => el.innerText.trim(), errorAlert);
        }
        throw new Error(`تعذر تسجيل الدخول: ${errorMsg}`);
      }
    }

    console.log('====================================================');
    console.log('[COMPLETED] تم الانتهاء من فحص الجلسة وإدارتها بنجاح.');
    console.log('====================================================');
  } catch (error) {
    console.error(`[EXECUTION ERROR] حدث خطأ أثناء تنفيذ التدفق: ${error.message}`);
  } finally {
    if (browser) {
      await browser.close();
      console.log('[CLEANUP] تم إغلاق المتصفح.');
    }
  }
}

// تنفيذ العملية
executeAutomation();
