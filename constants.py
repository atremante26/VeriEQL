# -*- coding: utf-8 -*-

import datetime
import os
import re

from z3 import (
    Context,
    ArithRef,
    Function,
    Int as Z3_Int,
    String as Z3_String,
    BoolVal as Z3_BoolVal,
    IntVal as Z3_IntVal,
    RealVal as Z3_RealVal,
    StringVal as Z3_StringVal,
    And as Z3_And,
    Or as Z3_Or,
    Not as Z3_Not,
    If as Z3_If,
    Sum as Z3_Sum,
    Implies as Z3_Implies,
    DeclareSort as Z3_DeclareSort,
    IntSort as Z3_IntSort,
    BoolSort as Z3_BoolSort,
    RatVal as Z3_RatVal,
    StringSort as Z3_StringSort,
    SeqRef as Z3_SeqRef,
    StrToInt,
    IntToStr,
    Concat,
    Replace,
    InRe,
    Re as Z3_Re,
    Full,
    ReSort,

    ToReal,
    ToInt,
    IntNumRef,
    RatNumRef,
    BoolRef,
)

################################################################
# z3 wrapper
################################################################

Z3_CONTEXT = Context()
IntVal = lambda arg: Z3_IntVal(arg, ctx=Z3_CONTEXT)
RealVal = lambda arg: Z3_RealVal(arg, ctx=Z3_CONTEXT)
BoolVal = lambda arg: Z3_BoolVal(arg, ctx=Z3_CONTEXT)
StringVal = lambda arg: Z3_StringVal(arg, ctx=Z3_CONTEXT)
Int = lambda arg: Z3_Int(arg, ctx=Z3_CONTEXT)
Not = lambda *args: Z3_Not(*args, ctx=Z3_CONTEXT)
If = lambda a, b, c: Z3_If(a, b, c, ctx=Z3_CONTEXT)
Sum = lambda *args: Z3_Sum(*args, ctx=Z3_CONTEXT)
And = lambda *args: Z3_And(*args, ctx=Z3_CONTEXT)
Or = lambda *args: Z3_Or(*args, ctx=Z3_CONTEXT)
Implies = lambda a, b: Z3_Implies(a, b, ctx=Z3_CONTEXT)
Re = lambda a: Z3_Re(a, ctx=Z3_CONTEXT)
TupleSort = Z3_DeclareSort('TupleSort', ctx=Z3_CONTEXT)
BooleanSort = Z3_BoolSort(Z3_CONTEXT)
VarSort = IntSort = Z3_IntSort(Z3_CONTEXT)
StringSort = Z3_StringSort(Z3_CONTEXT)
DateSort = Z3_DeclareSort('DateSort', ctx=Z3_CONTEXT)

DATE2YEAR_FUNCTION = Function("DATE2YEAR_FUNCTION", DateSort, IntSort)
DATE2MONTH_FUNCTION = Function("DATE2MONTH_FUNCTION", DateSort, IntSort)
DATE2DAY_FUNCTION = Function("DATE2DAY_FUNCTION", DateSort, IntSort)
MONTH2DAYS_FUNCTION = Function("MONTH2DAYS_FUNCTION", IntSort, IntSort)

POS_INF__Int = Int('POS_INF__Int')
NEG_INF__Int = Int('NEG_INF__Int')
Z3_TRUE = BoolVal(True)
Z3_FALSE = BoolVal(False)
Z3_0 = IntVal('0')
Z3_1 = IntVal('1')
Z3_2 = IntVal('2')
Z3_3 = IntVal('3')
Z3_4 = IntVal('4')
Z3_5 = IntVal('5')
Z3_6 = IntVal('6')
Z3_7 = IntVal('7')
Z3_8 = IntVal('8')
Z3_9 = IntVal('9')
Z3_10 = IntVal('10')
Z3_11 = IntVal('11')
Z3_12 = IntVal('12')
Z3_28 = IntVal('28')
Z3_29 = IntVal('29')
Z3_30 = IntVal('30')
Z3_31 = IntVal('31')
Z3_100 = IntVal('100')
Z3_365 = IntVal('365')
Z3_400 = IntVal('400')
Z3_10000 = IntVal('10000')
Z3_NULL_VALUE = IntVal('-10')
Z3_EMPTY_STRING = StringVal("")
Z3_SPACE_STRING = StringVal(" ")
Z3_R0 = RealVal('0.0')
Z3_R1 = RealVal('1.0')
Z3_DATE_SEP = StringVal("-")

VARCHAR = "VARCHAR"
DATE = "DATE"
INTEGER = "INTEGER"

################################################################
# constants
################################################################

# big INT
INT_LOWER_BOUND = IntVal('-2147483648')
INT_UPPER_BOUND = IntVal('2147483647')

PROJ_PATH = os.path.dirname(__file__)
MIN_DATE = datetime.datetime(1, 1, 1)
DATE_LOWER_BOUND = IntVal('1')
MAX_DATE = datetime.datetime(9999, 12, 31)
DATE_UPPER_BOUND = IntVal(f'{(MAX_DATE - MIN_DATE).days + 1}')  # avoid bool('0000-01-01') == 0
SQL_NULL = {"null": None}
NumericType = int | float | ArithRef | IntNumRef | RatNumRef
BACKUP_SUFFIX = '__BACKUP__'
SPACE_STRING = "__SPACE_STRING__"
SIGN = StringVal("-")
# note that the hash code of string in python is out of the range int32
IS_FALSE = "__IS_FALSE__"
IS_TRUE = "__IS_TRUE__"

VARCHAR_LENGTH = 20
TIMEOUT = 600  # 10 min
MIN_YEAR = IntVal('0000')
MAX_YEAR = IntVal('9999')
JULIANDATE_OFFSET = 2440586.5  # julianday('1970-01-01')=2440587.5, -1 because '1970-01-01' -> 1

DATE_SHIFT_PATTERN = re.compile(r"([+-])\s*(\d+)\s*(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)", re.IGNORECASE)
PRINTF_FLOAT_PATTERN = re.compile(r"%\.(\d+)[fF]%%", re.IGNORECASE)

class DIALECT:
    ALL = "all"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    PSQL = "psql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"


class STATE:
    EQUIV = "EQU"
    NON_EQUIV = "NEQ"
    UNKNOWN = 'UNK'
    TIMEOUT = "TMO"
    SYN_ERR = "SYN"
    NOT_IMPL_ERR = "NIE"
    NOT_SUP_ERR = "NSE"
    OOM = "OOM"
    OTHER_ERR = "OTE"