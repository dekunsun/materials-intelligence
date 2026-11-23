# CSP 随机删除对照：PEROV seed 43、44 的训练

日期：2026-11-22 至 11-23（UTC）。这里只记录训练本身。生成、弛豫和打分的结果在 `results/csp_perov_seeds_eval_20261123T1025Z/`。

## 做了什么

- G0 通过后，按预注册（`src/csp/random_removal_control.py`）训练 PEROV 组的第 2、3 次运行：seed 43 和 44。配方和 G0 完全相同：每个 microbatch 64、梯度累积 4、FP32、106,000 步、按验证损失选 checkpoint。训练包和 G0 的 PEROV 训练包逐字节相同（`a68a65dd…`），所以代码和数据都相同，只有 seed 不同。
- 预算经同意：RTX A5000，Secure Cloud，每小时上限 $0.30，每台最坏 12 小时。

## 结果

| | seed 43 | seed 44 | （对照：seed 42，G0） |
|---|---|---|---|
| 完成步数，退出码 | 106,000，0 | 106,000，0 | 106,000，0 |
| 训练时长（含验证） | 11.40 小时（0.387 秒/步） | 8.99 小时（0.305 秒/步） | 9.22 小时（0.313 秒/步） |
| GPU 平均利用率 | 约 49% | 约 63% | 约 62% |
| 按验证损失选出的 checkpoint | 第 34,200 步（epoch 359） | 第 47,025 步（epoch 494） | 第 34,675 步（epoch 364） |
| 该 checkpoint 的验证损失（进度条，3 位有效数字） | 0.849 | 0.865 | 0.846 |
| 训练结束时的验证损失 | 0.917 | 0.943 | 约 0.94 |
| test_loss（选出的 checkpoint，算一次） | 0.874 | 0.892 | 0.883 |

- 三个 seed 的验证集相同，所以这里的验证损失可以互相比较；但它只是 3 位有效数字的进度条读数。test_loss 每次计算会随机抽时间步，只算了一次，不是预注册指标，不用来下结论。
- seed 43 的 pod 比另外几台慢约 25%，GPU 利用率也低。两台都是 A5000、同一机房（EU-SE-1），原因可能是那台主机的 CPU 或数据加载，**没有核实**。速度不影响训练结果本身（同样的步数和配方），只影响时间和费用。

## 上限的改动（经同意）

seed 43 按 0.37 秒/步推算，会在本机监控的 11 小时上限之后几分钟才结束。2026-11-22 23:27 UTC，经同意把它的本机监控上限改为 11 小时 50 分、watchdog 改为 11 小时 55 分；pod 端 12 小时备用删除不变。为此 `src/csp/pod/pod_monitor.sh` 的上限参数改为可以写成“小时:分钟”。替换脚本时用新文件替换，seed 44 正在运行的监控不受影响。

## 费用

| | pod 存在时长 | 按 $0.27/小时估算 |
|---|---|---|
| seed 43 | 11.57 小时（22:49:06 – 10:22:56） | 约 $3.12 |
| seed 44 | 9.14 小时（22:49:37 – 07:57:39） | 约 $2.47 |
| 合计 | | **约 $5.59** |

是价格乘以时长的估算，没有和账单核对。在批准的最坏情况（约 $6.5）以内。

## 安全措施和清理

- **修过的监控脚本第一次在真实 pod 上完整跑通**：训练结束后约 7 分钟，它核对了 pod 上每个 checkpoint 的 SHA-256 与本机一致，然后删除 pod。空转时间每台约 0.12 小时（G0 是 1.26 和 1.71 小时）。
- 删除后 API 确认账户里没有 pod，也没有排队中的 pod。seed 44 的 watchdog 后来又发了一次 DELETE，返回 404（pod 已不存在）；seed 43 的 watchdog 在 pod 删除后被手动停掉。
- pod 端备用删除没有触发过，仍然**没有验证过**。
- 这次的临时 SSH 私钥已删除。checkpoint 存在 `data/raw/csp_g0/PEROV_s43/`、`PEROV_s44/`（已 gitignore），哈希见 `logs/<RUN>/checkpoint_sha256.txt`。

## 文件

- `config.json`：pod、时间、费用、checkpoint、测试损失、上限改动的记录
- `logs/<RUN>/`：`steps.jsonl.gz`、`train_log.txt.gz`、`val_loss_history.csv`、`gpu_util.csv`、`hydra_config/`、`pip_freeze.txt`、`nvidia_smi.txt`、`setup.log`、`equicsp_train.log`、`monitor.log`、`watchdog.log`、`launch.log`（去掉了进度条行）、`pod_created.json`、`checkpoint_sha256.txt`

