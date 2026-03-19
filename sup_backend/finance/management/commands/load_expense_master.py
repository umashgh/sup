"""
Management command to load ExpenseMaster data from reference_numbers.md.
Idempotent: deletes all existing rows then bulk-creates from CSV.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from finance.models import ExpenseMaster


# Budget type classification for each expense name
BUDGET_TYPE_MAP = {
    # Needs (survival)
    'Groceries etc.': 'needs',
    'Rent': 'needs',
    'Electricity/Fuel & Light': 'needs',
    'Public Transport': 'needs',
    'Mobile/Internet Bills': 'needs',
    'Tuition Fees': 'needs',
    'Coaching/Exam Prep': 'needs',
    'Books & Supplies': 'needs',
    'Doctor Consultations': 'needs',
    'Medicines': 'needs',
    'Hospitalization': 'needs',
    'Society maintenance': 'needs',
    'Housing loan': 'needs',
    'Property tax': 'needs',
    'Insurance premium': 'needs',
    'Graduation': 'needs',
    # Wants (lifestyle)
    'Dining Out': 'wants',
    'Vehicle Fuel': 'wants',
    'Vehicle Maintenance': 'wants',
    'Flights (non-work)': 'wants',
    'Sports': 'wants',
    'Toys/games etc.': 'wants',
    'Clothing & Footwear': 'wants',
    'Personal Care & Effects': 'wants',
    'Entertainment/Recreation': 'wants',
    'Household help': 'wants',
    'Allowance': 'wants',
    'Pet expenses': 'wants',
    'Charity': 'wants',
    'Vacations': 'wants',
    'Settling down': 'wants',
}

# pertains_to mapping from CSV values to model choices
PERTAINS_TO_MAP = {
    'household': 'household',
    'vehicle': 'vehicle',
    'child': 'child',
    'house': 'house',
    'pet': 'pet',
    'dependent adult': 'dependent_adult',
}

# Raw CSV data from docs/reference_numbers.md section 14.3
# Format: name,category,pertains_to,inflation_pct,frequency,typical_amount,insurance_indicator,copay_percent,uncertainty_level,number_level
RAW_DATA = """Groceries etc.,groceries,household,6.00%,annual,200000,No,0,Medium,1
Dining Out,lifestyle,household,5.00%,annual,25000,No,0,High,1
Rent,utilities,household,5%,annual,100000,No,0,High,1
Electricity/Fuel & Light,utilities,household,3%,annual,6000,No,0,Low,1
Vehicle Fuel,transport,vehicle,3%,annual,50000,No,0,High,1
Vehicle Maintenance,transport,vehicle,5%,annual,10000,No,0,Medium,1
Public Transport,transport,household,2%,annual,2000,No,0,Low,1
Flights (non-work),transport,household,5%,annual,25000,No,0,High,1
Mobile/Internet Bills,utilities,household,3%,annual,25000,No,0,Low,1
Tuition Fees,education,child,8%,annual,50000,No,0,High,1
Coaching/Exam Prep,education,child,8%,annual,50000,No,0,High,1
Books & Supplies,education,child,5%,annual,10000,No,0,Medium,1
Sports,sports,child,5%,annual,20000,No,0,High,1
Toys/games etc.,sports,child,3%,annual,10000,No,0,High,1
Graduation,education,child,8%,one time,2500000,No,0,Low,1
Settling down,lifestyle,child,0%,one time,0,No,0,Low,1
Doctor Consultations,healthcare,household,4%,annual,10000,No,0,High,1
Medicines,healthcare,household,4%,annual,10000,No,0,Volatile,1
Hospitalization,healthcare,household,4%,one time,1000000,Yes,0,Volatile,1
Clothing & Footwear,lifestyle,household,2.50%,annual,10000,No,0,Medium,1
Personal Care & Effects,lifestyle,household,8.00%,annual,10000,No,0,Medium,1
Entertainment/Recreation,lifestyle,household,2.00%,annual,25000,No,0,Medium,1
Household help,lifestyle,household,5%,annual,30000,No,0,Low,1
Society maintenance,housing,household,3%,annual,30000,No,0,Low,1
Housing loan,housing,household,0%,annual,5000000,No,0,Medium,1
Property tax,housing,house,2%,annual,10000,No,0,Low,1
Insurance premium,lifestyle,household,4%,annual,30000,No,0,Low,1
Allowance,lifestyle,child,5%,annual,1000,No,0,Medium,1
Allowance,lifestyle,dependent adult,5%,annual,5000,No,0,Medium,1
Pet expenses,pets,pet,5%,annual,20000,No,0,Medium,1
Charity,lifestyle,household,5%,annual,0,No,0,Low,1
Vacations,lifestyle,household,8%,annual,100000,No,0,Medium,1
Groceries etc.,groceries,household,6.00%,annual,500000,No,0,Medium,2
Dining Out,lifestyle,household,5.00%,annual,100000,No,0,High,2
Rent,utilities,household,5%,annual,350000,No,0,High,2
Electricity/Fuel & Light,utilities,household,3%,annual,12000,No,0,Low,2
Vehicle Fuel,transport,vehicle,3%,annual,50000,No,0,High,2
Vehicle Maintenance,transport,vehicle,5%,annual,15000,No,0,Medium,2
Public Transport,transport,household,2%,annual,2000,No,0,Low,2
Flights (non-work),transport,household,5%,annual,100000,No,0,High,2
Mobile/Internet Bills,utilities,household,3%,annual,50000,No,0,Low,2
Tuition Fees,education,child,8%,annual,150000,No,0,High,2
Coaching/Exam Prep,education,child,8%,annual,50000,No,0,High,2
Books & Supplies,education,child,5%,annual,10000,No,0,Medium,2
Sports,sports,child,5%,annual,50000,No,0,High,2
Toys/games etc.,sports,child,3%,annual,25000,No,0,High,2
Graduation,education,child,8%,one time,5000000,No,0,Low,2
Settling down,lifestyle,child,0%,one time,10000000,No,0,Low,2
Doctor Consultations,healthcare,household,4%,annual,20000,No,0,High,2
Medicines,healthcare,household,4%,annual,10000,No,0,Volatile,2
Hospitalization,healthcare,household,4%,one time,2500000,Yes,0,Volatile,2
Clothing & Footwear,lifestyle,household,2.50%,annual,50000,No,0,Medium,2
Personal Care & Effects,lifestyle,household,8.00%,annual,25000,No,0,Medium,2
Entertainment/Recreation,lifestyle,household,2.00%,annual,100000,No,0,Medium,2
Household help,lifestyle,household,5%,annual,300000,No,0,Low,2
Society maintenance,housing,household,3%,annual,100000,No,0,Low,2
Housing loan,housing,household,0%,annual,800000,No,0,Medium,2
Property tax,housing,house,2%,annual,15000,No,0,Low,2
Insurance premium,lifestyle,household,4%,annual,100000,No,0,Low,2
Allowance,lifestyle,child,5%,annual,5000,No,0,Medium,2
Allowance,lifestyle,dependent adult,5%,annual,10000,No,0,Medium,2
Pet expenses,pets,pet,5%,annual,50000,No,0,Medium,2
Charity,lifestyle,household,5%,annual,200000,No,0,Low,2
Vacations,lifestyle,household,8%,annual,300000,No,0,Medium,2
Groceries etc.,groceries,household,6.00%,annual,500000,No,0,Medium,3
Dining Out,lifestyle,household,5.00%,annual,150000,No,0,High,3
Rent,utilities,household,5%,annual,350000,No,0,High,3
Electricity/Fuel & Light,utilities,household,3%,annual,25000,No,0,Low,3
Vehicle Fuel,transport,vehicle,3%,annual,50000,No,0,High,3
Vehicle Maintenance,transport,vehicle,5%,annual,20000,No,0,Medium,3
Public Transport,transport,household,2%,annual,2000,No,0,Low,3
Flights (non-work),transport,household,5%,annual,150000,No,0,High,3
Mobile/Internet Bills,utilities,household,3%,annual,50000,No,0,Low,3
Tuition Fees,education,child,8%,annual,200000,No,0,High,3
Coaching/Exam Prep,education,child,8%,annual,75000,No,0,High,3
Books & Supplies,education,child,5%,annual,20000,No,0,Medium,3
Sports,sports,child,5%,annual,50000,No,0,High,3
Toys/games etc.,sports,child,3%,annual,50000,No,0,High,3
Graduation,education,child,8%,one time,10000000,No,0,Low,3
Settling down,lifestyle,child,0%,one time,10000000,No,0,Low,3
Doctor Consultations,healthcare,household,4%,annual,30000,No,0,High,3
Medicines,healthcare,household,4%,annual,10000,No,0,Volatile,3
Hospitalization,healthcare,household,4%,one time,5000000,Yes,0,Volatile,3
Clothing & Footwear,lifestyle,household,2.50%,annual,100000,No,0,Medium,3
Personal Care & Effects,lifestyle,household,8.00%,annual,50000,No,0,Medium,3
Entertainment/Recreation,lifestyle,household,2.00%,annual,200000,No,0,Medium,3
Household help,lifestyle,household,5%,annual,300000,No,0,Low,3
Society maintenance,housing,household,3%,annual,100000,No,0,Low,3
Housing loan,housing,household,0%,annual,1200000,No,0,Medium,3
Property tax,housing,house,2%,annual,30000,No,0,Low,3
Insurance premium,lifestyle,household,4%,annual,150000,No,0,Low,3
Allowance,lifestyle,child,5%,annual,5000,No,0,Medium,3
Allowance,lifestyle,dependent adult,5%,annual,15000,No,0,Medium,3
Pet expenses,pets,pet,5%,annual,50000,No,0,Medium,3
Charity,lifestyle,household,5%,annual,500000,No,0,Low,3
Vacations,lifestyle,household,8%,annual,800000,No,0,Medium,3"""


def parse_pct(s):
    """Convert '6.00%' or '6%' to Decimal."""
    s = s.strip().replace('%', '')
    return Decimal(s) if s else Decimal('0')


def parse_amount(s):
    """Convert amount string to Decimal, handling '-' as 0."""
    s = s.strip().replace(',', '')
    if not s or s == '-':
        return Decimal('0')
    return Decimal(s)


class Command(BaseCommand):
    help = 'Load ExpenseMaster data from reference CSV. Idempotent.'

    def handle(self, *args, **options):
        rows = []
        for line in RAW_DATA.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 10:
                self.stderr.write(f'Skipping malformed line: {line}')
                continue

            name = parts[0]
            category = parts[1]
            pertains_to_raw = parts[2]
            inflation_pct = parse_pct(parts[3])
            frequency = parts[4].strip()
            typical_amount = parse_amount(parts[5])
            insurance_indicator = parts[6].strip().lower() == 'yes'
            copay_percent = parse_amount(parts[7])
            uncertainty_level = parts[8].strip().capitalize()
            number_level = int(parts[9])

            # Map pertains_to
            pertains_to = PERTAINS_TO_MAP.get(pertains_to_raw, 'others')

            # Map budget_type
            budget_type = BUDGET_TYPE_MAP.get(name, 'wants')

            # Normalize uncertainty_level to lowercase
            uncertainty_level = uncertainty_level.lower()

            # Normalize frequency
            if frequency == 'one time':
                frequency = 'one_time'

            rows.append(ExpenseMaster(
                name=name,
                category=category,
                budget_type=budget_type,
                number_level=number_level,
                pertains_to=pertains_to,
                typical_amount=typical_amount,
                frequency=frequency,
                inflation_pct=inflation_pct,
                insurance_indicator=insurance_indicator,
                copay_percent=copay_percent,
                uncertainty_level=uncertainty_level,
            ))

        # Idempotent: clear and reload
        deleted_count, _ = ExpenseMaster.objects.all().delete()
        if deleted_count:
            self.stdout.write(f'Deleted {deleted_count} existing ExpenseMaster rows.')

        ExpenseMaster.objects.bulk_create(rows)
        self.stdout.write(self.style.SUCCESS(
            f'Loaded {len(rows)} ExpenseMaster rows '
            f'({len(rows) // 3} items x 3 levels).'
        ))

        # Validation: check each level has same count
        for level in [1, 2, 3]:
            count = ExpenseMaster.objects.filter(number_level=level).count()
            self.stdout.write(f'  Level {level}: {count} items')
