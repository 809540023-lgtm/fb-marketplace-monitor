# Frontend Workstream

This document translates the platform sitemap and MVP backlog into a frontend delivery spec. Scope is frontend only: routes, page responsibilities, shared UI inventory, data/state needs, form flows, and a three-sprint delivery order.

## 1. Frontend Scope

The frontend is split into four entry surfaces:

1. Public marketing site
2. Student portal
3. Staff workspace
4. Admin console

The MVP frontend should optimize for one business loop first:

`visit -> course view -> trial booking or application -> lead capture -> payment -> confirmation`

Everything else should support that loop without blocking it.

---

## 2. Route Map

### 2.1 Public Site

- `/`
  - Brand landing page
  - Primary CTA to trial booking and application
- `/about`
  - Brand story, teaching philosophy, team
- `/courses`
  - Public course catalog
- `/courses/[slug]`
  - Course detail page with classes and CTA
- `/trial-booking`
  - Trial lesson booking flow
- `/apply`
  - Enrollment and payment flow
- `/faq`
  - Common questions and objections
- `/testimonials`
  - Student success stories
- `/contact`
  - Contact methods and inquiry form
- `/jobs`
  - Public recruiting page

### 2.2 Student Portal

- `/student`
  - Student dashboard
- `/student/courses`
  - Enrolled courses and schedules
- `/student/homework`
  - Assignments and submissions
- `/student/exams`
  - Quiz and exam results
- `/student/payments`
  - Order and payment history
- `/student/notifications`
  - In-app messages
- `/student/ai-practice`
  - AI learning practice space

### 2.3 Staff Workspace

- `/staff`
  - Staff dashboard
- `/staff/leads`
  - Assigned leads and follow-ups
- `/staff/leads/[id]`
  - Lead detail, notes, timeline, AI draft
- `/staff/tasks`
  - Task list and follow-up reminders
- `/staff/classes`
  - My classes and teaching schedule
- `/staff/performance`
  - Personal KPI summary

### 2.4 Admin Console

- `/admin/login`
  - Authentication entry
- `/admin`
  - Operational dashboard
- `/admin/leads`
  - CRM list and filtering
- `/admin/leads/[id]`
  - Lead detail and pipeline control
- `/admin/courses`
  - Course management
- `/admin/classes`
  - Class management and openings
- `/admin/enrollments`
  - Enrollment and payment review
- `/admin/staff`
  - Employees and role management

---

## 3. Page Responsibilities

### 3.1 Public Site

#### `/`

Responsibilities:

- Explain the brand in one screen
- Surface the main course categories
- Drive users to trial booking or application
- Capture trust through testimonials and FAQ
- Expose AI chat as a conversion helper

#### `/courses`

Responsibilities:

- Present public courses in a scannable list
- Support filtering by goal, level, and delivery mode
- Route users into the right course detail page

#### `/courses/[slug]`

Responsibilities:

- Explain one course clearly
- Show who it is for, what it includes, and how it runs
- Show open classes and clear CTAs

#### `/trial-booking`

Responsibilities:

- Collect lead data with minimal friction
- Let users choose a time slot
- Capture goal and current Japanese level

#### `/apply`

Responsibilities:

- Collect enrollment details
- Let users choose class and payment method
- Confirm the enrollment and payment outcome

#### `/jobs`

Responsibilities:

- List open roles
- Convert candidates into applicants through one form

### 3.2 Student Portal

#### `/student`

Responsibilities:

- Show a personal learning snapshot
- Surface next class, pending work, and payment reminders

#### `/student/courses`

Responsibilities:

- Show active and completed enrollments
- Show course schedule, materials, and class links

#### `/student/homework`

Responsibilities:

- Show pending assignments
- Support homework submission and review status

#### `/student/exams`

Responsibilities:

- Show test history and scores
- Display simple learning progress signals

#### `/student/payments`

Responsibilities:

- Show order history and invoice data
- Expose payment status clearly

#### `/student/ai-practice`

Responsibilities:

- Offer practice exercises
- Show AI-generated summaries and weak-point hints

