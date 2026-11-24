# 外推检验第二阶段：Alexandria 外部数据（草稿，尚未预登记）

> 状态（2026-11-24）：**草稿，等确认。** 只下载了 Alexandria 的一个分片（`alexandria_00000.json.bz2`，61.6 MB，10 万个条目）用来核对字段和数量；没有跑任何模型。下面有几处需要你决定（第 8 节）。定稿后再提交 git 作为预登记。第一阶段的设计和结果见 `FAR_FROM_TRAINING_TEST.md` 和 `results/csp_far_stage1_20261124T0908Z/`。

## 1. 为什么需要第二阶段

第一阶段在 WBM 上“成立”，但“远”是温和的远：候选都由元素替换生成，事后修正框架键后，结构外推格只有 30 个含稳定候选的框架。真正远离训练集的结构，需要外部数据。

## 2. 用一个分片核对过的事实

| 问题 | 核对结果 | 影响 |
|---|---|---|
| 字段 | 每个条目都有 `e_above_hull`、`e_form`、`energy_total`、`energy_corrected`、分解产物、计算时间、来源路径（`location`）；`parameters` 是空的，单个条目上看不到赝势和 U 值 | 真值用条目自带的凸包距离 |
| 修正方案 | 纯氧化物每个 O 的修正是 −0.7023 eV，含 Fe 氧化物每个 Fe 约 −2.79 eV：是 MP **旧版**修正，不是 MP2020 | 同一组成的模型能量和 DFT 能量加的修正相同，算差值时抵消，不影响 |
| 原始能量能否和 MP 比 | 和 MP 2023 快照里化学式、空间群、原子数相同的条目比：不加 U 的 1,661 对，中位差 0.95 meV/atom，69% 在 5 meV 以内；加 U 的 500 对，中位差 5.1 meV/atom，只有 34% 在 5 meV 以内 | **排除 GGA+U 体系**（含 Co、Cr、Fe、Mn、Mo、Ni、V、W 并含 O 或 F） |
| 来源 | `location` 记录了生成流程：cgat_comp、extra、cgat_prot、orbital、high_throughput、cgat_comp_2、m3gnet、substitutions 等；计算时间从 2014 到 2025 年 | **筛选偏差不只在 2025 年新增条目**：m3gnet、orbital、cgat 这些来源多半经过机器学习预筛，必须按来源分层报告 |
| 输入结构 | 条目里只有 DFT 弛豫后的结构 | 和第一阶段不同：模型从正确的几何出发，任务更容易。报告里写明 |
| 和 WBM 重复 | 化学式、空间群、原子数都相同的有 3,960 个 | 排除 |
| 框架键 | 用 spglib 自己算，规范化方式和第一阶段的事后修正相同；在 3,000 个随机 MP 结构上，和 MP 文件里的 spglib 标签一致 99.4% | 约 0.6% 的标注误差 |

**分片里的数量**（排除 WBM 重复和 GGA+U 之后，真值为 Alexandria 自己的凸包距离 ≤ 0）：

| 格子 | 候选 | 稳定 | 框架数 | 含稳定候选的框架 |
|---|---|---|---|---|
| 插值 | 24,692 | 918 | 2,140 | 532 |
| 结构外推 | 1,656 | 33 | 418 | 21 |
| 化学外推 | 63,121 | 1,497 | 1,944 | 478 |
| 双重外推 | 3,329 | 40 | 567 | 26 |

全量有 58 个分片。如果各分片相近，结构外推格约有 9.6 万个候选、约 1,900 个稳定（分片是否有代表性没有核实）。框架数比 WBM 多得多。结构外推格里的稳定候选主要来自 orbital（10）、m3gnet（10）、cgat_comp_2（9）。

## 3. 定义

