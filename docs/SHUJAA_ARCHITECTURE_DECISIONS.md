# 03-SHUJAA_ARCHITECTURE_DECISIONS.md

> **الصفة:** سجل القرارات والعقود المعمارية المعتمدة لمشروع شجاع
> **الإصدار:** 1.3
> **آخر تحديث موثق:** 16 أغسطس 2026
> **تنبيه:** القرار المعماري يحدد ما يجب بناؤه؛ لا يثبت وحده أنه نُفذ أو اختُبر.

---

## CURRENT AUTHORITATIVE STATE

هذه الوثيقة هي سلطة **القرارات طويلة العمر فقط**، وليست سجل الحالة اليومية. عند checkpoint `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`: Stage 4 مغلقة ضمن Local/Mock، وStage 5 ما زالت `PLANNED` ولم يبدأ تنفيذها، والـbaseline الكامل `224 passed`.

ADR-027 حالته `IMPLEMENTED + VERIFIED — DEVELOPMENT COMMAND SCOPE`: سجل القيود والـvalidator واختباراته موجودة ومرفوعة. لا يعني ذلك Policy Engine عامًا. Audit 01 مكتمل، وحكم التوافق الموثق في artifact مستقل. النسخة النشطة من Shujaa Development هي `v0.6`؛ لم تُنشأ `v0.7` ولم تُستخدم.

ADR-028 `ADOPTED`: ادعاءات الحفظ والاختبار والرفع والتحقق تخضع لسلسلة حالة صريحة وEvidence Receipts. اعتماد القرار لا يثبت وحده أن تعديل السجل والـvalidator قد وصل إلى Codespace أو Git؛ حالة التنفيذ تُثبت فقط بالمخرجات التشغيلية المطلوبة في ADR-028.

---

## 1) الغرض

يحفظ هذا الملف القرارات طويلة العمر التي يجب ألا تضيع بين المحادثات أو تختلط بحالة التنفيذ اليومية.

يجيب عن:

- ما الحدود المعمارية المعتمدة؟
- من يملك كل حالة ومن يحق له تغييرها؟
- كيف نتعامل مع الفشل والسباقات والصلاحيات؟
- ما الذي نُفذ بالفعل، وما الذي ما زال قرارًا أو خطة؟
- ما القواعد التي يجب ألا يكسرها أي تغيير لاحق؟

الحالة اليومية والخطوة التالية مكانهما `01-SHUJAA_HANDOFF.md`، وترتيب المراحل في `02-SHUJAA_ACTIVE_ROADMAP.md`، والكود الفعلي في GitHub.

---

## 2) قاموس حالة القرار

| الوسم | المعنى |
|---|---|
| `ADOPTED` | قرار معتمد يجب احترامه. |
| `IMPLEMENTED + VERIFIED` | نُفذ واختُبر ضمن نطاق موضح. |
| `PARTIALLY IMPLEMENTED` | نُفذ جزء منه فقط. |
| `PLANNED` | معتمد اتجاهيًا لكن التنفيذ في مرحلة لاحقة. |
| `PROPOSED` | اقتراح لم يُعتمد نهائيًا. |
| `HISTORICAL` | قرار أو تصور قديم محفوظ للسجل وليس السلطة الحالية. |

---

## 3) ADR-001 — شجاع أولًا والحياد التقني

**الحالة:** `ADOPTED`

القرار:

- تُقاس الخيارات بمنفعتها الصافية لشجاع: الجودة، الأمن، الخصوصية، الاعتمادية، المرونة، الكلفة الكلية، والاستدامة.
- لا نختار تقنية بسبب الشركة أو البلد أو الشهرة أو المجانية وحدها.
- قبل اعتماد نموذج أو Framework أو أداة نجيب عن:
  1. لماذا نحتاجها؟
  2. لماذا هذا الخيار؟
  3. ما البدائل الحديثة؟
  4. ماذا لو توقف أو تغير ترخيصه أو سعره؟
  5. كيف نستبدله دون إعادة بناء شجاع؟
- القرارات المتغيرة تقنيًا تتطلب بحثًا حديثًا ومقارنة حيادية، بما فيها الحلول الصينية وغيرها عندما تكون مؤهلة.

---

## 4) ADR-002 — سلطة الأدلة وعدم الافتراض

**الحالة:** `ADOPTED`

القرار:

- Git هو مصدر حقيقة الكود.
- مخرجات GitHub Codespace الفعلية هي الدليل التشغيلي.
- `SHUJAA_HANDOFF.md` مصدر استمرارية، وليس Runtime.
- الذاكرة والمحادثات والسجلات التاريخية لا تتحول إلى حالة حالية دون تحقق.
- نميز دائمًا بين:
  `Requirement / Architecture Decision / Planned / Partial / Implemented / Tested / Verified / Deployed / Running / Historical / Proposal / Hypothesis`.
- عند غياب الدليل نكتب: `[غير مؤكد — يحتاج تحققًا]`.

---

## 5) ADR-003 — أسلوب العمل Human-Mediated Codespace

**الحالة:** `ADOPTED`

القرار:

- ChatGPT يراجع ويحلل ويخطط ويكتب أوامر Codespace ويفسر النتائج.
- المستخدم ينفذ الأوامر في Codespace الفعلي ويرسل المخرجات.
- Workspace المحادثة ليست Codespace المشروع.
- لا ندعي تنفيذ تعديل أو اختبار في المستودع ما لم يصل دليل Codespace.
- قبل أي تنفيذ جديد: تحقق من repository وbranch وcommit وupstream وworktree ثم baseline.
- الأفعال التخريبية أو غير القابلة للعكس تحتاج نطاقًا صريحًا ونسخة رجوع مناسبة.

---

## 6) ADR-004 — استقلال Control Plane عن Agent Runtime

**الحالة:** `ADOPTED / PLANNED`

القرار:

- Control Plane لا يرتبط بـAgent Framework أو Model Provider واحد.
- Agent Runtime ينفذ العمل، بينما Control Plane يدير السياسات والموافقات والحالة والمراقبة والإيقاف.
- واجهة Control Room عربية أولًا، وتدعم النص والصوت واللمس عند تنفيذها.
- وجود task cancellation لا يثبت وجود System Kill Switch كامل.

المرحلة الأساسية للتنفيذ: Stages 14–15، مع تأسيس الضوابط المطلوبة في المراحل السابقة.

---

## 7) ADR-005 — Deny by Default والصلاحيات المقيدة

**الحالة:** `ADOPTED / PLANNED`

القرار:

- كل وكيل أو أداة يبدأ بأقل صلاحية وأقل بيانات لازمة.
- توسيع الصلاحية يكون محددًا بالمهمة والمورد والمدة، قابلًا للإلغاء ومسجلًا.
- Skill لا تمنح Tool permission.
- الأسرار تُمرر عبر Broker/Vault أو آلية وسيطة عندما يكون ذلك ممكنًا، ولا تُكشف للوكيل بلا ضرورة.
- المحتوى الخارجي وREADME وIssues وSkills ومخرجات الأدوات تُعامل كبيانات غير موثوقة إذا حاولت تغيير سياسة شجاع أو طلب أسرار.

