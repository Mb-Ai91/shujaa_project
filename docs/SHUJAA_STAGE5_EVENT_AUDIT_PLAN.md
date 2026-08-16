# SHUJAA_STAGE5_EVENT_AUDIT_PLAN.md

> **المرحلة:** Stage 5 — Event Model + Audit Foundation
> **الحالة:** `PLANNED — STABILIZATION VERIFICATION PENDING — IMPLEMENTATION NOT STARTED`
> **تاريخ الخطة:** 15 أغسطس 2026
> **آخر تحديث موثق:** 16 أغسطس 2026
> **مرجع التثبيت الحالي:** commit `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`، والاختبارات `224 passed`
> **النطاق:** Local/Mock foundation فقط؛ لا Production أو Distributed أو Policy Enforcement

---

## CURRENT AUTHORITATIVE STATE

- Stage 4: `VERIFIED COMPLETE — LOCAL/MOCK SCOPE`.
- Owner Constraint Gate: `GO — DEVELOPMENT COMMAND SCOPE`، واختباراته الموجهة `13 passed`.
- Audit 01: مكتمل؛ حكم التوافق محفوظ في artifact مستقل يميز الاستنتاج عن الدليل الخام.
- Stage 5: لم يبدأ تنفيذها، وممنوع بدؤها في جولة إغلاق فجوتي التثبيت.
- Shujaa Development: النسخة النشطة `v0.6`؛ لم تُنشأ أو تُستخدم `v0.7`.

---

## 1) الهدف

إنشاء أساس موحد، مملوك لشجاع وقابل للاستبدال، يجيب عن سؤالين مختلفين:

1. **Event:** ما الذي حدث تشغيليًا داخل Work/Task/Execution/Runtime؟
2. **Audit Record:** من طلب أو نفذ ماذا، على أي مورد، وبأي سياق، وما النتيجة؟

Stage 5 لا تجعل Audit مجرد log نصي، ولا تجعل كل Event سجلًا أمنيًا، ولا تنقل إليها Policy أو Observability أو Durable Workflow Journal.

## 2) لماذا نحتاجها الآن؟

- Stage 4 أنشأت نقاط سلطة واضحة للحالة والنتائج والملكية وRetry؛ وهذه هي النقاط الصحيحة لإصدار أحداث منظمة.
- المراحل اللاحقة تحتاج سجلًا موحدًا: Catalog وPolicy وAccess Graph وRuntime Safety وControl Plane.
- دون عقود مستقلة سيصبح كل مكوّن مسؤولًا عن صيغة logging خاصة به، ما يخلق drift وازدواجًا وصعوبة في التدقيق والخروج من أي مزود.

## 3) الخيار المعتمد مبدئيًا والبدائل

### الخيار

عقود Shujaa-owned مستقلة عن Framework أو مزود، مع:

- Event Envelope versioned وغير قابل للتعديل بعد الإنشاء.
- Audit Record versioned ومنفصل، ويمكن ربطه بـEvent أو operation.
- Protocols للمخازن، وتنفيذ Local/Mock أولًا.
- append dispositions منظمة وidempotency محلية.
- adapters لاحقة لأي قاعدة بيانات أو Event Bus دون تغيير الكود الأساسي.

### بدائل غير معتمدة كبنية أساسية

| البديل | سبب عدم اعتماده كأساس |
|---|---|
| logs نصية فقط | لا توفر schema أو identity أو causation أو تحققًا موثوقًا. |
| callbacks الخاصة بـFramework | تربط شجاع بإطار واحد وتخلط مصدر الحدث بعقده. |
| Kafka/NATS/مزود خارجي الآن | توسع مبكر قبل ثبات العقود، مع كلفة وتشغيل وlock-in غير مطلوبين في Local/Mock. |
| دمج Event وAudit في سجل واحد | يخلط التشغيل بالأمن والاحتفاظ والصلاحيات والغرض. |

### إذا توقف التنفيذ أو تغيرت التقنية

