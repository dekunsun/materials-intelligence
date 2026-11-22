# CSP 随机删除对照：1,000 步 smoke test

日期：2026-11-22（UTC）。这次只是费用测量，不是实验结果：只训练了 1,000 步，模型还远没训练好。

## 做了什么

- 训练对象：PEROV 组、seed 42，用预注册的 EquiCSP 配方（见 `src/csp/random_removal_control.py`）：每个 microbatch 64、梯度累积 4（等效 batch 256）、FP32、上游默认的 Adam 和学习率调度、`deterministic=True`、每 5 个 epoch 验证一次。和正式训练相比，唯一的差别是 `max_steps=1000`（正式训练为 106,000）。
- 数据：本机预处理好的 PEROV 数据（训练 24,317 条，验证 8,150 条，测试 9,046 条），文件哈希见 `config.json`。
- 硬件：RunPod Secure Cloud 上的 1 张 NVIDIA A40（显存 48 GB），API 返回的价格为 $0.59/小时。原本打算用 RTX A5000（$0.27/小时）或 RTX 3090，但这两种当时都没有空闲机器。
- 软件：Python 3.8.20、torch 1.9.0+cu111、torch-scatter 2.0.9、torch-sparse 0.6.12、pytorch_lightning 1.3.8。完整版本清单见 `logs/pip_freeze.txt`。
- 流程：本机打包 → 上传 → 在 pod 上装环境（44 秒）→ 训练 → 取回日志 → 终止 pod，并通过 API 确认已没有任何 pod 或排队中的 pod。

## 测量结果

| 指标 | 数值 |
|---|---|
| 1,000 步总训练时间（含 2 次验证） | 293.0 秒，即每步 0.293 秒 |
| 稳定阶段每步（不含前 50 步和验证） | 平均 0.285 秒，中位数 0.283 秒，p90 0.295 秒 |
| 每次验证 | 约 3.85 秒 |
| GPU 利用率（每 15 秒采样一次） | 48–67%，通常约 62% |
| 显存 | torch 峰值分配 2.2 GiB；nvidia-smi 显示最多 9.6 GB |
| 训练是否正常结束 | 是（exit 0，最后跑了测试集评估） |

## 正式训练的费用估算

假设：同一种 GPU、同一价格；每步 0.293 秒（已包含验证时间，正式训练同样每约 475 步验证一次）；每次训练另加约 10 分钟用于开机、装环境、上传和收尾。

| | 时长 | 费用（A40 Secure，$0.59/小时） |
|---|---|---|
| 1 次正式训练（106,000 步） | 约 8.8 小时 | 约 $5.2 |
| 7 次核心训练 | 约 62 GPU 小时 | 约 $36 |
| 9 次（含 2 次可选） | 约 79 GPU 小时 | 约 $47 |

几次训练可以同时在不同 pod 上跑，这样总耗时约 9 小时。ABC2D6 组的训练集略大（25,585 条），但每步的计算量只取决于 batch 大小，所以每步时间按相同处理。

本次测试花费：pod 从创建（03:52:12）到终止（04:04:39）共 12 分 27 秒，按 $0.59/小时约 $0.12。这个数字是用价格乘以时长算出来的；当前 API key 没有读取账单的权限，所以没有和 RunPod 账单核对。

## 需要注意的地方

- **只测了一次**，在一台机器上。不同机器、不同时段的速度可能不同。
- **GPU 利用率只有约 62%**，说明有一部分时间花在 CPU 上（上游配置里数据加载 `num_workers=0`）。所以更便宜的 GPU（比如 A5000）不一定慢很多，在一张 A40 上同时跑几次训练也可能更省钱。这两点都**没有测过**，只是可能的省钱方向。
- **论文用的 GPU 是 V100 16GB，我们用的是 A40。** 配方相同，但不同 GPU 上的数值结果不会完全一致。预注册里的 G0 检查（我们复现的 ABC2D6 和 PEROV 结果要落在论文数值 ±1 以内）就是为这种差异准备的。
- **前两次启动没有开始训练**：第一次是 Hydra 找不到配置目录，第二次是打包时误删了 EquiCSP 的 `conf/data/`。两次都在训练开始前就退出了，修好后第三次正常跑完。两处修复都已写进 `src/csp/equicsp_train.py` 和 `src/csp/make_pod_bundle.sh`。
- **此前由 cloud session 发起的那次 smoke test**：它没有把任何结果推到 GitHub，所以不知道它有没有创建过 pod、花了多少钱。本次测试开始前，账户里已经没有任何 pod。

## 文件

