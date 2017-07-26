# FlowVis
Visualize netflows using t-SNE

## Input

Prepare you netflows in the form of CSV having the following columns

```
StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label
```

If you don't have labels put any thing as last column like `NA` or `OTHER` or `None`

You can use any file that have the above format like 

* [CTU-Malware-Capture-Botnet-46 or Scenario 5 in the CTU-13 dataset.](https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-46/detailed-bidirectional-flow-labels/capture20110815-2.binetflow)

## Usage


```
python flowvis.py [pca|tsne] [id|tanh|range|std] inputfile.csv
```

we recommend using `tsne` and `tanh` (other methods are used for comparison)

```
python flowvis.py tsne tanh inputfile.csv
```

this would output resulted images and `data.js` which can be viewed using `flowvis.html`

## Results

![results](/results/tsne-tanh.png)


