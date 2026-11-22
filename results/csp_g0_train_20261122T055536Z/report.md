# CSP 随机删除对照：G0 的两次训练

日期：2026-11-22（UTC）。这里只记录训练本身。**G0 检查还没有做**：G0 要用训练好的模型给 11 个 ABC2D6 目标各生成 20 个候选结构，再按论文的流程打分，看 consensus 是否落在 8 ± 1（ABC2D6）和 3 ± 1（PEROV）以内。这一步的流程还没写。

## 做了什么

- ABC2D6 组和 PEROV 组各训练一次，seed 42，预注册配方（`src/csp/random_removal_control.py`）：每个 microbatch 64、梯度累积 4、FP32、上游默认的 Adam 和学习率调度、`deterministic=True`、每 5 个 epoch 验证一次、106,000 个优化步，按验证损失选 checkpoint。命令：`bash src/csp/pod_train.sh <ARM> 42 106000`。
- 硬件：两台 RunPod Secure Cloud 上的 RTX A5000（24 GB，9 个 vCPU，$0.27/小时）。ABC2D6 在 EU-SE-1，PEROV 在 CA-MTL-1：GPU 型号相同，但不是同一台机器。
- 两组的测试集文件完全相同（哈希一致），训练集和验证集不同。

## 结果

| | ABC2D6 | PEROV |
|---|---|---|
| 训练集 / 验证集 / 测试集 | 25,585 / 8,560 / 9,046 | 24,317 / 8,150 / 9,046 |
| 完成步数，退出码 | 106,000，0 | 106,000，0 |
| 训练时长（含验证） | 9.60 小时（0.326 秒/步） | 9.22 小时（0.313 秒/步） |
| GPU 平均利用率 | 约 62% | 约 62% |
| 按验证损失选出的 checkpoint | 第 39,500 步（epoch 394） | 第 34,675 步（epoch 364） |
| 该 checkpoint 的验证损失（进度条显示值，3 位有效数字） | 0.837 | 0.846 |
| 训练结束时的验证损失 | 约 0.93 | 约 0.94 |
| 训练结束后在测试集上的 test_loss（用选出的 checkpoint） | 0.831 | 0.883 |

- **选出的 checkpoint 都在训练前三分之一左右**，之后验证损失回升了约 0.1。这是预注册配方本来的做法（上游默认按 `val_loss` 只保留最好的一个），这里只是记录，不做解读。
- test_loss 是扩散模型的训练损失，每次计算都会随机抽取时间步，这里各只算了一次。它不是 G0 的指标，也不在预注册里，**不能用来下结论**。两组的验证集不同，验证损失也不能直接比较。
- checkpoint 存在 `data/raw/csp_g0/<ARM>_s42/`（已被 gitignore，每个 50 MB），SHA-256 见 `logs/<ARM>/checkpoint_sha256.txt`。`superseded/` 里是训练中途被替换掉的旧的"最好" checkpoint，是每小时备份时留下的副本，不会用到。

## 费用

| | pod 存在时长 | 按 $0.27/小时估算 |
|---|---|---|
| ABC2D6 | 11.05 小时（05:55:36 – 16:58:39） | 约 $2.98 |
| PEROV | 11.04 小时（06:02:46 – 17:05:26） | 约 $2.98 |
| 合计 | | **约 $5.97** |

这是价格乘以时长的估算，没有和 RunPod 账单核对（API key 没有读取账单的权限）。

**其中约 $0.80 是浪费的。** 训练结束后，两台 pod 又空转了 1.26 小时（ABC2D6）和 1.71 小时（PEROV），直到 11 小时上限才被删除。原因是监控脚本的一个 bug：它在删 pod 前会核对 checkpoint 是否都已拷回，但比较的是两边完整的文件列表。上游设置只保留最好的一个 checkpoint，pod 上旧的会被删掉，而本机每小时备份时留下了旧文件，所以两边列表永远对不上，脚本就一直等到上限。checkpoint 本身没有问题：训练结束后的最后一次拷贝里，pod 上所有 checkpoint 都已在本机，大小一致。

修复：`src/csp/pod/pod_monitor.sh` 改为只核对 pod 上现有的每个 checkpoint，在本机都要有、而且 SHA-256 相同。这个检查在本机文件上测过（一致、哈希不同、缺文件三种情况），但**还没有在真实 pod 上完整跑过一次**。

## 安全措施和清理

- 每台 pod 有三道上限：本机监控脚本 11 小时；本机 watchdog 11 小时 20 分；pod 自己的 12 小时备用删除（用 RunPod 注入 pod 的自身凭证，不是我们的 key；没有真正触发过，所以没验证过）。实际是第一道在 11 小时删除的。
- 删除后通过 API 确认：账户里没有 pod，也没有排队中的 pod。
- 这次用的临时 SSH 私钥，以及 A5000 速度测试时遗留的那把，都已删除。

## 文件

- `config.json`：代码和数据的哈希、Hydra 参数、pod 信息、时间、费用估算、测试损失
- `logs/<ARM>/`：`steps.jsonl.gz`（每步时间戳）、`train_log.txt.gz`、`val_loss_history.csv`（从进度条提取的验证损失）、`gpu_util.csv`、`hydra_config/`、`pip_freeze.txt`、`nvidia_smi.txt`、`setup.log`、`monitor.log`、`pod_created.json`、`checkpoint_sha256.txt`
- 脚本：`src/csp/pod_train.sh`、`src/csp/make_pod_bundle.sh`、`src/csp/pod/`（建 pod、监控、watchdog、pod 端备用删除）

