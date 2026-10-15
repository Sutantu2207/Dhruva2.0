# DHRUVA.AI (V2) — ASSESSMENT FRONTEND & QUESTION BANK ARCHITECTURE

> **Component:** Assessment Frontend & Evaluation Workspace  
> **Phase:** Phase 5 — Question Bank, Assessments & Deterministic Grading UI  
> **Route:** `/workspace/assessments`  
> **Standard:** Production-Grade / Zero-Mock Data / Strict Role-Based Access Isolation  

---

## 1. Overview & Architectural Principles

The Phase 5 Assessment Frontend implements the complete institutional testing lifecycle for Dhruva.AI V2:
1. **Question Bank Studio**: Faculty-facing authoring suite supporting Single-Choice MCQ, Multi-Select Choice, Numerical with tolerance intervals, and Structured Text with grading rubrics.
2. **Assessment Builder**: Course offering scheduling, duration limits, attempt limits, question allocation, and publication state machine (`DRAFT` $\to$ `PUBLISHED` $\to$ `CLOSED`).
3. **Student Assessment Runner**: Server-authoritative timing, sanitized student view with zero answer-key leakage, interactive navigation, and atomic submission.
4. **Transparent Grading & Manual Evaluation**: Itemized deterministic scoring breakdown and audit-trailed manual evaluation for subjective questions.

### Core Invariants Enforced
- **Zero Answer Key Leakage**: Student testing endpoints strictly strip `answer_key`, `explanation`, and privileged rubrics at both the network and UI levels.
- **Authoritative Timing Gates**: Time windows (`publish_at`, `due_at`) and durations are validated and gated by the server's authoritative UTC clock.
- **Immutability on Publication**: Questions and point allocations cannot be mutated once an assessment transitions to `PUBLISHED`.
- **Zero Hallucination Grading**: All autograded points are computed deterministically (exact match for MCQ, proportional partial credit with guessing penalty for Multi-Select, tolerance boundaries for Numerical).

---

## 2. Implemented Screens & Workspaces

The assessment workspace is located at `/workspace/assessments` and features role-sensitive views:

### 2.1 Tab 1: Question Bank Studio (`isStaff` only)
- **Question Banks Directory**: Lists institutional banks filtered by course or department.
- **Question Authoring Modal**:
  - `MCQ`: Dynamic options with radio selector designating the single correct answer.
  - `MULTI_SELECT`: Dynamic options with multi-check boxes designating all correct answers.
  - `NUMERICAL`: Target value and allowed symmetric tolerance interval ($\pm \Delta$).
  - `STRUCTURED_TEXT`: Sample solution and grading rubric.
  - Allocated marks, difficulty (`EASY`, `MEDIUM`, `HARD`), and post-assessment educational rationale.
- **Authoritative Item Inspector**: Displays authored questions with full answer keys and explanations visible only to authorized staff.

### 2.2 Tab 2: Assessment Builder (`isStaff` only)
- **Assessment Directory**: Filterable list of assessments across lifecycle states (`DRAFT`, `PUBLISHED`, `CLOSED`).
- **Configuration Modal**: Title, Course Offering UUID, assessment type (`QUIZ`, `ASSIGNMENT`, `MIDTERM`, `FINAL_EXAM`), local duration minutes, passing percentage, and max attempts.
- **Question Allocator**: Links questions from authoring banks with assessment-specific mark allocations and sequence ordering.
- **Lifecycle Action Gates**:
  - `Publish Assessment`: Locks questions immutably and exposes assessment to enrolled students.
  - `Close Assessment`: Shuts down new attempts and finalizes autograded results.