### 3.3 Staff Workspace

#### `/staff`

Responsibilities:

- Show daily tasks, follow-ups, and class schedule

#### `/staff/leads`

Responsibilities:

- Show assigned leads only
- Make follow-up actions fast and repeatable

#### `/staff/leads/[id]`

Responsibilities:

- Show lead profile, timeline, notes, and next action
- Provide AI follow-up draft as an assistive action

#### `/staff/tasks`

Responsibilities:

- Show task queue and overdue items

#### `/staff/classes`

Responsibilities:

- Show teaching schedule and class access points

#### `/staff/performance`

Responsibilities:

- Summarize lead handling, trial count, and conversion output

### 3.4 Admin Console

#### `/admin`

Responsibilities:

- Provide the operational overview
- Highlight the metrics that need attention now

#### `/admin/leads`

Responsibilities:

- Manage the lead funnel
- Filter by source, owner, stage, and follow-up date

#### `/admin/leads/[id]`

Responsibilities:

- Show full lead context
- Allow assignment, status transitions, and note history

#### `/admin/courses`

Responsibilities:

- Create and edit public courses
- Toggle public visibility

#### `/admin/classes`

Responsibilities:

- Create classes
- Assign teachers
- Control capacity and schedule visibility

#### `/admin/enrollments`

Responsibilities:

- Review enrollment and payment state
- Confirm or correct operational records

#### `/admin/staff`

Responsibilities:

- Manage staff accounts, roles, and basic profile data

---

## 4. Shared Component Inventory

### 4.1 Layout

- `PublicShell`
- `StudentShell`
- `StaffShell`
- `AdminShell`
- `TopNav`
- `SideNav`
- `Footer`
- `MobileMenu`
- `Breadcrumbs`

### 4.2 Conversion Components

- `HeroBanner`
- `CourseCard`
- `CourseFilterBar`
- `TestimonialCarousel`
- `FaqAccordion`
- `CtaStrip`
- `TrustBadgeRow`
- `LeadCaptureForm`
- `TrialBookingForm`
- `EnrollmentForm`
- `PaymentSummaryCard`

### 4.3 Data Display Components

- `MetricCard`
- `StatusBadge`
- `Timeline`
- `DataTable`
- `EmptyState`
- `LoadingSkeleton`
- `InlineError`
- `PillFilter`
- `SearchInput`

### 4.4 Operational Components

- `LeadTimeline`
- `LeadNotesPanel`
- `AssignmentList`
- `ClassScheduleGrid`
- `PaymentStatusPanel`
- `NotificationInbox`
- `PerformanceSummary`
- `AiSuggestionPanel`

### 4.5 Form Components

- `TextField`
- `TextAreaField`
- `SelectField`
- `MultiSelectField`
- `DatePicker`
- `TimeSlotPicker`
- `PhoneField`
- `EmailField`
- `FileUploadField`
- `OtpField`
- `SubmitBar`

---

## 5. State and Data Needs

### 5.1 Global State

Required frontend global state:

- authenticated user
- current role
- permissions and scope
- locale and language
- notification count
- selected branch if multi-branch is enabled later

Recommended state ownership:

- server state for records and lists
- local state for form inputs and modal interactions
- URL state for filters and pagination

### 5.2 Public Site State

Needs:

- course list
- featured courses
- open classes by course
- FAQ content
- testimonials
- trial slot availability

Caching guidance:

- cache marketing content aggressively
- revalidate course and FAQ data on deploy or CMS change

### 5.3 CRM State

Needs:

- lead list
- lead detail
- lead logs
- trial booking list
- assigned staff
- follow-up timestamps

UI behavior:

- filter state must stay in the URL
- lead detail should preserve timeline scroll and selected tab

### 5.4 Enrollment and Payment State

Needs:

- selected course
- selected class
- student identity
- coupon code
- payment intent or order status

UI behavior:

- preserve form progress across step changes
- show final confirmation state clearly

### 5.5 Student Portal State

Needs:

- enrolled courses
- current class sessions
- assignments
- exam results
- payment history
- notifications