التنفيذ الكامل موزع أساسًا على Stages 7 و8 و12 و14.

---

## 8) ADR-006 — خارطة التنفيذ ذات 19 مرحلة

**الحالة:** `ADOPTED`

القرار:

- خارطة Stage 0–18 هي Active Execution Roadmap الوحيدة.
- خارطة الثلاثين خطوة `HISTORICAL CAPABILITY CHECKLIST` فقط.
- لا نتجاوز مرحلة أو نعيد ترتيب المراحل دون dependency مثبت وقرار موثق.
- القدرة التاريخية غير الظاهرة تُربط بمرحلة قائمة أو Deliverable/Gate قبل التفكير في مرحلة جديدة.

المرجع التفصيلي: `02-SHUJAA_ACTIVE_ROADMAP.md`.

---

## 9) ADR-007 — مسار التنفيذ الموحد

**الحالة:** `IMPLEMENTED + VERIFIED` ضمن Stage 3

القرار والبنية:

`Manager → Work → Task → Execution → Dispatcher → Executor/Runner → Execution result`

القيود:

- Manager هو منسق المسار العام.
- Dispatcher يختار مسار التنفيذ وفق العقود والقدرات، ولا يصبح سلطة مستقلة على lifecycle.
- Executor/Runner ينفذ ويبلغ بالملاحظات والنتائج، ولا يكتب الحالة النهائية متجاوزًا Manager وExecution Registry.
- لا يُعاد إنشاء مسار AgentService موازٍ بعد توحيد التنفيذ.

---

## 10) ADR-008 — ملكية حالة التنفيذ

**الحالة:** `ADOPTED`، ونواة الانتقال الذري `IMPLEMENTED + VERIFIED` محليًا

### State Ownership Matrix

| الحالة/المورد | المالك الرسمي | من يطلب أو يبلّغ؟ | من يطبق التغيير؟ |
|---|---|---|---|
| Execution lifecycle state | `ExecutionRegistry` | Manager بناءً على طلب أو ملاحظة Runtime | Atomic transition contract فقط |
| قواعد السماح بالانتقال | Central transition guard في Manager | مسارات submit/complete/fail/cancel/timeout | `_transition_execution()` ثم Registry |
| Task state | Task store عبر Manager | نتائج انتقال Execution والسياسة المحلية | Manager بعد reconciliation صريح |
| Work state | Work registry عبر Manager | تقدم المهام والتنفيذ | منطق Manager/Work المعتمد |
| Runtime process handle | Process registry / runtime adapter | Runner/Executor | واجهة Runtime المخصصة |
| Executor identity والبيانات غير الحالية | Execution record metadata | Dispatcher/Manager | `save()` المقيدة للحقول غير الحالية |
| السجل الدائم للأحداث والتدقيق | Event/Audit layer مستقبلًا | جميع المكونات عبر عقود منظمة | Stage 5 وما بعدها |

قواعد إلزامية:

- لا يُغيّر `status` أو `state_version` أو `terminal_operation_id` عبر `save()` العامة.
- `state_version` أداة تحكم في التزامن واكتشاف stale writes، وليست metadata تجميلية.
- مصدر الوقت المحلي monotonic يُستخدم عندما يتطلب القرار قياس مدة محلية؛ لا يُخلط مع timestamp دائم موزع.
- لا تكتب Task حالة نهائية تخالف الفائز النهائي في Execution.

---

## 11) ADR-009 — سلطة الفشل والنتيجة النهائية

**الحالة:** `ADOPTED`، وجزء السباق النهائي `IMPLEMENTED + VERIFIED`

### Failure Authority Matrix

| المصدر | سلطته |
|---|---|
| Executor/Runner | يبلغ success/failure/exit/error كملاحظة؛ لا يفرض الكتابة النهائية مباشرة. |
| Timeout observer | يطلب انتقال timeout ضمن العقد؛ لا يمحو حالة نهائية سبقت طلبه. |
| Cancel requester | يطلب cancel؛ قبول الطلب لا يساوي بالضرورة فوزه بالسباق النهائي. |
| Manager | يفسر الملاحظة ويطلب الانتقال المسموح ويصالح Task وExecution. |
| Execution Registry | يحسم ذريًا هل طُبق الانتقال أو كان stale أو replay أو تعارضًا نهائيًا. |
| Policy/Control Plane مستقبلًا | يقرر السماح عالي المستوى؛ لا يتجاوز سلامة state machine. |

لا يملك أي observer منفرد حق الكتابة فوق terminal state قائمة.

---

## 12) ADR-010 — دلالات الانتقال الذري والسباق النهائي

**الحالة:** `IMPLEMENTED + VERIFIED` محليًا في Stage 4 First Slice

نتيجة كل محاولة انتقال يجب أن تكون واحدة من:

| النتيجة | معناها والتصرف المطلوب |
|---|---|
| `APPLIED` | طُبق الانتقال؛ يجوز للمنسق متابعة reconciliation المبني عليه. |
| `STALE_VERSION` | تغيرت الحالة منذ قراءة الطالب؛ أعد القراءة ولا تكتب اعتمادًا على snapshot قديمة. |
| `IDEMPOTENT_REPLAY` | العملية النهائية نفسها أُعيدت؛ تعامل معها كإعادة آمنة بلا أثر مكرر. |
| `CONFLICTING_TERMINAL_ATTEMPT` | توجد نهاية مختلفة فازت؛ احتفظ بالفائز وسجل الملاحظة الخاسرة. |

قواعد إضافية:

- أول انتقال نهائي صالح يفوز ذريًا.
- تكرار العملية النهائية نفسها لا ينشئ أثرًا جديدًا.
- محاولة نهاية مختلفة لاحقة لا تغير الفائز.
- `LosingObservation` توثق الملاحظة الخاسرة بصورة منظمة.
- `LosingObservation` حاليًا نتيجة محلية منظمة، وليست Durable Journal أو Audit دائمًا.

---

## 13) ADR-011 — Terminal operation idempotency

**الحالة:** `IMPLEMENTED + VERIFIED` محليًا

القرار:

- تستخدم العمليات النهائية `terminal_operation_id` ثابتًا للمحاولة المنطقية نفسها.
- إعادة الطلب بالمعرف نفسه وبالمعنى النهائي نفسه هي replay آمنة.
- استخدام معرف أو معنى نهائي متعارض بعد وجود terminal winner لا يكتب فوق النتيجة.
- يجب ألا تُستخدم idempotency لإخفاء تعارض حقيقي أو دمج عمليتين مختلفتين.

هذا العقد محلي حاليًا؛ توسيعه عبر عمليات موزعة يحتاج Stage 16 وdistributed fencing/leases.

---

## 14) ADR-012 — المصالحة بين Task وExecution

