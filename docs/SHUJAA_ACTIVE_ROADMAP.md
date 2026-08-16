# 02-SHUJAA_ACTIVE_ROADMAP.md

> **الصفة:** خارطة التنفيذ الرسمية النشطة لمشروع شجاع
> **الإصدار:** 1.2
> **آخر تحديث موثق:** 16 أغسطس 2026
> **النطاق:** 19 مرحلة مترابطة بالاعتماديات، من Stage 0 إلى Stage 18
> **المرجع التشغيلي عند هذا التحديث:** commit `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`

---

## CURRENT AUTHORITATIVE STATE

| البند | الحالة الحالية |
|---|---|
| checkpoint | `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`، المحلي = البعيد، Worktree نظيفة |
| آخر مرحلة مغلقة | Stage 4 — `VERIFIED COMPLETE — LOCAL/MOCK SCOPE` |
| الموقع الحالي | Stage 5 — `PLANNED`; التنفيذ لم يبدأ؛ Stabilization Verification ما زالت معلقة حتى حفظ الوثائق والحكم في Git |
| baseline | `224 passed`؛ واختبارات Owner Gate الموجهة `13 passed` |
| Audit | Audit 01 مكتمل؛ حكم التوافق محفوظ في artifact مستقل |
| الإجراء الحالي | إغلاق GAP-1 وGAP-2 فقط؛ ممنوع بدء Stage 5 في هذه الجولة |

---

## 1) الغرض والسلطة

هذا الملف هو المرجع التنفيذي الرسمي لترتيب مراحل بناء **شجاع**، وللإجابة عن:

- ما الذي أُنجز؟
- أين وصلنا الآن؟
- ما المرحلة التالية؟
- ما الذي لا يزال متبقيًا؟
- ما البوابة التي يجب اجتيازها قبل الانتقال؟

خارطة الثلاثين خطوة السابقة هي **قائمة قدرات تاريخية** تساعد على منع نسيان المتطلبات، لكنها ليست خارطة تنفيذ موازية ولا تتغلب على هذه الخارطة.

عند تعارض مستند قديم مع قرار أحدث موثق، تكون الأولوية بالترتيب:

1. دليل Git والاختبارات الحالي.
2. قرار مالك المشروع الأحدث.
3. هذه الخارطة النشطة.
4. `01-SHUJAA_HANDOFF.md` المحدث.
5. القرارات المعمارية في `03-SHUJAA_ARCHITECTURE_DECISIONS.md`.
6. السجلات والخرائط التاريخية.

أي تعارض يُكشف ويُوثق، ولا يُحل بالافتراض.

---

## 2) معاني الحالات

| الحالة | المعنى |
|---|---|
| `VERIFIED COMPLETE` | اكتملت المرحلة وثبتت بالأدلة والاختبارات المناسبة. |
| `COMPLETE — INHERITED BASELINE` | جزء تأسيسي مكتمل بُنيت عليه مراحل لاحقة وتغطيه الاختبارات الحالية، لكنه لم يخضع الآن لمراجعة مستقلة جديدة لكل Definition of Done. |
| `IN PROGRESS` | المرحلة بدأت، لكن Definition of Done الكامل لم يتحقق بعد. |
| `PLANNED` | ضمن الخارطة، ولم يبدأ تنفيذها. |
| `BLOCKED` | يوجد مانع مثبت يجب حله. |
| `HOLD — VERIFY FIRST` | يلزم تحقق تشغيلي قبل بدء التعديل أو استئنافه. |

`Partial Capability ≠ Full Capability`: وجود جزء من القدرة لا يعني اكتمال المرحلة أو النظام الكامل.

---

## 3) نقطة الوضع الحالية

> **HISTORICAL SNAPSHOT:** الجدول التالي محفوظ لسياق checkpoint السابق؛ الحالة الحالية في أعلى الوثيقة.

| البند | الحالة الموثقة |
|---|---|
| المستودع | `https://github.com/Mb-Ai91/shujaa_project` |
| الفرع | `refactor/modular-architecture` |
| commit | `9205d288ac649b875a2ba2e492f25fcb7e58856a` |
| عنوان commit | `fix(runtime): preserve stale terminal payload` |
| المحلي/التتبّع/البعيد | متطابقة عند آخر تحقق |
| Ahead / Behind | `0 / 0` |
| Worktree | نظيفة عند آخر تحقق |
| الاختبارات المركزة الأخيرة | `27 passed` |
| الاختبارات الكاملة | `211 passed` |
| المرحلة المكتملة | Stage 4 — Full Execution Lifecycle Control |
| المرحلة التالية | Stage 5 — Event Model + Audit Foundation |
| حالة المرحلة التالية | `PLANNED — ENTRY GATE PENDING` |

