from policyengine_uk.model_api import *


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions"
    definition_period = YEAR
    reference = dict(
        title="Finance Act 2004 s. 188-194",
        href="https://www.legislation.gov.uk/ukpga/2004/12/section/188",
    )
    unit = GBP

    def formula_2004_07_22(person, period, parameters):
        contributions = person("pension_contributions", period)
        pension_allowance = person("pension_annual_allowance", period)
        age_limit = parameters(period).gov.hmrc.pensions.pension_contribution.age_limit
        pay = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        under_age_limit = person("age", period) < age_limit
        basic_amount = parameters(
            period
        ).gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount
        tax_relief = min_(pay, contributions) * under_age_limit
        max_pension_relief = max_(basic_amount, pension_allowance)

        return min_(
            tax_relief,
            max_pension_relief
        )
