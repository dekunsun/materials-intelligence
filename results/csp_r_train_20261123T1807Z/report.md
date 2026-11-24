# CSP 随机删除对照：R1–R3 的训练

日期：2026-11-23 至 11-24（UTC）。这里只记录训练本身。生成、弛豫和打分的结果在 `results/csp_r_eval_20261124T0335Z/`。

## 做了什么

- 按预注册（`src/csp/random_removal_control.py`）训练三个随机删除组：R1 seed 42、R2 seed 43、R3 seed 44。
- **训练配方：** 和 PEROV 三个 seed 完全相同。每个 microbatch 64，梯度累积 4，FP32，106,000 步，按验证损失选 checkpoint。
- **训练包：** 和 PEROV 的训练包逐文件比较过（`bundle_check.json`）。只有 4 个数据文件不同：`train.csv`、`train_ori.pt`、`val.csv`、`val_ori.pt`。它们是每个 R 组自己的随机删除划分，用预注册的抽样种子逐字节重抽核对过（`tests/check_csp_r_data.py`）。代码和测试集都相同。
- **预算（经同意）：** RTX A5000，Secure Cloud，每小时上限 $0.30，3 台，每台最坏 12 小时。

## 结果

| | R1 seed 42 | R2 seed 43 | R3 seed 44 |
|---|---|---|---|
| 完成步数，退出码 | 106,000，0 | 106,000，0 | 106,000，0 |
| 训练时长（含验证） | 8.86 小时（0.301 秒/步） | 8.98 小时（0.305 秒/步） | 9.38 小时（0.319 秒/步） |
| GPU 平均利用率 | 约 65% | 约 64% | 约 63% |
| 按验证损失选出的 checkpoint | 第 36,574 步（epoch 384） | 第 44,649 步（epoch 469） | 第 37,999 步（epoch 399） |
| 该 checkpoint 的验证损失（进度条，3 位有效数字） | 0.845 | 0.856 | 0.847 |
| test_loss（选出的 checkpoint，算一次） | 0.864 | 0.860 | 0.866 |

- **验证损失不能互相比较。** 每个 R 组的验证集是和训练集一起随机抽的，三个 R 组之间、R 和 PEROV 之间的验证集都不同。
- **test_loss 不用来下结论。** 测试集相同，但 test_loss 每次计算会随机抽时间步，只算了一次，也不是预注册指标。
- **速度：** 三台都在 EU-SE-1，速度相近，没有出现 PEROV seed 43 那样慢 25% 的情况。

## 启动过程（`launch_record.json`）

- R1 第一次就创建成功（18:07 UTC）。R2 和 R3 第一次各试 10 次，都没有 A5000 Secure 的空位，没有创建任何 pod。
- 之后用 `src/csp/pod/create_and_guard.sh` 重试：pod 一旦存在就立刻启动 watchdog。R2 在 18:26 UTC 创建。
- **余额暂停：** 18:23 UTC 余额是 $6.67，够 R1、R2 但不够三台的最坏情况，所以暂停了 R3 的重试（当时没有 R3 的 pod）。充值后恢复重试，R3 在 18:39 UTC 创建。充值金额**没有核实**，因为 API key 只有 Pods 权限。

## 费用

| | pod 存在时长 | 按 $0.27/小时估算 |
|---|---|---|
| R1 | 9.11 小时（18:07:18 – 03:13:41） | 约 $2.46 |
| R2 | 9.14 小时（18:26:52 – 03:35:01） | 约 $2.47 |
| R3 | 9.51 小时（18:39:20 – 04:09:34） | 约 $2.57 |
| 合计 | | **约 $7.50** |

是价格乘以时长的估算，没有和账单核对。在批准的最坏情况（约 $10.80）以内。

## 安全措施和清理

- 每台训练结束后约 4–8 分钟（R3 不到 4 分钟），本机监控核对了 pod 上每个 checkpoint 的 SHA-256 和本机一致，然后删除 pod（HTTP 204）。训练后空转约 0.07–0.14 小时。
- 最后一台删除后，API 确认账户里没有 pod，也没有排队中的 pod。
- 三个 watchdog 都没有触发，在对应 pod 删除后手动停掉。pod 端 12 小时备用删除没有触发过，仍然**没有验证过**。
- 这次的临时 SSH 私钥已删除。checkpoint 存在 `data/raw/csp_g0/R1_s42/`、`R2_s43/`、`R3_s44/`（已 gitignore），较早的 epoch checkpoint 在各自的 `superseded/` 里，哈希见 `logs/<RUN>/checkpoint_sha256.txt`。

## 文件

- `config.json`：pod、时间、费用、checkpoint、测试损失、清理记录
- `launch_record.json`：批准、上限、三台 pod 和启动过程
- `bundle_check.json`：三个训练包和 PEROV 训练包的逐文件对比
- `logs/<RUN>/`：`steps.jsonl.gz`、`train_log.txt.gz`、`val_loss_history.csv`、`gpu_util.csv`、`hydra_config/`、`pip_freeze.txt`、`nvidia_smi.txt`、`setup.log`、`equicsp_train.log`、`monitor.log`、`watchdog.log`、`launch.log`（去掉了进度条行）、`pod_created.json`（去掉了公钥）、`checkpoint_sha256.txt`

