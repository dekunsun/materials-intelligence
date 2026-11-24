# 稳定性筛选的外推检验（设计稿，尚未运行）

> 状态（2026-11-24）：本文在运行前提交（commit `ffdb574`）。**第一阶段已完成：三个外推格都“成立”**，结果见 `results/csp_far_stage1_20261124T0908Z/report.md`；D10 按规则不变。第二阶段尚未开始。以下是运行前的原文。
>
> 原状态：只有设计，没有跑任何模型，也没有在本文定义的格子里算任何模型指标。本文定稿后、算任何分组指标之前，会把本文、划分脚本和判定脚本提交到 git，作为预登记。第二阶段要下载外部数据、在本机 CPU 上跑模型，开始前单独确认，并另写一份第二阶段的预登记。

## 1. 问题

**AI 模型能不能可靠地挑出热力学稳定、并且在结构上远离自身训练数据的候选？**

- CSP 随机移除对照（`RANDOM_REMOVAL_CONTROL.md`）说明：EquiCSP 对 11 个目标的结构恢复，依赖训练集里被移除的钙钛矿框架。那是生成模型的结构预测。
- 这里问的是另一类模型的另一件事：通用势函数等能量模型给出的稳定性判断，离开训练数据之后还靠不靠得住。
- 它决定看板上的 D10（更大规模的晶体筛选算力，现为暂缓）。D10 的继续条件是“离已知原型更远的测试集上，模型仍有区分和增量价值”，停止条件是“模型在那里和模板一样失败”。稳定性筛选里没有直接对应的模板方法，本文用 Wrenformer 代替（第 3 节）。

## 2. 两个距离轴，四个格子

距离都相对于训练集来量，都在**弛豫前**的结构上算（筛选时就能知道）。

| | 框架已知 | 框架陌生 |
|---|---|---|
| **化学组成熟悉** | 插值 | 结构外推 |
| **化学组成陌生** | 化学外推 | 双重外推 |

**化学轴（C1）。** 候选的化学体系（元素集合）在训练参照里出现过至少一次，记为熟悉；否则陌生。这是比较温和的化学外推：在 WBM 里，含有训练集里从没同时出现过的元素对的候选只有几百个，不单独判定。

**结构轴（S2，判定用）。** 框架键 = Pearson 符号 + 空间群 + 全部 Wyckoff 位置的多重集，不管哪个位点放哪种元素。框架键在训练参照里出现过至少一次，记为已知；否则陌生。

- 不用原型标签本身（S1）做判定，是因为可行性检查发现：WBM 里 S1 陌生的候选有 71% 只是已知框架换了元素分组，几何上并不新。
- 只作描述、不参与判定的另几种定义：弛豫后结构的 S2；S1。与训练结构的最近邻指纹距离（S3）要给全部参照结构算指纹，放到第二阶段。

**训练参照。** MP 2023-02-07 快照（154,718 个编号；Matbench Discovery 里叫 MP 2022），框架键来自 `mp_energies.csv.gz` 的 `protostructure_spglib`，和 WBM 用同一个标签器（spglib）。
- 只在 MP 数据上训练的模型，训练集是 MPtrj（145,923 种材料，本地核对过）或其他 MP 版本。2026-11-24 已核对：MPtrj 里不在这个快照中的编号有 1,085 个（0.74%），低于事先定的 1%，所以参照只用这个快照，不再给这些结构补标签。
- 基线模型 Wrenformer 和 Voronoi RF 的训练集就是这个 MP 2022 快照。势函数模型的训练集 MPtrj 来自更早的 MP 版本；共用这个参照，是偏保守的做法：宁可把候选算成“熟悉”。

## 3. 模型和基线