هذه نقطة مثبتة بتاريخ 15 أغسطس 2026، وليست بديلًا عن فحص Codespace عند العودة. يجب التحقق قراءةً فقط من Git ثم تشغيل baseline المناسب قبل أي تعديل جديد.

---

## 4) خارطة المراحل النشطة

| المرحلة | الاسم | الحالة الحالية | النتيجة الرئيسية |
|---:|---|---|---|
| 0 | Core Contracts & Architectural Boundaries | `COMPLETE — INHERITED BASELINE` | العقود الأساسية وحدود Manager وRunner/Executor والهوية والنتائج والأخطاء. |
| 1 | Identity & Persistent State | `COMPLETE — INHERITED BASELINE` | هويات Work/Task/Execution/Agent والأساس المحلي للحالة المستمرة. الاستمرارية الشاملة لكل كيانات شجاع ليست مكتملة بعد. |
| 2 | Work Model | `COMPLETE — INHERITED BASELINE` | Work Registry وQueue والأولوية والاعتماديات والتقدم والنتائج ومراجع الآثار. |
| 3 | Unified Execution Model | `VERIFIED COMPLETE` | مسار موحد: Manager → Work → Task → Execution → Dispatcher → Executor/Runner. |
| 4 | Full Execution Lifecycle Control | `VERIFIED COMPLETE` | تحكم محلي/Mock في دورة التنفيذ وسباقات الحالات النهائية والإلغاء والمهلة وRetry الآمنة والتنظيف والملكية؛ Pause/Resume منقولة بالاعتماديات وفق ADR-023. |
| 5 | Event Model + Audit Foundation | `PLANNED` | نموذج أحداث منظم وأساس سجل التدقيق، مع فصل الحدث التشغيلي عن سجل التدقيق الأمني. |
| 6 | Catalog Foundation | `PLANNED` | Capability Catalog موحد بهوية مستقرة وDescriptor وDependency Graph وLifecycle وResolver/Bindings لكل قدرة قابلة للإضافة والاستبدال والتقاعد. |
| 7 | Policy & Access Control | `PLANNED` | Policy-as-Data وAccess Graph ونقطة إنفاذ موحدة والموافقات والصلاحيات المحدودة. |
| 8 | Runtime Isolation & Safety | `PLANNED` | Runtime Adapters قابلة للاستبدال مع العزل وSandbox وحدود الموارد والأسرار وKill Switch دون branching دائم داخل Manager. |
| 9 | Durable Workflows | `PLANNED` | Durable Engine خلف عقد شجاع للاستئناف والتعافي وRetry وReplay وCompensation وJournal، مع خطة خروج من المزود. |
| 10 | Observability | `PLANNED` | Adapters مستقلة لـMetrics وLogs وTraces والتنبيهات مع portability وprivacy والتكاليف. |
| 11 | Evaluation Framework | `PLANNED` | واجهات مستقلة لمشغلات ونماذج وبيانات التقييم، مع regression وقياس الجودة وقابلية استبدال المزود. |
| 12 | Skills / MCP / External Capability Expansion | `PLANNED` | واجهات Shujaa-owned وSkills Registry وMCP/Tool Gateway وAdapters ودورة إضافة/ترقية/تعطيل/استبدال/إزالة آمنة. |
| 13 | LLM / Model Provider Layer | `PLANNED` | واجهة مستقلة للنماذج والمزودين، Routing وfallback وBindings واختبارات عقد واستبدال بلا تعديل Core. |
| 14 | Control Plane Backend | `PLANNED` | الإدارة المركزية للحالة والسياسات والموافقات والإيقاف والمراقبة. |
| 15 | Control Panel / UI | `PLANNED` | غرفة تحكم عربية أولًا للنص والصوت واللمس والإشراف البشري. |
| 16 | Production Data & Distributed Runtime | `PLANNED` | Storage/Runtime contracts قابلة للاستبدال للتخزين الإنتاجي والتشغيل الموزع وleases/fencing والاتساق، مع migration/export. |
| 17 | Deployment & Production Hardening | `PLANNED` | قابلية نقل cloud/deployment providers مع الأمن التشغيلي وDR/IR وRTO/RPO والأداء وSLA وخطة الخروج. |
| 18 | Promotion Pipeline | `PLANNED` | مسار موثوق: Sandbox → Staging → Production مع اعتماد وتوقيع وتراجع. |

