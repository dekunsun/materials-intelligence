# 外推检验第二阶段结果：Alexandria

> 预登记：`modules/csp/FAR_FROM_TRAINING_STAGE2.md`，提交 `c3f5fd2`，在任何模型对样本做预测之前推到 GitHub。打分代码：`src/csp/far_stage2_decide.py`（预登记时的版本）。描述性数字：`src/csp/far_stage2_describe.py`（预登记第 5 节列出的项目，代码在看到结果之前写好）。

## 结论

**预登记的判定：成立。** 在结构类型 MP 里没有、化学体系 MP 里有的 Alexandria 结构上（结构外推格），四个只用 MPtrj 训练的模型把稳定和不稳定结构分开的能力，是插值格的 0.97 倍（四个模型的中位数；95% 区间 0.80–1.19）。区间下限 0.804，刚过 0.8 的门槛。去掉两个用机器学习势预筛的来源后，也成立（0.95，0.83–1.14）。

按预登记的规则，第一、第二阶段都成立，D10（更大规模的晶体筛选算力）从“暂缓”改为“候选投入”。

## 主要数字

Somers' D：任取一个稳定、一个不稳定的结构，模型把稳定的排在前面的概率减去反过来的概率；随机为 0，全对为 1。不稳定结构都在凸包以上 0.1 eV/atom 以内。

| 分析 | 格子 | 判定 | 稳定结构 / 框架 | r 中位数（95% 区间） | 外推格 D 中位数（95% 区间） |
|---|---|---|---|---|---|
| 全部来源 | 结构外推（决定 D10） | **成立** | 300 / 90 | 0.97（0.80–1.19） | 0.58（0.49–0.68） |
| 全部来源 | 双重外推（不参与判定） | 部分成立 | 300 / 88 | 0.91（0.77–1.06） | 0.51（0.43–0.61） |
| 去掉 m3gnet、orbital | 结构外推 | 成立 | 110 / 39 | 0.95（0.83–1.14） | 0.60（0.51–0.73） |
| 去掉 m3gnet、orbital | 双重外推 | 部分成立 | 73 / 27 | 0.72（0.49–0.95） | 0.42（0.28–0.60） |

每个模型的 D（全部来源）：

| 模型 | 插值 | 结构外推 | 双重外推 | 能量误差中位绝对值，插值 / 结构外推 / 双重外推（meV/atom） |
|---|---|---|---|---|
| CHGNet | 0.26 | 0.31 | 0.35 | 37 / 26 / 39 |
| MACE-MP-0 | 0.56 | 0.54 | 0.44 | 13 / 14 / 21 |
| SevenNet-0 | 0.65 | 0.62 | 0.58 | 10 / 11 / 15 |
| MatRIS-10M-MP | 0.82 | 0.77 | 0.76 | 5 / 6 / 8 |

## 怎么读

1. **结构陌生、化学熟悉时，模型基本保住了区分能力。** 四个模型在结构外推格的 D 都和插值格接近；比值的中位数 0.97。这和第一阶段（WBM，事后修正后 0.91）方向一致，而这里的结构类型数多得多（含稳定结构的框架 90 个，第一阶段 30 个）。
2. **两个维度都陌生时，开始下降。** 双重外推格判为部分成立；去掉两个来源后，MACE-MP-0 和 SevenNet-0 的比值降到 0.62；全部来源下，两者在双重外推格的能量误差约是插值格的 1.5 倍。这一格不参与判定，但它说明“远”的代价主要出现在化学和结构同时陌生的时候。
3. **模型之间的差别比格子之间的差别大。** 同一个格子里，D 从 CHGNet 的 0.26–0.35 到 MatRIS 的 0.76–0.82。选哪个模型，对能否分开离凸包很近的结构影响更大。
4. **CHGNet 的比值大于 1 不代表外推更好。** 它在插值格的 D 只有 0.26，分母小，比值不稳定；判定用中位数，受它影响小。

## 偏离预登记和需要说明的事

