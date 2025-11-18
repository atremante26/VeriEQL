# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import (DATE, IntVal)
from operator import (add, sub)


@register_formula('date_shift_predicate')
class FDateShiftPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, sign, num, unit, out_date=None):
        sign = add if sign else sub
        num = IntVal(str(num))
        super(FDateShiftPredicate, self).__init__(
            operator=None,
            operands=[expression, sign, num, unit],
            type=DATE,
        )
        self.out_date = out_date

    def __str__(self):
        return f'DATE_SHIFT_{self.operands[0]}_{"+" if self.operands[1] else "-"}_{self.operands[2]}_{self.operands[3]}'
