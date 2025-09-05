# To evaluate EX

for file in ../predictions/*json; do python evaluation_ex.py --predicted_sql_path $file --ground_truth_path ../../dev_20240627/dev.sql --db_root_path ../../dev_20240627/dev_databases/  --diff_json_path ../../dev_20240627/dev.json --num_cpus 24; done
