# CSP 随机移除对照（预登记）

> 状态（2026-11-21）：规则已写好，划分已生成并记录哈希，**还没有跑任何训练**。训练要租 GPU，属于付费计算：先跑一次冒烟测试测出每步时间，报告总花费，等批准后再跑。

## 1. 问题

Wei et al.（[arXiv:2609.26502](https://arxiv.org/abs/2609.26502) v2）去掉训练集里的钙钛矿框架后重训 EquiCSP，它对 11 个 1:1:2:6 目标的一致恢复从 8 个降到 3 个。

要回答的是：**下降是因为去掉了特定的模板信息，还是只是因为训练数据变少了？**

论文自己的实验方案也承认这一点：没有随机移除对照，下降就分不开"去掉了这个家族"和"训练样本变少"（[PROTOCOL.md](https://github.com/usccolumbia/benchmark_deep_csp/blob/631c7654942ed9fdf57cc42f37764e0d0994dd31/ablation/PROTOCOL.md)）。

## 2. 现有数据已经能说明什么

数字都由 `src/csp/random_removal_control.py` 从论文公开的逐目标结果重新算出，和论文的汇总表一致（`results/csp_random_control_20261121T223433Z/existing_arms.json`）。

| EquiCSP，11 个 1:1:2:6 目标 | 训练结构数 | 结构匹配（20 个候选内） | 一致恢复（还要求空间群一致） |
|---|---|---|---|
| 基线（全部数据，上游发布的最终检查点） | 27,136 | 8 | 8 |
| 去掉 ABC2D6 家族（重训，种子 42，按验证集选检查点） | 25,585 | 10 | 8 |
| 再去掉钙钛矿框架（PEROV，同样的训练方案） | 24,317 | 7 | 3 |

论文的"8 → 3"把三个因素混在一起：

1. **检查点选择不同。** 基线用的是上游发布的最终检查点，消融模型用的是按验证集选的检查点。论文在注意事项里写了这一点。
2. **训练数据变少。**
3. **训练的随机性。** 每组只训练一次。

**ABC2D6 组对 PEROV 组是现有数据里最干净的比较。** 两组训练方案、种子、检查点选法都一样，目标也一样，所以第 1 个因素被排除了。

- 一致恢复：PEROV 丢了 5 个（mp-12449、mp-16307、mp-19093、mp-6389、mp-6603），一个也没多。
- 结构匹配：丢了 3 个，一个也没多。

**但第 2、3 个因素还在。**

- PEROV 比 ABC2D6 组少 1,268 个训练结构（少 5.0%）。
- 两组各只有一次训练。重训本身能把结果移动多少，没有测过：只去掉 ABC2D6 家族，结构匹配反而从 8 个升到 10 个，这里面混着检查点选择的差别。

**现有数据的读法。** 去掉同一家族的 1,551 个结构，一致恢复一个没丢；再去掉 1,268 个钙钛矿框架结构，丢了 5 个。这更像是特定模板信息的作用，但排除不了"数据变少加上单次训练的波动"。这正是对照要回答的。

## 3. 对照设计（预登记）

规则写在 `results/csp_random_control_20261121T223433Z/config.json`，在任何训练之前提交到 git。

**新的对照组 R1–R3。** 和 PEROV 一样去掉 ABC2D6 家族，再从剩下的、不属于钙钛矿框架的结构里，**随机**去掉同样数量的结构（1,268 个训练、410 个验证）。每组抽一次，抽样种子固定。

这样 PEROV 和 R 的训练集一样大，去掉的家族也一样，**唯一的差别是多去掉的那批结构是哪些**。

| 组 | 训练种子 | 作用 |
|---|---|---|
| ABC2D6 | 42 | 检查运行流程（论文：一致恢复 8 个） |
| PEROV | 42、43、44 | 种子 42 同时用来检查流程（论文：3 个） |
| R1、R2、R3 | 42、43、44 | 随机移除对照 |
| ABC2D6（可选） | 43、44 | 测量不丢模板时的训练波动 |

核心 7 次训练，可选 2 次。训练方案沿用论文：106,000 步，有效批量 256，FP32，按验证集选检查点，从头训练。

**指标。**

- 主要：11 个目标里一致恢复的个数。
- 次要：结构匹配的个数。

**判定规则（事先定好）。**

- **G0 流程检查：** 我们的 ABC2D6 和 PEROV（种子 42）的一致恢复必须分别在论文的 8 和 3 的 ±1 以内。不满足就停下，先查运行流程，不做任何归因，也不再花钱。
- **支持"特定模板信息可能重要"：** 每一次 R 都高于每一次 PEROV，并且 R 的平均比 PEROV 的平均多至少 3 个。
- **支持"数据变少"：** R 的平均比 PEROV 的平均多不到 2 个（差 ≤ 1）。
- **下降没有复现：** PEROV 三次的平均 ≥ 6，说明 8 → 3 经不起重复种子，报告后停止。
- **其他情况：** 结论不定。报告全部结果；没有新的书面决定，不再追加训练。

3 对 3 次训练，精确单侧置换检验最小的 p 值是 1/20 = 0.05。我们只报告每次训练和每个目标的计数，不做更强的说法。

## 3a. 修订 A1（2026-11-21，在任何训练之前）

原规则（commit `4220c46`）不改，修订另存为 `amendments.json`，同样在训练前提交。

- **抽样种子。** 每次训练生成 20 个候选时，抽样种子固定为这次的训练种子（42、43、44），并记录库版本和 GPU 型号。GPU 计算本身可能不完全确定，剩下的波动正是重复种子要测的。
- **比较对象。** 所有比较都在我们自己的训练之间进行，训练、抽样、评分用同一套固定版本的代码和设置。论文的 8 和 3 只用于 G0 流程检查。
- **规则顺序。** 按 G0 → 下降没有复现 → 特定模板信息 → 数据变少 → 结论不定 的顺序判断，第一个满足的决定结果。R 低于 PEROV 的情况也归入"数据变少"。
- **结论强度。**
    - 即使 R 明显好于 PEROV，也只支持"去掉的是哪些结构可能比去掉多少更重要"，限于 EquiCSP 和这 11 个目标，**不证明因果机制**（比如论文的简并解释）。
    - "数据变少"只说明这个实验分不开两者和训练集大小。
    - 结论不定就报告为不定，不归入任何一种解释。
- **审批。** 冒烟测试和完整训练分开审批。

## 4. 已完成和未完成

**已完成。**

- 下载论文的公开发布（commit `631c765`）和 MP-20 划分文件（DiffCSP commit `7121d15`）。MP-20 三个文件的 SHA-256 和论文审计文件里记录的完全一致。
- 生成 R1–R3 的移除名单，每组训练集剩 24,317 个、验证集剩 8,150 个，和 PEROV 一样。三组随机部分两两重叠 62–74 个，和独立抽样的期望值（约 66 个）相符。

**未完成。**

- 没有跑任何训练。
- 每次训练的时长和花费还不知道：论文用一张 V100 16GB，没给时长。
- 下一步：用 EquiCSP 的上游代码（[EmperorJia/EquiCSP](https://github.com/EmperorJia/EquiCSP)，MIT）在租用的 GPU 上跑 1,000 步冒烟测试，按测出的时间报告 7–9 次训练的总花费，**等批准后再跑**。
- 评估沿用论文的指标代码（[CSPBenchMetrics](https://github.com/usccolumbia/CSPBenchMetrics)）和 20 个候选的流程，到时再固定版本。

## 5. 局限

- 随机抽样没有在成分或元素数上和钙钛矿结构配对。对照只能区分"这批结构"和"同样数量的任意结构"，分不了更细。
- 只有 11 个目标，一个目标就是 9 个百分点。
- 只有一个模型（EquiCSP）和一个家族（钙钛矿框架）。
- 论文的结论能不能推广到更大、离已知原型更远的测试集，这个对照回答不了。

## 6. 文件

- `src/csp/fetch_csp_ablation.py`：下载并核对哈希。
- `src/csp/random_removal_control.py`：现有结果的配对比较、预登记规则、划分生成。
- `results/csp_random_control_20261121T223433Z/`：`config.json`、`amendments.json`、`existing_arms.json`、`existing_arms_paired.csv`、`splits.json`、`splits/`、溯源记录。

---

## English version

# CSP random-removal control (pre-registered)

> Status (2026-11-21): the rules are written and the splits are built and hashed. **No training has been run.** Training needs a rented GPU, which is paid compute. The next step is one smoke test to measure time per step and report the total cost. Nothing else runs until that cost is approved.

## 1. Question

Wei et al. ([arXiv:2609.26502](https://arxiv.org/abs/2609.26502) v2) retrained EquiCSP without the perovskite frameworks in its training set. Its consensus recovery of the 11 1:1:2:6 targets fell from 8 to 3.

The question is: **did it fall because specific template information was removed, or only because the model had less training data?**

The paper's own protocol acknowledges this: without random-removal controls, a decrease cannot separate "this family was removed" from "there were fewer training examples" ([PROTOCOL.md](https://github.com/usccolumbia/benchmark_deep_csp/blob/631c7654942ed9fdf57cc42f37764e0d0994dd31/ablation/PROTOCOL.md)).

## 2. What the existing data can already show

Every number was recomputed by `src/csp/random_removal_control.py` from the paper's released per-target results, and matches the paper's summary table (`results/csp_random_control_20261121T223433Z/existing_arms.json`).

| EquiCSP, 11 1:1:2:6 targets | Training structures | Structure match (within 20 candidates) | Consensus (space group must also agree) |
|---|---|---|---|
| Baseline (all data, upstream final checkpoint) | 27,136 | 8 | 8 |
| ABC2D6 family removed (retrained, seed 42, validation-selected checkpoint) | 25,585 | 10 | 8 |
| Perovskite frameworks also removed (PEROV, same recipe) | 24,317 | 7 | 3 |

The paper's "8 → 3" mixes three factors:

1. **Different checkpoint selection.** The baseline uses the upstream final checkpoint; the ablated models use the validation-selected checkpoint. The paper states this in its caveats.
2. **Less training data.**
3. **Training randomness.** Each arm was trained once.

**ABC2D6 vs PEROV is the cleanest contrast in the existing data.** The two arms share the recipe, the seed, the checkpoint selection and the targets, so factor 1 is excluded.

- Consensus: PEROV loses 5 (mp-12449, mp-16307, mp-19093, mp-6389, mp-6603) and gains none.
- Structure match: it loses 3 and gains none.

**Factors 2 and 3 remain.**

- PEROV has 1,268 fewer training structures than the ABC2D6 arm (5.0% fewer).
- Each arm was trained once, and how much retraining alone moves the result has not been measured. Removing only the ABC2D6 family raised the structure match from 8 to 10, and that change also includes the checkpoint-selection difference.

**How to read the existing data.** Removing 1,551 structures of the same family cost no consensus recoveries. Removing a further 1,268 perovskite-framework structures cost 5. That looks more like an effect of specific template information, but it cannot rule out "less data plus single-run noise". That is what the control has to answer.

## 3. Control design (pre-registered)

The rules are in `results/csp_random_control_20261121T223433Z/config.json`, committed to git before any training.

**New control arms R1–R3.** Like PEROV, remove the ABC2D6 family. Then remove the same **number** of further structures (1,268 training, 410 validation), drawn **at random** from the remaining structures that are not perovskite frameworks. Each arm is one draw with a fixed sampling seed.

PEROV and R then have training sets of the same size with the same family removed. **The only difference is which further structures are gone.**

| Arm | Training seeds | Role |
|---|---|---|
| ABC2D6 | 42 | Runner check (paper: consensus 8) |
| PEROV | 42, 43, 44 | Seed 42 doubles as a runner check (paper: 3) |
| R1, R2, R3 | 42, 43, 44 | Random-removal control |
| ABC2D6 (optional) | 43, 44 | Measures training noise when no template is removed |

The core plan is 7 training runs, plus 2 optional runs. The recipe follows the paper: 106,000 steps, effective batch 256, FP32, validation-selected checkpoint, trained from scratch.

**Metrics.**

- Primary: the number of the 11 targets with a consensus recovery.
- Secondary: the number with a structure match.

**Decision rules (set in advance).**

- **G0 runner check:** our ABC2D6 and PEROV runs (seed 42) must land within ±1 of the paper's 8 and 3. If either misses, stop and audit the runner. Nothing is attributed, and no more money is spent.
- **"Specific template information may matter" supported:** every R run beats every PEROV run, and the R mean exceeds the PEROV mean by at least 3.
- **"Less data" supported:** the R mean exceeds the PEROV mean by 1 or less.
- **Drop not reproduced:** if the PEROV mean over three seeds is 6 or more, the 8 → 3 drop does not survive repeated seeds. Report that and stop.
- **Anything else:** inconclusive. Report all runs, and add no further runs without a new written decision.

With 3 vs 3 runs, the smallest exact one-sided permutation p-value is 1/20 = 0.05. We report counts per run and per target and claim no more than that.

## 3a. Amendment A1 (2026-11-21, before any training)

The original rules (commit `4220c46`) stay as they are. The amendment is saved separately as `amendments.json` and is also committed before training.

- **Sampling seeds.** When each run generates its 20 candidates, the sampling seed is fixed to that run's training seed (42, 43, 44). Library versions and the GPU type are recorded. GPU kernels may still not be fully deterministic, and that remaining variation is part of what the repeated seeds measure.
- **What is compared.** Every comparison is between our own runs, trained, sampled and scored with the same pinned code and settings. The paper's 8 and 3 are used only for the G0 runner check.
- **Rule order.** The rules apply in the order G0 → drop not reproduced → specific template information → less data → inconclusive, and the first that matches decides. R scoring below PEROV also counts as "less data".
- **Strength of the conclusion.**
    - Even if R clearly beats PEROV, that supports only "which structures were removed may matter more than how many", for EquiCSP on these 11 targets. **It does not establish a causal mechanism** (for example the paper's degeneracy explanation).
    - "Less data" means only that this experiment cannot tell the two apart from training-set size.
    - Inconclusive is reported as inconclusive and is not assigned to either reading.
- **Approvals.** The smoke test and the full training runs are approved separately.

## 4. Done and not done

**Done.**

- Downloaded the paper's release (commit `631c765`) and the MP-20 split files (DiffCSP commit `7121d15`). The SHA-256 of all three MP-20 files matches the hashes recorded in the paper's audit file.
- Built the R1–R3 removal lists. Each leaves 24,317 training and 8,150 validation structures, the same as PEROV. The random parts of the three draws overlap pairwise by 62–74 structures, in line with the about 66 expected from independent draws.

**Not done.**

- No training has been run.
- The time and cost per training run are unknown. The paper used one V100 16GB and gives no duration.
- Next step: a 1,000-step smoke test on a rented GPU with EquiCSP's upstream code ([EmperorJia/EquiCSP](https://github.com/EmperorJia/EquiCSP), MIT). From the measured time, report the total cost of the 7–9 runs, and **wait for approval before running them**.
- Evaluation will use the paper's metric code ([CSPBenchMetrics](https://github.com/usccolumbia/CSPBenchMetrics)) and its 20-candidate protocol; versions will be pinned at that step.

## 5. Limits

- The random draws are not matched to the perovskite structures on composition or number of elements. The control can tell "these structures" from "the same number of any structures", nothing finer.
- There are only 11 targets; one target is 9 percentage points.
- One model (EquiCSP) and one family (perovskite frameworks).
- The control cannot say whether the paper's conclusion carries over to a larger test set further from known prototypes.

## 6. Files

- `src/csp/fetch_csp_ablation.py`: downloads and checks hashes.
- `src/csp/random_removal_control.py`: paired comparison of the existing results, pre-registered rules, split generation.
- `results/csp_random_control_20261121T223433Z/`: `config.json`, `amendments.json`, `existing_arms.json`, `existing_arms_paired.csv`, `splits.json`, `splits/`, provenance record.
