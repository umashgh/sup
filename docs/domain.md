---
applyTo: '**'
---
FreeUp app Requirements Document

A. CONTEXT: This is an app for salaried individuals in India. There are many who are into desk bound jobs, and are looking to free up their time to pursue their passions, hobbies, or side hustles. For that they need to be in a position to live off their assets, and not depend on their regular salary income. This app looks at the family expenses, and the incomes and assets used to service those expenses. A cashflow projection is done for a multi-year period, and stress points are identified. The user can then take actions to mitigate those stress points, and further do a What If analysis to see how the changes impact the cashflow projection. 

B. DOMAIN KNOWLEDGE
1.1.	Purpose: The freeup app is designed for Indian household financial planning, enabling users (and their financial advisors) to assess the sufficiency of their income and assets to meet regular and one-time expenses over a multi-year horizon.

1.1.1    This analysis is done for a family. Family Profile:
1.1.1.1    Contains family members, houses, vehicles, their investment areas data, and wealth/income/expense levels.
1.1.1.2   Family members include earning adults, dependent adults, children, and pets.
1.1.1.3    Relevant data for each family member: 
1.1.1.3.1.  Earning adult: age, retirement age, has pf, health_insurance. 
1.1.1.3.2.  Dependent adult: age, has pf, health insurance, allowance. 
1.1.1.3.3.  Child: age, allowance, age when graduation starts, age when expense ends.
1.1.1.3.4.  Pet: age.
1.1.1.4.   Houses: current value, expected renovation age.
1.1.1.5.   Vehicles: current value, expected replacement age.
1.1.1.6.    Investment areas:
1.1.1.6.1.  Financial assets: user-selected financial assets (master category: financial).
1.1.1.6.2.  Physical assets: user-selected physical assets (master category: physical).
1.1.1.7.   Levels:
1.1.1.7.1.  Wealth level: 1 (up to 2 crores), 2 (2 to 10 crores), 3 (above 10 crores).
1.1.1.7.2. Income level: 1 (up to 20 lakhs), 2 (20 lakhs to 50 lakhs), 3 (above 50 lakhs).
1.1.1.7.3. Expense level: 1 (up to 20 lakhs), 2 (20 lakhs to 50 lakhs), 3 (above 50 lakhs).

1.2.	Asset Types:
1.2.1.	Liquid assets: Amenable to Systematic Withdrawal Plan (SWP), e.g., mutual funds, FDs, savings accounts.
1.2.2.	Illiquid assets: Not SWP-eligible, e.g., real estate, gold, vehicles.
1.2.3.    Retirals: Assets that are typically not liquid until retirement, e.g., Provident Fund (PF), National Pension System (NPS), gratuity.
1.2.4.   Assets have appreciation pct (typically for real estate) and return pct (for all types of assets). Both appreciate base value
1.2.5.  Assets can be fully or partly liquidated to meet unmet expenses
1.2.3.	Asset values can be mostly derived from a master data table as the data is fairly standard
1.2.4.	Typical split: 60% liquid, 40% illiquid, but user-configurable.

1.3.	Income Streams:
1.3.1.	Derived from employment, pension (from family member information), asset returns (interest, dividends, rent, SWP) (from family profile investment information) etc.
1.3.2.	Asset must be linked to an income stream for returns to be counted as withdrawal income. Not all the asset return for the year needs to be withdrawn
1.3.3. Incomes have a growth pct (e.g. increments for salary, or better returns from business) and efficiency pct (e.g. tax, brokerage, etc. that reduces the in-hand income)

1.4.	Expenses:
1.4.1.	Types: Monthly, annual, one-time (e.g., asset replacement, life events).
1.4.2.	One-time expenses: Typically met by illiquid or non-income-generating liquid assets.
1.4.3.	Insurance: Some expenses are covered by insurance (copay logic applies).
1.4.4.	Expenses have inflation pct (e.g., healthcare, education, lifestyle) and uncertainty level (none, low, medium, high, volatile).
1.4.5.    Expenses are derived from household, vehicle, child, dependent adult, earning adult, pet, etc. They can be selected from a master data table based on the family profile.
1.4.6.    Expense Categorization (Smart Defaults):
1.4.6.1.  **Needs (Survival)**:
    - Housing (Rent/EMI, Maintenance)
    - Food & Groceries (Base level)
    - Utilities (Electricity, Internet, Mobile)
    - Insurance (Life, Health)
    - Education (School Fees - derived from Child Age)
    - Dependent Care (Medical/Allowance - derived from Dependent Adult)
1.4.6.2.  **Wants (Lifestyle)**:
    - Travel (Vacations)
    - Dining Out / Entertainment
    - Shopping / Gadgets
    - Vehicle Upgrades
1.4.6.3.  **Savings/Investments**:
    - SIPs, PPF, VPF (Voluntary)
1.4.7.    Default Split Logic:
    - Base Split: 50% Needs, 30% Wants, 20% Savings.
    - Adjustments:
        - If Child Age 4-21: Increase Needs by 10% (Education), reduce Wants/Savings.
        - If Dependent Adult present: Increase Needs by 5% (Medical), reduce Wants.
        - If Home Loan present: Increase Needs (EMI), reduce Savings.

1.5.	Projection Logic:
1.5.1.	All values are projected over a user-defined period (default: 25 years).
1.5.2.	Inflation, growth, and uncertainty rates are applied as per master data and user configuration.

