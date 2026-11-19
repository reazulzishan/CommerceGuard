"""Run notebook 02 headless (copy) and export the real curve data the video graphs draw from."""
import json, sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("curves.json")
nb = nbformat.read(ROOT / "notebooks/02_commerceguard_multimodel.ipynb", 4)
nb.cells.append(nbformat.v4.new_code_cell(f'''
import json, re
from sklearn.metrics import precision_recall_curve, average_precision_score
def pr(y, s, n=140):
    P, R, _ = precision_recall_curve(y, s)
    idx = np.unique(np.linspace(0, len(P) - 1, n).astype(int))
    return {{"recall": R[idx].round(4).tolist(), "precision": P[idx].round(4).tolist(), "ap": round(float(average_precision_score(y, s)), 3), "base": round(float(np.mean(y)), 3)}}
d = {{}}
d["m1"] = pr(rte["y"], ste); d["m1_bn"] = pr(rte["y"][bn_te], ste[bn_te])
for tgt, m in risk_models.items():
    te_ = pte if tgt == "y_cancel" else pte[pte.y_cancel == 0]
    s = cal[tgt].predict(m.predict_proba(te_[FEAT])[:, 1])
    d["m2_" + tgt] = pr(te_[tgt], s)
    q = pd.qcut(pd.Series(s).rank(method="first"), 10, labels=False)
    d["cal_" + tgt] = {{"pred": pd.Series(s).groupby(q.values).mean().round(3).tolist(), "actual": te_[tgt].reset_index(drop=True).groupby(q.values).mean().round(3).tolist()}}
imp = pd.Series(np.abs(sv).mean(0), index=FEAT).sort_values(ascending=False).head(8)
d["shap_cancel"] = [[k, round(float(v), 4)] for k, v in imp.items()]
k = np.unique(np.linspace(0, len(cum) - 1, 200).astype(int))
d["loss"] = {{"x": ((k + 1) / len(cum)).round(4).tolist(), "y": cum.values[k].round(4).tolist()}}
w = pd.Series(coef[wmask], index=names[wmask])
lat = w[[bool(re.fullmatch(r"[a-z ]{{3,}}", i)) for i in w.index]].sort_values()
d["words_unhappy"] = [[i, round(float(v), 2)] for i, v in lat.tail(8)[::-1].items()]
d["words_happy"] = [[i, round(float(v), 2)] for i, v in lat.head(8).items()]
json.dump(d, open(r"{OUT}", "w"))
print("exported", list(d))
'''))
NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
print(nb.cells[-1].outputs[-1].get("text", nb.cells[-1].outputs))
for c in nb.cells:
    if c.cell_type == "code" and "TEST" in c.source and c.outputs:
        print([o.get("text", "")[:200] for o in c.outputs if o.get("text")][:1])
