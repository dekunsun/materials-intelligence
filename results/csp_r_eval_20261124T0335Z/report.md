# CSP 随机删除对照：R1–R3 的生成、弛豫、打分和预注册判定

日期：2026-11-24（UTC），03:35 – 06:23，全部在本机 CPU 上跑（Apple M3 Pro），没有用付费算力。训练记录在 `results/csp_r_train_20261123T1807Z/`。PEROV 的数字来自 G0（seed 42）和 `results/csp_perov_seeds_eval_20261123T1025Z/`（seed 43、44）。

## 结论

**按预注册规则，结论是“模板特有”（template_specific）。** 判定由 `src/csp/r_decision.py` 给出，这个脚本在任何 R1–R3 候选生成之前就 commit 了（`57970a3`），这次没有改过。

| 弛豫后 consensus（主指标） | seed 42 | seed 43 | seed 44 | 平均 |
|---|---|---|---|---|
| PEROV（去掉钙钛矿框架） | 3 / 11 | 4 / 11 | 4 / 11 | 3.67 |
| R1–R3（随机去掉同样数量） | 8 / 11 | 8 / 11 | 8 / 11 | 8.00 |

按修订 A1 的顺序逐条检查：

| 规则 | 条件 | 结果 |
|---|---|---|
| G0 运行检查 | G0 通过 | 通过 |
| 没有复现（not_reproduced） | PEROV 平均 ≥ 6 | 不适用（3.67） |
| **模板特有（template_specific）** | 每个 R 都高于每个 PEROV，**并且** R 平均 − PEROV 平均 ≥ 3 | **满足**：最低的 R 是 8，最高的 PEROV 是 4；差值 13/3 ≈ 4.33 |

**这说明什么。** 两组都去掉了 ABC2D6 家族，训练集一样大（24,317 个），训练配方、seed 和打分方法都一样，唯一的差别是多去掉的 1,268 个训练结构是哪些。

- 随机去掉 1,268 个：consensus 是 8、8、8，和 G0 里只去掉 ABC2D6 家族的 seed 42（8）一样。
- 去掉 1,268 个钙钛矿框架结构：consensus 是 3、4、4。

所以在这个设置下，PEROV 的下降不能用“训练数据变少”来解释，而是和去掉的是哪些结构有关。

## 这个结论的范围

- **样本很小。** 每组 3 次训练。精确的单侧置换 p 值是 1/20 = 0.05，这是 3 对 3 能得到的最小值（预注册里写明了）。它不参与判定。判定依据是预注册的规则，不是显著性检验。
- **只限于这个设置：** 11 个 1:1:2:6 目标、EquiCSP、论文的训练配方、每个目标 20 个候选、ORB-v3 弛豫（模型版本是推断的，**没有确认**）。
- **没有回答“为什么”。** 结论只是说：去掉的那批钙钛矿框架结构，对这些目标的作用大于同样数量的随机结构。它没有说明是框架里的哪些结构起作用，也没有说明模型是怎么用到这些信息的。
- **ABC2D6 组只训练了 seed 42。** 不丢模板时的训练波动没有直接测过；预注册里的可选运行（ABC2D6 seed 43、44）没有做。三个 R 结果都是 8，波动看起来不大，但这不能代替那两次运行。
- **验证集不同。** 每组用自己的验证集（和训练集按同样的规则删除）选 checkpoint，这是预注册的设计。所以 PEROV 和 R 的 checkpoint 是在不同验证集上选的。

## 不参与判定的两项

| | PEROV | R | 规则给出的结果 |
|---|---|---|---|
| 未弛豫 consensus（敏感性检查，不是预注册的） | 3、3、2 | 8、8、7 | 也是 template_specific（差值 5） |
| 弛豫后 fit（次要指标） | 4、6、4 | 8、8、8 | 不套规则；差值 3.33 |

弛豫前后结论一样，所以这次的结论不依赖于 ORB-v3 弛豫。

## 逐个目标（`per_target_all_runs.csv`，弛豫后 consensus）

