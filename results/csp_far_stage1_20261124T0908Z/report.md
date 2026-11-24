# 稳定性筛选的外推检验：第一阶段（WBM）结果

日期：2026-11-24（UTC）。全部在本机 CPU 上算，几分钟，没有用付费算力。设计和规则在运行前提交并推到 GitHub（commit `ffdb574`），见 `modules/csp/FAR_FROM_TRAINING_TEST.md`。

## 结论

**按预登记的规则，三个外推格都是“成立”。** 在 WBM 上，只用 MP 数据训练的前 10 名模型，在框架或化学体系陌生的候选里挑稳定结构的能力，几乎没有下降；只看组成和原型的基线 Wrenformer 则明显下降。

| 格子 | 候选 / 稳定 / 含稳定的框架 | r 中位数 [95% 区间] | d：头部模型 − Wrenformer [95% 区间] | 结果 |
|---|---|---|---|---|
| 结构外推（化学熟悉、框架陌生） | 1,109 / 173 / 37 | 0.944 [0.867, 1.036] | 0.552 [0.447, 0.658] | 成立 |
| 化学外推（化学陌生、框架已知） | 114,879 / 20,282 / 509 | 1.074 [1.040, 1.100] | 0.462 [0.425, 0.506] | 成立 |
| 双重外推 | 653 / 120 / 25 | 1.168 [1.041, 1.218] | 0.490 [0.301, 0.692] | 成立 |

- r 是外推格的归一化分数（NRp，随机为 0、全对为 1）除以插值参照的 NRp；1 表示没有下降。
- **D10 不变。** 预登记写明：只有第一阶段时，只更新证据，不改决定。
- **运行后发现框架键有一个漏洞。** 事后修正后三格仍然成立，但结构外推格的 r 降到 0.908 [0.813, 1.034]，接近门槛。见“运行后发现的问题”。

## 读法

- **结构外推：** 前 10 名的 r 在 0.89–1.02 之间。头部模型 EquiformerV3+DeNS-MP 的 NRp 从插值参照的 0.78 降到 0.72。Wrenformer 从 0.29 降到 0.17（r 0.58），Voronoi RF 的 r 只有 0.19。也就是说，离开已知框架，看结构细节的势函数模型基本保住了能力，只看原型的基线掉得多。
- **老一代模型掉得更多：** 结构外推格里 CHGNet 的 r 是 0.77，MACE-MP-0 是 0.90。
- **化学外推没有下降，r 大于 1。** 这里“化学陌生”多是训练集里没有的三元、四元组合；r 大于 1 可能和这些体系的竞争相更简单有关，**没有验证**，不作结论。

## 敏感性检查（只作描述，不影响判定）

| 变化 | 结构外推格的 r 中位数 | d |
|---|---|---|
| 预登记设置 | 0.944 | 0.552 |
| 只用唯一原型候选 | 0.924 | 0.569 |
| 按弛豫后结构定框架 | 0.919 | 0.541 |
| 用原型标签（S1）代替框架 | 1.050 | 0.552 |
| 按化学体系整群（区间） | [0.880, 1.011] | [0.480, 0.638] |
| 逐个去掉 37 个含稳定候选的框架（范围） | 0.922–0.979 | 0.532–0.584 |

结论不依赖某一种定义，也不依赖某一个框架。详见 `sensitivity.json`。

## 这个结果的范围

- **“远”是温和的远。** WBM 的候选都是元素替换生成的。结构外推格只有 37 个含稳定候选的框架，多数来自 WBM 第 3 轮的替换（母结构是前几轮弛豫出来的 WBM 结构）。框架键在 MP 里没有，但几何上可能仍接近已知结构；连续的几何距离（S3）放在第二阶段。
- **只适用于只用 MP 数据训练的模型。** 用了 OMat24、Alexandria 的模型没有参与判定。
- **真值是 DFT**，不是合成或实测。
- **事先看过的东西：** D2A 已经算过按原型标签（S1）分组的模型指标，显示前 10 名召回率低 1–4 个百分点；本次结构格子是那一组的子集。这一点在设计里写明了。
- **和 CSP 随机移除对照放在一起看**（观察，不是结论）：生成模型恢复结构，强烈依赖训练集里的框架；能量模型判断稳定性，在这种温和的“框架陌生”上几乎不掉。两者任务不同、“远”的程度也不同，不能直接比较。

## 运行后发现的问题（2026-11-24，事后修正）

**预登记的框架键有一个漏洞，会让结构外推格混进一些已知框架。** AFLOW 式标签里的 Wyckoff 字母，是在“按元素分组”的前提下，从几种等价的原点选择里挑一种来规范化的。`far_split.py` 去掉了元素分组，却沿用了已经规范化过的字母，所以同一个框架只要元素分组不同，就可能得到不同的字母，被判成“陌生”。这会让结果偏向“成立”。

**修正：** 去掉元素分组之后，在空间群所有等价的原点选择上重新规范化字母（用 Matbench Discovery 标签器自带的对照表），MP 和 WBM 两边同样处理（`src/csp/far_posthoc_canonical.py`）。1,762 个原先“框架陌生”的结构里，有 398 个其实是已知框架；原先“已知”的一个也没有变。

