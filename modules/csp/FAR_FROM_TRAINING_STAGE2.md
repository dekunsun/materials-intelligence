# 外推检验第二阶段：Alexandria 外部数据（预登记）

> 状态（2026-11-25）：**预登记。** 本文件、抽样结果（`results/csp_far_stage2_20261125T1725Z/sample.csv`）和全部代码在任何模型对样本做预测之前提交到 git。之后的结果只能按这里的规则判定；任何改动都单独写成“偏离预登记”。第一阶段的设计和结果见 `FAR_FROM_TRAINING_TEST.md` 和 `results/csp_far_stage1_20261124T0908Z/`。

## 1. 为什么需要第二阶段

第一阶段在 WBM 上“成立”，但“远”是温和的远：候选都由元素替换生成，事后修正框架键后，结构外推格只有 30 个含稳定候选的框架。真正远离训练集的结构，需要外部数据。Alexandria 的结构外推格有 324 个含稳定候选的框架。

## 2. 数据和核对过的事实

数据：Alexandria PBE 2025.07.02，58 个分片加凸包文件，共 3.74 GB，CC BY 4.0，下载后每个文件的字节数和服务器列表一致。原始文件不提交，`data/raw/alexandria/MANIFEST.json` 记录每个文件的 SHA-256。

| 问题 | 核对结果 | 影响 |
|---|---|---|
| 字段 | 每个条目有 `e_above_hull`、`energy_total`（原始能量）、`energy_corrected`、来源路径（`location`）；`parameters` 是空的 | 真值用条目自带的凸包距离 |
| 修正方案 | MP **旧版**修正（纯氧化物每个 O −0.7023 eV） | 同一组成的模型能量和 DFT 能量修正相同，差值里抵消 |
| 原始能量能否和 MP 比 | 不加 U：中位差 0.95 meV/atom；加 U：中位差 5.1 meV/atom | **排除 GGA+U 体系**（含 Co、Cr、Fe、Mn、Mo、Ni、V、W 并含 O 或 F） |
| 来源 | m3gnet、orbital、cgat 等来源多半经过机器学习预筛 | 按来源分层（第 7 节） |
| 输入结构 | 只有 DFT 弛豫后的结构 | 模型从正确的几何出发，任务比第一阶段容易 |
| 和 WBM 重复 | 化学式、空间群、原子数都相同 | 排除 |
| 框架键 | spglib 自算，按第一阶段事后修正的方式规范化；和 MP 标签一致 99.4% | 约 0.6% 的标注误差 |

**全量数量**（共 5,777,914 个条目；排除 GGA+U 191,520 个、和 WBM 重复 230,202 个；真值为凸包距离 ≤ 0）：

| 格子 | 候选 | 稳定 | 含稳定候选的框架 |
|---|---|---|---|
| 插值 | 1,431,588 | 53,418 | 4,483 |
| 结构外推 | 97,442 | 1,874 | 324 |
| 化学外推 | 3,639,328 | 87,795 | 2,515 |
| 双重外推 | 194,687 | 2,233 | 340 |

结构外推格的稳定条目主要来自 orbital（665）、cgat_comp_2（600）、m3gnet（510）；去掉 m3gnet 和 orbital 后剩 699 个，127 个框架。数据见 `pool_summary.json`。

## 3. 定义

- **训练参照、化学轴：** 和第一阶段相同（MP 2023 快照；化学体系是否出现过）。
- **结构轴：** spglib 框架键，在空间群全部等价原点选择上规范化，MP 标签同样处理。
- **真值：** Alexandria 自带的 `e_above_hull` ≤ 0。它相对 Alexandria 自己的凸包，比 MP 的凸包更密，所以“稳定”的标准比第一阶段严。
- **模型的预测：** 从 DFT 弛豫后的结构出发，用模型弛豫（FIRE 加 FrechetCellFilter，力收敛 0.05 eV/Å，最多 500 步，和 Matbench Discovery 对这四个模型的设置相同）。预测凸包距离 = DFT 凸包距离 + (模型能量 − DFT 原始能量)/原子数。报错或能量非有限值记为失败，排在最后；500 步内没收敛不算失败，保留最后的能量。

## 4. 抽样（已完成，随机种子 11）

