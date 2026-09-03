# 02-SHUJAA_ACTIVE_ROADMAP.md

> **الصفة:** خارطة التنفيذ الرسمية النشطة لمشروع شجاع
> **الإصدار:** 1.3
> **آخر تحديث موثق:** 3 سبتمبر 2026 بعد Stage 8 Exit Gap Audit؛ Slice 8.1 محققة ومتحققة وملتزمة ومدفوعة، وStage 8 ما زالت غير مكتملة.
> **النطاق:** 19 مرحلة مترابطة بالاعتماديات، من Stage 0 إلى Stage 18

---

## CURRENT STATE MIRROR

> مرآة مختصرة فقط. الحالة التشغيلية وEvidence والبنود المفتوحة يملكها `SHUJAA_HANDOFF.md`.

<!-- SHUJAA_CURRENT_STATE_MIRROR_BEGIN -->
| الحقل | القيمة |
|---|---|
| CURRENT_STAGE | 8 |
| CURRENT_SLICE | 8.1 |
| SLICE_STATUS | VERIFIED |
| SLICE7_1_STATUS | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| SLICE7_2_STATUS | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| SLICE7_3_STATUS | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| STAGE7_STATUS | CLOSED_VERIFIED_COMMITTED_AND_SYNCED |
| STAGE7_ENTRY_GATE | GO |
| STAGE7_EXIT_GATE | GO |
| SLICE_7_1 | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| SLICE_7_2 | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| SLICE_7_3 | IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED |
| FIRST_ACTION | TASK_CANCEL |
| CURRENT_ACTION | STAGE8_EXIT_GAP_AUDIT_DOCUMENTED |
| RED_STARTED | YES |
| GREEN_STARTED | YES |
| PRODUCTION_STARTED | YES_FOR_SLICE8_1 |
| IMPLEMENTATION_STARTED | YES_FOR_SLICE8_1_COMMITTED_AND_SYNCED |
| TARGETED_EVIDENCE | SLICE8_1_TARGETED=53_PASSED; MIGRATED_LEGACY_NODES=11_PASSED; API_COMPOSITION_TARGETED=6_PASSED; TARGETED_FAILURES=0 |
| FULL_REGRESSION | FINAL_FULL_REGRESSION=736_COLLECTED_736_PASSED_0_FAILED_0_ERRORS; PRE_CORRECTION_FULL_REGRESSION=735_COLLECTED_723_PASSED_12_FAILED |
| IMPLEMENTATION_CHECKPOINT | 6609a9899c1ebcc7573c33b30fee64c8fb4fe159 |
| STAGE7_EXIT_GATE_CHECKPOINT | af94f932ae1eef9f0376f14001abe880ecbe633c |
| OTHER_STAGE7_SLICES | DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER |
| STAGE8_ENTRY_GATE_CONTRACT | SAVED_COMMITTED_AND_SYNCED |
| STAGE8_ENTRY_GATE | GO_TO_DESIGN_RESEARCH_ONLY |
| STAGE8_STATUS | IN_PROGRESS_SLICE8_1_VERIFIED_EXIT_GAPS_OPEN |
| STAGE8_STARTED | YES |
| FIRST_SLICE_STATUS | VERIFIED |
| FIRST_SLICE_STARTED | YES_RED_GREEN_TARGETED_VERIFY |
| FIRST_SLICE_EXACT_CONSUMER | TASK_CANCEL_LOCAL_PROCESS_CLEANUP_PATH_ONLY |
| FIRST_SLICE_RECOMMENDATION | ADOPTED_AS_SLICE8_1_CONTRACT_BOUNDARY |
| SLICE8_1_STATUS | VERIFIED |
| SLICE8_1_EXACT_CONSUMER | TASK_CANCEL_LOCAL_PROCESS_CLEANUP_PATH_ONLY |
| SLICE8_1_RED_STARTED | YES |
| SLICE8_1_GREEN_STARTED | YES |
| SLICE8_1_RED_EVIDENCE | SHA256=affdc17067938d7e74ab44c1b3359b7ed1daff56499e929cfad64ac8fa7ac341; FINAL_REGRESSION=736_COLLECTED_736_PASSED_0_FAILED_0_ERRORS |
| RED_GATE | PASS_CORRECTED |
| RED_AMENDMENT_REQUIRED | NO_COMPLETED |
| CONCURRENCY_MECHANISM | BOUNDED_LOCAL_ATOMIC_OWNERSHIP_CLAIM |
| BOUNDED_LOCAL_ATOMIC_OWNERSHIP_CLAIM | IMPLEMENTED_AND_VERIFIED |
| EXPLICIT_ADAPTER_WIRING | IMPLEMENTED_AND_VERIFIED_IN_APPS_API_APP |
| LEGACY_FIXTURES_MIGRATED | 11_PASSED |
| RED_ANTI_BYPASS | CORRECTED_AND_TARGETED_VERIFIED |
| API_COMPOSITION_TEST | ADDED_AND_PASSED |
| PRE_CORRECTION_FULL_REGRESSION | 735_COLLECTED_723_PASSED_12_FAILED |
| PRE_CORRECTION_BLOCKERS | ADDRESSED_AND_FINAL_REGRESSION_PASSED |
| SLICE8_1_IMPLEMENTATION_VERIFIED | YES |
| FINAL_VERIFY_GATE | PASS |
| FINAL_FULL_REGRESSION | 736_COLLECTED_736_PASSED_0_FAILED_0_ERRORS |
| FINAL_FULL_REGRESSION_DURATION | 16.61s |
| FINAL_FULL_REGRESSION_EXIT_CODE | 0 |
| RED_SHA256 | affdc17067938d7e74ab44c1b3359b7ed1daff56499e929cfad64ac8fa7ac341 |
| STATE_SYNC_REQUIRED_BEFORE_COMMIT | SATISFIED_FOR_SLICE8_1_CLOSURE_COMMIT |
| IMPLEMENTED_GUARANTEE | At most one admitted local termination attempt per exact process-ownership generation among concurrent in-process callers. |
| NON_GUARANTEES | EXACTLY_ONCE=NO; DISTRIBUTED_COORDINATION=NO; RESTART_DURABILITY=NO; CRASH_RECOVERY=NO; SAFE_AUTOMATIC_RETRY_ON_UNKNOWN_OUTCOME=NO |
| PRODUCTION_COMPOSITION_WIRING | VERIFIED |
| BOUNDED_LOCAL_ATOMIC_CLAIM_FINALIZE_QUARANTINE | VERIFIED |
| LEGACY_FALLBACK | ABSENT |
| STAGE5_STAGE7_REGRESSIONS | PASS |
| PREVIOUS_STATE_SYNC | PASS |
| SLICE8_1_CLOSURE | IMPLEMENTED_AND_VERIFIED_COMMITTED_AND_SYNCED |
| SLICE_CLOSED | YES |
| VERIFY_FINALIZED | YES |
| CURRENT_IMPLEMENTATION_COMMIT | bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239 |
| CURRENT_IMPLEMENTATION_PUSH | VERIFIED_AT_bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239 |
| COMMIT | YES_FOR_SLICE8_1_AT_bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239 |
| PUSH | YES_FOR_SLICE8_1_REMOTE_VERIFIED_AT_bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239 |
| SAFETY_CLEANUP_AUDIT_DECISION | CONTAINMENT_PRESERVING_EXECUTION_WITH_STRUCTURED_AUDIT_FAILURE |
| STAGE8_EXIT_ACCOUNTABILITY | MANDATORY |
| STAGE8_CLOSURE | BLOCKED_PENDING_FINAL_EXIT_DISPOSITIONS_WITH_IMPLEMENTATION_AND_VERIFICATION_EVIDENCE |
| SLICE8_2_AUTHORIZED | NO |
| NEXT_DIRECTION | LOCAL_PROCESS_LAUNCH_CONTAINMENT |
| NEXT_DIRECTION_STATUS | APPROVED_FOR_STUDY_ONLY |
| NEXT_DIRECTION_SCOPE | SANDBOX_ISOLATION_AND_RESOURCE_LIMITS_AT_LOCAL_PROCESS_LAUNCH_ONLY |
| NEXT_DIRECTION_FINAL_CONTRACT | NO |
| NEXT_DIRECTION_RED | NO |
| NEXT_DIRECTION_GREEN | NO |
| SANDBOX_ISOLATION_CURRENT_STATUS | OPEN_REQUIRED |
| SANDBOX_ISOLATION_FINAL_DISPOSITION_RECORDED | NO |
| SANDBOX_ISOLATION_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED |
| RESOURCE_LIMITS_CURRENT_STATUS | OPEN_REQUIRED |
| RESOURCE_LIMITS_FINAL_DISPOSITION_RECORDED | NO |
| RESOURCE_LIMITS_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED |
| SECRETS_SAFETY_CURRENT_STATUS | PARTIAL_CANCEL_PATH_ONLY |
| SECRETS_SAFETY_FINAL_DISPOSITION_RECORDED | NO |
| SECRETS_SAFETY_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED |
| SAFE_PAUSE_RESUME_CURRENT_STATUS | OPEN_REQUIRED |
| SAFE_PAUSE_RESUME_FINAL_DISPOSITION_RECORDED | NO |
| SAFE_PAUSE_RESUME_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED | IMPLEMENTED_AND_VERIFIED |
| THREAT_MODEL_DECISION_STATUS | OWNER_APPROVED_FOR_CURRENT_LOCAL_PROCESS_LAUNCH_CONTAINMENT_SCOPE |
| WORKLOAD_TRUST | SEMI_TRUSTED_RUNTIME_WITH_UNTRUSTED_INPUTS_AND_POTENTIALLY_COMPROMISED_TOOLS |
| USERSPACE_MALICIOUS_OR_COMPROMISED_BEHAVIOR | IN_SCOPE |
| ARBITRARY_HOSTILE_USER_CODE | OUT_OF_CURRENT_SCOPE |
| KERNEL_ESCAPE_RESISTANCE | NOT_CLAIMED |
| FILESYSTEM_POLICY | READ_MINIMUM_REQUIRED_WRITE_DEDICATED_PER_EXECUTION_RUNTIME_PATHS_ONLY |
| HOME_DIRECTORY_ACCESS | DENIED_BY_DEFAULT |
| SSH_AND_GIT_CREDENTIAL_ACCESS | DENIED |
| SYSTEM_WRITABLE_PATH_ACCESS | DENIED_BY_DEFAULT |
| NETWORK_POLICY | OUTBOUND_ONLY_WHEN_EXPLICITLY_REQUIRED_NO_INBOUND_BY_DEFAULT |
| EGRESS_ALLOWLIST_GUARANTEE | NOT_CLAIMED_IN_CURRENT_SCOPE |
| TARGET_SECURITY_RUNTIME | MANAGED_LINUX |
| CODESPACES_ROLE | DEVELOPMENT_NOT_REFERENCE_SECURITY_RUNTIME |
| EXTERNAL_RUNTIME_DEPENDENCY | ALLOWED_IF_PINNED_REPLACEABLE_AND_BEHIND_SHUJAA_CONTRACT |
| PROCESS_TREE_CONTAINMENT | REQUIRED |
| RESOURCE_LIMIT_DIMENSIONS | CPU,MEMORY,PIDS,FDS,OUTPUT,WALL_CLOCK |
| RESOURCE_LIMIT_VALUES | CONFIGURABLE_NOT_ARCHITECTURALLY_FROZEN |
| FUTURE_HOSTILE_CODE_TRIGGER | REOPEN_THREAT_MODEL_AND_STRONGER_ISOLATION_RESEARCH |
| PLATFORM_DECISION_STATUS | NOT_FINALIZED |
| CONTAINMENT_MECHANISM_DECISION_STATUS | NOT_ADOPTED |
| CONTAINMENT_CONTRACT_FROZEN | NO |
| REFERENCE_SECURITY_ENVIRONMENT_PROVISIONED | NO |
| EXTERNAL_COST_AUTHORIZED | NO |
| PRIMARY_FEASIBILITY_CANDIDATE | SYSTEMD_TRANSIENT_UNIT_WITH_EXPLICIT_HARDENING_AND_CGROUP_V2 |
| PRIMARY_CANDIDATE_STATUS | RECOMMENDED_FOR_FEASIBILITY_NOT_ADOPTED |
| BACKUP_CANDIDATE | ROOTLESS_OCI |
| BACKUP_CANDIDATE_STATUS | RESERVE_ALTERNATIVE_NOT_ADOPTED |
| RAW_NAMESPACES_CGROUPS_PYTHON_IMPLEMENTATION | NOT_RECOMMENDED |
| RESEARCH_SATURATION_GENERAL | NO |
| RESEARCH_SATURATION_CURRENT_SEMI_TRUSTED_SHARED_KERNEL_SCOPE | YES |
| STRONGER_HOSTILE_CODE_ISOLATION_RESEARCH_TRIGGERED | NO |
| RUNTIME_KILL_SWITCH_PRIMITIVE | IMPLEMENTED_AND_VERIFIED |
| FULL_SYSTEM_OR_HIERARCHICAL_KILL_SWITCH | NOT_CLAIMED |
| RESEARCH_GATE_REQUIRED | CONDITIONAL |
| RESEARCH_GATE_TRIGGERED | NO |
| EXTERNAL_RESEARCH_RUN | NO |
| NEXT | WAIT_FOR_OWNER_STAGE8_REFERENCE_SECURITY_RUNTIME_ENVIRONMENT_DECISION |
<!-- SHUJAA_CURRENT_STATE_MIRROR_END -->

### Stage 8 entry boundary

- Stage 8 في التنفيذ، وحالة Slice 8.1 هي `VERIFIED`؛ الشريحة محققة ومتحققة وملتزمة ومدفوعة عند `bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239`، ولا يعني ذلك اكتمال Stage 8.
- لا توجد Slice 8.2 معتمدة. Stage 8 غير مكتملة وإغلاقها `BLOCKED` حتى تحصل التزامات الخروج المفتوحة على dispositions نهائية مدعومة بالتنفيذ والتحقق.
- Sandbox/Isolation وResource Limits وsafe runtime-specific pause/resume ما زالت `OPEN_REQUIRED`؛ Secrets safety هي `PARTIAL_CANCEL_PATH_ONLY`. لا تسجل أي منها حاليًا `IMPLEMENTED_AND_VERIFIED` ولا final disposition.
- عقد Slice 8.1 المعدل لمسار `task.cancel` المحلي محفوظ، وRED/GREEN والتصحيحات الموجهة وFinal Verify مكتملة.
- bounded local atomic claim/finalize/quarantine وProduction composition wiring منفذة ومتحققة، والـ11 legacy fixtures وanti-bypass واختبار composition/API ناجحة، ولا توجد legacy fallback في المسار المرحّل.
- الأدلة الحالية: `53 passed` لملف Slice، و`11 passed` للعقد المهاجرة، و`6 passed` لـAPI/composition، مع `TARGETED_FAILURES=0`.
- Full Regression السابقة `735 collected / 723 passed / 12 failed` تاريخية قبل التصحيحات؛ Final Regression نجحت: `736 collected / 736 passed / 0 failed / 0 errors` خلال `16.61s` مع exit code=`0`، وتشمل نجاح Stage 5 وStage 7 regressions.
- State Sync السابقة نجحت قبل إغلاق Slice 8.1، وCommit/Push مثبتان عند `bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239` مع تطابق HEAD والـremote الفعلي.
- `At most one admitted local termination attempt per exact process-ownership generation among concurrent in-process callers.` ولا يضمن ذلك exactly-once أو distributed coordination أو restart durability أو crash recovery أو safe automatic retry عند outcome مجهولة.
- المستهلك الدقيق هو `TASK_CANCEL_LOCAL_PROCESS_CLEANUP_PATH_ONLY`؛ وتبقى timeout/error/startup/shutdown/owner-conflict خارج هذه الشريحة ومجرودة ومؤجلة صراحة.
- Safety-cleanup Audit semantics لهذه الشريحة هي `CONTAINMENT_PRESERVING_EXECUTION_WITH_STRUCTURED_AUDIT_FAILURE` مع بقاء pre-action evidence fail-closed وفق Stage 7.
- Stage 8 Exit Accountability إلزامية، ولا تقليص أو تأجيل صامت لالتزامات الخارطة.
- أصغر اتجاه تالٍ معتمد للدراسة هو `LOCAL_PROCESS_LAUNCH_CONTAINMENT`، ويقتصر على Sandbox/Isolation وResource Limits عند launch لعملية محلية؛ لا عقد نهائي ولا RED ولا GREEN ولا Slice 8.2 معتمدة.
- Threat Model معتمدة من المالك للنطاق الحالي شبه الموثوق؛ اختيار containment mechanism غير معتمد. systemd transient unit مع hardening صريح وcgroup v2 مرشح feasibility أول فقط، وRootless OCI بديل احتياطي، ولا يُدعى تنفيذ أو تحقق أي منهما.

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

1. Git/Codespace لحقيقة Runtime.
2. قرار مالك المشروع الأحدث.
3. `SHUJAA_HANDOFF.md` للحالة التشغيلية الحالية.
4. هذه الخارطة لترتيب المراحل ومرآة الحالة المختصرة.
5. سجل ADR للقرارات طويلة العمر فقط.
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
| 5 | Event Model + Audit Foundation | `VERIFIED COMPLETE — LOCAL/MOCK SCOPE` | Event/Audit منفصلان ومختبران مع Local stores خلف Protocols. |
| 6 | Catalog Foundation | `VERIFIED COMPLETE — LOCAL/IN-MEMORY CATALOG & EXPLICIT BINDING FOUNDATION` | Capability Catalog بهوية وإصدار وDescriptor وLifecycle واعتماديات وصفية، وDependency Graph وimpact/candidate read models، وExplicit Binding validation/registry محلية؛ دون automatic selection أو Policy Enforcement أو Runtime integration. |
| 7 | Policy & Access Control | `VERIFIED COMPLETE — LOCAL ACTION-SPECIFIC AUTHORIZATION FOUNDATION AND CURRENT COMMAND ENFORCEMENT` | إنفاذ fail-closed لمسار `task.cancel` الحالي ومساري `work.submit` الحاليين، مع prerequisite مستقلة وقابلة للاستهلاك لـpause/resume/terminate؛ دون Security Model عام أو Runtime integration. |
| 8 | Runtime Isolation & Safety | `IN PROGRESS — SLICE 8.1 VERIFIED; EXIT GAPS OPEN` | Slice 8.1 ملتزمة ومزامنة؛ لا توجد Slice 8.2 معتمدة، وإغلاق المرحلة محجوب حتى final dispositions مدعومة بالتنفيذ والتحقق. اتجاه الدراسة التالي فقط: `LOCAL_PROCESS_LAUNCH_CONTAINMENT`. |
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
**الحالة:** `VERIFIED COMPLETE — LOCAL/MOCK SCOPE`
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

أغلقت Stage 5 بعد Slice 5.6. تبقى Stage 6 `PLANNED` حتى Entry Gate مستقل.

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
- `SC-TOOL-001`: يسمح بـ`rg/ripgrep` للبحث المحلي Read-only داخل مساحة العمل ونطاق المهمة فقط؛ يمنع استهداف الأسرار وخيار `--pre`، وتبقى Data Egress Policy منفصلة.
- `SC-OUTPUT-001`: المخرجات الضخمة إلى ملف قابل للتنزيل.
- `SC-OWNER-001`: لا تغيير لمسار المالك بلا إذن.
- `SC-SAVE-001`: لا ادعاء حفظ بلا تحقق موثق.

### أثرها على Stage 5

`AUDIT_01=COMPLETE`. سجل القيود والـvalidator واختباراته ملتزمة ومرفوعة في `4f15ca35b6e6c3f4ec4e0477019992aed4ea7519`؛ الاختبارات الموجهة `13 passed` والـbaseline `224 passed`. حكم التوافق محفوظ في artifact مستقل، وStage 5 لم يبدأ.

---

## 17) Stage 5 Exit Gate — إغلاق موثق

