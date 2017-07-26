#! /usr/bin/env python
# coding: UTF-8

import sys
import math
import os
import datetime
import time
import numpy as np
import itertools
import json

from collections import defaultdict, namedtuple

from norm import NormalizedFeature

if len(sys.argv)!=4:
    print """
USAGE {} [pca|tsne] [id|tanh|range|std] file
""".format(os.path.basename(sys.argv[0]))
    exit(-1)

alg = sys.argv[1]
norm_alg = sys.argv[2]
filename = sys.argv[3]

title_map = {
  'id':'{}',
  'tanh': 'tanh-normalized {}',
  'range': 'range-normalized {}',
  'std': 'std-normalized {}',
}

if alg!='tsne' and alg!='pca': raise ValueError("alg should be either tsne or pca")

NormalizedFeature.set_norm(norm_alg)

AggKey=namedtuple("AggKey", ["proto", "src", "dst", "dst_port"])
FlowLine=namedtuple("FlowLine", [
    "STARTTIME","DUR","PROTO","SRCADDR","SPORT","DIR","DSTADDR","DPORT",
    "STATE","STOS","DTOS","TOTPKTS","TOTBYTES","SRCBYTES","LABEL"
])

STARTTIME,DUR,PROTO,SRCADDR,SPORT,DIR,DSTADDR,DPORT,STATE,STOS,DTOS,TOTPKTS,TOTBYTES,SRCBYTES,LABEL = range(15)

fmt = '%Y/%m/%d %H:%M:%S.%f'

def ts(input):
  return time.mktime(
    datetime.datetime.strptime(input, fmt).timetuple()
   )

counter = 0
idByKey = {}
keyById = {}

def try_int(i, fallback=None):
    try: return int(i)
    except ValueError: pass
    except TypeError: pass
    return fallback

def getIdByKey(proto, src, dst, dst_port):
    global counter
    k = (proto, src,dst,dst_port,)
    if k in idByKey:
       return idByKey[k]
    counter+=1
    idByKey[k] = counter
    keyById[counter] = k
    return counter



srcPortSetById = defaultdict(set)
isBotById = defaultdict(lambda:False)
isNormalById = defaultdict(lambda:False)
lastTimeById = {}

flows = NormalizedFeature("flows")
srcPorts = NormalizedFeature("srcPorts")
packets = NormalizedFeature("packets")
totalBytes = NormalizedFeature("totalBytes")
srcBytes = NormalizedFeature("srcBytes")
dstBytes = NormalizedFeature("dstBytes")
balanceRatio = NormalizedFeature("balanceRatio")
waitTime = NormalizedFeature("waitTime")
duration = NormalizedFeature("duration")

f=open(filename, 'r')
lines=itertools.imap(lambda i: i.strip().split(','), f)
lines=itertools.ifilter(lambda line: 'Background' not in line[LABEL], lines)
lines.next()
for line in lines:
  dport = line[DPORT] #if line[PROTO]!='icmp' else 0
  id = getIdByKey(line[PROTO], line[SRCADDR], line[DSTADDR], dport)
  isBotById[id]|= ( 'Bot' in line[LABEL] )
  isNormalById[id]|= ( 'Normal' in line[LABEL] )
  srcPortSetById[id].add(try_int(line[SPORT],0))
  flows.add_value(id, 1)
  duration.add_value(id, float(line[DUR]))
  packets.add_value(id, try_int(line[TOTPKTS], 0))
  total_bytes_i = try_int(line[TOTBYTES], 0)
  src_bytes_i = try_int(line[SRCBYTES], 0)
  dst_bytes_i = total_bytes_i - src_bytes_i
  
  totalBytes.add_value(id, math.log(total_bytes_i+1))
  srcBytes.add_value(id, math.log(src_bytes_i+1))
  dstBytes.add_value(id, math.log(dst_bytes_i+1))
  
  balanceRatio.add_value(id, 2.0*src_bytes_i/total_bytes_i-1.0)
  t = ts(line[STARTTIME])
  t0 = lastTimeById.get(id, None)
  lastTimeById[id] = t
  if t0:
    dt = t-t0
    waitTime.add_value(id, dt)