- 三个格子：插值、结构外推、双重外推。化学外推格不抽，第一阶段已回答得较好。
- 每个格子 **300 个稳定** 结构，和 **300 个不稳定** 结构：从凸包以上 (0, 0.025]、(0.025, 0.05]、(0.05, 0.075]、(0.075, 0.1] eV/atom 四个区间各抽 75 个。只用离凸包 0.1 eV/atom 以内的不稳定结构、并且每个区间数量相同，让三个格子的不稳定结构离凸包的远近分布一样，格子之间的差别就只来自模型误差。
- 插值格按结构外推格的元素数构成抽样（稳定、不稳定分别匹配）。
- 结果：每格 600 个，共 1,800 个。结构外推格的 300 个稳定结构分布在 90 个框架；去掉 m3gnet 和 orbital 后剩 110 个、39 个框架。双重外推格：300 个、88 个框架；去掉两个来源后 73 个、27 个框架。

## 5. 指标

- **Somers' D = 2 × AUC − 1：** 任取一个稳定、一个不稳定的结构，模型把稳定的排在前面的概率减去反过来的概率。随机为 0，全对为 1。它不受抽样改变的稳定比例影响，所以代替第一阶段的 R 精度。
- 因为不稳定结构都在凸包以上 0.1 eV/atom 以内，D 衡量的是：模型误差是否小到能分开离凸包很近的结构。
- **比值：** r = 外推格的 D / 插值格的 D。判定看四个模型 r 的中位数，以及四个模型在外推格 D 的中位数。
- **区间：** 按框架整群 bootstrap（外推格和插值格各自重抽），1,000 次，种子 11，取 95% 区间。
- **描述性，不影响判定：** 每个模型的 D 和 r；能量误差的中位绝对值；弛豫步数和未收敛比例；第一阶段数据上的 Somers' D。

## 6. 模型

只用 MPtrj 训练、权重公开、Matbench Discovery 里有设置的四个，在 Mac（Apple M3 Pro）CPU 上运行：

| 模型 | 软件包 | 权重 | 许可证 |
|---|---|---|---|
| CHGNet | chgnet 0.4.2 | 0.3.0 | BSD-3 |
| MACE-MP-0 | mace-torch 0.3.17 | 2023-12-03-mace-128-L1_epoch-199（medium），float64 | MIT |
| SevenNet-0 | sevenn 0.10.4 | SevenNet_0__11Jul2024 | GPL-3.0 |
| MatRIS-10M-MP | matris 1.0.0 | MatRIS_10M_MP.pth.tar（GitHub v1.0.0 发布） | 见其仓库 |

其他：torch 2.15.0、ase 3.29.0、e3nn 0.4.4。MatRIS 的权重来自软件包指定的 GitHub 发布，Matbench Discovery 列的是 figshare 链接，两者是否同一文件没有核实。它们不是第一阶段的前 10 名，所以第二阶段用这四个的中位数。

## 7. 判定规则

按顺序检查，结构外推格决定 D10：

| 顺序 | 结果 | 条件 |
|---|---|---|
| 1 | 样本不足 | 格子里稳定结构少于 50 个，或含稳定结构的框架少于 20 个 |
| 2 | 失败 | r 中位数的 95% 区间上限 < 0.5；或外推格 D 中位数的 95% 区间上限 < 0.2 |
| 3 | 成立 | r 中位数的 95% 区间下限 ≥ 0.8，并且外推格 D 中位数的 95% 区间下限 > 0.2 |
| 4 | 部分成立 | 其他情况 |

- **来源分层：** 主分析用全部来源。去掉 m3gnet 和 orbital（两个用机器学习势预筛的来源，和被测模型同类）后再算一遍。两者一个成立、一个失败，记为“部分成立”；其他情况以主分析为准（包括去掉来源后样本不足）。cgat 来源也经过机器学习预筛，但样本不够再去掉，只能写进局限。
- **双重外推格：** 同样计算和报告，不参与判定。
- **对 D10：** 第一、第二阶段都“成立”，更大规模的晶体筛选才从暂缓改为候选投入。
- **模型跑不完：** 如果某个模型无法跑完全部 1,800 个结构，用其余模型的中位数判定，并写成偏离预登记。
- 代码：`src/csp/far_stage2_decide.py`；边界测试在 `tests/check_far_stage2.py`，只用虚构数据。

## 8. 预登记前已经看到的东西