**التاريخ:** 23 أغسطس 2026
**الحالة:** `VERIFIED COMPLETE — LOCAL/MOCK SCOPE`
**مرجع كود الإغلاق:** `afcba30fe74d6d9e6e28290f9868cb448633c593`

- الاختبارات: `10 new + 126 affected + 367 full`.
- Event وAudit منفصلان وخلف Protocols مستقلة.
- lifecycle emission من نقاط السلطة المركزية.
- Privacy وfailure وrace وintegrity paths مختبرة.
- مراجعة bypass paths: `PASSED`.
- لا اقتران مباشر بمزود أو Framework داخل Event/Audit Core.

| القدرة المرحّلة | المرحلة |
|---|---:|
| Catalog وResolver/Bindings | 6 |
| Policy Enforcement وApprovals | 7 |
| Durable Journal وRecovery | 9 |
| Metrics وLogs وTraces وAlerts | 10 |
| Production storage وdistributed ordering وtamper resistance | 16 |

أُغلقت Stage 6 بعد اكتمال Slices 6.1–6.7 ضمن نطاق Local/In-Memory؛ Slice 6.8 مؤجلة لعدم وجود مستهلك وظيفي مباشر وليست فجوة خروج.

---


<!-- STAGE6_SLICE6_1_CONTRACT_BEGIN -->
## Stage 6 — Catalog Foundation

### Slice 6.1 — Capability Catalog Foundation

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

**الغرض:** إنشاء أساس عام لـCapability Catalog يملكه شجاع، يعمل Local/In-Memory فقط، دون تكامل مع Runtime في هذه الشريحة.

#### CapabilityAssetType

القيم الرسمية المغلقة: `AGENT`، `TOOL`، `SKILL`، `MODEL`، `CONNECTOR`، `RUNTIME`، `WORKFLOW_ENGINE`.

لا توجد `OTHER`، ولا أنواع نصية حرة، ولا أنواع مرتبطة بمزود أو منصة.

#### CapabilityLifecycle

القيم الرسمية المغلقة: `SANDBOX`، `STAGING`، `ACTIVE`، `DEPRECATED`، `RETIRED`، `QUARANTINED`.

Lifecycle وصفية فقط، ولا تنفذ انتقالات أو سلوكًا تشغيليًا في Slice 6.1.

#### CapabilityDescriptor والهوية

الحقول الوحيدة: `asset_id`، `version`، `asset_type`، `capabilities`، `lifecycle`، `dependency_asset_ids`، `provenance`، `risk_tier`، `required_permissions`.

الهوية الدقيقة هي `(asset_id, version)`.

- `asset_id` و`version` required ومن نوع `str`.
- يرفض الفارغ وwhitespace-only وleading/trailing whitespace.
- الهوية case-sensitive.
- `version` opaque، بلا SemVer وبلا latest ضمني.
- `provenance` required ويخضع لقواعد النص نفسها.
- `risk_tier` قد يكون `None`؛ وإلا يخضع لقواعد النص نفسها، وهو declaration-only بلا Policy semantics.

#### Canonical collections

- عناصر `capabilities` و`required_permissions` نصوص صالحة؛ canonical item = `strip + casefold`.
- التكرارات الدلالية فيها تنتج `SCHEMA_REJECTED`، وتخزن كـtuple حتمية مرتبة lexicographically.
- عناصر `dependency_asset_ids` تتبع قواعد `asset_id`، وتبقى case-sensitive، وتُرفض تكراراتها، وتخزن كـtuple حتمية مرتبة.
- ترتيب الإدخال لا يحمل معنى دلاليًا.

#### Registration contract

النتائج المنظمة: `REGISTERED`، `IDEMPOTENT_REPLAY`، `IDENTITY_CONFLICT`، `SCHEMA_REJECTED`.

- هوية جديدة صالحة → `REGISTERED`.
- الهوية نفسها والمحتوى القياسي نفسه → `IDEMPOTENT_REPLAY`.
- الهوية نفسها مع اختلاف دلالي → `IDENTITY_CONFLICT`.
- Descriptor غير صالح → `SCHEMA_REJECTED`.
- التعارض لا يغير السجل الفائز، والمرفوض لا يُخزن.
- المساواة الدلالية تقارن جميع الحقول بعد canonicalization.

#### Atomicity and concurrency

- يمتلك Catalog حدود check-and-write ذرية واحدة بلا caller locking.
- المتطابقون المتزامنون: فائز واحد `REGISTERED` والبقية `IDEMPOTENT_REPLAY`.
- المختلفون بالهوية نفسها: فائز واحد والبقية `IDENTITY_CONFLICT`.
- عدة متنافسين يتركون سجلًا فائزًا واحدًا فقط لكل `(asset_id, version)`.
- تغطى هذه الحالات من RED suite الأولى.

#### Read contract

```text
get(asset_id, version) -> CapabilityDescriptor | None
list() -> tuple[CapabilityDescriptor, ...]
find_by_capability(capability, *, lifecycle_states) -> tuple[CapabilityDescriptor, ...]
```

- `get` دقيق، بلا latest ضمني.
- `list` مرتبة حسب `asset_id` ثم `version`؛ ترتيب version للعرض فقط لا للأحدثية.
- capability match دقيق بعد canonicalization.
- `lifecycle_states` مطلوب؛ الفارغ يعيد tuple فارغة؛ لا `ACTIVE` ضمني.
- لا ranking ولا fuzzy matching، والنتائج immutable snapshots.

#### Dependency semantics

`dependency_asset_ids` declaration-only: لا existence validation، ولا traversal أو graph أو cycle detection، ولا dependency-version resolution، ولا Resolver/Binding.

#### خارج النطاق

update/delete، lifecycle transitions، dependency graph/resolution، Resolver/Binding، adapter selection، Policy/permission enforcement، Manager، Dispatcher، AgentRegistry، Event/Audit، MCP/Skills، model providers، n8n/LangGraph/Hermes/platform integrations، distributed storage، وproduction database.

#### نطاق ملفات التنفيذ اللاحق

لا ينشئ هذا التحديث أي ملف تنفيذ أو اختبار. يبقى النطاق اللاحق فقط:

- `core/capabilities/__init__.py`
- `core/capabilities/models.py`
- `core/capabilities/contracts.py`
- `core/capabilities/catalog.py`
- `tests/test_stage6_capability_catalog_foundation.py`

#### أدلة الإغلاق

- Implementation commit: `fe3c97f96e6473791236d1804b5ab7f1d2520b2b`.
- Pre-reconciliation verified checkpoint: `988a82234cf8662e90a262e8baac8494ef69bf97`.
- Slice 6.1 targeted suite: `74 passed`.
- Full regression: `441 passed`.
- `git diff --check`: ناجح عند checkpoint.
- Local وremote متطابقان، وشجرة العمل نظيفة عند checkpoint.
- لم تُعد الاختبارات في دفعة المصالحة التوثيقية لعدم وجود Trigger.
- تبقى كل عناصر «خارج النطاق» أعلاه خارج Slice 6.1.
- عقد Slice 6.2 محفوظ ومعتمد من المالك؛ الدفعة التالية RED Entry Gate مستقل، ولا يبدأ production code قبل إثبات RED وموافقة المالك على GREEN.

<!-- STAGE6_SLICE6_1_CONTRACT_END -->

<!-- STAGE6_SLICE6_2_CONTRACT_BEGIN -->
## Slice 6.2 — Capability Dependency Graph Read Model

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

### الغرض

إضافة Read Model محلي/In-Memory وحتمي لعلاقات اعتماد القدرات المسجلة، مبني فوق ناتج Slice 6.1، ليكون أساسًا لاحقًا لـimpact analysis دون تنفيذ impact analysis الكامل في هذه الشريحة.

### الحدود والسلطة

- شجاع يملك العقود والنماذج والتنفيذ؛ لا اعتماد على مزود أو Framework خارجي.
- Graph للقراءة فقط ولا تعدّل Catalog أو Descriptor.
- لا Runtime integration، ولا persistence، ولا distributed graph، ولا lifecycle transitions، ولا Resolver/Binding، ولا removal enforcement.
- لا transitive dependents أو transitive impact analysis في Slice 6.2.

### هوية العقد

- هوية descriptor الدقيقة هي `(asset_id, version)`.
- لأن `dependency_asset_ids` غير مرتبطة بإصدار، تُحل علاقات الاعتماد على مستوى `asset_id`.
- تمثل النتائج التي تشير إلى المصدر هويته الدقيقة `(asset_id, version)`، بينما تمثل الدورة مجموعة `asset_id` دورية.

### Snapshot معزولة

- تُبنى Graph من tuple ثابتة من `CapabilityDescriptor`، مأخوذة من `catalog.list()` أو مدخلة مباشرة بالقيمة نفسها.
- تنسخ Graph المدخل وتبني فهارسها الخاصة غير القابلة للتعديل.
- لا تحتفظ بمرجع حي إلى Catalog، ولا تصل إلى lock الخاص به، ولا تستدعيه بعد البناء.
- التسجيلات اللاحقة في Catalog لا تغيّر Graph سابقة؛ يلزم إنشاء Graph جديدة لرؤية Snapshot أحدث.

### العقود العامة المقترحة

- `CapabilityIdentity = tuple[str, str]`.
- `UnresolvedDependency`: يحتوي `source_asset_id` و`source_version` و`dependency_asset_id`.
- `DependencyCycle`: يحتوي `asset_ids: tuple[str, ...]` تمثل SCC دورية واحدة بترتيب حتمي.
- `CapabilityDependencyGraphProtocol` يعرّف واجهة القراءة.
- `InMemoryCapabilityDependencyGraph` تنفيذ Local/In-Memory.

الاستعلامات:

- `direct_dependencies(asset_id, version) -> tuple[str, ...] | None`
  - `None`: هوية المصدر غير موجودة.
  - `()`: المصدر موجود بلا اعتماديات.
  - وإلا tuple مرتبة من dependency asset IDs المباشرة.
- `direct_dependents(dependency_asset_id) -> tuple[CapabilityIdentity, ...]`
  - يعيد هويات المصادر الدقيقة التي تشير مباشرة إلى asset ID المطلوب.
  - لا يشترط أن يكون asset ID المطلوب مسجلًا؛ عدم وجود مراجع يعيد `()`.
- `unresolved_dependencies() -> tuple[UnresolvedDependency, ...]`.
- `dependency_cycles() -> tuple[DependencyCycle, ...]`.

### معنى resolved وunresolved

- dependency تكون resolved إذا وُجد أي descriptor مسجل يحمل `asset_id` الهدف، بغض النظر عن version أو lifecycle.
- لا يوجد اختيار latest، ولا version binding، ولا lifecycle filtering في هذه الشريحة.
- إذا لم يوجد أي descriptor بذلك `asset_id`، تسجل نتيجة unresolved لكل هوية مصدر دقيقة تشير إليه.
- النتائج تزيل التكرار وتُرتب حتميًا حسب هوية المصدر ثم dependency asset ID.

### الدورات — SCC فقط

- لا تُعدّد جميع المسارات الدورية الممكنة.
- تُبنى دورة واحدة لكل Strongly Connected Component دورية على مستوى `asset_id`.
- SCC متعددة العناصر تعد دورة.
- SCC أحادية العنصر تعد دورة فقط عند وجود self-loop.
- تُدمج الحواف المتكررة الناتجة من إصدارات متعددة قبل حساب SCC.
- الحواف unresolved لا تدخل SCC لأنها لا تملك عقدة هدف مسجلة.
- ترتب `asset_ids` داخل كل دورة، وترتب سجلات الدورات lexicographically لضمان نتيجة ثابتة وغير مكررة.

### التطبيع والتحقق والحتمية

- تستخدم استعلامات الهوية قواعد Slice 6.1 نفسها؛ لا fuzzy أو substring أو prefix matching.
- المدخلات غير الصالحة تتبع TypeError/validation semantics الموجودة في عقود 6.1 بدل إنشاء سياسة موازية.
- كل المخرجات tuples immutable ومرتبة حتميًا.
- لا تُكشف dict أو set داخلية قابلة للتعديل.
- القراءة بعد البناء لا تحتاج lock الخاص بالCatalog.

### Invariants البناء والحالات الحدّية

- Snapshot الفارغة صالحة: `direct_dependencies` لهوية صحيحة يعيد `None`، و`direct_dependents` و`unresolved_dependencies` و`dependency_cycles` تعيد `()`.
- tuple المدخلة مباشرة يجب أن تحقق canonicalization وidentity uniqueness invariants نفسها التي يفرضها Catalog في Slice 6.1.
- تكرار الهوية الدقيقة نفسها `(asset_id, version)` مدخل غير صالح ويرفع `ValueError`؛ لا silent merge ولا last-write-wins.
- بناء الفهارس وحساب SCC يجب أن يكونا `O(V + E)` قبل كلفة الترتيب الحتمي؛ يُمنع تعداد المسارات أو الدورات الممكنة.

### ملفات التنفيذ المتوقعة

- `core/capabilities/models.py`
- `core/capabilities/contracts.py`
- `core/capabilities/dependency_graph.py`
- `core/capabilities/__init__.py`
- `tests/test_stage6_capability_dependency_graph.py`

### بوابة RED ومعايير القبول

يجب أن تثبت RED المستقلة قبل GREEN:

1. Snapshot isolation وعدم الاحتفاظ بمرجع Catalog حي.
2. التفريق بين المصدر غير الموجود والمصدر بلا dependencies.
3. direct dependencies/dependents لكل الإصدارات وبترتيب حتمي.
4. resolved بأي إصدار دون latest/lifecycle/version binding.
5. unresolved بهوية المصدر الدقيقة.
6. SCC متعددة العناصر، وself-loop، وعدم التكرار أو تعداد كل دورة ممكنة.
7. استبعاد الحواف unresolved من SCC.
8. immutability وعدم تسريب المجموعات الداخلية.
9. عدم إضافة transitive impact أو enforcement أو Runtime/persistence.
10. Snapshot الفارغة ونتائجها المحددة.
11. رفض الهوية الدقيقة المكررة دون silent merge.
12. عدم تعداد المسارات/الدورات، ومراجعة حد البناء وSCC كـ`O(V + E)` قبل الترتيب.
13. نجاح اختبارات Slice 6.1 المتأثرة فقط عند وجود Trigger، ثم full regression في Exit Gate.

### أدلة الإغلاق

- Implementation commit: `683625b9c64d21b73a176928e3f19f7ddfd30e93`.
- RED: `25 failed` للأسباب المقصودة.
- GREEN: `25 targeted passed` و`74 affected passed`.
- Full regression: `466 passed`؛ failures/errors/skipped = `0/0/0`.
- `git diff --check`: ناجح، وLocal HEAD = Remote HEAD بعد push.
- بقي النطاق Local/In-Memory وRead-only وفق العقد، دون أي عنصر من خارج النطاق.

### الإجراء التالي

Slice 6.2 مغلقة ومتحققة. عقد Slice 6.3 محفوظ ومعتمد؛ الدفعة التالية RED Entry Gate مستقل، ولا يبدأ production code قبل إثبات RED وموافقة المالك على GREEN.

<!-- STAGE6_SLICE6_2_CONTRACT_END -->

<!-- STAGE6_SLICE6_3_CONTRACT_BEGIN -->
## Slice 6.3 — Capability Dependency Impact Read Model

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

### الغرض

إضافة استعلام Local/In-Memory وحتمي فوق Dependency Graph في Slice 6.2 يعيد الهويات الدقيقة للقدرات المتأثرة **احتماليًا** بصورة مباشرة أو غير مباشرة بتغيّر asset ID، دون ادعاء impact تشغيلي قطعي قبل وجود version binding.

### العقد العام

```python
potential_transitive_dependents(
    dependency_asset_id: str,
) -> tuple[CapabilityIdentity, ...]
```

- يضاف الاستعلام إلى `CapabilityDependencyGraphProtocol` و`InMemoryCapabilityDependencyGraph`؛ لا ينشأ Graph موازٍ ولا Snapshot ثانية.
- يبقى الإدخال `asset_id` بلا version، وتبقى النتائج هويات مصادر دقيقة `(asset_id, version)`.
- تستخدم validation semantics نفسها التي يستخدمها `direct_dependents()` في Slice 6.2.

### دلالة potential والانتشار بين الإصدارات

- النتيجة محافظة وتمثل **potential impact** فقط، لأن dependency declarations غير مرتبطة بإصدار ولا يوجد Resolver/Binding بعد.
- يدرج في النتيجة فقط الإصدار الذي أعلن dependency فعلًا.
- بعد إدراج هوية المصدر الدقيقة، يستخدم `asset_id` لذلك المصدر كنقطة انتشار إلى المستوى الأعلى.
- إذا أعلن إصدار واحد من asset اعتمادًا ولم تعلنه إصداراته الأخرى، فلا تدرج الإصدارات الأخرى بسبب تلك الحافة، لكن قد تظهر مصادر أعلى تعتمد على asset ID للمصدر؛ وهذا سبب وصف النتيجة بأنها potential.
- lifecycle وrisk tier وrequired permissions لا تدخل في الحساب.

### الهدف المفقود واستبعاد الهدف

- لا يشترط أن يكون `dependency_asset_id` الهدف مسجلًا؛ declarations التي تشير إلى هدف مفقود تدخل التحليل المباشر والمتعدي.
- تستبعد من النتيجة كل `CapabilityIdentity` يكون `asset_id` لها مساويًا للهدف، مهما كان version.
- يبدأ traversal من asset ID الهدف وتُعالج reverse adjacency الخاصة به مرة واحدة.
- إذا أعادت cycle الوصول إلى الهدف، فلا يضاف إلى النتيجة ولا يعاد توسيعه؛ يبقى الهدف visited منذ البداية، وبذلك لا ينكسر traversal ولا ينشأ loop.
- كشف الدورات وتمثيل SCC يبقيان من اختصاص `dependency_cycles()` في Slice 6.2؛ استعلام 6.3 لا يعيد cycles أو paths.

### Snapshot والفهارس والتعقيد

- تبني Snapshot معزولة reverse adjacency داخلية مرة واحدة عند إنشاء Graph، أو تعيد استخدام الفهرس الداخلي المعزول الموجود إن كان يحقق العقد.
- لا يعاد مسح جميع descriptors عند كل مستوى من traversal، ولا يحتفظ التنفيذ بمرجع حي إلى Catalog أو lock الخاص به.
- traversal تكراري لا recursive، ويستخدم `visited asset IDs` لمنع إعادة العمل والدوران.
- تعقيد traversal للاستعلام هو `O(Vr + Er)` للعقد والحواف القابلة للوصول، ويضاف حتى `O(R log R)` لترتيب `R` نتيجة ترتيبًا حتميًا.
- لا تكشف reverse adjacency أو visited sets أو أي collection داخلية قابلة للتعديل.

### الحتمية وعدم القابلية للتعديل

- تزيل النتائج التكرار وتُرتب lexicographically حسب `(asset_id, version)`.
- النتيجة tuple immutable، ولا تتغير Graph القديمة بتسجيلات Catalog اللاحقة.
- Snapshot الفارغة والهدف بلا dependents يعيدان `()`.

### خارج النطاق

- definite runtime impact أو severity أو explanations أو path enumeration.
- removal/retirement enforcement، وupdate/delete، وlifecycle transitions.
- version selection أو latest semantics أو version constraints.
- Resolver/Binding أو fallback/rollback selection.
- Policy/permission enforcement وStage 7 Access Graph.
- Runtime adapters أو Manager/Dispatcher أو persistence أو distributed graph.
- لا يثبت العقد ترتيب الشرائح التالية؛ أي ترتيب لاحق `CANDIDATE DIRECTION` فقط ويعاد حسمه عبر `NEXT_SLICE_DISCOVERY` بعد إغلاق 6.3.

### ملفات التنفيذ المتوقعة