- **判定用的模型：** 本仓库重新计分结果（`results/csp_screening_20261121T192919Z/model_metrics.csv`）里，只在 MP 数据上训练的模型，按唯一原型上的 F1（`f1_uniq`）取前 10 名，同分按名字排序。
- **固定的“头部模型”：** 上面排第 1 的模型（EquiformerV3+DeNS-MP）。在格子里不重新挑最好的，避免“赢家诅咒”。
- **只报告、不判定：** CHGNet、MACE-MP-0 两个老一代模型；用了 OMat24、sAlex、Alexandria 的模型。后者的训练集离 WBM 多远没法逐结构核对，只知道 sAlex 构建时按原型标签去掉了与 WBM 初始、弛豫结构相同的条目（[OMat24 论文](https://arxiv.org/abs/2410.12771) 4.3 节）。
- **基线：** Wrenformer（只看组成和 Wyckoff 原型，最接近模板方法；唯一原型上的 F1 0.47）；随机（即格子的稳定比例）。Voronoi RF（唯一原型上的 F1 0.33）太弱，只作描述。

## 4. 第一阶段：WBM，不需要计算

用已下载的 WBM 摘要和已公开的逐结构预测，在四个格子里打分。

**候选池：** 完整 WBM（256,963 个）。只保留唯一原型的过滤会在重复结构里留下 DFT 能量最低的那个，等于按真值挑候选，所以只作敏感性检查。缺预测的结构排在最后。

可行性检查（只数了候选、稳定数和框架数，没有算模型指标；参照为 MP 2023 快照）：

| 完整 WBM | 候选数 | DFT 稳定 | 稳定比例 | 框架数 | 含稳定候选的框架数 |
|---|---|---|---|---|---|
| 插值 | 140,322 | 22,394 | 16.0% | 1,232 | 765 |
| 结构外推 | 1,109 | 167 | 15.1% | 74 | 37 |
| 化学外推 | 114,879 | 20,144 | 17.5% | 806 | 509 |
| 双重外推 | 653 | 120 | 18.4% | 51 | 25 |

- 化学轴样本充足；结构轴很薄，两个结构格子各只有几十个框架。“新”框架多数来自 WBM 第 3 轮的替换（两个结构格子合计 1,762 个里有 1,103 个，而第 3 轮只占全部 WBM 的 31%），母结构是前几轮弛豫出来的 WBM 结构。
- 格子之间的元素数构成不同：插值格二元占 22%，化学外推格四元占 24%。稳定比例也随元素数变化。

**所以第一阶段对化学外推回答得比较可靠，对结构外推只是初步答案。**

## 5. 指标

- **R 精度：** 在一个格子里，取模型预测最稳定的 k 个候选，k 等于格子里 DFT 稳定的候选数，算其中真正稳定的比例。
- **归一化分数：** NRp = (R 精度 − p) / (1 − p)，p 是格子的稳定比例。随机挑是 0，全对是 1。这样稳定比例不同的格子可以比较。
- **插值参照：** 每个外推格都和插值格比，但插值格按这个外推格的元素数构成重新加权（按二元、三元、四元、五元分层计算 R 精度和 p，再按外推格的构成加权）。
- **比值：** 每个模型的 r = 外推格 NRp / 插值参照 NRp。判定看 10 个模型的 r 的中位数。
- **增量价值：** d = 头部模型的 NRp − Wrenformer 的 NRp，在同一格子里配对计算。
- **区间：** 按框架键做整群 bootstrap（每个格子内部重抽框架，1,000 次，种子 11）。

## 6. 判定规则（预登记，按顺序检查）

D10 由**结构外推格**判定。双重外推格和化学外推格用同样的规则报告，用来区分“化学外推难”还是“结构外推难”，不直接改 D10。

| 顺序 | 结果 | 条件 |
|---|---|---|
| 1 | 样本不足 | 格子里 DFT 稳定的候选少于 50 个，或含稳定候选的框架少于 20 个：只描述，不判定 |
| 2 | 失败 | r 中位数的 95% 区间上限 < 0.5；或 d 的 95% 区间上限 < 0.10 |
| 3 | 成立 | r 中位数的 95% 区间下限 ≥ 0.8，并且 d 的 95% 区间下限 > 0.10 |
| 4 | 部分成立 | 其他情况 |

- 0.8、0.5、0.10 这三个数是判断，不是从数据推出来的；在看到任何分组指标之前写下，不再改。
- **对 D10 的影响：** 只有第一阶段的结果时，D10 不改，只更新证据。第一、第二阶段都“成立”，更大规模的晶体筛选才从暂缓改为候选投入；任一阶段“失败”，继续暂缓，并把“AI 能挑出新结构里的稳定候选”限定在已知原型附近。

**只作描述的敏感性检查**（判定之后另写脚本计算，不影响判定）：唯一原型候选池；按化学体系整群；弛豫后结构的 S2；S1；逐个去掉一个框架后结果的范围；Voronoi RF 基线；CHGNet 和 MACE-MP-0。

## 7. 第二阶段：外部数据（另行确认，另写预登记）

第二阶段的细节要等确认数据字段之后才能定，这里只先定原则：

- **数据：** Alexandria PBE 数据库（CC BY 4.0）。取框架键不在训练参照里、也不在 WBM 里的条目，并在同一数据库里定义自己的插值格作参照。
- **筛选偏差：** Alexandria 2025 年新增的约 130 万个条目，用 Matra-Genoa 生成、再经 Orb-v2 和 ALIGNN 筛选后才算 DFT（[arXiv:2512.09169](https://arxiv.org/abs/2512.09169)）。较早的条目是否也经过机器学习预筛，**还没有核实**。每个条目尽量记下来源批次，分层报告。
- **能量一致性：** 先下载一个分片（约 62 MB）确认字段、赝势和 U 值。确认和 MP 一致后，用 MP2020 修正，相对 MP 2023 快照的凸包计算稳定性，和第一阶段同一个参照；加入 Alexandria 的更密凸包只作敏感性检查。
- **抽样：** 格子内按自然比例随机抽样，不把稳定和不稳定配成对半；目标约 2,000 个结构。
- **模型：** 3–4 个只用 MPtrj 训练、权重公开的模型（例如 CHGNet、MACE-MP-0、SevenNet-0、MatRIS-10M-MP）。它们不是第一阶段的前 10 名，所以第二阶段的判定用这几个模型自己的中位数，报告时写明两阶段的模型不同。
- **弛豫：** 和 Matbench Discovery 的设置一致（优化器、晶胞过滤、力收敛标准、步数上限，从固定版本的代码里读出来）；弛豫失败记为缺预测，排在最后。先每个模型跑 20 个结构测时间，报告 CPU 小时数再决定。
- **不用的数据：** GNoME（只有稳定结构，无法估计精度；许可 CC BY-NC）；MP 2024 年后加入的 GNoME 条目（r2SCAN，和 PBE 不可比）；OQMD（DFT 设置和 MP 不同）。

## 8. 能回答什么，不能回答什么

- **能回答：** 在 DFT 真值下，只用 MP 数据训练的模型挑稳定候选的能力，在化学和结构两个方向上分别掉多少。第一阶段只针对“由元素替换生成”的候选。
- **不能回答：**
  - 用了 OMat24、Alexandria 的大模型，在真正陌生的结构上表现如何。它们的训练集太大，逐结构核对不了。
  - DFT 稳定的候选能不能合成。真值仍然是 DFT。
  - 生成模型能不能产生这些结构。这是 CSP 的问题，见随机移除对照。

## 9. 已经看过的东西（如实说明）

- D2A（`results/csp_screening_20261121T192919Z/boundaries.csv`）已经算过各模型在“S1 弛豫前标签陌生”那一组（4,255 个唯一原型）上的精度、召回率和 F1，报告里写过“前 10 名召回率低 1–4 个百分点”。本文结构格子是那一组的子集，而且 S2 是在看过那些结果之后才定为判定定义的。
- 写本文时还看过各格子的候选数、稳定比例和元素数构成（第 4 节）。
- 在本文定义的格子里，没有算过任何模型指标。

## 10. 顺序和花费

1. 把本文、划分脚本（`src/csp/far_split.py`）、判定脚本（`src/csp/far_decide.py`）和它们的检查（`tests/check_far_decide.py`）提交到 git（预登记），再算任何分组指标。判定用的 10 个模型由脚本从固定文件里选出：EquiformerV3+DeNS-MP（头部模型）、DPA-4.0.1-Pro-MPtrj、DPA-4.0-Pro-MPtrj、MatRIS-10M-MP、eSEN-30M-MP、eqV2 S DeNS、MatRIS v0.5.0 MPtrj、DPA-3.1-MPtrj、AlphaNet-v1-MPtrj、Eqnorm MPtrj。
2. 第一阶段：不花钱，本机几分钟。
3. 下载 Alexandria 一个分片，确认字段（约 62 MB，需要确认）。
4. 写第二阶段的预登记；完整下载约 3.8 GB（58 个分片加凸包文件）；先测时间、报告 CPU 小时数，确认后再跑。没有付费算力。

---

# Extrapolation test for stability screening (design, not yet run)

> Status (2026-11-24): this document was committed before the run (commit `ffdb574`). **Stage 1 is done: all three extrapolation cells hold**; see `results/csp_far_stage1_20261124T0908Z/report.md`. D10 is unchanged by rule. Stage 2 has not started. The original text follows.
>
> Original status: design only. No model has been run, and no model metric has been computed in the cells this document defines. Once the text is settled, and before any per-cell metric is computed, this document, the split script and the decision script will be committed to git as the pre-registration. Stage 2 needs an external download and CPU runs on the Mac; it will be confirmed separately and get its own pre-registration.

## 1. Question

**Can AI models reliably identify thermodynamically stable candidates that are structurally distant from their training data?**

- The CSP random-removal control (`RANDOM_REMOVAL_CONTROL.md`) showed that EquiCSP's structure recovery on 11 targets depends on the removed perovskite frameworks in its training set. That is structure prediction by a generative model.
- This test asks something else, about other models: whether the stability judgements of energy models such as universal interatomic potentials still hold once candidates leave the training data.
- It decides D10 on the board (larger-scale crystal screening compute, currently deferred). D10's continue condition is "on a test set further from known prototypes, models still separate and add value"; its stop condition is "models fail there as badly as templates". Stability screening has no direct template method, so this document uses Wrenformer in its place (Section 3).

## 2. Two distance axes, four cells

Both distances are measured against the training reference, on the **initial (pre-relaxation)** structures, so they are known at screening time.

| | Known framework | Unfamiliar framework |
|---|---|---|
| **Familiar chemistry** | Interpolation | Structural extrapolation |
| **Unfamiliar chemistry** | Chemical extrapolation | Double extrapolation |

**Chemical axis (C1).** A candidate's chemical system (its set of elements) is familiar if it appears at least once in the training reference, and unfamiliar otherwise. This is a mild form of chemical extrapolation: in WBM only a few hundred candidates contain an element pair that never appears together in training, and those are not decided separately.

**Structural axis (S2, used for the decision).** The framework key is the Pearson symbol, the space group and the multiset of all Wyckoff positions, regardless of which element sits on which site. A framework is known if its key appears at least once in the training reference, and unfamiliar otherwise.

- The prototype label itself (S1) is not used for the decision. The feasibility check found that 71% of WBM's S1-unfamiliar candidates are known frameworks with a different grouping of sites into elements, so they are not new geometry.
- Descriptive only, not used for the decision: S2 on the relaxed structure, and S1. The nearest-neighbour fingerprint distance to training structures (S3) needs fingerprints for every reference structure and moves to Stage 2.

**Training reference.** The MP 2023-02-07 snapshot (154,718 IDs; Matbench Discovery calls it MP 2022). Framework keys come from `protostructure_spglib` in `mp_energies.csv.gz`, with the same labeller (spglib) as WBM.
- Models trained on MP data alone used MPtrj (145,923 materials, checked locally) or another MP release. Checked on 2026-11-24: 1,085 MPtrj IDs (0.74%) are not in the snapshot, below the 1% set in advance, so the reference is the snapshot alone and those structures are not labelled.
- The baselines Wrenformer and Voronoi RF were trained on exactly this MP 2022 snapshot. The interatomic potentials' training set, MPtrj, comes from an earlier MP release; sharing this reference is conservative, erring towards counting a candidate as familiar.

## 3. Models and baselines

- **Models for the decision:** in this repository's re-score (`results/csp_screening_20261121T192919Z/model_metrics.csv`), the top 10 models trained on MP data alone, ranked by F1 on unique prototypes (`f1_uniq`), with ties broken by name.
- **Fixed "lead model":** the rank-1 model above (EquiformerV3+DeNS-MP). The best model is not re-picked within a cell, to avoid the winner's curse.
- **Reported, not decided:** two older models, CHGNet and MACE-MP-0; and models that also used OMat24, sAlex or Alexandria. How far WBM is from the latter's training data cannot be checked structure by structure. What is known is that sAlex was built by removing entries whose prototype labels matched WBM's initial or relaxed structures ([OMat24 paper](https://arxiv.org/abs/2410.12771), Section 4.3).
- **Baselines:** Wrenformer (composition and Wyckoff prototype only, the closest stand-in for a template method; F1 0.47 on unique prototypes) and random (the cell's stable share). Voronoi RF (F1 0.33 on unique prototypes) is too weak and is described only.

## 4. Stage 1: WBM, no compute

Score the four cells using the downloaded WBM summary and the published per-structure predictions.

**Candidate pool:** the full WBM set (256,963). The unique-prototype filter keeps the duplicate with the lowest DFT energy, which selects on the truth, so it is a sensitivity check only. Structures without a prediction are ranked last.

Feasibility check (counts of candidates, stable structures and frameworks only, no model metric; reference: the MP 2023 snapshot):

| Full WBM | Candidates | DFT-stable | Stable share | Frameworks | Frameworks with a stable candidate |
|---|---|---|---|---|---|
| Interpolation | 140,322 | 22,394 | 16.0% | 1,232 | 765 |
| Structural extrapolation | 1,109 | 167 | 15.1% | 74 | 37 |
| Chemical extrapolation | 114,879 | 20,144 | 17.5% | 806 | 509 |
| Double extrapolation | 653 | 120 | 18.4% | 51 | 25 |

- The chemical axis has plenty of data. The structural axis is thin: each structural cell has only a few dozen frameworks. Most "new" frameworks come from WBM's third substitution round (1,103 of the 1,762 in the two structural cells, against 31% of all WBM), whose parents were WBM structures relaxed in earlier rounds.
- The cells differ in element-count mix: binaries are 22% of the interpolation cell, and quaternaries 24% of the chemical-extrapolation cell. The stable share also varies with element count.

**So Stage 1 answers chemical extrapolation fairly reliably and gives only a first answer on structural extrapolation.**

## 5. Metrics

- **R-precision:** in a cell, take the k candidates a model predicts to be most stable, with k equal to the number of DFT-stable candidates in the cell, and compute the share that is truly stable.
- **Normalised score:** NRp = (R-precision − p) / (1 − p), where p is the cell's stable share. A random pick scores 0 and a perfect one 1, so cells with different stable shares can be compared.
- **Interpolation reference:** each extrapolation cell is compared with the interpolation cell, reweighted to that extrapolation cell's element-count mix. R-precision and p are computed in strata of binaries, ternaries, quaternaries and quinaries, then weighted by the extrapolation cell's mix.
- **Ratio:** for each model, r = extrapolation-cell NRp / interpolation-reference NRp. The decision uses the median r of the 10 models.
- **Added value:** d = the lead model's NRp − Wrenformer's NRp, paired within the same cell.
- **Intervals:** cluster bootstrap by framework key (frameworks resampled within each cell, 1,000 resamples, seed 11).

## 6. Decision rules (pre-registered, checked in order)

D10 is decided by the **structural-extrapolation cell**. The double-extrapolation and chemical-extrapolation cells are reported under the same rules to separate "chemical extrapolation is hard" from "structural extrapolation is hard"; they do not change D10 directly.

| Order | Outcome | Condition |
|---|---|---|
| 1 | Too small | Fewer than 50 DFT-stable candidates in the cell, or fewer than 20 frameworks containing a stable candidate: described, not decided |
| 2 | Fails | Upper bound of the 95% interval of the median r < 0.5; or upper bound of the 95% interval of d < 0.10 |
| 3 | Holds | Lower bound of the 95% interval of the median r ≥ 0.8, **and** lower bound of the 95% interval of d > 0.10 |
| 4 | Partial | Anything else |

- The thresholds 0.8, 0.5 and 0.10 are judgement calls, not derived from data. They are written before any per-cell metric is seen and will not change.
- **Effect on D10:** with Stage 1 results only, D10 does not change; only the evidence is updated. Larger-scale crystal screening moves from defer to candidate investment only if both Stage 1 and Stage 2 "hold". If either stage "fails", it stays deferred, and "AI can pick stable candidates among new structures" is limited to candidates near known prototypes.

**Descriptive sensitivity checks only** (computed by a separate script after the decision, without affecting it): the unique-prototype pool; clustering by chemical system; S2 on relaxed structures; S1; the range of results when each framework is left out in turn; the Voronoi RF baseline; and CHGNet and MACE-MP-0.

## 7. Stage 2: external data (separate confirmation and pre-registration)

Stage 2's details can only be fixed once the data fields are confirmed. Only the principles are set here:

- **Data:** the Alexandria PBE database (CC BY 4.0). Take entries whose framework key is absent from the training reference and from WBM, and define an interpolation cell within the same database as the reference.
- **Selection bias:** the roughly 1.3 million entries Alexandria added in 2025 were generated with Matra-Genoa and screened with Orb-v2 and ALIGNN before DFT ([arXiv:2512.09169](https://arxiv.org/abs/2512.09169)). Whether earlier entries were also pre-screened by machine learning is **not yet verified**. Each entry's source batch is recorded where possible and reported by stratum.
- **Energy consistency:** first download one shard (about 62 MB) to check the fields, pseudopotentials and U values. Once they are confirmed to match MP, apply the MP2020 corrections and compute stability against the MP 2023 snapshot hull, the same reference as Stage 1. A denser hull including Alexandria is a sensitivity check only.
- **Sampling:** random sampling within cells at their natural stable share, not balanced to half stable; about 2,000 structures in total.
- **Models:** 3–4 MPtrj-only models with public weights (for example CHGNet, MACE-MP-0, SevenNet-0, MatRIS-10M-MP). They are not Stage 1's top 10, so Stage 2 decides on the median of these models, and the report says the two stages use different models.
- **Relaxation:** the same settings as Matbench Discovery (optimiser, cell filter, force tolerance and step cap, read from the pinned code). A failed relaxation counts as a missing prediction and is ranked last. Each model is first timed on 20 structures, and the CPU-hour estimate is reported before any decision.
- **Not used:** GNoME (stable structures only, so precision cannot be estimated; licence CC BY-NC); GNoME-derived MP entries added after 2024 (r2SCAN, not comparable with PBE); OQMD (DFT settings differ from MP).

## 8. What this can and cannot answer

- **It can answer** how much the ability of MP-only models to pick stable candidates drops, under DFT truth, in the chemical and the structural direction separately. Stage 1 covers only candidates generated by element substitution.
- **It cannot answer:**
  - how large models trained on OMat24 or Alexandria do on truly unfamiliar structures, because their training sets are too large to check structure by structure;
  - whether DFT-stable candidates can be synthesised, because the truth is still DFT;
  - whether a generative model can produce these structures. That is the CSP question; see the random-removal control.

## 9. What has already been seen (disclosure)

- D2A (`results/csp_screening_20261121T192919Z/boundaries.csv`) already computed each model's precision, recall and F1 on the "S1-unfamiliar initial label" group (4,255 unique prototypes), and its report says "the top 10's recall is 1–4 points lower". This document's structural cells are a subset of that group, and S2 was chosen as the decision definition after those results had been seen.
- While writing this document, the candidate counts, stable shares and element-count mix per cell were also seen (Section 4).
- No model metric has been computed in the cells this document defines.

## 10. Order and cost

1. Commit this document, the split script (`src/csp/far_split.py`), the decision script (`src/csp/far_decide.py`) and their checks (`tests/check_far_decide.py`) to git (the pre-registration) before any per-cell metric is computed. The script picks the 10 decision models from a fixed file: EquiformerV3+DeNS-MP (the lead model), DPA-4.0.1-Pro-MPtrj, DPA-4.0-Pro-MPtrj, MatRIS-10M-MP, eSEN-30M-MP, eqV2 S DeNS, MatRIS v0.5.0 MPtrj, DPA-3.1-MPtrj, AlphaNet-v1-MPtrj and Eqnorm MPtrj.
2. Stage 1: no cost, a few minutes on the Mac.
3. Download one Alexandria shard to check the fields (about 62 MB; needs confirmation).
4. Write the Stage 2 pre-registration; download the full set, about 3.8 GB (58 shards plus the hull file); time the models, report the CPU hours, and run only after confirmation. No paid compute.
