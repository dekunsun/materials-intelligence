# CSP 随机删除对照：PEROV seed 43、44 的生成、弛豫和打分

日期：2026-11-23（UTC），10:24 – 12:52，全部在本机 CPU 上跑（Apple M3 Pro），没有用付费算力。训练记录在 `results/csp_perov_seeds_train_20261122T224906Z/`。seed 42 的数字来自 G0（`results/csp_g0_score_20261122T174350Z/`）。

## 结论

**PEROV 组三个 seed 的 consensus 是 3、4、4，平均 3.67。预注册的“没有复现”规则（平均 ≥ 6）不适用，实验按预注册继续。**

| | seed 42（G0） | seed 43 | seed 44 | 平均 |
|---|---|---|---|---|
| consensus（弛豫后，主指标） | 3 / 11 | 4 / 11 | 4 / 11 | **3.67** |
| fit（弛豫后） | 4 / 11 | 6 / 11 | 4 / 11 | 4.67 |
| consensus（未弛豫） | 3 / 11 | 3 / 11 | 2 / 11 | 2.67 |
| fit（未弛豫） | 4 / 11 | 4 / 11 | 4 / 11 | 4.00 |

- 这只说明：PEROV 组的低 consensus 在三个训练 seed 上都出现了，seed 之间差 1。ABC2D6 组只训练了 seed 42（consensus 8），没有重复 seed。
- **这还不能回答模板依赖的问题。** “模板特有”和“数据量”两条规则都要等 R1–R3 随机删除组。

## R1–R3 需要达到什么

PEROV 三个 seed 的 consensus 合计 11，所以按预注册的顺序：

| 结果 | 条件（R1–R3 的弛豫后 consensus） |
|---|---|
| 模板特有（template_specific） | 每个 R 都 ≥ 5（都高于 PEROV 最高的 4），**并且**三个 R 合计 ≥ 20（平均 ≥ 6.67） |
| 数据量（data_amount） | 三个 R 合计 ≤ 14（平均 ≤ 4.67），包括 R 比 PEROV 还低的情况 |
| 无法判断（inconclusive） | 其他情况，例如合计 15–19，或合计 ≥ 20 但有一个 R ≤ 4 |

这些阈值是从预注册规则直接算出来的，不是新加的。

## 逐个目标（`per_target_three_seeds.csv`）

| 目标 | 参考空间群 | 三个 seed 中 consensus 的次数 | fit 的次数 |
|---|---|---|---|
| mp-19274、mp-10321、mp-12449 | 123、14、14 | 3 / 3 | 3 / 3 |
| mp-1215245（Zr1Ti1Ni2H6） | 38 | 2 / 3（seed 43、44） | 2 / 3 |
| mp-557387 | 34 | 0 / 3 | 2 / 3（seed 42、43，空间群不对） |
| mp-16307 | 225 | 0 / 3 | 1 / 3（seed 43，空间群不对） |
| mp-6231、mp-19093、mp-6389、mp-6603、mp-556434 | | 0 / 3 | 0 / 3 |

- 有 3 个目标在三个 seed 上都是 consensus，而且都排第 1。seed 之间的差别全部来自 mp-1215245。
- mp-6231（立方双钙钛矿）在论文里是 consensus，三个 seed 都没有任何匹配。论文的数字只用于 G0，这里记录下来但不用来下结论。
- 3 个 seed 的样本很小。“每个目标几次”只是描述，不是估计出的概率。

## 弛豫的影响比 G0 大

G0 里未弛豫和弛豫后几乎一样。这两次不一样：seed 43 弛豫后 fit 从 4 变成 6；seed 44 弛豫后 consensus 从 2 变成 4（mp-1215245 和 mp-12449 都是弛豫后才出现空间群正确的匹配）。所以 ORB-v3 的具体模型和设置（推断出来的，**没有得到确认**）对这些数有影响。主指标按预注册用弛豫后的数；R1–R3 必须用完全相同的弛豫设置，组间比较才对等。

## 运行情况