- `core/capabilities/contracts.py`
- `core/capabilities/dependency_graph.py`
- `tests/test_stage6_capability_dependency_impact.py`
- يعدل اختبار scope في Slice 6.2 بالحد الأدنى للسماح بالاستعلام الجديد، دون إضعاف منع العمليات المتعدية الأخرى أو عمليات mutation.

### بوابة RED ومعايير القبول

يجب أن تثبت RED المستقلة قبل GREEN:

1. signature وإضافة الاستعلام العام فقط إلى Protocol والتنفيذ الحاليين.
2. Snapshot فارغة، وهدف بلا dependents، وهدف غير مسجل.
3. direct وmulti-hop potential dependents.
4. دقة هوية المصدر عند تعدد الإصدارات، وعدم إدراج إصدار لم يعلن الحافة.
5. الانتشار للأعلى عبر `asset_id` بعد إدراج الإصدار المعلن فقط.
6. استبعاد جميع هويات asset ID الهدف عبر كل versions.
7. cycles وself-loop تنتهي دون تكرار أو إعادة الهدف، مع بقاء SCC من اختصاص 6.2.
8. deduplication والترتيب الحتمي والـimmutability.
9. تجاهل lifecycle وrisk وpermissions.
10. Snapshot isolation وعدم استخدام Catalog أو lock بعد البناء.
11. deep chain يثبت traversal تكراريًا دون recursion failure.
12. فحص بنيوي يثبت reverse adjacency مبنية مرة واحدة وعدم rescanning للـdescriptors في كل مستوى؛ لا يعتمد الحكم على timing test هش.
13. عدم إضافة paths أو severity أو enforcement أو Resolver/Binding أو Runtime/persistence.
14. تشغيل اختبارات Slice 6.2 المتأثرة بسبب تغيّر الـAPI، ثم full regression في Exit Gate.

### أدلة الإغلاق

- Implementation commit: `1d20fced920cdff4b413392d3df78f27b1b8b1e4`.
- RED: `14 failed` للأسباب المقصودة.
- GREEN: `14 targeted passed` و`25 affected passed`.
- Full regression: `480 passed`؛ failures/errors/skipped = `0/0/0`.
- `git diff --check`: ناجح، وLocal HEAD = Remote HEAD بعد push.
- بقي التنفيذ Local/In-Memory وRead-only وضمن الحدود المعتمدة.

### الإجراء التالي

Slice 6.3 مغلقة ومتحققة. عقد Slice 6.4 محفوظ ومعتمد؛ الدفعة التالية RED Entry Gate مستقل، ولا يبدأ production code قبل إثبات RED وموافقة المالك على GREEN.
<!-- STAGE6_SLICE6_3_CONTRACT_END -->

<!-- STAGE6_SLICE6_4_CONTRACT_BEGIN -->
## Slice 6.4 — Capability Dependency Resolution Candidates Read Model

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

### الغرض

إضافة Read Model محلي/In-Memory وحتمي يعرض هويات الإصدارات المسجلة التي يمكن أن تكون مدخلات محتملة لـResolver مستقبلي لكل dependency معلنة، دون اختيار إصدار أو اعتماد قرار تشغيل.

كلمة `Resolution` هنا تعني **resolution candidates فقط**؛ لا تعني أن Slice 6.4 تنفذ Resolver أو Binding أو قرارًا معتمدًا.

### العقد العام

- `DependencyCandidateDisposition` قيمه المغلقة: `UNRESOLVED` و`UNIQUE` و`MULTIPLE_CANDIDATES`.
- `DependencyResolutionCandidates` سجل immutable يحتوي فقط:
  - `dependency_asset_id: str`
  - `candidate_identities: tuple[CapabilityIdentity, ...]`
  - `disposition: DependencyCandidateDisposition`
- يضاف إلى `CapabilityDependencyGraphProtocol` والاستدعاء المحلي:

```python
dependency_resolution_candidates(
    asset_id: str,
    version: str,
) -> tuple[DependencyResolutionCandidates, ...] | None
```

### دلالة المصدر والتحقق

- المدخلان `asset_id` و`version` يتبعان validation contract نفسه في 6.2/6.3؛ الإدخال غير الصالح لا يتحول إلى `None` ولا ينشئ سلوكًا جديدًا.
- `None` تعني فقط أن الهوية الدقيقة `(asset_id, version)` صالحة شكليًا لكنها غير موجودة في Snapshot.
- `()` تعني أن المصدر موجود ولا يعلن dependencies.
- النتيجة تحتوي سجلًا واحدًا لكل `dependency_asset_id` معلن، بترتيب حتمي.

### المرشحون والتصنيف

- `candidate_identities` هي جميع هويات `(asset_id, version)` الموجودة في Graph Snapshot المعزولة، سواء أُخذت من `catalog.list()` أو أُدخلت مباشرة وفق عقد 6.2، والتي يساوي `asset_id` فيها هدف dependency مطابقةً تامة وحساسة لحالة الأحرف.
- المرشحون هم إصدارات **مسجلة فقط**، وليسوا إصدارات مؤهلة أو معتمدة للتشغيل.
- لا تصفية حسب lifecycle؛ قد تشمل النتائج `SANDBOX` و`STAGING` و`ACTIVE` و`DEPRECATED` و`RETIRED` و`QUARANTINED`.
- لا تدخل `risk_tier` أو `required_permissions` أو provenance أو capabilities في الترشيح.
- صفر مرشحين → `UNRESOLVED` و`candidate_identities == ()`.
- مرشح واحد → `UNIQUE`.
- أكثر من مرشح → `MULTIPLE_CANDIDATES`.
- `UNIQUE` لا تعني `RESOLVED` أو `APPROVED` أو قابلية التشغيل؛ تعني فقط وجود هوية إصدار واحدة مسجلة حاليًا.

### Snapshot والفهرسة

- تستخدم Graph الـSnapshot المعزولة نفسها في 6.2/6.3 ولا تحتفظ بمرجع حي إلى Catalog أو lock الخاص به.
- يبنى مرة واحدة فهرس داخلي immutable بالشكل `asset_id -> tuple[CapabilityIdentity, ...]`.
- تستخدم الاستعلامات الفهرس؛ لا يعاد مسح descriptors أو Catalog لكل dependency.
- التسجيل اللاحق لا يغير Graph موجودة؛ يلزم بناء Snapshot جديدة.
- كل tuples مرتبة حتميًا، ولا تُكشف dict أو set داخلية قابلة للتعديل.

### الحدود الصريحة

- لا اختيار latest أو preferred version، ولا version constraints أو compatibility ranking.
- لا Resolver/Binding، ولا fallback/rollback، ولا adapter selection أو Runtime integration.
- لا lifecycle eligibility أو transition، ولا Policy/permission enforcement.
- لا mutation أو registration/update/delete/retirement/removal enforcement.
- لا تغيير لسلوك direct graph أو SCC أو potential impact المثبت في 6.2/6.3.
- لا يفرض العقد أن Binding هي الشريحة التالية؛ يعاد `NEXT_SLICE_DISCOVERY` بعد إغلاق 6.4.

### ملفات التنفيذ المتوقعة

- `core/capabilities/models.py`
- `core/capabilities/contracts.py`
- `core/capabilities/dependency_graph.py`
- `core/capabilities/__init__.py`
- `tests/test_stage6_capability_dependency_resolution_candidates.py`

### بوابة RED ومعايير القبول

يجب أن تثبت RED المستقلة قبل GREEN:

1. إضافة واجهة القراءة المعتمدة فقط، دون API لاختيار أو اعتماد أو تشغيل مرشح، ودون أي API mutating.
2. فصل input غير الصالح عن source الصحيح المفقود.
3. فصل source المفقود `None` عن source بلا dependencies `()`.
4. سجل واحد حتمي لكل dependency معلنة.
5. `UNRESOLVED` و`UNIQUE` و`MULTIPLE_CANDIDATES` وفق عدد الهويات المسجلة.
6. شمول جميع الإصدارات المسجلة وترتيبها دون lifecycle/risk/permission filtering.
7. إثبات أن `UNIQUE` لا ينفذ اختيارًا أو اعتمادًا.
8. exact case-sensitive matching دون fuzzy/prefix/substring/case folding.
9. Snapshot isolation وبناء فهرس immutable مرة واحدة دون rescans لكل dependency.
10. immutability وعدم تسريب المجموعات الداخلية.
11. عدم إحداث regression في عقود واختبارات 6.1–6.3.
12. عدم إضافة Resolver/Binding أو Runtime/Policy/lifecycle/removal semantics.
13. full regression في Exit Gate فقط بعد نجاح targeted وaffected suites.

### أدلة الإغلاق

- Implementation commit: `48027daa054c1b982cae30b2489978ad9531a2e9`.
- RED: `18 failed` للأسباب المقصودة.
- GREEN: `18 targeted passed` و`113 affected passed`.
- Full regression: `498 passed`؛ failures/errors/skipped = `0/0/0`.
- `git diff --check`: ناجح، وLocal HEAD = Remote HEAD بعد push.
- بقي النطاق Local/In-Memory وRead-only دون Resolver/Binding أو اختيار تشغيلي.

### الإجراء التالي

Slice 6.4 مغلقة ومتحققة. الخطوة التالية هي `NEXT_SLICE_DISCOVERY` لـStage 6؛ لا يُعتمد ترتيب لاحق، ولا يبدأ RED أو production code قبل عقد مستقل وموافقة المالك.

<!-- STAGE6_SLICE6_4_CONTRACT_END -->



<!-- STAGE6_SLICE6_5_CONTRACT_BEGIN -->
## Slice 6.5 — Explicit Dependency Binding Validation Read Model

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

### الغرض وحدود معنى Binding

إضافة Read Model محلي/In-Memory وحتمي للتحقق البنيوي من Binding صريح يقترحه المستدعي. لا تختار Slice 6.5 Binding، ولا تحفظها، ولا تعتمدها، ولا تجعلها قابلة للتشغيل.

### العقد العام

- `DependencyBindingDisposition` قيمه المغلقة: `STRUCTURALLY_VALID` و`DEPENDENCY_NOT_DECLARED` و`TARGET_NOT_FOUND`.
- `DependencyBindingValidation` سجل immutable يحتوي فقط:
  - `dependency_asset_id: str`
  - `target_identity: CapabilityIdentity`
  - `disposition: DependencyBindingDisposition`
- يضاف إلى `CapabilityDependencyGraphProtocol` والتنفيذ المحلي:

```python
validate_dependency_binding(
    asset_id: str,
    version: str,
    dependency_asset_id: str,
    target_version: str,
) -> DependencyBindingValidation | None
```

هوية الهدف مشتقة حتميًا بالشكل `(dependency_asset_id, target_version)`.

### ترتيب القرار والتحقق

1. كل مدخل يتبع validation contract الحالي في 6.2–6.4؛ الأنواع غير الصحيحة تنتج `TypeError` والنصوص غير الصالحة تنتج `ValueError`، ولا تتحول إلى نتيجة منظمة.
2. إذا كانت هوية المصدر صالحة شكليًا لكنها غير موجودة في Snapshot، تعاد `None` فقط.
3. إذا وجد Descriptor المصدر الدقيق لكنه لا يعلن `dependency_asset_id`، تعاد `DEPENDENCY_NOT_DECLARED` دون اعتبار لاعتماديات إصدارات المصدر الأخرى.
4. إذا كانت dependency معلنة لكن هوية الهدف الدقيقة غير مسجلة، تعاد `TARGET_NOT_FOUND`.
5. إذا كانت dependency معلنة وهوية الهدف الدقيقة مسجلة، تعاد `STRUCTURALLY_VALID`.

### هوية المصدر وعدم استخدام union

- يفحص إعلان dependency على Descriptor هوية المصدر الدقيقة `(asset_id, version)` فقط.
- لا يستخدم union اعتماديات جميع إصدارات `asset_id`.
- union المستخدم في 6.3 يخص potential impact ولا يغير دلالة Binding الخاصة بإصدار مصدر محدد في 6.5.

### اتساق المرشحين مع Slice 6.4

بعد صلاحية المدخل، ووجود المصدر الدقيق، وثبوت إعلانه dependency، تكون `STRUCTURALLY_VALID` صحيحة إذا وفقط إذا كانت `(dependency_asset_id, target_version)` ضمن `candidate_identities` للdependency نفسها في Snapshot نفسها وفق تعريف 6.4.

- لا تنشئ 6.5 تعريفًا ثانيًا للمرشحين.
- تستخدم الهوية والفهارس وSnapshot نفسها التي تعتمد عليها 6.4.
- `TARGET_NOT_FOUND` تشمل غياب `dependency_asset_id` كليًا، أو وجود الأصل بإصدارات أخرى دون `target_version` المطلوبة.

### معنى STRUCTURALLY_VALID

تعني structural match فقط. لا تعني approved أو authorized أو eligible أو selected أو resolved automatically أو runtime-capable أو persisted binding.

- Lifecycle لا تدخل في التحقق.
- تبقى هوية `RETIRED` أو`QUARANTINED` structurally valid إذا كانت مسجلة بدقة وتحققت الشروط البنيوية.
- تعامل self-dependency بنيويًا بصورة عادية؛ يبقى كشف cycles من اختصاص Slice 6.2.

### Snapshot isolation والفهرسة

- Snapshot بُنيت قبل تسجيل الهدف وتعيد `TARGET_NOT_FOUND` تبقى كذلك.
- التسجيل اللاحق في Catalog لا يغير Snapshot القديمة.
- Snapshot جديدة مبنية بعد التسجيل فقط قد تعيد `STRUCTURALLY_VALID`.
- لا قراءة لاحقة من Catalog، ولا Catalog live reference، ولا live lock، ولا hidden index update.
- تستخدم فهارس Snapshot القائمة؛ لا يعاد مسح Catalog أو جميع descriptors لكل validation.
- النتائج immutable وحتمية، ولا تُكشف مجموعات داخلية قابلة للتعديل.

### خارج النطاق

- Binding persistence وautomatic Resolver وautomatic selection.
- latest وranking وversion constraints.
- Lifecycle transitions وPolicy وpermissions وapprovals.
- Runtime وAdapter integration وfallback وrollback.
- removal enforcement وpersistence وdistributed behavior.

### ملفات التنفيذ المتوقعة

- `core/capabilities/models.py`
- `core/capabilities/contracts.py`
- `core/capabilities/dependency_graph.py`
- `core/capabilities/__init__.py`
- `tests/test_stage6_capability_dependency_binding_validation.py`

### بوابة RED ومعايير القبول

1. واجهة التحقق المعتمدة فقط، دون تخزين أو اختيار أو اعتماد أو تشغيل Binding.
2. validation الحالي وفصل invalid input عن source الصحيح المفقود.
3. ترتيب القرار المثبت ونتائجه الثلاث فقط.
4. فحص declaration على Descriptor المصدر بالإصدار الدقيق دون union بين الإصدارات.
5. invariant مطابق لمرشحي 6.4 في Snapshot نفسها، دون تعريف مرشحين موازٍ.
6. `TARGET_NOT_FOUND` للهدف الغائب وللإصدار الدقيق الغائب مع وجود إصدارات أخرى.
7. إثبات أن `STRUCTURALLY_VALID` structural match فقط.
8. عدم تصفية Lifecycle، بما فيها `RETIRED` و`QUARANTINED`.
9. self-dependency عادية بنيويًا مع بقاء cycles ضمن 6.2.
10. Snapshot قديمة تبقى `TARGET_NOT_FOUND` بعد التسجيل، وSnapshot جديدة فقط قد تصبح `STRUCTURALLY_VALID`.
11. استخدام الفهارس القائمة بلا Catalog rescan أو live reference/lock/hidden update.
12. immutability والحتمية وعدم تسريب المجموعات الداخلية.
13. عدم إحداث regression في عقود 6.1–6.4.
14. عدم إضافة أي عنصر من خارج النطاق.
15. full regression في Exit Gate فقط بعد نجاح targeted وaffected suites.

### أدلة الإغلاق

- Implementation commit: `256f781f8f14d880d74786dedd8417b1f28af3ea`.
- RED: `24 failed` للأسباب المقصودة.
- GREEN: `24 targeted passed` و`131 affected passed`.
- Full regression: `522 passed`؛ failures/errors/skipped = `0/0/0`.
- `git diff --check`: ناجح، وLocal HEAD = Remote HEAD بعد push.
- بقي النطاق Local/In-Memory وRead-only دون Binding persistence أو Resolver/selection أو Policy/Runtime.

### الإجراء التالي

Slice 6.5 مغلقة ومتحققة. الخطوة التالية هي `NEXT_SLICE_DISCOVERY` لـStage 6؛ لا يُعتمد ترتيب لاحق، ولا يبدأ RED أو production code قبل عقد مستقل وموافقة المالك.

<!-- STAGE6_SLICE6_5_CONTRACT_END -->

<!-- STAGE6_SLICE6_6_CONTRACT_BEGIN -->
## Slice 6.6 — Explicit Dependency Binding Plan Validation Read Model

**الحالة:** `VERIFIED COMPLETE — LOCAL/IN-MEMORY SCOPE`

### الغرض

إضافة Read Model محلي/In-Memory وحتمي للتحقق البنيوي من خطة Bindings كاملة يقترحها المستدعي لهوية مصدر دقيقة. لا تختار Slice 6.6 أي target، ولا تكمل Binding ناقصة تلقائيًا، ولا تحفظ الخطة أو تعتمدها أو تجعلها قابلة للتشغيل، ولا تعيد تعريف قواعد Binding المنفردة المثبتة في Slice 6.5.

### النماذج العامة

```python
@dataclass(frozen=True)
class DependencyBindingProposal:
    dependency_asset_id: str
    target_version: str
```

الـBindings تدخل في `tuple` immutable تحفظ multiplicity؛ لا تستخدم `set` أو `frozenset` لأنهما يمحوان التكرار قبل اكتشافه.

```python
class DependencyBindingPlanIssueKind(str, Enum):
    MISSING_BINDING = "missing_binding"
    DUPLICATE_BINDING = "duplicate_binding"
    CONFLICTING_BINDING = "conflicting_binding"
```

```python
@dataclass(frozen=True)
class DependencyBindingPlanIssue:
    dependency_asset_id: str
    kind: DependencyBindingPlanIssueKind
    target_versions: tuple[str, ...]
```

دلالة `target_versions` مغلقة: `()` للـ`MISSING_BINDING`، وإصدار واحد للـ`DUPLICATE_BINDING`، وجميع الإصدارات المختلفة مرتبة حتميًا للـ`CONFLICTING_BINDING`. لا يضاف `duplicate_count` لعدم وجود حاجة مثبتة له.

```python
@dataclass(frozen=True)
class DependencyBindingPlanValidation:
    source_identity: CapabilityIdentity
    binding_validations: tuple[DependencyBindingValidation, ...]
    issues: tuple[DependencyBindingPlanIssue, ...]
    structurally_complete: bool
```

### الاستعلام

```python
validate_dependency_binding_plan(
    asset_id: str,
    version: str,
    bindings: tuple[DependencyBindingProposal, ...],
) -> DependencyBindingPlanValidation | None
```

هوية المصدر الدقيقة `(asset_id, version)` تقدم مرة واحدة على مستوى الخطة، وكل Proposal تحتوي فقط `dependency_asset_id + target_version`.

### Validation contract وترتيب القرار

1. يخضع `asset_id` و`version` لعقد التحقق الحالي في 6.2–6.5.
2. يجب أن تكون `bindings` من نوع `tuple`، ويجب أن يكون كل عنصر `DependencyBindingProposal`.
3. تخضع حقول كل Proposal لعقد النصوص الحالي؛ النوع غير الصحيح ينتج `TypeError` والنص غير الصالح ينتج `ValueError`.
4. تتحقق جميع المدخلات قبل فحص وجود المصدر، ولا تتحول المدخلات غير الصالحة إلى `None` أو تقرير منظم.
5. إذا كانت هوية المصدر صالحة شكليًا لكنها غير موجودة في Snapshot، تعاد `None` فقط.
6. إذا كان المصدر الدقيق موجودًا، يعاد تقرير immutable دائمًا.