1.6.	Business Rules:
1.6.1.	All data is user-centric; every record is linked to a user.
1.6.2.	Reset logic for assets, incomes, and expenses is robust, context-aware, and idempotent.
1.6.2.1. Reset logic is used to create a best guess user's financial data (default) based on the family profile
1.6.2.1.	Reset logic should not delete user-added data unless explicitly mentioned.
1.6.2.2.    Default assets: based on houses, PF information from family members, investment areas based on wealth level.
1.6.2.3.    Default incomes: based on family members earning members salary, dependent adults pension, earning members pension after retirement, rent on houses, withdrawal from liquid investment areas. based on income level.
1.6.2.4.    Default expenses: based on family members, household, houses, vehicles, investment areas. chosen based on who/what expense pertains to and expense level.
1.6.2.5.    Assets have to be put in place first, then incomes, then expenses.
1.6.2.6.    Large one time expenses (>5 lakh) can be met by suitable assets (which are not being used for any income generation).
1.6.3.	All master data queries use the correct number_level (wealth/income/expense level).
1.6.4.	Indian number formatting (lakhs/crores) is used throughout the UI.

1.6.5.  Calculation involves putting up an year-wise cashflow projection, with annualized incomes and expenses, and then calculating the net cashflow for each year.
1.6.5.1.  For asset based incomes, the asset value is first increased by appreciation_pct, and then increased by growth pct, and then the withdrawal_pct is applied to get the income.
1.6.5.1.1 All incomes are reduced by efficiency_pct to get the in-hand income.
1.6.5.2.  For one time expenses, the linked asset is projected till the expense year, and then the expense is met from that asset. Asset value is reduced by the expense amount from that year onwards.
1.6.5.3.  Excess cashflow is carried forward to the next year, and shortfall is met by fully or partly reducing a liquid asset, if possible. This shortfall is highlighted as a problem area.
1.6.5.6. Excess cashflow over 10% of annual income is flagged as a waste of income, and can be used to upgrade lifestyle (more expense) or build another asset.
1.6.6.	Monte Carlo simulations are run to assess robustness under uncertainty. Uncertainty levels are used to perturb the inputs (asset returns, inflation rates, expense shocks, income interruptions) and run 1000+ simulations.
1.6.7.  What if analysis applies more user controlled perturbations to the inputs (delete incomes, add expenses, change asset returns, etc.) and runs the cashflow projection again.
1.6.8.  The output is more impactful when the observations are summarised, and recommendations are made based on the observations. 
1.6.8.1. Recent observations, or larger problems need more focus.
1.6.8.2. Ares of observations can be:
1.6.8.2.1	Consistently excess cash over 10% of annual income needs to be flagged as a waste of income, can go towards upgrading lifestyle (more expense) or build another asset, particularly if there is a one time expense not being met
1.6.8.2.2	If the excess is more than salary for earning adult, can mention the adult doesn’t seem to need the salary
1.6.8.2.3 If there is a shortfall, it needs to be highlighted as a problem area, and the user needs to be prompted to look at the cashflow chart
1.6.8.2.4 If an asset was used to meet a shortfall, it hs to be recorder in the observations
1.6.8.2.4 Free Up year: the earliest when the regular income is no longer needed to meet expenses, and the user can start living off the assets. This is typically when the assets are enough to meet all expenses for the rest of the life. This year has to be identified and recorded
1.6.8.2. Cashflow can be shown as a annual stacked income chart against total expenses, and total assets after withdrawals. Such a chart will give a visual feedback about the financial health of the user.

2.	Coding Standards and Preferences
2.1.	General:
2.1.1.	Use ORM for all DB interactions. VERY IMPORTANT: Stick to the models and fields defined in this document. Do not create new models or fields unless explicitly mentioned.
2.1.2.	Use built-in authentication and admin.
2.1.3.	All user-level data models must have a direct ForeignKey to the user.
2.1.4.	All business logic (reset, import, projections) is implemented as reusable service functions.

2.2.	Styling & UX:
2.2.1.	Use HTMX and template partials for better user experience
2.2.2.	All forms and lists use Bootstrap CSS. Both to have consistent look and feel
2.2.3.	Tab navigation between fields to be enabled
2.2.4.	Content is displayed in centered, semi-transparent cards.
2.2.5.	Has to render well on both desktop and mobile phone, but mobile first
2.2.6.	Banded tables (alternating row colors) for all lists.
2.2.7.	Consistent background wallpaper (randomly rotated from images that depict flight, active life, creative life, religious tourism, startup life etc).
2.2.8.	All buttons and navigation controls use consistent, modern styling.
2.2.9.	Dynamic field logic in forms (e.g., enable/disable, show/hide based on user input).
2.2.10.	Use radio buttons for member type, checkboxes for booleans, and appropriate widgets for all fields.
2.2.11.	Saving a page should progress to the next page (like in a wizard)
2.2.12. Provide micro-animations for user interactions (e.g., button clicks, form submissions)
2.2.13  Should be able to enable dark mode
2.2.14. Use monochromatic color scheme for icons and buttons, with a consistent color palette across the application
2.2.15  To segue into details from a summary (e.g. family members summary to family member details), a bold right arrow which leads to the list with horizontal scrolling animation. When saved in details, it should return to the summary with a horizontal scrolling animation.

2.3.	Admin & Bulk Operations:
2.3.1.	Admin is accessible via navbar for superusers.
2.3.2.	Master data (AssetMaster, IncomeMaster, ExpenseMaster) is managed via admin and bulk CSV import.
2.3.3.	All master admin screens show all columns in list view.
2.3.4.	CSV import/export is available for all master and user-level tables.
2.3.5.	Provide downloadable CSV templates for all bulk import screens.

