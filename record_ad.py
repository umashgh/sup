#!/usr/bin/env python3
"""
record_ad.py — Records the salaryfree ad video walkthrough via Playwright.

Scenario: Layoff Buffer (TERMINATION), joint family 47/49, ₹50L severance,
          ₹25L liquid + ₹50L security assets → ~4.4 yr comfort runway.

Prerequisites:
    pip install playwright
    playwright install chromium
    cd sup_backend && python manage.py runserver   # separate terminal

Output:
    ad_clips/raw/  — raw .webm recording

Post-process to 1080×1560 MP4 (9:16 crop of the 2/3-height viewport):
    mkdir -p ad_clips/final
    ffmpeg -i ad_clips/raw/*.webm \\
        -vf "scale=1080:1560:flags=lanczos,fps=30" \\
        -c:v libx264 -crf 16 -preset slow -movflags +faststart \\
        ad_clips/final/salaryfree_ad.mp4
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page

# ─────────────────────────────────────────────────────────────────────────────
# Config
# (c) Only 2/3 of a phone screen is visible in a social feed — use 560px height
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL   = "http://localhost:8000"
VIEWPORT   = {"width": 390, "height": 560}
OUTPUT_DIR = Path("ad_clips/raw")

# ─────────────────────────────────────────────────────────────────────────────
# Visual-effects library — injected into every page before scripts run
# ─────────────────────────────────────────────────────────────────────────────
FX_INIT_SCRIPT = """
window.__sf = {
  _spotlit: null,

  spotlight(el) {
    if (!el) return;
    this.clearSpotlight();
    el._sfSaved = { position: el.style.position, zIndex: el.style.zIndex,
                    boxShadow: el.style.boxShadow, transition: el.style.transition };
    el.style.transition  = 'box-shadow 0.35s ease';
    el.style.position    = 'relative';
    el.style.zIndex      = '9999';
    el.style.boxShadow   = '0 0 0 9999px rgba(0,0,0,0.55), 0 0 0 3px rgba(255,255,255,0.25)';
    this._spotlit = el;
  },
  clearSpotlight() {
    const el = this._spotlit;
    if (el && el._sfSaved) {
      el.style.position   = el._sfSaved.position;
      el.style.zIndex     = el._sfSaved.zIndex;
      el.style.boxShadow  = el._sfSaved.boxShadow;
      el.style.transition = el._sfSaved.transition;
      delete el._sfSaved;
    }
    this._spotlit = null;
  },

  underline(el) {
    if (!el) return;
    document.querySelectorAll('.__sf_ul').forEach(e => e.remove());
    el.style.position = 'relative';
    const bar = document.createElement('span');
    bar.className = '__sf_ul';
    bar.style.cssText = [
      'position:absolute','bottom:-4px','left:0','height:3px','width:0',
      'background:linear-gradient(90deg,#e05a3a,#f0a830)',
      'border-radius:2px','transition:width 0.65s ease',
      'pointer-events:none','z-index:9999',
    ].join(';');
    el.appendChild(bar);
    requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = '100%'; }));
  },
  clearUnderlines() { document.querySelectorAll('.__sf_ul').forEach(e => e.remove()); },

  zoom(el, scale = 1.08) {
    if (!el) return;
    el._sfZ = { transform: el.style.transform, zIndex: el.style.zIndex };
    el.style.transition = 'transform 0.4s cubic-bezier(0.34,1.56,0.64,1)';
    el.style.transform  = `scale(${scale})`;
    el.style.zIndex     = '100';
    el.style.position   = 'relative';
  },
  unzoom(el) {
    if (!el || !el._sfZ) return;
    el.style.transition = 'transform 0.35s ease';
    el.style.transform  = el._sfZ.transform || '';
    el.style.zIndex     = el._sfZ.zIndex     || '';
  },

  ring(el, color = '#1a56db') {
    if (!el) return;
    el._sfR = el.style.boxShadow;
    el.style.transition = 'box-shadow 0.3s ease';
    el.style.boxShadow  = `0 0 0 3px ${color}, 0 0 20px ${color}55`;
  },
  clearRing(el) { if (el) el.style.boxShadow = el._sfR || ''; },

  showOverlay(opts = {}) {
    this.clearOverlay();
    const { text = '', bg = 'rgba(26,22,18,0.92)', color = 'white',
            fontSize = '1.5rem', fadeIn = true } = opts;
    const ov = document.createElement('div');
    ov.id = '__sf_ov';
    ov.style.cssText = [
      'position:fixed','top:0','left:0','right:0','bottom:0',
      `background:${bg}`, 'display:flex','align-items:center','justify-content:center',
      'z-index:999999', `opacity:${fadeIn ? '0' : '1'}`,
      'transition:opacity 0.7s ease',
      `font-family:"DM Serif Display",Georgia,serif`,
      `font-size:${fontSize}`, `color:${color}`,
      'text-align:center', 'padding:32px', 'line-height:1.55',
    ].join(';');
    ov.innerHTML = text;
    document.body.appendChild(ov);
    if (fadeIn) requestAnimationFrame(() => requestAnimationFrame(() => { ov.style.opacity = '1'; }));
    return ov;
  },
  fadeOutOverlay() {
    const ov = document.getElementById('__sf_ov');
    if (ov) { ov.style.opacity = '0'; setTimeout(() => ov.remove(), 750); }
  },
  clearOverlay() { const ov = document.getElementById('__sf_ov'); if (ov) ov.remove(); },

  /* Alpine-compatible slider setter */
  setSlider(slider, value) {
    const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    s.call(slider, value);
    slider.dispatchEvent(new Event('input',  { bubbles: true }));
    slider.dispatchEvent(new Event('change', { bubbles: true }));
  },

  /* Alpine-compatible number input setter */
  setNumber(input, value) {
    const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    s.call(input, value);
    input.dispatchEvent(new Event('input',  { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  },

  clearAll() { this.clearSpotlight(); this.clearUnderlines(); this.clearOverlay(); },
};
"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
async def sleep(s: float):
    await asyncio.sleep(s)

async def smooth_scroll(page: Page, to_y: int, ms: int = 700):
    await page.evaluate(f"""
        (function() {{
            const start = window.scrollY, end = {to_y}, dur = {ms}, t0 = performance.now();
            function step(t) {{
                const p = Math.min((t - t0) / dur, 1);
                const e = p < 0.5 ? 2*p*p : -1+(4-2*p)*p;
                window.scrollTo(0, start + (end - start) * e);
                if (p < 1) requestAnimationFrame(step);
            }}
            requestAnimationFrame(step);
        }})();
    """)
    await sleep(ms / 1000 + 0.1)

async def click_continue(page: Page, wait_after: float = 0.6):
    """Click Continue → / Get my number → at the bottom of the questions flow."""
    btn = page.locator("button.btn-primary").last
    await btn.scroll_into_view_if_needed()
    await sleep(0.25)
    await btn.click()
    await sleep(wait_after)

async def click_preset(page: Page, label: str, ring_color: str = '#2d7a5f'):
    """Click a preset button by its visible text (e.g. '₹25L', '₹50L')."""
    await page.evaluate(f"""
        const btns = Array.from(document.querySelectorAll('.preset-btn'));
        const btn  = btns.find(b => b.innerText.includes('{label}'));
        if (btn) {{
            window.__sf.ring(btn, '{ring_color}');
            setTimeout(() => {{ window.__sf.clearRing(btn); btn.click(); }}, 350);
        }}
    """)
    await sleep(0.8)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 1 — Opening home page
# ─────────────────────────────────────────────────────────────────────────────
async def scene_home(page: Page):
    print("  ▶ Scene 1: Home page")
    await page.goto(f"{BASE_URL}/")
    await page.wait_for_load_state("networkidle")
    await sleep(1.2)

    # Spotlight "Find out →" and click it
    await page.evaluate("""
        const btn = document.querySelector('a.btn-primary[href="#stories"]');
        if (btn) window.__sf.spotlight(btn);
    """)
    await sleep(1.8)
    await page.evaluate("""
        const btn = document.querySelector('a.btn-primary[href="#stories"]');
        if (btn) { window.__sf.clearSpotlight(); btn.click(); }
    """)
    await sleep(1.0)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 2 — Scenario selector: scroll stories, pick Layoff Buffer
# ─────────────────────────────────────────────────────────────────────────────
async def scene_scenario_selector(page: Page):
    print("  ▶ Scene 2: Scenario selector")
    await smooth_scroll(page, 1200, 1100)
    await sleep(0.5)
    await smooth_scroll(page, 800, 800)
    await sleep(0.3)

    await page.evaluate("""
        const card = Array.from(document.querySelectorAll('.story'))
                         .find(c => c.innerText.includes('Layoff Buffer'));
        if (card) { card.scrollIntoView({ behavior:'smooth', block:'center' }); window.__sf.spotlight(card); }
    """)
    await sleep(1.8)
    await page.evaluate("""
        const card = Array.from(document.querySelectorAll('.story'))
                         .find(c => c.innerText.includes('Layoff Buffer'));
        if (card) { window.__sf.clearSpotlight(); card.click(); }
    """)
    await page.wait_for_url("**/questions/**", timeout=12000)
    await page.wait_for_load_state("networkidle")
    await sleep(1.0)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 3 — Quick tier questions (show only the meaningful screens)
# ─────────────────────────────────────────────────────────────────────────────
async def scene_tier1_questions(page: Page):
    print("  ▶ Scene 3: Tier 1 questions")

    # ── Q: family_type → joint ──
    await page.wait_for_selector(".choice", timeout=6000)
    await sleep(0.5)
    await page.evaluate("""
        const c = Array.from(document.querySelectorAll('.choice'))
                       .find(x => x.innerText.includes('kids + parents'));
        if (c) { window.__sf.ring(c, '#1a56db'); setTimeout(() => { window.__sf.clearRing(c); c.click(); }, 400); }
    """)
    await sleep(0.8)
    await click_continue(page)

    # ── Q: ages → 47 / 49 (show both sliders briefly) ──
    await sleep(0.4)
    await page.evaluate("""
        const sliders = document.querySelectorAll('input[type=range]');
        if (sliders[0]) window.__sf.setSlider(sliders[0], 47);
        if (sliders[1]) window.__sf.setSlider(sliders[1], 49);
    """)
    await sleep(0.9)
    await click_continue(page)

    # ── kids count → 1 (rapid) ──
    await sleep(0.3)
    await page.evaluate("""
        const s = document.querySelector('input[type=range]');
        if (s) window.__sf.setSlider(s, 1);
    """)
    await sleep(0.4)
    await click_continue(page)

    # ── kids age range — default ──
    await sleep(0.3)
    await click_continue(page)

    # ── dependent adults → 1 (rapid) ──
    await sleep(0.3)
    await page.evaluate("""
        const s = document.querySelector('input[type=range]');
        if (s) window.__sf.setSlider(s, 1);
    """)
    await sleep(0.4)
    await click_continue(page)

    # ── household attributes — defaults ──
    await sleep(0.3)
    await click_continue(page)

    # ── SHOW: severance → ₹50L preset ──
    await sleep(0.5)
    await click_preset(page, '50L')
    await click_continue(page)

    # ── SHOW: expense style → Comfortable ──
    await sleep(0.5)
    await page.evaluate("""
        const c = Array.from(document.querySelectorAll('.choice'))
                       .find(x => x.innerText.includes('Comfortable'));
        if (c) { window.__sf.ring(c, '#2d7a5f'); setTimeout(() => { window.__sf.clearRing(c); c.click(); }, 400); }
    """)
    await sleep(0.9)
    await click_continue(page)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 4 — Expense estimate: show total, fine-tune, tweak a number
# ─────────────────────────────────────────────────────────────────────────────
async def scene_expense_estimate(page: Page):
    print("  ▶ Scene 4: Expense estimate")

    # Wait for expense total to render
    await page.wait_for_function(
        "() => { const sp = document.querySelector('.slider-value-display span'); "
        "        return sp && sp.innerText.includes('₹'); }",
        timeout=8000
    )
    await sleep(1.2)

    # Spotlight the total
    await page.evaluate("""
        const el = document.querySelector('.slider-value-display');
        if (el) window.__sf.spotlight(el);
    """)
    await sleep(1.8)
    await page.evaluate("window.__sf.clearSpotlight();")

    # Open fine-tune
    await page.evaluate("""
        const d = Array.from(document.querySelectorAll('div'))
                       .find(d => d.style.cursor === 'pointer' && d.innerText.includes('Fine-tune'));
        if (d) d.click();
    """)
    await sleep(0.8)

    # Expand Needs section
    await page.evaluate("""
        const d = Array.from(document.querySelectorAll('div'))
                       .find(d => d.style.cursor === 'pointer' &&
                                  d.innerText.includes('Needs') &&
                                  !d.innerText.includes('Fine-tune'));
        if (d) d.click();
    """)
    await sleep(0.7)

    # Scroll down to see items
    await smooth_scroll(page, 350, 600)
    await sleep(0.5)
    await smooth_scroll(page, 0, 600)
    await sleep(0.4)

    # Drag first expense slider a little lower
    await page.evaluate("""
        const sliders = document.querySelectorAll('.expense-slider');
        if (sliders[0]) {
            const cur = parseInt(sliders[0].value);
            window.__sf.ring(sliders[0].closest('div[style]'), '#b04030');
            window.__sf.setSlider(sliders[0], Math.max(0, cur - 3000));
        }
    """)
    await sleep(0.7)

    # Spotlight updated total
    await page.evaluate("""
        window.__sf.clearAll();
        const el = document.querySelector('.slider-value-display');
        if (el) window.__sf.spotlight(el);
    """)
    await sleep(1.2)
    await page.evaluate("window.__sf.clearAll();")
    await sleep(0.3)
    await click_continue(page)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 5 — Assets: set real values so results look great
# (a) ₹25L living + ₹50L security → ~4.4 yr comfort runway
# ─────────────────────────────────────────────────────────────────────────────
async def scene_assets(page: Page):
    print("  ▶ Scene 5: Assets (₹25L living, ₹50L security)")

    # assets_for_living → ₹25L preset
    await sleep(0.4)
    await click_preset(page, '25L')
    await click_continue(page)

    # assets_for_security → ₹50L preset (5000000)
    await sleep(0.4)
    await click_preset(page, '50L')
    await click_continue(page)

    # monthly_passive_income → 0 default
    await sleep(0.3)
    await click_continue(page)

    # emergency_fund_months → 6 default
    await sleep(0.3)
    await click_continue(page)

    # one_time_expenses → skip
    await sleep(0.4)
    await click_continue(page)

    # future_assets → "Get my number →"
    await sleep(0.5)
    btn = page.locator("button.btn-primary").last
    await btn.scroll_into_view_if_needed()
    await sleep(0.2)
    await btn.click()

    await page.wait_for_url("**/results/**", timeout=15000)
    await page.wait_for_load_state("networkidle")
    await sleep(1.5)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 6 — Tier 1 Results: zoom each result card
# ─────────────────────────────────────────────────────────────────────────────
async def scene_tier1_results(page: Page):
    print("  ▶ Scene 6: Tier 1 results – zoom cards")

    await page.wait_for_selector(".result-card", timeout=10000)
    await sleep(0.8)

    # Scroll past the dark reveal into cards
    await smooth_scroll(page, 480, 700)
    await sleep(0.5)

    cards = await page.query_selector_all(".result-card")
    for i in range(min(4, len(cards))):
        await page.evaluate(f"""
            const cards = document.querySelectorAll('.result-card');
            if (cards[{i}]) {{
                cards[{i}].scrollIntoView({{ behavior:'smooth', block:'center' }});
                window.__sf.zoom(cards[{i}], 1.07);
            }}
        """)
        await sleep(1.1)
        await page.evaluate(f"""
            const cards = document.querySelectorAll('.result-card');
            if (cards[{i}]) window.__sf.unzoom(cards[{i}]);
        """)
        await sleep(0.4)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 7 — Blind spots highlight → Go deeper
# ─────────────────────────────────────────────────────────────────────────────
async def scene_blind_spots(page: Page):
    print("  ▶ Scene 7: Blind spots + Go deeper")

    # Scroll to blind spots section
    await page.evaluate("""
        const h = Array.from(document.querySelectorAll('h2'))
                       .find(x => x.innerText.includes('blind spots'));
        if (h) h.scrollIntoView({ behavior:'smooth', block:'start' });
    """)
    await sleep(0.9)

    # Underline heading
    await page.evaluate("""
        const h = Array.from(document.querySelectorAll('h2'))
                       .find(x => x.innerText.includes('blind spots'));
        if (h) window.__sf.underline(h);
    """)
    await sleep(1.6)

    # Ring the paragraph below
    await page.evaluate("""
        const h = Array.from(document.querySelectorAll('h2'))
                       .find(x => x.innerText.includes('blind spots'));
        if (h && h.nextElementSibling) window.__sf.ring(h.nextElementSibling, '#e05a3a');
        window.__sf.clearUnderlines();
    """)
    await sleep(1.2)
    await page.evaluate("window.__sf.clearAll();")
    await sleep(0.4)

    # Scroll to + click "Go deeper" button
    await page.evaluate("""
        const btn = Array.from(document.querySelectorAll('.btn-primary'))
                         .find(b => b.innerText.includes('deeper'));
        if (btn) btn.scrollIntoView({ behavior:'smooth', block:'center' });
    """)
    await sleep(0.7)
    await page.evaluate("""
        const btn = Array.from(document.querySelectorAll('.btn-primary'))
                         .find(b => b.innerText.includes('deeper'));
        if (btn) { window.__sf.ring(btn, '#1a56db'); setTimeout(() => { window.__sf.clearRing(btn); btn.click(); }, 450); }
    """)
    await page.wait_for_url("**/questions/**", timeout=12000)
    await page.wait_for_load_state("networkidle")
    await sleep(1.2)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 8 — Tier 2 questions (b) — take it all the way through
# ─────────────────────────────────────────────────────────────────────────────
async def scene_tier2_questions(page: Page):
    print("  ▶ Scene 8: Tier 2 questions")

    # ── living_assets_split → 80% liquid ──
    await page.wait_for_selector("input[type=range]", timeout=10000)
    await sleep(0.8)
    await page.evaluate("""
        const slider = document.querySelector('input[type=range]');
        if (slider) {
            let v = 60;
            const iv = setInterval(() => {
                v = Math.min(v + 2, 80);
                window.__sf.setSlider(slider, v);
                if (v >= 80) clearInterval(iv);
            }, 55);
        }
    """)
    await sleep(1.4)
    await click_continue(page)

    # ── security_assets_split → default 70/30, continue ──
    await page.wait_for_selector("input[type=range]", timeout=6000)
    await sleep(0.5)
    await click_continue(page)

    # ── asset_growth_rates: cash 4%, property appreciation 6% ──
    await page.wait_for_selector("label input[type=number]", timeout=6000)
    await sleep(0.5)
    await page.evaluate("""
        const labels = Array.from(document.querySelectorAll('label'));
        const cashL = labels.find(l => l.innerText.includes('Cash') || l.innerText.includes('liquid return'));
        const propL = labels.find(l => l.innerText.includes('Property appreciation'));
        if (cashL) {
            const inp = cashL.querySelector('input[type=number]');
            if (inp) { window.__sf.ring(cashL, '#1a56db'); window.__sf.setNumber(inp, 4); }
        }
        if (propL) {
            setTimeout(() => {
                if (cashL) window.__sf.clearRing(cashL);
                const inp = propL.querySelector('input[type=number]');
                if (inp) { window.__sf.ring(propL, '#1a56db'); window.__sf.setNumber(inp, 6); }
            }, 700);
        }
    """)
    await sleep(1.6)
    await page.evaluate("window.__sf.clearAll();")
    await click_continue(page)

    # ── inflation_rates: lifestyle inflation 8% ──
    await page.wait_for_selector("label input[type=number]", timeout=6000)
    await sleep(0.5)
    await page.evaluate("""
        const labels = Array.from(document.querySelectorAll('label'));
        const l = labels.find(x => x.innerText.includes('Lifestyle') || x.innerText.includes('wants'));
        if (l) {
            const inp = l.querySelector('input[type=number]');
            if (inp) { window.__sf.ring(l, '#e05a3a'); window.__sf.setNumber(inp, 8); }
        }
    """)
    await sleep(1.2)
    await page.evaluate("window.__sf.clearAll();")
    await click_continue(page)

    # ── termination_restart_timeline: wiggle → settle at 4 months ──
    await page.wait_for_selector("input[type=range]", timeout=6000)
    await sleep(0.5)
    await page.evaluate("""
        const slider = document.querySelector('input[type=range]');
        if (slider) {
            const moves = [6, 3, 1, 4, 7, 9, 6, 4];
            let idx = 0;
            const iv = setInterval(() => {
                window.__sf.setSlider(slider, moves[idx++]);
                if (idx >= moves.length) { clearInterval(iv); setTimeout(() => window.__sf.setSlider(slider, 4), 250); }
            }, 230);
        }
    """)
    await sleep(2.5)
    await click_continue(page)

    # ── termination_restart_income: ₹2L preset ──
    await page.wait_for_selector(".preset-btn", timeout=6000)
    await sleep(0.4)
    await click_preset(page, '2L')

    # "Get my number →"
    btn = page.locator("button.btn-primary").last
    await btn.scroll_into_view_if_needed()
    await sleep(0.3)
    await btn.click()
    await page.wait_for_url("**/results/**", timeout=15000)
    await page.wait_for_load_state("networkidle")
    await sleep(1.5)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 9 — Tier 2 Results: scroll cards + zoom 20-yr chart
# ─────────────────────────────────────────────────────────────────────────────
async def scene_tier2_results(page: Page):
    print("  ▶ Scene 9: Tier 2 results – scroll + zoom chart")

    await page.wait_for_selector(".result-card", timeout=10000)
    await sleep(1.0)

    # Scroll through result cards
    await smooth_scroll(page, 450, 800)
    await sleep(0.4)
    await smooth_scroll(page, 850, 700)
    await sleep(0.4)
    await smooth_scroll(page, 1200, 700)
    await sleep(0.4)
    await smooth_scroll(page, 850, 700)
    await sleep(0.3)

    # Scroll to + zoom the 20-year projection chart
    await page.evaluate("""
        const chart = document.querySelector('.chart-container');
        if (chart) chart.scrollIntoView({ behavior:'smooth', block:'center' });
    """)
    await sleep(0.7)
    await page.evaluate("""
        const chart = document.querySelector('.chart-container');
        if (chart) window.__sf.zoom(chart, 1.06);
    """)
    await sleep(1.5)
    await page.evaluate("""
        const chart = document.querySelector('.chart-container');
        if (chart) window.__sf.unzoom(chart);
    """)
    await sleep(0.6)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 10 — Rates panel: change property → 3%, recalculate, highlight changes
# ─────────────────────────────────────────────────────────────────────────────
async def scene_rates_adjust(page: Page):
    print("  ▶ Scene 10: Rates adjustment")

    # Scroll to "Rates & assumptions"
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const s = sections.find(x => x.innerText.includes('Rates') && x.innerText.includes('assumptions'));
        if (s) s.scrollIntoView({ behavior:'smooth', block:'start' });
    """)
    await sleep(0.9)

    # Change property appreciation to 3%
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const s = sections.find(x => x.innerText.includes('Rates') && x.innerText.includes('assumptions'));
        if (s) {
            const propL = Array.from(s.querySelectorAll('label'))
                               .find(l => l.innerText.includes('Property appreciation'));
            if (propL) {
                const inp = propL.querySelector('input[type=number]');
                if (inp) {
                    window.__sf.ring(propL, '#e05a3a');
                    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    setter.call(inp, 3);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        }
    """)
    await sleep(1.1)
    await page.evaluate("window.__sf.clearAll();")

    # Click Recalculate
    await page.evaluate("""
        const btn = Array.from(document.querySelectorAll('button'))
                         .find(b => b.innerText.includes('Recalculate'));
        if (btn) { window.__sf.ring(btn, '#1a56db'); setTimeout(() => { window.__sf.clearRing(btn); btn.click(); }, 400); }
    """)
    await sleep(2.5)

    # Scroll up to results + highlight changed cards
    await smooth_scroll(page, 450, 900)
    await sleep(0.5)
    await page.evaluate("""
        document.querySelectorAll('.result-card').forEach(c => {
            if (c.innerText.includes('Inflation-adjusted') || c.innerText.includes('20-year') ||
                c.innerText.includes('Portfolio') || c.innerText.includes('Depletion')) {
                window.__sf.ring(c, '#1a56db');
            }
        });
    """)
    await sleep(1.8)
    await page.evaluate("window.__sf.clearAll();")

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 11 — Advanced possibilities: Monte Carlo + AI Advisor
# ─────────────────────────────────────────────────────────────────────────────
async def scene_advanced_options(page: Page):
    print("  ▶ Scene 11: Advanced options")

    # Scroll to Monte Carlo and spotlight it
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const mc = sections.find(s => s.innerText.includes('Monte Carlo'));
        if (mc) mc.scrollIntoView({ behavior:'smooth', block:'center' });
    """)
    await sleep(0.7)
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const mc = sections.find(s => s.innerText.includes('Monte Carlo'));
        if (mc) {
            const card = mc.querySelector('div[style*="gradient"]') || mc.firstElementChild;
            if (card) window.__sf.spotlight(card);
        }
    """)
    await sleep(1.4)
    await page.evaluate("window.__sf.clearSpotlight();")
    await sleep(0.4)

    # Scroll to AI Advisor and spotlight it
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const ai = sections.find(s => s.innerText.includes('AI Advisor') || s.innerText.includes('Asha'));
        if (ai) ai.scrollIntoView({ behavior:'smooth', block:'center' });
    """)
    await sleep(0.7)
    await page.evaluate("""
        const sections = Array.from(document.querySelectorAll('section'));
        const ai = sections.find(s => s.innerText.includes('AI Advisor') || s.innerText.includes('Asha'));
        if (ai) {
            const card = ai.querySelector('div[style*="gradient"]') || ai.firstElementChild;
            if (card) window.__sf.spotlight(card);
        }
    """)
    await sleep(1.4)
    await page.evaluate("window.__sf.clearAll();")
    await sleep(0.4)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 12 — Logo zoom finale
# ─────────────────────────────────────────────────────────────────────────────
async def scene_finale(page: Page):
    print("  ▶ Scene 12: Finale")

    await page.goto(f"{BASE_URL}/")
    await page.wait_for_load_state("networkidle")
    await smooth_scroll(page, 0, 300)
    await sleep(0.8)

    # Zoom the brand mark progressively until it fills the screen
    await page.evaluate("""
        const brand = document.querySelector('.brand-mark');
        if (brand) {
            brand.style.transition = 'transform 1.3s cubic-bezier(0.25,0.46,0.45,0.94)';
            brand.style.position   = 'relative';
            brand.style.zIndex     = '9999';
            brand.style.display    = 'inline-block';
            requestAnimationFrame(() => requestAnimationFrame(() => {
                brand.style.transform = 'scale(9)';
            }));
        }
    """)
    await sleep(1.4)

    # Fade to dark
    await page.evaluate("""
        const ov = window.__sf.showOverlay({ bg:'rgba(26,22,18,0.0)', fadeIn:false });
        if (ov) {
            setTimeout(() => {
                ov.style.transition = 'background 0.85s ease';
                ov.style.background = 'rgba(26,22,18,1)';
            }, 80);
        }
    """)
    await sleep(1.1)

    # Show salaryfree logotype centred
    await page.evaluate("""
        const ov = document.getElementById('__sf_ov');
        if (ov) {
            ov.innerHTML = `
                <div style="text-align:center;">
                  <div style="font-size:2.8rem;letter-spacing:-0.02em;line-height:1.1;">
                    <span style="font-family:'Space Grotesk',sans-serif;font-weight:400;color:#a8bfd8;letter-spacing:-0.01em;">salary</span><span style="font-family:'DM Serif Display',Georgia,serif;font-style:italic;color:#c9715f;letter-spacing:-0.02em;">free</span>
                  </div>
                </div>`;
        }
    """)
    await sleep(2.2)

    # Fade out logo, fade in tagline
    await page.evaluate("""
        const ov = document.getElementById('__sf_ov');
        if (ov) {
            ov.style.transition = 'opacity 0.55s ease';
            ov.style.opacity = '0';
            setTimeout(() => {
                ov.innerHTML = `
                    <div style="max-width:300px;text-align:center;">
                      <p style="font-family:'DM Serif Display',Georgia,serif;font-size:1.6rem;color:#faf7f2;line-height:1.5;font-style:italic;margin:0;">
                        You might be more <em style="color:#c9715f;">free</em> than you think.
                      </p>
                      <p style="font-family:'Space Grotesk',sans-serif;font-size:0.75rem;color:rgba(255,255,255,0.4);margin-top:22px;letter-spacing:0.07em;text-transform:uppercase;">
                        salaryfree.in
                      </p>
                    </div>`;
                ov.style.opacity = '1';
            }, 650);
        }
    """)
    await sleep(4.0)

    await page.evaluate("window.__sf.fadeOutOverlay();")
    await sleep(1.2)

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
async def run():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--window-size=390,560"],
        )
        context = await browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=2,
            record_video_dir=str(OUTPUT_DIR),
            record_video_size=VIEWPORT,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        )
        await context.add_init_script(FX_INIT_SCRIPT)
        page = await context.new_page()

        scenes = [
            scene_home,
            scene_scenario_selector,
            scene_tier1_questions,
            scene_expense_estimate,
            scene_assets,
            scene_tier1_results,
            scene_blind_spots,
            scene_tier2_questions,
            scene_tier2_results,
            scene_rates_adjust,
            scene_advanced_options,
            scene_finale,
        ]

        for scene_fn in scenes:
            try:
                await scene_fn(page)
            except Exception as e:
                print(f"\n  ✗ {scene_fn.__name__} failed: {e}")
                import traceback; traceback.print_exc()
                # Continue to next scene rather than aborting
                continue

        await context.close()
        await browser.close()

    videos = sorted(OUTPUT_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if videos:
        latest = videos[-1]
        print(f"\n✅ Recording saved: {latest}")
        print("\nConvert to social-ready MP4 (1080×1560, 2/3-screen aspect):")
        print(f"  ffmpeg -i '{latest}' \\")
        print(f"      -vf 'scale=1080:1560:flags=lanczos,fps=30' \\")
        print(f"      -c:v libx264 -crf 16 -preset slow -movflags +faststart \\")
        print(f"      ad_clips/final/salaryfree_ad.mp4")
    else:
        print("\n⚠ No video file found in", OUTPUT_DIR)


if __name__ == "__main__":
    asyncio.run(run())