---

# CSP random-removal control: the two G0 training runs

Date: 2026-11-22 (UTC). This records the training only. **The G0 check itself has not been done.** G0 needs each trained model to generate 20 candidate structures for each of the 11 ABC2D6 targets, scored with the paper's protocol, and then checks whether consensus lands within 8 ± 1 (ABC2D6) and 3 ± 1 (PEROV). That pipeline is not written yet.

## What was run

- One run each of the ABC2D6 and PEROV arms, seed 42, with the pre-registered recipe in `src/csp/random_removal_control.py`:
  - microbatch 64 with gradient accumulation 4;
  - FP32, with the upstream default Adam and LR schedule;
  - `deterministic=True`;
  - validation every 5 epochs;
  - 106,000 optimiser steps;
  - checkpoint selected by validation loss.

  The command was `bash src/csp/pod_train.sh <ARM> 42 106000`.
- Hardware: two RTX A5000s (24 GB, 9 vCPUs, $0.27/hour) on RunPod Secure Cloud. ABC2D6 ran in EU-SE-1 and PEROV in CA-MTL-1: the same GPU model, but different machines.
- The two arms' test-set files are identical (same hashes). Their training and validation sets differ.

## Results

| | ABC2D6 | PEROV |
|---|---|---|
| Train / val / test structures | 25,585 / 8,560 / 9,046 | 24,317 / 8,150 / 9,046 |
| Steps completed, exit code | 106,000, 0 | 106,000, 0 |
| Training time, including validation | 9.60 h (0.326 s/step) | 9.22 h (0.313 s/step) |
| Mean GPU utilisation | about 62% | about 62% |
| Validation-selected checkpoint | step 39,500 (epoch 394) | step 34,675 (epoch 364) |
| Its validation loss (progress-bar value, 3 significant figures) | 0.837 | 0.846 |
| Validation loss at the end of training | about 0.93 | about 0.94 |
| End-of-run test_loss (on the selected checkpoint) | 0.831 | 0.883 |

- **Both selected checkpoints fall about a third of the way into training.** After that, validation loss rose by about 0.1. Keeping the best checkpoint by `val_loss` is the pre-registered recipe (the upstream default, which keeps one). This is recorded here, not interpreted.
- test_loss is the diffusion training loss, which samples random time steps each time it is computed, and it was computed once per run. It is not the G0 metric and was not pre-registered, so **no conclusion should be drawn from it**. The two arms have different validation sets, so their validation losses are not directly comparable either.
- Checkpoints are in `data/raw/csp_g0/<ARM>_s42/` (gitignored, 50 MB each). Their SHA-256 hashes are in `logs/<ARM>/checkpoint_sha256.txt`.
  - `superseded/` holds earlier "best" checkpoints that were replaced during training. They are copies left by the hourly backup and are not used.

## Cost

| | Pod lifetime | At $0.27/hour |
|---|---|---|
| ABC2D6 | 11.05 h (05:55:36 – 16:58:39) | about $2.98 |
| PEROV | 11.04 h (06:02:46 – 17:05:26) | about $2.98 |
| Total | | **about $5.97** |

These are estimates (price × time), not checked against RunPod's billing; the API key has no billing permission.

**About $0.80 of this was wasted.** After training ended, the pods sat idle for 1.26 h (ABC2D6) and 1.71 h (PEROV) until the 11-hour cap deleted them.
- **Cause:** a bug in the monitor script. Before deleting a pod it checks that every checkpoint has been copied back, but it compared the full file listings on both sides. The upstream setting keeps only the best checkpoint, so older ones are deleted on the pod, while the hourly copies kept them on the Mac. The two listings could never match, so the monitor waited for the cap.
- **The checkpoints are fine:** after training ended, the last copy held every checkpoint on the pod, at the same size.

Fix: `src/csp/pod/pod_monitor.sh` now checks only the checkpoints present on the pod: each must exist on the Mac with the same SHA-256. The check was tested on local files for three cases (match, wrong hash, missing file). It has **not yet run end to end on a real pod**.

## Safeguards and clean-up

- Each pod had three caps:
  1. the Mac monitor at 11 h;
  2. a Mac watchdog at 11 h 20 min;
  3. a backstop on the pod itself at 12 h. It uses the pod's own RunPod-injected credentials, not our key. It never fired, so it is unverified.

  The first cap deleted both pods at 11 h.
- After deletion, the API confirmed there were no pods and no queued pods on the account.
- The throwaway SSH private key used here is deleted, and so is the one left over from the A5000 speed test.

## Files

- `config.json`: code and data hashes, Hydra overrides, pod details, times, cost estimates, test losses
- `logs/<ARM>/`:
  - `steps.jsonl.gz` (a timestamp per step) and `train_log.txt.gz`
  - `val_loss_history.csv` (validation loss taken from the progress bar)
  - `gpu_util.csv`, `hydra_config/`, `pip_freeze.txt`, `nvidia_smi.txt`, `setup.log`
  - `monitor.log`, `pod_created.json`, `checkpoint_sha256.txt`
- Scripts: `src/csp/pod_train.sh`, `src/csp/make_pod_bundle.sh`, and `src/csp/pod/` (pod creation, monitor, watchdog, pod-side backstop)