- `config.json`：版本、Hydra 参数、数据和打包文件的哈希、硬件、价格，以及 pod 的创建和终止时间
- `logs/steps.jsonl`：每个优化步的时间戳（由 `src/csp/equicsp_train.py` 里的计时 callback 写出）
- `logs/train_log.txt`、`logs/hydra_config/`、`logs/gpu_util.csv`、`logs/nvidia_smi.txt`、`logs/pip_freeze.txt`、`logs/setup.log`

---

# CSP random-removal control: 1,000-step smoke test

Date: 2026-11-22 (UTC). This run measures cost only. It is not an experimental result: 1,000 steps is far from a trained model.

## What was run

- PEROV arm, seed 42, using the pre-registered EquiCSP recipe in `src/csp/random_removal_control.py`: microbatch 64 with gradient accumulation 4 (effective batch 256), FP32, upstream default Adam and LR scheduler, `deterministic=True`, validation every 5 epochs. The only difference from a full run is `max_steps=1000` instead of 106,000.
- Data: the PEROV arm prepared on the Mac (train 24,317, val 8,150, test 9,046). File hashes are in `config.json`.
- Hardware: one NVIDIA A40 (48 GB) on RunPod Secure Cloud, at $0.59/hour as returned by the API. The RTX A5000 ($0.27/hour) and RTX 3090 tried first had no capacity at the time.
- Software: Python 3.8.20, torch 1.9.0+cu111, torch-scatter 2.0.9, torch-sparse 0.6.12, pytorch_lightning 1.3.8. The full list is in `logs/pip_freeze.txt`.
- Procedure: bundle on the Mac → upload → build the environment on the pod (44 s) → train → copy the logs back → terminate the pod, then confirm through the API that no pods or queued pods are left.

## Measurements

| Measure | Value |
|---|---|
| Wall time for 1,000 steps (including 2 validation passes) | 293.0 s, i.e. 0.293 s per step |
| Steady-state time per step (excluding the first 50 steps and validation) | mean 0.285 s, median 0.283 s, p90 0.295 s |
| One validation pass | about 3.85 s |
| GPU utilisation (sampled every 15 s) | 48–67%, typically about 62% |
| GPU memory | torch peak allocated 2.2 GiB; nvidia-smi shows up to 9.6 GB |
| Did training end normally? | Yes (exit 0, followed by the test-set evaluation) |

## Projected cost of the full runs

Assumptions: same GPU type and price; 0.293 s per step, which already includes validation (a full run also validates about every 475 steps); about 10 extra minutes per run for start-up, environment setup, upload and wrap-up.

| | Duration | Cost (A40 Secure, $0.59/hour) |
|---|---|---|
| One full run (106,000 steps) | about 8.8 h | about $5.2 |
| 7 core runs | about 62 GPU-hours | about $36 |
| 9 runs (including the 2 optional) | about 79 GPU-hours | about $47 |

Runs can go in parallel on separate pods, which brings the total elapsed time to about 9 hours. The ABC2D6 arm has a slightly larger training set (25,585), but the compute per step depends only on batch size, so the same time per step applies.

Cost of this test: the pod ran 12 min 27 s, from creation (03:52:12) to termination (04:04:39), which is about $0.12 at $0.59/hour. This figure is price × time. The API key has no billing read permission, so it was not checked against RunPod's billing.

## Caveats

- **One measurement** on one machine. Speed may differ on other hosts or at other times.
- **GPU utilisation of about 62%** means part of each step is spent on the CPU (the upstream config loads data with `num_workers=0`). A cheaper GPU such as the A5000 may therefore not be much slower, and running several jobs on one A40 might lower the total cost. Neither has been **tested**; both are only possible ways to save money.
- **The paper used a V100 16GB; we used an A40.** The recipe is the same, but numerical results will not match exactly across GPU types. The pre-registered G0 check (our ABC2D6 and PEROV results must land within ±1 of the paper's) exists for this kind of difference.
- **The first two launches never started training.** The first failed because Hydra could not find the config directory; the second because the bundle step had dropped EquiCSP's `conf/data/`. Both exited before training began, and the third launch ran to completion. Both fixes are in `src/csp/equicsp_train.py` and `src/csp/make_pod_bundle.sh`.
- **The earlier smoke test started from a cloud session** pushed nothing to GitHub. Whether it created a pod, or spent anything, is unknown. There were no pods on the account before this test began.

## Files

- `config.json`: versions, Hydra overrides, data and bundle hashes, hardware, price, and pod creation and termination times
- `logs/steps.jsonl`: a timestamp per optimiser step, written by the timer callback in `src/csp/equicsp_train.py`
- `logs/train_log.txt`, `logs/hydra_config/`, `logs/gpu_util.csv`, `logs/nvidia_smi.txt`, `logs/pip_freeze.txt`, `logs/setup.log`