**الحالة:** `IMPLEMENTED + VERIFIED` محليًا ضمن Stage 4

القرار:

- Execution هي مرجع نتيجة محاولة التنفيذ.
- Task تعكس النتيجة المعتمدة بعد استهلاك `TransitionResult`، لا بمجرد وصول observation.
- عند `STALE_VERSION` أو `CONFLICTING_TERMINAL_ATTEMPT` يجب إعادة قراءة الفائز قبل تحديث Task.
- عند `IDEMPOTENT_REPLAY` لا تتكرر الآثار الجانبية.
- cancel/timeout/complete/fail تمر بالمسار المركزي نفسه.
- لا توجد كتابة مباشرة للحالة لتجاوز نتيجة السباق.

تحققت المصالحة لمسارات cancel/timeout/complete/fail، بما فيها stale writes وreplay والتعارضات النهائية وحماية حمولة الفائز.

---

## 15) ADR-013 — Cleanup وOwnership وRetry

**الحالة:** `PARTIALLY IMPLEMENTED + VERIFIED` ضمن النطاق المحلي/Mock

القرارات الحاكمة:

- نتيجة العمل النهائية وفشل cleanup شيئان منفصلان؛ فشل التنظيف لا يعيد كتابة سبب النهاية الأصلي بصمت.
- لا تُحرر ownership قبل حسم الانتقال والآثار التي تعتمد عليها.
- retry محاولة تنفيذ جديدة ذات هوية واضحة، وليست إعادة فتح execution نهائية بلا عقد.
- لا تُنفذ retry لآثار جانبية غير آمنة دون idempotency أو compensation مناسبة.
- real runtime stop يحتاج adapters صريحة؛ تغيير الحالة إلى cancelled لا يثبت وحده توقف العملية الفعلية.

نُفذت ملكية العملية المحلية والتحقق من الهوية والتنظيف والإفراج الآمن وRetry المعلنة آمنة. تبقى runtime stop adapters العامة وdurable/distributed retry وcompensation لقدرات المراحل اللاحقة، وليست ملغاة من المشروع.

---

## 16) ADR-014 — Durable وDistributed حدود مختلفة

**الحالة:** `ADOPTED / PLANNED`

القرار:

- نجاح In-Memory أو Local/Mock لا يساوي durable أو distributed أو production-ready.
- Durable Journal وRecovery وReplay المنهجي ضمن Stage 9 وما يتصل بها.
- distributed leases/fencing والتخزين الإنتاجي ضمن Stage 16.
- لا نضيف Journal ثقيلًا إلى Stage 4 المحلية بلا آثار خارجية أو حاجة مثبتة.
- عند إدخال أثر خارجي، يُصنف retry safety وidempotency وcompensation قبل الاعتماد.

---

## 17) ADR-015 — Event وAudit طبقتان مترابطتان لا مترادفتان

**الحالة:** `ADOPTED / PLANNED` لStage 5

القرار:

- Event يصف ما حدث تشغيليًا داخل النظام.
- Audit يثبت من طلب، وبأي صلاحية وسياسة، ومن وافق، وما الذي نُفذ، والنتيجة.
- ليست كل Events سجلات Audit أمنية، وليس Audit مجرد log نصي.
- السجل المطلوب لاحقًا versioned، قابل للاستعلام، ويحمي التكامل وفق مستوى المخاطر.

حلقة السلطة المرجعية:

من طلب؟ → نيابة عن من؟ → لأي هدف؟ → تحت أي Policy version؟ → بأي صلاحية؟ → على أي بيانات؟ → بأي Agent/Tool/Model version؟ → من وافق؟ → ما الإجراء؟ → ما النتيجة؟ → كيف نثبتها ونتراجع عنها؟

---

## 18) ADR-016 — Catalog وAccess Graph وPolicy-as-Data

**الحالة:** `ADOPTED / PLANNED`

- Catalog مركزي للوكلاء والأدوات وMCP والنماذج والمهارات وWorkflows والآثار.
- كل أصل يملك owner وversion وprovenance وpermissions وrisk وtests وdependencies وlifecycle.
- Access Graph يحدد من يصل إلى ماذا، عبر أي أداة، لأي بيانات، تحت أي Policy، ولمدة كم.
- السياسات منفصلة عن كود الوكلاء، versioned وauditable وreviewable وrollbackable.
- Point of Enforcement موحدة قدر الإمكان، ولا توزع قرارات السياسة بصمت داخل adapters.

المراحل الأساسية: Stage 6 للكتالوج، Stage 7 للسياسة والوصول، ثم التكامل في Control Plane.

---

## 19) ADR-017 — Memory منفصلة عن Skills

**الحالة:** `ADOPTED / PLANNED`

- Memory = ماذا يعرف شجاع.
- Skills = كيف ينفذ شجاع عملًا.
- لا تُدمجان في مخزن أو سلطة واحدة.
- Skill لا تمنح نفسها صلاحيات ولا تعدّل النسخة النشطة من نفسها.
- كل Skill خارجية تمر عبر فحص المصدر والترخيص والأمن والاختبارات وSandbox ثم الترقية المرحلية.

---

## 20) ADR-018 — استقلال النماذج والأطر والأدوات

**الحالة:** `ADOPTED / PLANNED`

- ترتبط النماذج والأطر خلف واجهات يملكها شجاع وadapters قابلة للاستبدال.
- لا يُعتمد Framework أو Provider واحد كقيد معماري دائم.
- Routing وfallback لا يتجاوزان السياسة أو الخصوصية أو حدود البيانات.
- يجب وجود خطة خروج واختبارات عقد عند استبدال أي مزود.

يفسر ADR-025 هذا الاستقلال كمتطلب شامل ودائم للإضافة والترقية والاستبدال والتعطيل والإزالة الآمنة لكل قدرة خارجية، وليس للنماذج والأطر فقط.

المرحلة الأساسية للنماذج: Stage 13. الأدوات وMCP والمهارات: Stage 12.

---

## 21) ADR-019 — Kill Switch هرمي

**الحالة:** `ADOPTED / PLANNED`

المستويات المستهدفة:

- Task.
- Workflow.
- Agent.
- Tool.
- Model.
- Tenant/Project scope عند الحاجة.
- Global.

يجب أن يميز التنفيذ لاحقًا بين:

- منع بدء عمل جديد.
- طلب إيقاف عمل جارٍ.
- إيقاف Runtime فعلي.
- مصالحة الحالة بعد الإيقاف.
- تنظيف الموارد.

وجود cancel محلي للـTask لا يثبت اكتمال Kill Switch الهرمي.

---

## 22) ADR-020 — Preserve قبل Rebuild

**الحالة:** `ADOPTED`

المسار المعتمد:

`Preserve → Inspect → Compare → Targeted Fix → Refactor → Migration → Partial Replacement → Full Rebuild`

إعادة البناء من الصفر هي الخيار الأخير، ويجب أن تُقارن بالقيمة والمخاطر والكلفة والزمن وفقدان المعرفة وإمكان rollback.

