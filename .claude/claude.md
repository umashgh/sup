# sup — Financial Freedom Planning App

Mobile-first financial planning app for Indian households. Helps salaried individuals and startup founders determine if they can "free up" from regular jobs to pursue passions. Guest-friendly — no signup required, anonymous sessions via `guest_<uuid>`.

## Tech Stack

- **Backend**: Django 5.2 + Django REST Framework, Python 3.12, SQLite (dev)
- **Primary Frontend**: Django templates + Alpine.js 3.x + Chart.js 4.x (mobile-first, no build step)
- **Secondary Frontend**: Ionic React 8.5 + React 19 + Vite 5 (less developed, in `sup_frontend/`)
- **MCP Server**: Python MCP server for PDF/EPUB knowledge base (`sup_mcp/`)
- **Key deps**: `django-htmx`, `pandas`, `whitenoise`, `pypdf`, `rank_bm25`

## Project Structure

```
sup_backend/          Django project with 3 apps: core, finance, ventures
  core/               Scenario management, question system, calculators
  finance/            Financial data models (FamilyProfile, Asset, Income, Expense)
  ventures/           Startup founder models (Venture, StartupCost, FounderSalary)
  templates/          Alpine.js mobile templates
  static/css/         Mobile CSS
sup_frontend/         Ionic React app (separate, less developed)
sup_mcp/              MCP knowledge base server (PDF/EPUB indexing + BM25 search)
docs/                 Domain knowledge, requirements, research
  domain.md           Comprehensive domain knowledge (42KB) — READ THIS for financial logic
  reqs.md             Technical requirements
ref/                  Reference PDFs/EPUBs
```

## Architecture

### Progressive Disclosure (3-Tier System)
- **QUICK**: Fast estimates, ~3 minutes (14 screens solo, up to 17 for joint family)
- **STANDARD**: Detailed 20-year projections, ~7 minutes (adds 5–7 screens on top of QUICK)
- **ADVANCED**: Monte Carlo, tax optimization (not yet implemented)

### 5 Scenarios
- FOUNDER, RETIREMENT — implemented
- R2I, HALF_FIRE, TERMINATION — models exist, calculators not implemented

### Calculator Strategy Pattern
`(scenario_type, tier)` maps to a calculator class in `core/calculators/`. All calculators inherit from `BaseCalculator` (abstract) with `calculate()` and `get_required_fields()` methods.

### Dynamic Question System
Questions with conditional logic defined in `core/questions.py`. 4 input types: `card_select`, `slider`, `amount_slider`, `toggle`. Questions can depend on previous answers.

### State Management
SessionStorage used for tier advancement state (not DB-persisted for guests). Keys: `tier_1_answers`, `advancing_to_tier_2`, `calculation_results`.

## Key Models

- `ScenarioProfile` (core) — scenario type + scenario-specific fields (ages, pension, salary, severance, etc.)
- `FamilyProfile` (finance) — family structure, wealth/income/expense levels (1-3), budget splits (Needs/Wants/Savings default 50/30/20), emergency fund months
- `FamilyMember` (finance) — earning adults, dependent adults, children, pets
- `Asset` (finance) — 4 types: Liquid, Semi-liquid, Growth, Property with start/end years, appreciation/return rates
- `Income` / `Expense` (finance) — passive income streams, needs/wants/savings categorization
- `Venture`, `StartupCost`, `FounderSalary` (ventures) — founder-specific

## API Endpoints

### Core
- `POST /start/` — guest login (creates anonymous user)
- `POST /api/scenarios/select/` — select scenario type
- `POST /api/scenarios/questions/` — get next questions (with conditional logic)
- `POST /api/scenarios/calculate/` — run calculation for current tier
- `POST /api/scenarios/advance-tier/` — advance QUICK → STANDARD → ADVANCED

### Finance REST API (`/api/finance/`)
- ViewSets for: profile, members, assets, incomes, expenses, masters (read-only)
- `GET /api/finance/project/` — projection with austerity mode toggle

### Ventures REST API (`/api/ventures/`)
- Venture, StartupCost, FounderSalary CRUD

### Response format
`{success: true/false, error: str, ...}`

## Indian Financial Context

- Currency: ₹ — format as Lakhs (₹10L) and Crores (₹1.5Cr)
- Default inflation: 6% expenses, 4% pension
- Default asset returns: Liquid 6%, Semi-liquid 8%, Growth 12%, Property 5%
- Timezone: `Asia/Kolkata`
- QUICK tier default asset splits: 60/40 liquid/semi-liquid, 70/30 growth/property
- Budget smart adjustments: child age 4-21 → +10% Needs, dependent adult → +5% Needs

## UI/Design Rules

- Mobile-first: 375x667 portrait (iPhone SE), 9:16 aspect ratio
- Touch targets >= 44px (iOS HIG)
- Color palette: deep blue `#1a56db`, professional aesthetic (no playful colors)
- Font: Inter, base 16px (prevents iOS zoom on focus)
- Alpine.js for reactivity (`x-data`, `x-model`, `x-if`)

## Code Conventions

- snake_case for all field names
- Every model has a `user` ForeignKey (user-centric design)
- Calculator classes: inherit `BaseCalculator`, implement `calculate()` and `get_required_fields()`
- Validation returns specific missing field names
- Field references use dot notation: `scenario.current_age`, `family.monthly_expenses`

## Running the Project

```bash
# Backend
cd sup_backend && python3 manage.py runserver  # localhost:8000/scenarios/

# Ionic frontend (separate)
cd sup_frontend && npm run dev  # localhost:5173

# MCP server
cd sup_mcp && python3 main.py  # stdio for Claude Desktop
```

## Testing

- Manual testing guide: `TESTING_GUIDE.md`
- Ionic frontend: Vitest (unit), Cypress (e2e)
- Backend: Django test files exist but are currently empty

## Not Yet Implemented

- R2I, HALF_FIRE, TERMINATION scenario calculators
- ADVANCED tier (Monte Carlo, tax optimization)
- User accounts / save-load scenarios
- PDF export, email results
- Automated backend tests
