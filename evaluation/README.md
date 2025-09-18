# To evaluate EX

for file in ../predictions/*json; do python evaluation_ex.py --predicted_sql_path $file --ground_truth_path ../../dev_20240627/dev.sql --db_root_path ../../dev_20240627/dev_databases/  --diff_json_path ../../dev_20240627/dev.json --num_cpus 24; done

# To submit jobs on cluster

for file in ./predictions/*.json; do submit-job.sh ./run.sh -b  $(basename $file)  -t 600 -m 8000 -d ./log/$(basename $file) -c 2 --multi ; done
for file in ./predictions/*.json; do submit-job.sh ./run.sh -b  $(basename $file)_vanilla  -t 600 -m 8000 -d ./log/$(basename $file)_vanilla -c 2 --multi ; done

# To gather results on cluster

for file in log/*/; do echo $file/$(basename $file); python concatenate_results.py $file/$(basename $file) evaluation/VeriEQL_results/$(basename $file); done

# To evaluate VeriEQL

for file in ../predictions/*json; do python evaluation_verieql.py ./VeriEQL_results/$(basename $file)_no_shrink/ $file EX_results/$(basename $file)_EX.csv VeriEQL_results_val/$(basename $file).csv; done

# To cross check
for file in ../predictions/*json; do python evaluation_crosscheck_verieql.py $file ./VeriEQL_results_val/$(basename $file).csv ./VeriEQL_results_val/ ./VeriEQL_results_val_cc/$(basename $file).csv; done

# To calculate performance metrics
for file in ../predictions/*json; do python calculate.py EX_results/$(basename $file)_EX.csv --prediction $file; done
for file in ../predictions/*json; do python calculate.py VeriEQL_results_val/$(basename $file).csv --prediction $file; done
for file in ../predictions/*json; do python calculate.py VeriEQL_results_val_cc/$(basename $file).csv --prediction $file; done

# To calculate coverage 
for file in ../predictions/*json; do python coverage.py ./VeriEQL_results/$(basename $file)/ EX_results/$(basename $file)_EX.csv; done
for file in ../predictions/*json; do python coverage.py ./VeriEQL_results/$(basename $file)_vanilla/ EX_results/$(basename $file)_EX.csv; done

# To generate the histogram

python analyze_incorrectness.py ./VeriEQL_results_val_cc/ VeriEQL_results_val_cc_verieql_only_histogram.png VeriEQL_results_val_cc_verifyeql_only_histogram.json


# To generate runtime
for file in VeriEQL_results_val_null/*; do echo $file; python runtime.py $file; done