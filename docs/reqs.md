**Overall Requirements**
- Build a mobile browser app in the domain captured in the #domain.md file
- The app should load very fast
- The app should unfold vertically - information to capture should unfold vertically
- The app should make data entry easy by using pre-configured data templates
- A story building approach has to be taken to capture the data
- A sense of completion and quality of inputs should be given to the user by using a progress bar
- A click through demo should be available to the user. The demo should use representative sample data that will show all features to the user
- A vertically flowing graph should be used to convey the family financial health over the future years
- Floating scroll buttons should be available
- Easy social login and guest mode that persists across sessions should be available.

**Technical Requirements**
- python django
- IONIC framework
- sqlite




**Founder FIRE Specific Requirements**
- **Venture Profile**:
    - Capture "Venture" details: Name, Stage (Idea, MVP, Growth), Target Runway (months).
    - **Startup Costs**: One-time vs Recurring business expenses (separate from family expenses).
    - **Founder Salary**: distinct from "Employment Income". Ability to model "Zero Salary" periods.
    - **Side Hustle / Consulting**: Ability to model "Fractional Work" income that supports the runway but tapers off as the venture grows.
- **Risk & Scenarios**:
    - **Business Failure Probability**: Add a specific uncertainty factor for the venture itself.
    - **Separation of Assets**: Explicitly tag assets as "Personal" vs "Business Pledged" (assets that might be liquidated to save the business).
    - **Worst-Case Planning**: Specific "What If" scenario for "Business Failure + Medical Emergency" occurring simultaneously.
- **Runway Calculation**:
    - **Budget Modes**: Toggle between "Comfort Budget" (current lifestyle) and "Austerity Budget" (stripped down expenses) to see impact on runway.
    - **Emergency Fund Lock**: Logic to set aside a fixed "Emergency Fund" (e.g., 6 months expenses) that is *excluded* from the Runway calculation.
    - **Insurance Check**: Explicitly prompt for "Private Health Insurance" costs in the post-quit expense model (replacing employer cover).
    - Calculate "Family Runway" (how long family survives on liquid assets).
    - Calculate "Business Runway" (how long business survives on its capital).
    - Highlight the intersection/gap between these two.

**Smart Defaults & Categorization**
- **Expense Categories**:
    - **Needs (Survival)**: Housing, Food, Utilities, Insurance, Education (School Fees).
    - **Wants (Lifestyle)**: Travel, Dining Out, Entertainment, Luxury Goods.
    - **Savings/Investments**: SIPs, PPF, etc. (These stop or reduce during runway phase).
- **Smart Splits**:
    - Auto-calculate default splits based on Family Profile (e.g., if Child Age > 4, allocate 15% to Education).
    - **Slider UI**: Provide a simple slider interface to adjust the "Needs vs Wants" split (e.g., 50/30/20 rule as a baseline).
    - **Dynamic Updates**: Moving the slider should immediately update the "Austerity Budget" calculation.

**Financial Health Graph**
- **Stacked Area Chart**:
    - **X-Axis**: Years (Current Year to +25 Years).
    - **Y-Axis**: Amount (Inflation Adjusted).
    - **Layers**:
        1.  **Base Layer (Red)**: Survival Expenses (Needs).
        2.  **Middle Layer (Orange)**: Lifestyle Expenses (Wants).
        3.  **Top Layer (Green)**: Available Passive Income (from Assets).
    - **Visual Indicators**:
        - **Runway Gap**: Highlight area where Passive Income < Survival Expenses.
        - **Freedom Point**: Mark the year where Passive Income > Total Expenses.

**Founder Finance Concepts (from Research)**
- **Burn Rate Management**:
    - Explicitly track "Personal Burn Rate" separate from "Business Burn Rate".
    - Allow user to toggle "Debt Repayment" strategies (e.g., pause principal repayment on home loan if possible - *advanced feature*).
- **Emergency Fund Logic**:
    - **Hard Lock**: The Emergency Fund (e.g., 6 months of Survival Expenses) is *never* touched for Business Runway.
    - **Visual Warning**: If Runway calculation dips into Emergency Fund, show a critical alert.
- **Post-Quit Considerations**:
    - **Health Insurance**: Mandatory prompt to add "Private Health Insurance" expense if "Employer Insurance" is currently active.
    - **Retirals**: Toggle to "Pause PF/NPS Contributions" during the bootstrapping phase to increase cash flow.
    - **Income Boosters**:
        - **Side Hustle**: Add a "Consulting/Freelance" income stream that tapers off over 1-2 years.
        - **Asset Liquidation**: Option to mark specific assets (e.g., "Second Car") for liquidation to boost initial runway.