### تجميع الخطة والتصنيف المتبادل الاستبعاد

تجمع Proposals حسب `dependency_asset_id` مع حفظ multiplicity والإصدارات المختلفة:

- لا Proposal لاعتماد معلن: `MISSING_BINDING` واحدة.
- أكثر من Proposal وجميعها لنفس `target_version`: `DUPLICATE_BINDING` واحدة.
- أكثر من `target_version` مختلف: `CONFLICTING_BINDING` واحدة فقط، مهما كانت multiplicity الداخلية.

لكل `dependency_asset_id` بحد أقصى Issue تجميع واحدة. لا تجتمع `MISSING_BINDING` أو`DUPLICATE_BINDING` أو`CONFLICTING_BINDING` معًا للdependency نفسها. وجود targets مختلفة يصنف `CONFLICTING_BINDING` فقط ولا يضيف duplicate للمجموعة نفسها.

### إعادة استخدام Slice 6.5

لكل زوج فريد `(dependency_asset_id, target_version)` تستخدم 6.6 مسار التحقق المعتمد نفسه في 6.5 وتعيد `DependencyBindingValidation` نفسها بنتائجها المغلقة:

- `STRUCTURALLY_VALID`
- `DEPENDENCY_NOT_DECLARED`
- `TARGET_NOT_FOUND`

لا تنشئ 6.6 تعريفًا ثانيًا للصلاحية البنيوية. يتحقق كل زوج فريد مرة واحدة فقط: التكرار المتطابق ينتج validation واحدة مع `DUPLICATE_BINDING`، والtargets المتعارضة تنتج validation لكل target فريد مع `CONFLICTING_BINDING`. يجوز اجتماع conflict مع `TARGET_NOT_FOUND` لأنهما مشكلتان مستقلتان. الاعتماد غير المعلن يظهر عبر نتيجة 6.5 `DEPENDENCY_NOT_DECLARED` ولا تضاف له Issue تجميع جديدة.

### تعريف الاكتمال البنيوي

تكون `structurally_complete=True` إذا وفقط إذا:

1. لكل dependency معلنة Proposal واحدة بالضبط.
2. لا توجد Proposal لاعتماد غير معلن.
3. لا توجد duplicate أو conflicting bindings.
4. جميع `binding_validations` هي `STRUCTURALLY_VALID`.

في جميع الحالات الأخرى تكون `False`. لا يعني الاكتمال approved أو authorized أو eligible أو selected أو resolved automatically أو persisted أو executable أو runtime-capable.

### الحالات الحدية

- مصدر بلا dependencies مع خطة فارغة: مكتمل بنيويًا.
- مصدر بلا dependencies مع خطة غير فارغة: تعيد كل Binding `DEPENDENCY_NOT_DECLARED` والخطة غير مكتملة.
- Proposal لاعتماد غير معلن لا تصبح صالحة بسبب اكتمال بقية الاعتماديات.
- self-dependency تعامل بنيويًا مثل غيرها عبر 6.5، ويبقى كشف cycles ضمن 6.2.
- المطابقة exact وحساسة لحالة الأحرف، ولا يستخدم union اعتماديات إصدارات المصدر الأخرى.

### الحتمية والترتيب

لا يؤثر ترتيب المدخلات في ترتيب المخرجات:

- ترتب `binding_validations` حسب `(dependency_asset_id, target_version)`.
- يعرف العقد ترتيب Issue ثابتًا: `MISSING_BINDING` ثم `DUPLICATE_BINDING` ثم `CONFLICTING_BINDING`.
- ترتب `issues` حسب `(dependency_asset_id, ISSUE_KIND_ORDER[kind], target_versions)` حيث الرتب `0، 1، 2` وفق الترتيب الثابت أعلاه، ولا يعتمد الترتيب على قابلية مقارنة Enum أو على تغير قيمها مستقبلًا.
- ترتب `target_versions` داخل conflict تصاعديًا.
- لا تكشف أي مجموعة داخلية قابلة للتعديل.

### Snapshot isolation والفهرسة

- تستخدم 6.6 Graph Snapshot نفسها وقواعد 6.5 نفسها.
- لا قراءة لاحقة من Catalog، ولا Catalog live reference أو live lock أو hidden index update.
- لا rescan كامل للCatalog أو جميع descriptors؛ تستخدم فهارس Snapshot القائمة.
- التسجيل اللاحق في Catalog لا يغير نتيجة Snapshot قديمة؛ Snapshot جديدة فقط قد تنتج نتيجة مختلفة.
- النتائج immutable وحتمية.

### خارج النطاق

- Binding storage أو persistence.
- automatic Resolver أو automatic selection.
- latest أو ranking أو version constraints.
- Lifecycle filtering أو transitions.
- Policy وpermissions وapprovals.
- Runtime وAdapter integration.
- fallback وrollback.
- removal enforcement.
- distributed behavior.
- mutation لأي Catalog أو Graph.

### ملفات التنفيذ المتوقعة

- `core/capabilities/models.py`
- `core/capabilities/contracts.py`
- `core/capabilities/dependency_graph.py`
- `core/capabilities/__init__.py`
- `tests/test_stage6_capability_dependency_binding_plan_validation.py`

### بوابة RED ومعايير القبول

1. النماذج العامة مغلقة وimmutable ومحدودة الحقول، مع tuple تحفظ multiplicity.
2. شكل API المعتمد فقط، دون storage أو selection أو mutation.
3. Validation contract وترتيبه وفصل invalid input عن المصدر الصحيح المفقود.
4. المصدر الدقيق المفقود يعيد `None`.
5. خطة فارغة لمصدر بلا dependencies مكتملة بنيويًا.
6. missing binding لاعتماد معلن.
7. undeclared binding عبر نتيجة 6.5 نفسها.
8. duplicate مطابق ينتج Issue واحدة وvalidation واحدة للزوج الفريد.
9. targets مختلفة تنتج conflict واحدة فقط مهما كانت multiplicity ولا تنتج duplicate للمجموعة نفسها.
10. إعادة جميع المشكلات المستقلة معًا بدل first-error disposition.
11. target غير موجود يبقى `TARGET_NOT_FOUND` وفق 6.5.
12. خطة صحيحة كاملة تنتج `structurally_complete=True` دون معنى approval أو Runtime.
13. فحص Descriptor المصدر الدقيق وعدم استخدام union بين الإصدارات.
14. إعادة استخدام دلالات ومسار 6.5 دون تعريف موازٍ أو drift.
15. self-dependency وLifecycle تتبعان حدود 6.5 الحالية.
16. ترتيب حتمي صريح مستقل عن ترتيب الإدخال وعن مقارنة Enum.
17. بحد أقصى Issue تجميع واحدة لكل dependency، وعدم إضافة `duplicate_count`.
18. Snapshot isolation واستخدام الفهارس بلا Catalog rescan أو live reference.
19. immutability وعدم تسريب المجموعات الداخلية.
20. عدم إحداث regression في عقود 6.1–6.5 وعدم إدخال أي عنصر من خارج النطاق.
21. full regression في Exit Gate فقط بعد نجاح targeted وaffected suites.

### الإجراء التالي

Slice 6.6 مغلقة ومتحققة ضمن Local/In-Memory scope. Evidence التفصيلية وClosure Receipt مربوطة في Handoff: `/workspaces/shujaa_handoff_bundle/stage6_6_closure/20260828T225400Z_826/closure_receipt_final.txt`.

الخطوة التالية هي `NEXT_SLICE_DISCOVERY` مستقل؛ لا يفترض مسبقًا أن Resolver أو Binding persistence أو Lifecycle هي الشريحة التالية، ولا يبدأ RED قبل عقد وموافقة مستقلين.

<!-- STAGE6_SLICE6_6_CONTRACT_END -->

<!-- STAGE6_SLICE6_7_CONTRACT_BEGIN -->
### Slice 6.7 — In-Memory Explicit Dependency Binding Registry

**الحالة:** `IMPLEMENTED AND VERIFIED`

**الغرض:** حفظ خطة ربط صريحة اجتازت تحقق Slice 6.6 داخل Registry محلية وفي الذاكرة، دون اختيار تلقائي أو سلوك Runtime.

#### Public boundary

- `ExplicitDependencyBindingRegistryProtocol` هو العقد العام ويعرض `register()` و`get()` و`list()`.
- `InMemoryExplicitDependencyBindingRegistry` هو التنفيذ المحلي لهذه الشريحة.
- السجل مرتبط بـimmutable Dependency Graph snapshot ولا يحتفظ بمرجع حي إلى Catalog.

النماذج العامة:

- `ExplicitDependencyBinding`: `dependency_asset_id` و`target_identity`.
- `ExplicitDependencyBindingSet`: `source_identity` وcanonical immutable bindings.
- `DependencyBindingRegistrationResult`: `disposition` و`validation`.
- dispositions: `REGISTERED`، `IDEMPOTENT_REPLAY`، `IDENTITY_CONFLICT`، `SOURCE_NOT_FOUND`، `PLAN_REJECTED`.

#### register contract

المدخلات هي هوية المصدر الدقيقة و`tuple[DependencyBindingProposal, ...]`. قواعد الأنواع والقيم والأخطاء تبقى متوافقة مع Slice 6.6.

الترتيب الملزم:

1. validate input.
2. استدعاء `validate_dependency_binding_plan()` مرة واحدة.
3. `None` يعيد `SOURCE_NOT_FOUND`.
4. `structurally_complete=False` يعيد `PLAN_REJECTED`.
5. اشتقاق canonical binding set من نتيجة Validation، لا من ترتيب إدخال المستدعي.
6. اكتساب Registry lock.
7. المفتاح غير موجود: تخزين وإرجاع `REGISTERED`.
8. الموجود يساوي canonical set: `IDEMPOTENT_REPLAY`.
9. الموجود مختلف: `IDENTITY_CONFLICT` دون استبدال الفائز.

#### Result and read semantics

- `SOURCE_NOT_FOUND` فقط يعيد `validation=None`.
- `REGISTERED` و`IDEMPOTENT_REPLAY` و`IDENTITY_CONFLICT` و`PLAN_REJECTED` تحمل نتيجة Validation الداخلية للمحاولة الحالية.
- `get(asset_id, version)` يعيد `None` للهوية غير المسجلة.
- `list()` تعيد Binding Sets immutable مرتبة حتميًا حسب `(asset_id, version)`.
- replay وconflict ورفض الخطة لا تغير الحالة المخزنة، ولا توجد partial writes.

#### Atomicity and concurrency

- Validation وCanonicalization يحدثان خارج Registry lock.
- القفل يغطي `compare/store` الذري فقط.
- في محاولات متزامنة متطابقة: تسجيل واحد `REGISTERED` والبقية `IDEMPOTENT_REPLAY`.
- في خطط صحيحة مختلفة لنفس المصدر: تسجيل واحد `REGISTERED` والبقية `IDENTITY_CONFLICT`.
- أول من يكتسب القفل يفوز؛ الفائز scheduling-dependent، ولا تفترض الاختبارات هوية الخطة الفائزة.

#### خارج النطاق

لا Resolver، ولا automatic version selection، ولا Lifecycle أو permissions/policy، ولا Runtime أو Persistence، ولا update/delete/rebind، ولا مسؤوليات Stage 7 أو Stage 8.

**البوابة التالية:** موافقة مستقلة على RED. حفظ هذا العقد لا يمنح RED أو GREEN أو implementation أو Commit للكود.

<!-- STAGE6_SLICE6_7_CONTRACT_END -->


<!-- STAGE6_EXIT_GATE_CONTRACT_BEGIN -->
## Stage 6 Exit Gate Contract

### الهدف

إغلاق Stage 6 بالحالة:

`VERIFIED COMPLETE — LOCAL/IN-MEMORY CATALOG & EXPLICIT BINDING FOUNDATION`

### الأحكام

- `GO`: Git مطابق، الأدلة مكتملة ومربوطة بالـcheckpoint نفسه، المراجعات ناجحة، `STAGE6_EXIT_GAP_AUDIT=PASS`، ولا drift أو فجوة مانعة.
- `HOLD`: دليل ناقص/قديم، اختلاف Git أو State Sync، provenance غير قابلة للتحقق، أو غموض يمنع الحكم.
- `FAIL`: regression مثبت، فجوة مانعة، خرق الهوية/الذرية/العزل، hidden selection، اقتران بمزود، أو إدخال مسؤوليات Stage 7/8.
- الأولوية: `FAIL` ثم `HOLD` ثم `GO`. لا `CONDITIONAL GO`.

### النطاق المثبت

- Catalog بهوية وإصدار وDescriptor وLifecycle واعتماديات وصفية.
- permissions داخل Catalog metadata وصفية فقط؛ لا Policy Enforcement في Stage 6.
- Dependency Graph وimpact analysis وresolution candidates كـread models حتمية ومعزولة.
- Binding validation وخطة كاملة وRegistry محلية ذرية وimmutable.
- لا automatic selection أو implicit dependency أو provider coupling.
- Slice 6.8 مؤجلة بلا مستهلك وظيفي مباشر وليست فجوة خروج.

### الأدلة الحالية المرتبطة بـBASE_HEAD

- `BASE_HEAD=734ae282678a40189ab4d4343436682a21233da2`.
- targeted: `21 passed`.
- full regression: `592 passed` و`0 failed`.
- conformance review: `PASS`.
- State Sync: `1 passed`.
- `STAGE6_EXIT_GAP_AUDIT=PASS — NO BLOCKING GAPS`.
- Git/remote synchronized وworktree كانت نظيفة عند بوابة الدخول.

### قاعدة الاقتصاد

- الأدلة السابقة أدلة حالية مرتبطة بالـHEAD نفسه.
- لا يُعاد أي اختبار ناجح؛ لا يوجد trigger جديد لأن Production وHEAD لم يتغيرا.
- حفظ الوثائق لا يثبت اجتياز Exit Gate؛ التنفيذ والتحقق لهما موافقة مستقلة.

### الحدود

- Stage 7: Policy-as-Data وAccess Graph وauthorization وapprovals وlifecycle eligibility وPolicy Enforcement.
- Stage 8: Runtime Adapters والعزل والموارد والأسرار وKill Switch والتحكم الآمن.
- لا يمنح `GO` إذن Stage 7 أو RED/GREEN.

### نتيجة الإغلاق

- `STAGE6_EXIT_GATE=GO`.
- Slices 6.1–6.7 مكتملة.
- Slice 6.8 مؤجلة لعدم وجود مستهلك وظيفي مباشر، وليست فجوة خروج.
- Stage 6: `VERIFIED COMPLETE — LOCAL/IN-MEMORY CATALOG & EXPLICIT BINDING FOUNDATION`.
- Stage 7 لم تبدأ، ولا يمنح هذا الإغلاق إذن Stage 7 أو RED/GREEN.

<!-- STAGE6_EXIT_GATE_CONTRACT_END -->


<!-- STAGE7_ENTRY_GATE_CONTRACT_BEGIN -->
## Stage 7 Entry Gate Contract

**الحالة:** `EXECUTED — GO`

### السلطة والحكم

- حفظ هذا العقد أو Commit/Push لا يبدأ Stage 7.
- بعد حفظ العقد والتزامه ومزامنته يلزم: موافقة مالك مستقلة لتنفيذ Entry Gate، ثم تنفيذها على baseline الجديد، ثم حكم `GO` قبل تغيير Stage 7 إلى `DESIGN/RESEARCH`.
- `GO` يسمح بدخول Stage 7 إلى `DESIGN/RESEARCH` فقط. First Slice Design وRED يحتاجان عقدًا وموافقة مالك مستقلين.
- الأولوية `FAIL` ثم `HOLD` ثم `GO`. اختلاف branch أو HEAD/upstream أو نظافة Worktree أو Stage 6 prerequisite ينتج `HOLD`؛ الخرق الأمني أو تجاوز حدود المراحل ينتج `FAIL`.

### Stage 6 والـEvidence

- Stage 6 prerequisite هو `CLOSED_VERIFIED_COMMITTED_AND_SYNCED`، وتستهلك Stage 7 عقود Catalog وDescriptor وDependency Graph وExplicit Binding الحالية دون تغييرها.
- `required_permissions` وصفية وليست Policy Enforcement.
- أي Production Delta لاحقة لا تبطل Evidence Stage 6 تلقائيًا؛ targeted impact review/revalidation فقط عند أثر مادي على عقود Stage 6 أو افتراضاتها أو الحدود التي تستهلكها Stage 7.
- لا Full Regression دون trigger واسع أو غير قابل للحصر أو trigger آخر مثبت.

### النطاق والملكية

- النطاق الإيجابي: Policy-as-Data وAccess Graph وauthorization وapprovals وlifecycle eligibility ونقطة enforcement موحدة وfail-closed.
- Stage 7 قد تقرر lifecycle eligibility/authorization، لكن القرار وحده لا يغيّر `CapabilityLifecycle` ولا ينقل ملكية Catalog أو lifecycle mutation إلى Stage 7.
- خارج النطاق: Runtime Adapters وsandbox وresource isolation وsecrets وKill Switch implementation في Stage 8؛ durability وrecovery في Stage 9؛ distributed production runtime؛ automatic capability/version selection؛ وتعديل Catalog أو Binding contracts دون فجوة مثبتة وبوابة مستقلة.

### القرارات والبحث وأول Slice

- OPEN_DECISIONS تُغلق بحسب صلتها المادية بالـSlice فقط؛ والبقية `DEFERRED_WITH_TRIGGER`، ولا يؤجل Slice قرار لا يستهلكه.
- `RESEARCH_GATE_REQUIRED=CONDITIONAL`: تصبح Research Gate إلزامية قبل اعتماد Policy Language أو DSL أو Framework أو Engine، أو تجميد Security Model مؤثر داخل public contract.
- لا يلزم بحث خارجي لحفظ Entry Gate، أو دخول `DESIGN/RESEARCH`، أو Slice محلي قابل للرجوع وframework-neutral لا يجمّد اختيارًا أمنيًا.
- اتجاه أول Slice فقط: `framework-neutral single-action authorization/enforcement vertical slice`.
- لا فعل معتمد؛ تُقارن `cancel_task` و`submit` و`retry` لاحقًا عند First Slice Design بحسب الحاجة الوظيفية والمخاطر ووضوح actor/action/resource ومقدار تغيير العقود وقابلية الاختبار والرجوع.

<!-- STAGE7_ENTRY_GATE_CONTRACT_END -->


<!-- STAGE7_SLICE7_1_CONTRACT_BEGIN -->
## Slice 7.1 — Single-Action Authorization Boundary for cancel_task

**الحالة:** `IMPLEMENTED AND TARGETED VERIFIED — COMMITTED AND SYNCED`

### 1. الحاجة والمستهلك

- حماية `cancel_task` قبل lifecycle mutation أو cleanup.
- المستهلك المباشر: `POST /tasks/<task_id>/cancel`.
- أي runtime caller لاحق ملزم بالمرور عبر command path نفسها.
- بقية Slices 7.2–7.5 تبقى `PROPOSAL_ONLY` غير معتمدة، وتُعاد الحاجة بعد 7.1.

### 2. Actor المعتمد لهذه الشريحة

- principal خدمي محلي واحد، stable وopaque وغير سري، يمثل قناة API المصادق عليها.
- لا يدّعي تمثيل المستخدم البشري.
- لا تُخزن API key ولا قيمتها ولا hash أو اشتقاق منها داخل Actor أو Policy أو Audit.
- API key تبقى credential للتحقق فقط، وليست actor identity.
- تعدد principals وidentity federation مؤجلان حتى مستهلك وظيفي مثبت.

### 3. موضع Enforcement

- enforcement إلزامية داخل `ShujaaManager.cancel_task` command entry عبر evaluator محقون.
- API-only enforcement ممنوعة لأنها قابلة للتجاوز من direct in-process caller.
- غياب evaluator أو exception أو malformed/unknown decision ينتج fail-closed.
- لا permissive/default allow.
- lifecycle helpers وExecution Registry تبقى داخلية ولا تتجاوز command entry.
- Manager command entry لا يتجاوز سلامة state machine أو terminal winner.