---

# CSP random-removal control: PEROV seed 43 and 44 training

Date: 2026-11-22 to 11-23 (UTC). This records the training only. Sampling, relaxation and scoring results are in `results/csp_perov_seeds_eval_20261123T1025Z/`.

## What was run

- After G0 passed, the PEROV arm's runs 2 and 3 (seeds 43 and 44) were trained as pre-registered in `src/csp/random_removal_control.py`.
  - The recipe is the same as G0: microbatch 64, gradient accumulation 4, FP32, 106,000 steps, checkpoint selected by validation loss.
  - The bundle is byte-identical to G0's PEROV bundle (`a68a65dd…`). So code and data are the same, and only the seed differs.
- Approved budget: RTX A5000 on Secure Cloud, a ceiling of $0.30/hour, at most 12 hours per pod.

## Results

| | seed 43 | seed 44 | (for reference: seed 42, G0) |
|---|---|---|---|
| Steps completed, exit code | 106,000, 0 | 106,000, 0 | 106,000, 0 |
| Training time, including validation | 11.40 h (0.387 s/step) | 8.99 h (0.305 s/step) | 9.22 h (0.313 s/step) |
| Mean GPU utilisation | about 49% | about 63% | about 62% |
| Validation-selected checkpoint | step 34,200 (epoch 359) | step 47,025 (epoch 494) | step 34,675 (epoch 364) |
| Its validation loss (progress bar, 3 significant figures) | 0.849 | 0.865 | 0.846 |
| Validation loss at the end of training | 0.917 | 0.943 | about 0.94 |
| test_loss (selected checkpoint, computed once) | 0.874 | 0.892 | 0.883 |

- The three seeds share one validation set, so these validation losses can be compared. They are still only 3-significant-figure progress-bar readings.
- test_loss samples random time steps each time it is computed and was computed once. It is not a pre-registered metric, so no conclusion is drawn from it.
- The seed 43 pod ran about 25% slower than the others, with lower GPU utilisation.
  - Both pods were A5000s in the same data centre (EU-SE-1). The host's CPU or data loading may be the cause; this is **not verified**.
  - Speed does not change the training itself (same steps and recipe), only time and cost.

## Cap change (approved)

At 0.37 s/step, seed 43 was projected to finish a few minutes after the Mac monitor's 11-hour cap.
- At 2026-11-22 23:27 UTC, with the owner's approval, its monitor cap was raised to 11 h 50 min and its watchdog to 11 h 55 min. The pod-side 12-hour backstop was unchanged.
- To allow this, `src/csp/pod/pod_monitor.sh` now accepts the cap as hours:minutes.
- The script was replaced with a new file, so seed 44's running monitor was not affected.

## Cost

| | Pod lifetime | At $0.27/hour |
|---|---|---|
| seed 43 | 11.57 h (22:49:06 – 10:22:56) | about $3.12 |
| seed 44 | 9.14 h (22:49:37 – 07:57:39) | about $2.47 |
| Total | | **about $5.59** |

These are estimates (price × time), not checked against billing. The total is within the approved worst case (about $6.5).

## Safeguards and clean-up

- **The fixed monitor ran end to end on real pods for the first time.**
  - About 7 minutes after training ended, it checked that every checkpoint on each pod matched the Mac copy by SHA-256, then deleted the pod.
  - Idle time was about 0.12 h per pod (G0: 1.26 h and 1.71 h).
- After deletion, the API confirmed there were no pods and no queued pods on the account.
  - Seed 44's watchdog later sent another DELETE and got 404, because the pod no longer existed.
  - Seed 43's watchdog was stopped by hand after its pod was deleted.
- The pod-side backstop never fired, so it is still **unverified**.
- The throwaway SSH private key from these runs is deleted.
- Checkpoints are in `data/raw/csp_g0/PEROV_s43/` and `PEROV_s44/` (gitignored). Their hashes are in `logs/<RUN>/checkpoint_sha256.txt`.

## Files

- `config.json`: pod details, times, cost, checkpoints, test losses, and the record of the cap change
- `logs/<RUN>/`:
  - `steps.jsonl.gz` and `train_log.txt.gz`
  - `val_loss_history.csv` and `gpu_util.csv`
  - `hydra_config/`, `pip_freeze.txt`, `nvidia_smi.txt`, `setup.log`, `equicsp_train.log`
  - `monitor.log`, `watchdog.log`, `launch.log` (progress-bar lines removed), `pod_created.json`, `checkpoint_sha256.txt`