- **一个结构弛豫失败：** MatRIS-10M-MP 在一个 160 原子的结构（插值格，稳定）上两次因内存不足被系统终止（峰值约 39 GB，Mac 有 18 GB）。按预登记规则记为失败、排在最后。去掉这个结构重算，结构外推格 r 0.97（0.81–1.20），仍然成立。其他 7,199 次弛豫没有失败；CHGNet 有 3 次 500 步内没收敛，按规则保留最后的能量。
- **运行中断和 `--exclude`：** MatRIS 的运行中途被会话结束打断一次，弛豫脚本按设计从断点续跑。为了先跑完其余结构，弛豫脚本在预登记之后加了一个 `--exclude` 选项，只影响运行顺序，不改变任何结构的计算方式或结果。
- **描述性脚本：** `far_stage2_describe.py` 在预登记之后、看到结果之前写成，只计算预登记第 5 节列出的描述性数字。在第一阶段数据上，Somers' D 给出的结构外推比值是 0.91，和第一阶段 R 精度的结果（0.908）一致。

## 局限（和预登记第 10 节相同，这里重点列出）

- 区间下限 0.804 刚过门槛；第一阶段修正后的下限 0.81 也一样。两个阶段都“成立”，但都不是大幅超过。
- 输入是 DFT 弛豫后的结构，比从初始结构出发容易。
- 预测凸包距离里含有 DFT 真值，D 衡量的是误差是否小于离凸包的距离，不是从零开始的发现能力。
- 没有模板式基线，增量价值只能和随机比（D > 0.2）；第一阶段里模板式基线 Wrenformer 在结构外推格明显下降。
- 排除了 GGA+U 体系，不覆盖含过渡金属的氧化物和氟化物。
- 结构外推格的稳定结构多来自机器学习预筛的来源（orbital、cgat_comp_2、m3gnet）；分层只去掉了两个。
- 一台 Mac CPU，四个模型；不是第一阶段的前 10 名。

## 文件

`decision.json`（判定）、`per_model_cells.csv`（每个模型的 D 和 r）、`descriptive.json`（能量误差、步数、第一阶段的 Somers' D）、`predictions/`（四个模型对 1,800 个结构的能量）、`sample.csv`、`pool_summary.json`、`config.json`。

---

# Extrapolation test, Stage 2 results: Alexandria

> Pre-registration: `modules/csp/FAR_FROM_TRAINING_STAGE2.md`, commit `c3f5fd2`, pushed to GitHub before any model predicted on the sample. Scoring code: `src/csp/far_stage2_decide.py` (as pre-registered). Descriptive numbers: `src/csp/far_stage2_describe.py` (the items listed in Section 5 of the pre-registration; the code was written before the results were seen).

## Conclusion

**Pre-registered outcome: holds.** On Alexandria structures whose framework is absent from MP but whose chemical system is present (the structural-extrapolation cell), four MPtrj-only models separate stable from unstable structures 0.97 times as well as in the interpolation cell (median of the four models; 95% interval 0.80–1.19). The lower bound, 0.804, is just above the 0.8 threshold. Without the two sources pre-screened with ML potentials it also holds (0.95, 0.83–1.14).

By the pre-registered rule, Stage 1 and Stage 2 both hold, so D10 (larger-scale crystal screening compute) moves from "defer" to "candidate investment".

## Main numbers

Somers' D: the probability that a model ranks a random stable structure above a random unstable one, minus the reverse; random scores 0 and perfect 1. All unstable structures are within 0.1 eV/atom of the hull.

| Analysis | Cell | Outcome | Stable structures / frameworks | Median r (95% interval) | Median D in the cell (95% interval) |
|---|---|---|---|---|---|
| All sources | Structural extrapolation (decides D10) | **Holds** | 300 / 90 | 0.97 (0.80–1.19) | 0.58 (0.49–0.68) |
| All sources | Double extrapolation (does not decide) | Partial | 300 / 88 | 0.91 (0.77–1.06) | 0.51 (0.43–0.61) |
| Without m3gnet, orbital | Structural extrapolation | Holds | 110 / 39 | 0.95 (0.83–1.14) | 0.60 (0.51–0.73) |
| Without m3gnet, orbital | Double extrapolation | Partial | 73 / 27 | 0.72 (0.49–0.95) | 0.42 (0.28–0.60) |

