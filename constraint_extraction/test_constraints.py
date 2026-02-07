"""
Run with python constraint_extraction/test_constraints.py from project root.
"""
import sys
from pathlib import Path
import json
import time

PROJECT_ROOT = Path(__file__).parent.parent
print(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from verieql import verify_sql_equivalence
from constants import DIALECT

with open("BIRD_schemas/table_to_columns.json", 'r') as f:
    schemas = json.load(f)

with open("constraint_extraction/constraint_results/LLM/all_constraints_LLM.json", 'r') as f:
    constraints = json.load(f)


def run_demo(title, database, sql1, sql2, constraint_type):
    print("\n" + "="*60)
    print(f"DEMO: {title}")
    print(f"Database: {database}")
    print(f"Constraint Type: {constraint_type}")
    print()
    
    print(f"SQL 1: {sql1}")
    print()
    print(f"SQL 2: {sql2}")
    print()
    
    # Show relevant constraints
    db_constraints = constraints[database][0]
    relevant = [c for c in db_constraints if constraint_type.lower() in str(c).lower()]
    print(f"Relevant {constraint_type} constraints: {len(relevant)}")
    print()
    
    config = {
        'generate_code': True,
        'timer': True,
        'show_counterexample': True,
        'dialect': DIALECT.MYSQL,
        'all_null_is_deleted': False,
        "encode_date": True,
        "encode_string": True
    }
    
    try:
        result = verify_sql_equivalence(
            sql1,
            sql2,
            schemas[database],
            ROW_NUM=2,
            constraints=db_constraints,
            **config
        )
               
        print(f"\nResult: {result['equivalent']}")
        
        if result['counterexample'] and not result['equivalent']:
            print(f"\nCounterexample found (constraints make this non-equivalent):")
            print(result['counterexample'])
        
        return result
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)[:100]}")
        return None


# DEMO 1: RANGE CONSTRAINTS (BETWEEN) - TP range
run_demo(
    title="RANGE Constraints - TP",
    database="thrombosis_prediction",
    sql1="SELECT * FROM LABORATORY WHERE TP BETWEEN 6.0 AND 8.5",
    sql2="SELECT * FROM LABORATORY WHERE TP >= 6.0 AND TP <= 8.5",
    constraint_type="BETWEEN"
)

# DEMO 2: RANGE CONSTRAINTS - ALB range
run_demo(
    title="RANGE Constraints - ALB Range",
    database="thrombosis_prediction",
    sql1="SELECT * FROM LABORATORY WHERE ALB BETWEEN 3.5 AND 5.5",
    sql2="SELECT * FROM LABORATORY WHERE ALB >= 3.5 AND ALB <= 5.5",
    constraint_type="BETWEEN"
)

# DEMO 3: CATEGORICAL CONSTRAINTS (IN) - SEX values
run_demo(
    title="CATEGORICAL Constraints - Patient Sex",
    database="thrombosis_prediction",
    sql1="SELECT ID, SEX FROM PATIENT WHERE SEX = 'M'",
    sql2="SELECT ID, SEX FROM PATIENT WHERE SEX = 'M'",
    constraint_type="IN"
)

# DEMO 4: CATEGORICAL CONSTRAINTS - ADMISSION
run_demo(
    title="CATEGORICAL Constraints - Admission Status",
    database="thrombosis_prediction",
    sql1="SELECT ID, ADMISSION FROM PATIENT WHERE ADMISSION = '-'",
    sql2="SELECT ID, ADMISSION FROM PATIENT WHERE ADMISSION = '-'",
    constraint_type="IN"
)

# DEMO 5: NOT NULL CONSTRAINTS - Patient Diagnosis
run_demo(
    title="NOT NULL Constraints - Patient Diagnosis",
    database="thrombosis_prediction",
    sql1="SELECT DIAGNOSIS FROM PATIENT",
    sql2="SELECT DIAGNOSIS FROM PATIENT WHERE DIAGNOSIS IS NOT NULL",
    constraint_type="NOT NULL"
)

# DEMO 6: FUNCTIONAL DEPENDENCIES - Patient attributes
run_demo(
    title="FUNCTIONAL DEPENDENCY - Patient ID determines SEX",
    database="thrombosis_prediction",
    sql1="SELECT ID, SEX FROM PATIENT WHERE ID = 1",
    sql2="SELECT ID, SEX FROM PATIENT WHERE ID = 1 AND SEX = 'F'",
    constraint_type="DEPENDENCY"
)

# DEMO 7: FUNCTIONAL DEPENDENCIES - Examination ID determines THROMBOSIS
run_demo(
    title="FUNCTIONAL DEPENDENCY - Examination ID determines Thrombosis",
    database="thrombosis_prediction",
    sql1="SELECT ID, THROMBOSIS FROM EXAMINATION WHERE ID = 14872",
    sql2="SELECT ID, THROMBOSIS FROM EXAMINATION WHERE ID = 14872 AND THROMBOSIS = 0",
    constraint_type="DEPENDENCY"
)

# DEMO 8: MULTIPLE RANGE CONSTRAINTS
run_demo(
    title="MULTIPLE RANGE Constraints - Blood Panel",
    database="thrombosis_prediction",
    sql1="SELECT * FROM LABORATORY WHERE TP BETWEEN 6.0 AND 8.5 AND ALB BETWEEN 3.5 AND 5.5",
    sql2="SELECT * FROM LABORATORY WHERE TP >= 6.0 AND TP <= 8.5 AND ALB >= 3.5 AND ALB <= 5.5",
    constraint_type="BETWEEN"
)


# DEMO 9: REAL BIRD QUERY - #1202 
run_demo(
    title="Real BIRD Query Q1202 - Multiple Constraints",
    database="thrombosis_prediction",
    sql1="SELECT COUNT(DISTINCT PATIENT.ID) FROM PATIENT INNER JOIN EXAMINATION ON PATIENT.ID = EXAMINATION.ID WHERE PATIENT.SEX = 'M' AND EXAMINATION.EXAMINATION_DATE BETWEEN '1995-01-01' AND '1997-12-31' AND EXAMINATION.DIAGNOSIS = 'BEHCET' AND PATIENT.ADMISSION = '-'",
    sql2="SELECT COUNT(T1.ID) FROM PATIENT AS T1 INNER JOIN EXAMINATION AS T2 ON T1.ID = T2.ID WHERE T2.DIAGNOSIS = 'BEHCET' AND T1.SEX = 'M' AND STRFTIME('%Y', T2.EXAMINATION_DATE) BETWEEN '1995' AND '1997' AND T1.ADMISSION = '-'",
    constraint_type="MULTIPLE"
)

# DEMO 10: Query with Constraints Improving Verification
run_demo(
    title="Constraint-Enhanced Verification",
    database="thrombosis_prediction",
    sql1="SELECT COUNT(*) FROM LABORATORY WHERE TP <= 6.0 OR TP >= 8.5",
    sql2="SELECT COUNT(*) FROM LABORATORY WHERE TP < 6.0 OR TP > 8.5",
    constraint_type="BETWEEN"
)