| 目标 | PEROV（3 个 seed 中几次） | R（3 个 seed 中几次） | G0 ABC2D6 seed 42 |
|---|---|---|---|
| mp-19274、mp-10321、mp-12449 | 3 | 3 | 是 |
| mp-6231、mp-19093、mp-16307、mp-6603 | 0 | 3 | 是 |
| mp-6389 | 0 | 2（seed 42、44） | 是 |
| mp-1215245（Zr1Ti1Ni2H6） | 2（seed 43、44） | 1（seed 43） | 否 |
| mp-557387、mp-556434 | 0 | 0 | 否 |

- R1 和 R3 的 8 个 consensus 目标和 G0 里 ABC2D6 seed 42 的 8 个完全相同。R2 少了 mp-6389，多了 mp-1215245。
- 差别集中在 5 个目标上：mp-6231、mp-19093、mp-16307、mp-6603、mp-6389。R 组基本都能恢复，PEROV 组三个 seed 一次也没有。R 组每次 consensus 的匹配都排第 1。
- 和论文不同的地方，只记录、不用来下结论：论文里 PEROV 丢掉的 5 个是 mp-12449、mp-16307、mp-19093、mp-6389、mp-6603。我们的 PEROV 三个 seed 都恢复了 mp-12449，而 mp-6231 一次也没有恢复。
- 3 个 seed 的样本很小，“几次”只是描述，不是估计出的概率。

## 运行情况

- **代码：** sample.py、relax.py、score.py、run_eval.sh 和 PEROV seed 打分时逐字节相同；r_decision.py 和 `57970a3` 里的相同（SHA-256 见 `config.json`）。
- **生成：** 每个 R 组 11 个目标 × 20 个候选 = 220 个，全部写出，0 个失败，成分全部正确（sample.py 会断言成分）。checkpoint 是按验证损失选出的那个，哈希和训练记录一致，加载参数时没有缺失或多余的键。生成种子等于训练种子，每个目标前重设（修订 A1）。
- **弛豫：** 0 个报错，设置和 PEROV 相同。最大原子力 ≤ 0.01 eV/Å 的：R1 206 / 220，R2 213 / 220，R3 205 / 220（PEROV 是 182–189）。用满 500 步的：10、8、7 个，它们保留第 500 步的结构，照常参与排序和打分，没有删掉任何候选。
- **打分：** 每次运行每个目标都是 20 个文件、20 个读入，判定脚本也检查了这一点。
- **数据泄漏检查（2026-11-24）：** 在 ABC2D6、PEROV、R1–R3 五组里，训练集和验证集都不含 11 个目标本身，也不含和目标化学式相同的结构。R 组和 PEROV 的行数相同（训练 24,317，验证 8,150）。
- **没有核实：** 这次没有重跑逐字节可重复性检查（G0 只查过 seed 42 的一个目标）。R3 是在 R1、R2 还在生成时同时开始的，几台任务抢 CPU 只影响用时，不影响结果，但这一点也没有专门验证。

## 论文没写、这里自己选的

和 G0 相同：ORB-v3 模型是推断的 orb_v3_conservative_inf_omat（**没有确认**）；优化器 ASE FIRE + FrechetCellFilter；每个目标正好生成 20 个；在 CPU 上生成。

## 文件

- `decision.json`：判定结果、每条规则的检查、不参与判定的几项、所有输入打分表的路径和 SHA-256
- `per_target_all_runs.csv`：六次运行每个目标的 consensus、fit、排名
- `per_target_consensus.png`：逐目标的图，由 `src/csp/plot_r_control.py` 画出（2026-11-24 补充）
- `config.json`：判定、各次运行的汇总、代码和 checkpoint 的哈希、各项设置、泄漏检查
- `R1_s42/`、`R2_s43/`、`R3_s44/`：`raw/`（220 个候选和 `sample_meta.json`）、`relaxed/`（弛豫、排序后的候选和每个目标的 `relax_report.json`）、`score_relaxed.csv`、`score_raw.csv` 和各步日志
- `run_R1R2.log`、`run_R3.log`、`started_at`、`started_R3_at`、`finished_R1R2_at`、`finished_R3_at`

## 下一步（按依赖顺序）