- 第一阶段的全部结果（成立；事后修正后结构格 r 0.908）。
- Alexandria 的字段、来源、全量和样本的数量和构成（上面的表）。没有任何模型对这些条目的预测。
- 为了估计 CPU 时间，四个模型各弛豫了 0 号分片的 20 个条目；这些能量没有和 DFT 比较，这 20 个条目都不在样本里。
- 看到全量数量后改过的设计：每格稳定结构从 200 改为 300、不稳定从 400 改为 300，原因是去掉两个来源后的检查需要足够的稳定结构；不稳定结构限制在凸包以上 0.1 eV/atom 以内、分四个区间，是在看到任何模型输出之前定的。
- D > 0.2 的门槛是新定的判断。

## 9. 计算

在 Mac CPU 上本地运行，不花钱。20 个结构的测时（每个模型 4 个线程）：CHGNet 约 1.0 秒/结构，MACE-MP-0 约 2.8 秒，SevenNet-0 约 6.3 秒，MatRIS-10M-MP 约 29 秒（峰值内存 12 GB，Mac 的 GPU 跑不了）。1,800 个结构估计：前三个模型合计约 5 小时，MatRIS 约 15 小时。测时样本小，而且一个 96 原子的结构占了 MatRIS 一半的时间，估计不精确。

## 10. 已知局限

- 输入是 DFT 弛豫后的结构，比从初始结构出发容易。
- 真值用的是 Alexandria 自己的凸包和 MP 旧版修正，和第一阶段的 MP2020 修正加 MP 凸包不同。
- 排除了 GGA+U 体系，不覆盖含过渡金属的氧化物和氟化物。
- 预测凸包距离里含有 DFT 真值，只有模型误差会打乱排序；所以 D 衡量的是“误差是否小于离凸包的距离”，不是从零开始的发现能力。
- 没有 Wrenformer 这类模板式基线，增量价值只能和随机比（D > 0.2）。
- 结构外推格的稳定结构多来自机器学习预筛的来源；分层只去掉了两个来源。
- 框架标签器和 MP 标签一致 99.4%，不是 100%。

## 11. 文件

`src/csp/far_stage2_pool.py`（给每个条目标格子）、`far_stage2_sample.py`（抽样）、`far_stage2_relax.py`（弛豫，在单独的环境 `data/raw/mlip_venv` 里运行）、`far_stage2_decide.py`（打分和判定）；`results/csp_far_stage2_20261125T1725Z/` 里的 `sample.csv`、`pool_summary.json`、`config.json`（数据和代码的 SHA-256、软件版本）。

---

# Extrapolation test, Stage 2: Alexandria external data (pre-registration)

> Status (2026-11-25): **pre-registration.** This file, the drawn sample (`results/csp_far_stage2_20261125T1725Z/sample.csv`) and all code are committed to git before any model predicts on the sample. Results are judged only by the rules here; any change is written up separately as a deviation. Stage 1's design and results: `FAR_FROM_TRAINING_TEST.md` and `results/csp_far_stage1_20261124T0908Z/`.

## 1. Why Stage 2

Stage 1 holds on WBM, but "far" there is mild: candidates come from element substitution, and after the post-hoc fix to the framework key the structural cell has only 30 frameworks with a stable candidate. Structures that are genuinely far from training need external data. Alexandria's structural cell has 324 frameworks with a stable candidate.

## 2. Data and facts checked

Data: Alexandria PBE 2025.07.02, 58 shards plus the hull file, 3.74 GB in all, CC BY 4.0; after download every file's byte count matched the server listing. Raw files are not committed; `data/raw/alexandria/MANIFEST.json` records each file's SHA-256.

| Question | What the check found | Consequence |
|---|---|---|
| Fields | Each entry has `e_above_hull`, `energy_total` (raw energy), `energy_corrected` and a source path (`location`); `parameters` is empty | The truth is the entry's own hull distance |
| Correction scheme | MP's **legacy** corrections (−0.7023 eV per O in pure oxides) | Model and DFT energies of the same composition get the same correction, which cancels in their difference |
| Raw energies vs MP | GGA: median difference 0.95 meV/atom; GGA+U: median 5.1 meV/atom | **Exclude GGA+U systems** (Co, Cr, Fe, Mn, Mo, Ni, V or W with O or F) |
| Sources | m3gnet, orbital, cgat and other sources were probably ML pre-screened | Stratify by source (Section 7) |
| Input structures | Only DFT-relaxed structures | Models start from the correct geometry, an easier task than Stage 1 |
| Overlap with WBM | Same formula, space group and number of sites | Excluded |
| Framework key | Computed with spglib, canonicalised as in Stage 1's post-hoc fix; agrees with MP's labels on 99.4% | About 0.6% labelling error |