UI behavior:

- show only relevant active items first
- allow empty states to guide first actions

### 5.6 Staff/Admin State

Needs:

- assigned leads or all leads depending on scope
- class schedules
- task queue
- KPI metrics
- admin summaries

UI behavior:

- table filters must be fast and persistent
- destructive actions need confirmation

---

## 6. Form Flows

### 6.1 Trial Booking Flow

Steps:

1. Choose course or goal
2. Choose available slot
3. Enter name, phone, email, Japanese level, and goal
4. Optionally connect LINE
5. Review and submit
6. Show success page and next-step guidance

Validation rules:

- name, phone, and one contact method are required
- slot must be available at submit time
- duplicate lead detection should warn, not hard fail

### 6.2 Enrollment Flow

Steps:

1. Choose course
2. Choose class
3. Enter student profile
4. Apply coupon if available
5. Review fee summary
6. Pay
7. Show confirmation and account next steps

Validation rules:

- class capacity must be checked before payment intent creation
- required profile fields should be validated before payment
- show payment failure recovery path

### 6.3 Lead Follow-up Flow

Steps:

1. Open lead detail
2. Add note or follow-up action
3. Use AI draft if needed
4. Change status
5. Schedule next follow-up

Validation rules:

- notes cannot be empty if next action is created
- only assigned or permitted staff can update the lead

### 6.4 Course and Class Management Flow

Steps:

1. Create course
2. Add course modules
3. Create class
4. Assign teacher and schedule
5. Open class for enrollment

Validation rules:

- class cannot open without teacher and schedule
- capacity must be greater than enrolled count

### 6.5 Applicant Flow

Steps:

1. Open jobs page
2. Choose role
3. Fill application form
4. Upload resume
5. Submit
6. Show acknowledgment

Validation rules:

- required fields must be completed before file upload is accepted

---

## 7. Delivery Order for 3 Sprints

### Sprint 1: Public Conversion Core

Goal:

Ship the minimum public experience that can generate leads.

Deliver:

- public shell and responsive layout
- homepage
- course list
- course detail
- trial booking form
- application form
- success pages
- shared conversion components

Frontend priorities:

- form UX
- mobile responsiveness
- clear CTAs
- fast loading public pages

### Sprint 2: Admin and Staff Operations

Goal:

Let internal users handle leads, courses, and enrollments.

Deliver:

- admin login
- admin dashboard
- lead list
- lead detail
- course management
- class management
- enrollment and payment review
- staff workspace shell
- lead follow-up panel

Frontend priorities:

- dense but readable data tables
- filters and saved query state
- timeline and detail views
- role-based navigation

### Sprint 3: Student Portal and AI Assist

Goal:

Add the learner experience and AI-assisted productivity features.

Deliver:

- student dashboard
- enrolled courses view
- homework and exam views
- notifications center
- AI practice area
- AI follow-up draft panel
- performance summary cards

Frontend priorities:

- clear empty states
- progressive disclosure
- low-friction learning actions
- AI suggestions as assistive, not mandatory

---

## 8. Recommended Frontend Architecture

- Next.js App Router
- Server Components for data-heavy pages where practical
- Client Components for forms, filters, tables, and interactive panels
- Route groups for `public`, `student`, `staff`, and `admin`
- Shared UI primitives in a single design system layer
- React Query or equivalent for server state if the team prefers explicit client caching
- Zod or similar schema validation shared with form logic

---

## 9. Frontend Acceptance Criteria

- Public pages are usable on mobile and desktop.
- Trial and enrollment flows are reachable within three to four interactions from the homepage.
- Admin and staff pages enforce role-based access at the UI level.
- Forms preserve partial input and surface validation clearly.
- AI panels never block manual completion of a task.
- Empty states always suggest the next useful action.

---

## 10. Notes for Execution

- Treat marketing content as static-ish and optimize for speed.
- Treat CRM and operational pages as server-driven, filterable, and auditable.
- Keep AI features additive in the UI, never mandatory for core workflows.
- Preserve a clear separation between public conversion content and authenticated operations.