1. 更新 `modules/csp/RANDOM_REMOVAL_CONTROL.md` 的状态和结论，然后 commit（等确认）。
2. 预注册的核心 7 次训练到此全部完成。可选的 ABC2D6 seed 43、44 可以直接测出不丢模板时的训练波动，但它们不会改变这次的判定。要不要跑需要单独决定，而且是付费运行。

---

# CSP random-removal control: R1–R3 sampling, relaxation, scoring and the pre-registered decision

Date: 2026-11-24 (UTC), 03:35 – 06:23. Everything ran on the Mac's CPU (Apple M3 Pro), with no paid compute. The training record is in `results/csp_r_train_20261123T1807Z/`. PEROV's numbers come from G0 (seed 42) and `results/csp_perov_seeds_eval_20261123T1025Z/` (seeds 43 and 44).

## Verdict

**Under the pre-registered rules, the outcome is template_specific.** The decision comes from `src/csp/r_decision.py`. That script was committed (`57970a3`) before any R1–R3 candidate was generated, and it was not changed for this run.

| Relaxed consensus (primary) | seed 42 | seed 43 | seed 44 | Mean |
|---|---|---|---|---|
| PEROV (perovskite frameworks removed) | 3 / 11 | 4 / 11 | 4 / 11 | 3.67 |
| R1–R3 (the same number removed at random) | 8 / 11 | 8 / 11 | 8 / 11 | 8.00 |

The rules, in amendment A1's order:

| Rule | Condition | Result |
|---|---|---|
| G0 runner check | G0 passed | Passed |
| not_reproduced | PEROV mean ≥ 6 | Does not apply (3.67) |
| **template_specific** | Every R beats every PEROV run **and** mean(R) − mean(PEROV) ≥ 3 | **Met.** The lowest R is 8 and the highest PEROV is 4; the difference is 13/3 ≈ 4.33 |

**What this shows.** Both arms remove the ABC2D6 family and have the same training-set size (24,317). They share the recipe, seeds and scoring. The only difference is which 1,268 extra training structures are removed.
- With 1,268 removed at random, consensus is 8, 8 and 8. That equals G0's seed-42 arm with only the ABC2D6 family removed (8).
- With the 1,268 perovskite-framework structures removed, consensus is 3, 4 and 4.

So, in this setup, PEROV's drop is not explained by having less training data. It depends on which structures are removed.

## Scope of the conclusion

- **The sample is small.**
  - Each arm has 3 training runs.
  - The exact one-sided permutation p-value is 1/20 = 0.05, the smallest value 3 vs 3 can give (as the pre-registration notes). It does not decide anything.
  - The decision rests on the pre-registered rules, not on a significance test.
- **It holds only for this setup:** 11 targets of type 1:1:2:6, EquiCSP, the paper's training recipe, 20 candidates per target, and ORB-v3 relaxation (the model variant is inferred, **not confirmed**).
- **It does not answer "why".**
  - It says only that, for these targets, the removed perovskite-framework structures matter more than the same number of random structures.
  - It does not say which structures within that set matter, or how the model uses them.
- **The ABC2D6 arm was trained on seed 42 only.**
  - Training variation without the template loss was not measured directly. The optional pre-registered runs (ABC2D6 seeds 43 and 44) were not done.
  - All three R runs scored 8, so the variation looks small. That does not replace those runs.
- **Validation sets differ.** Each arm selects its checkpoint on its own validation set, which has the same removal rule applied. This is the pre-registered design. So PEROV and R checkpoints were selected on different validation sets.

## Two things reported that do not decide anything

| | PEROV | R | What the rules would give |
|---|---|---|---|
| Unrelaxed consensus (sensitivity check, not pre-registered) | 3, 3, 2 | 8, 8, 7 | Also template_specific (difference 5) |
| Relaxed fit (secondary metric) | 4, 6, 4 | 8, 8, 8 | Rules not applied; difference 3.33 |

The outcome is the same before and after relaxation, so it does not depend on the ORB-v3 relaxation.

## Per target (`per_target_all_runs.csv`, relaxed consensus)

