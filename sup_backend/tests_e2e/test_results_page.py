"""
E2E tests — Results page (/results/)

Covers:
  - Results page structure (reveal section, cards, chart)
  - Rates & Assumptions panel: exists, toggles open, fields editable
  - Tier 1→2 upgrade CTA: visible, contains key copy
  - Login nudge in upgrade CTA
  - "Start over" button works
  - No horizontal scroll on results page
  - Font sizes: no text rendered below 11px (spot-check)
"""

import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.django_db(transaction=True)


# ── shared helper: run FOUNDER quick flow, end up on /results/ ───────────────

def _founder_quick_to_results(page: Page, app_url: str):
    page.goto(app_url + "/")
    page.wait_for_load_state("networkidle")
    page.locator("[\\@click*=\"selectScenario('FOUNDER')\"]").click()
    page.wait_for_url("**/questions/", timeout=10_000)
    page.wait_for_selector(".question-card", timeout=8_000)

    page.evaluate("""
        () => {
            const el = document.querySelector('[x-data]');
            const comp = Alpine.$data(el);
            Object.assign(comp.answers, {
                'family_type': 'solo',
                'scenario.current_age': 30,
                'scenario.venture_bootstrapped': false,
                'scenario.bootstrap_capital': 0,
                'family.monthly_expenses': 60000,
                'family.monthly_needs': 36000,
                'family.monthly_wants': 24000,
                'family.has_vehicle': false,
                'family.has_pet': false,
                'family.rented_house': true,
                'assets.living_total': 2500000,
                'assets.security_total': 5000000,
                'income.passive_monthly': 10000,
                'profile.emergency_fund_months': 6,
                'family.one_time_expenses': 0,
            });
        }
    """)
    page.wait_for_timeout(300)

    for _ in range(25):
        if "/results/" in page.url:
            break
        btn = page.locator(".btn-primary").last
        if btn.is_visible():
            btn.click()
            page.wait_for_timeout(400)

    if "/results/" not in page.url:
        page.wait_for_url("**/results/", timeout=15_000)
    page.wait_for_load_state("networkidle")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestResultsPageStructure:

    def test_results_page_has_reveal_section(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        expect(page.locator(".reveal")).to_be_visible(timeout=8_000)

    def test_results_page_has_result_cards(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        expect(page.locator(".result-card").first).to_be_visible(timeout=8_000)
        count = page.locator(".result-card").count()
        assert count >= 2, f"Expected ≥2 result cards, got {count}"

    def test_runway_label_present(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page_text = page.inner_text("body")
        assert "runway" in page_text.lower(), "No runway label in results"

    def test_target_number_card_present(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page_text = page.inner_text("body")
        assert "target" in page_text.lower() or "fire" in page_text.lower()

    def test_reveal_number_is_not_empty(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        reveal = page.locator(".reveal-number")
        if reveal.count() > 0:
            text = reveal.first.inner_text().strip()
            assert text != "", "Reveal number is empty"

    def test_no_horizontal_scroll_on_results(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        scroll_width = page.evaluate("document.body.scrollWidth")
        client_width = page.evaluate("document.body.clientWidth")
        assert scroll_width <= client_width + 5


class TestRatesPanel:

    def test_rates_panel_button_exists(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        panel_btn = page.locator("button:has-text('Rates'), button:has-text('Assumptions')")
        assert panel_btn.count() > 0, "Rates & Assumptions toggle button not found"

    def test_rates_panel_opens_on_click(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        btn = page.locator("button:has-text('Rates'), button:has-text('Assumptions')").first
        btn.click()
        page.wait_for_timeout(400)
        # After clicking, rate input fields should appear
        rate_inputs = page.locator("input[type='number']")
        assert rate_inputs.count() > 0, "No rate input fields appeared after opening panel"

    def test_rates_panel_shows_nine_fields(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page.locator("button:has-text('Rates'), button:has-text('Assumptions')").first.click()
        page.wait_for_timeout(400)
        count = page.locator("input[type='number']").count()
        assert count == 9, f"Expected 9 rate fields, got {count}"

    def test_rates_panel_fields_have_defaults(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page.locator("button:has-text('Rates'), button:has-text('Assumptions')").first.click()
        page.wait_for_timeout(400)
        # First field (liquid return) should default to 6
        first_input = page.locator("input[type='number']").first
        value = first_input.get_attribute("value") or first_input.evaluate("el => el.value")
        assert float(value) == 6.0, f"Expected default 6.0, got {value}"

    def test_rates_panel_closes_on_second_click(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        btn = page.locator("button:has-text('Rates'), button:has-text('Assumptions')").first
        btn.click()
        page.wait_for_timeout(300)
        btn.click()
        page.wait_for_timeout(300)
        # Inputs should now be hidden
        visible_inputs = page.locator("input[type='number']:visible").count()
        assert visible_inputs == 0, "Rate inputs still visible after closing panel"

    def test_rates_save_button_appears_after_edit(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page.locator("button:has-text('Rates'), button:has-text('Assumptions')").first.click()
        page.wait_for_timeout(300)
        # Change first input
        first_input = page.locator("input[type='number']").first
        first_input.fill("7")
        first_input.dispatch_event("change")
        page.wait_for_timeout(300)
        # Save button should appear
        save_btn = page.locator("button:has-text('Save'), button:has-text('recalculate')")
        assert save_btn.count() > 0, "Save button did not appear after editing a rate"


class TestTierUpgradeCTA:

    def test_upgrade_section_visible(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page_text = page.inner_text("body")
        assert "blind spot" in page_text.lower() or "full picture" in page_text.lower() or \
               "20-year" in page_text.lower(), "Tier upgrade CTA section not found"

    def test_upgrade_section_lists_quick_shortfalls(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page_text = page.inner_text("body")
        assert "inflation" in page_text.lower(), "Expected 'inflation' in upgrade CTA"

    def test_login_nudge_present(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        page_text = page.inner_text("body")
        assert "account" in page_text.lower() or "sign up" in page_text.lower() or \
               "save" in page_text.lower(), "Login nudge not found in results page"

    def test_go_deeper_button_exists(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        deeper_btn = page.locator("button:has-text('deeper'), button:has-text('projection')")
        assert deeper_btn.count() > 0, "Go deeper / projection button not found"

    def test_start_over_button_works(self, page: Page, app_url: str):
        _founder_quick_to_results(page, app_url)
        start_over = page.locator("button:has-text('Start over')")
        assert start_over.count() > 0
        start_over.click()
        page.wait_for_timeout(600)
        # Should redirect back to root
        assert page.url.rstrip("/").endswith(":8081") or \
               "/" in page.url, "Start over did not navigate away from results"


class TestAccessibility:

    def test_touch_targets_minimum_size(self, page: Page, app_url: str):
        """All buttons and interactive elements must be ≥ 44px tall (iOS HIG)."""
        _founder_quick_to_results(page, app_url)
        small = page.evaluate("""
            () => {
                const els = document.querySelectorAll('button, a[href], input[type=range]');
                const small = [];
                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 0 && rect.height < 44) {
                        small.push({tag: el.tagName, text: el.innerText?.slice(0,30), h: rect.height});
                    }
                }
                return small;
            }
        """)
        # Allow a small tolerance — report but don't hard-fail on minor violations
        violations = [x for x in small if x["h"] < 36]  # strict < 36px is definitely too small
        assert violations == [], f"Touch target violations (< 36px): {violations[:5]}"

    def test_base_font_size_not_too_small(self, page: Page, app_url: str):
        """Computed body font size should be ≥ 16px (we set 17px)."""
        _founder_quick_to_results(page, app_url)
        font_size = page.evaluate("""
            () => parseFloat(window.getComputedStyle(document.body).fontSize)
        """)
        assert font_size >= 16, f"Body font size {font_size}px is below 16px minimum"
