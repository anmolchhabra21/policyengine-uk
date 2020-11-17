from openfisca_core.model_api import *
from openfisca_uk.entities import *

class earnings(Variable):
    value_type = float
    entity = Person
    label = u'Gross earnings from employment'
    definition_period = YEAR

class profit(Variable):
    value_type = float
    entity = Person
    label = u'Profit from self-employment'
    definition_period = YEAR

class interest(Variable):
    value_type = float
    entity = Person
    label = u'Interest from savings'
    definition_period = YEAR

class rental_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from letting'
    definition_period = YEAR

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from non-state pensions'
    definition_period = YEAR

class state_pension(Variable):
    value_type = float
    entity = Person
    label = u'Income from the State Pension'
    definition_period = YEAR

class SSP(Variable):
    value_type = float
    entity = Person
    label = u'Statutory Sick Pay'
    definition_period = YEAR

class SMP(Variable):
    value_type = float
    entity = Person
    label = u'Statutory Maternity Pay'
    definition_period = YEAR

class SPP(Variable):
    value_type = float
    entity = Person
    label = u'Statutory Paternity Pay'
    definition_period = YEAR

class holiday_pay(Variable):
    value_type = float
    entity = Person
    label = u'Holiday pay'
    definition_period = YEAR