- تبقى حالة Work/Task/Execution هي مصدر الحقيقة، ولا يعاد بناؤها من Event Store في Stage 5.
- يمكن إزالة أو استبدال Local Adapter خلف Protocol.
- schemas مصدّرة ومملوكة لشجاع، مع versioning واختبارات عقد.
- لا تعتمد بقية المنظومة على API مزود خارجي مباشر.

## 4) مبادئ التصميم الحاكمة

1. `Event ≠ Audit Record ≠ Log ≠ Metric ≠ Trace`.
2. العقود غير قابلة للتعديل بعد الإنشاء؛ التصحيح يكون بسجل جديد مرتبط، لا overwrite.
3. كل سجل له هوية وإصدار ومصدر ووقت وcorrelation/causation واضحان.
4. أقل بيانات لازمة: لا secrets ولا prompts أو results خام افتراضيًا.
5. lifecycle state لا يعاد كتابتها بسبب فشل التسجيل؛ الفائز النهائي يبقى مرجعًا.
6. فشل التسجيل لا يكون صامتًا؛ يعاد كحالة منظمة ويُختبر.
7. لا ادعاء exactly-once موزع؛ Stage 5 تقدم append محليًا وdedup منطقيًا فقط.
8. `PAUSED` وpause/resume قد تملك Event types محجوزة، لكن ذلك لا يخلق API أو capability تشغيلية.
9. كل Event/Audit يتعلق بقدرة خارجية يستخدم stable logical capability identity، ولا يجعل provider-specific identity عقدًا أساسيًا للمستهلك.

## 5) العقود المقترحة — تثبت نهائيًا بعد Entry Gate

### Event Envelope v1

الحد الأدنى المقترح:

- `event_id`
- `schema_version`
- `event_type`
- `occurred_at` بتوقيت UTC
- `recorded_at` بتوقيت UTC
- `source_component`
- `correlation_id`
- `causation_id` عند وجود سبب سابق
- `operation_id` عند وجود عملية منطقية
- `work_id` / `task_id` / `execution_id` بحسب السياق
- `actor_ref` عند توفره
- `capability_asset_id` المنطقي عند تعلق الحدث بقدرة خارجية
- `resolved_adapter_id` ونسخة التنفيذ عند توفرهما للتتبع، دون ربط Core بهما
- `payload` محدود ومتحقق

### Audit Record v1

الحد الأدنى المقترح:

- `audit_id`
- `schema_version`
- `recorded_at`
- `action`
- `actor_type` و`actor_id`
- `on_behalf_of` اختياريًا عند وجود دليل
- `resource_type` و`resource_id`
- `request_id` / `operation_id`
- `event_id` المرتبط اختياريًا
- `outcome`
- `reason_code` منظم
- `error_code` أو reference آمن عند الحاجة
- حقول Policy/Approval تبقى اختيارية ومحجوزة حتى Stage 7، ولا تُملأ بقيم وهمية.

### Append Result

النتائج المقترحة:

- `APPENDED`
- `IDEMPOTENT_REPLAY`
- `IDENTITY_CONFLICT`
- `SCHEMA_REJECTED`
- `WRITE_FAILED`

تحتاج التسمية النهائية إلى مطابقة ما هو موجود فعليًا بعد Entry Gate.

## 6) مصادر الأحداث داخل Stage 5

### مطلوب في النطاق

- قبول Work/Task/Execution.
- transition applied وterminal winner.
- stale/replay/conflicting terminal observation بصورة لا تكرر الأثر.
- dispatch accepted/rejected.
- cancel/timeout/complete/fail.
- cleanup dispositions وفشل التحقق أو الإنهاء.
- retry admission: applied/replay/conflict/denied.
- runtime handoff accepted/failed.

### محجوز تعريفًا فقط

- pause requested/accepted/rejected/resumed، دون تنفيذ Pause/Resume.

### خارج النطاق

- Policy decisions والموافقات الفعلية: Stage 7.
- Metrics/Traces/Alerts: Stage 10.
- Durable workflow journal وrecovery: Stage 9.
- Distributed global ordering وtransactional outbox: Stage 16 أو حيث تثبت الاعتمادية.
- Control Plane/UI: Stages 14–15.

