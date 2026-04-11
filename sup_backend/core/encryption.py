"""
Passphrase-based encryption for user data.

Design:
  - Key derived from passphrase via PBKDF2-SHA256 (480k iterations), never stored.
  - All user model data serialised to JSON, encrypted with Fernet (AES-128-CBC + HMAC).
  - Original DB fields are cleared after encryption; restored on login with correct passphrase.
  - A short verification token (Fernet-encrypted b'SALARYFREE_VERIFIED') lets us check the
    passphrase without storing it.
  - The derived Fernet key is stored in the Django session for the duration of the session so
    data can be re-encrypted on logout.
"""

import os
import json
import base64
from decimal import Decimal

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_VERIFY_PLAINTEXT = b'SALARYFREE_VERIFIED'


# ── Key derivation ────────────────────────────────────────────────────────────

def derive_key(passphrase: str, salt_hex: str) -> bytes:
    """Return a url-safe base64-encoded 32-byte Fernet key derived from *passphrase*."""
    salt = bytes.fromhex(salt_hex)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480_000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode('utf-8')))


# ── Passphrase verification ───────────────────────────────────────────────────

def verify_passphrase(user_encryption, passphrase: str) -> bool:
    try:
        key = derive_key(passphrase, user_encryption.kdf_salt)
        token = Fernet(key).decrypt(user_encryption.verification_token.encode('utf-8'))
        return token == _VERIFY_PLAINTEXT
    except (InvalidToken, Exception):
        return False


# ── Serialisation ─────────────────────────────────────────────────────────────

def _d(value):
    """Convert Decimal / None to str / None for JSON round-trip."""
    return str(value) if value is not None else None


