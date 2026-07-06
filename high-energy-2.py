import numpy as np
from sklearn.cluster import KMeans
import bisect
import subprocess
import re
import concurrent.futures as futures

with open("molecules_fcss_with_nmr.csv") as f:
    lines = f.readlines()
    cols = [k.strip("\n").split(';') for k in lines]
    cols = cols[1:]
    data = [{ "nmr" : list(filter(lambda w: w != '-', x[5:15])), 'fcss': x[15], "spark": x[2] } for x in cols if x[2] != '-']
    csv =  {}
    for k,v in data[0].items():
        csv[k] = [x[k] for x in data]

full_kv = {}
for code in csv['fcss']:
    kv = {}
    codes = code.strip().split(" ")
    for c in codes:
        if c in kv:
            kv[c] += 1
        else:
            kv[c] = 1
    for k, v in kv.items():
        if k in full_kv:
            full_kv[k] = max(v, full_kv[k])
        else:
            full_kv[k] = v

# print(full_kv)

keys = sorted(list(full_kv.keys()))
cumulative_keys = {}
cumulative_values = {}
cumulative_sum = 0
for k in keys:
    cumulative_keys[k] = cumulative_sum
    for v in range(0, full_kv[k]):
        cumulative_values[cumulative_sum + v] = k
    cumulative_sum += full_kv[k]

def encode_fcsp(code):
    words = code.strip().split(" ")
    freq = {}
    fimi = []
    for w in words:
        if w in freq:
            freq[w] += 1
        else:
            freq[w] = 1
        fimi.append(cumulative_keys[w] + freq[w])
    fimi = map(lambda x: str(x), sorted(fimi))
    return " ".join(fimi)

def decode_fcsp(fimi_line):
    fimi = [int(w) for w in fimi_line.strip().split(" ")]
    words = [cumulative_values[f] for f in fimi]
    return " ".join(sorted(words))

def normalize(fcsp):
    return " ".join(sorted(fcsp.split(" ")))

#print(normalize(csv['fcss'][11]))

nmr_attrs_start = cumulative_sum + 1
shifts = sorted([float(x) for y in csv['nmr'] for x in y])
shifts = np.array(shifts, dtype=float)
X = shifts.reshape(-1, 1)

activities = sorted([float(x) for x in csv['spark']])
activities = np.array(activities[:-5], dtype=float)
threshold = activities[len(activities) // 2]
max_threshold = activities[-1]
Y = activities.reshape(-1, 1)

def experiment(rid, props_count, bound):
    data_split = [[], []]
    for i in range(0, len(data)):
        fcsp_line = encode_fcsp(csv['fcss'][i])
        max_nmr_line = nmr_encoder(csv['nmr'][i])
        full_line = fcsp_line + " " + max_nmr_line
        #full_line = max_nmr_line
        p = prop_encoder(float(csv['spark'][i]))
        prop_part = " | %s" % p
        if p > 0:
            data_split[p-1].append(full_line+prop_part+"\n")
    np.random.shuffle(data_split[0])
    np.random.shuffle(data_split[1])
    #print(data_split)
    i, j = 0, 0
    with open("train-%s.fimi" % rid, "w") as f_train:
        fmt = "# attributes: %d properties: O("+",".join([str(x) for x in range(1, props_count+1)])+")\n"
        f_train.write(fmt % (max_fimi+1))
        while i < len(data_split[0])-2:
            f_train.write(data_split[0][i])
            i += 1
        while j < len(data_split[1])-2:
            f_train.write(data_split[1][j])
            j += 1
    with open("verify-%s.fimi" % rid, "w") as f_test:
        fmt = "# attributes: %d properties: O("+",".join([str(x) for x in range(1, props_count+1)])+")\n"
        f_test.write(fmt % (max_fimi+1))
        while i < len(data_split[0]):
            f_test.write(data_split[0][i])
            i += 1
        while j < len(data_split[1]):
            f_test.write(data_split[1][j])
            j += 1
    env = { "JAVA_OPTS" : "-Xms512m -Xmx512m" }
    #subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "split", "5", "spark-%s.fimi" % rid,  "train-%s.fimi" % rid, "verify-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "tau", "train-%s.fimi" % rid, "tau-train-%s.fimi" % rid], stdout=subprocess.DEVNULL,  env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "tau", "verify-%s.fimi" % rid, "tau-%s.fimi" % rid], stdout=subprocess.DEVNULL,  env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "generate", "-m", "model-%s.fimi" % rid, "-a", "cbo", "--strategy=boundedVotingMajority:%s" % bound, "train-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env) 
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "tune", "-a3", "-t2", "-m", "model-%s.fimi" % rid, "-o", "model-tuned-%s.fimi" % rid, "train-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env) 
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "predict",  "-m", "model-tuned-%s.fimi" % rid, "-o", "predictions-%s.fimi" % rid, "tau-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "predict",  "-m", "model-tuned-%s.fimi" % rid, "-o", "predictions-train-%s.fimi" % rid, "tau-train-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env)
    text = subprocess.check_output(["./jsm4s/target/universal/stage/bin/jsm-cli", "stats", "verify-%s.fimi" % rid, "predictions-%s.fimi" % rid], env=env)
    for line in str(text).split("\n"):
        m = re.search(r"Correct predictions ratio \d+/\d+ (\d+\.\d+)%", line)
        if m:
            result_test = float(m.group(1))
    text = subprocess.check_output(["./jsm4s/target/universal/stage/bin/jsm-cli", "stats", "train-%s.fimi" % rid, "predictions-train-%s.fimi" % rid], env=env)
    for line in str(text).split("\n"):
        m = re.search(r"Correct predictions ratio \d+/\d+ (\d+\.\d+)%", line)
        if m:
            #print(line)
            result_train = float(m.group(1))
    #print(">", result_test, result_train)
    return result_test, result_train