2.4.	Testing & Data:
2.4.1.	Create admin user (admin/admin) and test user (u1/u1) on setup.
2.4.2.	Provide basic CSV files for initial master data import.
2.4.3.	Write test cases for all features: 
2.4.3.1. screen accessibility, 
2.4.3.2. login, 
2.4.3.3 CRUD, 
2.4.3.4. reset logic, 
2.4.3.5. bulk import 
2.4.3.6 check the validity of every href in all htmls, 
2.4.3.7. check validity of every url
2.4.4.	Import master data in section 14 of this document
2.4.5.  Periodically run the test cases and fix the issues that come up

2.5.	Other:
2.5.1.	All code for features must be implemented in full (no “pattern can be reused” placeholders).
2.5.2.	All new/updated fields must be handled in models, forms, admin, and templates.
2.5.3.	All code changes must be made using proper version control and migration practices.
2.5.4.	Copy-paste requirements from this document along with requirement number wherever they are being implemented in the code
2.5.5.  VERY IMPORTANT: Implement logic only as per the requirements in this document. Do not add any new features or logic that is not specified here. If you think something is missing, please ask for clarification before implementing it.
2.5.6.  VERY IMPORTANT: Do not bring in any general domain understading or assumptions that are not explicitly mentioned in this document. Stick to the requirements as they are written.
 
C. REQUIREMENTS DOCUMENT (REQ1) – DETAILED LEVEL
1.	USER TYPES
1.1	Anonymous users: Can view the home page.
1.2	Authenticated users: Can access all CRUD, assessment, and results features.
1.3	Superusers: Can access admin and manage master data.

2.	LANDING & NAVIGATION
2.1	Home Page:
2.1.1	Accessible to all users.
2.1.2	Section 1: Shows a large "FREE UP" banner. Below that a upward scrolling action text chosen at random from a fixed list ["Scale your side hustle", "Settle down in the mountains", "Regrow forests", "Prep a sub-4", "Become a teacher", "Live off-grid", "Explore ancient ruins", "Sail around the world", "Master an instrument",  "Write a masterpiece", "Take up acting", "Become a chef", "Join a mission",  "Fund-raise a cause", "Run an ultra", "Walk the continent", "Get your PhD", "Grow a farm", "Build a school", "Join a charity", "Mentor a prodigy", "Restore a classic", "Achieve fluency"]
2.1.3	Section 2: Two large, cheerful buttons: “Assess” (starts wizard) and “View Old Assessment”.
2.1.3.1. “Assess” button takes the user to the logic/register page if not authenticated, or directly to the family profile page if authenticated. After authentication, the user is redirected to the family profile page.
2.1.3.2. “View Old Assessment” button takes the user to the logic/register page if not authenticated, or directly to the user's results page if authenticated. After authentication, the user is redirected to the results page.
2.1.4	Visually appealing background, wallpaper randomly circulating between a set of images mentioned earlier, mobile first css styling
2.1.5	Banded tables for any lists.
2.2	Navigation:
2.2.1	Top navbar with links to all major modules (family profile, assets, incomes, expenses, calculation & results, config, admin).
2.2.2	Logout available from navbar.
2.2.3	Page sequence of the app is as here: Home page -> Logic/Register if needed -> Family Profile [Link to Family Members, Houses, Vehicles in the profile page] -> Assets -> Incomes -> Expenses -> [Calculate] Results. Top nvbar links appear in that order. Modelling config can be the last link, and it doesn’t need to come in the flow.
2.2.4	In every page, there needs to be a Save button that takes one to the next page in the above sequence
2.2.5	User has to save Assets, Incomes and Expenses in that order

3.	AUTHENTICATION
3.1	Login/Registration:
3.1.1	Normal Login and Register buttons in the nav bar
3.1.2	Clicking “Assess” or “View Old Assessment” prompts login/registration if not authenticated.
3.1.3.  In future versions, social login can be added, but for now only email/password login is needed.
3.1.4   Provision has to made for end-to-end encryption of user data as this is a financial app. Just a placeholder for now, implementation can be doone later.
3.2	Admin:
3.2.1	Admin functionality for user and master data management.
3.2.2	Admin login created on setup (user id admin, password admin).

4.	ADMIN/MASTER DATA MANAGEMENT
4.1	Master Data Models:
4.1.1	AssetMaster: category (financial, real estate, retirals, others), name, appreciation_pct (default 0), typical_return_pct (defautlt 0), typical_initial_value (default 0, positive number), uncertainty_level (none, low, medium, high, volatile) (default none), basis (single/per unit) (default single), liquid (yes/no default no), number_level (1/2/3).
4.1.2	IncomeMaster: category (salary, asset return, others), name, growth_pct (default 0), typical_amount (default 0, positive number), frequency (monthly, annual, one time. default annual), efficiency_pct (default 100), uncertainty_level  (none, low, medium, high, volatile) (default none), number_level (1/2/3).
4.1.3	ExpenseMaster: category, name, pertains_to (household, adult, child, house, vehicle, others. default household), inflation_pct (default 0), typical_amount (default 0, positive number), frequency (monthly, annual, one time. default annual), insurance_indicator (yes/no, default no), copay_percent (default 0, positive number), uncertainty_level (none, low, medium, high, volatile) (default none), number_level (1/2/3).
4.1.4.  These master data models are used to populate the user-level data models (Assets, Incomes, Expenses) with default values. So the columns have to be kept identical to the user-level data models.
4.2	Admin Screens:
4.2.1	All columns shown in list view.
4.2.2	Bulk import/export via CSV.
4.2.3	Downloadable CSV templates for each master.
4.2.4	Initial tables in section 14 of this document. Import them into master tables