def serialize_user_data(user) -> dict:
    """Collect every sensitive model record for *user* into a plain dict."""
    from core.models import ScenarioProfile, UserRatePreferences
    from finance.models import FamilyProfile, FamilyMember, Asset, Income, Expense

    data: dict = {}

    # ScenarioProfile
    try:
        sp = ScenarioProfile.objects.get(user=user)
        data['scenario_profile'] = {
            'scenario_type': sp.scenario_type,
            'current_age': sp.current_age,
            'retirement_age': sp.retirement_age,
            'life_expectancy': sp.life_expectancy,
            'pension_monthly': _d(sp.pension_monthly),
            'pension_start_age': sp.pension_start_age,
            'gratuity_lumpsum': _d(sp.gratuity_lumpsum),
            'current_monthly_salary': _d(sp.current_monthly_salary),
            'parttime_monthly_income': _d(sp.parttime_monthly_income),
            'parttime_start_month': sp.parttime_start_month,
            'full_fire_target_month': sp.full_fire_target_month,
            'severance_lumpsum': _d(sp.severance_lumpsum),
            'severance_month_count': sp.severance_month_count,
            'income_restart_month': sp.income_restart_month,
            'restart_monthly_income': _d(sp.restart_monthly_income),
            'venture_bootstrapped': sp.venture_bootstrapped,
            'bootstrap_capital': _d(sp.bootstrap_capital),
            'founder_salary_start_month': sp.founder_salary_start_month,
        }
    except ScenarioProfile.DoesNotExist:
        data['scenario_profile'] = None

    # FamilyProfile
    try:
        fp = FamilyProfile.objects.get(user=user)
        data['family_profile'] = {
            'modelling_start_year': fp.modelling_start_year,
            'modelling_end_year': fp.modelling_end_year,
            'bank_rate': _d(fp.bank_rate),
            'wealth_level': fp.wealth_level,
            'income_level': fp.income_level,
            'expense_level': fp.expense_level,
            'rented_house': fp.rented_house,
            'financial_investment_areas': fp.financial_investment_areas,
            'physical_investment_areas': fp.physical_investment_areas,
            'num_houses': fp.num_houses,
            'num_vehicles': fp.num_vehicles,
            'has_pet': fp.has_pet,
            'emergency_fund_months': fp.emergency_fund_months,
            'needs_percent': fp.needs_percent,
            'wants_percent': fp.wants_percent,
            'savings_percent': fp.savings_percent,
            'has_private_health_insurance': fp.has_private_health_insurance,
            'pause_retirals': fp.pause_retirals,
            'current_tier': fp.current_tier,
        }
    except FamilyProfile.DoesNotExist:
        data['family_profile'] = None

    # FamilyMembers
    data['family_members'] = [
        {
            'member_type': m.member_type,
            'name': m.name,
            'age': m.age,
            'retirement_age': m.retirement_age,
            'has_pf': m.has_pf,
            'health_insurance': m.health_insurance,
            'allowance': _d(m.allowance),
            'age_of_graduation_start': m.age_of_graduation_start,
            'age_of_expenses_end': m.age_of_expenses_end,
        }
        for m in FamilyMember.objects.filter(user=user)
    ]

    # Assets — carry original pk so incomes can reference them
    asset_list = []
    for a in Asset.objects.filter(user=user):
        asset_list.append({
            '_orig_id': a.pk,
            'name': a.name,
            'category': a.category,
            'start_year': a.start_year,
            'end_year': a.end_year,
            'initial_value': _d(a.initial_value),
            'appreciation_pct': _d(a.appreciation_pct),
            'return_pct': _d(a.return_pct),
            'swp_possible': a.swp_possible,
            'uncertainty_level': a.uncertainty_level,
            'liquid': a.liquid,
            'is_business_pledged': a.is_business_pledged,
        })
    data['assets'] = asset_list

    # Incomes — reference asset by original pk
    data['incomes'] = [
        {
            'name': inc.name,
            'category': inc.category,
            'start_year': inc.start_year,
            'end_year': inc.end_year,
            'typical_amount': _d(inc.typical_amount),
            'frequency': inc.frequency,
            'growth_pct': _d(inc.growth_pct),
            'efficiency_pct': _d(inc.efficiency_pct),
            'uncertainty_level': inc.uncertainty_level,
            'linked_asset_orig_id': inc.linked_asset_id,
            'withdrawal_pct': _d(inc.withdrawal_pct),
        }
        for inc in Income.objects.filter(user=user)
    ]

    # Expenses
    data['expenses'] = [
        {
            'name': exp.name,
            'category': exp.category,
            'budget_type': exp.budget_type,
            'pertains_to': exp.pertains_to,
            'start_year': exp.start_year,
            'end_year': exp.end_year,
            'typical_amount': _d(exp.typical_amount),
            'frequency': exp.frequency,
            'inflation_pct': _d(exp.inflation_pct),
            'insurance_indicator': exp.insurance_indicator,
            'copay_percent': _d(exp.copay_percent),
            'uncertainty_level': exp.uncertainty_level,
        }
        for exp in Expense.objects.filter(user=user)
    ]

    # UserRatePreferences
    try:
        rp = UserRatePreferences.objects.get(user=user)
        data['rate_preferences'] = {
            'liquid_return_pct': _d(rp.liquid_return_pct),
            'semi_liquid_return_pct': _d(rp.semi_liquid_return_pct),
            'growth_return_pct': _d(rp.growth_return_pct),
            'property_appreciation_pct': _d(rp.property_appreciation_pct),
            'property_rental_yield_pct': _d(rp.property_rental_yield_pct),
            'needs_inflation_pct': _d(rp.needs_inflation_pct),
            'wants_inflation_pct': _d(rp.wants_inflation_pct),
            'passive_growth_pct': _d(rp.passive_growth_pct),
            'swr_rate_pct': _d(rp.swr_rate_pct),
        }
    except UserRatePreferences.DoesNotExist:
        data['rate_preferences'] = None

    return data


# ── Clearing / Restoration ────────────────────────────────────────────────────