Each model's D (all sources):

| Model | Interpolation | Structural extrapolation | Double extrapolation | Median absolute energy error, interpolation / structural / double (meV/atom) |
|---|---|---|---|---|
| CHGNet | 0.26 | 0.31 | 0.35 | 37 / 26 / 39 |
| MACE-MP-0 | 0.56 | 0.54 | 0.44 | 13 / 14 / 21 |
| SevenNet-0 | 0.65 | 0.62 | 0.58 | 10 / 11 / 15 |
| MatRIS-10M-MP | 0.82 | 0.77 | 0.76 | 5 / 6 / 8 |

## Reading it

1. **With an unfamiliar framework but familiar chemistry, the models largely keep their ability to separate.** All four models' D in the structural cell is close to their interpolation D; the median ratio is 0.97. This agrees in direction with Stage 1 (WBM, 0.91 after the post-hoc fix), on far more frameworks (90 with a stable structure, against 30 in Stage 1).
2. **When both axes are unfamiliar, it starts to drop.** The double-extrapolation cell is partial; without the two sources, MACE-MP-0's and SevenNet-0's ratios fall to 0.62, and with all sources their energy errors in the double cell are about 1.5 times those in interpolation. This cell does not decide, but it shows that the cost of "far" appears mainly when chemistry and structure are unfamiliar together.
3. **Differences between models are larger than differences between cells.** In the same cell, D ranges from CHGNet's 0.26–0.35 to MatRIS's 0.76–0.82. The choice of model matters more for separating structures close to the hull.
4. **CHGNet's ratio above 1 does not mean it extrapolates better.** Its interpolation D is only 0.26, so the ratio has a small denominator and is unstable; the decision uses the median, which it barely moves.

## Deviations and disclosures

- **One failed relaxation:** MatRIS-10M-MP was killed twice by the system for running out of memory on one 160-atom structure (interpolation cell, stable; peak about 39 GB on an 18 GB Mac). By the pre-registered rule it is a failure, ranked last. Without that structure, the structural cell's r is 0.97 (0.81–1.20), still holding. None of the other 7,199 relaxations failed; CHGNet did not converge within 500 steps 3 times, and by the rule the final energy was kept.
- **An interrupted run and `--exclude`:** MatRIS's run was interrupted once when the session ended, and the relaxation script resumed from where it stopped, as designed. To finish the other structures first, an `--exclude` option was added to the relaxation script after pre-registration; it changes only the order of the run, not how any structure is computed or its result.
- **Descriptive script:** `far_stage2_describe.py` was written after pre-registration and before the results were seen, and computes only the descriptive numbers listed in Section 5 of the pre-registration. On the Stage 1 data, Somers' D gives a structural ratio of 0.91, matching Stage 1's R-precision result (0.908).

## Limits (as in Section 10 of the pre-registration; the main ones)

- The lower bound, 0.804, is just above the threshold; so is Stage 1's corrected lower bound, 0.81. Both stages hold, but neither by a wide margin.
- Inputs are DFT-relaxed structures, which is easier than starting from initial structures.
- The predicted hull distance contains the DFT truth, so D measures whether the error is smaller than the distance to the hull, not discovery from scratch.
- There is no template-like baseline, so added value is judged only against random (D > 0.2); in Stage 1 the template-like baseline Wrenformer dropped clearly in the structural cell.
- GGA+U systems are excluded, so transition-metal oxides and fluorides are not covered.
- Most stable structures in the structural cell come from ML pre-screened sources (orbital, cgat_comp_2, m3gnet); the stratification removes only two of them.
- One Mac CPU and four models, which are not Stage 1's top 10.

## Files

`decision.json` (the decision), `per_model_cells.csv` (each model's D and r), `descriptive.json` (energy errors, steps, Somers' D on Stage 1), `predictions/` (the four models' energies on 1,800 structures), `sample.csv`, `pool_summary.json`, `config.json`.