---

## 5) ما أُنجز حتى الآن

### Stage 0 — Core Contracts & Architectural Boundaries

- العقود الأساسية.
- حدود مسؤولية `ShujaaManager`.
- عقود Runner وExecutor.
- هويات الوكلاء والمهام.
- عقود النتائج والأخطاء.

### Stage 1 — Identity & Persistent State

- `work_id`
- `task_id`
- `execution_id`
- `agent_id`
- أساس حفظ Task والحالة المحلية.

هذا لا يعني اكتمال التخزين الإنتاجي أو الموزع؛ موضعهما اللاحق Stage 16.

### Stage 2 — Work Model

- Work Registry وWork Queue.
- الأولوية والاعتماديات.
- parent/child work.
- progress والنتائج وartifact references.
- SLA/deadline foundations.
- ربط Work بالمهام والتنفيذ.

### Stage 3 — Unified Execution Model

- توحيد مسار تنفيذ Work والمهام والوكلاء.
- توجيه التنفيذ عبر Manager وDispatcher بدل المسارات المتوازية القديمة.
- تثبيت العقود والاختبارات اللازمة للانتقال إلى Stage 4.

### Stage 4 — الشريحة الأولى المكتملة

**الاسم:** Atomic Execution Lifecycle Control
**الحالة:** `VERIFIED COMPLETE AND PUSHED`

تحقق فيها:

1. Central transition guard داخل `ShujaaManager`.
2. Atomic transition contract في `ExecutionRegistryProtocol`.
3. `state_version` محلي للتحقق من الكتابات القديمة والمتزامنة.
4. `terminal_operation_id` لدعم terminal idempotency.
5. نتائج انتقال منظمة:
   - `APPLIED`
   - `STALE_VERSION`
   - `IDEMPOTENT_REPLAY`
   - `CONFLICTING_TERMINAL_ATTEMPT`
6. `LosingObservation` منظم للمحاولة النهائية الخاسرة.
7. منع `save()` العامة من تغيير `status` و`state_version` و`terminal_operation_id`.
8. إبقاء `save()` للبيانات غير الحالية مثل `executor_id`.
9. نقل تسعة مسارات حالة في Manager إلى `_transition_execution()`.
10. اختبار تنافس متزامن يثبت فائزًا نهائيًا واحدًا ويمنع الكتابة فوقه.

---

## 6) العمل الحالي داخل Stage 4 — HISTORICAL

### الشريحة الثانية الموافق عليها

**Local Cancel/Timeout Control and Terminal Reconciliation**
**حالتها:** `APPROVED SCOPE — NOT STARTED AFTER RESUME`

الهدف المبسط:

- توحيد حالة `Task` و`Execution` عندما يتسابق cancel أو timeout مع complete أو fail.
- استهلاك كل نتيجة من `TransitionResult` بصورة صريحة.
- منع أي كتابة مباشرة تتجاوز حارس الانتقال المركزي.
- الحفاظ على فائز نهائي واحد وعدم إفساد النتيجة النهائية القائمة.
- إضافة اختبارات حمراء أولًا، ثم أصغر تنفيذ يجعلها خضراء، ثم full regression.

### بوابة الدخول قبل تنفيذ الشريحة الثانية

1. فتح Codespace الفعلي.
2. التحقق من repository root والفرع وHEAD وupstream وworktree.
3. التأكد من أن checkpoint هو `db71a469…`، أو توثيق أي تقدم أحدث.
4. تشغيل baseline المناسب.
5. فحص مسارات `cancel_task` وtimeout واستهلاك `TransitionResult` والاختبارات الحالية.
6. تثبيت Scope وDefinition of Done التنفيذي التفصيلي قبل تعديل الكود.

### ما هو خارج نطاق هذه الشريحة مؤقتًا، وليس ملغى من المشروع

- Retry.
- Pause / Resume.
- Cleanup engine.
- Ownership release.
- Runtime stop adapters.
- Recovery.
- Durable journal.
- Distributed lease / fencing.
- Real providers.
- Event / Audit model.
- MCP / Skills.
- Policy.
- Control Plane.