def clear_user_data(user):
    """Erase all sensitive fields / records. Called after encryption is set up."""
    from core.models import ScenarioProfile, UserRatePreferences
    from finance.models import FamilyProfile, FamilyMember, Asset, Income, Expense

    FamilyMember.objects.filter(user=user).delete()
    Asset.objects.filter(user=user).delete()
    Income.objects.filter(user=user).delete()
    Expense.objects.filter(user=user).delete()
    UserRatePreferences.objects.filter(user=user).delete()

    try:
        sp = ScenarioProfile.objects.get(user=user)
        for f in [
            'current_age', 'retirement_age', 'life_expectancy',
            'pension_monthly', 'pension_start_age', 'gratuity_lumpsum',
            'current_monthly_salary', 'parttime_monthly_income',
            'parttime_start_month', 'full_fire_target_month',
            'severance_lumpsum', 'severance_month_count',
            'income_restart_month', 'restart_monthly_income',
            'bootstrap_capital', 'founder_salary_start_month',
        ]:
            setattr(sp, f, None)
        sp.venture_bootstrapped = False
        sp.save()
    except ScenarioProfile.DoesNotExist:
        pass

    try:
        fp = FamilyProfile.objects.get(user=user)
        fp.wealth_level = 1
        fp.income_level = 1
        fp.expense_level = 1
        fp.rented_house = False
        fp.financial_investment_areas = []
        fp.physical_investment_areas = []
        fp.num_houses = 1
        fp.num_vehicles = 1
        fp.has_pet = False
        fp.emergency_fund_months = 6
        fp.needs_percent = 50
        fp.wants_percent = 30
        fp.savings_percent = 20
        fp.has_private_health_insurance = False
        fp.pause_retirals = False
        # Keep current_tier so _get_smart_redirect_for_user still works
        fp.save()
    except FamilyProfile.DoesNotExist:
        pass