---

# CSP random-removal control: R1–R3 training

Date: 2026-11-23 to 11-24 (UTC). This records the training only. Sampling, relaxation and scoring results are in `results/csp_r_eval_20261124T0335Z/`.

## What was run

- The three random-removal arms were trained as pre-registered in `src/csp/random_removal_control.py`: R1 seed 42, R2 seed 43, R3 seed 44.
- **Recipe:** the same as the three PEROV seeds. Microbatch 64, gradient accumulation 4, FP32, 106,000 steps, checkpoint selected by validation loss.
- **Bundles:** each was compared file by file with the PEROV bundle (`bundle_check.json`).
  - Only 4 data files differ: `train.csv`, `train_ori.pt`, `val.csv` and `val_ori.pt`.
  - These are each R arm's own random-removal split. They were checked byte for byte by redrawing them from the pre-registered sampling seeds (`tests/check_csp_r_data.py`).
  - Code and test set are the same.
- **Approved budget:** RTX A5000 on Secure Cloud, a ceiling of $0.30/hour, 3 pods, at most 12 hours each.

## Results

| | R1 seed 42 | R2 seed 43 | R3 seed 44 |
|---|---|---|---|
| Steps completed, exit code | 106,000, 0 | 106,000, 0 | 106,000, 0 |
| Training time, including validation | 8.86 h (0.301 s/step) | 8.98 h (0.305 s/step) | 9.38 h (0.319 s/step) |
| Mean GPU utilisation | about 65% | about 64% | about 63% |
| Validation-selected checkpoint | step 36,574 (epoch 384) | step 44,649 (epoch 469) | step 37,999 (epoch 399) |
| Its validation loss (progress bar, 3 significant figures) | 0.845 | 0.856 | 0.847 |
| test_loss (selected checkpoint, computed once) | 0.864 | 0.860 | 0.866 |

- **Validation losses cannot be compared.** Each R arm's validation set was drawn at random together with its training set, so the validation sets differ between the R arms and between R and PEROV.
- **No conclusion is drawn from test_loss.** The test set is shared, but test_loss samples random time steps each time it is computed. It was computed once and is not a pre-registered metric.
- **Speed:** all three pods were in EU-SE-1 and ran at similar speeds. None was 25% slower, as PEROV seed 43's pod was.

## Launch (`launch_record.json`)

- R1 was created on the first try (18:07 UTC). R2 and R3 each failed 10 tries at first, because there was no A5000 Secure capacity. No pod was created.
- They were then retried with `src/csp/pod/create_and_guard.sh`, which starts the watchdog as soon as a pod exists. R2 was created at 18:26 UTC.
- **Balance pause:**
  - At 18:23 UTC the balance was $6.67. That covered R1 and R2, but not the worst case for all three, so R3's retry was paused. No R3 pod existed.
  - After the owner topped up, the retry resumed, and R3 was created at 18:39 UTC.
  - The top-up amount is **not verified**, because the API key has Pods scope only.

## Cost

| | Pod lifetime | At $0.27/hour |
|---|---|---|
| R1 | 9.11 h (18:07:18 – 03:13:41) | about $2.46 |
| R2 | 9.14 h (18:26:52 – 03:35:01) | about $2.47 |
| R3 | 9.51 h (18:39:20 – 04:09:34) | about $2.57 |
| Total | | **about $7.50** |

These are estimates (price × time), not checked against billing. The total is within the approved worst case (about $10.80).

## Safeguards and clean-up

- About 4–8 minutes (R3: under 4) after each run ended, the Mac monitor checked that every checkpoint on the pod matched the Mac copy by SHA-256, then deleted the pod (HTTP 204). Idle time after training was about 0.07–0.14 h.
- After the last deletion, the API confirmed there were no pods and no queued pods on the account.
- None of the three watchdogs fired. Each was stopped by hand after its pod was deleted.
- The pod-side 12-hour backstop never fired, so it is still **unverified**.
- The throwaway SSH private key from these runs is deleted.
- Checkpoints are in `data/raw/csp_g0/R1_s42/`, `R2_s43/` and `R3_s44/` (gitignored).
  - Earlier epoch checkpoints are in each run's `superseded/`.
  - Hashes are in `logs/<RUN>/checkpoint_sha256.txt`.

## Files

- `config.json`: pod details, times, cost, checkpoints, test losses and the clean-up record
- `launch_record.json`: the approval, caps, the three pods and the launch events
- `bundle_check.json`: file-by-file comparison of the three bundles with the PEROV bundle
- `logs/<RUN>/`:
  - `steps.jsonl.gz` and `train_log.txt.gz`
  - `val_loss_history.csv` and `gpu_util.csv`
  - `hydra_config/`, `pip_freeze.txt`, `nvidia_smi.txt`, `setup.log`, `equicsp_train.log`
  - `monitor.log`, `watchdog.log`, `launch.log` (progress-bar lines removed), `pod_created.json` (public key removed), `checkpoint_sha256.txt`
