"""
Compute itemized expense estimates from ExpenseMaster based on family composition.
Used by Tier 1 (QUICK) to replace ad-hoc frugal/lavish estimation.
"""

import math
from decimal import Decimal
from finance.models import ExpenseMaster


def compute_expenses(
    expense_level,
    family_type='solo',
    kids_count=0,
    dependent_adults_count=0,
    has_vehicle=False,
    has_pet=False,
    rented_house=False,
):
    """
    Compute itemized expense estimate from ExpenseMaster.

    Args:
        expense_level: 1, 2, or 3 (maps to number_level)
        family_type: 'solo', 'partner', 'partner_kids', 'joint'
        kids_count: number of children
        dependent_adults_count: number of dependent adults
        has_vehicle: whether household owns a vehicle
        has_pet: whether household has a pet
        rented_house: whether living in rented house

    Returns:
        dict with 'items', 'monthly_total', 'annual_total',
        'monthly_needs', 'monthly_wants', 'needs_percent', 'wants_percent'
    """
    expense_level = int(expense_level)
    kids_count = int(kids_count)
    dependent_adults_count = int(dependent_adults_count)

    master_items = ExpenseMaster.objects.filter(number_level=expense_level)

    items = []

    for master in master_items:
        pt = master.pertains_to
        quantity = 0

        if pt == 'household':
            # Special: Rent only if rented, Housing loan only if owned
            if master.name == 'Rent' and not rented_house:
                continue
            if master.name == 'Housing loan' and rented_house:
                continue
            quantity = 1

        elif pt == 'child':
            if kids_count > 0:
                quantity = kids_count
            else:
                continue

        elif pt == 'dependent_adult':
            if dependent_adults_count > 0:
                quantity = dependent_adults_count
            else:
                continue

        elif pt == 'vehicle':
            if has_vehicle:
                quantity = 1
            else:
                continue

        elif pt == 'pet':
            if has_pet:
                quantity = 1
            else:
                continue

        elif pt == 'house':
            # Property tax etc. — only if they own a house
            if not rented_house:
                quantity = 1
            else:
                continue

        else:
            # 'adult', 'others' — include by default
            quantity = 1

        annual_amount = float(master.typical_amount) * quantity
        is_one_time = master.frequency == 'one_time'

        items.append({
            'id': master.pk,
            'name': master.name,
            'category': master.category,
            'pertains_to': pt,
            'budget_type': master.budget_type,
            'annual_amount': round(annual_amount),
            'monthly_amount': round(annual_amount / 12) if not is_one_time else 0,
            'quantity': quantity,
            'is_one_time': is_one_time,
            'frequency': master.frequency,
        })

    # Compute totals (excluding one-time items)
    recurring_items = [i for i in items if not i['is_one_time']]

    annual_needs = sum(i['annual_amount'] for i in recurring_items if i['budget_type'] == 'needs')
    annual_wants = sum(i['annual_amount'] for i in recurring_items if i['budget_type'] == 'wants')
    annual_total = annual_needs + annual_wants

    monthly_needs = round(annual_needs / 12)
    monthly_wants = round(annual_wants / 12)
    monthly_raw = monthly_needs + monthly_wants

    # Round monthly total to nearest 5K (finer granularity to reflect small toggles)
    monthly_total = round(monthly_raw / 5000) * 5000
    if monthly_total == 0 and monthly_raw > 0:
        monthly_total = 5000

    total_for_pct = monthly_needs + monthly_wants
    needs_percent = round((monthly_needs / total_for_pct) * 100) if total_for_pct > 0 else 60
    wants_percent = 100 - needs_percent

    return {
        'items': items,
        'monthly_total': monthly_total,
        'annual_total': annual_total,
        'monthly_needs': monthly_needs,
        'monthly_wants': monthly_wants,
        'needs_percent': needs_percent,
        'wants_percent': wants_percent,
    }