- **训练参照、化学轴：** 和第一阶段相同（MP 2023 快照；化学体系是否出现过）。
- **结构轴：** spglib 算出的框架键，在空间群的全部等价原点选择上规范化，和 MP 标签同样处理。
- **真值：** Alexandria 自带的 `e_above_hull` ≤ 0。它相对 Alexandria 自己的凸包，比 MP 的凸包更密，所以“稳定”的标准比第一阶段严。
- **模型的预测：** 从 DFT 弛豫后的结构出发，用模型弛豫（FIRE 加 FrechetCellFilter，力收敛 0.05 eV/Å，最多 500 步，和 Matbench Discovery 对这四个模型的设置相同），预测凸包距离 = DFT 凸包距离 + (模型能量 − DFT 原始能量)/原子数。弛豫失败记为缺预测，排在最后。

## 4. 抽样和指标

- **按类别分层抽样：** 每个格子随机抽 200 个稳定和 400 个不稳定的结构（稳定的不够就全取）。插值格按结构外推格的元素数构成分层抽样。三个格子（插值、结构外推、双重外推）共约 1,800 个结构；化学外推格第一阶段已经回答得较好，这里不跑。
- **主指标：Somers' D = 2 × AUC − 1。** 它是“任取一个稳定、一个不稳定的候选，模型把稳定的排在前面”的概率减去反过来的概率。它不受分层抽样改变的稳定比例影响，随机为 0、全对为 1。第一阶段的 R 精度在类别分层抽样下会失真，所以这里换指标；报告里也给出第一阶段数据的 Somers' D，便于对照。
- **比值和区间：** r = 外推格的 D / 插值格的 D；判定看四个模型 r 的中位数；按框架整群 bootstrap，1,000 次，种子 11。

## 5. 模型

只用 MPtrj 训练、权重公开、Matbench Discovery 里有设置的四个：CHGNet 0.3.0（BSD-3）、MACE-MP-0 medium（MIT）、SevenNet-0（GPL-3.0）、MatRIS-10M-MP（BSD-3）。它们不是第一阶段的前 10 名，所以第二阶段用这四个的中位数，报告时写明。

## 6. 判定规则（草稿）

按顺序检查，结构外推格决定 D10：

| 顺序 | 结果 | 条件 |
|---|---|---|
| 1 | 样本不足 | 抽到的稳定结构少于 50 个，或含稳定结构的框架少于 20 个 |
| 2 | 失败 | r 中位数的 95% 区间上限 < 0.5；或四个模型 D 的中位数，在外推格里的 95% 区间上限 < 0.2 |
| 3 | 成立 | r 中位数的 95% 区间下限 ≥ 0.8，并且 D 的中位数在外推格里的 95% 区间下限 > 0.2 |
| 4 | 部分成立 | 其他情况 |

- **来源分层：** 主分析用全部来源。另外去掉 m3gnet 和 orbital 两个来源再算一遍；如果两者的结果不同（一个成立、一个失败），记为“部分成立”。
- **对 D10：** 第一、第二阶段都“成立”，更大规模的晶体筛选才从暂缓改为候选投入。

## 7. 已知局限

- 输入是 DFT 弛豫后的结构，比从初始结构出发容易。
- 真值用的是 Alexandria 自己的凸包和 MP 旧版修正，和第一阶段的 MP2020 修正加 MP 凸包不同。
- 排除了 GGA+U 体系，所以不覆盖含过渡金属的氧化物和氟化物。
- 第二阶段没有 Wrenformer 这类模板式基线（要另外训练或运行），增量价值只能和随机比（D > 0.2 的门槛）。
- 来源里的机器学习预筛方式没有逐一核实，只能按来源分层。
- 框架标签器和 MP 文件的标签一致 99.4%，不是 100%。

## 8. 需要你决定的事

1. **完整下载 Alexandria PBE：** 58 个分片约 3.6 GB，加凸包文件约 168 MB，CC BY 4.0，存到已 gitignore 的 `data/raw/alexandria/`。
2. **在 Mac 上安装四个模型的软件包：** 建一个单独的虚拟环境，装 chgnet、mace-torch、sevenn、matris。会从 PyPI 下载软件和模型权重，约几 GB。
3. **CPU 时间：** 先每个模型跑 20 个结构测时间，再报告总的 CPU 小时数。
4. **判定门槛：** 0.8、0.5 沿用第一阶段；增量价值的门槛 D > 0.2 是新定的判断，可以调。
5. **是否保留类别分层抽样加 Somers' D**，代替第一阶段的 R 精度。