## 7) مسار التنفيذ المعتمد

### Slice 5.0 — Entry Gate and Existing-State Inventory

**الهدف:** معرفة ما هو موجود قبل التصميم النهائي.

الأعمال:

1. تحقق Git والاختبارات من checkpoint المرجعي.
2. فحص `WorkEvent` وأي `event_refs` أو logging أو stores أو callbacks حالية.
3. حصر كل نقطة إنشاء واستهلاك حدث في Core وAdapters وTests.
4. كشف أي schema مكرر أو اقتران بـFramework.
5. تنفيذ Capability Portability Compatibility Audit رجعي للمراحل 0–4 قراءةً فقط.
6. فحص provider-specific imports وSDK/schema coupling داخل Core.
7. فحص `requested_agent_id` و`required_capability` و`executor_id` و`runtime_id` وDispatcher/Runner/Agent Executor وRetry lineage.
8. تصنيف النتائج إلى `COMPATIBLE` أو `PATCH BEFORE STAGE 5` أو `MIGRATE IN STAGE 6/8/12/13`.
9. تثبيت Scope وDoD النهائيين بناءً على الواقع.

**البوابة:** لا تعديل إنتاج قبل Evidence Receipt وقرار `ENTRY_GATE=GO`.

### Slice 5.1 — Canonical Contracts

**الهدف:** تثبيت Event/Audit envelopes والهوية والإصدار والتحقق.

الاختبارات أولًا:

- الحقول المطلوبة والقيم الفارغة والأنواع غير الصحيحة.
- immutability.
- UTC timestamps.
- correlation/causation الصحيحان.
- payload محدود ولا يقبل secrets المعروفة في اختبارات سلبية.
- فصل Event عن Audit Record.

**الناتج:** عقود فقط؛ بلا تكامل واسع أو مزود خارجي.

### Slice 5.2 — Local Append Stores and Integrity Foundation

**الهدف:** Protocols وتنفيذ Local/Mock قابل للاستبدال.

المطلوب:

- append-only behavior.
- identity uniqueness وidempotent replay.
- رفض identity conflict.
- ترتيب محلي محدد أو sequence محلي إن أثبتت الحاجة.
- فشل schema/write منظم وغير صامت.
- read/query الحد الأدنى للاختبارات والمراجعة، لا محرك تحليلات.
- integrity metadata محلية إذا أمكن تثبيتها دون ادعاء tamper-proof production.

### Slice 5.3 — Stage 4 Lifecycle Event Integration

**الهدف:** إصدار Events من نقاط السلطة المركزية فقط.

الترتيب:

1. transition outcomes.
2. terminal winner وlosing observation.
3. dispatch وruntime handoff.
4. cleanup ownership dispositions.
5. safe retry admission.

الضوابط:

- replay لا يولد أثرًا مكررًا لنفس event identity.
- فشل emission لا يعيد كتابة terminal winner.
- لا يكتب Executor مباشرة متجاوزًا Manager.
- لا logging للـcommand/result/error الخام افتراضيًا.

### Slice 5.4 — Audit Foundation Integration

**الهدف:** تسجيل الأفعال الحساسة الحالية دون ادعاء Policy مكتملة.

النطاق الأول:

- submit/cancel/retry requests.
- dispatch rejection.
- cleanup request/result.
- timeout/system terminal actions.

كل record يحدد actor المتاح فعليًا؛ عند غياب هوية مثبتة يستخدم نوعًا صريحًا مثل `system` ولا يخترع user identity أو policy version.

### Slice 5.5 — Privacy, Failure, and Concurrency Hardening

الاختبارات:

- منع secrets والحقول الحساسة أو استبدالها بـreferences.
- duplicate append وidentity conflict.
- سباق append للعملية نفسها.
- store corruption أو write failure.
- emission failure بعد transition ناجح.
- عدم تغيير الفائز النهائي بسبب audit failure.
- عدم تكرار Audit عند replay.

### Slice 5.6 — Exit Gate and Documentation

