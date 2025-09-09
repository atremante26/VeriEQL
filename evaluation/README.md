# To evaluate EX

for file in ../predictions/*json; do python evaluation_ex.py --predicted_sql_path $file --ground_truth_path ../../dev_20240627/dev.sql --db_root_path ../../dev_20240627/dev_databases/  --diff_json_path ../../dev_20240627/dev.json --num_cpus 24; done

# To gather results on cluster


for file in log/*/; do echo $file/$(basename $file); python concatenate_results.py $file/$(basename $file) evaluation/VeriEQL_results/$(basename $file); done

# To evaluate VeriEQL

for file in ../predictions/*json; do python evaluation_verieql.py ./VeriEQL_results/$(basename $file)/ $file EX_results/$(basename $file)_EX.csv VeriEQL_results_val/$(basename $file).csv; done

# To cross check
for file in ../predictions/*json; do python evaluation_crosscheck_verieql.py $file ./VeriEQL_results_val/$(basename $file).csv ./VeriEQL_results_val/ ./VeriEQL_results_val_cc/$(basename $file).csv; done

# To calculate performance metrics
for file in ../predictions/*json; do python calculate.py EX_results/$(basename $file)_EX.csv --prediction $file; done
for file in ../predictions/*json; do python calculate.py VeriEQL_results_val/$(basename $file).csv --prediction $file; done
for file in ../predictions/*json; do python calculate.py VeriEQL_results_val_cc/$(basename $file).csv --prediction $file; done

# To calculate coverage 
for file in ../predictions/*json; do python coverage.py ./VeriEQL_results/$(basename $file)/ EX_results/$(basename $file)_EX.csv; done