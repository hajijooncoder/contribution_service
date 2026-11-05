import { test, expect } from '@playwright/test';

test.describe('MAHOUNN Legal Contribution Platform E2E Suite', () => {
  test('landing page renders Lovable design, 5-step pipeline, and 8 pillars', async ({ page }) => {
    await page.goto('/');

    // Check title and hero
    await expect(page).toHaveTitle(/MAHOUNN|پلتفرم مشارکت/);
    await expect(page.locator('text=عدالت تنها یک هدف نیست...')).toBeVisible();
    await expect(page.locator('text=پلتفرم توسعه گراف دانش حقوقی ایران با مشارکت حقوقدانان، وکلای دادگستری، دانشجویان حقوق و کلیه متخصصین حقوقی و قضایی ایران...')).toBeVisible();

    // Check 5-step pipeline
    await expect(page.locator('text=منبع')).toBeVisible();
    await expect(page.locator('text=متن')).toBeVisible();
    await expect(page.locator('text=ثبت')).toBeVisible();
    await expect(page.locator('text=بررسی')).toBeVisible();
    await expect(page.locator('text=اعتبار مشارکت')).toBeVisible();

    // Check Proof of Contribution section
    await expect(page.locator('text=مشارکت شما فقط یک ادعا نیست.')).toBeVisible();
    await expect(page.locator('text=مشارکت مطلقاً به معنای دسترسی مستقیم به پایگاه داده نیست.')).toBeVisible();

    // Check 8-pillar scoring cards
    await expect(page.locator('text=اعتبار منبع')).toBeVisible();
    await expect(page.locator('text=سازگاری با Knowledge Graph')).toBeVisible();
    await expect(page.locator('text=مشارکت بیشتر الزاماً به معنای اعتبار بیشتر نیست؛ مشارکت معتبر و مفید ارزشمند است.')).toBeVisible();

    // Check footer trust mantra
    await expect(page.locator('text=اعتماد · شفافیت · مشارکت · تأیید · اثر')).toBeVisible();
  });

  test('user can open and close the login modal', async ({ page }) => {
    await page.goto('/');

    const loginButton = page.locator('button:has-text("ورود / ثبت‌نام")').first();
    await loginButton.click();

    // Check modal visibility
    await expect(page.locator('text=ورود به پلتفرم')).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();

    // Close modal
    const closeBtn = page.locator('button:has-text("انصراف")');
    await closeBtn.click();
    await expect(page.locator('text=ورود به پلتفرم')).not.toBeVisible();
  });

  test('submission form enforces real-time URL validation and character limits', async ({ page }) => {
    await page.goto('/');

    // Navigate to submit tab
    await page.click('button:has-text("ارسال مشارکت")');

    // Fill valid official gazette URL
    const urlInput = page.locator('input[type="url"]');
    await urlInput.fill('https://rrk.ir/laws/show/10001');

    // Wait for debounced validation badge
    await expect(page.locator('text=مرجع رسمی تایید شد:')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=روزنامه رسمی جمهوری اسلامی ایران')).toBeVisible();

    // Test text length counter & warning
    const textArea = page.locator('textarea');
    await textArea.fill('کوتاه');
    await expect(page.locator('text=متن حقوقی باید حداقل ۲۰ نویسه داشته باشد.')).toBeVisible();

    // Test air-gap notice
    await expect(page.locator('text=مشارکت مطلقاً به معنای دسترسی مستقیم به پایگاه داده نیست:')).toBeVisible();
  });

  test('contributor table displays audit trail with provenance modal', async ({ page }) => {
    await page.goto('/');

    // Check table headers
    await expect(page.locator('text=اثر مشارکت، روشن و قابل پیگیری.')).toBeVisible();
    await expect(page.locator('th:has-text("شناسه")')).toBeVisible();
    await expect(page.locator('th:has-text("دانش افزوده")')).toBeVisible();

    // Click "مشاهده سند" button to open audit modal
    const viewDocBtn = page.locator('button:has-text("مشاهده سند")').first();
    await viewDocBtn.click();

    // Check modal content
    await expect(page.locator('text=سابقه قابل بررسی مشارکت')).toBeVisible();
    await expect(page.locator('text=وضعیت در گراف دانش')).toBeVisible();

    // Close audit modal
    await page.click('button:has-text("بستن")');
    await expect(page.locator('text=سابقه قابل بررسی مشارکت')).not.toBeVisible();
  });
});