- contract review.
- directed suites + race tests + full regression.
- فحص bypass paths.
- توثيق Local/Mock وحدود عدم durability/distribution.
- commit مستقل لكل شريحة منضبطة أو checkpoint واضح قابل للرجوع.
- تحديث Handoff وRoadmap وArchitecture Decisions.

## 8) Failure Authority Matrix

| الحالة | صاحب الحقيقة | تصرف Event/Audit |
|---|---|---|
| Execution transition | Manager + Execution Registry | يسجل النتيجة ولا يعيد تقريرها. |
| terminal winner | Execution Registry | Event/Audit يحفظان الفائز أو الملاحظة الخاسرة دون overwrite. |
| Event append failure | Event Store | يعيد failure منظمًا؛ لا يغير lifecycle state. |
| Audit append failure | Audit Store | لا يفشل بصمت؛ يرفع نتيجة منظمة للمسار الطالب. سياسة fail-closed عالية المستوى مؤجلة لـStage 7. |
| schema rejection | Contract boundary | يرفض السجل قبل الكتابة مع reason code. |
| duplicate identity | Store | replay آمنة إذا المحتوى نفسه، وconflict إذا اختلف. |

## 9) Definition of Done لـStage 5

لا تُغلق Stage 5 إلا إذا ثبت:

1. عقود Event وAudit منفصلة وversioned وimmutable.
2. identity وcorrelation وcausation وactor/resource/outcome محددة ومختبرة.
3. Local/Mock stores خلف Protocols، append-only منطقيًا، مع replay/conflict منظمين.
4. نقاط lifecycle المعتمدة تصدر Events من السلطة المركزية دون bypass.
5. الأفعال الحساسة في النطاق تنتج Audit Records مرتبطة وقابلة للتتبع.
6. فشل التسجيل ظاهر ولا يعيد كتابة terminal winner.
7. البيانات الحساسة لا تُسجل خامًا افتراضيًا، مع negative tests.
8. Pause/Resume event semantics موثقة دون ادعاء capability.
9. اختبارات العقود والتكامل والسباقات والفشل وfull regression ناجحة.
10. الحدود Local/Mock وما ينتقل إلى Stages 7/9/10/16 موثقة صراحة.

## 10) Exit Gate

`STAGE5_EXIT_GATE=GO` يتطلب:

- Git identity ونظافة النطاق.
- جميع اختبارات Stage 5 الموجهة ناجحة.
- full regression ناجح.
- `git diff --check` ناجح.
- لا secrets أو raw sensitive payloads في fixtures أو outputs.
- لا اقتران مباشر بمزود أو Framework.
- Event/Audit schemas تستخدم هوية شجاع المنطقية للقدرات وتبقي تفاصيل المزود metadata قابلة للاستبدال.
- لا ادعاء exactly-once أو tamper-proof أو production readiness.
- مراجعة source paths التي يمكن أن تتجاوز Event/Audit boundary.
- تحديث الوثائق والـcheckpoint ثم commit/push/remote verification.

## 11) المخاطر والضوابط

| الخطر | الضابط |
|---|---|
| تضخم الأحداث | أنواع محددة، payload صغير، وعدم تسجيل كل log كحدث. |
| تسريب أسرار | allowlist للحقول وnegative tests وreferences بدل القيم الخام. |
| ازدواج الأحداث | event identity وoperation linkage وidempotent append. |
| كسر التنفيذ عند فشل السجل | failure disposition صريحة دون إعادة كتابة lifecycle winner. |
| ادعاء ضمانات موزعة | حدود Local/Mock مكتوبة واختبارات لا تتجاوزها. |
| lock-in | Protocols وschemas يملكها شجاع وadapters قابلة للاستبدال. |
| خلط Event وAudit وObservability | عقود ومخازن وأغراض منفصلة مع روابط صريحة. |

## 12) نقطة التوقف الحالية

