# -*- coding: utf-8 -*-


from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import VARCHAR


@register_formula('strftime_predicate')
class FStrftimePredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression,
                 get_year: bool = False,
                 get_month: bool = False,
                 get_day: bool = False,
                 func_name: str = "STRFTIME",
                 ):
        super(FStrftimePredicate, self).__init__(
            operator=None,
            operands=[expression, get_year, get_month, get_day],
            type=VARCHAR,
        )
        self.func_name = func_name

    def __str__(self):
        return f"{self.func_name}_{''.join(map(lambda x: str(int(x)), self.operands[1:]))}_{self.operands[0]}"