---

## 23) ADR-021 — اللغة وتجربة المستخدم

**الحالة:** `ADOPTED`

- العربية الفصحى الواضحة هي لغة التواصل والواجهة الأساسية.
- يُستخدم المصطلح الإنجليزي عندما يكون أدق، مع شرح عربي موجز.
- لا يُقال عن عنصر مؤجل إنه «مستبعد» وحدها؛ الصياغة المعتمدة هي: **خارج نطاق هذه الشريحة مؤقتًا، وليس ملغى من المشروع**.
- يجب التمييز صراحة بين نهاية شريحة، ونهاية Stage، ونهاية المشروع.
- بعد نهاية كل Stage كاملة تُعرض خارطة الإنجاز والموقع الحالي والمتبقي.

---

## 24) ADR-022 — أولوية شجاع وسلطة المالك الوحيدة

**التاريخ:** 13 أغسطس 2026
**الحالة:** `ADOPTED — PERMANENT PROJECT POLICY`

### المشكلة

قد يتعارض ترتيب العمل بحسب الأهمية الظاهرة مع ترتيب الاعتماديات والبنية التحتية، وقد تحقق خطوة فائدة قريبة لكنها تضر المرونة أو الأمن أو الاستدامة على المدى البعيد.

### القرار

- شجاع ونجاحه هما الأولوية العليا في كل قرار متعلق بالمشروع.
- معيار الاختيار هو **المنفعة الصافية لشجاع على المدى القريب والبعيد**، بما يشمل القيمة، الأمن، الخصوصية، الصحة المعمارية، المرونة، الجودة، الاستدامة، قابلية الاختبار، الكلفة، وسهولة الخروج أو الرجوع.
- يُدمج ترتيب الأهمية والأولوية مع ترتيب الاعتماديات؛ لا تُقدَّم ميزة مهمة قبل استيفاء عقودها ومتطلباتها وبنيتها التحتية.
- ترتيب التنفيذ المعتمد هو: القيود الأمنية وحقوق الملكية الصلبة، ثم المتطلبات السابقة والمسار الحرج، ثم خفض المخاطر، ثم أعلى منفعة صافية، ثم القابلية للتحقق والرجوع والكلفة.
- عند تعارض منفعة قريبة مع مصلحة بعيدة، تُعرض المفاضلة صراحة ويُختار ما يزيد نجاح شجاع الكلي، لا ما يعطي تقدمًا شكليًا أسرع.
- أي ترتيب سابق قابل للمراجعة إذا أثبت الدليل أن ترتيبًا آخر أصلح لشجاع، مع توثيق السبب والأثر.

### سلطة المالك

- مالك شجاع هو المستخدم، وهو **صاحب السلطة البشرية النهائية والامتيازات العليا الوحيدة داخل حوكمة المشروع**.
- وحده يملك اعتماد تغييرات السياسات الجوهرية، ومنح أعلى الصلاحيات، والموافقة على الاستثناءات عالية أو حرجة المخاطر، والإجراءات التدميرية أو الإنتاجية.
- لا يملك أي Agent أو Manager أو Model أو Tool أو Skill أو مزود خارجي صلاحية مطلقة، ولا يجوز له منح نفسه صلاحيات أو ترقية نفسه أو تجاوز قرار المالك.
- تبقى صلاحيات جميع المكونات `Deny by Default + Controlled Privilege Escalation` وتخضع للتدقيق والحد الأدنى من الامتياز والبيانات.
- سلطة المالك النهائية لا تحول الادعاء إلى دليل، ولا تلغي التحقق التقني أو قوانين وسلامة المنصات الخارجية؛ بل تجعل قرار القبول النهائي بعد عرض الأدلة والمخاطر والبدائل للمالك وحده.

### قاعدة الحسم

عند وجود عدة مسارات صحيحة تقنيًا، يُوصى بالمسار الذي يحقق أكبر منفعة صافية لشجاع ويحافظ على خياراته المستقبلية، ثم يُرفع القرار النهائي للمالك عند الحاجة إلى تفويض أو مفاضلة جوهرية.

---

## 25) حدود الحالة المثبتة حاليًا — HISTORICAL SNAPSHOT

> هذا القسم محفوظ تاريخيًا وقد تجاوزته `CURRENT AUTHORITATIVE STATE` أعلاه.

عند checkpoint `db71a469…` يمكن القول فقط:

- Stage 3 مكتملة ومتحققة.
- Stage 4 بدأت وما زالت قيد العمل.
- شريحتها الأولى مكتملة ومرفوعة ومختبرة.
- حارس الانتقالات الذري وlocal state version وterminal idempotency وlosing observation منفذة محليًا.
- الشريحة الثانية معتمدة نطاقًا عامًا ولم يبدأ تنفيذها بعد العودة.

لا يجوز استنتاج أن شجاع يملك حاليًا:

- Retry كاملًا.
- Pause/Resume كاملين.
- Cleanup engine.
- Ownership release كاملًا.
- Runtime stop adapters حقيقية.
- Recovery أو Durable Journal.
- Distributed lease/fencing.
- Real providers جاهزة للإنتاج.
- Event/Audit أو MCP/Skills أو Policy أو Control Plane منفذة كاملة.
- Production readiness.

هذه العناصر **ما زالت ضمن معمارية شجاع وخارطته**، لكنها خارج نطاق الشريحة الحالية مؤقتًا أو مقررة لمراحل لاحقة.

---

## 26) قواعد تحديث سجل القرارات

عند قرار جديد أو تغيير قرار قائم، أضف:

- رقم ADR وعنوانه.
- تاريخ القرار.
- الحالة: Proposed/Adopted/Implemented/Verified/Superseded.
- المشكلة التي يحلها.
- القرار وحدوده.
- البدائل التي رُفضت ولماذا.
- المخاطر والآثار.
- خطة الخروج أو rollback.
- المرحلة المتأثرة.
- الدليل عند الادعاء بالتنفيذ أو التحقق.

لا يُحذف القرار القديم؛ يُوسم `SUPERSEDED` ويرتبط بالقرار الذي حل مكانه.

---

## 27) ADR-023 — تأجيل Pause/Resume إلى طبقات Runtime Capability

**التاريخ:** 15 أغسطس 2026
**الحالة:** `ADOPTED`
**صاحب القرار:** مالك شجاع

### المشكلة

يحتوي نموذج Execution على الحالة `PAUSED`، وتدعم بيئة POSIX الحالية `SIGSTOP` و`SIGCONT`، لكن النظام لا يملك بعد عقد تحكم runtime أو كشف قدرات أو سياسة صلاحيات أو مهلة واعية بالتوقف. كما أن مسار `agent-executor` لا يعلن عقد pause/resume تعاونيًا. تنفيذ الإشارات مباشرة داخل المدير سيحوّل دعمًا خاصًا ببيئة واحدة إلى ادعاء قدرة عامة غير صحيح.

### الأدلة

