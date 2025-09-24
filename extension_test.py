# -*- coding: utf-8 -*-

from constants import DIALECT
from environment import Environment
import argparse
import json


def load_constraints():
    """Load constraints from dev_constraints.json"""
    try:
        with open('BIRD_schemas/dev_constraints.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: dev_constraints.json not found. Using empty constraints.")
        return {}


def load_schemas():
    """Load table definitions from table_definitions.json"""
    try:
        with open('BIRD_schemas/table_to_columns.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: table_definitions.json not found. Using empty schemas.")
        return {}


def eval(sql1, sql2, schema, ROW_NUM=2, constraints=None, **kwargs):
    # encode_date = True: must encode dates/datetimes as tuples;
    # encode_date = False: only follow this encoding if queries involve STRFTIME
    DATE_KEYS = ["STRFTIME", "JULIANDAY"]
    kwargs["encode_date"] = kwargs.get("encode_date", False) or any(
        any(map(lambda query: key in str.upper(query), [sql1, sql2])) for key in DATE_KEYS)
    # encode_string = True: must encode strings as Z3 builtin strings;
    # encode_string = False: only follow this encoding if queries involve SUBSTR, LIKE
    # since date involves arithmetic operations, once encode_date = True, encode_string must be True.
    STRING_KEYS = [" LIKE ", "SUBSTR"]
    kwargs["encode_string"] = kwargs.get("encode_string", False) or any(
        any(map(lambda query: key in str.upper(query), [sql1, sql2])) for key in STRING_KEYS) or kwargs["encode_date"]
    with Environment(**kwargs) as env:
        for k, v in schema.items():
            env.create_database(attributes=v, bound_size=ROW_NUM, name=k)
        env.add_constraints(constraints)
        env.save_checkpoints()
        if env._script_writer is not None:
            env._script_writer.save_checkpoints()
        result = env.analyze(sql1, sql2, out_file="test/test.py")
        if env.show_counterexample:
            print(env.counterexample)
        if env.traversing_time is not None:
            print(f"Time cost: {env.traversing_time + env.solving_time:.2f}")
        if result == True:
            print("\033[1;32;40m>>> Equivalent! \033[0m")
        else:
            print("\033[1;31;40m>>> Non-Equivalent! Found a counterexample! \033[0m")


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser(description="Testing for VeriEQL extensions")
    args_parser.add_argument('--extension_type', type=str, required=True,
                             help='Evaluate sample questions for different extension types')
    args = args_parser.parse_args()

    if args.extension_type == 'real':
        questions = {
            62: [
                "SELECT COUNT(*) FROM SCHOOLS INNER JOIN FRPM ON SCHOOLS.CDSCODE = FRPM.CDSCODE WHERE SCHOOLS.COUNTY = 'LOS ANGELES' AND SCHOOLS.CHARTER = 0 AND (FRPM.FREE_MEAL_COUNT_K12 * 100 / FRPM.ENROLLMENT_K12) < 0.18",
                "SELECT COUNT(T2.SCHOOL) FROM FRPM AS T1 INNER JOIN SCHOOLS AS T2 ON T1.CDSCODE = T2.CDSCODE WHERE T2.COUNTY = 'LOS ANGELES' AND T2.CHARTER = 0 AND CAST(T1.FREE_MEAL_COUNT_K12 AS REAL) * 100 / T1.ENROLLMENT_K12 < 0.18",
                "california_schools"
            ],
            227: [
                "SELECT ROUND((CAST(SUM(CASE WHEN MOLECULE.LABEL = '+' THEN 1 ELSE 0 END) AS REAL) / COUNT(MOLECULE.MOLECULE_ID)) * 100, 3) AS PERCENTAGE FROM MOLECULE",
                "SELECT ROUND(CAST(COUNT(CASE WHEN T.LABEL = '+' THEN T.MOLECULE_ID ELSE NULL END) AS REAL) * 100 / COUNT(T.MOLECULE_ID),3) FROM MOLECULE T",
                "toxicology"
            ],
            245: [
                "SELECT AVG(BOND_COUNT) FROM ( SELECT ATOM.ATOM_ID, COUNT(CONNECTED.BOND_ID) AS BOND_COUNT FROM ATOM INNER JOIN CONNECTED ON ATOM.ATOM_ID = CONNECTED.ATOM_ID WHERE ATOM.ELEMENT = 'I' GROUP BY ATOM.ATOM_ID ) AS SUBQUERY",
                "SELECT CAST(COUNT(T2.BOND_ID) AS REAL) / COUNT(T1.ATOM_ID) FROM ATOM AS T1 INNER JOIN CONNECTED AS T2 ON T1.ATOM_ID = T2.ATOM_ID WHERE T1.ELEMENT = 'I'",
                "toxicology"
            ]
        }
    elif args.extension_type == 'datetime':
        questions = {
            1: ["SELECT COUNT(DISTINCT PATIENT.ID) FROM PATIENT INNER JOIN EXAMINATION ON PATIENT.ID = EXAMINATION.ID WHERE PATIENT.SEX = 'M' AND EXAMINATION.EXAMINATION_DATE BETWEEN '1995-01-01' AND '1997-12-31' AND EXAMINATION.DIAGNOSIS = 'BEHCET' AND PATIENT.ADMISSION = '-'",
                "SELECT COUNT(T1.ID) FROM PATIENT AS T1 INNER JOIN EXAMINATION AS T2 ON T1.ID = T2.ID WHERE T2.DIAGNOSIS = 'BEHCET' AND T1.SEX = 'M' AND STRFTIME('%Y', T2.EXAMINATION_DATE) BETWEEN '1995' AND '1997' AND T1.ADMISSION = '-'",
                "thrombosis_prediction"],
            # 68: [
            #    "SELECT SCHOOLS.COUNTY FROM SCHOOLS WHERE SCHOOLS.SOC = 11 AND SCHOOLS.CLOSEDDATE BETWEEN '1980-01-01' AND '1989-12-31' GROUP BY SCHOOLS.COUNTY ORDER BY COUNT(*) DESC LIMIT 1",
            #    "SELECT COUNTY FROM SCHOOLS WHERE STRFTIME('%Y', CLOSEDDATE) BETWEEN '1980' AND '1989' AND STATUSTYPE = 'CLOSED' AND SOC = 11 GROUP BY COUNTY ORDER BY COUNT(SCHOOL) DESC LIMIT 1",
            #    "california_schools"
            # ],
            # 969: [
            #    "SELECT COUNT(*) FROM DRIVERS WHERE NATIONALITY = 'BRITISH' AND STRFTIME('%Y', DOB) = '1980';",
            #    "SELECT COUNT(DRIVERID) FROM DRIVERS WHERE NATIONALITY = 'BRITISH' AND STRFTIME('%Y', DOB) = '1980'",
            #    "formula_1"
            # ],
            # 1150: [
            #    "SELECT CAST(COUNT(ID) * 100.0 / (SELECT COUNT(ID) FROM PATIENT WHERE SEX = 'F') AS REAL) FROM PATIENT WHERE SEX = 'F' AND STRFTIME('%Y', BIRTHDAY) > '1930'",
            #    "SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', BIRTHDAY) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*) FROM PATIENT WHERE SEX = 'F'",
            #    "thrombosis_prediction"
            # ],
            # 1339: [
            #    "SELECT AVG(EXPENSE.COST) FROM EXPENSE INNER JOIN MEMBER ON EXPENSE.LINK_TO_MEMBER = MEMBER.MEMBER_ID WHERE MEMBER.FIRST_NAME = 'ELIJAH' AND MEMBER.LAST_NAME = 'ALLEN' AND (STRFTIME('%M', EXPENSE.EXPENSE_DATE) = '09' OR STRFTIME('%M', EXPENSE.EXPENSE_DATE) = '10')",
            #    "SELECT AVG(T2.COST) FROM MEMBER AS T1 INNER JOIN EXPENSE AS T2 ON T1.MEMBER_ID = T2.LINK_TO_MEMBER WHERE T1.LAST_NAME = 'ALLEN' AND T1.FIRST_NAME = 'ELIJAH' AND (SUBSTR(T2.EXPENSE_DATE, 6, 2) = '09' OR SUBSTR(T2.EXPENSE_DATE, 6, 2) = '10')",
            #    "student_club"
            # ]
        }
    elif args.extension_type == 'substring':
        questions = {
            242: [
                "SELECT MOLECULE.MOLECULE_ID FROM ATOM INNER JOIN MOLECULE ON ATOM.MOLECULE_ID = MOLECULE.MOLECULE_ID WHERE SUBSTR(ATOM.ATOM_ID, 7, 2) BETWEEN '21' AND '25' AND MOLECULE.LABEL = '+'",
                "SELECT DISTINCT T2.MOLECULE_ID FROM ATOM AS T1 INNER JOIN MOLECULE AS T2 ON T1.MOLECULE_ID = T2.MOLECULE_ID WHERE SUBSTR(T1.ATOM_ID, -2) BETWEEN '21' AND '25' AND T2.LABEL = '+'",
                "toxicology"
            ],
            246: [
                "SELECT BOND.BOND_TYPE, BOND.BOND_ID FROM ATOM INNER JOIN CONNECTED ON ATOM.ATOM_ID = CONNECTED.ATOM_ID INNER JOIN BOND ON CONNECTED.BOND_ID = BOND.BOND_ID WHERE SUBSTR(ATOM.ATOM_ID, 7, 2) + 0 = 45",
                "SELECT T1.BOND_TYPE, T1.BOND_ID FROM BOND AS T1 INNER JOIN CONNECTED AS T2 ON T1.BOND_ID = T2.BOND_ID WHERE SUBSTR(T2.ATOM_ID, 7, 2) = '45'",
                "toxicology"
            ],
            1332: [
                "SELECT BUDGET.SPENT FROM EVENT INNER JOIN BUDGET ON EVENT.EVENT_ID = BUDGET.LINK_TO_EVENT WHERE EVENT.EVENT_NAME = 'SEPTEMBER MEETING' AND BUDGET.CATEGORY = 'FOOD'",
                "SELECT T2.SPENT FROM EVENT AS T1 INNER JOIN BUDGET AS T2 ON T1.EVENT_ID = T2.LINK_TO_EVENT WHERE T1.EVENT_NAME = 'SEPTEMBER MEETING' AND T2.CATEGORY = 'FOOD' AND SUBSTR(T1.EVENT_DATE, 6, 2) = '09'",
                "student_club"
            ]
        }
    elif args.extension_type == 'subquery':
        questions = {
            222: [
                "SELECT (SELECT COUNT(*) FROM MOLECULE WHERE LABEL = '+') - (SELECT COUNT(*) FROM MOLECULE WHERE LABEL = '-') AS DIFFERENCE",
                "SELECT COUNT(CASE WHEN T.LABEL = '+' THEN T.MOLECULE_ID ELSE NULL END) - COUNT(CASE WHEN T.LABEL = '-' THEN T.MOLECULE_ID ELSE NULL END) AS DIFF_CAR_NOTCAR FROM MOLECULE T",
                "toxicology"
            ],
            744: [
                "SELECT (SELECT COUNT(*) FROM SUPERHERO WHERE PUBLISHER_ID = (SELECT ID FROM PUBLISHER WHERE PUBLISHER_NAME = 'MARVEL COMICS')) - (SELECT COUNT(*) FROM SUPERHERO WHERE PUBLISHER_ID = (SELECT ID FROM PUBLISHER WHERE PUBLISHER_NAME = 'DC COMICS')) AS DIFFERENCE",
                "SELECT SUM(CASE WHEN T2.PUBLISHER_NAME = 'MARVEL COMICS' THEN 1 ELSE 0 END) - SUM(CASE WHEN T2.PUBLISHER_NAME = 'DC COMICS' THEN 1 ELSE 0 END) FROM SUPERHERO AS T1 INNER JOIN PUBLISHER AS T2 ON T1.PUBLISHER_ID = T2.ID",
                "superhero"
            ],
            790: [
                "SELECT (SELECT SUM(WEIGHT_KG) FROM SUPERHERO WHERE FULL_NAME = 'EMIL BLONSKY') - (SELECT SUM(WEIGHT_KG) FROM SUPERHERO WHERE FULL_NAME = 'CHARLES CHANDLER') AS DIFFERENCE;",
                "SELECT ( SELECT WEIGHT_KG FROM SUPERHERO WHERE FULL_NAME LIKE 'EMIL BLONSKY' ) - ( SELECT WEIGHT_KG FROM SUPERHERO WHERE FULL_NAME LIKE 'CHARLES CHANDLER' ) AS CALCULATE",
                "superhero"
            ]
        }
    elif args.extension_type == 'like':
        questions = {
            836: [
                "SELECT COUNT(*) FROM SUPERHERO WHERE FULL_NAME LIKE 'JOHN%';",
                "SELECT COUNT(ID) FROM SUPERHERO WHERE FULL_NAME LIKE 'JOHN%'",
                "superhero"
            ],
            1240: [
                "SELECT AVG(LABORATORY.HCT) FROM LABORATORY WHERE LABORATORY.DATE LIKE '1991%' AND LABORATORY.HCT < 29",
                "SELECT AVG(T2.HCT) FROM PATIENT AS T1 INNER JOIN LABORATORY AS T2 ON T1.ID = T2.ID WHERE T2.HCT < 29 AND STRFTIME('%Y', T2.DATE) = '1991'",
                "thrombosis_prediction"
            ],
            1319: [
                "SELECT MAJOR.COLLEGE FROM MEMBER INNER JOIN MAJOR ON MEMBER.LINK_TO_MAJOR = MAJOR.MAJOR_ID WHERE MEMBER.POSITION = 'VICE PRESIDENT'",
                "SELECT T2.COLLEGE FROM MEMBER AS T1 INNER JOIN MAJOR AS T2 ON T1.LINK_TO_MAJOR = T2.MAJOR_ID WHERE T1.POSITION LIKE 'VICE PRESIDENT'",
                "student_club"
            ]
        }
    elif args.extension_type == 'iif':
        questions = {
            977: [
                "SELECT COUNT(*) FROM RESULTS INNER JOIN STATUS ON RESULTS.STATUSID = STATUS.STATUSID WHERE RESULTS.RACEID > 50 AND RESULTS.RACEID < 100 AND RESULTS.TIME IS NOT NULL AND STATUS.STATUSID = 2",
                "SELECT SUM(IIF(TIME IS NOT NULL, 1, 0)) FROM RESULTS WHERE STATUSID = 2 AND RACEID < 100 AND RACEID > 50",
                "formula_1"
            ],
            1485: [
                "SELECT (SELECT SUM(CONSUMPTION) FROM YEARMONTH WHERE CUSTOMERID = 7 AND DATE = 201304) - (SELECT SUM(CONSUMPTION) FROM YEARMONTH WHERE CUSTOMERID = 5 AND DATE = 201304) AS DIFFERENCE FROM YEARMONTH LIMIT 1;",
                "SELECT SUM(IIF(CUSTOMERID = 7, CONSUMPTION, 0)) - SUM(IIF(CUSTOMERID = 5, CONSUMPTION, 0)) FROM YEARMONTH WHERE DATE = '201304'",
                "debit_card_specializing"
            ]
        }
    elif args.extension_type == 'julianday':
        questions = {
            971: [
                "SELECT DRIVERS.DRIVERREF FROM DRIVERS WHERE DRIVERS.NATIONALITY = 'GERMAN' ORDER BY DRIVERS.DOB ASC LIMIT 1",
                "SELECT DRIVERREF FROM DRIVERS WHERE NATIONALITY = 'GERMAN' ORDER BY JULIANDAY(DOB) ASC LIMIT 1",
                "formula_1"
            ],
            1002: [
                "SELECT DRIVERS.FORENAME, DRIVERS.SURNAME, DRIVERS.NATIONALITY, RACES.NAME FROM DRIVERS INNER JOIN RESULTS ON DRIVERS.DRIVERID = RESULTS.DRIVERID INNER JOIN RACES ON RESULTS.RACEID = RACES.RACEID ORDER BY DRIVERS.DOB DESC LIMIT 1",
                "SELECT T1.FORENAME, T1.SURNAME, T1.NATIONALITY, T3.NAME FROM DRIVERS AS T1 INNER JOIN DRIVERSTANDINGS AS T2 ON T1.DRIVERID = T2.DRIVERID INNER JOIN RACES AS T3 ON T2.RACEID = T3.RACEID ORDER BY JULIANDAY(T1.DOB) DESC LIMIT 1",
                "formula_1"
            ]
        }
    elif args.extension_type == 'index':
        questions = {
            1: [
                "SELECT NAME FROM CARDS WHERE ISPROMO = 1 AND NOT SIDE IS NULL",
                "SELECT DISTINCT NAME FROM CARDS WHERE ISPROMO = 1 AND SIDE IS NOT NULL",
                "card_games"
            ],
            2: [
                "SELECT (T1.FREE_MEAL_COUNT_AGES_5_17 / T1.ENROLLMENT_AGES_5_17) AS ELIGIBLEFREERATE FROM FRPM AS T1 INNER JOIN SCHOOLS AS T2 ON T1.CDSCODE = T2.CDSCODE WHERE T2.SOCTYPE = 'CONTINUATION HIGH SCHOOLS' AND NOT T1.FREE_MEAL_COUNT_AGES_5_17 IS NULL AND NOT T1.ENROLLMENT_AGES_5_17 IS NULL AND T1.ENROLLMENT_AGES_5_17 > 0 ORDER BY ELIGIBLEFREERATE ASC LIMIT 3",
                "SELECT FREE_MEAL_COUNT_AGES_5_17 / ENROLLMENT_AGES_5_17 FROM FRPM WHERE EDUCATIONAL_OPTION_TYPE = 'CONTINUATION SCHOOL' AND FREE_MEAL_COUNT_AGES_5_17 / ENROLLMENT_AGES_5_17 IS NOT NULL ORDER BY FREE_MEAL_COUNT_AGES_5_17 / ENROLLMENT_AGES_5_17 ASC LIMIT 3",
                "california_schools"
            ]
        }
    elif args.extension_type == 'null':
        questions = {
            1: [
                "SELECT ((R1.FASTESTLAPSPEED - R2.FASTESTLAPSPEED) / R1.FASTESTLAPSPEED) * 100 AS PERCENTAGE_DIFFERENCE FROM RESULTS R1 JOIN RESULTS R2 ON R1.DRIVERID = R2.DRIVERID WHERE R1.RACEID = 853 AND R2.RACEID = 854 AND R1.DRIVERID = (SELECT DRIVERID FROM DRIVERS WHERE FORENAME = 'PAUL' AND SURNAME = 'DI RESTA')",
                "SELECT (SUM(IIF(T2.RACEID = 853, T2.FASTESTLAPSPEED, 0)) - SUM(IIF(T2.RACEID = 854, T2.FASTESTLAPSPEED, 0))) * 100 / SUM(IIF(T2.RACEID = 853, T2.FASTESTLAPSPEED, 0)) FROM DRIVERS AS T1 INNER JOIN RESULTS AS T2 ON T2.DRIVERID = T1.DRIVERID WHERE T1.FORENAME = 'PAUL' AND T1.SURNAME = 'DI RESTA'",
                "formula_1"
            ]
        }

    else:
        print(f"Unknown extension type: {args.extension_type}")
        print("Available types: real, datetime, substring, subquery, like, iif")
        exit(1)

    # Load constraints and schemas
    all_constraints = load_constraints()
    all_schemas = load_schemas()

    # Configuration for VeriEQL analysis
    config = {
        'generate_code': True,
        'timer': True,
        'show_counterexample': True,
        "dialect": DIALECT.MYSQL,
        'all_null_is_deleted': True,
    }

    # Run evaluation for all questions in the selected extension type
    for question_id, (sql1, sql2, schema_name) in questions.items():
        print(f"\n{'=' * 60}")
        print(f"Question ID: {question_id} ({args.extension_type})")
        print(f"Schema: {schema_name}")
        print(f"{'=' * 60}")
        print(f"SQL1: {sql1}")
        print(f"SQL2: {sql2}")
        print(f"{'=' * 60}")

        # Get the specific schema and constraints for this database
        schema = all_schemas.get(schema_name, {})
        constraints = all_constraints.get(schema_name, [])[0]

        if not schema:
            print(f"Warning: No schema found for database '{schema_name}'")

        eval(sql1, sql2, schema, 2, constraints=constraints, **config)
        # eval(sql1, sql2, schema, ROW_NUM=2, constraints=constraints, **config)