| 修正后的格子 | 候选 / 稳定 / 含稳定的框架 | r 中位数 [95% 区间] | d [95% 区间] | 按同样规则 |
|---|---|---|---|---|
| 结构外推 | 920 / 129 / 30 | 0.908 [0.813, 1.034] | 0.573 [0.458, 0.687] | 成立 |
| 化学外推 | 115,088 / 20,300 / — | 1.074 [1.041, 1.102] | 0.462 [0.420, 0.506] | 成立 |
| 双重外推 | 444 / 102 / 20 | 1.181 [1.056, 1.236] | 0.477 [0.247, 0.713] | 成立 |

- 修正后结论不变，但结构外推格离门槛更近：r 的区间下限 0.813，只比 0.8 高一点。逐个去掉 30 个框架，r 在 0.88–0.96 之间；按化学体系整群，区间是 [0.84, 0.99]。
- 修正后结构外推格里，前 10 名的 r 在 0.84–1.03 之间；Wrenformer 降到 0.46，CHGNet 0.79，MACE-MP-0 0.94。
- **以预登记的结果为准，修正版是事后分析。** 两个都写在这里，读者可以自己比较。第二阶段的框架键会直接用修正后的规范化。
- 文件：`posthoc_canonical_framework/`（修正后的划分、判定、逐模型结果、敏感性检查）。

## 运行情况

- 判定代码和预登记时的版本逐字节相同（`config.json` 里 `code_unchanged_since_pre_registration: true`）。
- MPtrj 核对：145,923 种材料里有 1,085 个（0.74%）不在 MP 2023 快照中，低于事先定的 1%，按规则参照只用快照。
- 判定用的 10 个模型由脚本从固定文件里选出，和预登记里列出的一致。
- 敏感性脚本 `src/csp/far_sensitivity.py` 是在判定之后写的，只作描述。

## 文件

- `split.csv.gz`、`split_summary.json`：每个 WBM 结构的格子标签（不含模型指标）和各格子的计数
- `decision.json`：预登记判定的结果、区间和阈值
- `per_model_cells.csv`：每个模型在每个外推格的 NRp、插值参照 NRp 和 r
- `sensitivity.json`：敏感性检查
- `config.json`：代码和输入的哈希、命令、MPtrj 核对、时间
- `posthoc_canonical_framework/`：事后修正框架键之后的同一套分析

## 下一步（按依赖顺序）

第二阶段：用 Alexandria 外部数据检验真正远离训练集的结构。先下载一个分片（约 62 MB）确认字段、赝势和 U 值，再写第二阶段的预登记。需要你确认。

---

# Extrapolation test for stability screening: Stage 1 (WBM) results

Date: 2026-11-24 (UTC). Everything ran on the Mac's CPU in a few minutes, with no paid compute. The design and rules were committed and pushed to GitHub before the run (commit `ffdb574`); see `modules/csp/FAR_FROM_TRAINING_TEST.md`.

## Verdict

**Under the pre-registered rules, all three extrapolation cells "hold".** On WBM, the top 10 models trained on MP data alone pick stable structures among candidates with an unfamiliar framework or chemical system almost as well as among familiar ones. Wrenformer, the baseline that sees only composition and prototype, drops clearly.

| Cell | Candidates / stable / frameworks with a stable one | Median r [95% interval] | d: lead model − Wrenformer [95% interval] | Outcome |
|---|---|---|---|---|
| Structural extrapolation (familiar chemistry, unfamiliar framework) | 1,109 / 173 / 37 | 0.944 [0.867, 1.036] | 0.552 [0.447, 0.658] | Holds |
| Chemical extrapolation (unfamiliar chemistry, known framework) | 114,879 / 20,282 / 509 | 1.074 [1.040, 1.100] | 0.462 [0.425, 0.506] | Holds |
| Double extrapolation | 653 / 120 / 25 | 1.168 [1.041, 1.218] | 0.490 [0.301, 0.692] | Holds |

- r is the extrapolation cell's normalised score (NRp: 0 for random, 1 for perfect) divided by the interpolation reference's NRp; 1 means no drop.
- **D10 does not change.** The pre-registration says Stage 1 alone updates the evidence only.
- **A flaw in the framework key was found after the run.** After a post-hoc correction all three cells still hold, but the structural cell's r falls to 0.908 [0.813, 1.034], close to the threshold. See "A problem found after the run".

## Reading it

- **Structural extrapolation:** the top 10 models' r ranges from 0.89 to 1.02. The lead model, EquiformerV3+DeNS-MP, goes from an NRp of 0.78 in the interpolation reference to 0.72. Wrenformer goes from 0.29 to 0.17 (r 0.58), and Voronoi RF's r is only 0.19. So away from known frameworks, the interatomic potentials, which see structural detail, largely keep their ability, while the prototype-only baseline loses much more.
- **Older models drop more:** in the structural cell, CHGNet's r is 0.77 and MACE-MP-0's 0.90.
- **Chemical extrapolation shows no drop; r is above 1.** "Unfamiliar chemistry" here is mostly ternary and quaternary combinations absent from training. r above 1 may reflect simpler competing phases in those systems; this is **not verified**, and no conclusion is drawn.