- **代码：** sample.py、relax.py、score.py 和 G0 用的逐字节相同（SHA-256 见 `config.json`）。这次用新写的 `src/csp/g0/run_eval.sh` 调用它们，步骤和 G0 的 `run_g0.sh` 相同。
- **生成：** 每个 seed 11 个目标 × 20 个候选 = 220 个，全部写出，0 个失败，成分全部正确。checkpoint 是按验证损失选出的那个（seed 43 第 34,200 步，seed 44 第 47,025 步），哈希和训练记录一致，参数加载没有缺失或多余的键。生成种子等于训练种子，每个目标前重设（修订 A1）。
- **弛豫：** 0 个报错。最大原子力 ≤ 0.01 eV/Å 的：seed 43 182 / 220，seed 44 189 / 220（G0 的 PEROV 是 188）。用满 500 步的：20 个和 22 个。没收敛的候选保留第 500 步的结构，照常参与排序和打分，没有删掉任何候选。
- **没有核实：** 这次没有重跑逐字节可重复性检查（G0 只查过 seed 42 的一个目标）。

## 论文没写、这里自己选的

和 G0 相同：ORB-v3 模型是推断的 orb_v3_conservative_inf_omat（**没有确认**）；优化器 ASE FIRE + FrechetCellFilter；每个目标正好生成 20 个；在 CPU 上生成。

## 文件

- `config.json`：三个 seed 的汇总、各条规则的状态、R1–R3 的阈值、代码和 checkpoint 的哈希、各项设置
- `per_target_three_seeds.csv`：三个 seed 每个目标的 fit、consensus、排名
- `PEROV_s43/`、`PEROV_s44/`：`raw/`（220 个候选和 `sample_meta.json`）、`relaxed/`（弛豫、排序后的候选和每个目标的 `relax_report.json`）、`score_relaxed.csv`、`score_raw.csv` 和各步日志
- `run.log`、`started_at`、`finished_at`

## 下一步（按依赖顺序）

预注册的下一步是训练 R1–R3 随机删除组（R1 seed 42、R2 seed 43、R3 seed 44）。先要为每个 R 组做训练包，然后每次付费运行都要先说明 GPU、价格和上限，得到同意后再启动。

---

# CSP random-removal control: sampling, relaxation and scoring of PEROV seeds 43 and 44

Date: 2026-11-23 (UTC), 10:24 – 12:52. Everything ran on the Mac's CPU (Apple M3 Pro), with no paid compute. The training record is in `results/csp_perov_seeds_train_20261122T224906Z/`. Seed 42's numbers come from G0 (`results/csp_g0_score_20261122T174350Z/`).

## Verdict

**PEROV's relaxed consensus over three seeds is 3, 4 and 4, a mean of 3.67. The pre-registered not_reproduced rule (mean ≥ 6) does not apply, so the experiment continues as pre-registered.**

| | seed 42 (G0) | seed 43 | seed 44 | Mean |
|---|---|---|---|---|
| Consensus (relaxed, primary) | 3 / 11 | 4 / 11 | 4 / 11 | **3.67** |
| Fit (relaxed) | 4 / 11 | 6 / 11 | 4 / 11 | 4.67 |
| Consensus (unrelaxed) | 3 / 11 | 3 / 11 | 2 / 11 | 2.67 |
| Fit (unrelaxed) | 4 / 11 | 4 / 11 | 4 / 11 | 4.00 |

- **What this shows:** PEROV's low consensus appears on all three training seeds, with a spread of 1 between seeds. The ABC2D6 arm was trained on seed 42 only (consensus 8) and has no repeat seeds.
- **What it does not show:** an answer to the template-dependence question. The template_specific and data_amount rules both need the R1–R3 random-removal arms.

## What R1–R3 would need

The three PEROV seeds sum to 11. So, in the pre-registered order:

| Outcome | Condition (relaxed consensus of R1–R3) |
|---|---|
| template_specific | Every R ≥ 5 (all above PEROV's highest, 4), **and** the three R sum to ≥ 20 (mean ≥ 6.67) |
| data_amount | The three R sum to ≤ 14 (mean ≤ 4.67), including R scoring below PEROV |
| inconclusive | Anything else, for example a sum of 15–19, or a sum ≥ 20 with one R ≤ 4 |

These thresholds follow directly from the pre-registered rules. Nothing new is added.

## Per target (`per_target_three_seeds.csv`)

| Target | Reference space group | Consensus, out of 3 seeds | Fit, out of 3 seeds |
|---|---|---|---|
| mp-19274, mp-10321, mp-12449 | 123, 14, 14 | 3 / 3 | 3 / 3 |
| mp-1215245 (Zr1Ti1Ni2H6) | 38 | 2 / 3 (seeds 43, 44) | 2 / 3 |
| mp-557387 | 34 | 0 / 3 | 2 / 3 (seeds 42, 43; wrong space group) |
| mp-16307 | 225 | 0 / 3 | 1 / 3 (seed 43; wrong space group) |
| mp-6231, mp-19093, mp-6389, mp-6603, mp-556434 | | 0 / 3 | 0 / 3 |

- Three targets are consensus on every seed, each at rank 1. All of the seed-to-seed difference comes from mp-1215245.
- mp-6231 (a cubic double perovskite) is consensus in the paper, but has no match at all on any of our three seeds. The paper's numbers are used only for G0, so this is recorded but no conclusion is drawn from it.
- Three seeds is a small sample. "Times out of 3" describes what happened; it is not an estimated probability.

## Relaxation matters more than in G0

In G0, unrelaxed and relaxed scores were nearly the same. Here they are not:
- seed 43's fit goes from 4 unrelaxed to 6 relaxed;
- seed 44's consensus goes from 2 to 4. For both mp-1215245 and mp-12449, a match with the right space group appears only after relaxation.

So the ORB-v3 model and its settings (inferred, **not confirmed**) do move these counts. The primary metric is the relaxed count, as pre-registered. R1–R3 must use exactly the same relaxation settings for the comparison between arms to be like for like.

## Run health

- **Code:** sample.py, relax.py and score.py are byte-identical to the versions used in G0 (SHA-256 in `config.json`). They were called by the new `src/csp/g0/run_eval.sh`, which runs the same steps as G0's `run_g0.sh`.
- **Sampling:** 11 targets × 20 candidates = 220 per seed.
  - All were written, with 0 failures and every composition correct.
  - The checkpoints are the validation-selected ones (seed 43 step 34,200, seed 44 step 47,025). Their hashes match the training record, and loading reported no missing or unexpected keys.
  - The sampling seed equals the training seed and is reset before each target (amendment A1).
- **Relaxation:**
  - 0 errors.
  - Max atomic force ≤ 0.01 eV/Å: 182 / 220 (seed 43) and 189 / 220 (seed 44). G0's PEROV run had 188.
  - 20 and 22 candidates used all 500 steps. They keep their step-500 structure and are ranked and scored as usual; no candidate is dropped.
- **Not verified:** the byte-for-byte reproducibility check was not repeated here. G0 checked it for one target on seed 42 only.

## Choices the paper does not state

The same as G0:
- the ORB-v3 model is the inferred orb_v3_conservative_inf_omat (**not confirmed**);
- the optimiser is ASE FIRE on a FrechetCellFilter;
- exactly 20 candidates are generated per target;
- sampling runs on the CPU.

## Files

- `config.json`: the three-seed summary, the status of each rule, the R1–R3 thresholds, code and checkpoint hashes, and all settings
- `per_target_three_seeds.csv`: fit, consensus and rank per target for the three seeds
- `PEROV_s43/` and `PEROV_s44/`, each with:
  - `raw/`: the 220 candidates and `sample_meta.json`
  - `relaxed/`: relaxed, ranked candidates, with a `relax_report.json` per target
  - `score_relaxed.csv`, `score_raw.csv`, and the logs for each step
- `run.log`, `started_at`, `finished_at`

## Next, in dependency order

The pre-registered next step is training the R1–R3 random-removal arms (R1 seed 42, R2 seed 43, R3 seed 44).
- A training bundle has to be built for each R arm first.
- Each paid run needs a statement of GPU, price and caps, and approval, before it starts.