### 2.3 Tab 3: Deterministic & Manual Evaluation Center (`isStaff` only)
- **Assessment Submissions Browser**: Select any assessment to inspect all student attempts in a structured table (Student UUID, Attempt #, Status, Submitted Timestamp, Score).
- **Direct Submission Lookup**: Input direct submission UUID for immediate verification.
- **Itemized Breakdown Inspector**: Transparent display of question type, awarded points vs. allocated points, and grading notes.
- **Subjective Manual Evaluator Modal**: For `STRUCTURED_TEXT` items in `PENDING_MANUAL` status, faculty can enter awarded marks (validated $\le$ allocated points) and audit feedback, which invokes the backend manual grading endpoint and transitions submission to `GRADED`.

### 2.4 Tab 4: Student Assessment Runner & Performance Report
- **Assessment Launch Portal**: Displays published assessments available to the student.
- **Sanitized Test Runner**:
  - Live countdown timer based on server duration.
  - Question navigation bubbles with answered/unanswered progress tracking.
  - Dedicated input controls per question type.
  - Finalization confirmation modal to prevent accidental submissions.
- **Deterministic Performance Report**:
  - High-impact metrics: Raw Score, Total Points, Percentage, Passing Status badge, Grade Letter.
  - Itemized breakdown table detailing autograded formulas and feedback notes.

---

## 3. API Endpoints Used

All requests use the centralized `api` HTTP client with Bearer authentication and multi-tenant correlation IDs:

| Action | Method & Endpoint | Payload / Parameters | Access Control |
|---|---|---|---|
| List Question Banks | `GET /institutions/{slug}/question-banks` | `course_id`, `department_id`, `page`, `page_size` | Staff Roles |
| Create Question Bank | `POST /institutions/{slug}/question-banks` | `title`, `description`, `course_id` | Staff Roles |
| Author Question | `POST /institutions/{slug}/question-banks/{id}/questions` | `question_type`, `prompt_text`, `answer_key`, `options`, `points`, `difficulty` | Staff Roles |
| List Bank Questions | `GET /institutions/{slug}/question-banks/{id}/questions` | `bank_id`, `question_type` | Staff Roles |
| Create Assessment Draft | `POST /institutions/{slug}/assessments` | `course_offering_id`, `title`, `assessment_type`, `publish_at`, `due_at`, `duration_minutes` | Staff Roles |
| List Assessments | `GET /institutions/{slug}/assessments` | `course_offering_id`, `status`, `page`, `page_size` | Authenticated |
| Get Assessment (Student) | `GET /institutions/{slug}/assessments/{id}` | Sanitized view with zero answer keys | Students / Enrolled |
| Get Assessment (Staff) | `GET /institutions/{slug}/assessments/{id}` | Full author view with question details | Staff Roles |
| Link Question | `POST /institutions/{slug}/assessments/{id}/questions` | `question_id`, `points`, `sort_order` | Staff Roles |
| Publish Assessment | `POST /institutions/{slug}/assessments/{id}/publish` | `{}` | Staff Roles |
| Close Assessment | `POST /institutions/{slug}/assessments/{id}/close` | `{}` | Staff Roles |
| Submit Assessment | `POST /institutions/{slug}/assessments/{id}/submit` | `answers_payload` (mapping `question_id` to answer) | Students |
| List Submissions | `GET /institutions/{slug}/assessments/{id}/submissions` | `status`, `page`, `page_size` | Staff Roles |
| Get Submission Detail | `GET /institutions/{slug}/submissions/{id}` | `submission_id` | Submitter or Staff |
| Grade Subjective Answer | `POST /institutions/{slug}/submissions/{id}/grade-manual` | `question_id`, `awarded_points`, `feedback` | Staff Roles |

---

## 4. Test Verification Results

### 4.1 Frontend Test Suite (`npm test`)
Executed via Node `--test` test runner:
- **`src/__tests__/assessment.test.ts`**:
  - Deterministic grading algorithms (MCQ exact match, multi-select partial credit + guessing penalty, numerical tolerance checks): **4/4 passed**.
  - Student answer-key sanitization guardrail (zero leaks): **1/1 passed**.
  - Assessment state machine transitions (`DRAFT` $\to$ `PUBLISHED` $\to$ `CLOSED`): **3/3 passed**.
  - Assessment RBAC permission guardrails: **3/3 passed**.
  - Question form validation guards (options validation, numerical bounds): **2/2 passed**.
  - Student answer entry & duplicate submission protection: **2/2 passed**.
  - Manual subjective evaluation constraints: **1/1 passed**.
- **Total Frontend Tests**: **30 passed / 0 failed / 11 test suites**.

### 4.2 TypeScript Compilation & Next.js Build
- **Typecheck**: `npm run typecheck` (`tsc --noEmit`) $\to$ **Zero errors**.
- **Production Build**: `npm run build` (`next build`) $\to$ **Static generation of 10/10 routes successfully completed**.

### 4.3 Backend Assessment Regression Tests
- **`tests/test_assessment_engine.py`**: **11/11 tests passed**.
- **Full Backend Suite**: **75/75 tests passed**.

---

## 5. Security & RBAC Enforcement Summary

1. **Role Gating**:
   - `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD`, `FACULTY`: Allowed question authoring, assessment publishing, and manual evaluation.
   - `STUDENT`: Allowed assessment taking and personal submission result inspection.
2. **Timing Gating**:
   - Submissions past `due_at` or before `publish_at` rejected with 403 Forbidden by backend.
3. **State Machine Locking**:
   - `publish_assessment` sets assessment status to `PUBLISHED` and prevents further question additions or removals.