5.	CRUD FOR FAMILY PROFILE DATA
5.1	Configuration screen:
5.1.1	User can set modeling start/end years (default: current year to +25 years). All projections done as part of 6. Calculation & Results use the start year as base, and stop with the end year.
5.1.2	User can set bank rate (default: 6%). This will be used as the discounting rate for any NPV calculations, and also to calculate risk adjusted returns
5.1.3   The configuration fields are stored in Family Profile model, and are used in the calculations done in Calculation & Results.
5.2	Family Profile:
5.2.1	This is the first landing screen when the user clicks Assess button
5.2.2	Single profile per user, with all key fields:
5.2.2.1	Display only Family total members and splits (earning adults, dependent adults, children, pets – as summarized from Family Members list, non-editable here), link to Edit Family Members List
5.2.2.1.1.	Edit Family Members List: Table CRUD for earning adults, dependent adults, children, pets. 
5.2.2.1.2.  Add or Edit of family members opens a form with all fields. Only the fields relevant to the member type are editable, and the user can enter values for those fields only. Other fields are nulled out (model has to accommodate that)
5.2.2.1.2.1 Data model:
5.2.2.1.2.1.1 Fields: user, member_type (earning adult, dependent adult, child, pet), name, age, retirement_age (positive integer default 60), has_pf (yes/no, default no), health_insurance (yes/no default no), allowance (currency field), age_of_graduation_start (positive integer default 18), age_of_expenses_end (posituve integer default 24).
5.2.2.1.3. Relevant fields by member types:
5.2.2.1.3.1. Earning adult: age, retirement age, has pf, health_insurance. 
5.2.2.1.3.2. Dependent adult: age, has pf, health insurance, allowance. 
5.2.2.1.3.3. Child: age, allowance, age of graduation start, age of expenses end. 
5.2.2.1.3.4. Pet: age
5.2.2.2. Number of houses, link to edit Houses list (saving behavior as in Family Members)
5.2.2.2.1 Edit Houses: Editable that shows the houses, and CRUD should be possible through row level Edit/Delete buttons and Add button on top
5.2.2.2.3 Data model
5.2.2.2.3.1 Fields: name, current value (currency), expected renovation year (current year +10, positive integer).
5.2.2.2.4 Counts summarized in profile. Save button click brings one back to whatever its previous page was
5.2.2.3. Number of vehicles and link to edit Vehicles (saving behavior as in Family Members) 
5.2.2.2.1 Edit Vehicles: Editable that shows the vehicles, and CRUD should be possible through row level Edit/Delete buttons and Add button on top
5.2.2.2.3 Data model
5.2.2.2.3.1 Fields: name, current value (currency, nullable), expected replacement year (current year +5, positive integer).
5.2.2.2.4 Counts summarized in profile. Save button click brings one back to whatever its previous page was
5.2.2.4. Wealth/income/expense levels, 
5.2.2.5. Whether living in rented house. 
5.2.2.6. Areas of Investment :
5.2.2.6.1	Financial assets for user-selected financial assets. This is a distinct list of assets of master assets category “financial” from which the user can select
5.2.2.6.2	Physical assets  for user-selected physical assets. This is a distinct list of assets of mster assets category “physical” from which the user can select
5.2.6  Family Profile Data model:
5.2.6.1 Fields: user, modelling start year (default current year), modelling end year (default current year + 20), bank rate (default 6%), wealth_level (1/2/3), income_level (1/2/3), expense_level (1/2/3), rented_house (yes/no default no), financial_investment_areas (JSON field with list of selected financial assets), physical_investment_areas (JSON field with list of selected physical assets).

6.	CRUD FOR USER ASSETS DATA:
6.1	User assets page shows a List of all user's assets (formset). 
6.1.1	All user assets have default values pulled from AssetMaster based on wealth level and the specific item from master.
6.1.2	The page shows a Summary of asset value by category at top of page.
6.1.3	Collapsible summary-details div for asset table.
6.1.4.  User can add new assets or edit/delete existing ones.
6.1.4.1. Add Asset: Button opens a form to add a new asset. 
6.1.4.1.1. If the user selects a master asset, the default values are pulled from AssetMaster based on wealth level and the specific item. 
6.1.4.1.2. Else the user can enter a new asset name or category. If all master fields are provided, the asset is also saved as a staged master asset in a separate table for admin review.
6.1.5.  Data model: 
6.1.5.1. Fields: user, name, category, start year (default current year), end year (default start year + 20), initial_value (default 0, positive number), appreciation_pct (default 0), return_pct (default 0), SWP possible (yes/no. default no), uncertainty_level (none, low, medium, high, volatile) (default none), liquid (yes/no default no).
6.1.5.2. While default values are pulled from AssetMaster, the user can change the values as needed. User can enter names and categories that are not in the master data
6.2	Reset Assets: Button triggers logic to do the following and show a refreshed page:
6.2.1	Analyze profile, family members, houses, financial investment areas, physical investment areas.
6.2.2	Pull assets selected from master data based on Reset Logic mentioned in the Domain Knowledge section
6.2.3	Add PF per earning member and dependent adult if they have it selected. Default end date is retirement year for earning adults, and modelling end year for dependent adults. If PF is not selected, it is not added.
6.2.4	Remove/archive assets not matching profile (unless manually added).
6.2.5	Add missing typical assets.
6.2.6	Start year is the current year and end year is the modelling end year
6.2.7   Do not reset assets that are manually added by the user, unless explicitly mentioned.

