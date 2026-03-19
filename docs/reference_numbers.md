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
name,category,pertains_to,inflation_pct,frequency,typical_amount,insurance_indicator,copay_percent,uncertainty_level,number_level
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