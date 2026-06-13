create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  name varchar(120) not null,
  email varchar(255) not null unique,
  phone varchar(40),
  password_hash varchar(255) not null,
  role varchar(40) not null,
  status varchar(40) not null default 'active',
  locale varchar(20) not null default 'zh-TW',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists user_permissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  permission_key varchar(120) not null,
  scope varchar(40) not null default 'self',
  created_at timestamptz not null default now(),
  unique (user_id, permission_key, scope)
);

create table if not exists staff (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references users(id) on delete cascade,
  department varchar(80) not null,
  title varchar(120) not null,
  manager_id uuid references staff(id) on delete set null,
  hire_date date,
  kpi_target jsonb not null default '{}'::jsonb,
  status varchar(40) not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists teachers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references users(id) on delete cascade,
  specialties text,
  years_experience numeric(5,2),
  available_slots jsonb not null default '[]'::jsonb,
  bio text,
  rating numeric(3,2),
  contract_type varchar(40),
  pay_scheme varchar(40),
  created_at timestamptz not null default now()
);

create table if not exists courses (
  id uuid primary key default gen_random_uuid(),
  slug varchar(160) not null unique,
  name varchar(200) not null,
  course_type varchar(80) not null,
  level varchar(40),
  description text not null default '',
  objectives text not null default '',
  total_sessions integer not null default 0,
  session_minutes integer not null default 90,
  price numeric(12,2) not null default 0,
  delivery_mode varchar(40) not null default 'online',
  is_public boolean not null default true,
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists course_modules (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references courses(id) on delete cascade,
  title varchar(200) not null,
  sort_order integer not null default 0,
  description text not null default '',
  material_url text
);

create table if not exists classes (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references courses(id) on delete restrict,
  name varchar(200) not null,
  teacher_id uuid references teachers(id) on delete set null,
  start_date date not null,
  end_date date,
  weekday_mask varchar(40),
  start_time time,
  end_time time,
  capacity integer not null default 0,
  enrolled_count integer not null default 0,
  location_label varchar(160),
  meeting_url text,
  status varchar(40) not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists class_sessions (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references classes(id) on delete cascade,
  module_id uuid references course_modules(id) on delete set null,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  teacher_id uuid references teachers(id) on delete set null,
  classroom varchar(160),
  meeting_url text,
  status varchar(40) not null default 'scheduled',
  lesson_plan text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  name varchar(120) not null,
  phone varchar(40),
  email varchar(255),
  line_id varchar(120),
  source_channel varchar(80) not null default 'website',
  campaign_name varchar(160),
  interested_course_id uuid references courses(id) on delete set null,
  budget_range varchar(80),
  japanese_level varchar(40),
  study_goal text,
  departure_plan_date date,
  intent_score numeric(5,2),
  win_probability numeric(5,2),
  status varchar(40) not null default 'new',
  assigned_staff_id uuid references staff(id) on delete set null,
  last_contact_at timestamptz,
  next_follow_up_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists lead_logs (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references leads(id) on delete cascade,
  staff_id uuid references staff(id) on delete set null,
  contact_method varchar(40) not null,
  content text not null,
  next_action text,
  created_at timestamptz not null default now()
);

create table if not exists trial_bookings (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid not null references leads(id) on delete cascade,
  course_id uuid references courses(id) on delete set null,
  class_id uuid references classes(id) on delete set null,
  slot_start_at timestamptz not null,
  slot_end_at timestamptz not null,
  status varchar(40) not null default 'booked',
  feedback text,
  created_at timestamptz not null default now()
);

create table if not exists students (
  id uuid primary key default gen_random_uuid(),
  user_id uuid unique references users(id) on delete set null,
  chinese_name varchar(120) not null,
  english_name varchar(120),
  japanese_name varchar(120),
  gender varchar(40),
  nationality varchar(80),
  native_language varchar(80),
  age_group varchar(40),
  city varchar(80),
  japanese_level varchar(40),
  study_goal text,
  source_channel varchar(80),
  consultant_id uuid references staff(id) on delete set null,
  status varchar(40) not null default 'active',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists enrollments (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references students(id) on delete cascade,
  class_id uuid not null references classes(id) on delete restrict,
  lead_id uuid references leads(id) on delete set null,
  enrolled_at timestamptz not null default now(),
  status varchar(40) not null default 'pending',
  payment_status varchar(40) not null default 'unpaid',
  coupon_code varchar(80),
  list_price numeric(12,2) not null default 0,
  paid_amount numeric(12,2) not null default 0,
  consultant_id uuid references staff(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists payments (
  id uuid primary key default gen_random_uuid(),
  enrollment_id uuid not null references enrollments(id) on delete cascade,
  order_no varchar(120) not null unique,
  amount numeric(12,2) not null default 0,
  payment_method varchar(40) not null,
  status varchar(40) not null default 'pending',
  paid_at timestamptz,
  invoice_data jsonb not null default '{}'::jsonb,
  gateway_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists attendance (
  id uuid primary key default gen_random_uuid(),
  class_session_id uuid not null references class_sessions(id) on delete cascade,
  student_id uuid not null references students(id) on delete cascade,
  status varchar(40) not null,
  notes text,
  created_at timestamptz not null default now(),
  unique (class_session_id, student_id)
);

create table if not exists assignments (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references classes(id) on delete cascade,
  class_session_id uuid references class_sessions(id) on delete set null,
  title varchar(200) not null,
  content text not null,
  due_at timestamptz,
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists assignment_submissions (
  id uuid primary key default gen_random_uuid(),
  assignment_id uuid not null references assignments(id) on delete cascade,
  student_id uuid not null references students(id) on delete cascade,
  content text not null,
  score numeric(6,2),
  feedback text,
  submitted_at timestamptz,
  created_at timestamptz not null default now(),
  unique (assignment_id, student_id)
);

create table if not exists exams (
  id uuid primary key default gen_random_uuid(),
  class_id uuid not null references classes(id) on delete cascade,
  title varchar(200) not null,
  exam_type varchar(40) not null,
  total_score numeric(6,2) not null default 100,
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists exam_results (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid not null references exams(id) on delete cascade,
  student_id uuid not null references students(id) on delete cascade,
  score numeric(6,2),
  result_level varchar(40),
  feedback text,
  created_at timestamptz not null default now(),
  unique (exam_id, student_id)
);

create table if not exists job_positions (
  id uuid primary key default gen_random_uuid(),
  title varchar(160) not null,
  department varchar(80) not null,
  description text not null,
  requirements text not null,
  salary_range varchar(120),
  location varchar(120),
  status varchar(40) not null default 'draft',
  created_at timestamptz not null default now()
);

create table if not exists applicants (
  id uuid primary key default gen_random_uuid(),
  position_id uuid not null references job_positions(id) on delete cascade,
  name varchar(120) not null,
  email varchar(255),
  phone varchar(40),
  resume_url text,
  interview_status varchar(40) not null default 'new',
  ai_match_score numeric(5,2),
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists interviews (
  id uuid primary key default gen_random_uuid(),
  applicant_id uuid not null references applicants(id) on delete cascade,
  interview_at timestamptz not null,
  interviewer_id uuid references staff(id) on delete set null,
  rating numeric(5,2),
  summary text,
  recommendation varchar(40),
  result varchar(40) not null default 'pending',
  created_at timestamptz not null default now()
);

create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  channel varchar(40) not null,
  type varchar(80) not null,
  title varchar(200) not null,
  content text not null,
  status varchar(40) not null default 'queued',
  sent_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists ai_logs (
  id uuid primary key default gen_random_uuid(),
  module_name varchar(80) not null,
  user_id uuid references users(id) on delete set null,
  action_name varchar(120) not null,
  input_summary text,
  output_summary text,
  model_name varchar(80),
  status varchar(40) not null default 'success',
  created_at timestamptz not null default now()
);

create index if not exists idx_users_role on users(role);
create index if not exists idx_users_status on users(status);
create index if not exists idx_staff_department on staff(department);
create index if not exists idx_courses_public on courses(is_public);
create index if not exists idx_classes_course_id on classes(course_id);
create index if not exists idx_classes_status on classes(status);
create index if not exists idx_class_sessions_class_id on class_sessions(class_id);
create index if not exists idx_class_sessions_start on class_sessions(starts_at);
create index if not exists idx_leads_status on leads(status);
create index if not exists idx_leads_assigned_staff_id on leads(assigned_staff_id);
create index if not exists idx_leads_source_channel on leads(source_channel);
create index if not exists idx_leads_next_follow_up_at on leads(next_follow_up_at);
create index if not exists idx_lead_logs_lead_id on lead_logs(lead_id);
create index if not exists idx_trial_bookings_lead_id on trial_bookings(lead_id);
create index if not exists idx_trial_bookings_slot_start_at on trial_bookings(slot_start_at);
create index if not exists idx_students_consultant_id on students(consultant_id);
create index if not exists idx_enrollments_student_id on enrollments(student_id);
create index if not exists idx_enrollments_class_id on enrollments(class_id);
create index if not exists idx_enrollments_payment_status on enrollments(payment_status);
create index if not exists idx_payments_enrollment_id on payments(enrollment_id);
create index if not exists idx_payments_status on payments(status);
create index if not exists idx_notifications_user_id on notifications(user_id);
create index if not exists idx_notifications_status on notifications(status);
create index if not exists idx_ai_logs_module_name on ai_logs(module_name);
create index if not exists idx_ai_logs_created_at on ai_logs(created_at desc);