- لا توجد دوال `pause_task` أو `resume_task` في التطبيق.
- عقد Process Registry يقتصر على `register/get/release` ولا يمثل أوامر التحكم.
- timeout الحالي يعتمد انتظارًا بمهلة جدارية؛ إيقاف العملية قد يستهلك المهلة ويؤدي إلى `TIMED_OUT` خطأً.
- تحقق البيئة الحالية فقط: `OS_NAME=posix` ووجود `SIGSTOP` و`SIGCONT`؛ وهذا لا يثبت دعم كل runtime أو agent executor.

### القرار

1. تبقى `PAUSED` حالة نموذج محجوزة، وليست capability منفذة أو موعودة في Stage 4.
2. لا تُضاف إشارات POSIX مباشرة إلى `ShujaaManager`.
3. يُنفذ التحكم لاحقًا عبر Runtime Control/Capability Adapter يعلن `pause/resume/terminate` ويُرفض غير المدعوم فيه افتراضيًا.
4. تُنقل المتطلبات حسب المراحل:
   - Stage 5: الأحداث والتدقيق.
   - Stage 6: إعلان واكتشاف القدرات.
   - Stage 7: السياسة والتفويض.
   - Stage 8: pause/resume محلي آمن ومحدد بالـruntime.
   - Stage 9: checkpoint/recovery والاستئناف المتين.
   - Stages 14–15: Control Plane والواجهة.
5. يُعد هذا نقل نطاق معتمدًا من Stage 4، لا حذفًا للقدرة من الخارطة.

### الشروط السابقة للتنفيذ

- عقد Runtime Control صريح.
- Capability detection/negotiation مع `Deny by Default`.
- تعريف budget/timeout يستبعد أو يحسب زمن التوقف بسياسة موثقة.
- pause تعاوني أو checkpoint لمسارات agent-executor التي لا تدعم إشارات العمليات.
- التحقق من الملكية وPID/PGID وprocess start time قبل التحكم.
- مصفوفة انتقالات وسباقات تشمل `RUNNING → PAUSED → RUNNING`، والإلغاء أو انتهاء المهلة أو الاكتمال أثناء التوقف، وطلبات resume المتكررة أو المتأخرة، وفشل الإشارة.
- Policy/Audit لمن طلب التحكم والسبب والنتيجة.

### البديل المرفوض

إضافة `os.killpg(..., SIGSTOP/SIGCONT)` مباشرة في المدير خلال Stage 4. رُفض لأنه يقترن بـPOSIX، ولا يغطي agent runtimes، ويكسر معنى المهلة، ويوسع السباقات، ويجعل الحالة المعلنة أوسع من القدرة الفعلية.

### المخاطر والضوابط

- الخطر: بقاء `PAUSED` في enum قد يُفهم خطأً كقدرة جاهزة. الضابط: توثيقها `RESERVED / NOT IMPLEMENTED` وعدم إتاحة API لها.
- الخطر: تأخر التحكم التفاعلي. الضابط: Stage 8 هو أول هدف تنفيذ محلي بعد اكتمال الاعتماديات.
- الخطر: اختلاف دعم runtimes. الضابط: capability negotiation ورفض غير المدعوم افتراضيًا.

### معيار إعادة النظر

يُعاد تقييم القرار عند اكتمال عقود Stages 5–7 وبداية Stage 8. لا يتحول إلى `IMPLEMENTED` إلا بعد اختبارات انتقالات وسباقات وملكية ومهلة على runtime مدعوم، ولا يتحول إلى `VERIFIED` للاستئناف المتين قبل Stage 9.

---

## 28) ملحق تحقق تشغيلي — Stage 4 Pre-Exit — HISTORICAL

**التاريخ:** 15 أغسطس 2026
**الحالة:** `VERIFIED CHECKPOINT — NOT STAGE CLOSURE`

- الفرع: `refactor/modular-architecture`
- commit المحلي والبعيد: `07038eacb2f3c6b672d26a9ff92018a723dc8cb8`
- التباعد: `0 remote-only / 0 local-only`
- شجرة العمل: نظيفة.
- آخر تحقق شامل: `210 passed in 15.40s`.
- القدرة المثبتة: lifecycle/terminal authority، process ownership cleanup، dispatch atomicity، safe retry admission، retry runtime handoff.
- غير المثبت: Pause/Resume، durability، distributed coordination، production readiness.
- الخطوة التالية: Stage 4 Exit Gate وتوثيق الإغلاق؛ لا يبدأ تنفيذ Pause/Resume في هذه البوابة.

---

## 29) سجل قرار الإغلاق — Stage 4 Exit Gate — HISTORICAL MILESTONE

**التاريخ:** 15 أغسطس 2026
**الحالة:** `VERIFIED COMPLETE — LOCAL/MOCK SCOPE`

### الحكم

أُغلقت Stage 4 بعد مطابقة Definition of Done مع الكود والاختبارات ومراجعة المسارات المركزية والملكية والتنظيف وRetry. الإغلاق لا يوسع نطاق القدرة إلى durable أو distributed أو production.

### الدليل

- commit المحلي والبعيد: `9205d288ac649b875a2ba2e492f25fcb7e58856a`
- الالتزام الأخير: `fix(runtime): preserve stale terminal payload`
- شجرة العمل نظيفة والتباعد `0/0` بعد الرفع.
- الاختبارات الموجهة: `27 passed`.
- الاختبارات الكاملة: `211 passed in 11.72s`.
- `PUSH_AND_VERIFICATION=GO`.

### فجوة Exit Gate وإغلاقها

كشفت المراجعة أن إعادة محاولة terminal observation بعد `STALE_VERSION` كانت تعيد تمرير الحالة وoperation ID دون `error/result`. أثبت تشخيص مباشر أن النهاية تصبح `FAILED` مع `error=None`. أضيف اختبار regression أحمر، ثم عُدلت إعادة المحاولة لتمرير الحمولة نفسها، ونجحت الاختبارات الموجهة والكاملة.

### القدرات المثبتة

- lifecycle authority مركزية وatomic transition dispositions.
- terminal winner وidempotency وTask/Execution reconciliation.
- cancel/timeout أمام سباقات complete/fail.
- process ownership وidentity-aware cleanup وrelease محليًا.
- dispatch rejection atomicity.
- safe retry admission وlineage وruntime handoff مع replay/conflict short-circuit.

### الحدود والقرار التالي

- Pause/Resume تبقى `RESERVED / NOT IMPLEMENTED` وتتبع ADR-023.
- Event/Audit الدائمان يبدأ تصميمهما في Stage 5 بعد Entry Gate مستقل.
- durable recovery في Stage 9، والتنسيق الموزع والتخزين الإنتاجي في Stage 16.
- المرحلة التالية: `Stage 5 — Event Model + Audit Foundation`. هذا السطر يسجل حالة الإغلاق التاريخية؛ الحالة الحالية في أعلى الوثيقة.

---

## 30) ADR-024 — فصل Event عن Audit واعتماد عقود مملوكة لشجاع

