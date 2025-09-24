# -*- coding:utf-8 -*-

from .abs_predicate import FAbsPredicate
from .any_value_predicate import FAnyValuePredicate
from .base_predicate import FBasePredicate
from .case_predicate import FCasePredicate
from .coalesce_predicate import FCoalescePredicate
from .exists_predicate import FExistsPredicate
from .first_value_predicate import FFirstValuePredicate
from .if_predicate import FIfPredicate
from .in_predicate import FInPredicate
from .is_false_predicate import FIsFalsePredicate
from .is_not_false_predicate import FIsNotFalsePredicate
from .is_not_null_predicate import FIsNotNullPredicate
from .is_not_true_predicate import FIsNotTruePredicate
from .is_null_or_hold_predicate import FIsNullOrHoldPredicate
from .is_null_predicate import FIsNullPredicate
from .is_true_predicate import FIsTruePredicate
from .last_value_predicate import FLastValuePredicate
from .mod_predicate import FModPredicate
from .not_in_condition import FNotInPredicate
from .nullif_predicate import FNullIfPredicate
from .power_predicate import FPowerPredicate
from .to_real_predicate import FToRealPredicate
from .substr_predicate import FSubstrPredicate
from .like_predicate import FLikePredicate
from .date_like_predicate import FDateLikePredicate
from .to_date_predicate import FToDatePredicate
from .strftime_predicate import FStrftimePredicate
from .to_juliandate_predicate import FToJulianDatePredicate

PredicateType = FBasePredicate | \
                FInPredicate | FNotInPredicate | FIsNullPredicate | FIsNotNullPredicate | FCasePredicate | \
                FCoalescePredicate | FIfPredicate | FAbsPredicate | FPowerPredicate | FExistsPredicate | \
                FAnyValuePredicate | FFirstValuePredicate | FLastValuePredicate | FModPredicate | \
                FIsTruePredicate | FIsFalsePredicate | FIsNotTruePredicate | FIsNotFalsePredicate | \
                FIsNullOrHoldPredicate | FNullIfPredicate | FToRealPredicate | FSubstrPredicate | \
                FLikePredicate | FDateLikePredicate | FToDatePredicate | FStrftimePredicate | FToJulianDatePredicate

__all__ = [
    'FInPredicate',
    'FNotInPredicate',
    'FIsNullPredicate',
    'FIsNotNullPredicate',
    'FCasePredicate',
    'FCoalescePredicate',
    'FIfPredicate',
    'FAbsPredicate',
    'FPowerPredicate',
    'FExistsPredicate',
    'FAnyValuePredicate',
    'FFirstValuePredicate',
    'FLastValuePredicate',
    'FModPredicate',
    'FIsTruePredicate',
    'FIsFalsePredicate',
    'FIsNotTruePredicate',
    'FIsNotFalsePredicate',
    'is_null_or_hold_predicate',
    'FToRealPredicate',
    'FNullIfPredicate',
    'FSubstrPredicate',
    'FToDatePredicate',
    'FStrftimePredicate',
    'FLikePredicate',
    'FDateLikePredicate',
    'FToJulianDatePredicate',

    'PredicateType',
]
