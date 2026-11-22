# CSP 随机删除对照：G0 runner 检查结果

日期：2026-11-22（UTC），17:44 – 20:03，全部在本机 CPU 上跑（Apple M3 Pro），没有用付费算力。

## 结论

**G0 通过。** 预注册的标准是：我们自己训练的两个模型，consensus 要落在论文数值 ± 1 以内。

| | 论文 | 我们（弛豫后，主指标） | 我们（未弛豫） | 标准 | 结果 |
|---|---|---|---|---|---|
| ABC2D6 组 consensus | 8 / 11 | **8 / 11** | 7 / 11 | 7–9 | 通过 |
| PEROV 组 consensus | 3 / 11 | **3 / 11** | 3 / 11 | 2–4 | 通过 |
| ABC2D6 组 fit | 10 / 11 | 8 / 11 | 8 / 11 | 不是 G0 指标 | |
| PEROV 组 fit | 7 / 11 | 4 / 11 | 4 / 11 | 不是 G0 指标 | |

两个数都和论文相同，不只是在 ± 1 以内。这只说明我们的流程（训练、生成、弛豫、打分）在这一个 seed 上能得到和论文一样的 consensus 数，**不说明**模板依赖的问题有了答案。那要等 PEROV 的另外两个 seed 和 R1–R3 随机删除组。

## 逐个目标对照（`per_target_vs_paper.csv`）

- **ABC2D6 组：** consensus 在 11 个目标上逐个一致。fit 有 2 个目标不同：mp-557387 和 mp-1215245，论文有匹配但空间群不对，我们连匹配都没有。所以 consensus 不受影响。
- **PEROV 组：** consensus 数相同，但有 2 个目标互换了：
  - mp-6231（Ba2ErSbO6，立方双钙钛矿）：论文 consensus，我们没有任何匹配；
  - mp-12449：论文只有 fit（排第 3），我们是 consensus（排第 1）。

  fit 有 3 个目标不同（mp-6231、mp-16307、mp-6603），都是论文有、我们没有。
- **两组的 fit 都比论文少**，分别少 2 个和 3 个。原因还没查清。可能的来源：
  - 论文没说保留最好的 20 个之前一共生成了多少个，我们正好生成 20 个；如果论文生成得更多，每个目标的机会就更多；
  - ORB-v3 的具体模型和优化器是推断出来的（见下文）；
  - 只有一个 seed，抽样本身就有波动。

  fit 不是预注册的 G0 指标。这里记录下来，是因为它提示：**拿我们的 fit 数直接和论文的 fit 数比，是不对等的**。后续各组之间的比较应该都用我们自己的流程算出的数。

## 运行情况

- **生成：** 每组 11 个目标 × 20 个候选 = 220 个，全部写出，0 个失败，成分全部正确。checkpoint 是按验证损失选出的那个（ABC2D6 第 39,500 步，PEROV 第 34,675 步），参数加载没有缺失或多余的键。
- **可重复性：** PEROV 的 mp-6231 和之前一次测试运行（同一 seed、同一 checkpoint、同一台机器）生成的 20 个 CIF 逐字节相同。只查了这一个目标。
- **弛豫：** 0 个报错。最大原子力 ≤ 0.01 eV/Å 的：ABC2D6 197 / 220，PEROV 188 / 220。用满 500 步的：16 个和 24 个。没收敛的候选保留了第 500 步的结构，照常参与排序和打分，没有删掉任何候选。
- **未弛豫的结果**几乎一样（只有 ABC2D6 的 mp-19093 少一个 consensus），所以弛豫这一步的具体设置对 G0 结论影响不大。

## 论文没写、这里自己选的

- **ORB-v3 的具体模型：** orb_v3_conservative_inf_omat。是在论文公开的候选结构上比较 8 个模型后推断的（残余力最小，能量顺序和公开排名最接近），**没有得到确认**。
- **优化器：** ASE FIRE + FrechetCellFilter（原子位置和晶胞一起弛豫）。
- **生成数量：** 保留最好的 20 个之前生成多少个，论文没写；我们正好生成 20 个。
- **生成设备：** CPU。训练在 GPU 上，生成在 CPU 上。后面的运行也都在 CPU 上生成，保持一致。

## 打分器的检查

打分器（`src/csp/g0/score.py`）用在论文公开的候选结构上（`ablation_top20_predictions.zip`），得到 ABC2D6 fit 10、consensus 8，PEROV fit 7、consensus 3，每个目标都和论文一致。所以上面的差异来自候选结构本身，不是来自打分方法。

## 文件

- `config.json`：判定、汇总数字、checkpoint 和代码的哈希、参考结构的哈希、各项设置、自己选的设置
- `per_target_vs_paper.csv`：每个目标上论文和我们的 fit、consensus、排名
- `<ARM>/raw/`：生成的 220 个候选和 `sample_meta.json`；`<ARM>/relaxed/`：弛豫、排序后的候选和每个目标的 `relax_report.json`
- `<ARM>/score_relaxed.csv`、`score_raw.csv`，以及各步日志
- 脚本：`src/csp/g0/`（`run_g0.sh`、`sample.py`、`relax.py`、`score.py`、`orb_variant_check.py`）

## 下一步（按依赖顺序）

G0 通过后，预注册的下一步是 PEROV seed 43、44 和 R1–R3 随机删除组的训练（A5000 Secure，生成放在 CPU 上）。每次付费运行都要先得到同意。