### 4. العقود الدنيا

Immutable Shujaa-owned contracts:

- `ActorRef`.
- `ResourceRef`.
- `AuthorizationContext`.
- `AuthorizationRequest`.
- `AuthorizationDecision`.
- `CancelAuthorizationEvaluatorProtocol`.

الحد الأدنى فقط:

- actor.
- action=`task.cancel`.
- resource type=`task`.
- resource ID.
- request/operation identity.
- effect=`ALLOW|DENY`.
- reason code.
- policy version.

لا headers أو payload عام أو command/result/error خام أو secrets.

### 5. دلالة القرار

- Missing evaluator أو exception أو malformed/unknown decision: `EVALUATOR_UNAVAILABLE`.
- `DENY`: `POLICY_DENIED`.
- الحالتان لا تنفذان mutation أو cleanup.

### 6. التسلسل الأمني الإلزامي

1. Evaluate.
2. عند `ALLOW`، سجّل authorization evidence إلزامية قبل الفعل.
3. فقط نجاح append أو idempotent replay يسمح بالفعل.
4. فشل التسجيل السابق للفعل ينتج `AUDIT_UNAVAILABLE`، ولا cancel أو mutation أو cleanup.
5. نفّذ lifecycle/race reconciliation الحالية مرة واحدة منطقيًا.
6. سجل outcome audit منفصلة مرتبطة بالقرار والعملية.

يجب استخدام هويتين deterministic منفصلتين:

- authorization evidence identity.
- outcome audit identity.

لا تدّع atomicity أو durability أو exactly-once موزع.

### 7. فشل Outcome Audit بعد الفعل

إذا فشل التسجيل بعد حدوث الفعل:

- لا تعكس lifecycle winner.
- لا تدّع أن الفعل لم يحدث.
- لا تعيد تنفيذ cleanup بسبب فشل Audit.
- أعد نتيجة الفعل الحقيقية مع `audit_status=FAILED` و`warning_code=POST_ACTION_AUDIT_FAILED`.
- حافظ على HTTP status الذي يعكس نتيجة الفعل الحقيقية.
- لا تستخدم generic 500 يوحي بأن الإلغاء لم يحدث.
- التفاصيل الخارجية sanitized؛ التفاصيل اللازمة للتشخيص تبقى داخليًا دون secrets.

### 8. Idempotency والسباقات

- `ALLOW` لا يتجاوز terminal authority أو first-winner semantics.
- السماح مرتبط بالactor/action/resource/operation داخل الاستدعاء نفسه.
- لا يتحول إلى token عام ولا يعبر لفعل أو مورد آخر.
- replay/conflict/stale dispositions الحالية تبقى سلطوية.

### 9. REQUIRED_NOW

- immutable contracts وProtocol.
- actor mapping في composition root.
- evaluator إلزامي منطقيًا لمسار cancel.
- pre-action evidence وpost-action outcome منفصلتان.
- الأخطاء المنظمة: `POLICY_DENIED` و`EVALUATOR_UNAVAILABLE` و`AUDIT_UNAVAILABLE` و`POST_ACTION_AUDIT_FAILED`.
- API wiring واختبارات anti-bypass والفشل والسباق.
- الحفاظ على عقود Stage 4/5 الحالية.

### 10. DEFERRED_WITH_TRIGGER

- فعل ثانٍ: عند مستهلك مباشر مثبت.
- RBAC/ABAC/ReBAC أو DSL/Framework/Engine: عند حاجة مثبتة وبعد Research Gate.
- approvals: عند فعل يحتاج موافقة بشرية.
- multi-principal/federation: عند تجاوز principal الخدمي الواحد.
- Runtime isolation: Stage 8.
- durability/recovery/outbox: Stage 9.
- Stage 6 permissions integration: بوابة مستقلة عند مستهلك مثبت.

### 11. النطاق السلبي

لا:

- Security Model عام.
- Framework أو dependency خارجية.
- approval workflow.
- Stage 8/9.
- تعديل Stage 6.
- تعميم enforcement لفعل آخر.
- Full Regression في RED/GREEN الموجهة دون trigger.

### 12. RED contract

Matrix الاختبارات المقترحة، دون إنشاء الاختبارات الآن:

- immutability وvalidation.
- missing/exception/malformed evaluator.
- `DENY` بلا mutation/cleanup.
- `ALLOW` مع فشل pre-action evidence بلا أثر.
- evidence قبل transition.
- applied/replay/conflicting terminal winner.
- post-action audit failure يحفظ النتيجة.
- no cross-action/resource permit reuse.
- minimal actor/policy/resource بلا secrets.
- API key لا تصبح identity أو Audit data.
- anti-bypass call-site coverage.
- الحفاظ على Stage 5 post-action audit semantics.

### 13. Research Gate

`RESEARCH_GATE=NOT_TRIGGERED`

طالما بقي العقد framework-neutral ومحليًا وقابلًا للرجوع. يتحول إلى `REQUIRED` قبل تجميد Security Model عام أو اعتماد DSL/Framework/Engine.

### 14. Hard Stops

- actor غير محسوم أو تسريب credential.
- bypass لمسار Manager command.
- default allow.
- mutation بعد فشل pre-action evidence.
- تغيير lifecycle winner بسبب post-action Audit failure.
- Framework/Security Model trigger.
- Stage 6/8/9 scope.
- تغير HEAD أو Worktree غير متوقعة.

### 15. Implementation and targeted verification closure

- أُغلق المانع الأخير الخاص بـsanitized post-action diagnostic بمراجعة conformance ناجحة.
- Stage 7.1: `30 passed`.
- affected verification السابقة: `99 passed`.
- post-repair directly affected: `28 passed`.
- مجموعات الأدلة الثلاث متداخلة، ولا تُجمع كعدد اختبارات فريد.
- لم يُشغّل Full Regression لعدم وجود trigger ضمن هذه الحزمة.
- implementation checkpoint هو `15b6887792b5c8c05ab08de8aa4631f6a1b67ae2`.
- عند checkpoint إغلاق Slice 7.1 كانت Stage 7 `IN_PROGRESS_NOT_COMPLETE`؛ تجاوزتها حالة Exit Gate النهائية المسجلة أدناه.
- عند checkpoint إغلاق Slice 7.1 بقيت بقية Slices `PROPOSAL_ONLY` وتحتاج إثبات حاجة وموافقة مستقلة.
- لم تبدأ Slice 7.2 أو أي First Slice أخرى.
- لا يتضمن الإغلاق ADR جديدًا؛ الإصلاح داخل عقد Slice 7.1 المحفوظ.

<!-- STAGE7_SLICE7_1_CONTRACT_END -->


<!-- STAGE7_SLICE7_2_CONTRACT_BEGIN -->
## Slice 7.2 — Single-Action Authorization Boundary for work.submit

**الحالة:** `IMPLEMENTED AND TARGETED VERIFIED — COMMITTED AND SYNCED`

### 1. الحاجة والمستهلك

- `ShujaaManager.submit` ينشئ Work وTask وExecution ويبدأ dispatch/runtime handoff، لكنه لا يملك بعد authorization boundary داخل Manager command entry.
- المستهلكان الوظيفيان المباشران هما `POST /shujaa-task` و`POST /agents/<agent_id>/execute`.
- API authentication وحدها لا تمنع direct in-process bypass لمسار Manager.
- Submit Audit الحالية لا تربط الفعل بالـauthenticated service actor أو policy version.

### 2. الفعل والفاعل والطلب

- الفعل الوحيد لهذه الشريحة هو `work.submit`.
- يعاد استخدام `API_SERVICE_ACTOR` بوصفه principal خدميًا محليًا stable وopaque وغير سري.
- API key تبقى credential للتحقق فقط؛ لا تصبح actor identity ولا تدخل Policy أو Audit.
- كلا مساري API يمران عبر `ShujaaManager.submit` ولا يملكان enforcement بديلة.

### 3. العقود المعاد استخدامها والعقد الجديد

تعاد دون توسيع الحقول:

- `ActorRef`.
- `ResourceRef`.
- `AuthorizationContext`.
- `AuthorizationRequest`.
- `AuthorizationDecision`.
- `AuthorizationEffect`.

يضاف فقط:

- `SubmitAuthorizationEvaluatorProtocol`.
- `SinglePrincipalSubmitEvaluator` محلي خاص بالفعل.

يبقى `CancelAuthorizationEvaluatorProtocol` و`SubmitAuthorizationEvaluatorProtocol` عقدين منفصلين خاصين بالفعلين. لا ينشأ abstraction عام تلقائيًا؛ يعاد بحثه فقط عند ظهور فعل ثالث بمستهلك وظيفي حقيقي وتكرار بنيوي مثبت وعبر Design Gate مستقلة.

### 4. Canonical submit operation identity

`SUBMIT_OPERATION_ID_SOURCE=authorization_request.context.operation_id`

- لا يوجد `submit_operation_id` مستقل في توقيع Manager أو مصدر هوية ثانٍ.
- `submit_operation_id` هو هوية محاولة Submit منطقية واحدة، وليس Retry key ولا مفتاحًا لاستعادة نتيجة سابقة.
- request binding الإلزامية: `action=work.submit` و`resource_type=work_submission` و`resource_id=context.operation_id`.
- بمجرد نجاح pre-action authorization evidence بنتيجة `APPENDED` يصبح operation ID مستهلكًا، قبل dispatch وأي side effect.
- إعادة استخدام الهوية المستهلكة تنتج دائمًا `SUBMIT_OPERATION_REUSED` وHTTP `409` ولا تنشئ Work أو Task أو Execution أخرى، حتى إذا انتهت المحاولة السابقة بفشل dispatch.
- `IDEMPOTENT_REPLAY` و`IDENTITY_CONFLICT` لا يسمحان بالتنفيذ ويعاملان كإعادة استخدام.
- أي محاولة جديدة تستخدم operation ID جديدًا وتُعامل كعملية جديدة بالكامل.
- استخدام ID جديد ليس recovery آمنًا إذا كانت نتيجة المحاولة السابقة مجهولة؛ يمنع automatic retry في الحالة الملتبسة بسبب خطر duplicate submission.
- استعادة النتيجة الأصلية أو retry بنفس ID أو تسوية outcome المجهولة مؤجلة إلى عقد idempotent/durable مستقل ضمن المرحلة المناسبة.
- الاختلاف عن cancel مقصود: cancel يسمح بـ`IDEMPOTENT_REPLAY` لطبيعته idempotent، بينما submit يقبل `APPENDED` فقط.

### 5. Security semantics وfail-closed behavior

1. يسمح input validation البنيوي قبل authorization ما دام بلا side effects.
2. Missing evaluator/request أو evaluator exception أو malformed/unknown decision ينتج `EVALUATOR_UNAVAILABLE`، دون dispatch أو mutation أو thread.
3. malformed أو unbound AuthorizationRequest ينتج `AUTHORIZATION_REQUEST_INVALID`، وهو منفصل عن قرار Policy.
4. `DENY` الصريح ينتج `POLICY_DENIED`.
5. عند `ALLOW` تسجل authorization evidence إلزامية قبل dispatch.
6. `APPENDED` وحدها تسمح بمتابعة Submit.
7. Audit exception أو malformed receipt أو write failure قبل الفعل ينتج `AUDIT_UNAVAILABLE` ولا side effects.
8. لا automatic retry لمحاولة ذات outcome ملتبسة، لا بالهوية نفسها ولا بهوية جديدة يولدها النظام.
9. لا permissive/default allow ولا API-only enforcement.

### 6. Evidence وOutcome Audit

- authorization evidence لها identity منفصلة deterministic مشتقة من canonical operation ID.
- outcome audit تبقى منفصلة وترتبط بالactor وrequest ID وoperation ID وpolicy version وWork الناتجة.
- لا command أو payload أو API key أو headers أو raw error داخل AuthorizationRequest أو Audit.
- فشل post-action outcome Audit لا يعكس accepted result ولا يكرر dispatch.
- عند exception بعد حدوث الفعل يسجل diagnostic داخلي برسالة ثابتة وحقول custom محصورة في: `diagnostic_code` و`exception_type` و`operation_id` و`request_id` و`resource_type` و`resource_id`.
- لا `str(exc)` أو `repr(exc)` أو `exc.args` أو traceback أو `exc_info` أو `logger.exception`.

### 7. API mapping

- `AUTHORIZATION_REQUEST_INVALID` → HTTP `400`.
- `POLICY_DENIED` → HTTP `403`.
- `SUBMIT_OPERATION_REUSED` → HTTP `409`.
- `EVALUATOR_UNAVAILABLE` أو `AUDIT_UNAVAILABLE` → HTTP `503`.
- validation الحالية تبقى `400`، وagent-not-found تبقى `404`.
- لا generic `500` يوحي بفشل الفعل بعد حدوثه بسبب post-action Audit فقط.

### 8. النطاق الإيجابي

- evaluator محقون خاص بـSubmit.
- enforcement داخل `ShujaaManager.submit`.
- request/operation identity يولدها API داخل AuthorizationRequest.
- pre-action evidence قبل dispatcher/registries/thread/events.
- outcome Audit مرتبطة بقرار authorization.
- حماية كلا مساري API وdirect Manager command entry.
- الحفاظ على dispatch rejection وStage 5 Event/Audit semantics الحالية.

### 9. النطاق السلبي

لا:

- تغيير cancel أو retry أو read endpoints.
- evaluator عام لكل الأفعال.
- RBAC أو ABAC أو ReBAC أو Access Graph عام.
- Policy DSL أو Framework أو Engine.
- approval workflow.
- agent-level أو capability-level permission model.
- idempotent submit recovery أو durable operation-result store أو outbox.
- Runtime isolation أو secrets management أو Kill Switch.
- API جديدة أو dependency خارجية.
- Full Regression دون trigger.

### 10. قرارات مؤجلة مع Trigger

- agent/capability-specific authorization: عند principal أو permission consumer مثبت.
- multi-principal/federation: عند قناة هوية ثانية فعلية.
- abstraction مشترك للـevaluators: عند فعل ثالث فعلي وتكرار بنيوي مثبت وDesign Gate مستقلة.
- retry/recovery/result lookup للـSubmit: عند عقد durable/idempotent مستقل في المرحلة المناسبة.
- Access Graph وPolicy-as-Data العامان: عند مستهلك وعلاقات وصول مثبتة وبعد Research Gate عند التجميد.
- approvals: عند فعل يحتاج موافقة بشرية فعلية.

### 11. الملفات المتوقعة

Production:

- `shujaa_crew/core/policy/contracts.py`.
- `shujaa_crew/core/policy/evaluator.py`.
- `shujaa_crew/core/manager/service.py`.
- `shujaa_crew/apps/api/app.py`.

RED/GREEN affected tests:

- `shujaa_crew/tests/test_stage7_submit_authorization_enforcement.py`.
- `shujaa_crew/tests/test_api.py`.
- `shujaa_crew/tests/test_dispatch_failure_atomicity.py`.
- `shujaa_crew/tests/test_retry_admission_contract.py`.
- `shujaa_crew/tests/test_stage5_dispatch_handoff_events.py`.
- `shujaa_crew/tests/test_stage5_submit_audit_integration.py`.
- `shujaa_crew/tests/test_tasks.py`.

### 12. RED test matrix

- canonical operation ID له مصدر واحد، ولا parameter مستقل في Manager.
- `APPENDED` يستهلك الهوية قبل dispatch.
- `IDEMPOTENT_REPLAY` وidentity conflict ينتجان `409` بلا Submission ثانية.
- dispatch rejection لا يسمح بإعادة استخدام الهوية.
- محاولة جديدة تحتاج ID جديدًا وتُعامل كعملية جديدة.
- outcome الملتبسة تمنع automatic retry بالهوية نفسها أو الجديدة.
- لا recovery أو استعادة نتيجة سابقة في هذه الشريحة.
- missing/exception/malformed evaluator يفشل مغلقًا.
- `DENY` منفصل عن `AUTHORIZATION_REQUEST_INVALID`.
- pre-action evidence تسبق dispatcher وregistries وthread وEvent.
- فشل pre-action Audit يمنع التنفيذ.
- post-action Audit failure يحفظ النتيجة ويسجل diagnostic sanitized فقط.
- كلا مساري API يمران عبر Manager enforcement.
- API key لا تصبح actor ولا تدخل Audit.
- request لا تعبر action/resource/operation أخرى.
- direct Manager call بلا authorization يفشل مغلقًا.
- dispatch rejection وEvent/Audit semantics الحالية محفوظة.
- Slice 7.1 لا تتراجع، ولا evaluator abstraction عام.

### 13. Targeted verification

- ملف Stage 7.2 الجديد كاملًا.
- Stage 7.1 suite بسبب مشاركة policy contracts.
- اختبارات Submit/API/dispatch/audit المتأثرة مباشرة فقط.
- anti-bypass وprivacy/static scope checks و`git diff --check`.
- State Sync بعد إغلاق التحقق فقط.
- لا Full Regression إلا عند ظهور trigger واسع غير قابل للحصر.

### 14. Rollback وCheckpoint

- Contract base checkpoint هو `d408bef21869e8895ce63d814387443f342343ee`.
- لا dependency أو migration أو durable schema في العقد.
- RED وGREEN وVERIFY مراحل منفصلة بعد Contract Commit/Push.
- إذا فشلت GREEN يبقى RED والدليل، ولا يبدأ proposal آخر.
- rollback بعد implementation commit يكون بـrevert محدد، لا reset أو clean.

### 15. Research Gate

`RESEARCH_GATE=NOT_TRIGGERED`

لأن العقد single-principal وsingle-action ومحلي وframework-neutral ويعيد استخدام 7.1. يصبح `REQUIRED_BEFORE_FREEZE` قبل Access Graph عام أو RBAC/ABAC/ReBAC أو Policy DSL/Framework/Engine أو Security Model عام.

### 16. Hard Stops

- مصدر operation ID ثانٍ أو parameter مستقل في Manager.
- dispatch بعد أي نتيجة pre-action غير `APPENDED`.
- replay/conflict ينشئ Work أو Task أو Execution أخرى.
- automatic retry عند outcome مجهولة بالهوية نفسها أو الجديدة.
- ادعاء recovery أو استعادة نتيجة بلا عقد durable مستقل.
- خلط `AUTHORIZATION_REQUEST_INVALID` مع `POLICY_DENIED`.
- default allow أو API-only enforcement.
- تسجيل command/payload/API key/headers/raw exception/traceback.
- تغيير accepted result أو تكرار dispatch بسبب post-action Audit failure.
- تعميم evaluator قبل Trigger الفعل الثالث وDesign Gate.
- دخول Stage 8 أو 9 أو framework/security-model freeze.
- تغير HEAD أو Worktree أو توسع ملفات غير متوقع.

### 17. Implementation and targeted verification closure

- `SLICE7_2_STATUS=IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED`.
- implementation checkpoint: `3b5259a69fa23133e6886afcaa14cf748d998c94`، مدفوع إلى `origin/refactor/modular-architecture`.
- ملف Stage 7.2 الجديد: `31 passed`.
- التحقق المتأثر المباشر: `100 passed`.
- التنفيذان متمايزان في هذه الحزمة: `131 collected / 131 passed / 0 failed / 0 errors`.
- Full Regression لم تُشغّل لأن `FULL_REGRESSION_TRIGGER=NO`.
- المصدر الوحيد لهوية العملية هو `authorization_request.context.operation_id`، وتُستهلك الهوية عند `APPENDED` قبل dispatch.
- `IDEMPOTENT_REPLAY` و`IDENTITY_CONFLICT` ينتجان `SUBMIT_OPERATION_REUSED` وHTTP `409` بلا Submission أخرى.
- لا automatic retry عند outcome ملتبسة، لا بالهوية نفسها ولا بهوية جديدة يولدها النظام.
- عند checkpoint إغلاق Slice 7.2 كانت Stage 7 `IN_PROGRESS_NOT_COMPLETE` وبقية Slices `PROPOSAL_ONLY`؛ تجاوزتها حالة Exit Gate النهائية المسجلة أدناه.