---

# Extrapolation test, Stage 2: Alexandria external data (draft, not yet pre-registered)

> Status (2026-11-24): **draft, awaiting confirmation.** Only one Alexandria shard (`alexandria_00000.json.bz2`, 61.6 MB, 100,000 entries) was downloaded, to check fields and counts; no model has been run. Several points need your decision (Section 8). Once settled, this is committed to git as the pre-registration. Stage 1's design and results: `FAR_FROM_TRAINING_TEST.md` and `results/csp_far_stage1_20261124T0908Z/`.

## 1. Why Stage 2

Stage 1 holds on WBM, but "far" there is mild: candidates come from element substitution, and after the post-hoc fix to the framework key the structural cell has only 30 frameworks with a stable candidate. Structures that are genuinely far from training need external data.

## 2. Facts checked on one shard

| Question | What the check found | Consequence |
|---|---|---|
| Fields | Every entry has `e_above_hull`, `e_form`, `energy_total`, `energy_corrected`, decomposition products, run time and a source path (`location`); `parameters` is empty, so pseudopotentials and U values are not visible per entry | The truth is the entry's own hull distance |
| Correction scheme | Pure oxides get −0.7023 eV per O, and Fe oxides about −2.79 eV per Fe: these are MP's **legacy** corrections, not MP2020 | The model energy and the DFT energy of the same composition get the same correction, which cancels in their difference |
| Raw energies vs MP | Against MP 2023 entries with the same formula, space group and number of sites: 1,661 GGA pairs, median difference 0.95 meV/atom, 69% within 5 meV; 500 GGA+U pairs, median 5.1 meV/atom, only 34% within 5 meV | **Exclude GGA+U systems** (containing Co, Cr, Fe, Mn, Mo, Ni, V or W together with O or F) |
| Sources | `location` records the generating workflow: cgat_comp, extra, cgat_prot, orbital, high_throughput, cgat_comp_2, m3gnet, substitutions and others; run years 2014 to 2025 | **Selection bias is not confined to the 2025 additions**: m3gnet, orbital and cgat sources were probably ML pre-screened, so results must be stratified by source |
| Input structures | Entries carry only DFT-relaxed structures | Unlike Stage 1, models start from the correct geometry, which is easier; the report says so |
| Overlap with WBM | 3,960 share formula, space group and number of sites with a WBM entry | Excluded |
| Framework key | Computed with spglib and canonicalised as in Stage 1's post-hoc fix; agrees with MP's spglib labels on 99.4% of 3,000 random MP structures | About 0.6% labelling error |