def restore_user_data(user, data: dict):
    """Recreate all model records from a previously serialised dict."""
    from core.models import ScenarioProfile, UserRatePreferences
    from finance.models import FamilyProfile, FamilyMember, Asset, Income, Expense

    # ScenarioProfile
    if data.get('scenario_profile'):
        sp_d = data['scenario_profile']
        sp, _ = ScenarioProfile.objects.get_or_create(user=user)
        sp.scenario_type = sp_d.get('scenario_type', sp.scenario_type)
        sp.current_age = sp_d.get('current_age')
        sp.retirement_age = sp_d.get('retirement_age')
        sp.life_expectancy = sp_d.get('life_expectancy')
        sp.pension_monthly = Decimal(sp_d['pension_monthly']) if sp_d.get('pension_monthly') else None
        sp.pension_start_age = sp_d.get('pension_start_age')
        sp.gratuity_lumpsum = Decimal(sp_d['gratuity_lumpsum']) if sp_d.get('gratuity_lumpsum') else None
        sp.current_monthly_salary = Decimal(sp_d['current_monthly_salary']) if sp_d.get('current_monthly_salary') else None
        sp.parttime_monthly_income = Decimal(sp_d['parttime_monthly_income']) if sp_d.get('parttime_monthly_income') else None
        sp.parttime_start_month = sp_d.get('parttime_start_month')
        sp.full_fire_target_month = sp_d.get('full_fire_target_month')
        sp.severance_lumpsum = Decimal(sp_d['severance_lumpsum']) if sp_d.get('severance_lumpsum') else None
        sp.severance_month_count = sp_d.get('severance_month_count')
        sp.income_restart_month = sp_d.get('income_restart_month')
        sp.restart_monthly_income = Decimal(sp_d['restart_monthly_income']) if sp_d.get('restart_monthly_income') else None
        sp.venture_bootstrapped = sp_d.get('venture_bootstrapped', False)
        sp.bootstrap_capital = Decimal(sp_d['bootstrap_capital']) if sp_d.get('bootstrap_capital') else None
        sp.founder_salary_start_month = sp_d.get('founder_salary_start_month')
        sp.save()

    # FamilyProfile
    if data.get('family_profile'):
        fp_d = data['family_profile']
        fp, _ = FamilyProfile.objects.get_or_create(user=user)
        fp.modelling_start_year = fp_d.get('modelling_start_year', fp.modelling_start_year)
        fp.modelling_end_year = fp_d.get('modelling_end_year', fp.modelling_end_year)
        fp.bank_rate = Decimal(fp_d['bank_rate']) if fp_d.get('bank_rate') else fp.bank_rate
        fp.wealth_level = fp_d.get('wealth_level', 1)
        fp.income_level = fp_d.get('income_level', 1)
        fp.expense_level = fp_d.get('expense_level', 1)
        fp.rented_house = fp_d.get('rented_house', False)
        fp.financial_investment_areas = fp_d.get('financial_investment_areas', [])
        fp.physical_investment_areas = fp_d.get('physical_investment_areas', [])
        fp.num_houses = fp_d.get('num_houses', 1)
        fp.num_vehicles = fp_d.get('num_vehicles', 1)
        fp.has_pet = fp_d.get('has_pet', False)
        fp.emergency_fund_months = fp_d.get('emergency_fund_months', 6)
        fp.needs_percent = fp_d.get('needs_percent', 50)
        fp.wants_percent = fp_d.get('wants_percent', 30)
        fp.savings_percent = fp_d.get('savings_percent', 20)
        fp.has_private_health_insurance = fp_d.get('has_private_health_insurance', False)
        fp.pause_retirals = fp_d.get('pause_retirals', False)
        fp.current_tier = fp_d.get('current_tier', fp.current_tier)
        fp.save()
        # Re-link to ScenarioProfile
        try:
            fp.scenario = ScenarioProfile.objects.get(user=user)
            fp.save(update_fields=['scenario'])
        except ScenarioProfile.DoesNotExist:
            pass

    # FamilyMembers
    FamilyMember.objects.filter(user=user).delete()
    for m in data.get('family_members', []):
        FamilyMember.objects.create(
            user=user,
            member_type=m['member_type'],
            name=m['name'],
            age=m['age'],
            retirement_age=m.get('retirement_age'),
            has_pf=m.get('has_pf', False),
            health_insurance=m.get('health_insurance', False),
            allowance=Decimal(m['allowance']) if m.get('allowance') else Decimal('0'),
            age_of_graduation_start=m.get('age_of_graduation_start', 18),
            age_of_expenses_end=m.get('age_of_expenses_end', 24),
        )

    # Assets — build orig_id → new Asset map for income FK repair
    Asset.objects.filter(user=user).delete()
    orig_to_new: dict = {}
    for a in data.get('assets', []):
        orig_id = a.get('_orig_id')
        new_a = Asset.objects.create(
            user=user,
            name=a['name'],
            category=a['category'],
            start_year=a['start_year'],
            end_year=a['end_year'],
            initial_value=Decimal(a['initial_value']),
            appreciation_pct=Decimal(a['appreciation_pct']),
            return_pct=Decimal(a['return_pct']),
            swp_possible=a.get('swp_possible', False),
            uncertainty_level=a.get('uncertainty_level', 'none'),
            liquid=a.get('liquid', False),
            is_business_pledged=a.get('is_business_pledged', False),
        )
        if orig_id:
            orig_to_new[orig_id] = new_a

    # Incomes
    Income.objects.filter(user=user).delete()
    for inc in data.get('incomes', []):
        linked = orig_to_new.get(inc.get('linked_asset_orig_id'))
        Income.objects.create(
            user=user,
            name=inc['name'],
            category=inc['category'],
            start_year=inc['start_year'],
            end_year=inc['end_year'],
            typical_amount=Decimal(inc['typical_amount']),
            frequency=inc.get('frequency', 'annual'),
            growth_pct=Decimal(inc['growth_pct']),
            efficiency_pct=Decimal(inc['efficiency_pct']),
            uncertainty_level=inc.get('uncertainty_level', 'none'),
            linked_asset=linked,
            withdrawal_pct=Decimal(inc['withdrawal_pct']),
        )

    # Expenses
    Expense.objects.filter(user=user).delete()
    for exp in data.get('expenses', []):
        Expense.objects.create(
            user=user,
            name=exp['name'],
            category=exp['category'],
            budget_type=exp.get('budget_type', 'needs'),
            pertains_to=exp.get('pertains_to', 'household'),
            start_year=exp['start_year'],
            end_year=exp['end_year'],
            typical_amount=Decimal(exp['typical_amount']),
            frequency=exp.get('frequency', 'annual'),
            inflation_pct=Decimal(exp['inflation_pct']),
            insurance_indicator=exp.get('insurance_indicator', False),
            copay_percent=Decimal(exp['copay_percent']),
            uncertainty_level=exp.get('uncertainty_level', 'none'),
        )

    # UserRatePreferences
    if data.get('rate_preferences'):
        rp_d = data['rate_preferences']
        from core.models import UserRatePreferences
        rp, _ = UserRatePreferences.objects.get_or_create(user=user)
        rp.liquid_return_pct = Decimal(rp_d['liquid_return_pct'])
        rp.semi_liquid_return_pct = Decimal(rp_d['semi_liquid_return_pct'])
        rp.growth_return_pct = Decimal(rp_d['growth_return_pct'])
        rp.property_appreciation_pct = Decimal(rp_d['property_appreciation_pct'])
        rp.property_rental_yield_pct = Decimal(rp_d['property_rental_yield_pct'])
        rp.needs_inflation_pct = Decimal(rp_d['needs_inflation_pct'])
        rp.wants_inflation_pct = Decimal(rp_d['wants_inflation_pct'])
        rp.passive_growth_pct = Decimal(rp_d['passive_growth_pct'])
        rp.swr_rate_pct = Decimal(rp_d['swr_rate_pct'])
        rp.save()