7.	CRUD FOR USER INCOMES DATA:
7.1	User Income page shows a List of all incomes (formset). 
7.1.1	All user incomes have default values pulled from IncomeMaster based on income level and the specific item from IncomeMaster.
7.1.2	Total current income by category shown at top of the page.
7.1.3	Collapsible summary-details div for income table.
7.1.4.  User can add new incomes or edit/delete existing ones.
7.1.4.1. Add Income: Button opens a form to add a new income. 
7.1.4.1.1. If the user selects a master asset, the default values are pulled from IncomeMaster based on wealth level and the specific item. 
7.1.4.1.2. Else the user can enter a new income name or category. If all master fields are provided, the asset is also saved as a staged master income in a separate table for admin review.
7.1.5.  Data model: 
7.1.5.1. Fields: user, category (salary, asset return, others), name, growth_pct (default 0), typical_amount (default 0, positive number), frequency (monthly, annual, one time. default annual), efficiency_pct (default 100), uncertainty_level  (none, low, medium, high, volatile) (default none), start_year (default current year), end_year (default modelling end year).
7.1.5.2. While default values are pulled from IncomeMaster, the user can change the values as needed. User can enter names and categories that are not in the master data
7.2	Reset Incomes: Button at top triggers logic to do the following and show a refreshed page:
7.2.1	Create employment/pension income based on family members. For earning adult salary Start year is modelling start year, end year is retirement year, and pension starts when salary ends. For dependent adults with PF, pension can be added from current year till modelling end year 
7.2.2	If liquid financial assets exist, add withdrawal line items from them with 0% withdrawal, which the user can change later
7.2.3	If the number of houses (less 1 if not living in a rented house) add one line for rent which is return. Same for commercial property also
7.2.4	Remove/archive incomes not matching assets/profile (unless manually added).
7.2.5	Add missing typical incomes.
7.2.6. Start year is the current year and end year is the modelling end year, except for items mentioned above
7.2.7   Do not reset incomes that are manually added by the user, unless explicitly mentioned.

8.	CRUD FOR USER EXPENSES DATA:
8.1	User Expenses page shows a List of all expenses (formset). Fields: category, name, pertains_to, amount, inflation rates, frequency, insurance/copay, start/end years, uncertainty pct, etc.
8.1.1	All user expenses have Default values pulled from ExpenseMaster based on expense level and the specific item from ExpenseMaster.
8.1.2	Page shows a Summary of current expenses by category at top.
8.1.3	Collapsible summary-details div for expense table.
8.1.4.  User can add new expenses or edit/delete existing ones.
8.1.4.1     Add Expense: Button opens a form to add a new expense.
8.1.4.1.1 If the user selects a master expense, the default values are pulled from ExpenseMaster based on wealth level and the specific item.
8.1.4.1.2 Else the user can enter a new expense name or category. If all master fields are provided, the expense is also saved as a staged master expense in a separate table for admin review.
8.1.5.  Data model:
8.1.5.1 Fields: user, category, name, pertains_to (household, adult, child, house, vehicle, others. default household), inflation_pct (default 0), typical_amount (default 0, positive number), frequency (monthly, annual, one time. default annual), insurance_indicator (yes/no, default no), copay_percent (default 0, positive number), uncertainty_level (none, low, medium, high, volatile) (default none), start_year (default current year), end_year (default modelling end year).
8.2	Reset Expenses: Button at the top of the page triggers logic to do the following and show a refreshed page:
8.2.1	Create typical expenses based on family profile matching pertains to column in expense master (household, adult, child, house, vehicle, others). Number of rows will be based on basis (single/per unit) and values will be based on number_level.
8.2.1.1 For household expenses, add all expenses based on number_level (once as the basis is single). 
8.2.1.2 For each family member type, use the counts and  from family profile. Start and end years as appropriate.
8.2.1.3 For house and vehicle expenses, use the number of houses and vehicles from family profile.
8.2.2	Remove/archive expenses not matching profile/assets (unless manually added).
8.2.3	Add missing typical expenses.
8.2.5	For large one-time expenses (>5 lakh), project assets into year of expense and link a suitable asset (refer Domain Knowledge for what this means).