تعود هذه العناصر في شرائح لاحقة من Stage 4 أو في مراحلها المحددة في الخارطة.

---

## 7) Definition of Done الإجمالي لـStage 4

لا تُعلن Stage 4 مكتملة بمجرد اكتمال شريحة واحدة. يتطلب إغلاقها، ضمن النطاق المحلي/Mock المعتمد:

- انتقالات حالة مركزية ومسموح بها فقط.
- terminal idempotency ورفض التعارضات النهائية.
- تنسيق صحيح بين Task وExecution.
- cancel وtimeout مضبوطين أمام سباقات complete/fail.
- retry semantics آمنة ومحددة.
- pause/resume semantics واضحة إذا بقيت ضمن نطاق Stage 4 النهائي.
- process ownership وownership release مضبوطين.
- cleanup semantics وفشل التنظيف موثق ومختبر.
- failure propagation متسقة.
- عدم وجود مسار تنفيذ موازٍ يتجاوز Manager.
- اختبارات موجهة واختبارات سباقات واختبارات regression كاملة ناجحة.
- توثيق ما بقي Local/Mock وما ينتقل صراحة إلى المراحل اللاحقة.

لا يتطلب إغلاق Stage 4 المحلية الادعاء بوجود durable/distributed/production runtime؛ هذه قدرات لمراحل لاحقة.

---

## 8) قواعد الانتقال بين المراحل

- شجاع ونجاحه هما الأولوية العليا، ويُختار الترتيب الذي يحقق أكبر منفعة صافية للمشروع على المدى القريب والبعيد.
- لا يكفي أن تكون القدرة مهمة؛ يجب استيفاء عقودها واعتمادياتها وبنيتها التحتية وبوابة دخولها قبل التنفيذ.
- ترتيب المفاضلة هو: القيود الأمنية وحقوق الملكية الصلبة، ثم المتطلبات السابقة والمسار الحرج، ثم خفض المخاطر، ثم القيمة والمنفعة الصافية، ثم قابلية الاختبار والرجوع والكلفة.
- المستخدم هو المالك وصاحب السلطة البشرية النهائية والامتيازات العليا الوحيدة داخل حوكمة شجاع؛ جميع الوكلاء والأدوات والنماذج تبقى محدودة الصلاحية و`Deny by Default`.
- لا نتجاوز مرحلة لمجرد أن مرحلة لاحقة أكثر جاذبية أو أسهل تنفيذًا.
- لا تبدأ مرحلة قبل اجتياز Entry Gate الخاص بها.
- لا تُغلق مرحلة قبل تحقق Exit Gate وDefinition of Done بالأدلة.
- لا نحول Proposal أو Architecture Decision إلى `Implemented` بلا دليل كود واختبارات.
- إذا ظهرت قدرة من خارطة الثلاثين القديمة، تُربط أولًا بمرحلة حالية أو Deliverable/Gate داخلها.
- لا تُنشأ مرحلة جديدة ولا يُعاد ترتيب المراحل إلا بقرار موثق وسبب dependency قوي.
- في القرارات المتغيرة تقنيًا، يسبق الاعتماد بحث حديث ومقارنة حيادية وخطة خروج.

---

## 9) خريطة القدرات التاريخية إلى المراحل النشطة

| القدرة التاريخية | موضعها الحالي |
|---|---|
| Manager / Task / Execution Core | Stages 0–4 |
| Durable Execution | Stages 4 و9 و16 حسب المحلي/الدائم/الموزع |
| Event وAudit | Stage 5 |
| Catalog / Inventory | Stage 6 |
| Policy Enforcement وAccess Graph وHuman Approval | Stage 7، مع عرضها لاحقًا في Stages 14–15 |
| Sandbox / Isolation وKill Switch وSecrets safety | Stage 8، مع تكامل Control Plane لاحقًا |
| Deterministic / Adaptive / Case Workflows | Stage 9 وما بعده |
| Observability | Stage 10 |
| Evaluation | Stage 11 |
| Tool/MCP Gateway وSkills Registry | Stage 12 |
| Memory | عقد مستقل يُثبت في مرحلته المعمارية المناسبة؛ تكامله لا يُدمج مع Skills |
| Artifact Store / Integrity | يُثبت كقدرة مشتركة ضمن Stages 5 و9 و16–18 حسب نوع الأثر |
| Model Gateway | Stage 13 |
| Control Plane Backend | Stage 14 |
| Arabic Control Room | Stage 15 |
| Distributed lease/fencing وProduction Data | Stage 16 |
| DR / Incident Response / Performance / SLA / Cost / Portability / Rollback | Stage 17 |
| Sandbox → Staging → Production | Stage 18 |

