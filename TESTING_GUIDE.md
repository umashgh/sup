# Mobile Testing & Verification Guide

## Overview
This guide documents the complete mobile-first financial planning flow and verification steps after the recent error handling improvements.

---

## What Was Fixed

### Problem
Users were seeing a generic "Calculation failed" error without knowing what went wrong.

### Root Cause
The frontend JavaScript was not parsing the actual backend validation error:

```javascript
// OLD CODE (line 244):
if (!response.ok) throw new Error('Calculation failed');
```

### Solution
Modified `/templates/questions_flow.html` to parse and display specific backend errors:

```javascript
// NEW CODE (lines 248-261):
if (!response.ok) {
  // Parse actual error from backend
  const errorData = await response.json();
  console.error('❌ Calculation error:', errorData);

  // Show specific error message
  let errorMsg = 'Calculation failed';
  if (errorData.error) {
    errorMsg = errorData.error;
  } else if (errorData.missing_fields) {
    errorMsg = `Missing required fields: ${errorData.missing_fields.join(', ')}`;
  }

  throw new Error(errorMsg);
}
```

### Additional Improvements
- Added debug logging: `console.log('📤 Sending calculation data:', data)`
- Shows specific missing field names to help troubleshooting
- Preserves all user-entered answers in `this.answers` object

---

## Complete User Flow Testing

### Prerequisites
1. Django development server running on `http://localhost:8000`
2. Mobile device or browser dev tools in mobile mode (375×667 iPhone SE recommended)
3. Browser console open (F12 → Console tab) for debugging

### Start Server
```bash
cd /Users/umashankar/apps/sup/sup_backend
python3 manage.py runserver
```

---

## Test Scenario 1: Retirement Planning (QUICK Tier)

### Step 1: Scenario Selection
1. Navigate to `http://localhost:8000/scenarios/`
2. Verify you see:
   - **Page title**: "Financial Independence Calculator"
   - **Guest notice**: "No account required. Start immediately with a guest session."
   - **5 scenario cards** with SVG icons (not emojis)
3. Tap **"Retirement Planning"** card
4. **Expected behavior**:
   - Guest session auto-created (check Network tab: POST to `/start/`)
   - Redirected to `/flow/questions/`

### Step 2: Answer Questions (QUICK Tier)
You should see these questions in sequence:

1. **Current Age** (slider: 18-75 years)
   - Drag slider to: **35 years**

2. **Retirement Age** (slider: 30-80 years)
   - Drag slider to: **60 years**

3. **Life Expectancy** (slider: 60-100 years)
   - Drag slider to: **85 years**

4. **Monthly Expenses** (amount slider with presets)
   - Tap preset: **₹50,000** or drag slider

5. **Liquid Savings** (amount slider)
   - Tap preset: **₹10L** (₹1,000,000)

**Navigation**:
- Tap **"Continue"** after each question
- Progress bar at top shows completion percentage
- **"← Back"** button appears after first question

### Step 3: Calculate Results
1. On the last question, tap **"Calculate"** button
2. **Open browser console** (F12) and check for:
   - `📤 Sending calculation data:` with object showing all your answers
   - If successful: redirect to `/flow/results/`
   - If failed: `❌ Calculation error:` with specific error message

3. **Expected console output** (success):
```javascript
📤 Sending calculation data: {
  scenario: {
    current_age: 35,
    retirement_age: 60,
    life_expectancy: 85
  },
  family: {
    monthly_expenses: 50000
  },
  assets: {
    liquid: 1000000
  },
  income: {},
  profile: {}
}
✅ Calculation results: { ... }
```

4. **Expected error output** (if validation fails):
```javascript
❌ Calculation error: {
  missing_fields: ["scenario.current_age", "family.monthly_expenses"]
}
```

### Step 4: View Results
If calculation succeeds, you should see:
- **Years to Retirement**: 25 years
- **Retirement Duration**: 25 years
- **Required Corpus**: ₹1.5Cr (25× annual expenses)
- **Corpus Gap**: ₹50L
- **Monthly Savings Needed**: ₹16,667