**التاريخ:** 15 أغسطس 2026
**الحالة:** `ADOPTED PLANNING BASELINE — IMPLEMENTATION NOT STARTED`

### المشكلة

تحتاج مراحل شجاع اللاحقة إلى معرفة ما حدث تشغيليًا وإثبات من طلب أو نفذ فعلًا حساسًا. استخدام logs أو callbacks الخاصة بإطار واحد يخلط الأغراض، ويضعف الهوية والإصدار والخصوصية، ويربط المشروع بمزود أو Framework.

### القرار

1. Event التشغيلي وAudit Record عقدان منفصلان يمكن ربطهما بـevent/operation identity.
2. العقود versioned وimmutable ويملكها شجاع، وتبقى adapters خلف Protocols.
3. يبدأ التنفيذ بـLocal/Mock append stores؛ لا Event Bus أو distributed guarantees في Stage 5.
4. الحقول الأساسية تشمل identity وschema version والوقت والمصدر وcorrelation/causation والفاعل والمورد والعملية والنتيجة بحسب نوع السجل.
5. أقل بيانات لازمة؛ لا secrets أو command/result/error الخام افتراضيًا.
6. فشل Event/Audit append لا يعيد كتابة lifecycle winner، ولا يُخفى؛ يعاد كتصرف منظم ويُختبر.
7. لا ادعاء exactly-once موزع أو tamper-proof production في هذه المرحلة.
8. Pause/Resume event types قد تُعرّف دون إنشاء capability تشغيلية.

### توزيع السلطة

- Manager وExecution Registry يبقيان مصدر حقيقة lifecycle.
- Event Store يسجل الوقائع التشغيلية ولا يقرر الحالة.
- Audit Store يسجل الفعل والسياق والنتيجة ولا يمنح الصلاحية.
- Policy Engine في Stage 7 يقرر السماح لاحقًا؛ Stage 5 لا تختلق policy version أو approval.
- Observability في Stage 10 تستهلك أو تربط البيانات عند الحاجة، ولا تحل محل Event/Audit.

### البدائل المرفوضة

- logs نصية فقط.
- دمج Event وAudit في schema واحد.
- Framework callbacks كعقد شجاع الأساسي.
- اعتماد Kafka/NATS أو مزود خارجي قبل تثبيت العقود والحاجة التشغيلية.

### المخاطر والضوابط

- تضخم السجل: أنواع محددة وpayload صغير.
- التسريب: allowlist وreferences واختبارات سلبية.
- الازدواج: identity وoperation linkage وidempotent append.
- lock-in: Protocols وschemas مملوكة لشجاع.
- ضمانات زائفة: توثيق Local/Mock صراحة.

### معيار الانتقال إلى التنفيذ

لا يبدأ التنفيذ قبل Stage 5 Slice 5.0: تحقق Git وbaseline، فحص البنية الحالية، ثم تثبيت Scope وDefinition of Done التنفيذيين و`ENTRY_GATE=GO`.

المرجع التفصيلي: `04-01-SHUJAA_STAGE5_EVENT_AUDIT_PLAN.md`.

---

## 31) ADR-025 — Shujaa-Owned Capability Portability Boundary

**التاريخ:** 16 أغسطس 2026
**الحالة:** `ADOPTED — PERMANENT ARCHITECTURAL INVARIANT`
**صاحب القرار:** مالك شجاع

### المشكلة

إذا تعامل Manager أو Workflow أو Core مباشرة مع API أو SDK أو schema لمزود أو أداة أو نموذج بعينه، يصبح الاستبدال أو الإزالة تغييرًا بنيويًا، وقد تنتشر الاعتماديات بصمت وتتعطل أجزاء غير مرتبطة. عبارة «قابل للاستبدال» وحدها لا تكفي ما لم تشمل دورة الحياة وفحص الاعتماديات والرجوع.

### القرار

توضع كل قدرة خارجية خلف Boundary يملكها شجاع:

`Shujaa Capability Interface → Resolver/Binding → Adapter → External Capability`

وينطبق ذلك على:

- Tools.
- MCP servers/capabilities.
- Skills.
- Models وModel Providers.
- Agent Frameworks.
- Runtime Adapters.
- أي capability خارجية مستقبلية.

### القواعد الملزمة

1. Core يطلب capability منطقية ولا يعتمد على provider name أو SDK type.
2. لكل أصل stable identity وversioned descriptor وprovenance وcapabilities وrisk وpermissions وdependencies وlifecycle state.
3. Resolver/Binding يفصل المستهلك عن التنفيذ المختار، ويدعم fallback وrollback ضمن Policy.
4. Adapter وحده يعرف API وschemas الخاصة بالمزود.
5. الإضافة والترقية والاستبدال تمر عبر contract/security/evaluation tests وSandbox ثم Staging.
6. التعطيل والإزالة يبدآن بـdependency/impact analysis؛ يمنع الحذف الكاسر افتراضيًا.
7. عند غياب بديل، يُحصر الفشل في المستهلك المرتبط ويكون منظمًا؛ لا ينهار Core.
8. التقاعد يلغي الصلاحيات ومراجع الأسرار ويحافظ على Audit وprovenance والقدرة على تفسير التاريخ.
9. الحذف المادي يخضع للاحتفاظ والسلطة والمخاطر، وليس وسيلة التعطيل الأولى.
10. أي استثناء يحتاج Architecture Decision صريحًا ونطاقًا ومدة وخطة خروج؛ لا ينشأ اقتران دائم بصمت.

### الضمان وحدوده

الضمان هو عدم الحاجة إلى تعديل Core أو إعادة بناء شجاع، وحصر الأثر وكشفه وإدارته والرجوع عنه. لا يضمن استمرار Workflow يعتمد حصريًا على قدرة أزيلت بلا بديل؛ في هذه الحالة يمنع التغيير أو يطلب migration/بديلًا أو موافقة على إيقاف المستهلك.

### دورة الحياة المرجعية

`DISCOVERED → VALIDATED → SANDBOX → STAGING → ACTIVE → DEPRECATED → RETIRED/QUARANTINED`

### البدائل المرفوضة

- hard-coded provider integrations داخل Core.
- سجل منفصل ومعمارية مختلفة لكل نوع قدرة.
- حذف مباشر دون Dependency Graph.
- تبديل مزود بلا contract tests أو rollback.
- اعتبار fallback مبررًا لتجاوز Policy أو privacy boundaries.

### معيار المطابقة

لا تُعد القدرة الخارجية متوافقة مع شجاع حتى تثبت:

- Interface/Adapter isolation.
- catalog identity وdependency declaration.
- capability negotiation.
- contract tests.
- add/upgrade/replace/disable/retire scenarios.
- fallback/rollback حيث يلزم.
- safe removal أو منعها عند وجود اعتماديات.

### المراحل المتأثرة

كل مرحلة من Stages 5–18 تُدخل قدرة أو مزودًا أو تقنية خارجية تخضع لهذا invariant. التسليم المباشر موزع على:

