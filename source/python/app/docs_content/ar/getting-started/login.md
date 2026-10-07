---
title: تسجيل الدخول والمصادقة
description: سجّل الدخول برمز Bearer أو مفتاح API، أو اعمل مفتوحًا في التطوير المحلي.
category: البدء
order: 10
slug: getting-started/login
language: ar
shots: [01-login.png]
---

# تسجيل الدخول والمصادقة

> سجّل الدخول برمز Bearer أو مفتاح API، أو اعمل مفتوحًا في التطوير المحلي.

## كيف يعمل الدخول

وضعان:

- **التطوير (افتراضي):** مفتوح. بدون `REQUIRE_AUTH` تعمل الواجهة وAPI بلا بيانات.
- **الإنتاج:** اضبط `REQUIRE_AUTH=1`. كل مسار `/api/v1/*` يتطلب **رمز Bearer** (من تسجيل الدخول) أو **X-API-Key** (محدد النطاق ومنتهي الصلاحية وقابل للإلغاء).

## الدخول من الواجهة

1. افتح التطبيق وانقر **Login** في تذييل الشريط الجانبي.
2. أدخل البريد وكلمة المرور. الرمز يُحفظ في الذاكرة فقط — أبدًا في localStorage.
3. شارة المستخدم تتغير من `anonymous` إلى `● signed in`.

![تسجيل الدخول](shot:01-login.png)

### ما الذي تتحقق منه

- بعد الدخول، الصفحات المحمية تعمل دون 401.
- **خطأ شائع:** وضع مفتاح API (`wi_…`) في حقل كلمة المرور. المفاتيح تُوضع في صندوق الرمز أو ترويسة `X-API-Key`.

## الدخول من API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"YOUR_PASSWORD"}'
```

```python
import httpx
r = httpx.post("http://127.0.0.1:8000/api/v1/auth/login",
               json={"email": "admin@local", "password": "YOUR_PASSWORD"})
headers = {"Authorization": f"Bearer {r.json()['token']}"}
```

## ماذا يحدث

- البيانات الصحيحة تُرجع رمزًا وتسجل حدث تدقيق.
- البيانات الخاطئة تُرجع `401 bad credentials` مع تدقيق للفشل.
- الرموز عديمة الحالة بتوقيع HMAC: **تسجيل الخروج** يتخلص من رمز العميل ويسجل الحدث.

## ذات صلة

- [مصادقة API](/docs/ar/api/authentication)
- [مفاتيح API](/docs/ar/administration/api-keys)
- [التحكم بالوصول والعزل](/docs/ar/security/rbac)