---

## Test Scenario 2: Startup Founder (QUICK Tier)

### Step 1: Select Founder Scenario
1. Navigate back to `http://localhost:8000/scenarios/`
2. Tap **"Startup Founder"** card

### Step 2: Answer Questions
Expected questions:

1. **Monthly Expenses** (amount slider)
   - Set to: **₹75,000**

2. **Liquid Savings** (amount slider)
   - Set to: **₹25L** (₹2,500,000)

3. **Semi-Liquid Assets** (bonds, debt MFs)
   - Set to: **₹10L**

4. **Growth Assets** (equity, stocks)
   - Set to: **₹5L**

5. **Property Value** (if any)
   - Set to: **₹0** (or skip if not asked)

6. **Monthly Passive Income** (rental, dividends)
   - Set to: **₹10,000**

7. **Emergency Fund Months**
   - Set to: **12 months**

8. **Is venture bootstrapped?** (toggle)
   - Toggle ON

9. **Bootstrap Capital Needed**
   - Set to: **₹10L**

### Step 3: Calculate
1. Tap **"Calculate"**
2. Check console for data being sent
3. Expected results:
   - **Free-up Year**: Year when passive income >= expenses
   - **Emergency Lock**: ₹9L (12 months × ₹75K needs portion)
   - **Bootstrap Capital**: ₹10L
   - **Available Liquid**: ₹6L (₹25L - ₹9L - ₹10L)

---

## Test Scenario 3: Standard Tier (20-Year Projection)

### Prerequisites
Complete QUICK tier first for any scenario

### Step 1: Advance to STANDARD Tier
1. On results page, tap **"Unlock Deeper Insights"** button
2. Expected: More detailed questions appear

### Step 2: Additional Questions (STANDARD Tier)
For Retirement STANDARD, expect:

1. **Pension Monthly Amount** (if applicable)
   - Set to: **₹30,000**

2. **Pension Start Age**
   - Set to: **65 years**

3. **Gratuity Lumpsum** (at retirement)
   - Set to: **₹15L**

### Step 3: View 20-Year Projection
Results should include:
- **Chart**: Corpus vs Expenses vs Income over 20 years
- **Sustainability**: "✅ Sustainable" or "⚠️ Depletion in Year X"
- **Final Corpus**: Projected corpus at Year 20
- **Pension Income**: Shows when pension kicks in

---

## Troubleshooting Common Errors

### Error: "Missing required fields: scenario.current_age"
**Cause**: Question was skipped or not answered
**Fix**: Go back and ensure all questions are answered