**Full counts** (5,777,914 entries; 191,520 GGA+U and 230,202 WBM overlaps excluded; truth = hull distance ≤ 0):

| Cell | Candidates | Stable | Frameworks with a stable one |
|---|---|---|---|
| Interpolation | 1,431,588 | 53,418 | 4,483 |
| Structural extrapolation | 97,442 | 1,874 | 324 |
| Chemical extrapolation | 3,639,328 | 87,795 | 2,515 |
| Double extrapolation | 194,687 | 2,233 | 340 |

The structural cell's stable entries come mainly from orbital (665), cgat_comp_2 (600) and m3gnet (510); without m3gnet and orbital, 699 remain, in 127 frameworks. Details: `pool_summary.json`.

## 3. Definitions

- **Training reference and chemical axis:** as in Stage 1 (MP 2023 snapshot; whether the chemical system appears).
- **Structural axis:** the spglib framework key, canonicalised over all equivalent origin choices of the space group, applied the same way to MP's labels.
- **Truth:** Alexandria's own `e_above_hull` ≤ 0. It is relative to Alexandria's hull, which is denser than MP's, so "stable" is stricter than in Stage 1.
- **Model prediction:** start from the DFT-relaxed structure and relax with the model (FIRE with FrechetCellFilter, force tolerance 0.05 eV/Å, at most 500 steps, the settings Matbench Discovery uses for these four models). Predicted hull distance = DFT hull distance + (model energy − DFT raw energy)/atoms. An error or a non-finite energy is a failure, ranked last; not converging within 500 steps is not a failure, and the final energy is kept.

## 4. Sampling (done, seed 11)

- Three cells: interpolation, structural extrapolation and double extrapolation. The chemical cell is not sampled; Stage 1 answered it fairly well.
- Each cell: **300 stable** structures and **300 unstable** ones, 75 from each of the bins (0, 0.025], (0.025, 0.05], (0.05, 0.075] and (0.075, 0.1] eV/atom above the hull. Using only unstable structures within 0.1 eV/atom of the hull, in equal numbers per bin, gives the three cells the same distribution of distance above the hull, so differences between cells come only from model error.
- The interpolation cell matches the structural cell's mix of element counts (stable and unstable matched separately).
- Result: 600 per cell, 1,800 in all. The structural cell's 300 stable structures span 90 frameworks; without m3gnet and orbital, 110 in 39 frameworks. Double extrapolation: 300 in 88 frameworks; without the two sources, 73 in 27.

## 5. Metrics

- **Somers' D = 2 × AUC − 1:** the probability that a model ranks a random stable structure above a random unstable one, minus the reverse. Random scores 0 and perfect 1. It is unaffected by the stable share the sampling sets, so it replaces Stage 1's R-precision.
- Because every unstable structure is within 0.1 eV/atom of the hull, D measures whether the model's error is small enough to separate structures that sit close to the hull.
- **Ratio:** r = D in the extrapolation cell / D in the interpolation cell. The decision uses the median r of the four models, and the four models' median D in the extrapolation cell.
- **Intervals:** cluster bootstrap by framework (extrapolation and interpolation cells resampled separately), 1,000 resamples, seed 11, 95% intervals.
- **Descriptive, never decisive:** each model's D and r; the median absolute energy error; relaxation steps and the share not converged; Somers' D on the Stage 1 data.

## 6. Models

Four models trained only on MPtrj, with public weights and Matbench Discovery settings, run on a Mac (Apple M3 Pro) CPU:

| Model | Package | Weights | Licence |
|---|---|---|---|
| CHGNet | chgnet 0.4.2 | 0.3.0 | BSD-3 |
| MACE-MP-0 | mace-torch 0.3.17 | 2023-12-03-mace-128-L1_epoch-199 (medium), float64 | MIT |
| SevenNet-0 | sevenn 0.10.4 | SevenNet_0__11Jul2024 | GPL-3.0 |
| MatRIS-10M-MP | matris 1.0.0 | MatRIS_10M_MP.pth.tar (GitHub v1.0.0 release) | See its repository |