---

# CSP random-removal control: G0 runner-check results

Date: 2026-11-22 (UTC), 17:44 – 20:03. Everything ran on the Mac's CPU (Apple M3 Pro), with no paid compute.

## Verdict

**G0 passes.** The pre-registered criterion is that our two self-trained models give a consensus count within ± 1 of the paper's.

| | Paper | Ours (relaxed, primary) | Ours (unrelaxed) | Criterion | Result |
|---|---|---|---|---|---|
| ABC2D6 arm consensus | 8 / 11 | **8 / 11** | 7 / 11 | 7–9 | pass |
| PEROV arm consensus | 3 / 11 | **3 / 11** | 3 / 11 | 2–4 | pass |
| ABC2D6 arm fit | 10 / 11 | 8 / 11 | 8 / 11 | not a G0 metric | |
| PEROV arm fit | 7 / 11 | 4 / 11 | 4 / 11 | not a G0 metric | |

Both counts equal the paper's, not just within ± 1.
- **What this shows:** on this one seed, our pipeline (training, sampling, relaxation, scoring) reproduces the paper's consensus counts.
- **What it does not show:** an answer to the template-dependence question. That needs the other two PEROV seeds and the R1–R3 random-removal arms.

## Per-target comparison (`per_target_vs_paper.csv`)

- **ABC2D6 arm:** consensus agrees on all 11 targets.
  - Fit differs on 2 targets, mp-557387 and mp-1215245. In the paper they match with the wrong space group; ours don't match at all.
  - So consensus is unaffected.
- **PEROV arm:** the consensus count is the same, but 2 targets swap:
  - mp-6231 (Ba2ErSbO6, a cubic double perovskite): consensus in the paper; no match at all for us.
  - mp-12449: fit only in the paper (rank 3); consensus for us (rank 1).

  Fit differs on 3 targets (mp-6231, mp-16307, mp-6603). Each fits in the paper and not for us.
- **Both arms have fewer fits than the paper:** 2 fewer for ABC2D6 and 3 fewer for PEROV. The cause is not yet established. Possible sources:
  - The paper does not say how many candidates it generated before keeping the 20 lowest-energy ones. We generate exactly 20. If the paper generated more, each target had more chances.
  - The ORB-v3 model and the optimiser are inferred (see below).
  - There is one seed only, so sampling noise alone can move these counts.

  Fit is not the pre-registered G0 metric. It is recorded because it shows that **comparing our fit counts directly with the paper's would not be like for like**. Later comparisons between arms should all use numbers from our own pipeline.

## Run health

- **Sampling:** 11 targets × 20 candidates = 220 per arm.
  - All were written, with 0 failures and every composition correct.
  - The checkpoints are the validation-selected ones (ABC2D6 step 39,500, PEROV step 34,675). Loading them reported no missing or unexpected keys.
- **Reproducibility:** for PEROV mp-6231, the 20 CIFs are byte-identical to an earlier test run with the same seed, checkpoint and machine. Only this one target was checked.
- **Relaxation:**
  - 0 errors.
  - Max atomic force ≤ 0.01 eV/Å: 197 / 220 (ABC2D6) and 188 / 220 (PEROV).
  - 16 and 24 candidates used all 500 steps. They keep their step-500 structure and are ranked and scored as usual; no candidate is dropped.
- **Unrelaxed scores** are nearly the same; only ABC2D6 mp-19093 loses its consensus. So the exact relaxation settings have little effect on the G0 verdict.

## Choices the paper does not state

- **ORB-v3 model:** orb_v3_conservative_inf_omat.
  - We inferred it by comparing 8 models on the paper's released candidates. It gives the smallest residual forces and the energy order closest to the released ranks.
  - It is **not confirmed**.
- **Optimiser:** ASE FIRE on a FrechetCellFilter, which relaxes positions and cell together.
- **Number generated:** the paper does not say how many candidates were generated before keeping the best 20. We generate exactly 20.
- **Sampling device:** CPU. Training was on GPU and sampling on CPU. Later runs will also be sampled on CPU, for consistency.

## Scorer check

On the paper's released candidates (`ablation_top20_predictions.zip`), the scorer (`src/csp/g0/score.py`) gives:
- ABC2D6: fit 10, consensus 8;
- PEROV: fit 7, consensus 3.

Every target agrees with the paper. So the differences above come from the candidates themselves, not from the scoring.

## Files

- `config.json`: the verdict, summary counts, checkpoint and code hashes, reference-structure hashes, all settings, and the choices made here
- `per_target_vs_paper.csv`: fit, consensus and rank per target, paper vs ours
- `<ARM>/raw/`: the 220 generated candidates and `sample_meta.json`
- `<ARM>/relaxed/`: relaxed, ranked candidates, with a `relax_report.json` per target
- `<ARM>/score_relaxed.csv`, `score_raw.csv`, and the logs for each step
- Scripts: `src/csp/g0/` (`run_g0.sh`, `sample.py`, `relax.py`, `score.py`, `orb_variant_check.py`)

## Next, in dependency order

With G0 passed, the pre-registered next step is training PEROV seeds 43 and 44 and the R1–R3 random-removal arms. Training runs on A5000 Secure, and sampling on the CPU. Each paid run needs approval first.