- Stage 5: logical capability identity في Event/Audit.
- Stage 6: Catalog/Descriptor/Dependency Graph/Resolver/Bindings.
- Stage 7: Policy/Access لإدارة lifecycle.
- Stage 8: Runtime Adapters.
- Stage 9: Durable Workflow Engine adapters.
- Stage 10: Observability backend adapters.
- Stage 11: Evaluation provider/runner/data interfaces.
- Stage 12: Tool/MCP/Skill adapters وregistries.
- Stage 13: Model/Provider gateway.
- Stages 14–15: Control Plane/UI lifecycle management.
- Stage 16: storage/distributed-runtime contracts وmigration/export.
- Stage 17: cloud/deployment portability وexit/DR.
- Stage 18: promotion/rollback.

### Compatibility Gate رجعية للمراحل 0–4

اعتماد ADR-025 لا يلغي إغلاق المراحل السابقة تلقائيًا. تُجرى مراجعة read-only ضمن Stage 5 Slice 5.0 للتحقق من العقود والهويات وDispatcher/Runner/runtime IDs وRetry lineage وأي provider-specific coupling.

تُصنف كل نتيجة:

- `COMPATIBLE — NO CHANGE`.
- `PATCH REQUIRED BEFORE STAGE 5` إذا كان التعارض يمنع الأساس الجديد.
- `PLANNED MIGRATION` في Stage 6 أو 8 أو 12 أو 13 إذا كانت الاعتمادية تخص طبقتها الطبيعية.

لا يُنفذ retrofit استباقي ولا تُعاد فتح Stage 0–4 بلا دليل مباشر واختبار يثبت الفجوة. أي patch لازم يكون مستقلًا، محدودًا، قابلًا للرجوع، ويحافظ على baseline الكامل.

### تصحيح التوزيع

هذا القسم يصحح التوزيع المختصر السابق الذي ذكر Stages 5 و6 و7 و12 و13 و14–15 و18 فقط؛ ذلك كان تعدادًا غير كامل، لأن invariant يشمل أيضًا Runtime وDurable وObservability وEvaluation وStorage وDeployment في Stages 8–11 و16–17.

---

## 32) ADR-026 — Owner Instruction Authority and Large Output Delivery

**التاريخ:** 16 أغسطس 2026
**الحالة:** `ADOPTED — PERMANENT`

### السياق

في Human-Mediated Codespace Workflow ينفذ المالك الأوامر ويعيد الدليل التشغيلي. مخالفة طلبه أو تغيير نطاقه بلا إذن تكسر السلطة البشرية، كما أن إخراجًا ضخمًا في الطرفية قد يُقص أو يفرض نسخًا ولصقًا غير عملي.

### القرار

1. كل أمر أو منع أو نطاق صريح من المالك ملزم في المسار المتأثر.
2. لا يجوز للمساعد أن يخالفه أو يستبدله أو يوسعه أو ينقصه بصمت.
3. إذا اعتقد المساعد أن المالك قد يكون مخطئًا، أو وجد خطرًا أو خيارًا أنفع، فعليه عرض الدليل والأثر والتوصية ثم انتظار إذن صريح قبل التنفيذ المختلف.
4. عند تعارض الطلب مع صلاحية غير متاحة أو متطلبات سلامة أو منصة ملزمة، يتوقف المسار ويُشرح القيد؛ لا يُنفذ بديل غير مأذون.
5. يمكن متابعة بنود مستقلة لا يمسها التعارض، مع عزل الحالات وفق Batch Request Discipline.
6. الأوامر الطويلة مسموحة عند الحاجة. إذا كان **ناتج الطرفية** كبيرًا جدًا أو معرضًا للقص، تُوجَّه النتيجة الكاملة إلى ملف خارجي.
7. تعرض الطرفية metadata صغيرة فقط، مثل المسار والحجم وعدد الأسطر والحالة وchecksum عند الحاجة.
8. يُسلّم الملف دون نسخ ولصق، عبر تنزيل خاص من Codespace بالطريقة المعتمدة أو وسيلة ملف مكافئة آمنة.
9. لا يُجزأ الناتج الضخم للنسخ اليدوي إلا بطلب المالك.

### معيار المطابقة

- لا side effect خارج الطلب الصريح.
- لا silent substitution أو silent scope expansion.
- الاقتراح المختلف يبقى `PROPOSAL` حتى موافقة المالك.
- يحتفظ ملف الإخراج بالدليل الكامل، ويُتحقق من نجاح إنشائه قبل الاعتماد عليه.
- لا تُعرض أسرار أو بيانات حساسة في ملخص الطرفية أو ملف غير محمي.

### العلاقة بالقرارات الأخرى

هذا القرار يكمّل ADR-003 الخاص بـHuman-Mediated Codespace، وسياسة سلطة مالك شجاع، وProject Policy Mutation Gate. لا يمنح إذنًا بتجاوز Hard Security Gates، بل يوجب التوقف والشرح وطلب التوجيه عند وجودها.

---

## 33) ADR-027 — Owner Constraint Supremacy and Fail-Closed Action Gate

**التاريخ:** 16 أغسطس 2026
**الحالة:** `IMPLEMENTED + VERIFIED — DEVELOPMENT COMMAND SCOPE`

### المشكلة

الاعتماد على الذاكرة أو الانضباط النصي وحدهما يسمح لنمط عام بأن يظهر عند نقص السياق أو الاستعجال، وقد ينتج أمرًا يخالف قيدًا محفوظًا. المطلوب ليس ادعاء استحالة السهو، بل منع السهو من التحول إلى أمر أو أثر أو ادعاء حفظ.

### القرار

ينشئ شجاع بوابة fail-closed تسبق كل فعل:

`LOAD OWNER CONSTRAINTS → RESOLVE PRECEDENCE → VALIDATE ACTION → GO/HOLD`

وترتيب السلطة هو:

1. safety/permission/platform hard constraints.
2. current explicit owner instruction.
3. permanent owner policies and constraint registry.
4. verified operational evidence.
5. approved architecture and roadmap.
6. generic defaults.

لا يجوز لـgeneric default تجاوز طبقة أعلى. غياب السجل أو غموض القيد أو تعارض غير محلول ينتج `OWNER_CONSTRAINT_GATE=HOLD`.

### المصدر القابل للفحص

يضاف إلى جذر تطبيق شجاع:

`SHUJAA_OWNER_CONSTRAINTS.yaml`

ويحتوي stable constraint IDs والحالة والنطاق والمنع والبديل المسموح وسلطة التغيير. يصبح Git مصدر حقيقة النسخة التنفيذية، بينما تبقى Handoff/Roadmap/ADRs مراجع بشرية تربط بالمعرفات ولا تستبدل السجل.

### القيود المعتمدة أولًا