Also torch 2.15.0, ase 3.29.0, e3nn 0.4.4. MatRIS's weights come from the GitHub release the package points to; Matbench Discovery lists a figshare link, and whether the two are the same file is not verified. These are not Stage 1's top 10, so Stage 2 decides on these four's median.

## 7. Decision rules

Checked in order; the structural-extrapolation cell decides D10:

| Order | Outcome | Condition |
|---|---|---|
| 1 | Too small | Fewer than 50 stable structures in the cell, or fewer than 20 frameworks holding one |
| 2 | Fails | Upper bound of the 95% interval of the median r < 0.5; or upper bound of the 95% interval of the median D in the extrapolation cell < 0.2 |
| 3 | Holds | Lower bound of the 95% interval of the median r ≥ 0.8, and lower bound of the 95% interval of the median D in the extrapolation cell > 0.2 |
| 4 | Partial | Anything else |

- **Source strata:** the main analysis uses all sources. It is repeated without m3gnet and orbital (the two sources pre-screened with ML potentials, the same family as the models tested). If one holds and the other fails, the outcome is "partial"; otherwise the main analysis stands (including when the reduced sample is too small). The cgat sources were also ML pre-screened, but the sample is too small to drop them as well; this is listed as a limit.
- **Double extrapolation:** scored and reported the same way; does not decide.
- **D10:** larger-scale crystal screening moves from defer to candidate investment only if both Stage 1 and Stage 2 hold.
- **A model that cannot finish:** if a model cannot complete all 1,800 structures, the decision uses the remaining models' median and is written up as a deviation.
- Code: `src/csp/far_stage2_decide.py`; boundary tests on made-up data in `tests/check_far_stage2.py`.

## 8. What was seen before pre-registration

- All of Stage 1's results (holds; structural r 0.908 after the post-hoc fix).
- Alexandria's fields and sources, and the counts and composition of the full pool and of the sample (tables above). No model prediction on any of these entries.
- To estimate CPU time, each of the four models relaxed 20 entries of shard 0. Those energies were not compared with DFT, and none of the 20 entries is in the sample.
- Design changed after seeing the full counts: stable structures per cell from 200 to 300 and unstable from 400 to 300, because the check without the two sources needs enough stable structures. Limiting unstable structures to within 0.1 eV/atom of the hull, in four bins, was decided before any model output.
- The D > 0.2 threshold is a new judgement call.

## 9. Compute

Run locally on the Mac CPU at no cost. Timing on 20 structures (4 threads per model): CHGNet about 1.0 s per structure, MACE-MP-0 about 2.8 s, SevenNet-0 about 6.3 s, MatRIS-10M-MP about 29 s (peak memory 12 GB; it does not run on the Mac's GPU). Estimate for 1,800 structures: about 5 hours for the first three models together, about 15 hours for MatRIS. The timing sample is small, and one 96-atom structure accounts for half of MatRIS's time, so the estimate is rough.

## 10. Known limits

- Inputs are DFT-relaxed structures, which is easier than starting from initial structures.
- The truth uses Alexandria's own hull and MP's legacy corrections, unlike Stage 1's MP2020 corrections and MP hull.
- GGA+U systems are excluded, so transition-metal oxides and fluorides are not covered.
- The predicted hull distance contains the DFT truth, and only model error can disturb the ranking; D therefore measures whether the error is smaller than the distance to the hull, not discovery from scratch.
- There is no template-like baseline such as Wrenformer, so added value is judged only against random (D > 0.2).
- Most stable structures in the structural cell come from ML pre-screened sources; the stratification removes only two of them.
- The framework labeller agrees with MP's labels on 99.4% of structures, not 100%.

## 11. Files

`src/csp/far_stage2_pool.py` (labels every entry with its cell), `far_stage2_sample.py` (sampling), `far_stage2_relax.py` (relaxation, run in the separate environment `data/raw/mlip_venv`), `far_stage2_decide.py` (scoring and decision); in `results/csp_far_stage2_20261125T1725Z/`: `sample.csv`, `pool_summary.json` and `config.json` (SHA-256 of data and code, package versions).