9.	CALCULATION & RESULTS
9.1 Page shows 4 buttons at the top: Cashflow Projection, Stress Testing, What If, View Results
9.1.1	Cashflow Projection: 
9.1.1.1 Runs cashflow projection logic as mentioned in Domain Knowledge section, and opens the Results page.
9.1.1.2 Yearly cashflow is saved to the database for each year in the projection period. IMPORTANT: But this is saved only for straight calculation and not for Stress Testing or What If.
9.1.1.3 Data model: 
9.1.1.3.1 Fields: user, year, total_income, income_spilts, total_expense, net_cashflow, total_assets_after_withdrawals, excess_cashflow, shortfall, observations
9.1.1.3.2 Income splits is a JSON field that contains the income categories and their summary amounts for that year
9.1.1.4 Free Up year,, if any, is noted in the observations field.
9.2 What If:
9.2.1 In What If, the user can change certain income, expense, and asset values, and then run the cashflow projection logic again.
9.2.2 The Results page shows the new cashflow projection results based on the modified values. But the values are not saved to the database.
9.3	Stress Testing:
9.3.1	Run 1000+ cashflow projections, varying as per uncertainty level:
9.3.1.1	Assets: appreciation pct and returns.
9.3.1.2	Expenses: Inflation rates.
9.3.1.3 Income: growth pct.
9.3.1.4	Income interruptions (job loss, etc.).
9.3.1.5 Uncertainty levels are used to perturb the inputs in a realistic manner.
9.3.1.5.1 Volatile means binary with a 50% chance of being 0% or 100% of the original value.
9.3.1.5.2 High means 25% chance of being 0% or 200% of the original value.
9.3.1.5.3 Medium means 50% chance of being 0% or 150% of the original value.
9.3.1.5.4 Low means 75% chance of being 0% or 125% of the original value.
9.3.1.5.5 None means no perturbation.
9.3.2	Assess robustness of plan under uncertainty.
9.3.2.1 If the plan fails in more than 20% of the simulations, it is flagged as weak. Years of consistent shortfall are highlighted as problem areas.
9.3.2.2 If the plan succeeds in more than 80% of the simulations, it is flagged as robust. 
9.3.2.3 Most probable Free Up (year of retirement) is highlighted as a key year.
9.3.2.4 Most likely values of annual total assets, total income, total expenses, and net cashflow are recorded.
9.4	Results:
9.4.1 Calculation Results Page (shown on clicking Cashflow Projection button):
9.4.1.1 Observation column from cashflow projection tables has to be summarized using GenAI techniques. Attempt has to be made to use the frequency of comments, earlier years problems need more focus, one time expenses need focus
9.4.1.2	A chart has to be shown of annual expense, annual income (stacked categories), and total annual assets after withdrawals
9.4.1.3   Free UP year is star marked in the chart
9.4.2 Stress Test results page
9.4.2.1 Page structure is same as the Calculation Resulst Page. 
9.4.2.2 Analysis of the all observations across simulations has to be done using GenAI techniques, and the comments have to be about robustness or weaknesses of the plan under uncertainty.
9.4.2.2.1 Commentary to be based on Frequency of a comment, statistical significance of shortfalls and the Free Up year
9.4.2.2	The chart can be about the most likely cashflow and assets growth, and star mark the most likely Free Up year
9.4.3 What If results page
9.4.3.1 Page structure is same as the Calculation Results Page.
9.4.3.2 Similar action and presentation as in the Calculation Results Page, but with the modified values.
9.4.3.3 Since the values are not saved to the database, the results are not persisted. Seession caching can be done to show the results on revisiting.

10.	TESTING & DATA
10.1	Test Cases:
10.1.1	All screens accessible.
10.1.2	Login/registration works.
10.1.3	CRUD, reset, and bulk import logic tested.
11.	Bulk Operations:
11.1	Bulk import/export for assets, incomes, expenses.
11.2	Downloadable CSV templates for each.
11.3	Table view for copy-paste into CSV.
12.	Block Operations:
12.1	Block delete/edit in tables (apply change to all selected rows).

 
14.	MASTER DATA: IMPORT THE BELOW DATA INTO THE MASTER DATA TABLES (comma separated values)

14.1	Asset master Table
name,category,number_level,typical_initial_value,appreciation_pct,typical_return_pct,uncertainty_level,liquid,basis
House property,physical,1,5000000,3%,2%,Medium,No,single
Commercial property,physical,1,5000000,2%,6%,Medium,No,single
Land,physical,1,5000000,3%,0%,Medium,No,single
Gold,physical,1,500000,0%,12%,Medium,No,single
Bank Deposits(Savings/ FD),financial,1,200000,0%,4%,Low,Yes,single
Govt bonds,financial,1,200000,0%,7%,Low,No,single
Debt instruments,financial,1,200000,0%,9%,High,No,single
Mutual Funds(Equity),financial,1,500000,0%,15%,High,Yes,single
Mutual Funds(Debt),financial,1,200000,0%,7%,Medium,Yes,single
Direct Equity/PMS,financial,1,500000,0%,15%,High,Yes,single
Provident/Pension Funds (EPF/ PPF/ NPS),retirals,1,1000000,0%,8%,Low,No,per_unit
Life Insurance Payout,financial,1,2500000,0%,0%,Low,No,single
Venture capital,financial,1,0,0%,20%,Volatile,No,single
House property,physical,2,10000000,3%,2%,Medium,No,single
Commercial property,physical,2,5000000,2%,6%,Medium,No,single
Land,physical,2,5000000,3%,0%,Medium,No,single
Gold,physical,2,1000000,0%,12%,Medium,No,single
Bank Deposits(Savings/ FD),financial,2,500000,0%,4%,Low,Yes,single
Govt bonds,financial,2,500000,0%,7%,Low,No,single
Debt instruments,financial,2,500000,0%,9%,High,No,single
Mutual Funds(Equity),financial,2,2500000,0%,15%,High,Yes,single
Mutual Funds(Debt),financial,2,1000000,0%,7%,Medium,Yes,single
Direct Equity/PMS,financial,2,1000000,0%,15%,High,Yes,single
Provident/Pension Funds (EPF/ PPF/ NPS),retirals,2,2500000,0%,8%,Low,No,per_unit
Life Insurance Payout,financial,2,5000000,0%,0%,Low,No,single
Venture capital,financial,2,1000000,0%,20%,Volatile,No,single
House property,physical,3,20000000,3%,2%,Medium,No,single
Commercial property,physical,3,10000000,2%,6%,Medium,No,single
Land,physical,3,5000000,3%,0%,Medium,No,single
Gold,physical,3,1000000,0%,12%,Medium,No,single
Bank Deposits(Savings/ FD),financial,3,500000,0%,4%,Low,Yes,single
Govt bonds,financial,3,500000,0%,7%,Low,No,single
Debt instruments,financial,3,500000,0%,9%,High,No,single
Mutual Funds(Equity),financial,3,10000000,0%,15%,High,Yes,single
Mutual Funds(Debt),financial,3,5000000,0%,7%,Medium,Yes,single
Direct Equity/PMS,financial,3,2500000,0%,15%,High,Yes,single
Provident/Pension Funds (EPF/ PPF/ NPS),retirals,3,2500000,0%,8%,Low,No,per_unit
Life Insurance Payout,financial,3,10000000,0%,0%,Low,No,single
Venture capital,financial,3,5000000,0%,20%,Volatile,No,single