<!-- STAGE7_SLICE7_2_CONTRACT_END -->


<!-- STAGE7_SLICE7_3_CONTRACT_BEGIN -->
## Slice 7.3 — Stage 8 Runtime-Control Authorization Prerequisite

**الحالة:** `IMPLEMENTED AND TARGETED VERIFIED — COMMITTED AND SYNCED`

### 1. الحاجة والسلطة المرحلية

- هذه الشريحة تغلق prerequisite مثبتة لدخول Stage 8 وفق ADR-023: قرار authorization ثابت وقابل للاستهلاك لأوامر Runtime Control قبل إضافة تنفيذها الفعلي.
- Stage 7.3 تقرر authorization فقط. لا تنفذ Runtime Control ولا تثبت دعم runtime أو lifecycle eligibility.
- Stage 8 وحدها تملك التكامل الحقيقي مع Runtime Adapter وتنفيذ الفعل أو رفض runtime غير المدعومة افتراضيًا.
- عند اعتماد عقد Slice 7.3 بقيت بقية Stage 7 Slices `PROPOSAL_ONLY` وStage 7 `IN_PROGRESS_NOT_COMPLETE`؛ الحالة النهائية بعد التنفيذ في قسم Exit Gate أدناه.

### 2. Authorization مقابل technical support

- `ALLOW` لا يعني أن runtime تدعم pause أو resume أو terminate.
- `ALLOW` لا يثبت lifecycle eligibility، ولا يغير Execution state، ولا ينفذ Runtime action.
- Stage 8 وحدها تتحقق من capability support وruntime identity وownership وprocess identity وcurrent lifecycle state وtransition eligibility والسباقات وtimeout/budget semantics.
- لا mutation أو signal أو process control أو Adapter invocation داخل Stage 7.3.

### 3. الأفعال والمورد والربط

الأفعال الثلاثة الدقيقة هي:

- `execution.pause`.
- `execution.resume`.
- `execution.terminate`.

المورد الإلزامي:

- `resource_type=execution`.
- `resource_id=execution_id`.

يجب أن يرتبط كل طلب بدقة بالactor والفعل وExecution resource و`request_id` و`operation_id`، ويمنع cross-action وcross-execution وcross-operation reuse وأي اختلاف في action/resource/operation binding.

### 4. Terminate مقابل cancel

- `execution.terminate` Runtime Control action على Execution محددة، وليست مرادفًا لـ`task.cancel` ولا تعيد استخدام دلالاته تلقائيًا.
- لا تغير Task lifecycle ولا تنفذ cleanup داخل Stage 7.
- العلاقة والمصالحة بين `execution.terminate` و`task.cancel` تؤجل إلى عقد Stage 8.
- authorization لـterminate لا تعني تنفيذ الإنهاء أو نجاحه.

### 5. العقود والبوابة القابلة للاستهلاك

تعاد العقود المملوكة لشجاع دون توسيع غير لازم:

- `ActorRef`.
- `ResourceRef`.
- `AuthorizationContext`.
- `AuthorizationRequest`.
- `AuthorizationDecision`.
- `AuthorizationEffect`.

يضاف فقط نطاق Runtime Control الخاص:

- `RuntimeControlAuthorizationEvaluatorProtocol`.
- `SinglePrincipalRuntimeControlEvaluator`.
- Authorization Gate مستقلة وقابلة للاستهلاك لاحقًا داخل Stage 8 command path.

لا evaluator عام لكل أفعال النظام، ولا تعديل أو دمج لـ`CancelAuthorizationEvaluatorProtocol` أو`SubmitAuthorizationEvaluatorProtocol`. الأفعال الثلاثة عائلة Runtime Control المعتمدة في ADR-023، وليست Trigger لتعميم evaluator على النظام. أي تعميم مستقبلي يحتاج فعلًا ثالثًا ذا مستهلك Production وتكرارًا بنيويًا مثبتًا وDesign Gate مستقلة.

### 6. استقلال Authorization Gate

- لا Runtime stub أو fake Runtime Adapter أو fake runner في Production.
- لا callback أو downstream executor أو Runtime Adapter dependency تحقن في البوابة.
- لا تستدعي البوابة downstream أو Adapter أو Manager runtime method.
- التكامل الحقيقي بين Authorization Gate وRuntime Adapter يبدأ في Stage 8 فقط.
- يجوز test double داخل ملف RED فقط لتمثيل مستهلك Stage 8 المستقبلي؛ لا يصدر أو يستورد من Production ولا يصبح Runtime contract أو Adapter implementation.
- يثبت test double أن الفشل لا يصل إلى downstream وأن النجاح يمكن ملاحظته ضمن السيناريو نفسه، دون ادعاء Runtime integration أو Stage 8 anti-bypass verification.

### 7. لا transferable permit

- لا capability token أو permit عام أو serializable أو transferable.
- لا تقبل البوابة AuthorizationDecision أو Audit receipt سابقة بوصفها إذنًا للتنفيذ.
- لا Registry لنتائج authorization بوصفها صلاحيات قابلة لإعادة الاستخدام.
- كل Runtime Control operation تتطلب AuthorizationRequest وقرارًا وevidence جديدة مرتبطة بالطلب نفسه.
- عقد Stage 8 اللاحق يستدعي البوابة داخل command path نفسها وقبل Adapter invocation.
- نتيجة البوابة request-bound، ولا يعاد استخدامها لفعل أو Execution أو operation أخرى.

### 8. Operation identity وEvidence

`RUNTIME_CONTROL_OPERATION_ID_SOURCE=authorization_request.context.operation_id`

- لا operation ID ثانية ولا parameter مستقل داخل Authorization Gate.
- `APPENDED` وحدها تثبت نجاح pre-action authorization evidence لهذه المحاولة.
- `IDEMPOTENT_REPLAY` أو `IDENTITY_CONFLICT` لا تمنح إذن تنفيذ جديدًا.
- أي محاولة جديدة تتطلب operation ID وAuthorizationRequest وقرارًا وevidence جديدة.
- لا automatic retry عند outcome ملتبسة؛ recovery وdurability مؤجلتان إلى Stage 9.

### 9. Fail-closed وAudit semantics

- missing evaluator أو evaluator exception أو malformed/unknown decision: `EVALUATOR_UNAVAILABLE`.
- قرار `DENY` صحيح: `POLICY_DENIED`.
- action/resource/operation binding غير صحيح: `AUTHORIZATION_REQUEST_INVALID`.
- missing Audit store أو append exception أو malformed/non-success receipt: `AUDIT_UNAVAILABLE`.
- كل حالات الفشل تمنع نجاح Authorization Gate، و`APPENDED` فقط تسمح بإرجاع نجاح authorization.
- Audit تسجل الحد الأدنى: actor وaction وExecution resource و`request_id` و`operation_id` و`policy_version`.
- ممنوع تسجيل API keys أو credentials أو command/payload خام أو runtime output أو raw exception message/args أو traceback أو `exc_info` أو secrets.

### 10. REQUIRED_NOW

- العقود الخاصة بـRuntime Control والـsingle-principal evaluator والبوابة المستقلة.
- exact binding والفشل المغلق وpre-action Audit evidence.
- operation identity أحادية المصدر ومنع replay/conflict كإذن جديد.
- result request-bound بلا permit أو Registry.
- RED موجهة تغطي العقود والفشل والEvidence والعزل والخصوصية وحدود المراحل وtest double الاختباري فقط.

### 11. DEFERRED_WITH_TRIGGER

- Runtime Adapter وpause/resume/terminate الفعلية وcapability negotiation وruntime/process identity والتحولات والسباقات والtimeout/budget: Stage 8.
- العلاقة التنفيذية بين `execution.terminate` و`task.cancel`: عقد Stage 8.
- durability وrecovery والنتائج الملتبسة: Stage 9.
- API/UI: Stages 14–15.
- Policy DSL/Engine وRBAC/ABAC/ReBAC وAccess Graph والموافقات وmulti-principal: عند مستهلك مثبت وبعد البوابة المناسبة.
- retry authorization: عند Production consumer مثبت؛ يبقى مؤجلًا الآن.

### 12. النطاق السلبي الإلزامي

لا:

- API أو UI.
- Manager runtime methods.
- Runtime Adapter أو Runtime stub في Production.
- `os.kill` أو signals أو runner/process invocation.
- lifecycle mutation أو capability negotiation أو paused-budget implementation.
- Policy DSL/Engine أو RBAC/ABAC/ReBAC أو Access Graph أو approvals أو multi-principal model.
- durability أو recovery.
- تعديل Catalog أو Binding.
- تغيير ADR-023 إلى `IMPLEMENTED` أو `VERIFIED`.
- تعديل evaluator protocols الخاصة بـ7.1 و7.2.
- Full Regression قبل Stage 7 Exit Gate.
- بدء Stage 8.

### 13. ملفات التنفيذ المتوقعة لاحقًا

Production GREEN المستقبلية فقط:

- `shujaa_crew/core/policy/contracts.py`.
- `shujaa_crew/core/policy/evaluator.py`.
- `shujaa_crew/core/policy/runtime_control.py` إذا فصلت البوابة.
- `shujaa_crew/core/policy/__init__.py`.

RED الحالية فقط:

- `shujaa_crew/tests/test_stage7_runtime_control_authorization_prerequisite.py`.

### 14. RED matrix

- immutability وvalidation للحقول الفارغة والقيم غير المعروفة.
- الأفعال والمورد والربط والـcanonical operation ID الدقيقة.
- missing/exception/malformed evaluator وdecision وDENY.
- invalid binding وmissing/exception/malformed/non-success Audit.
- `APPENDED` فقط تنجح، وreplay/conflict لا يمنحان إذنًا جديدًا.
- actor وpolicy version وrequest/operation linkage والخصوصية.
- منع cross-action/execution/operation reuse وأي permit أو Registry أو automatic retry.
- `ALLOW` لا يثبت runtime support أو lifecycle eligibility ولا يغير Execution state.
- فصل terminate عن cancel، وعدم وجود Manager/API/lifecycle/runtime integration.
- لا Runtime stub في Production ولا evaluator عام ولا تعديل لبروتوكولات 7.1 و7.2.
- test double داخل ملف RED فقط؛ يمنع downstream عند الفشل ويلاحظ نجاح البوابة دون ادعاء Runtime integration.

### 15. Targeted verification وFull Regression

- أثناء Contract Save: State Sync، `git diff --check`، scope check وفرادة markers.
- أثناء RED: ملف RED وحده، ويجب أن يجمع بلا syntax/import/environment errors غير مقصودة ويفشل بسبب غياب تنفيذ Slice 7.3 تحديدًا.
- لا GREEN أو Production changes أو تعديل اختبارات قديمة أو توثيق أثناء RED.
- Full Regression مؤجلة إلى Stage 7 Exit Gate النهائي.

### 16. Research Gate

`RESEARCH_GATE=NOT_TRIGGERED`

لأن الشريحة action-specific وsingle-principal ومحلية وframework-neutral ولا تجمد Policy Language أو Security Model عامًا. تصبح Research Gate إلزامية قبل DSL/Framework/Engine أو RBAC/ABAC/ReBAC أو Access Graph عامة أو Security Model freeze.

### 17. Rollback وCheckpoint

- Contract base checkpoint هو `edb20d9ff5805c28b8b2e41c492ec7ba07d7ee63`.
- Contract Commit/Push يسبقان RED، ويصبح Commit العقد المدفوع `RED_BASE_HEAD`.
- RED لا تلتزم ولا تدفع، وGREEN تحتاج موافقة مالك مستقلة.
- rollback يكون بـrevert محدد، لا reset أو clean أو checkout.

### 18. Hard Stops

- أي Production change أو Runtime stub أثناء RED.
- أي downstream/Adapter/Manager runtime dependency داخل Authorization Gate.
- default allow أو نجاح pre-action بغير `APPENDED`.
- transferable/reusable permit أو Registry للصلاحيات.
- مصدر operation ID ثانٍ أو cross-binding reuse.
- ادعاء runtime support أو lifecycle eligibility أو تنفيذ/نجاح terminate من `ALLOW`.
- خلط `execution.terminate` مع `task.cancel`.
- secrets أو raw payload/error/traceback في Audit أو logs.
- evaluator عام أو تعديل بروتوكولات 7.1 و7.2.
- Stage 8/9 implementation أو Full Regression أو Green بلا موافقة مستقلة.
- تغير HEAD أو Worktree أو scope غير متوقع.

### 19. Implementation وTargeted Verification Closure

- `SLICE7_3_STATUS=IMPLEMENTED_AND_TARGETED_VERIFIED_COMMITTED_AND_SYNCED`.
- عند checkpoint إغلاق Slice 7.3 كانت `STAGE7_STATUS=IN_PROGRESS_NOT_COMPLETE`؛ تجاوزها Stage 7 Exit Gate النهائي أدناه.
- Implementation Commit: `6609a9899c1ebcc7573c33b30fee64c8fb4fe159` (`feat(policy): add runtime control authorization gate`)، مدفوع دفعًا عاديًا إلى `origin/refactor/modular-architecture` ومتطابق محليًا وبعيدًا.
- أضيفت Authorization Gate لأفعال Runtime Control الدقيقة: `execution.pause` و`execution.resume` و`execution.terminate`.
- التنفيذ Authorization-only؛ لا Runtime Adapter أو Runtime stub أو signal أو process control أو lifecycle mutation أو أي side effect في Production.
- مستهلك Stage 8 المستقبلي test double موجود داخل اختبار Slice 7.3 فقط، وليس عقد Runtime أو Adapter في Production.
- `execution.terminate` مختلفة عن `task.cancel`، ونجاح authorization لا يدّعي تنفيذ الإنهاء أو نجاحه.
- لا transferable أو reusable permit؛ كل نتيجة request-bound ولا تمنح صلاحية قابلة للنقل أو التخزين في Registry.
- `APPENDED` فقط يسمح بنجاح authorization؛ `IDEMPOTENT_REPLAY` و`IDENTITY_CONFLICT` لا يمنحان authorization جديدًا.
- New Slice tests: `30 passed`؛ Shared Stage 7.1/7.2 tests: `61 passed`؛ Dependency tests: `136 passed`.
- المجموعات الثلاث متمايزة صراحة: `227 passed / 0 failed / 0 errors`.
- ملف RED لم يتغير، وSHA-256 له: `1913c4ef87640d4626095bd40ec9f3f7dab7c10f73cded8102fbcd9d424ad9a0`.
- Contract conformance: `PASS`؛ Scope and diff checks: `PASS`.
- لم تتراجع Slice 7.1 أو Slice 7.2 ضمن التحقق المشترك.
- عند checkpoint Slice 7.3 بقيت بقية Stage 7 Slices مقترحات فقط وتحتاج حاجة مثبتة وموافقة مستقلة؛ صنفها Exit Gate لاحقًا `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER`.
- ضمن إغلاق Slice 7.3 كان `FULL_REGRESSION_TRIGGER=NONE`؛ شُغلت Full Regression لاحقًا مرة واحدة في Stage 7 Exit Gate ونجحت `683/683`.

<!-- STAGE7_SLICE7_3_CONTRACT_END -->


<!-- STAGE7_EXIT_GATE_CLOSURE_BEGIN -->
## Stage 7 Exit Gate and Documentation Closure

**الحالة:** `VERIFIED COMPLETE — LOCAL ACTION-SPECIFIC AUTHORIZATION FOUNDATION AND CURRENT COMMAND ENFORCEMENT`

`STAGE7_STATUS=VERIFIED_COMPLETE_LOCAL_ACTION_SPECIFIC_AUTHORIZATION_FOUNDATION_AND_CURRENT_COMMAND_ENFORCEMENT`

### أدلة الإغلاق

- Stage 7 Exit Gate: `GO` على checkpoint `af94f932ae1eef9f0376f14001abe880ecbe633c`.
- Full Regression: `collected=683`، `passed=683`، `failed=0`، `errors=0`.
- Slice 7.1 وSlice 7.2 وSlice 7.3 جميعها: `IMPLEMENTED` و`TARGETED_VERIFIED` و`COMMITTED` و`SYNCED`.
- لا Production delta بعد Exit Gate؛ delta الخاصة بهذه المهمة وثائقية في ملفي الحالة فقط.
- Stage 8 لم تبدأ، ولم يُضف ADR أو قرار معماري جديد.
- عبارات `IN_PROGRESS_NOT_COMPLETE` و`PROPOSAL_ONLY` داخل checkpoints المرحلية لكل Slice تسجل حالة تلك اللحظة، وقد تجاوزها هذا الإغلاق السلطوي.

### القدرة المثبتة

- fail-closed authorization enforcement داخل Manager لمسار task cancellation الحالي.
- fail-closed authorization enforcement لمساري `work.submit` الحاليين.
- authorization prerequisite مستقلة وقابلة للاستهلاك لأفعال Runtime Control: pause وresume وterminate.
- عقود actor/action/resource/context محلية immutable، مع evaluators مستقلة action-specific ودون generalized evaluator.
- pre-action authorization evidence تسبق أي side effect، ولا default أو permissive allow.
- فشل post-action Audit لا يعكس النتيجة الفعلية ولا lifecycle winner، ويصدر structured sanitized diagnostics دون raw exceptions أو secrets.
- لا transferable permits؛ Submit تقبل `APPENDED` فقط، وتمنع replay/conflict والـautomatic retry عند outcome ملتبسة.
- `execution.terminate` مستقلة عن `task.cancel` ولا تعيد استخدام دلالاتها تلقائيًا.

### المؤجلات غير المانعة

| البند | الحالة |
|---|---|
| retry authorization | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| approvals | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| Access Graph | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| generalized Security Model | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| RBAC/ABAC/ReBAC | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| Policy DSL/Framework/Engine | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| generalized evaluator | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |
| lifecycle eligibility/mutation غير المستهلكة حاليًا | `DEFERRED_NON_BLOCKING_NO_PRODUCTION_CONSUMER` |

عدم تنفيذ هذه البنود ليس نقصًا في إغلاق Stage 7، ولا يدعي هذا الإغلاق وجود Access Graph أو RBAC/ABAC/ReBAC أو Policy DSL/Framework/Engine أو approval workflow أو retry authorization أو generalized evaluator أو lifecycle mutation.

### حدود Stage 8 وStage 9

- Runtime Adapter وsandbox وresource isolation والتكامل والتنفيذ الحقيقي لأفعال pause/resume/terminate تبقى ضمن Stage 8، ولا يعد غيابها نقصًا في Stage 7.
- لا تدعي Stage 7 دعم runtime أو تنفيذ pause/resume/terminate أو lifecycle mutation.
- durability وrecovery تبقيان ضمن Stage 9.
- أُغلق Commit توثيق Stage 7 ومُزامنته عند `de201dece6bfeddf9a82e22884f491e854d7ff6f`؛ الانتقال الحالي هو عقد Stage 8 Entry Gate المحفوظ أدناه، دون بدء Stage 8.

<!-- STAGE7_EXIT_GATE_CLOSURE_END -->


<!-- STAGE8_ENTRY_GATE_CONTRACT_BEGIN -->
## Stage 8 Entry Gate Contract — Runtime Isolation & Safety

**الحالة:** `SAVED — PENDING ENTRY EXECUTION`

`STAGE8_ENTRY_GATE_CONTRACT=SAVED_PENDING_ENTRY_EXECUTION`

### 1. الهدف والسلطة

