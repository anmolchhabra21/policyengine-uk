from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

"""
This file calculates the overall liability for Income Tax.
"""

class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = u'Non-savings, non-dividend income for Income Tax'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        COMPONENTS = [
            "taxable_employment_income",
            "taxable_pension_income",
            "taxable_social_security_income",
            "taxable_trading_income",
            "taxable_property_income",
            "taxable_miscellaneous_income"
        ]
        ALLOWANCES = [
            "personal_allowance",
            "blind_persons_allowance",
            "marriage_allowance",
            "married_couples_allowance_deduction",
            "trading_allowance",
            "property_allowance"
        ]
        amount = add(person, period, COMPONENTS)
        reductions = add(person, period, ALLOWANCES)
        final_amount = max_(0, amount - reductions)
        return final_amount

class taxed_income(Variable):
    value_type = float
    entity = Person
    label = u'Income which is taxed'
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "earned_taxable_income",
            "taxed_savings_income",
            "taxed_dividend_income"
        ]
        return add(person, period, COMPONENTS)

class earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax on earned income'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        rates = parameters(period).taxes.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.calc(person("earned_taxable_income", period))
        amount = where(scot, scot_amount, uk_amount)
        return amount

class TaxBand(Enum):
    NONE = "None"
    BASIC = "Basic"
    HIGHER = "Higher"
    ADDITIONAL = "Additional"

class pays_scottish_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Whether the individual pays Scottish Income Tax rates'
    definition_period = YEAR

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        return person.household("country", period) == countries.SCOTLAND

class tax_band(Variable):
    value_type = Enum
    possible_values = TaxBand
    default_value = TaxBand.NONE
    entity = Person
    label = u"Tax band of the individual"
    definition_period = YEAR

    def formula(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        basic = allowances + rates.uk.thresholds[0]
        higher = allowances + rates.uk.thresholds[-2]
        add = allowances + rates.uk.thresholds[-1]
        band = select([ANI >= add, ANI >= higher, ANI > basic, ANI <= basic], [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC, TaxBand.NONE])
        return band

    def formula_2017_04_06(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        basic = allowances + where(scot, rates.scotland.pre_starter_rate.thresholds[0], rates.uk.thresholds[0])
        higher = allowances + where(scot, rates.scotland.pre_starter_rate.thresholds[-2], rates.uk.thresholds[-2])
        add = allowances + where(scot, rates.scotland.pre_starter_rate.thresholds[-1], rates.uk.thresholds[-1])
        band = select([ANI >= add, ANI >= higher, ANI > basic, ANI <= basic], [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC, TaxBand.NONE])
        return band
    

    def formula_2018_04_06(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        basic = allowances + where(scot, rates.scotland.post_starter_rate.thresholds[-3], rates.uk.thresholds[-3])
        higher = allowances + where(scot, rates.scotland.post_starter_rate.thresholds[-2], rates.uk.thresholds[-2])
        add = allowances + where(scot, rates.scotland.post_starter_rate.thresholds[-1], rates.uk.thresholds[-1])
        band = select([ANI >= add, ANI >= higher, ANI > basic, ANI <= basic], [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC, TaxBand.NONE])
        return band

class basic_rate_savings_income_pre_starter(Variable):
    value_type = float
    entity = Person
    label = u'Savings income which would otherwise be taxed at the basic rate, without the starter rate'
    definition_period = YEAR

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates.uk
        savings_income_total = person("taxable_savings_interest_income", period)
        savings_allowance = person("savings_allowance", period)
        savings_income = max_(0, savings_income_total - savings_allowance)
        other_income = person("earned_taxable_income", period)
        basic_rate_amount_with_savings = clip(savings_income + other_income, rates.thresholds[0], rates.thresholds[1])
        basic_rate_amount_without_savings = clip(other_income, rates.thresholds[0], rates.thresholds[1])
        amount = basic_rate_amount_with_savings - basic_rate_amount_without_savings
        return amount

class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = u'Savings income which is tax-free under the starter rate'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12"

    def formula(person, period, parameters):
        income = person("basic_rate_savings_income_pre_starter", period)
        limit = parameters(period).tax.income_tax.rates.savings_starter_rate.allowance
        return max_(0, limit - income)

class basic_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Savings income at the basic rate'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(person, period, ["savings_allowance", "savings_starter_rate_income"])
        savings_income_less_deductions = max_(0, person("taxable_savings_interest_income", period) - savings_deductions)
        basic_rate_amount_with = clip(other_income + savings_income_less_deductions, rates.uk.thresholds[0], rates.uk.thresholds[1])
        basic_rate_amount_without = clip(other_income, rates.uk.thresholds[0], rates.uk.thresholds[1])
        basic_rate_amount = max_(0, basic_rate_amount_with - basic_rate_amount_without)
        return basic_rate_amount

class higher_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Savings income at the higher rate'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(person, period, ["savings_allowance", "savings_starter_rate_income"])
        savings_income_less_deductions = max_(0, person("taxable_savings_interest_income", period) - savings_deductions)
        higher_rate_amount_with = clip(other_income + savings_income_less_deductions, rates.uk.thresholds[1], rates.uk.thresholds[2])
        higher_rate_amount_without = clip(other_income, rates.uk.thresholds[1], rates.uk.thresholds[2])
        higher_rate_amount = max_(0, higher_rate_amount_with - higher_rate_amount_without)
        return higher_rate_amount

class add_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Savings income at the higher rate'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(person, period, ["savings_allowance", "savings_starter_rate_income"])
        savings_income_less_deductions = max_(0, person("taxable_savings_interest_income", period) - savings_deductions)
        add_rate_amount_with = clip(other_income + savings_income_less_deductions, rates.uk.thresholds[2], inf)
        add_rate_amount_without = clip(other_income, rates.uk.thresholds[2], inf)
        add_rate_amount = max_(0, add_rate_amount_with - add_rate_amount_without)
        return add_rate_amount

class taxed_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Savings income which advances the person\'s income tax schedule'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        COMPONENTS = ["basic_rate_savings_income", "higher_rate_savings_income", "add_rate_savings_income"]
        amount = add(person, period, COMPONENTS)
        return amount

class taxed_dividend_income(Variable):
    value_type = float
    entity = Person
    label = u'Dividend income which is taxed'
    definition_period = YEAR

    def formula(person, period, parameters):
        return max_(0, person("taxable_dividend_income", period) - person("dividend_allowance", period))

class savings_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax on savings income'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        basic_rate_amount = person("basic_rate_savings_income", period)
        higher_rate_amount = person("higher_rate_savings_income", period)
        add_rate_amount = person("add_rate_savings_income", period)
        charge = rates.uk.rates[0] * basic_rate_amount + rates.uk.rates[1] * higher_rate_amount + rates.uk.rates[2] * add_rate_amount
        return charge

class dividend_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Income tax on dividend income'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period) + person("taxed_savings_income", period)
        taxable_dividends = person("taxed_dividend_income", period)
        tax_with_dividends = rates.dividends.calc(other_income + taxable_dividends)
        tax_without_dividends = rates.dividends.calc(other_income)
        dividend_tax = tax_with_dividends - tax_without_dividends
        return dividend_tax

class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = u'Income Tax before any tax charges'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"

    def formula(person, period, parameters):
        COMPONENTS = [
            "earned_income_tax",
            "savings_income_tax",
            "dividend_income_tax"
        ]
        total = add(person, period, COMPONENTS)
        return total