14.2	Income Master Table
name,category,typical_amount,frequency,growth_pct,efficiency_pct,uncertainty_level,number_level
Salary ,salary,600000,annual,3%,25%,high,1
Business/Professional Income,business,0,annual,10%,25%,very high,1
Agricultural Cultivation Income,salary,0,annual,3%,0%,low,1
Rental Income (House),rent,300000,annual,0%,25%,medium,1
Rental Income (Commercial),rent,0,annual,0%,25%,high,1
SWP of  Mutual Funds (Equity),financial,0,annual,0%,22%,low,1
SWP of  Mutual Funds (Debt),financial,0,annual,0%,25%,low,1
Fixed Deposit Interest,financial,100000,annual,0%,25%,none,1
Dividends,financial,25000,annual,0%,20%,high,1
Pension,salary,0,annual,0%,25%,none,1
Salary ,salary,3000000,annual,3%,25%,high,2
Business/Professional Income,business,0,annual,10%,25%,very high,2
Agricultural Cultivation Income,salary,0,annual,3%,0%,low,2
Rental Income (House),rent,500000,annual,0%,25%,medium,2
Rental Income (Commercial),rent,0,annual,0%,25%,high,2
SWP of  Mutual Funds (Equity),financial,0,annual,0%,22%,low,2
SWP of  Mutual Funds (Debt),financial,0,annual,0%,25%,low,2
Fixed Deposit Interest,financial,200000,annual,0%,25%,none,2
Dividends,financial,50000,annual,0%,20%,high,2
Pension,salary,0,annual,0%,25%,none,2
Salary ,salary,5000000,annual,3%,25%,high,3
Business/Professional Income,business,0,annual,10%,25%,very high,3
Agricultural Cultivation Income,salary,0,annual,3%,0%,low,3
Rental Income (House),rent,500000,annual,0%,25%,medium,3
Rental Income (Commercial),rent,0,annual,0%,25%,high,3
SWP of  Mutual Funds (Equity),financial,0,annual,0%,22%,low,3
SWP of  Mutual Funds (Debt),financial,0,annual,0%,25%,low,3
Fixed Deposit Interest,financial,200000,annual,0%,25%,none,3
Dividends,financial,50000,annual,0%,20%,high,3
Pension,salary,0,annual,0%,25%,none,3