**Counts in the shard** (after excluding WBM overlap and GGA+U; truth = Alexandria's own hull distance ≤ 0):

| Cell | Candidates | Stable | Frameworks | Frameworks with a stable one |
|---|---|---|---|---|
| Interpolation | 24,692 | 918 | 2,140 | 532 |
| Structural extrapolation | 1,656 | 33 | 418 | 21 |
| Chemical extrapolation | 63,121 | 1,497 | 1,944 | 478 |
| Double extrapolation | 3,329 | 40 | 567 | 26 |

The full set has 58 shards. If the shards are alike, the structural cell has about 96,000 candidates and about 1,900 stable ones (whether this shard is representative is not verified), across far more frameworks than WBM. In the shard, the structural cell's stable candidates come mainly from orbital (10), m3gnet (10) and cgat_comp_2 (9).

## 3. Definitions

- **Training reference and chemical axis:** as in Stage 1 (MP 2023 snapshot; whether the chemical system appears).
- **Structural axis:** the spglib framework key, canonicalised over all equivalent origin choices of the space group, applied the same way to the MP labels.
- **Truth:** Alexandria's own `e_above_hull` ≤ 0. It is relative to Alexandria's hull, which is denser than MP's, so "stable" is stricter than in Stage 1.
- **Model prediction:** start from the DFT-relaxed structure and relax with the model (FIRE with FrechetCellFilter, force tolerance 0.05 eV/Å, at most 500 steps, the settings Matbench Discovery uses for these four models). Predicted hull distance = DFT hull distance + (model energy − DFT raw energy)/atoms. A failed relaxation is a missing prediction, ranked last.

## 4. Sampling and metrics

- **Class-stratified sampling:** in each cell, sample 200 stable and 400 unstable structures at random (all stable ones if fewer). The interpolation cell is sampled to match the structural cell's element-count mix. Three cells (interpolation, structural and double extrapolation), about 1,800 structures; the chemical cell is skipped, since Stage 1 answered it fairly well.
- **Primary metric: Somers' D = 2 × AUC − 1,** the probability that a model ranks a random stable candidate above a random unstable one, minus the reverse. It is unaffected by the change in stable share that class-stratified sampling causes; random scores 0 and perfect 1. Stage 1's R-precision would be distorted by class-stratified sampling, hence the change; the report also gives Somers' D on the Stage 1 data for comparison.
- **Ratio and intervals:** r = extrapolation-cell D / interpolation-cell D; the decision uses the median r of the four models; cluster bootstrap by framework, 1,000 resamples, seed 11.

## 5. Models

Four models trained only on MPtrj, with public weights and Matbench Discovery settings: CHGNet 0.3.0 (BSD-3), MACE-MP-0 medium (MIT), SevenNet-0 (GPL-3.0) and MatRIS-10M-MP (BSD-3). They are not Stage 1's top 10, so Stage 2 decides on these four's median, and the report says so.

## 6. Decision rules (draft)

Checked in order; the structural-extrapolation cell decides D10:

| Order | Outcome | Condition |
|---|---|---|
| 1 | Too small | Fewer than 50 sampled stable structures, or fewer than 20 frameworks with a stable one |
| 2 | Fails | Upper bound of the 95% interval of the median r < 0.5; or upper bound of the 95% interval of the four models' median D in the extrapolation cell < 0.2 |
| 3 | Holds | Lower bound of the 95% interval of the median r ≥ 0.8, and lower bound of the 95% interval of the median D in the extrapolation cell > 0.2 |
| 4 | Partial | Anything else |

- **Source strata:** the main analysis uses all sources. It is repeated without the m3gnet and orbital sources; if the two disagree (one holds, the other fails), the outcome is "partial".
- **D10:** larger-scale crystal screening moves from defer to candidate investment only if both Stage 1 and Stage 2 hold.

## 7. Known limits

- Inputs are DFT-relaxed structures, which is easier than starting from initial structures.
- The truth uses Alexandria's own hull and MP's legacy corrections, unlike Stage 1's MP2020 corrections and MP hull.
- GGA+U systems are excluded, so transition-metal oxides and fluorides are not covered.
- Stage 2 has no template-like baseline such as Wrenformer (it would need training or running separately), so added value is judged only against random (the D > 0.2 threshold).
- How each source was ML pre-screened is not verified one by one; stratifying by source is the only handle.
- The framework labeller agrees with the MP labels on 99.4% of structures, not 100%.

## 8. Decisions needed from you

1. **Download the full Alexandria PBE set:** 58 shards, about 3.6 GB, plus the hull file, about 168 MB; CC BY 4.0; into the gitignored `data/raw/alexandria/`.
2. **Install the four models' packages on the Mac:** a separate virtual environment with chgnet, mace-torch, sevenn and matris, downloading software and weights from PyPI and the model hosts, a few GB.
3. **CPU time:** time each model on 20 structures first, then report the total CPU hours.
4. **Thresholds:** 0.8 and 0.5 carry over from Stage 1; the added-value threshold D > 0.2 is a new judgement call and can be changed.
5. **Whether to keep class-stratified sampling with Somers' D** in place of Stage 1's R-precision.