أي بند ما زال موضعه التفصيلي غير محسوم يُسجل كـ`ROADMAP CLARIFICATION`، ولا يُعتبر ملغى.

---

## 10) طريقة تحديث هذا الملف

يُحدّث الملف عند:

- اكتمال شريحة مؤثرة.
- إغلاق Stage كاملة.
- تغيير ترتيب أو نطاق مرحلة.
- ظهور capability غير ممثلة بوضوح.
- اعتماد قرار يغير Entry Gate أو Exit Gate.

بعد نهاية كل Stage كاملة، يجب عرض الخارطة للمستخدم مع:

1. ما أُنجز.
2. موقعنا الحالي.
3. ما تبقى.
4. المرحلة التالية وبوابة دخولها.

ولا يُستبدل checkpoint قديم بآخر إلا بعد التحقق من Git والاختبارات، مع تسجيل التاريخ والـcommit ومصدر الدليل.

---

## 11) تحديث تشغيلي — Stage 4 قبل بوابة الإغلاق — HISTORICAL

**التاريخ:** 15 أغسطس 2026
**الحالة:** `IN PROGRESS — EXIT GATE PENDING`

### خط الأساس الحالي

- الفرع: `refactor/modular-architecture`
- Local/Remote HEAD: `07038eacb2f3c6b672d26a9ff92018a723dc8cb8`
- التباعد: `0/0`
- شجرة العمل: نظيفة.
- آخر اختبار شامل موثق: `210 passed in 15.40s`.
- مصدر الدليل: مخرجات المستخدم من Codespace في 15 أغسطس 2026.

### الشرائح المكتملة في Stage 4

- Atomic lifecycle transitions and terminal reconciliation.
- Terminal outcome authority.
- Local process ownership and safe cleanup.
- Dispatch-failure atomicity.
- Safe Retry admission contract and lineage.
- Retry dispatch and runtime handoff with replay/conflict short-circuit.

### المتبقي لإغلاق Stage 4

بوابة واحدة مركبة:

1. تدقيق DoD النهائي مقابل التنفيذ والاختبارات.
2. تثبيت نقل Pause/Resume من نطاق Stage 4 التنفيذي إلى المراحل المعتمدة أدناه.
3. توثيق حدود القدرة المحلية/Mock وعدم إعلان production readiness.
4. اختبار شامل نهائي، ثم commit ودفع وتحقق تطابق Git لو احتاجت وثائق المستودع تعديلًا.

### Clarification معتمد: Pause/Resume

`PAUSED` يبقى حالة محجوزة في نموذج Execution، لكن Pause/Resume ليست قدرة منفذة في Stage 4. اعتمد المالك تأجيلها بالاعتماديات كما يلي:

| الجزء | المرحلة | معيار الجاهزية |
|---|---:|---|
| Event/Audit semantics | Stage 5 | أحداث pause/resume قابلة للتتبع |
| Runtime capability declaration/detection | Stage 6 | معرفة الدعم قبل الطلب ورفض غير المدعوم افتراضيًا |
| Authorization policy | Stage 7 | تحديد من يملك طلب التحكم ولماذا |
| Safe local/runtime-specific control | Stage 8 | Runtime Control Adapter مع اختبارات السباقات والهوية والمهلة |
| Durable resume/checkpoint recovery | Stage 9 | استئناف بعد restart/crash لا مجرد `SIGCONT` |
| Control Plane and UI exposure | Stages 14–15 | أوامر مراقبة وتحكم آمنة للمستخدم |

لا تُستخدم `SIGSTOP`/`SIGCONT` مباشرة داخل `ShujaaManager`. يلزم قبل Stage 8 عقد `pause/resume/terminate`، واكتشاف قدرات، ومهلة واعية بالتوقف، وتحقق PID/PGID/start-time، ودعم تعاوني لمسارات agent-executor، ومصفوفة سباقات كاملة.

هذا القرار لا يلغي Pause/Resume من شجاع؛ بل يحدد أول جاهزية محلية في Stage 8، والجاهزية المتينة في Stage 9، والإتاحة للمستخدم في Stages 14–15.

---

## 12) Stage 4 Exit Gate — إغلاق موثق