## Sensitivity checks (descriptive only; they do not affect the decision)

| Change | Structural cell median r | d |
|---|---|---|
| Pre-registered setting | 0.944 | 0.552 |
| Unique-prototype candidates only | 0.924 | 0.569 |
| Framework from the relaxed structure | 0.919 | 0.541 |
| Prototype label (S1) instead of framework | 1.050 | 0.552 |
| Clustering by chemical system (interval) | [0.880, 1.011] | [0.480, 0.638] |
| Leaving out each of the 37 frameworks with a stable candidate (range) | 0.922–0.979 | 0.532–0.584 |

The outcome depends neither on one definition nor on one framework. See `sensitivity.json`.

## Scope of this result

- **"Far" here is mild.** WBM candidates were all generated by element substitution. The structural cell has only 37 frameworks with a stable candidate, mostly from WBM's third substitution round, whose parents were WBM structures relaxed in earlier rounds. Their framework keys are absent from MP, but their geometry may still be close to known structures. Continuous geometric distance (S3) is in Stage 2.
- **It applies only to models trained on MP data alone.** Models that also used OMat24 or Alexandria were not part of the decision.
- **The truth is DFT**, not synthesis or measurement.
- **Seen beforehand:** D2A had already computed model metrics by prototype label (S1), showing the top 10's recall 1–4 points lower; this run's structural cell is a subset of that group. The design says so.
- **Read next to the CSP random-removal control** (an observation, not a conclusion): the generative model's structure recovery depends strongly on frameworks in its training set, while energy models' stability judgements barely drop on this mild kind of "unfamiliar framework". The tasks differ, and so does how far "far" is, so the two cannot be compared directly.

## A problem found after the run (2026-11-24, post-hoc correction)

**The pre-registered framework key had a flaw that lets some known frameworks into the structural cell.** The Wyckoff letters in an AFLOW-style label are canonicalised by picking one of several equivalent origin choices, given the grouping of sites into elements. `far_split.py` dropped the element grouping but kept the letters as canonicalised under it. So the same framework with a different element grouping can end up with different letters and be judged "unfamiliar". That biases the result towards "holds".

**Fix:** after dropping the element grouping, re-canonicalise the letters over all equivalent origin choices of the space group (using the table Matbench Discovery's labeller ships with), on both the MP and WBM sides (`src/csp/far_posthoc_canonical.py`). Of the 1,762 structures that were "unfamiliar framework", 398 are in fact known frameworks; none that was "known" changed.

| Corrected cell | Candidates / stable / frameworks with a stable one | Median r [95% interval] | d [95% interval] | Under the same rules |
|---|---|---|---|---|
| Structural extrapolation | 920 / 129 / 30 | 0.908 [0.813, 1.034] | 0.573 [0.458, 0.687] | Holds |
| Chemical extrapolation | 115,088 / 20,300 / — | 1.074 [1.041, 1.102] | 0.462 [0.420, 0.506] | Holds |
| Double extrapolation | 444 / 102 / 20 | 1.181 [1.056, 1.236] | 0.477 [0.247, 0.713] | Holds |

- The outcome is unchanged after the correction, but the structural cell is closer to the threshold: the lower bound of r is 0.813, just above 0.8. Leaving out each of the 30 frameworks gives r of 0.88–0.96; clustering by chemical system gives [0.84, 0.99].
- In the corrected structural cell, the top 10 models' r ranges from 0.84 to 1.03; Wrenformer falls to 0.46, CHGNet is 0.79 and MACE-MP-0 0.94.
- **The pre-registered result is the one of record; the correction is a post-hoc analysis.** Both are shown here so readers can compare. Stage 2 will use the corrected canonicalisation for its framework key from the start.
- Files: `posthoc_canonical_framework/` (corrected split, decision, per-model results and sensitivity checks).

## Run health

- The decision code is byte-identical to the pre-registered version (`code_unchanged_since_pre_registration: true` in `config.json`).
- MPtrj check: 1,085 of 145,923 materials (0.74%) are not in the MP 2023 snapshot, below the 1% set in advance, so by rule the reference is the snapshot alone.
- The script picked the 10 decision models from a fixed file, matching the list in the pre-registration.
- The sensitivity script `src/csp/far_sensitivity.py` was written after the decision and is descriptive only.

## Files

- `split.csv.gz`, `split_summary.json`: each WBM structure's cell labels (no model metrics) and per-cell counts
- `decision.json`: the pre-registered decision, intervals and thresholds
- `per_model_cells.csv`: each model's NRp, interpolation-reference NRp and r in each extrapolation cell
- `sensitivity.json`: the sensitivity checks
- `config.json`: code and input hashes, commands, the MPtrj check and timings
- `posthoc_canonical_framework/`: the same analysis after the post-hoc correction of the framework key

## Next, in dependency order

Stage 2: test structures that are genuinely far from training, using Alexandria external data. First download one shard (about 62 MB) to check fields, pseudopotentials and U values, then write the Stage 2 pre-registration. This needs your confirmation.