- `SC-ASSUME-001`: deny unverified assumptions.
- `SC-OWNER-001`: deny silent instruction override or scope substitution.
- `SC-TOOL-001`: deny `rg/ripgrep` in Codespace; allow `grep/find`; deny recheck/install suggestion without explicit owner order.
- `SC-OUTPUT-001`: route oversized terminal output to a downloadable file.
- `SC-SAVE-001`: deny save claims without verified writeback receipt.
- `SC-PROPOSAL-001`: deny execution of an unapproved proposal.

### معاملة الحفظ الذرية

لا يُقبل معنى «احفظ» إلا بالسلسلة:

`WRITE → UPDATE REFERENCES → VERIFY CONTENT → VERIFY VERSION → EVIDENCE RECEIPT`

إذا تعذر أي عنصر، تكون النتيجة `HOLD — SAVE NOT VERIFIED`.

### الإنفاذ

1. validator منخفض الحرية يفحص الأمر أو خطة الأثر قبل التسليم.
2. deny-list للأدوات والأفعال المحظورة وallow-list للبدائل المعتمدة.
3. negative regression tests لكل قيد دائم.
4. bootstrap إلزامي بعد restart أو compaction أو handoff.
5. إذا اختار المالك إنشاء Shujaa Development v0.7 مستقبلًا، تبقى `CANDIDATE` وتخضع لتقييم مستقل وموافقة المالك؛ لا ترقي نفسها. هذا شرط اختياري ولم يُستخدم في التنفيذ الحالي.
6. لا تعديل للسجل إلا بأمر المالك، مع version وreason وrollback وAudit.

### حدود الضمان

لا يدعي القرار عصمة النموذج من توليد نص خاطئ. الضمان المعماري هو أن الخطأ لا يجتاز البوابة إلى تنفيذ أو حفظ موثوق، وأن غياب الدليل يفشل مغلقًا بدل الرجوع إلى نمط عام.

### Definition of Done

- سجل القيود موجود في Git ومتحقق schema/content.
- validator وnegative tests ناجحة.
- حالات `rg`، فقدان السجل، output الكبير، تغيير النطاق، وsave claim مغطاة.
- Handoff/Roadmap/ADR/Stage plan تشير إلى المعرفات نفسها بلا drift.
- إذا استُخدمت v0.7: تجتاز candidate تقييمًا مستقلًا ثم يعتمدها المالك قبل الترقية.

### Evidence Receipt

- السجل والـvalidator والاختبارات ملتزمة ومرفوعة في `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`.
- الاختبارات الموجهة: `13 passed`؛ والـbaseline الكامل: `224 passed`.
- Audit 01 مكتمل؛ حكم التوافق محفوظ في artifact مستقل مع مراجع الأسطر وSHA-256 للدليل الخام.
- نطاق التنفيذ: أوامر التطوير المحددة فقط؛ لا ادعاء Policy Engine أو Runtime gate شامل.
- `v0.7`: لم تُنشأ ولم تُستخدم؛ النسخة النشطة `v0.6` لم تتغير.

---

## 34) ADR-028 — Completion State and Evidence Provenance Gate

**التاريخ:** 16 أغسطس 2026
**الحالة:** `ADOPTED — IMPLEMENTATION REQUIRES CODESPACE EVIDENCE`
**صاحب القرار:** مالك شجاع

### المشكلة

يمكن أن يولد artifact في مساحة المحادثة، أو يكتب في Codespace، أو يصبح متعقبًا أو ملتزمًا أو مرفوعًا دون أن يبلغ حالة التحقق المطلوبة. اختزال هذه الحالات في كلمة «تم» ينتج false completion وغموضًا في مصدر الدليل.

### القرار

تمر حالة كل كود أو ملف أو وثيقة أو تقرير أو artifact بالترتيب التالي فقط:

`GENERATED → WRITTEN_TO_CODESPACE → TRACKED → COMMITTED → PUSHED → VERIFIED`

لا تُستخدم كلمة «تم» أو «اكتمل» دون تسمية الحالة الفعلية ودليلها. لا يجوز القفز دلاليًا بين الحالات:

1. sandbox/chat artifact ليس Codespace artifact.
2. وجود الملف في Codespace لا يثبت أنه tracked في Git.
3. tracked لا يثبت committed.
4. committed لا يثبت pushed.
5. pushed لا يثبت verified حتى يتساوى Local HEAD وRemote HEAD وتتحقق الحالة المطلوبة.
6. sandbox links ليست دليل حفظ داخل المشروع.

### Evidence Receipts الإلزامية

- save claim: المسار، وفحص الوجود والمحتوى، وحالة tracking إذا كان الملف يجب أن يكون في Git، وحالة commit/push عند الحاجة.
- test claim: عدد الاختبارات وexit code.
- push claim: Local HEAD وRemote HEAD ونتيجة التطابق.
- audit/verdict claim: source artifact ومراجع الأدلة، مع حفظ التحليل المشتق منفصلًا أو إلحاقه بتمييز واضح لا يخلطه بالدليل الخام.
- Final GO لجولة كبيرة: Completion Verification مستقلة من Codespace.
- الطلب متعدد البنود: coverage لكل بند أصلي بقيمة واحدة من `VERIFIED / PARTIAL / NOT IMPLEMENTED / BLOCKED`.

عند غياب أي Evidence لازمة تكون النتيجة:

`HOLD — NOT VERIFIED`

ولا تُستبدل الأدلة بالذاكرة أو الاستنتاج.

### الانضباط والتناسب

- يطبق القرار كdiscipline داخل workflow وبقيد واحد في السجل وvalidator واختبارات صغيرة؛ لا ينشئ subsystem جديدة.
- لا تُحدّث Handoff أو Roadmap أو ADR بعد كل خطوة صغيرة. يكون التحديث عند milestone أو قرار معماري أو تغير حالة Stage.
- لا يغير هذا القرار Stage 5 ولا يبدأ production code لها.

### الإنفاذ

- `SC-COMPLETION-001` هو المعرف التنفيذي الدائم.
- يفشل validator مغلقًا عند حالة غير معتمدة أو receipt ناقصة أو رؤوس Git غير متطابقة أو audit provenance ناقص أو Final GO كبير بلا تحقق مستقل.
- تغطي negative tests الفروق بين generated/written/tracked/committed/pushed/verified، ومتطلبات test/push/audit/coverage.

### Rollback

يمكن عكس تعديل الـvalidator والسجل بcommit رجوع صريح، لكن يبقى القرار المعماري محفوظًا ويُوسم `SUPERSEDED` فقط بقرار مالك لاحق يحدد البديل. لا يؤدي rollback تقني إلى ادعاء أن السياسة ألغيت.

### Evidence State عند كتابة هذا القرار

- قرار المالك: `ADOPTED` بإفادة صريحة.
- ملفات الحزمة في مساحة المحادثة: `GENERATED` فقط.
- `WRITTEN_TO_CODESPACE / TRACKED / COMMITTED / PUSHED / VERIFIED`: `HOLD — NOT VERIFIED` حتى تصل Receipts من Codespace.
