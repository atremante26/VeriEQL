# To evaluate EX

for file in ../predictions/*json; do python evaluation_ex.py --predicted_sql_path $file --ground_truth_path ../../dev_20240627/dev.sql --db_root_path ../../dev_20240627/dev_databases/  --diff_json_path ../../dev_20240627/dev.json --num_cpus 24; done


# To evaluate VeriEQL

python evaluation_verieql.py ./VeriEQL_results/alpha_sql.json_verieql/ ../predictions/alpha_sql.json EX_results/alpha_sql_EX.csv test.csv

# To cross check
python evaluation_crosscheck_verieql.py ../predictions/alpha_sql.json VeriEQL_result_after_validation/test.csv VeriEQL_result_after_validation/ test_new.csv