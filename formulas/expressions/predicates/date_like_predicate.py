# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('date_like_predicate')
class FDateLikePredicate(FBasePredicate):
    def __init__(self, attr: FBaseExpression, prefix: str, suffix: str, no_pattern: bool = False):
        super(FDateLikePredicate, self).__init__(
            operator=None,
            operands=[attr, prefix, suffix, no_pattern],
        )

    def __str__(self):
        if self.operands[-1]:
            return f'DATE_LIKE_{self.operands[0]}'
        else:
            return f'DATE_LIKE_{self.operands[0]}_{self.operands[1]}%{self.operands[2]}'