14.3	Expense Master
name,category,pertains_to,inflation_pct,frequency,typical_amount,insurance_indicator,copay_percent,uncertainty_levelnumber_level
Groceries etc.,groceries,household,6.00%,annual, 200000.00 ,No,Medium,1
Dining Out,lifestyle,household,5.00%,annual,25000.00 ,No,High,1
Rent,utilities,household,5%,annual, 100000.00 ,No,High,1
Electricity/Fuel & Light,utilities,household,3%,annual, 6000.00 ,No,Low,1
Vehicle Fuel,transport,vehicle,3%,annual,50000.00 ,No,High,1
Vehicle Maintenance,transport,vehicle,5%,annual,10000.00 ,No,Medium,1
Public Transport,transport,household,2%,annual, 2000.00 ,No,Low,1
Flights (non-work),transport,household,5%,annual,25000.00 ,No,High,1
Mobile/Internet Bills,utilities,household,3%,annual,25000.00 ,No,Low,1
Tuition Fees,education,child,8%,annual,50000.00 ,No,High,1
Coaching/Exam Prep,education,child,8%,annual,50000.00 ,No,High,1
Books & Supplies,education,child,5%,annual,10000.00 ,No,Medium,1
Sports,sports,child,5%,annual,20000.00 ,No,High,1
Toys/games etc.,sports,child,3%,annual,10000.00 ,No,High,1
Graduation,education,child,8%,one time, 2500000.00 ,No,Low,1
Settling down,lifestyle,child,0%,one time,- ,No,Low,1
Doctor Consultations,healthcare,household,4%,annual,10000.00 ,No,High,1
Medicines,healthcare,household,4%,annual,10000.00 ,No,Volatile,1
Hospitalization,healthcare,household,4%,one time, 1000000.00 ,Yes,Volatile,1
Clothing & Footwear,lifestyle,household,2.50%,annual,10000.00 ,No,Medium,1
Personal Care & Effects,lifestyle,household,8.00%,annual,10000.00 ,No,Medium,1
Entertainment/Recreation,lifestyle,household,2.00%,annual,25000.00 ,No,Medium,1
Household help,lifestyle,household,5%,annual,30000.00 ,No,Low,1
Society maintenance,housing,household,3%,annual,30000.00 ,No,Low,1
Housing loan,housing,household,0%,annual, 5000000.00 ,No,Medium,1
Property tax,housing,house,2%,annual,10000.00 ,No,Low,1
Insurance premium,lifestyle,household,4%,annual,30000.00 ,No,Low,1
Allowance,lifestyle,child,5%,annual, 1000.00 ,No,Medium,1
Allowance,lifestyle,dependent adult,5%,annual, 5000.00 ,No,Medium,1
Pet expenses,pets,pet,5%,annual,20000.00 ,No,Medium,1
Charity,lifestyle,household,5%,annual,- ,No,Low,1
Vacations,lifestyle,household,8%,annual, 100000.00 ,No,Medium,1
Groceries etc.,groceries,household,6.00%,annual, 500000.00 ,No,Medium,2
Dining Out,lifestyle,household,5.00%,annual, 100000.00 ,No,High,2
Rent,utilities,household,5%,annual, 350000.00 ,No,High,2
Electricity/Fuel & Light,utilities,household,3%,annual,12000.00 ,No,Low,2
Vehicle Fuel,transport,vehicle,3%,annual,50000.00 ,No,High,2
Vehicle Maintenance,transport,vehicle,5%,annual,15000.00 ,No,Medium,2
Public Transport,transport,household,2%,annual, 2000.00 ,No,Low,2
Flights (non-work),transport,household,5%,annual, 100000.00 ,No,High,2
Mobile/Internet Bills,utilities,household,3%,annual,50000.00 ,No,Low,2
Tuition Fees,education,child,8%,annual, 150000.00 ,No,High,2
Coaching/Exam Prep,education,child,8%,annual,50000.00 ,No,High,2
Books & Supplies,education,child,5%,annual,10000.00 ,No,Medium,2
Sports,sports,child,5%,annual,50000.00 ,No,High,2
Toys/games etc.,sports,child,3%,annual,25000.00 ,No,High,2
Graduation,education,child,8%,one time, 5000000.00 ,No,Low,2
Settling down,lifestyle,child,0%,one time,10000000.00 ,No,Low,2
Doctor Consultations,healthcare,household,4%,annual,20000.00 ,No,High,2
Medicines,healthcare,household,4%,annual,10000.00 ,No,Volatile,2
Hospitalization,healthcare,household,4%,one time, 2500000.00 ,Yes,Volatile,2
Clothing & Footwear,lifestyle,household,2.50%,annual,50000.00 ,No,Medium,2
Personal Care & Effects,lifestyle,household,8.00%,annual,25000.00 ,No,Medium,2
Entertainment/Recreation,lifestyle,household,2.00%,annual, 100000.00 ,No,Medium,2
Household help,lifestyle,household,5%,annual, 300000.00 ,No,Low,2
Society maintenance,housing,household,3%,annual, 100000.00 ,No,Low,2
Housing loan,housing,household,0%,annual, 800000.00 ,No,Medium,2
Property tax,housing,house,2%,annual,15000.00 ,No,Low,2
Insurance premium,lifestyle,household,4%,annual, 100000.00 ,No,Low,2
Allowance,lifestyle,child,5%,annual, 5000.00 ,No,Medium,2
Allowance,lifestyle,dependent adult,5%,annual,10000.00 ,No,Medium,2
Pet expenses,pets,pet,5%,annual,50000.00 ,No,Medium,2
Charity,lifestyle,household,5%,annual, 200000.00 ,No,Low,2
Vacations,lifestyle,household,8%,annual, 300000.00 ,No,Medium,2
Groceries etc.,groceries,household,6.00%,annual, 500000.00 ,No,Medium,3
Dining Out,lifestyle,household,5.00%,annual, 150000.00 ,No,High,3
Rent,utilities,household,5%,annual, 350000.00 ,No,High,3
Electricity/Fuel & Light,utilities,household,3%,annual,25000.00 ,No,Low,3
Vehicle Fuel,transport,vehicle,3%,annual,50000.00 ,No,High,3
Vehicle Maintenance,transport,vehicle,5%,annual,20000.00 ,No,Medium,3
Public Transport,transport,household,2%,annual, 2000.00 ,No,Low,3
Flights (non-work),transport,household,5%,annual, 150000.00 ,No,High,3
Mobile/Internet Bills,utilities,household,3%,annual,50000.00 ,No,Low,3
Tuition Fees,education,child,8%,annual, 200000.00 ,No,High,3
Coaching/Exam Prep,education,child,8%,annual,75000.00 ,No,High,3
Books & Supplies,education,child,5%,annual,20000.00 ,No,Medium,3
Sports,sports,child,5%,annual,50000.00 ,No,High,3
Toys/games etc.,sports,child,3%,annual,50000.00 ,No,High,3
Graduation,education,child,8%,one time,10000000.00 ,No,Low,3
Settling down,lifestyle,child,0%,one time,10000000.00 ,No,Low,3
Doctor Consultations,healthcare,household,4%,annual,30000.00 ,No,High,3
Medicines,healthcare,household,4%,annual,10000.00 ,No,Volatile,3
Hospitalization,healthcare,household,4%,one time, 5000000.00 ,Yes,Volatile,3
Clothing & Footwear,lifestyle,household,2.50%,annual, 100000.00 ,No,Medium,3
Personal Care & Effects,lifestyle,household,8.00%,annual,50000.00 ,No,Medium,3
Entertainment/Recreation,lifestyle,household,2.00%,annual, 200000.00 ,No,Medium,3
Household help,lifestyle,household,5%,annual, 300000.00 ,No,Low,3
Society maintenance,housing,household,3%,annual, 100000.00 ,No,Low,3
Housing loan,housing,household,0%,annual, 1200000.00 ,No,Medium,3
Property tax,housing,house,2%,annual,30000.00 ,No,Low,3
Insurance premium,lifestyle,household,4%,annual, 150000.00 ,No,Low,3
Allowance,lifestyle,child,5%,annual, 5000.00 ,No,Medium,3
Allowance,lifestyle,dependent adult,5%,annual,15000.00 ,No,Medium,3
Pet expenses,pets,pet,5%,annual,50000.00 ,No,Medium,3
Charity,lifestyle,household,5%,annual, 500000.00 ,No,Low,3
Vacations,lifestyle,household,8%,annual, 800000.00 ,No,Medium,3

