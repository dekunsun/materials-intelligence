# A5000 与 A40 速度对比（1,000 步 smoke test）

日期：2026-11-22（UTC）。只用于比较 GPU 的速度和费用，不是实验结果。

在 RunPod Community Cloud 的 RTX A5000（24 GB，3 个 vCPU，$0.16/小时）上，把 A40 那次的测试（`results/csp_smoke_test_20261122T035212Z`）原样重跑一遍：PEROV 组、seed 42、预注册配方、`max_steps=1000`，命令为 `bash src/csp/pod_train.sh PEROV 42 1000`。

| | A40（Secure，$0.59/小时） | A5000（Community，$0.16/小时） |
|---|---|---|
| 每步（含验证） | 0.293 秒 | 0.289 秒 |
| 稳定阶段每步（平均 / 中位数） | 0.285 / 0.283 秒 | 0.280 / 0.278 秒 |
| 每次验证 | 约 3.85 秒 | 约 4.0 秒 |
| GPU 平均利用率 | 约 62% | 约 57% |
| 1,000 步后的 test_loss | 1.6398 | 1.6377 |

两张卡速度基本一样。这和 GPU 利用率不高的情况一致：瓶颈有一部分在 CPU 上，换更强的 GPU 也快不了多少。两次的 test_loss 接近但不完全相同，这是不同 GPU 上浮点运算顺序不同造成的，属于预期之内。

## 费用估算

假设每次正式训练（106,000 步）约 8.7 小时，已包含每次约 10 分钟的准备和收尾时间。

| GPU / 云 | 每次 | G0（2 次） | 7 次 | 9 次 |
|---|---|---|---|---|
| A5000 Community，$0.16/小时 | 约 $1.4 | 约 $2.8 | 约 $10 | 约 $13 |
| A5000 Secure，$0.27/小时 | 约 $2.3 | 约 $4.7 | 约 $16 | 约 $21 |
| A40 Secure，$0.59/小时 | 约 $5.1 | 约 $10 | 约 $36 | 约 $46 |

本次测试：pod 从 04:11:56 运行到 04:21:13，共约 9 分钟，按 $0.16/小时算约 $0.03。这是价格乘以时长，没有和账单核对。

## 需要注意的地方

- 两种 GPU 各只测了一次。
- **Community Cloud 的机器由第三方提供，可靠性比 Secure Cloud 低。** 一次训练要跑约 9 小时，中途宿主机出问题，进度就会丢失。EquiCSP 会保存 `last.ckpt`，但它在容器盘上，pod 一没就跟着没了。而且上游的恢复逻辑只加载模型权重，不恢复优化器和学习率调度器的状态，所以中断后续跑的结果不再完全等同于预注册配方。
- 当时 A5000 在 Secure 和 Community 上都很难开到，重试了 2 分钟才在 Community 上拿到一台。

---

# A5000 vs A40 speed (1,000-step smoke test)

Date: 2026-11-22 (UTC). A speed and cost comparison only, not an experimental result.

The A40 smoke test (`results/csp_smoke_test_20261122T035212Z`) was repeated unchanged on an RTX A5000 (24 GB, 3 vCPUs, $0.16/hour) on RunPod Community Cloud: PEROV arm, seed 42, pre-registered recipe, `max_steps=1000`. The command was `bash src/csp/pod_train.sh PEROV 42 1000`.

| | A40 (Secure, $0.59/h) | A5000 (Community, $0.16/h) |
|---|---|---|
| Seconds per step, including validation | 0.293 | 0.289 |
| Steady-state seconds per step (mean / median) | 0.285 / 0.283 | 0.280 / 0.278 |
| One validation pass | about 3.85 s | about 4.0 s |
| Mean GPU utilisation | about 62% | about 57% |
| test_loss after 1,000 steps | 1.6398 | 1.6377 |

The two cards run at essentially the same speed. That fits the low GPU utilisation: part of each step is limited by the CPU, so a stronger GPU barely helps. The test losses are close but not identical; floating-point operations run in a different order on different GPUs, so this is expected.

## Projected cost

Assumes each full run (106,000 steps) takes about 8.7 hours, including about 10 minutes of setup and wrap-up.

| GPU / cloud | Per run | G0 (2 runs) | 7 runs | 9 runs |
|---|---|---|---|---|
| A5000 Community, $0.16/h | about $1.4 | about $2.8 | about $10 | about $13 |
| A5000 Secure, $0.27/h | about $2.3 | about $4.7 | about $16 | about $21 |
| A40 Secure, $0.59/h | about $5.1 | about $10 | about $36 | about $46 |

This test: the pod ran from 04:11:56 to 04:21:13, about 9 minutes, which is about $0.03 at $0.16/hour. That is price × time; it was not checked against billing.

## Caveats

- Each GPU type was measured once.
- **Community Cloud machines are run by third-party hosts and are less reliable than Secure Cloud.** A full run takes about 9 hours, and if the host fails partway, the progress is lost. EquiCSP saves `last.ckpt`, but it lives on the container disk, which goes with the pod. Also, the upstream resume logic reloads only the model weights, not the optimizer or learning-rate scheduler state, so a resumed run is no longer exactly the pre-registered recipe.
- A5000s were scarce on both Secure and Community Cloud at the time; getting one on Community took 2 minutes of retries.