- يضبط هذا العقد دخول Stage 8 إلى `DESIGN/RESEARCH` فقط لبناء حدود Runtime Isolation & Safety دون نقل ملكية العقود السابقة أو ادعاء قدرة Runtime غير منفذة.
- حفظ العقد أو Commit/Push لاحق له لا يبدأ Stage 8، ولا يختار First Slice، ولا يمنح RED/GREEN أو تعديل Production/Tests.
- تنفيذ Entry Gate يحتاج موافقة مالك مستقلة على baseline نظيف ومحفوظ ومزامن، ثم حكم نهائي وفق الأولوية: `FAIL > HOLD > GO`.
- `FAIL`: مانع مثبت أو خرق شرط دخول/أمن/نطاق. `HOLD`: Evidence ناقصة أو متعارضة أو قرار Hard Stop غير محسوم. `GO`: جميع الشروط منطبقة، ويسمح بـ`DESIGN/RESEARCH` فقط.
- لا `CONDITIONAL GO`.

### 2. شروط الدخول والسلطات المستهلكة

- Project Truth Gate تثبت الفرع وHEAD/upstream/remote وahead/behind وWorktree والكاتب الوحيد عند نقطة التنفيذ.
- Stage 7 prerequisite هي `CLOSED_VERIFIED_COMMITTED_AND_SYNCED`، وStage 8 وFirst Slice لم تبدآ.
- تستهلك Stage 8 دون نقل ملكية: عقود lifecycle/ownership/identity/race/timeout من Stage 4؛ Event/Audit من Stage 5؛ Catalog/Descriptor/Capability/Explicit Binding من Stage 6؛ وقرارات authorization المنطبقة من Stage 7.
- أي فجوة أو تعارض في سلطة مستهلكة ينتج `HOLD — VERIFY FIRST`؛ لا يعاد تعريف العقد السابق ضمن Stage 8 بلا بوابة مستقلة.

### 3. النطاق الإيجابي والسلبي

النطاق المرجعي لـStage 8:

- Runtime Adapters قابلة للاستبدال.
- Isolation وSandbox.
- Resource limits.
- Secrets safety.
- Runtime-level Kill Switch primitives.
- safe runtime-specific pause/resume وفق العقود المعتمدة.

خارج التنفيذ التلقائي لهذا العقد:

- durability/recovery/journal/outbox في Stage 9.
- Kill Switch hierarchy وControl Plane/UI integration التي يمكن استكمالها في Stages 14–15.
- distributed isolation وproduction hardening التي يمكن امتدادها إلى Stages 16–17 بقرار مالك موثق.
- اختيار تقنية أو مزود أو dependency، أو public API جديدة، أو public `execution.terminate` command.
- Production fake أو Runtime stub، وإعادة تصميم launch/dispatch أو جميع Runtime paths لمجرد التناظر.

لا نقل إضافي للنطاق دون موافقة مالك صريحة وتحديث الخارطة والحالة السلطوية.

### 4. Authority provenance

`No runtime side effect may occur without explicit authority provenance.`

- الأفعال الخارجية أو المحفزة من المستخدم تتطلب قرار Stage 7 authorization المنطبق، و`task.cancel` يحتفظ بعقد Authorization الخاص به.
- cleanup الداخلي الناتج عن timeout/error/startup/shutdown يحتاج deterministic system-authority trigger مربوطًا بـtask وexecution وoperation وملكية process متحقق منها.
- لا يمنح cleanup الداخلي actor خارجيًا أو policy decision مصطنعة.
- Runtime Adapter تنفذ أمرًا محدودًا صادرًا من سلطة معلومة؛ لا تقرر policy أو lifecycle.
- authority provenance ليست transferable permit ولا يعاد استخدامها لفعل أو مورد أو عملية أخرى.

### 5. Audit boundary

`SAFETY_CLEANUP_AUDIT_DECISION=REQUIRES_FIRST_SLICE_SCOPING`

- Audit failure في safety/containment cleanup لا يرث تلقائيًا `AUDIT_UNAVAILABLE/no-side-effect` الخاصة بالأمر الخارجي.
- يجب أن يوازن القرار بين auditability وخطر ترك process مملوكة تعمل، ويحفظ lifecycle truth، ويظهر structured sanitized diagnostic، ويمنع silent failure.
- لا تعتمد الدلالة النهائية هنا؛ حسمها `HARD STOP` قبل RED لأول Slice تستهلك safety cleanup.

### 6. First Slice scoping

`FIRST_SLICE_RECOMMENDATION=LOCAL_PROCESS_CLEANUP_TERMINATION_ADAPTER_BOUNDARY_TYPE_ONLY`

`FIRST_SLICE_EXACT_CONSUMER=NOT_SELECTED`

- يفحص First Slice Design هل cancel/timeout/error/startup/shutdown/owner-conflict تمر عبر seam واحدة وبسلطات ونتائج ودلالات race متطابقة.
- إذا تطابقت ونُقلت دون تغيير semantics جاز معاملتها كعائلة مستهلك واحدة؛ وإذا اختلفت يبدأ Slice بمسار واحد فقط وتؤجل البقية لعقود مستقلة عند الحاجة.
- `task.cancel` مرشح أولي قوي لوجود المستهلك وعقد Stage 7، لكنه غير معتمد.
- لا API جديدة، ولا public `execution.terminate`، ولا Production fake أو Runtime stub، ولا إعادة تصميم launch/dispatch لمجرد التناظر.

### 7. Bypass boundary

`No direct runtime bypass is permitted for side effects explicitly migrated into or claimed by the approved Stage 8 scope.`

- المسارات غير المرحلة تبقى inventoried وexplicitly deferred، ولا تعامل كقدرات Stage 8 مكتملة.
- هذه القاعدة لا تدعي أن جميع Runtime paths رُحّلت، ولا تجبر ترحيل مسارات خارج Slice المعتمدة.

### 8. Hard Stops وCheckpoint/Rollback

- `HARD STOP` عند فشل Project Truth، أو غياب authority provenance، أو التباس ownership/process identity، أو race/timeout semantics غير محسومة، أو bypass داخل النطاق المدعى، أو Scope Drift.
- حسم Audit-failure semantics شرط قبل RED لأول Slice تستخدم safety cleanup.
- كل انتقال `DESIGN/RESEARCH → RED → GREEN → VERIFY → COMMIT → PUSH` يحتاج عقده وموافقته المستقلة عند الصلة.
- تبدأ كل Slice من checkpoint نظيفة ومحفوظة ومزامنة، ويوقف العمل عند Writer conflict أو Worktree غير متوقعة لفحصها دون reset/clean/checkout تلقائي.
- rollback يكون إلى checkpoint معروفة ومتحققة وبقرار صريح، مع حفظ lifecycle truth وauthority provenance؛ لا blind retry ولا side effect عكسية غير مخولة.

### 9. Research Gate

`RESEARCH_GATE_REQUIRED=CONDITIONAL`

- لا يلزم بحث خارجي لحفظ Entry Gate أو لأول boundary محلية framework-neutral.
- يصبح البحث إلزاميًا قبل تجميد أو اعتماد: sandbox/container/process-isolation technology؛ resource-control/cgroup mechanism؛ secrets manager/injection mechanism؛ Kill Switch implementation technology؛ Runtime Framework أو external engine؛ OS-specific mechanism كعقد عام؛ dependency أو مزود أمني خارجي؛ أو public isolation contract يصعب تغييره.
- Research requirement لا تمنح Network أو Data Egress permission؛ يلزم تفويض مستقل.

### 10. Stage 8 Exit Accountability

`STAGE8_EXIT_ACCOUNTABILITY=MANDATORY`

`NO_SILENT_DEFERRAL`

`NO_IMPLICIT_ROADMAP_SCOPE_REDUCTION`

`ROADMAP_SCOPE_REDUCTION=FORBIDDEN_WITHOUT_EXPLICIT_OWNER_DECISION_AND_STATE_UPDATE`

`SANDBOX_EXIT_DISPOSITION=REQUIRES_STAGE8_EXIT_GAP_REVIEW`

`RESOURCE_LIMITS_EXIT_DISPOSITION=REQUIRES_STAGE8_EXIT_GAP_REVIEW`

`SECRETS_EXIT_DISPOSITION=REQUIRES_STAGE8_EXIT_GAP_REVIEW`

`KILL_SWITCH_PRIMITIVE_EXIT_DISPOSITION=REQUIRES_STAGE8_EXIT_GAP_REVIEW`

`PAUSE_RESUME_EXIT_DISPOSITION=REQUIRES_STAGE8_EXIT_GAP_REVIEW`

| الالتزام | Exit disposition الحالية |
|---|---|
| Sandbox / Isolation | `REQUIRES_STAGE8_EXIT_GAP_REVIEW` |
| Resource limits | `REQUIRES_STAGE8_EXIT_GAP_REVIEW` |
| Secrets safety | `REQUIRES_STAGE8_EXIT_GAP_REVIEW` |
| Runtime-level Kill Switch primitive | `REQUIRES_STAGE8_EXIT_GAP_REVIEW` |
| safe runtime-specific pause/resume | `REQUIRES_STAGE8_EXIT_GAP_REVIEW` |

- قبل Stage 8 Exit يخضع كل بند مرجعي لـExit Gap Review مستقل ويحصل على حكم واحد فقط: `IMPLEMENTED_AND_VERIFIED`، أو `NOT_REQUIRED_IN_CURRENT_SCOPE_WITH_EVIDENCE`، أو `DEFERRED_OR_REALLOCATED_BY_EXPLICIT_OWNER_DECISION`.
- أي تأجيل أو نقل يسجل السبب والدليل والمخاطر المتبقية والمرحلة/البوابة المستهدفة وtrigger إعادة الفتح وأثره في ادعاءات الأمان وتحديث الخارطة والحالة السلطوية.
- غياب الحاجة في First Slice يؤجل التنفيذ المبكر فقط، ولا يلغي التزام الخارطة عند Exit.
- Runtime enforcement primitive اللازمة لـKill Switch ضمن مساءلة Stage 8؛ والحد المحلي المطلوب من Sandbox/isolation/resources/secrets يخضع لـStage 8 Exit Gap Review.
- لا Exit مع Capability غير منفذة أو غير مختبرة مدعاة، أو bypass ضمن النطاق المعتمد، أو paths غير مرحلة غير مسجلة، أو بنود منسية/مؤجلة بصمت.
- يلزم إثبات fail-closed أو containment-preserving behavior بحسب السلطة والمسار، واختبار ownership/identity/race/timeout/capability behavior، وتوثيق قرارات التنفيذ/التأجيل، ثم Full Regression وExit Gate وState Sync.

<!-- STAGE8_ENTRY_GATE_CONTRACT_END -->


<!-- STAGE8_SLICE8_1_CONTRACT_BEGIN -->
## Slice 8.1 — Task-Cancel Owned Local Process Termination Adapter Boundary

**الحالة:** `VERIFIED`

`SLICE8_1_STATUS=VERIFIED`

> صياغات التصميم والمرشحات الزمنية أدناه تحفظ سياق العقد المعتمد قبل التنفيذ؛ حالة التنفيذ الحالية والأدلة المسجلة في القسم 13 هي المرجع، دون تغيير دلالات claim/finalize/quarantine أو حدود الضمان.

### 1. الهوية وحدود المرحلة

- المستهلك الدقيق الوحيد هو `TASK_CANCEL_LOCAL_PROCESS_CLEANUP_PATH_ONLY`.
- يحفظ هذا العقد حدود Slice 8.1 بعد بدء RED وإثبات فجوة concurrency؛ لا يبدأ GREEN أو Runtime implementation، ولا ينشئ Adapter أو stub أو fake.
- يبدأ النطاق المرحّل بعد نجاح Stage 7 cancel authorization وpre-action evidence، وبعد إثبات lifecycle reconciliation أن cancel هو الفائز أو replay صالح وفق العقود الحالية، وعند وجود Process Ownership محلية موثقة وقابلة للتحقق.
- الفعل المرحّل هو إنهاء process أو process group المملوكة محليًا عبر Runtime Adapter واحدة.
- لا تعامل cancel/timeout/error/startup/shutdown/owner-conflict كعائلة مستهلك واحدة في هذه الشريحة.

المسارات غير المرحلة هي:

- timeout cleanup.
- execution-error cleanup.
- startup recovery cleanup.
- shutdown cleanup.
- owner-conflict cleanup.

تبقى هذه المسارات مجرودة ومؤجلة إلى عقود مستقلة عند وجود حاجة مثبتة، ولا تحسب كقدرات Stage 8 مكتملة، ولا يشملها ادعاء anti-bypass لهذه الشريحة قبل ترحيلها صراحة.

### 2. حدود الملكية والمسؤوليات

يبقى `ShujaaManager` مسؤولًا عن:

- استهلاك قرار Stage 7 authorization وحسم lifecycle winner ودلالة replay/conflict.
- استرجاع Process Ownership والتحقق من ملاءمتها orchestration-side.
- إنشاء أمر تقني محدود للـAdapter واستهلاك نتيجتها.
- lifecycle/result mapping وحفظ lifecycle truth.
- ownership release بعد نجاح تقني مثبت فقط أو already-exited مثبت وآمن.
- طلب atomic ownership claim من `ProcessRegistry` قبل استدعاء الـAdapter، ثم تفسير claim/finalization states دون نقل Policy أو lifecycle authority إلى Registry.
- Outcome Event/Audit والتشخيصات المنظمة وحماية مسار cancel من bypass.

تقتصر Runtime Adapter على:

- التحقق التقني من process identity والملكية وPID/PGID/start-time أو الحقول التي تثبتها العقود الحالية.
- إرسال `SIGTERM` وانتظار grace period محدود، ثم التصعيد إلى `SIGKILL` عند الحاجة.
- التحقق من النتيجة التقنية وإعادة نتيجة immutable ومنظمة.

Runtime Adapter لا تقرر Policy أو Authorization أو lifecycle، ولا تختار actor أو policy version، ولا تملك Audit semantics، ولا تفسر API credentials، ولا تعيد استخدام authority كتصريح قابل للنقل، ولا تنفذ Runtime Framework أو isolation أو sandbox عامًا في هذه الشريحة.

### 3. Authority provenance boundary

`Explicit authority provenance remains mandatory at the Manager/orchestration boundary, not necessarily inside the Runtime Adapter payload.`

- يثبت Manager مصدر السلطة قبل طلب أي side effect؛ وفعل `task.cancel` الخارجي يستهلك عقد Stage 7 authorization المنطبق.
- لا يمرر إلى Runtime Adapter افتراضيًا actor أو policy version أو authorization decision أو authorization evidence reference أو API key أو request headers أو command/payload خام.
- لا تفرض Authority/Evidence reference على Adapter ما لم تكشف RED حاجة تقنية مثبتة لا تلبيها معرّفات العملية والملكية؛ أي حاجة لاحقة لها تستلزم تعديل عقد صريح ومراجعة مستقلة.
- يجوز تمرير `operation_id` فقط للربط التقني أو diagnostic correlation عند ثبوت الحاجة؛ ليست permit أو authorization token، ولا يعاد استخدامها لفعل أو مورد آخر.

### 4. الأمر التقني والنتيجة

- تصمم RED لاحقًا عقدًا immutable وبأقل بيانات لازمة، ومن أمثلته غير المجمدة `OwnedLocalProcessTerminationCommand`؛ لا تجمد الأسماء أو الحقول قبل فحص العقود الحالية.
- تقتصر البيانات المرشحة على هوية cleanup operation عند الحاجة التقنية، وProcess Ownership اللازمة للتحقق، وcapability ثابتة خاصة بإنهاء process محلية مملوكة، وgrace timeout محدود إذا كان جزءًا من العقد الحالي أو ثبتت الحاجة إليه.
- يمنع تضمين actor/principal أو policy version أو authorization evidence أو API key/secret أو HTTP data أو task command/payload أو agent output أو raw exception.
- تكون نتيجة الـAdapter immutable ومنظمة، وتميز فقط الحالات التي يثبت احتياج السلوك الحالي والاختبارات إليها؛ المرشح منها graceful termination، forced termination after escalation، already exited، identity mismatch، process-group mismatch، ownership verification failure، unsupported operation، termination failure، وoutcome unknown.
- لا تضاف dispositions لمجرد التناظر.

### 5. ترتيب الـside effect والسلوك الآمن

الترتيب الإلزامي:

1. تنجح Stage 7 authorization.
2. تنجح pre-action authorization evidence وفق عقد cancel الحالي.
3. يحسم Manager lifecycle winner/replay.
4. يسترجع Manager Process Ownership ويتحقق منها.
5. يطلب Manager atomic claim من `ProcessRegistry` بالهوية الكاملة و`cleanup_operation_id`.
6. لا يُقبل سوى claim واحد؛ loser لا يستدعي Adapter، ويُحرر path-scoped lock قبل أي Adapter call.
7. يبني Manager أمرًا تقنيًا محدودًا.
8. تتحقق Runtime Adapter من process identity والملكية.
9. تنفذ Runtime Adapter termination دون إبقاء Registry lock ممسوكًا.
10. يستهلك Manager النتيجة ويحفظ lifecycle truth ويختار finalize decision من العقد المحدد.
11. تنفذ `ProcessRegistry` finalization atomically وفق القرار والدليل.
12. يحدث ownership release فقط بعد نجاح تقني مثبت أو already-exited مثبت وآمن.
13. تسجل Outcome Event/Audit النتيجة دون أسرار.

إذا كانت Adapter مفقودة أو غير صالحة أو أعادت نتيجة malformed، فالسلوك fail-safe ومنظم: لا permissive fallback، ولا direct POSIX fallback، ولا side effect بديل مخفي.

### 6. Audit semantics

- قبل الفعل الخارجي تبقى Stage 7 pre-action authorization evidence fail-closed كما هي؛ فشلها يمنع termination ولا يغير دلالات Slice 7.1.
- بعد بدء أو حدوث containment side effect يعتمد:

`SAFETY_CLEANUP_AUDIT_DECISION=CONTAINMENT_PRESERVING_EXECUTION_WITH_STRUCTURED_AUDIT_FAILURE`

- فشل Outcome Audit بعد termination لا يعكس الفعل، ولا يعيد إرسال signal، ولا يغير lifecycle winner أو يضيع cleanup truth.
- يظهر structured sanitized diagnostic دون raw exception أو traceback أو secrets، ويحظر silent audit failure.
- لا تورث دلالة `AUDIT_UNAVAILABLE/no-side-effect` الخاصة بمرحلة ما قبل الفعل إلى ما بعد containment side effect.

### 7. Replay والتكرار وconcurrency

`EXACTLY_ONCE_CLAIM=NO`

`DUPLICATE_SIDE_EFFECT_POLICY=PREVENT_ONLY_WHERE_PROVEN_BY_CURRENT_LIFECYCLE_AND_OWNERSHIP_CONTRACTS`

`CONCURRENCY_STATUS=REQUIRES_RED_CHARACTERIZATION`

`CONCURRENCY_GAP_BEHAVIOR=HOLD_WITH_CONCURRENCY_GAP`

`CONCURRENCY_MECHANISM=BOUNDED_LOCAL_ATOMIC_OWNERSHIP_CLAIM`

`CLAIM_OWNER=PROCESS_OWNERSHIP_REGISTRY`

`CLAIM_SCOPE=IN_PROCESS_PER_REGISTRY_PATH_EXACT_OWNERSHIP_GENERATION`

`CLAIM_PERSISTENCE=NON_DURABLE`

`LOCK_HELD_DURING_ADAPTER_CALL=NO`

`CONCURRENT_WINNER_COUNT=1`

`LOSER_ADAPTER_INVOCATION=0`

`EXACTLY_ONCE_GUARANTEE=NO`

`DISTRIBUTED_COORDINATION=NO`

`RESTART_DURABILITY=NO`

- لا تدعي الشريحة exactly-once أو universal at-most-once أو concurrency safety غير المثبتة.
- إذا أثبتت الحالة إنهاء العملية والإفراج عن ownership بعد نجاح مثبت، فلا يرسل replay signal جديدة.
- `OUTCOME_UNKNOWN` لا يسمح بـautomatic retry أو signal ثانية، ولا يفسر replay كتصريح جديد.
- تصف RED محاولتي cancel متزامنتين وتقيس adapter/signal invocations والنتيجة.
- إذا أثبتت RED إمكان side effects مكررة غير آمنة ضمن العقود الحالية، تتوقف عند `HOLD_WITH_CONCURRENCY_GAP` دون إصلاح صامت أو ادعاء exactly-once.
- أثبتت RED محاولتي side effect متزامنتين، واعتمد المالك bounded local atomic ownership claim قبل GREEN؛ durability وdistributed coordination وrecovery journal وoutbox تبقى Stage 9.