**التاريخ:** 15 أغسطس 2026
**الحالة:** `VERIFIED COMPLETE — LOCAL/MOCK SCOPE`

### الدليل التشغيلي

- الفرع: `refactor/modular-architecture`
- Local HEAD = Remote HEAD: `9205d288ac649b875a2ba2e492f25fcb7e58856a`
- التباعد: `0/0`، وشجرة العمل نظيفة.
- الالتزام الأخير: `fix(runtime): preserve stale terminal payload`.
- الاختبارات الموجهة الأخيرة: `27 passed`.
- الاختبارات الكاملة الأخيرة: `211 passed in 11.72s`.
- الرفع والتحقق: `PUSH_AND_VERIFICATION=GO`.

### تحقق Definition of Done

- الانتقالات مركزية والحسم ذري مع stale-version control.
- terminal idempotency والتعارضات النهائية والفائز النهائي محمية.
- Task وExecution متصالحتان عبر cancel/timeout/complete/fail، بما فيها حماية `error/result` بعد stale retry.
- ownership وrelease وcleanup المحلية منظمة ومختبرة، مع الاحتفاظ بالملكية عند فشل التحقق أو الإنهاء.
- رفض dispatch لا يترك سجلات جزئية.
- Retry تبدأ `DENY` وتحتاج `DECLARED_SAFE`، وتنشئ محاولة جديدة ذات lineage وقبول ذري، ولا تعيد handoff عند replay/conflict.
- لا يظهر مسار Core موازٍ يتجاوز Manager وExecution Registry.
- اختبارات السباقات والاختبارات الموجهة وfull regression ناجحة.
- Pause/Resume حُسم نطاقها عبر ADR-023، لا بإلغاء القدرة ولا بادعاء تنفيذها.

### الحدود

الإغلاق محلي/Mock فقط. لا يثبت durability أو distributed coordination أو production readiness أو Pause/Resume أو Event/Audit دائمين أو Control Plane.

### المرحلة التالية وبوابة دخولها

**Stage 5 — Event Model + Audit Foundation** هي المرحلة التالية. كانت البوابة `PENDING` عند هذا السجل التاريخي؛ الحالة الحالية في أعلى الوثيقة.

قبل التنفيذ:

1. تحقق Git وbaseline من checkpoint أعلاه.
2. افحص event structures الحالية ومسارات إنشائها واستهلاكها.
3. ثبّت فصل Event التشغيلي عن Audit الأمني.
4. عرّف الهوية والإصدار والفاعل وcorrelation/causation والطلب والنتيجة وحدود البيانات الحساسة.
5. اعتمد Scope وDefinition of Done واختبارات عقد حمراء قبل تعديل كود الإنتاج.

---

## 13) خطة تنفيذ Stage 5 — Event Model + Audit Foundation

**التاريخ:** 15 أغسطس 2026
**الحالة:** `PLANNED — STABILIZATION VERIFICATION PENDING — IMPLEMENTATION NOT STARTED`
**الخطة التفصيلية:** `04-01-SHUJAA_STAGE5_EVENT_AUDIT_PLAN.md`

| الشريحة | الهدف | بوابة الخروج |
|---|---|---|
| 5.0 | فحص Event/Audit الموجود وتثبيت النطاق | Evidence Receipt + Scope/DoD معتمدان |
| 5.1 | Event/Audit envelopes والهوية والإصدار | اختبارات عقود وimmutability وprivacy خضراء |
| 5.2 | Local append stores خلف Protocols | replay/conflict/failure/concurrency منظمة ومختبرة |
| 5.3 | تكامل lifecycle من نقاط سلطة Stage 4 | لا bypass ولا duplicate side effects |
| 5.4 | Audit للأفعال الحساسة الحالية | actor/resource/action/outcome قابلة للتتبع دون Policy وهمية |
| 5.5 | privacy والفشل والسباقات | negative/failure/race suites خضراء |
| 5.6 | المراجعة والإغلاق | full regression + docs + Git/remote verification |

### Definition of Done المختصر

- Event وAudit منفصلان، versioned وimmutable.
- correlation/causation والفاعل والمورد والنتيجة محددة.
- Local/Mock append stores قابلة للاستبدال وتتعامل مع replay/conflict صراحة.
- lifecycle events تصدر من نقاط السلطة المركزية.
- audit failure ظاهر ولا يغير terminal winner.
- sensitive payloads لا تسجل خامًا افتراضيًا.
- Pause/Resume events لا تعني قدرة Pause/Resume.
- اختبارات العقود والتكامل والسباقات والفشل وfull regression ناجحة.