### Error: "Calculation failed"
**Cause**: Generic backend error (shouldn't happen with new code)
**Check**: Browser console for actual error message

### Error: "Failed to create session"
**Cause**: CSRF token issue or network problem
**Fix**:
1. Hard refresh page (Cmd+Shift+R / Ctrl+Shift+F5)
2. Clear browser cookies for localhost
3. Check Django server is running

### Error: 403 Forbidden
**Cause**: CSRF verification failed
**Fix**: Ensure templates have `{% csrf_token %}` in forms

### Questions not loading
**Cause**: API endpoint /api/scenarios/questions/ failing
**Check**:
1. Network tab: see response status
2. Django server logs: check for Python errors
3. Database: ensure ScenarioProfile was created

---

## Mobile-Specific UI Testing

### Touch Interactions
- [ ] Sliders: Drag smoothly without jank
- [ ] Card taps: Register on first touch
- [ ] Back button: Works without double-tap
- [ ] Progress bar: Updates smoothly

### Visual Design
- [ ] Text readable without zooming (min 16px)
- [ ] Touch targets ≥44px (iOS recommendation)
- [ ] No horizontal scrolling
- [ ] Proper spacing between interactive elements

### Portrait Mode (9:16 ratio)
- [ ] Content fits without scrolling excessively
- [ ] Keyboard doesn't obscure inputs
- [ ] Navigation buttons always visible

### Performance
- [ ] Page loads < 2 seconds
- [ ] Slider dragging feels responsive (60fps)
- [ ] Transitions smooth (fade-in, card selection)
- [ ] No layout shift after JavaScript loads

---

## Browser Console Debugging

### What to Check

1. **Network Tab**:
   - POST `/start/` → 200 OK (guest login)
   - POST `/api/scenarios/select/` → 200 OK (scenario selection)
   - POST `/api/scenarios/questions/` → 200 OK (load questions)
   - POST `/api/scenarios/calculate/` → 200 OK (calculation)

2. **Console Tab**:
   - `📤 Sending calculation data:` → verify all fields present
   - `✅ Calculation results:` → successful calculation
   - `❌ Calculation error:` → validation failed with details

3. **Application Tab** (Storage):
   - sessionStorage: `scenario`, `current_tier`, `calculation_results`
   - cookies: `csrftoken`, `sessionid`

---

## Database Verification

### Check Guest User Created
```bash
python3 manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.filter(username__startswith='guest_').count()
# Should be > 0 after testing
```

### Check Scenario Profile
```bash
>>> from core.models import ScenarioProfile
>>> ScenarioProfile.objects.all()
# Should show scenario_type, tier, field values
```

### Check Family Profile
```bash
>>> from finance.models import FamilyProfile
>>> FamilyProfile.objects.all()
# Should have monthly_expenses and other saved values
```

---

## Known Limitations

### Current Implementation
- ✅ QUICK tier: Founder, Retirement
- ✅ STANDARD tier: Founder, Retirement
- ❌ R2I, Half FIRE, Termination scenarios: **Not yet implemented**
- ❌ ADVANCED tier: **Not yet implemented**

### Calculators
- QuickFounderCalculator: ✅ Working
- QuickRetirementCalculator: ✅ Working
- StandardFounderCalculator: ✅ Working (20-year projection)
- StandardRetirementCalculator: ✅ Working (20-year projection)

### Questions
- Dynamic question system: ✅ Working
- Conditional logic: ✅ Working (filters by scenario, tier, answers)
- Input types: ✅ card_select, slider, amount_slider, toggle

---

## Next Steps for Full Production

1. **Add Remaining Scenarios**:
   - R2I calculator (Quick + Standard)
   - Half FIRE calculator (Quick + Standard)
   - Termination calculator (Quick + Standard)

2. **Add ADVANCED Tier**:
   - Monte Carlo simulations
   - Tax optimization
   - Estate planning

3. **Testing**:
   - Unit tests for calculators
   - Integration tests for API endpoints
   - E2E tests for complete user flow

4. **Deployment**:
   - Set DEBUG=False in production
   - Configure allowed hosts
   - Set up static file serving (Whitenoise or CDN)
   - Add SSL certificate

5. **Analytics**:
   - Track scenario selections
   - Track calculation completions
   - Track tier advancement

---

## File Reference

### Modified Files (Error Handling Fix)
- `/templates/questions_flow.html` (lines 214-275)
  - Added error parsing logic
  - Added debug console logging
  - Improved error messages

### Core Files
- `/core/models.py` - ScenarioProfile model
- `/core/questions.py` - Question configuration
- `/core/views.py` - API endpoints
- `/core/calculators/` - Calculator implementations
- `/templates/scenario_selector.html` - Scenario selection UI
- `/templates/questions_flow.html` - Dynamic form UI
- `/templates/results.html` - Results display
- `/templates/base_mobile.html` - Mobile CSS framework

---

## Support

If you encounter issues not covered here:
1. Check Django server logs: `/api/scenarios/calculate/` endpoint
2. Check browser console: Network and Console tabs
3. Verify database: ScenarioProfile, FamilyProfile created
4. Hard refresh: Clear cache and cookies for localhost

---

**Last Updated**: 2026-02-14
**Version**: v1.1 (with error handling improvements)