for id in keyById:
    # add distinct source ports count per flow
    srcPorts.add_value( id, len(srcPortSetById[id])/float(NormalizedFeature.count[id]['flows']) )

NormalizedFeature.calculate()

X = np.array( [ (
    flows.get_norm_count(i),
    srcPorts.get_norm_count(i),
    packets.get_norm_avg(i),
    packets.get_norm_var(i),
    totalBytes.get_norm_avg(i),
    totalBytes.get_norm_var(i),
    srcBytes.get_norm_avg(i),
    srcBytes.get_norm_var(i),
    dstBytes.get_norm_avg(i),
    dstBytes.get_norm_var(i),
    balanceRatio.get_norm_avg(i),
    balanceRatio.get_norm_var(i),
    waitTime.get_norm_avg(i),
    waitTime.get_norm_var(i),
    duration.get_norm_avg(i),
    duration.get_norm_var(i),
) for i in range(1, counter+1) ] )

from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

if alg=='pca':
    model = PCA(n_components=2, random_state=0)
    title = "PCA"
elif alg=='tsne':
    model = TSNE(n_components=2, random_state=0)
    title = "t-SNE"
else:
    raise ValueError("alg should be either tsne or pca")

X_ = model.fit_transform(X)

def getDetails(i):
    v=keyById[i+1]
    return "{} {}→{}:{}".format(*v)

out=open("data.js", "w")
out.write("var data={};\n")

out.write("data.none=[\n")
for i,j in enumerate(X_):
    if not isBotById[i+1] and not isNormalById[i+1]:
        out.write("{{ x:{}, y:{}, details: {} }},\n".format(j[0], j[1], json.dumps(getDetails(i)) ))
out.write("];\n")
out.write("data.both=[\n")
for i,j in enumerate(X_):
    if isBotById[i+1] and isNormalById[i+1]:
        out.write("{{ x:{}, y:{}, details: {} }},\n".format(j[0], j[1], json.dumps(getDetails(i)) ))
out.write("];\n")
out.write("data.normal=[\n")
for i,j in enumerate(X_):
    if not isBotById[i+1] and isNormalById[i+1]:
        out.write("{{ x:{}, y:{}, details: {} }},\n".format(j[0], j[1], json.dumps(getDetails(i)) ))
out.write("];\n")
out.write("data.botnet=[\n")
for i,j in enumerate(X_):
    if isBotById[i+1] and not isNormalById[i+1]:
        out.write("{{ x:{}, y:{}, details: {} }},\n".format(j[0], j[1], json.dumps(getDetails(i)) ))
out.write("];\n")
out.close()

import matplotlib.pyplot as plt
fig, ax = plt.subplots()

both=np.array([ j for i,j in enumerate(X_) if isBotById[i+1] and isNormalById[i+1] ])
normal=np.array([ j for i,j in enumerate(X_) if not isBotById[i+1] and isNormalById[i+1] ])
bot=np.array([ j for i,j in enumerate(X_) if isBotById[i+1] and not isNormalById[i+1] ])
none=np.array([ j for i,j in enumerate(X_) if not isBotById[i+1] and not isNormalById[i+1] ])

ax.plot(normal[:, 0], normal[:, 1], '+b', markersize=5, alpha=0.4, label="normal")
ax.plot(bot[:, 0], bot[:, 1], 'xr', markersize=5, alpha=0.4, label="botnet")
if both: ax.plot(both[:, 0], both[:, 1], '*g', markersize=5, alpha=0.4, label="both")
if none: ax.plot(none[:, 0], none[:, 1], '.y', markersize=5, alpha=0.4, label="other")
ax.legend()

ax.set_title(title_map[norm_alg].format(title))

plt.savefig("{}-{}.png".format(alg, norm_alg), dpi=150)
plt.savefig("{}-{}.svg".format(alg, norm_alg), dpi=150)
#plt.show()