#### 7.1 عقد bounded local atomic ownership claim

`At most one admitted local termination attempt per exact process-ownership generation among concurrent in-process callers.`

- تنفذ `ProcessRegistry` claim atomية على المفتاح الكامل `(registry_path, task_id, execution_id, pid, pgid, process_start_time_ticks)`، ومالك الـclaim هو `cleanup_operation_id`.
- تكون claim مشتركة في الذاكرة بين مثيلات `ProcessRegistry` التي تشير إلى `registry_path` نفسه، وتستخدم current path-scoped lock أثناء claim وfinalize فقط.
- لا يُمسك lock أثناء Adapter call، والـclaim ليست permit أو policy أو lifecycle decision، وغير قابلة للنقل إلى operation أو ownership generation أخرى.
- لا تفسر Registry policy أو lifecycle أو signals؛ Manager يحتفظ بهذه المسؤوليات ويحوّل نتائج claim/finalize إلى السلوك المنظم.

الحالات الدنيا الملزمة:

- `ACQUIRED`
- `NOT_FOUND`
- `OWNERSHIP_MISMATCH`
- `CLAIMED_BY_OTHER_OPERATION`
- `SAME_OPERATION_REPLAY`
- `FINALIZED_AND_RELEASED`
- `OUTCOME_UNKNOWN_BLOCKED`

قرارات finalization الملزمة:

- `RELEASE_OWNERSHIP`
- `RETAIN_OWNERSHIP_AND_RELEASE_CLAIM`
- `RETAIN_OWNERSHIP_AND_QUARANTINE`

قواعد fail-safe:

- النجاح المثبت أو already-exited المثبت يختار `RELEASE_OWNERSHIP` وينهي claim دون replay signal.
- الفشل المثبت قبل أي side effect يختار `RETAIN_OWNERSHIP_AND_RELEASE_CLAIM` فقط إذا أثبتت نتيجة منظمة موثوقة عدم إرسال signal؛ ولا ينشئ ذلك automatic retry داخل الاستدعاء نفسه.
- النتيجة المعروفة بعد side effect لا تُعكس ولا تعاد تلقائيًا؛ تحفظ technical truth وlifecycle winner ويُختار release أو retain وفق الدليل المثبت.
- exception أو malformed result هي `OUTCOME_UNKNOWN` افتراضيًا ما لم تثبت نتيجة منظمة موثوقة خلاف ذلك؛ يحتفظ بالownership، ويختار `RETAIN_OWNERSHIP_AND_QUARANTINE`، ويمنع أي Adapter invocation لاحق للgeneration نفسها، ويصدر sanitized diagnostic.
- `OUTCOME_UNKNOWN_BLOCKED` لا يسمح signal ثانية أو automatic retry أو تحرير claim بطريقة تسمح بمحاولة جديدة؛ يحتفظ بالownership وبحالة quarantine محلية، وdurable recovery تبقى Stage 9.

### 8. Bypass وAPI والخصوصية

`No direct runtime bypass is permitted for task.cancel side effects migrated into Slice 8.1.`

- تثبت الاختبارات لاحقًا أن مسار cancel المرحّل لا يستدعي POSIX termination مباشرة خارج Adapter، وأن Manager لا يتجاوزها، وأن API لا تستدعي Adapter مباشرة، وأن Adapter لا تقرر policy أو lifecycle بدل Manager.
- لا يدعي ذلك حماية من كود عدائي يملك تنفيذًا حرًا داخل العملية؛ العزل الأوسع من التزامات Stage 8 اللاحقة.
- لا API عامة جديدة ولا public command باسم `execution.terminate`، ولا تغيير غير مقصود في HTTP status أو cancel result.
- لا PID أو PGID أو start-time أو raw exception في API response أو Audit، ولا API key أو payload أو command خام في Runtime contracts أو Audit.
- تحفظ دلالات Stages 4/5/7 الحالية؛ إذا كشفت RED تعارضًا مثبتًا تتوقف دون إعادة تصميم تلقائية.

### 9. نطاق التنفيذ الفعلي الحالي

ملفات Production المنفذة حاليًا لهذه الشريحة:

- `shujaa_crew/core/runtime/owned_local_process_termination_contract.py`
- `shujaa_crew/core/runtime/process_registry_contract.py`
- `shujaa_crew/core/runtime/process_registry.py`
- `shujaa_crew/adapters/runtime/__init__.py`
- `shujaa_crew/adapters/runtime/local_process_termination.py`
- `shujaa_crew/core/manager/service.py`
- `shujaa_crew/apps/api/app.py` لتصحيح composition binding المعتمد فقط.

ملف RED المنفذ والمصحح:

- `shujaa_crew/tests/test_stage8_task_cancel_owned_local_process_termination_adapter.py`

لا Production fake أو stub؛ Test doubles تبقى داخل Tests فقط.

### 10. مصفوفة RED لموافقة لاحقة

يجب أن تغطي RED على الأقل:

- immutability وminimality لعقد command/result، وغياب actor/policy/evidence/API key/payload عن Adapter command.
- أن `operation_id` إن استعملت لا تعمل كpermit.
- missing/malformed Adapter تفشل بأمان دون direct fallback.
- identity وownership verification قبل signal؛ وPID/start-time أو PGID mismatch يمنع termination.
- graceful termination، والتصعيد بعد grace period، وalready-exited، وtermination failure، وoutcome unknown.
- ownership release بعد النجاح المثبت فقط، وعدم release عند identity mismatch أو outcome unknown.
- Stage 7 authorization وpre-action evidence قبل Runtime side effect.
- post-action Audit failure يحفظ النتيجة ويظهر diagnostic منظمًا.
- replay بعد نجاح مثبت لا يرسل signal أخرى، وoutcome unknown لا يطلق automatic retry.
- محاولتي cancel متزامنتين تثبتان winner واحدًا فقط و`LOSER_ADAPTER_INVOCATION=0` لنفس ownership generation عبر مثيلات Registry للمسار نفسه.
- claim identity تشمل `registry_path/task_id/execution_id/pid/pgid/process_start_time_ticks` كاملة، ولا تتصادم ownership generations المختلفة.
- `SAME_OPERATION_REPLAY` و`CLAIMED_BY_OTHER_OPERATION` لا يستدعيان Adapter، والـclaim غير قابلة للنقل.
- Registry lock ممسوك أثناء claim/finalize فقط وغير ممسوك أثناء Adapter call.
- نجاح مثبت أو already-exited يحرر ownership؛ proven pre-side-effect failure يحتفظ بالownership ويحرر claim دون automatic retry.
- known post-side-effect outcome تحفظ technical truth وlifecycle winner دون rollback أو automatic retry، وتختار ownership finalization وفق الدليل.
- exception وmalformed/untrusted result ينتجان `OUTCOME_UNKNOWN_BLOCKED` مع ownership retained وclaim quarantined وsanitized diagnostic ودون signal لاحقة.
- تبقى Stage 7 authorization وlifecycle winner semantics دون تغيير بعد إضافة claim.
- Registry لا تفسر policy/lifecycle/signals، ولا يدعي العقد exactly-once أو distributed coordination أو restart durability.
- anti-bypass call-site/AST checks للمسار المرحّل.
- عدم تسريب secrets أو process identifiers الحساسة، وتوافق API ودلالات cancel الحالية، وعدم تراجع Slice 7.1.
- إثبات أن timeout/error/startup/shutdown/owner-conflict لم تدّع كمسارات مرحلة.

### 11. التحقق الموجه وحالة VERIFY

حفظت خطة RED/GREEN مجموعة التحقق المقترحة التالية:

- اختبار Stage 8.1 الجديد، وStage 7 cancel authorization suite.
- process cleanup manager tests، وprocess ownership contract/manager tests، وterminal reconciliation tests.
- Stage 5 cleanup lifecycle/audit/conformance tests، وAPI cancel tests إذا تأثرت.
- AST/call-site anti-bypass check، وsecret minimization check، وscope check، و`git diff --check`.

الأدلة الحالية:

- `RED_SHA256=affdc17067938d7e74ab44c1b3359b7ed1daff56499e929cfad64ac8fa7ac341`
- `SLICE8_1_TARGETED=53_PASSED`
- `MIGRATED_LEGACY_NODES=11_PASSED`
- `API_COMPOSITION_TARGETED=6_PASSED`
- `TARGETED_FAILURES=0`
- `PRE_CORRECTION_FULL_REGRESSION=735_COLLECTED_723_PASSED_12_FAILED`
- `PRE_CORRECTION_BLOCKERS=ADDRESSED_AND_FINAL_REGRESSION_PASSED`
- `SLICE8_1_IMPLEMENTATION_VERIFIED=YES`
- `FINAL_VERIFY_GATE=PASS`
- `FINAL_FULL_REGRESSION=736_COLLECTED_736_PASSED_0_FAILED_0_ERRORS`
- `FINAL_FULL_REGRESSION_DURATION=16.61s`
- `FINAL_FULL_REGRESSION_EXIT_CODE=0`

### 12. Stage 8 Exit Gap Audit وExit Accountability

`STAGE8_EXIT_ACCOUNTABILITY=MANDATORY`

- Slice 8.1 مكتملة ومتحققة وملتزمة ومزامنة عند `bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239` ضمن نطاقها، لكنها لا تغلق Stage 8.
- `SLICE8_2_AUTHORIZED=NO` و`STAGE8_CLOSURE=BLOCKED_PENDING_FINAL_EXIT_DISPOSITIONS_WITH_IMPLEMENTATION_AND_VERIFICATION_EVIDENCE`.
- تخضع هذه البنود لـExit Gap Review مستقل، ويحصل كل بند على حكم واحد فقط: `IMPLEMENTED_AND_VERIFIED` أو `NOT_REQUIRED_IN_CURRENT_SCOPE_WITH_EVIDENCE` أو `DEFERRED_OR_REALLOCATED_BY_EXPLICIT_OWNER_DECISION`.
- لا silent deferral ولا implicit roadmap scope reduction.

```text
SANDBOX_ISOLATION_CURRENT_STATUS=OPEN_REQUIRED
SANDBOX_ISOLATION_FINAL_DISPOSITION_RECORDED=NO
SANDBOX_ISOLATION_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED=IMPLEMENTED_AND_VERIFIED

RESOURCE_LIMITS_CURRENT_STATUS=OPEN_REQUIRED
RESOURCE_LIMITS_FINAL_DISPOSITION_RECORDED=NO
RESOURCE_LIMITS_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED=IMPLEMENTED_AND_VERIFIED

SECRETS_SAFETY_CURRENT_STATUS=PARTIAL_CANCEL_PATH_ONLY
SECRETS_SAFETY_FINAL_DISPOSITION_RECORDED=NO
SECRETS_SAFETY_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED=IMPLEMENTED_AND_VERIFIED

SAFE_PAUSE_RESUME_CURRENT_STATUS=OPEN_REQUIRED
SAFE_PAUSE_RESUME_FINAL_DISPOSITION_RECORDED=NO
SAFE_PAUSE_RESUME_PROPOSED_DISPOSITION_IF_COMPLETED_AND_VERIFIED=IMPLEMENTED_AND_VERIFIED
```

- أصغر اتجاه تالٍ معتمد للدراسة هو `LOCAL_PROCESS_LAUNCH_CONTAINMENT` ضمن Sandbox/Isolation وResource Limits عند launch فقط.
- `NEXT_DIRECTION_FINAL_CONTRACT=NO` و`NEXT_DIRECTION_RED=NO` و`NEXT_DIRECTION_GREEN=NO`؛ لا يبدأ هذا السجل Slice جديدة.
- Threat Model معتمدة للنطاق الحالي فقط، ولا يعني ذلك تنفيذ Sandbox أو Resource Limits. تشمل userspace behavior الخبيث أو المخترق، وتستبعد arbitrary hostile user code، ولا تدعي kernel escape resistance.
- filesystem مقيدة بأقل قراءة لازمة وكتابة إلى runtime paths مخصصة لكل Execution، مع رفض home وSSH/Git credentials ومسارات النظام القابلة للكتابة افتراضيًا. الشبكة outbound عند الحاجة الصريحة فقط، بلا inbound افتراضيًا ولا ادعاء egress allowlist.
- الهدف `MANAGED_LINUX` وCodespaces بيئة تطوير لا Reference Security Runtime. process-tree containment مطلوبة، وأبعاد الحدود CPU/memory/PIDs/FDs/output/wall-clock وقيمها قابلة للضبط وغير مجمدة معماريًا.
- systemd transient unit مع hardening صريح وcgroup v2 هو مرشح feasibility الأول فقط؛ ليس آلية معتمدة ولا منفذة ولا متحققة، ولا يحمل `IMPLEMENTED_AND_VERIFIED`.
- Rootless OCI بديل احتياطي جدي يعاد تقييمه عند فشل systemd في الحدود المطلوبة، أو الحاجة إلى فصل filesystem/runtime أقوى، أو ارتفاع أولوية portability بين المضيفين. التنفيذ الخام لـnamespaces/cgroups في Python غير موصى به.
- لا mechanism معتمدة ولا عقد containment مجمد ولا Reference Security Environment منشأة ولا تكلفة خارجية مأذونة. أي dependency خارجية يجب أن تكون pinned وقابلة للاستبدال وخلف عقد شجاع.
- Research Saturation مقيدة بالنطاق الحالي شبه الموثوق ذي shared kernel وليست عامة؛ لم يبدأ بحث العزل الأقوى، ويعاد فتح Threat Model إذا دخل hostile code مستقبلًا.
- Runtime Kill Switch primitive منفذة ومتحققة ضمن نطاقها، ولا يُدعى Full System أو Hierarchical Kill Switch.

### 13. Research Gate والحالة

`RESEARCH_GATE_REQUIRED=CONDITIONAL`

`RESEARCH_GATE_TRIGGERED=NO`

- لا يلزم بحث خارجي لحفظ هذا العقد؛ الشريحة محلية وframework-neutral، ولا تعتمد sandbox/container technology أو تجمد OS mechanism كعقد عام أو تضيف dependency أمنية خارجية.
- يصبح البحث إلزاميًا قبل اعتماد أو تجميد أي تقنية خارجية أو OS-specific public contract وفق Stage 8 Entry Gate.
- `STAGE8_STATUS=IN_PROGRESS_SLICE8_1_VERIFIED_EXIT_GAPS_OPEN` و`STAGE8_STARTED=YES` و`IMPLEMENTATION_STARTED=YES_FOR_SLICE8_1_COMMITTED_AND_SYNCED`؛ لا يعني إغلاق الشريحة اكتمال Stage 8.
- `SLICE8_1_RED_STARTED=YES` و`RED_GATE=PASS_CORRECTED` و`RED_AMENDMENT_REQUIRED=NO_COMPLETED`.
- `SLICE8_1_GREEN_STARTED=YES`، وbounded local atomic claim/finalize/quarantine وProduction composition wiring منفذة ومتحققة.
- الـ11 legacy fixtures مرحّلة، وanti-bypass RED مصححة، واختبار composition/API ناجح، ولا توجد legacy fallback في المسار المرحّل؛ Stage 5 وStage 7 regressions ناجحة.
- State Sync السابقة نجحت قبل إغلاق Slice 8.1، و`STATE_SYNC_REQUIRED_BEFORE_COMMIT=SATISFIED_FOR_SLICE8_1_CLOSURE_COMMIT`.
- `SLICE_CLOSED=YES` و`VERIFY_FINALIZED=YES` و`FINAL_FULL_REGRESSION=736_COLLECTED_736_PASSED_0_FAILED_0_ERRORS` و`COMMIT=YES_FOR_SLICE8_1_AT_bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239` و`PUSH=YES_FOR_SLICE8_1_REMOTE_VERIFIED_AT_bb4e2f7fa4111f1e3ca9a220dc1b39788bac5239`.
- `NEXT=WAIT_FOR_OWNER_STAGE8_REFERENCE_SECURITY_RUNTIME_ENVIRONMENT_DECISION`.

<!-- STAGE8_SLICE8_1_CONTRACT_END -->


<!-- CONTRACT_ADVERSARIAL_REVIEW_GATE_BEGIN -->
## Contract Adversarial Review Gate — Cross-Stage

**الحالة:** `ADOPTED — DESIGN/CONTRACT GATES ONLY`

قبل تقديم أي عقد Slice جديد أو تعديل عقد قائم للاعتماد، تنفذ مراجعة داخلية صامتة تغطي:

- الهوية والإصدارات ودلالات missing/empty/duplicate.
- cycles وtraversal وsnapshot isolation وimmutability وdeterminism.
- تعقيد البناء والاستعلام وتكلفة canonical ordering دون ادعاء رقمي غير مثبت.
- negative scope وحدود المراحل وanti-trigger tests.
- فصل proposal عن authorization، وعدم تحويل الترتيب اللاحق إلى خطة ملزمة.

تُحوّل النتائج المهمة إلى invariants ومعايير قبول قبل عرض العقد النهائي. تعمل هذه البوابة في مهام Design/Contract فقط، ولا تمنح إذن كتابة كود أو RED/GREEN أو commit/push، ولا تعدّل `Shujaa Development Skill` النشطة. أي ترتيب بعد الشريحة الحالية يبقى `CANDIDATE DIRECTION` حتى `NEXT_SLICE_DISCOVERY` مستقل.

<!-- CONTRACT_ADVERSARIAL_REVIEW_GATE_END -->


## Development Tooling and External-Idea Backlog

**تاريخ الاعتماد:** 24 أغسطس 2026
**الحالة:** `PLANNED BACKLOG — TRIGGERED EVALUATION ONLY`

هذا backlog لا يغيّر خارطة التنفيذ ذات 19 مرحلة، ولا يغيّر أسماء المراحل
أو ترتيبها أو نطاق Slice 6.1. إدراج أداة أو فكرة لا يعني اعتمادها أو
تثبيتها أو دمجها في production.

### Graphify Pilot

**Trigger:** بعد وجود commit نظيف ومتحقق لـStage 6.1.

الحدود:

- development-only.
- code-only وlocal AST أولًا.
- المخرجات خارج المستودع.
- لا production integration.
- لا Git hooks في البداية.
- لا تُرسل وثائق المشروع إلى external models.
- Graphify أداة navigation/index فقط.
- Git والكود والاختبارات والعقود السلطوية تبقى مصدر الحقيقة.

المقاييس:

- token/context reduction.
- files read.
- latency.
- correctness.
- stale-index risk.
- operational complexity.

### Deferred Development Ideas

| الفكرة | Trigger | نطاق التقييم فقط |
|---|---|---|
| OpenCode | مسار التطوير الحالي بعد evaluation | Development harness داخل Codespace فقط |
| MonkeyCode | مراجعة مستقبلية مستقلة | Cloud/mobile development UX |
| Prime Agent / Hermes | Stage 9 | Long-running goals، quality gates، bounded turns/time/tokens، resumability، controlled autonomy |
| MiniMax | Stages 12–13 | Provider/model performance وSkill lifecycle ideas |
| Apex | Stage 15 | Central command visualization، specialist-agent map، live task/state visibility، one-person-company model |

كل تقييم يخضع لـProvider Evaluation Gate المثبت في
`SHUJAA_HANDOFF.md`، ولا يصبح أي مزود اعتمادًا معماريًا.

### Scope Preservation

- لا تعديل على Stage 6.1.
- لا تغيير لترقيم أو نطاق المراحل اللاحقة.
- لا تثبيت Tools.
- لا production integration.
- لا تعديل على Manager أو Dispatcher أو AgentRegistry أو Event/Audit.