# ── High-level operations ─────────────────────────────────────────────────────

def setup_encryption(user, passphrase: str, hint: str = '') -> 'UserEncryption':
    """
    Encrypt all user data with *passphrase*, clear original fields, create UserEncryption.
    Returns the created/updated UserEncryption instance.
    """
    from core.models import UserEncryption

    salt_hex = os.urandom(32).hex()
    key = derive_key(passphrase, salt_hex)
    f = Fernet(key)

    verification_token = f.encrypt(_VERIFY_PLAINTEXT).decode('utf-8')
    payload = f.encrypt(json.dumps(serialize_user_data(user)).encode('utf-8')).decode('utf-8')

    ue, _ = UserEncryption.objects.update_or_create(
        user=user,
        defaults={
            'kdf_salt': salt_hex,
            'passphrase_hint': hint,
            'verification_token': verification_token,
            'encrypted_payload': payload,
        },
    )
    clear_user_data(user)
    return ue


def unlock_and_restore(user, passphrase: str) -> bool:
    """
    Verify *passphrase* and restore user data into DB fields.
    Returns True on success, False on wrong passphrase or missing record.
    """
    from core.models import UserEncryption
    try:
        ue = UserEncryption.objects.get(user=user)
    except UserEncryption.DoesNotExist:
        return True  # Not encrypted — nothing to do

    if not verify_passphrase(ue, passphrase):
        return False

    key = derive_key(passphrase, ue.kdf_salt)
    payload_json = Fernet(key).decrypt(ue.encrypted_payload.encode('utf-8')).decode('utf-8')
    restore_user_data(user, json.loads(payload_json))
    return True


def reencrypt_user_data(user, key_b64: str):
    """
    Re-encrypt user data using *key_b64* (derived key already in session).
    Called on logout to put data back into encrypted form.
    """
    from core.models import UserEncryption
    try:
        ue = UserEncryption.objects.get(user=user)
    except UserEncryption.DoesNotExist:
        return

    f = Fernet(key_b64.encode('utf-8') if isinstance(key_b64, str) else key_b64)
    payload = f.encrypt(json.dumps(serialize_user_data(user)).encode('utf-8')).decode('utf-8')
    ue.encrypted_payload = payload
    ue.save(update_fields=['encrypted_payload', 'updated_at'])
    clear_user_data(user)


def remove_encryption(user, passphrase: str) -> bool:
    """
    Verify passphrase, restore data, delete UserEncryption record.
    Returns True on success, False on wrong passphrase.
    """
    from core.models import UserEncryption
    try:
        ue = UserEncryption.objects.get(user=user)
    except UserEncryption.DoesNotExist:
        return True

    if not verify_passphrase(ue, passphrase):
        return False

    key = derive_key(passphrase, ue.kdf_salt)
    payload_json = Fernet(key).decrypt(ue.encrypted_payload.encode('utf-8')).decode('utf-8')
    restore_user_data(user, json.loads(payload_json))
    ue.delete()
    return True
