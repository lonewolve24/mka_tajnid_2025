# MKA Tajnid – Implementation Plan

## Overview

Build a **program-scoped, role-aware registration system** where:
- Admin creates and manages programs.
- Each user is assigned a default program and a role.
- On login the app automatically sets the active program context.
- All data entry and listing is scoped to the active program.
- Male/female records are further restricted by user role.

---

## Phase 1 – Core (implementing now)

### 1. Program Model
Fields: `name`, `year`, `is_active`
- `year` is metadata for reporting/filtering only.
- `name` + `year` must be unique.
- Admin-only CRUD.

### 2. UserProfile Model
Fields: `user` (OneToOne), `default_program` (FK → Program), `role`

Role choices:
| Role | What they see/do |
|---|---|
| `admin` | All programs, all genders, full CRUD |
| `program_manager` | Assigned program, all genders, full CRUD |
| `male_data_entry` | Assigned program, male records only |
| `female_data_entry` | Assigned program, female records only |
| `viewer` | Assigned program, all genders, read-only |

### 3. Session Context
- On login: load `user.profile.default_program` → store `active_program_id` in session.
- Every protected view calls `get_active_program(request)`:
  - If no program assigned → redirect to `no_program` page with "Contact admin" message.
  - Admin bypasses program restriction (sees all).

### 4. Registration Fields
- `gender`: `Male` | `Female` (required)
- `auxiliary_body` choices split by gender:
  - **Male**: Atfal, Khuddam, Ansar, Guest
  - **Female**: Lajina, Nasirat
- Server-side validation enforces correct gender ↔ auxiliary_body combination.
- Frontend JS dynamically filters auxiliary body dropdown on gender change.

### 5. View Scoping Rules
Every view enforces this order of filters:
1. Authenticated user check.
2. Active program check (redirect to `no_program` if missing).
3. Role-based gender filter:
   - `admin` / `program_manager` / `viewer` → no gender restriction.
   - `male_data_entry` → `.filter(gender='Male')`.
   - `female_data_entry` → `.filter(gender='Female')`.
4. User-requested filters (search, region, auxiliary body, gender UI filter — admin only).

### 6. Form Behavior
- `program` field removed from user-facing registration form.
- Program is assigned automatically from session active program.
- On create: `registration.program = get_active_program(request)`.
- On update: verify `registration.program == active_program` or deny.
- On delete: same verification.

### 7. Admin Overview
- Admin sees all registrations across all programs.
- Filters available: program, year, gender, region, auxiliary body.
- Export (CSV/PDF) respects admin filters.
- `UserProfile` inline editable on User admin page.

### 8. UI Changes
- Navbar badge: **"Program: [name] ([year])"** always visible when logged in.
- If `admin` role: badge shows "Admin – All Programs".
- `no_program.html`: clean "No program assigned – contact your administrator" page.
- Registration form: gender change triggers auxiliary body dropdown refresh via JS.

---

## Phase 2 – (after Phase 1 is stable)

- Allow users to have multiple allowed programs (not just one default).
- Program-switch UI for `program_manager` and `admin`.
- Audit log: `created_by`, `updated_by` on Registration.
- Group/permission-based expansion using Django groups.
- Cross-program report view for admin (compare programs side by side).
- Email notifications for admin on new program setup.

---

## File-by-File Change Map

| File | Changes |
|---|---|
| `tagnid/models.py` | Remove `database_key`, add `UserProfile` |
| `tagnid/forms.py` | Remove `program` field, add gender validation |
| `tagnid/views.py` | Add `get_active_program()`, scope all views, role filter |
| `tagnid/admin.py` | Remove `database_key`, add `UserProfileInline` |
| `tagnid/service.py` | Pass `program` and `gender` automatically |
| `tagnid/urls.py` | Add `no_program` URL |
| `tagnid/templates/tagnid/base.html` | Add program badge in navbar |
| `tagnid/templates/tagnid/registration_form.html` | Remove program field, add gender JS |
| `tagnid/templates/tagnid/registration_list.html` | Scope-aware filter UI |
| `tagnid/templates/tagnid/no_program.html` | New: contact admin page |
| `tagnid/migrations/` | New migration for Program + UserProfile |

---

## Key Rules (never break these)

1. A registration can never be created without an active program.
2. Male-only auxiliary bodies cannot be saved on a female record (and vice versa).
3. Non-admin users can never see or modify records outside their assigned program.
4. `admin` role always bypasses program and gender restrictions.
5. Program setup is admin-only — no user-facing program creation.