| Target | PEROV (out of 3 seeds) | R (out of 3 seeds) | G0 ABC2D6 seed 42 |
|---|---|---|---|
| mp-19274, mp-10321, mp-12449 | 3 | 3 | yes |
| mp-6231, mp-19093, mp-16307, mp-6603 | 0 | 3 | yes |
| mp-6389 | 0 | 2 (seeds 42, 44) | yes |
| mp-1215245 (Zr1Ti1Ni2H6) | 2 (seeds 43, 44) | 1 (seed 43) | no |
| mp-557387, mp-556434 | 0 | 0 | no |

- **Same targets as G0.** R1's and R3's 8 consensus targets are exactly G0's ABC2D6 seed-42 set. R2 loses mp-6389 and gains mp-1215245.
- **Where the difference is.** It sits in 5 targets: mp-6231, mp-19093, mp-16307, mp-6603 and mp-6389.
  - The R arm recovers these almost every time; the PEROV arm never does, on any seed.
  - Every R consensus match is at rank 1.
- **Differences from the paper**, recorded but not used for any conclusion:
  - The paper's PEROV arm loses mp-12449, mp-16307, mp-19093, mp-6389 and mp-6603.
  - Our PEROV arm recovers mp-12449 on all three seeds, and never recovers mp-6231.
- Three seeds is a small sample. "Times out of 3" describes what happened; it is not an estimated probability.

## Run health

- **Code:** sample.py, relax.py, score.py and run_eval.sh are byte-identical to the PEROV seed evaluation. r_decision.py is identical to `57970a3`. SHA-256 hashes are in `config.json`.
- **Sampling:** 11 targets × 20 candidates = 220 per R arm.
  - All were written, with 0 failures and every composition correct (sample.py asserts the composition).
  - The checkpoints are the validation-selected ones. Their hashes match the training record, and loading reported no missing or unexpected keys.
  - The sampling seed equals the training seed and is reset before each target (amendment A1).
- **Relaxation:**
  - 0 errors, with the same settings as PEROV.
  - Max atomic force ≤ 0.01 eV/Å: R1 206 / 220, R2 213 / 220, R3 205 / 220. PEROV had 182–189.
  - 10, 8 and 7 candidates used all 500 steps. They keep their step-500 structure and are ranked and scored as usual; no candidate is dropped.
- **Scoring:** every target in every run has 20 files and 20 read. The decision script checks this too.
- **Leakage check (2026-11-24):**
  - In ABC2D6, PEROV and R1–R3, neither train nor val contains any of the 11 targets, or any structure with the same reduced formula as a target.
  - R and PEROV have the same row counts (train 24,317, val 8,150).
- **Not verified:**
  - The byte-for-byte reproducibility check was not repeated. G0 checked it for one target on seed 42 only.
  - R3 started while R1 and R2 were still sampling. Competing for the CPU should change only the run time, not the results, but this was not checked separately.

## Choices the paper does not state

The same as G0:
- the ORB-v3 model is the inferred orb_v3_conservative_inf_omat (**not confirmed**);
- the optimiser is ASE FIRE on a FrechetCellFilter;
- exactly 20 candidates are generated per target;
- sampling runs on the CPU.

## Files

- `decision.json`: the decision, each rule's check, the items that do not decide, and the path and SHA-256 of every input score file
- `per_target_all_runs.csv`: consensus, fit and rank per target for all six runs
- `per_target_consensus.png`: the per-target figure, drawn by `src/csp/plot_r_control.py` (added 2026-11-24)
- `config.json`: the decision, per-run summaries, code and checkpoint hashes, all settings, and the leakage check
- `R1_s42/`, `R2_s43/` and `R3_s44/`, each with:
  - `raw/`: the 220 candidates and `sample_meta.json`
  - `relaxed/`: relaxed, ranked candidates, with a `relax_report.json` per target
  - `score_relaxed.csv`, `score_raw.csv`, and the logs for each step
- `run_R1R2.log`, `run_R3.log`, `started_at`, `started_R3_at`, `finished_R1R2_at`, `finished_R3_at`

## Next, in dependency order

1. Update the status and conclusion in `modules/csp/RANDOM_REMOVAL_CONTROL.md`, then commit (once confirmed).
2. The 7 core pre-registered training runs are now complete.
   - The optional ABC2D6 seeds 43 and 44 would measure training variation without the template loss directly. They would not change this decision.
   - Whether to run them is a separate decision, and they are paid runs.
