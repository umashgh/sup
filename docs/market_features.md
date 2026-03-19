Market Features — ProjectionLab + Toolsuite

Summary
- This document merges feature sets observed on ProjectionLab and Toolsuite and maps each feature to whether it is already represented in our project plan (`docs/plan.md`) and how it differs from our current direction.

Notes on methodology
- Source: ProjectionLab website and toolsuite.in homepage (2026-02-14). I merged public feature descriptions and translated them into concise product capabilities.
- "In plan" indicates whether the feature is already aligned with content in `docs/plan.md` (founder + family FIRE planning). If "No", the right column suggests the difference and why it might matter for Sup.

ProjectionLab (key capabilities)
- Monte Carlo simulations / "chance of success"
- Cash-flow analysis (Sankey diagrams)
- Tax analytics / effective tax bracket breakdown
- Historical backtesting / market volatility scenarios
- Multiple account types, contribution orders, drawdown strategies
- International tax presets and account types
- Rent vs. own analysis, buy vs. rent
- Event/milestone modeling (multi-phase retirement, part-time work)
- Tracking progress (actual vs projected)
- No account linking (privacy-first) + import/export

Toolsuite (key capabilities)
- Loan calculators and amortization schedules (EMI, per-payment rows)
- Amortization exports (CSV) and downloadable schedules
- Prepayment, balloon, lump-sum, variable-frequency payments
- Payment visualizations and Chart.js charts
- Copy-to-clipboard / shareable plan links / print-friendly output

Combined candidate features (merged list) with plan mapping

- Monte Carlo simulations / chance-of-success
  - In plan? : No
  - Notes: ProjectionLab-grade Monte Carlo would be new; valuable for founder scenarios if we extend to startup failure/dilution-aware MC.

- Cash-flow visualization (Sankey diagrams)
  - In plan? : Partially
  - Notes: `docs/plan.md` targets family + founder finances; Sankey-style cash-flow visualizations are not explicitly listed but align well with our aim to model family impact on startups.

- Tax analytics and multi-jurisdiction presets
  - In plan? : No
  - Notes: Useful for international founders; heavier effort (tax rules) and can be phased as a premium feature.

- Historical backtesting / black-swan modeling
  - In plan? : No
  - Notes: Adds credibility but requires market data ingestion & compute; consider as advanced analysis (later).

- Rent vs. own and specialized scenarios (72t, Roth conversions, SEPP)
  - In plan? : No
  - Notes: Useful for consumer audience; lower priority for founder-centric product unless targeted to household decisions.

- Loan & amortization toolkit (EMI, CSV export, prepay, balloon)
  - In plan? : No
  - Notes: Toolsuite strength — practical, transactional calculators. Could be reused for founder-investor payback schedules, revenue-share loans.

- Shareable plans, CSV/JSON export, print-friendly views
  - In plan? : Partially
  - Notes: `docs/plan.md` mentions knowledge base and app but not explicit export/share affordances. These are low-effort, high-value features for collaboration with advisors/investors.

- Founder / Startup-specific features (distinct Sup opportunities)
  - Startup equity & vesting modeling (vesting schedules, cliffs, 83(b) scenarios)
    - In plan? : Yes (aligned)
    - Notes: `docs/plan.md` focuses on founders & families; equity/vesting is a core differentiator and matches project focus.

  - Cap table history, dilution simulations, SAFEs/convertible notes modeling
    - In plan? : No (not explicitly listed)
    - Notes: High impact for founders; more product complexity (rounds, option pools, investor return modeling).

  - Two-track model: linked personal + venture finances (venture exit → personal FI)
    - In plan? : Yes (aligned)
    - Notes: This is central to our positioning and differentiates from general retirement tools.

  - Founder runway, burn, multi-venture dashboards
    - In plan? : Yes (aligned)
    - Notes: `docs/plan.md` intent supports these; implementation detail still needed.

  - Tax planning for founders (ISOs/NSOs, AMT, 83(b), exit tax scenarios by jurisdiction)
    - In plan? : No
    - Notes: Distinctly valuable but tax-complex; good for a phased premium feature.

  - Investor-return and cap table export for pitch decks (CSV/XLS)
    - In plan? : No
    - Notes: Practical bridge to fundraising workflows; complements cap table history.

- UX / sharing features
  - Interactive share links, read-only embeds, advisor mode
    - In plan? : Partially
    - Notes: `docs/plan.md` mentions knowledge base and app but not explicit sharing modes; these align with collaboration goals.

- Visualization primitives
  - Sankey cash-flow, amortization charts, cap-table waterfalls, runway timelines
    - In plan? : Partially
    - Notes: Visualizations are implied by plan goals (clarity for users), but specific chart types from ProjectionLab/Toolsuite can be adopted.

Prioritization guidance (suggested)
- MVP (near-term, low-effort / high-impact)
  - Two-track personal+venture modeling (already in plan)
  - Founder runway & burn tracking (already in plan)
  - Basic cap table + vesting schedule UI (start MVP without complex dilution modeling)
  - Export: CSV/print/share links for plans
  - Loan/amortization builder (reused for investor payback schedules)

- v1 (medium effort)
  - Monte Carlo including startup-risk factors
  - Cap-table dilution simulations and SAFE/note models
  - Sankey cash-flow visualizations and amortization charts
  - Advisor / investor view + sanitized sharing

- Later (higher effort / data / regulatory risk)
  - Full tax analytics (multi-jurisdiction); AMT and ISO modeling
  - Historical backtesting & black-swan modeling (needs market data)

Appendix: quick mapping to `docs/plan.md`
- `docs/plan.md` emphasis: founder + family FIRE planning, knowledge base (MCP), mobile browser app. The plan does not contain a full product feature list; features marked "In plan? : Yes (aligned)" above are those that naturally follow from the plan's goals (founder focus, family-safety modeling). Most ProjectionLab/Toolsuite features are new opportunities (marked No) and can be staged per the prioritization above.

File created: summary merging ProjectionLab + Toolsuite features and mapping to `docs/plan.md` (no changes made to existing plan files).