### خارج النطاق

Policy Enforcement وApprovals وDurable Journal وRecovery وObservability وdistributed ordering وtransactional outbox وProduction tamper resistance وControl Plane.

لا تنتقل Stage 5 من `PLANNED` إلى `IN PROGRESS` إلا بعد Slice 5.0 و`ENTRY_GATE=GO`.

---

## 14) invariant عابر للمراحل — Capability Portability — HISTORICAL DETAIL

> السلطة الحالية للتفاصيل هي ADR-025؛ يحتفظ هذا القسم بسجل التوزيع المرحلي.

**التاريخ:** 16 أغسطس 2026
**الحالة:** `ADOPTED — PERMANENT CROSS-STAGE REQUIREMENT`

### الهدف

كل Tool أو MCP أو Skill أو Model أو Provider أو Agent Framework أو Runtime Adapter خارجي يجب أن يكون قابلًا للإضافة والترقية والاستبدال والتعطيل والتقاعد والإزالة الآمنة دون تعديل Core أو إعادة بناء شجاع.

### المسار الثابت

`Consumer → Shujaa Capability Interface → Resolver/Binding → Adapter → External Capability`

### شروط القبول عبر المراحل

- لا provider-specific imports أو schemas في Manager/Workflow/Core خارج Adapter مخصص.
- stable `asset_id` وversioned descriptor وcapability declaration لكل أصل.
- Dependency Graph وimpact analysis قبل التعطيل أو الإزالة.
- lifecycle states تشمل Sandbox/Staging/Active/Deprecated/Retired/Quarantined.
- contract tests وsecurity/evaluation gates قبل التفعيل أو التبديل.
- fallback/rollback موثقان وقابلان للاختبار.
- إزالة الأصل تلغي permissions وsecret references وتحتفظ بـAudit والـprovenance.
- إذا لم يوجد بديل، يفشل المستهلك المتأثر بصورة منظمة؛ لا ينهار Core ولا تتأثر المكونات غير المرتبطة.

### توزيع التسليم

| المرحلة | الجزء الملزم |
|---:|---|
| 5 | هوية capability منطقية داخل Event/Audit وربط النسخة المنفذة عند توفرها |
| 6 | Catalog + Descriptor + Dependency Graph + Lifecycle + Resolver/Binding |
| 7 | Policy/Access controls للتفعيل والاستبدال والإزالة |
| 8 | Runtime Adapters وعزل process/agent runtimes عن Manager |
| 9 | Durable Workflow Engine adapters وmigration/recovery portability |
| 10 | Observability backend adapters وexport portability |
| 11 | Evaluation runner/model/data interfaces القابلة للاستبدال |
| 12 | Tool/MCP/Skill contracts وadapters وregistries ودورة الاستيراد |
| 13 | Model/Provider gateway وrouting/fallback والاستبدال |
| 14–15 | إدارة دورة الحياة والأثر من Control Plane/UI |
| 16 | Storage/Distributed Runtime contracts وخطط migration/export |
| 17 | Cloud/Deployment portability وDR وخطة الخروج |
| 18 | promotion وrollback بين البيئات |

هذا المتطلب لا يعني صفر أثر على Workflow يعتمد حصريًا على قدرة أزيلت؛ بل يعني حصر الأثر، كشفه قبل التغيير، منع الحذف الكاسر، وتوفير migration/fallback/rollback دون المساس ببنية شجاع الأساسية.

### بوابة توافق رجعية للمراحل 0–4

تُنفذ قراءةً فقط ضمن Stage 5 Slice 5.0 قبل أي كود جديد:

1. فحص provider-specific imports وSDK types وschemas داخل Core.
2. فحص الهويات والحقول `requested_agent_id` و`required_capability` و`executor_id` و`runtime_id` وطريقة binding.
3. فحص Dispatcher/Runner/Agent Executor لأي اقتران يمنع Resolver/Adapter لاحقًا.
4. فحص Retry وlineage عند استبدال أو تقاعد agent/runtime خارجي.
5. تصنيف النتائج: `COMPATIBLE` أو `PATCH BEFORE STAGE 5` أو `MIGRATE IN STAGE 6/8/12/13`.