pool = futures.ThreadPoolExecutor(10)


for k in range(13,26):
    for bound in range(30, 40, 10):
        for q in range(3, 4):
            km = KMeans(n_clusters=q, n_init='auto', random_state=0).fit(Y)
            prop_cluster = km.labels_
            cluster_sizes = { }
            for c in prop_cluster:
                if c in cluster_sizes:
                    cluster_sizes[c] += 1
                else:
                    cluster_sizes[c] = 1
            #print(cluster_sizes)
            #print(cluster_sizes[2] / (cluster_sizes[0] + cluster_sizes[2]))
            #print(prop_cluster)
            #print(len(prop_cluster))
            def prop_encoder(property):
                if property > max_threshold:
                    return 0
                #print(">", bisect.bisect(activities, float(property)))
                #print(">>",prop_cluster[bisect.bisect(activities, float(property))-1])
                #pos = bisect.bisect(activities, float(property))-1
                if (property <= threshold):
                    return 1
                return 2
                #print(pos, " -> ",prop_cluster[pos])
                #r = int(prop_cluster[pos]) + 1
                #return r
            
            kmeans = KMeans(n_clusters=k, n_init='auto', random_state=0).fit(X)
            labels = kmeans.labels_ 
            max_fimi = nmr_attrs_start + k
            runs = 20
            avg_of_runs_test = 0.0
            avg_of_runs_train = 0.0
            for r in range(0, runs):
                iters = 20
                def nmr_encoder(nmrs):
                    encoded = { }
                    def conv(x):
                        return int(labels[bisect.bisect(shifts, float(x))-1])
                    for n in nmrs:
                        encoded[nmr_attrs_start + conv(n)] = True
                    return " ".join([str(k) for k in sorted(encoded.keys())])
                result_test = 0.0
                result_train = 0.0
                futures = []
                for i in range(iters):
                    futures.append(pool.submit(experiment, i, q, bound))
                for i in range(iters):
                    test, train = futures[i].result()
                    result_train += train
                    result_test += test
                #print("Test = %s, Train = %s" % (result_test / iters, result_train / iters))
                avg_of_runs_test += result_test / iters
                avg_of_runs_train += result_train / iters
            avg_of_runs_test /= runs
            avg_of_runs_train /= runs
            print("Bound = %s, Q = %s, K = %s, Ptest = %s, Ptrain = %s" % (bound, q, k, avg_of_runs_test, avg_of_runs_train))
