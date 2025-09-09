# To evaluate EX

for file in ../predictions/*json; do python evaluation_ex.py --predicted_sql_path $file --ground_truth_path ../../dev_20240627/dev.sql --db_root_path ../../dev_20240627/dev_databases/  --diff_json_path ../../dev_20240627/dev.json --num_cpus 24; done


# To evaluate VeriEQL

for file in ../predictions/*json; do python evaluation_verieql.py ./VeriEQL_results/$(basename $file)/ $file EX_results/$(basename $file)_EX.csv VeriEQL_results_val/$(basename $file).csv

# To cross check
for file in ../predictions/*json; do python evaluation_crosscheck_verieql.py $file ./VeriEQL_results_val/$(basename $file).csv ./VeriEQL_results_val/ ./VeriEQL_results_val_cc/$(basename $file).csv

# To calculate metrics
python calculate.py [any csv files in VeriEQL_results*]