لا تعاد حالة Stage 0–4 إلى `IN PROGRESS` لمجرد اعتماد invariant جديد. يحدث ذلك فقط إذا ظهر تعارض مثبت يمنع المسار التالي؛ وعندها يُنفذ أصغر compatibility patch مستقل مع اختبارات كاملة.

---

## 15) invariant تشغيلي عابر للمراحل — Owner Instruction Gate وLarge Output Delivery — HISTORICAL DETAIL

> السلطة الحالية للتفاصيل هي ADR-026.

**التاريخ:** 16 أغسطس 2026
**الحالة:** `ADOPTED — PERMANENT CROSS-STAGE POLICY`

ينطبق على Stages 0–18 وعلى كل مراجعة أو أمر أو تعديل:

1. طلب المالك ونطاقه ومنعه الصريح بوابة تنفيذ ملزمة؛ لا مخالفة أو استبدال أو توسعة أو إسقاط صامت.
2. عند وجود خطأ محتمل أو خطر أو اقتراح أفضل: يُعرض أولًا، ويتوقف الإجراء المتأثر حتى يمنح المالك إذنًا صريحًا للمسار المختلف.
3. عدم الموافقة أو عدم الرد ليس إذنًا بالتنفيذ.
4. القيود الخارجة عن الصلاحية أو متطلبات السلامة والمنصة تُشرح بوضوح، ولا يُختار بديل تلقائيًا.
5. طول الأمر ليس المشكلة؛ المشكلة هي إخراج طرفية ضخم يتعرض للقص أو يفرض نسخًا ولصقًا مرهقًا.
6. الإخراج الضخم يُحفظ كاملًا مباشرة في ملف خارجي، وتعرض الطرفية ملخصًا محدودًا فقط، ثم يُتاح الملف للتنزيل الخاص من Codespace.
7. لا يُطلب نسخ ولصق ملف كبير أو تقسيمه يدويًا إلا بطلب صريح من المالك.

تدخل هذه السياسة ضمن Entry/Exit Gates: أي خطوة خالفت توجيهًا صريحًا أو فقدت جزءًا من الدليل بسبب قص الطرفية لا تُعد مكتملة حتى يصحح مسار التسليم أو يؤكد المالك الاستثناء.

---

## 16) بوابة عابرة للمراحل — Owner Constraint Supremacy — HISTORICAL IMPLEMENTATION PLAN

**التاريخ:** 16 أغسطس 2026
**الحالة:** `IMPLEMENTED + VERIFIED — DEVELOPMENT COMMAND SCOPE`
**المرجع:** `ADR-027`

تسبق هذه البوابة كل أمر وتعديل وحفظ في Stages 0–18:

| الطبقة | التسليم | بوابة الخروج |
|---|---|---|
| سجل القيود | `SHUJAA_OWNER_CONSTRAINTS.yaml` versioned وowner-controlled | schema + content verification |
| التحميل | قراءة السجل عند الإقلاع والاستئناف وقبل الأفعال | فقدان السجل ينتج `HOLD` |
| فحص الأوامر | validator للأدوات المحظورة والنطاق وطريقة الإخراج | negative tests خضراء |
| الحفظ | write/update/verify/version/receipt كمعاملة واحدة | لا claim بلا receipt |
| الاقتراح | فصل `PROPOSAL` عن التنفيذ | إذن المالك مثبت |
| المهارة | `v0.7` اختيارية فقط؛ لم تُستخدم | إذا أُنشئت تبقى candidate حتى independent eval + owner promotion |

### قيود أولية ملزمة

- `SC-ASSUME-001`: لا افتراض؛ المجهول يبقى غير مؤكد ويوقف الإجراء المتأثر.
- `SC-TOOL-001`: لا `rg/ripgrep` في Codespace؛ `grep/find` فقط، بلا إعادة فحص أو اقتراح تثبيت إلا بأمر المالك.
- `SC-OUTPUT-001`: المخرجات الضخمة إلى ملف قابل للتنزيل.
- `SC-OWNER-001`: لا تغيير لمسار المالك بلا إذن.
- `SC-SAVE-001`: لا ادعاء حفظ بلا تحقق موثق.

### أثرها على Stage 5

`AUDIT_01=COMPLETE`. سجل القيود والـvalidator واختباراته ملتزمة ومرفوعة في `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`؛ الاختبارات الموجهة `13 passed` والـbaseline `224 passed`. حكم التوافق محفوظ في artifact مستقل، وStage 5 لم يبدأ.