- Stage 4: `VERIFIED COMPLETE — LOCAL/MOCK`.
- Stage 5: `PLANNED — STABILIZATION VERIFICATION PENDING — IMPLEMENTATION NOT STARTED`.
- لا يبدأ Stage 5 في هذه الجولة؛ الإجراء الحالي محصور في توثيق التثبيت وإثبات حكم Audit.
- لا تعديل كود ولا إنشاء اختبارات حمراء قبل فحص البنية الحالية واعتماد Scope التنفيذي النهائي.

---

## 13) invariant مرتبط بالخطة — External Capability Portability

**الحالة:** `ADOPTED — PERMANENT PROJECT REQUIREMENT`

Stage 5 لا تبني Catalog أو Gateways قبل موعدها، لكنها تضع الأساس الذي يمنع Event/Audit من ترسيخ اقتران بمزود خارجي:

- تسجل `capability_asset_id` المنطقي المستقر الذي يملكه شجاع.
- يمكنها تسجيل adapter/provider/version التي نُفذت فعليًا لأغراض Audit، بوصفها resolution metadata لا هوية المستهلك الأساسية.
- لا تستخدم event types أو schemas مرتبطة باسم شركة أو API محدد.
- يبقى السجل قابلًا للتفسير بعد استبدال أو إزالة القدرة الخارجية.
- تسجل عمليات إضافة/ترقية/تبديل/تعطيل/تقاعد/إزالة القدرات لاحقًا عندما تنشئها Stages 6/7/12/13.
- يطبق invariant كذلك على Runtime وDurable وObservability وEvaluation وStorage وDeployment في Stages 8–11 و16–17.

قبل Stage 5 Slice 5.1، يجب أن تنتهي المراجعة الرجعية للمراحل 0–4 بحكم موثق. لا تعاد فتح مرحلة سابقة إلا إذا أثبت الدليل تعارضًا يمنع Stage 5؛ أما الفجوات التابعة لـCatalog أو Runtime أو Skills أو Models فتسجل migration في Stage 6/8/12/13.

المرجع الملزم الكامل: ADR-025 وقسم Capability Portability في Active Roadmap وHandoff.

---

## 14) ضابط تنفيذ دائم — إذن المالك وتسليم مخرجات التدقيق

ينطبق ADR-026 على كل شرائح Stage 5:

- لا يتغير نطاق الفحص أو الكود ولا يُنفذ اقتراح بديل دون إذن المالك الصريح.
- إذا كشف التدقيق خطأً أو خطرًا أو خيارًا أفضل، تسجل النتيجة والتوصية ويتوقف الإجراء المتأثر حتى قرار المالك.
- يجوز أن يكون أمر التدقيق طويلًا، لكن الناتج الكبير لا يُطبع كاملًا ولا يُطلب من المالك نسخه ولصقه.
- يكتب الناتج الكامل مباشرة إلى ملف خارجي، وتطبع الطرفية ملخصًا صغيرًا وحالة الإنشاء فقط.
- يُتاح الملف للتنزيل الخاص من Codespace، ثم يُراجع بوصفه Evidence واحدًا كاملًا غير مقصوص.
- أي Evidence قُص بسبب حجم الطرفية لا يكفي لإغلاق Slice أو Gate حتى يُستعاد كاملًا من الملف.

---

## 15) بوابة ADR-027 قبل استئناف Slice 5.0

**الحالة:** `VERIFIED — OWNER CONSTRAINT GATE GO`

تحققت متطلبات البوابة:

1. أضيف `SHUJAA_OWNER_CONSTRAINTS.yaml` والـvalidator والاختبارات إلى Git في `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519` ودُفعت إلى البعيد.
2. نجحت الاختبارات الموجهة: `13 passed`، والـbaseline الكامل: `224 passed`.
3. نُفذ Audit 01 كاملًا وحُفظ الناتج الخام دون تعديل.
4. حُفظ حكم التوافق في artifact مستقل مع SHA-256 ومراجع الأسطر.

**HISTORICAL / SUPERSEDED:** الملف السابق `shujaa_portability_audit_01.txt` سجل تاريخي غير مكتمل، وقد حل محله `shujaa_portability_audit_01_complete.txt`. شرط `v0.7` الاختياري غير مستخدم؛ النسخة النشطة `v0.6` لم تتغير.
