/**
 * sessionManager.js
 * وحدة مساعدة لإدارة وحفظ واسترجاع ملفات تعريف الارتباط (Cookies)
 * لتطبيقات واختبارات الأتمتة باستخدام Puppeteer.
 */

const fs = require('fs');
const path = require('path');

const STORAGE_FILE = path.join(__dirname, 'session-store.json');

/**
 * حفظ ملفات تعريف الارتباط في ملف محلي
 * @param {Array} cookies قائمة الكوكيز المستخرجة من الصفحة
 * @param {string} accountKey معرف الحساب أو الجلسة
 */
function saveSessionCookies(cookies, accountKey = 'default') {
  try {
    let store = {};
    if (fs.existsSync(STORAGE_FILE)) {
      const rawData = fs.readFileSync(STORAGE_FILE, 'utf8');
      store = rawData ? JSON.parse(rawData) : {};
    }

    store[accountKey] = {
      updatedAt: new Date().toISOString(),
      cookiesCount: cookies.length,
      cookies: cookies,
    };

    fs.writeFileSync(STORAGE_FILE, JSON.stringify(store, null, 2), 'utf8');
    console.log(`[STORAGE] ✓ تم حفظ الجلسة بنجاح للحساب [${accountKey}] (${cookies.length} كوكيز).`);
  } catch (error) {
    console.error(`[STORAGE ERROR] فشل حفظ الجلسة: ${error.message}`);
  }
}

/**
 * استرجاع ملفات تعريف الارتباط المخزنة
 * @param {string} accountKey معرف الحساب
 * @returns {Array|null} قائمة الكوكيز أو null إن لم توجد
 */
function loadSessionCookies(accountKey = 'default') {
  try {
    if (!fs.existsSync(STORAGE_FILE)) {
      return null;
    }

    const rawData = fs.readFileSync(STORAGE_FILE, 'utf8');
    const store = JSON.parse(rawData);

    if (store[accountKey] && Array.isArray(store[accountKey].cookies)) {
      console.log(`[STORAGE] ✓ تم استرجاع جلسة سابقة للحساب [${accountKey}] (تاريخ التحديث: ${store[accountKey].updatedAt}).`);
      return store[accountKey].cookies;
    }
  } catch (error) {
    console.warn(`[STORAGE WARN] تعذر قراءة الجلسة المخزنة: ${error.message}`);
  }
  return null;
}

module.exports = {
  saveSessionCookies,
  loadSessionCookies,
};
