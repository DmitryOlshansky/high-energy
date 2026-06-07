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

def create_binary_prop_encoder(thresholds):
    def encoder(value):
        return bisect.bisect(thresholds, value) + 1
    return encoder

prop_encoder = create_binary_prop_encoder([7.0, 11.25])
activities = sorted([float(x) for x in csv['spark']])

def experiment(rid):
    with open("spark-%s.fimi" % rid, "w") as f:
        f.write("# attributes: %d properties: O(1,2,3)\n" % (max_fimi+1))
        for i in range(0, len(data)):
            fcsp_line = encode_fcsp(csv['fcss'][i])
            max_nmr_line = nmr_encoder(csv['nmr'][i])
            #full_line = fcsp_line + " " + max_nmr_line
            full_line = max_nmr_line
            prop_part = " | %s" % prop_encoder(float(csv['spark'][i]))
            f.write(full_line+prop_part+"\n")
    env = { "JAVA_OPTS" : "-Xms512m -Xmx512m" }
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "split", "5", "spark-%s.fimi" % rid,  "train-%s.fimi" % rid, "verify-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "tau", "verify-%s.fimi" % rid, "tau-%s.fimi" % rid], stdout=subprocess.DEVNULL,  env=env)
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "generate", "-m", "model-%s.fimi" % rid, "-a", "cbo", "--strategy=boundedVotingMajority:50", "train-%s.fimi" %rid], stdout=subprocess.DEVNULL, env=env) 
    subprocess.check_call(["./jsm4s/target/universal/stage/bin/jsm-cli", "predict",  "-m", "model-%s.fimi" % rid, "-o", "predictions-%s.fimi" % rid, "tau-%s.fimi" % rid], stdout=subprocess.DEVNULL, env=env)
    text = subprocess.check_output(["./jsm4s/target/universal/stage/bin/jsm-cli", "stats", "verify-%s.fimi" % rid, "predictions-%s.fimi" % rid], env=env)
    for line in str(text).split("\n"):
        m = re.search(r"Correct predictions ratio \d+/\d+ (\d+.\d)+%", line)
        if m:
            result = float(m.group(1))
    return result

pool = futures.ThreadPoolExecutor(10)

for k in range(2,35):
    kmeans = KMeans(n_clusters=k, n_init='auto', random_state=0).fit(X)
    labels = kmeans.labels_ 
    max_fimi = nmr_attrs_start + k
    runs = 20
    avg_of_runs = 0.0
    for r in range(0, runs):
        iters = 20
        def nmr_encoder(nmrs):
            encoded = { }
            def conv(x):
                return int(labels[bisect.bisect(X, float(x))-1])
            for n in nmrs:
                encoded[nmr_attrs_start + conv(n)] = True
            return " ".join([str(k) for k in sorted(encoded.keys())])
        result = 0.0
        futures = []
        for i in range(iters):
            futures.append(pool.submit(experiment, i))
        for i in range(iters):
            result += futures[i].result()
        avg_of_runs += result / iters
    avg_of_runs /= runs
    print("K = %s, P = %s" % (k, avg_of_runs))
