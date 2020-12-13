import time
import statistics
import random
import json
import bm_utils
import functions
import os
import subprocess
import datetime

with open('config.json') as json_file:
    json_data = json.load(json_file)

result_json = {"results": []}

# main experiment loop
for experiment in json_data['experiments']:
    # setup
    measurement=[] # to measure the time taken to execute the function in each iteration
    params_list = []
    iterations = experiment['iterations']
    for param in experiment['params']:
        if(param=="BM_WORKLOAD_STR"):
            workload = bm_utils.workload_gen(experiment['workload_size'])
            params_list.append(workload)

        elif(param=="BM_WORKLOAD_BYTE"):
            workload = bm_utils.workload_gen(experiment['workload_size'])
            params_list.append(workload.encode('utf-8'))


        elif(param=="RSA_PUB_KEY"):
            pub_key = bm_utils.gen_keys()[0]
            params_list.append(pub_key)

        elif(param=="RSA_PRIV_KEY"):
            from functions import rsa_encrypt
            pub_key, priv_key = bm_utils.gen_keys()
            workload = params_list.pop()
            encrypted_workload = rsa_encrypt(workload, pub_key)
            params_list.append(encrypted_workload)
            params_list.append(priv_key)

        elif(param=="RSA_SIGN_KEY"):
            priv_key = bm_utils.gen_keys()[1]
            params_list.append(priv_key)

        elif(param=="RSA_VERIFY_KEY"):
            from functions import rsa_sign
            pub_key, priv_key = bm_utils.gen_keys()
            params_list.pop()
            workload = params_list[0]
            sign = rsa_sign(workload, priv_key)
            params_list.append(sign)
            params_list.append(pub_key)

    # import the function to run
    func_name = experiment['function']
    if(experiment['function'].startswith('F_')):
        inner_func_name = experiment['function'][2:]
        func_obj = getattr(functions, inner_func_name)
        params_list.insert(0, func_obj)
        func_name = 'run_function_extended'
    function = getattr(functions, func_name)
    print(experiment['name'])
    # run experiment
    for iter in range(iterations):
        start_time = time.process_time()
        # execute the function now
        var = function(*params_list)
        end_time = time.process_time()
        elapsed = end_time-start_time
        if(func_name=='run_function_extended'):
            elapsed = var
        measurement.append(elapsed)

    # calculate stats
    try:
        length = len(var)
    except:
        length = None
    mean = statistics.mean(measurement)*10**6
    median = statistics.median(measurement)*10**6
    stddev = statistics.stdev(measurement)*10**6
    mean_per_byte = mean/experiment['workload_size']

    # output the result
    result = {
        "name": experiment['name'],
        "iterations": experiment['iterations'],
        "workload_size": experiment['workload_size']
    }

    if(length is not None):
        result["size_blowup"] = length

    # output the statistic measures if speficied
    if("mean" in experiment['stat_measures']):
        result['mean'] = mean
        result['mean_per_byte'] = mean_per_byte
    if("median" in experiment['stat_measures']):
        result['median'] = median
    if("stddev" in experiment['stat_measures']):
        result['stddev'] = stddev

    # append it to the results json object
    result_json['results'].append(result)

os.makedirs('results', exist_ok=True)
filename = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
with open('results/'+filename+'-results.json', 'w') as json_file:
    json_file.write(json.dumps(result_json, indent=4))

