# 晶体筛选小试点：从初始结构出发

> 状态（2026-11-27）：预登记。经过一轮独立审查并按审查修改（第 10 节）；第 11 节的决定已定。本文件提交 git 即为预登记，之后才做正式运行和计分。背景：备忘录 v4 把“更大规模的晶体筛选”改为候选投入，继续条件是“从初始结构出发的小试点里，模型在化学和结构同时陌生的候选上仍有区分”，停止条件是“区分接近随机，或和模板式基线一样失败”（看板 D10）。

## 1. 要回答的问题

第二阶段里，MatRIS-10M-MP 从 **DFT 弛豫好的结构**出发，在化学和结构都陌生的候选上（双重外推格）区分稳定和不稳定结构的 Somers' D 是 0.76。真实筛选拿到的是**未弛豫的初始结构**。这个试点问：

1. 换成初始结构，这个区分能力还剩多少？
2. 它是否仍然比只看组成和原型的模板式方法好？

前两个阶段各缺一半：第一阶段（WBM）从初始结构出发，但“远”是温和的远；第二阶段（Alexandria）真正远，但从 DFT 结构出发。

## 2. 设计一句话

用第二阶段**已经抽好的 600 个双重外推格结构**，为每个结构用原型重建一个初始结构，让 MatRIS-10M-MP 从初始结构重新弛豫；和第二阶段已有的、从 DFT 结构出发的结果逐个配对比较。再用 Wrenformer 作模板式基线。

配对的好处：同一批结构、同一个真值，只换起点，起点的影响直接量出来；从 DFT 结构出发的那一半已经跑完，不用再算。

## 3. 初始结构从哪里来

- **Alexandria 自带的几何优化路径不能用。** 我只在内存里读了 3 个路径文件的开头（168 个条目，没有存盘）：第 0 步离最终结构已经很近，能量下降的中位数 2 meV/atom，75% 小于 14 meV/atom。这些“初始结构”多半已经被预弛豫过。
- **用原型库重建（类似 WBM 的做法）。** 每个 Alexandria 条目都有 `prototype_id`（它是生成时用的模板，不是弛豫后结构的标签：0 号分片里 21% 的条目两者空间群不同）。原型库 `prototypes.tar.bz2`（Alexandria 网站，60,559,936 字节，SHA-256 `cca31a77…4d7c`，最后修改 2024-09-03；压缩包里没有单独的许可文件，按网站对 Alexandria 数据的 CC BY 4.0 许可使用，不提交到 git）。做法（`src/csp/init_pilot_build.py`）：模板里的位置用占位元素 Xxa、Xxb……标记；按约化计数把条目的元素放上去；用 pymatgen 的 `DLSVolumePredictor`（按数据挖掘的键长估计体积，缩放限制在模板体积的 0.5–1.5 倍）缩放晶胞，出错就保留模板体积并记录（实际 0 次）。WBM 是把元素替换进真实的 MP 结构，这里是填进通用模板，所以只能叫“类似 WBM”。
- **覆盖率：** 600 个条目里 557 个有模板（285 种原型）。缺的 43 个全部来自 2024–2025 年的 orbital（24 个）和 m3gnet（19 个）来源，模板编号比 2024 年 9 月的原型库更新；网站上没有更新版本的原型库。其中 20 个稳定、23 个不稳定。怎么计分见第 6 节。
- **不用 DFT 结果挑样本或挑输入。** 重建后不检查它和 DFT 结构是否匹配；模型弛豫到错误结构，就是真实筛选里会犯的错误，照常计分。
- **元素计数相同时怎么填。** 双重外推格里约一半的化学式有相同的计数（例如 Cs2Hf2Cd2F14 填 ABCD7），元素填哪个位置有多种可能。做法：列出所有填法，用 pymatgen 的 `StructureMatcher` 合并给出相同结构的填法（最多保留 6 种，超过的按种子 11 取 6 种），每种都用 MatRIS 弛豫，取 MatRIS 每原子能量最低的那个作为它的预测。这是真实筛选能做的事，不用 DFT 答案。Wrenformer 同样取它预测形成能最低的填法。实际：557 个条目共 905 个填法；350 个条目只有 1 种，150 个有 2 种，57 个有 3–6 种。
- **没有模板的 43 个条目：** 主分析只用有模板的 557 个条目，三个预测在同一批条目上比较；全部 600 个、没有模板的排在最后（原定规则）作为敏感性分析报告，不影响判定（2026-11-27 决定，在任何计分之前；理由见第 11 节）。有模板的条目，如果所有填法都弛豫失败，记为缺预测、排在最后，不拿掉。

## 4. 模型和基线

- **主模型：MatRIS-10M-MP**，设置和第二阶段相同（FIRE 加 FrechetCellFilter，0.05 eV/Å，最多 500 步，CPU）。从初始结构出发，500 步内没收敛不算失败，保留最后的能量，并报告比例。
- **模板式基线：Wrenformer。** Matbench Discovery 用的是 10 个模型的集成；只有一个成员的检查点公开（模型卡上的 `checkpoint_url`，wandb 运行 2kozbp4q，集成里的第 2 个成员，用 MP 2022-08-13 的形成能训练；62,089,441 字节，SHA-256 `20cecd15…5f36`，MIT 许可）。所以这里是**单个检查点，比集成弱**。代码是模型卡指定的 aviary v0.1.0，从源码目录导入，装在单独的环境里（`src/csp/init_pilot_wrenformer.py`）。输入是初始结构的 Wyckoff 标签（aviary v0.1.0 的 `get_aflow_label_from_spglib`，和 Matbench Discovery 给 WBM 初始结构打标签的方法相同），不做弛豫。
- **Wrenformer 环境的检查（已做）：** 在 5,000 个随机 WBM 结构上，单个检查点和公开的集成预测相关 0.998，差的中位绝对值 19 meV/atom；对 DFT 的平均绝对误差 0.113 eV/atom（集成 0.105，和排行榜一致）。
- **形成能对齐：** Wrenformer 预测的是 MP2020 修正下、以 MP 元素参考为零点的形成能。Alexandria 的未修正能量加上 pymatgen 的 MP2020 修正（按普通 GGA 计算；样本里没有 GGA+U 体系），减去 MP 2023 里每种元素能量最低的 GGA 条目（`src/csp/init_pilot_eform.py`）。预测凸包距离 = DFT 凸包距离 + (Wrenformer 形成能 − 换算后的 DFT 形成能)。**检查（已做，通过）：** 在 1,819 个不在试点里、化学式、空间群和原子数与唯一一个 MP 2023 GGA 条目相同的 Alexandria 条目上，形成能差的中位绝对值 2.6 meV/atom（门槛 10 meV/atom）；79% 小于 10 meV/atom。

## 5. 指标

- **Somers' D**（和第二阶段相同）：任取一个稳定、一个不稳定的结构，模型把稳定的排在前面的概率减去反过来的概率；随机为 0，全对为 1。
- **p**（起点的代价）= D(MatRIS，初始结构) / D(MatRIS，DFT 结构)，同一批 557 个条目配对。
- **d**（相对模板的优势）= D(MatRIS，初始结构) − D(Wrenformer)。
- **区间：** 按框架整群 bootstrap，1,000 次，种子 11；配对的两个 D 在每次重抽中用同一批结构计算。

## 6. 判定规则（按顺序检查，双重外推格）

| 顺序 | 结果 | 条件 | 对 D10 |
|---|---|---|---|
| 1 | 失败 | D(初始) 的 95% 区间上限 < 0.2（接近随机）；或 d 的上限 < 0（不比模板好） | 退回暂缓 |
| 2 | 成立 | p 的下限 ≥ 0.8，D(初始) 的下限 > 0.2，且 d 的下限 > 0 | 改为批准（限定范围，只针对 MatRIS 这类模型） |
| 3 | 部分成立 | 其他情况 | 维持候选投入 |

- 这些条件直接对应备忘录 v4 的继续和停止条件：“接近随机”用 D > 0.2 的门槛，“和模板一样失败”用 d > 0。第二阶段用过的 0.10 门槛是在 R 精度上定的，不搬到 D 上。
- 样本不足的检查不需要：主分析是第二阶段已有 600 个条目中有模板的 557 个（280 个稳定，稳定结构分布在 75 个框架；全部 600 个是 300 个稳定、88 个框架）。
- **来源分层（沿用第二阶段）：** 去掉 m3gnet 和 orbital 两个来源再判一次（73 个稳定，27 个框架；没有模板的 43 个都来自这两个来源，所以这一分析不受上面选择的影响）。两者一个成立、一个失败，记为部分成立；否则以主分析为准。
- **敏感性，不影响判定：** 全部 600 个条目，没有模板的 43 个在两个初始结构预测里都排在最后；同样报告 D、p、d 和按规则得到的结果。
- **描述性，不影响判定：** 不稳定结构扩到凸包以上 0.1–0.3 eV/atom 时的 d（需要从第二阶段的池子里补抽条目，补抽部分的计算时间另报）；模型弛豫后落到和 DFT 不同结构的比例；按“输入的框架键”而不是 DFT 结构的框架键重新分格的结果；能量误差；未收敛比例；有并列填法的条目单独比较。

## 7. 计算和花费

- 全部在 Mac CPU 上跑，不花钱，花费上限 0 元。
- 第二阶段里 MatRIS 实际每步约 1 秒（中位数 7 步，每个结构中位 5.9 秒）。从原型出发估计要 100–300 步，600 个结构约 17–50 小时；有并列填法的条目要乘以填法数。
- **测时关卡：** 先用 20 个双重外推格结构（按真实比例含并列填法）测时间，报告预计总时长。超过 48 小时就停下来问你，不自动改用付费 GPU，也不自行缩小样本。
- **测时结果（已做）：** 按种子 11 的固定顺序取前 20 个条目（18 个有模板，27 次弛豫），全部完成，0 次失败，1 次到 500 步没收敛。从初始结构出发，每步的时间随原子数大约按 1.6 次方增长，同样原子数下差别也大（一个 56 原子、含大量氢的结构每步约 15 秒）。
- **并行：** MatRIS 单进程只用到 12 个核里的约 1.5 个。在一个 32 原子结构上比较了三种分法：3 个进程×4 线程每秒合计 0.88 步，4×3 是 0.77，6×2 是 0.66，所以用 3×4。条目按预计工作量（每个填法原子数的 1.6 次方之和，不用 DFT 结果）在固定顺序里依次分给当前最空的进程（`init_pilot_relax.py` 的 `balance()`）。这只改变跑的顺序，每个结构的弛豫方式不变。
- **预计：** 905 次弛豫约 88 个进程小时，3 个进程墙钟约 30 小时；按条目 bootstrap 的 95% 区间 14–54 小时，超过 48 小时的概率约 7%。Wrenformer 只要几分钟。
- **运行中的停止规则：** 正式运行到 48 小时还没完成，就停下来问你，不对已完成的部分计分。

## 8. 为什么不再抽新样本、不跑插值格

- 新样本的唯一好处是“没看过”，但真值是固定的，这里的输出全是新的模型结果；配对第二阶段已有的结果能省一半计算，还和第二阶段直接对得上。
- 插值格从初始结构出发的表现，第一阶段（WBM 标准任务）已经回答；双重外推格和插值格的比较，第二阶段已经回答。这里要的新信息是起点的代价，所以只跑双重外推格。

## 9. 已知局限

- 重建的初始结构和 Alexandria 实际用的不一定相同；用的是通用模板，比 WBM 的“真实结构加元素替换”更粗。
- 双重外推格里约一半条目的“陌生框架”是 DFT 弛豫后才出现的（模板本身的框架 MP 里有）；按输入重新分格的结果作为描述报告。
- 一个主模型、一个基线、557 个条目；Wrenformer 是单个公开检查点，不是集成；真值仍是 DFT。
- 主分析不含 2024 年 9 月之后的模板（43 个 orbital 和 m3gnet 条目），所以结论不覆盖这些最新的来源。
- 双重外推格的稳定结构大多来自机器学习预筛的来源；框架很集中：全量双重外推格里，最大的一个框架占稳定结构约五分之一。
- 排除了 GGA+U 体系（含 Co、Cr、Fe、Mn、Mo、Ni、V、W 的氧化物和氟化物）。

## 10. 审查后改了什么

独立审查（2026-11-27）指出的问题和处理：

| 问题 | 处理 |
|---|---|
| 用 DFT 结构匹配来筛样本，会在双重外推格里拿掉更多、也更难的条目，结果偏乐观 | 去掉这个筛选；重建失败记为缺预测，不拿掉 |
| 原设计的“成立”看双重外推格和插值格之比，第二阶段已经回答过，而且几乎达不到 | 改看配对的 p（起点的代价）；不跑插值格 |
| 去掉了第二阶段的来源分层 | 恢复 |
| 计数相同时用 DFT 答案选填法会泄漏答案 | 列出所有填法，按模型自己的最低能量选 |
| Wrenformer 是 10 个模型的集成，单个检查点更弱；形成能修正不一致；0.10 的门槛来自 R 精度 | 尽量用集成，否则写明；先校验形成能换算；改用 d > 0 |
| 时间估计用的是测时样本，第二阶段实际约 1 秒/步 | 按步数重估，并设测时关卡 |
| “WBM 的做法”说法不准 | 改为“类似 WBM” |

## 11. 已定的决定（2026-11-27）

1. **原型库：** 已下载；许可和覆盖率见第 3 节。
2. **Wrenformer：** 只有一个成员的检查点公开，就用它（第 4 节）；aviary v0.1.0 装上了，所以 d 仍是判定的一部分。
3. **计数相同时列出所有填法**（第 3 节）。
4. **第 6 节的判定规则和对 D10 的映射**，照原样采用。
5. **本机计算上限 48 小时**（第 7 节）。
6. **没有模板的 43 个条目：** 主分析用有模板的 557 个条目，全部 600 个（没有模板的排最后）作为敏感性分析。理由：缺模板只取决于原型库的日期（2024 年 9 月），和任何模型输出无关，在计分之前定下。如果按原定规则排最后，只会压低两个初始结构预测，不影响从 DFT 结构出发的预测，p 粗估会因此低约 0.1；这是原型库的日期造成的，不是从初始结构出发的代价。这一条改变了第 10 节表里“重建失败记为缺预测，不拿掉”的做法：那一条针对的是按和 DFT 结构是否匹配来筛样本，这里的排除不用任何 DFT 结果。

## 12. 预登记之前做过、看过的事

- 原型库、Wrenformer 检查点、aviary v0.1.0 源码已下载；初始结构已全部重建（`initial_structures.json.gz`）。
- **看过试点条目的 DFT 体积：** 重建后，我把 557 个条目第一个填法的每原子体积和 DFT 结构比了一次（初始/DFT 的中位数 1.05，5% 和 95% 分位 0.42 和 2.04），没有因此改变体积方法。之后又在 2,000 个验证条目（不在试点里）上比较了模板体积和 DLS；模板体积在那里更接近 DFT，但这些条目的模板很可能就是用这些 MP 结构做的，不代表陌生条目，所以仍用 DLS。
- **Wrenformer 预测跑过一次：** 为了测试流程，在全部 905 个初始结构上跑过一次 Wrenformer；没有计算任何分数，文件已删除，预登记之后重跑（结果是确定的）。
- **测时：** 20 个条目（按种子 11 的固定顺序取前 20 个，其中 2 个没有模板）从初始结构弛豫过，结果在 `results/csp_init_pilot_timing/`，只看了步数、秒数和是否收敛，用来估计时间，不计分；正式运行从头再跑。另外在一个结构上跑了 30 步，比较进程和线程的分法（只看速度）。
- 没有计算过任何 Somers' D、p 或 d。

## 13. 文件和脚本

按运行顺序（都在仓库根目录运行；数据在已 gitignore 的 `data/raw/alexandria/pilot/`）：

| 脚本 | 环境 | 做什么 |
|---|---|---|
| `src/csp/init_pilot_collect.py` | `.venv` | 取出 600 个试点条目和 2,000 个验证条目，记录模板覆盖率 |
| `src/csp/init_pilot_build.py` | `.venv` | 用原型库重建初始结构，列出并列填法，DLS 缩放体积 |
| `src/csp/init_pilot_eform.py` | `.venv` | 形成能换算和它的检查 |
| `src/csp/init_pilot_wrenformer.py` | `data/raw/aviary_venv` | Wrenformer 环境检查；对初始结构预测形成能 |
| `src/csp/init_pilot_relax.py` | `data/raw/mlip_venv` | MatRIS 从初始结构弛豫，可分多个进程 |
| `src/csp/init_pilot_decide.py` | `.venv` | 计分并按第 6 节判定，写 `decision.json` |
| `src/csp/init_pilot_describe.py` | `.venv` | 描述性数字，写 `descriptive.json`，不影响判定 |
| `tests/check_init_pilot.py` | `.venv` | 只用编造的输入检查模板路径、填法、判定规则和 557 的选取 |

---

# Crystal-screening pilot: starting from initial structures

> Status (2026-11-27): pre-registered. Revised after one independent review (Section 10); the decisions in Section 11 are made. Committing this file to git is the pre-registration; the main run and scoring come after. Background: Memo v4 made larger-scale crystal screening a candidate investment. Its continue condition is "in a small pilot starting from initial structures, models still separate stable candidates where chemistry and framework are both unfamiliar"; its stop condition is "separation is close to random, or fails as badly as a template-like baseline" (board D10).

## 1. The question

In Stage 2, MatRIS-10M-MP started from **DFT-relaxed structures** and separated stable from unstable candidates with unfamiliar chemistry and framework (the double-extrapolation cell) with Somers' D 0.76. A real screen gets **unrelaxed initial structures**. This pilot asks:

1. How much of that separation is left when the input is the initial structure?
2. Is it still better than a template-like method that sees only composition and prototype?

Each earlier stage covered half: Stage 1 (WBM) started from initial structures, but "far" was mild; Stage 2 (Alexandria) was genuinely far, but started from DFT structures.

## 2. The design in one sentence

Take the **600 double-extrapolation structures already sampled in Stage 2**, rebuild an initial structure for each from its prototype, and let MatRIS-10M-MP relax from it; compare entry by entry with Stage 2's existing results from the DFT structure. Wrenformer is the template-like baseline.

Why paired: same structures, same truth, only the starting point changes, so its effect is measured directly; the half that starts from DFT structures has already been run.

## 3. Where the initial structures come from

- **Alexandria's own geometry-optimisation paths cannot be used.** I read only the start of 3 path files in memory (168 entries, nothing saved): step 0 is already close to the final structure, with a median energy drop of 2 meV/atom and 75% below 14 meV/atom. These "initial structures" were most likely pre-relaxed.
- **Rebuild from the prototype library (WBM-like).** Every Alexandria entry has a `prototype_id`. It is the generation template, not the label of the relaxed structure: for 21% of shard 0 the two space groups differ. The prototype library `prototypes.tar.bz2` comes from the Alexandria site: 60,559,936 bytes, SHA-256 `cca31a77…4d7c`, last modified 2024-09-03. The archive has no licence file of its own; it is used under the site's CC BY 4.0 licence for Alexandria data and is not committed to git. Method (`src/csp/init_pilot_build.py`): the template's sites carry placeholder species Xxa, Xxb, …; the entry's elements go on them by reduced count; the cell is scaled with pymatgen's `DLSVolumePredictor` (volume from data-mined bond lengths, scaling kept within 0.5–1.5 of the template volume). If it raises, the template volume is kept and recorded; this happened 0 times. WBM substituted elements into real MP structures; this fills generic templates, so it is only "WBM-like".
- **Coverage:** 557 of the 600 entries have a template (285 prototypes). The 43 missing all come from the 2024–2025 orbital (24) and m3gnet (19) sources, whose template numbers are newer than the September 2024 library; the site has no newer library. Of the 43, 20 are stable and 23 unstable. Section 6 says how they are scored.
- **No DFT result is used to choose the sample or the input.** The rebuilt structure is not checked against the DFT structure; if the model relaxes to a wrong structure, that is an error a real screen would make, and it is scored as such.
- **When element counts tie.** About half the formulas in the double cell have tied counts (e.g. Cs2Hf2Cd2F14 in ABCD7), so elements can go into the sites in several ways. Method: list every assignment, merge those that give the same structure (pymatgen `StructureMatcher`; at most 6 are kept, and above that 6 are drawn with seed 11), relax each with MatRIS, and take the one with the lowest MatRIS energy per atom as its prediction. A real screen can do this; it uses no DFT answer. Wrenformer likewise takes its lowest predicted formation energy. In practice: 905 assignments for 557 entries; 350 entries have 1, 150 have 2, 57 have 3–6.
- **The 43 entries without a template:** the main analysis uses the 557 entries with a template, all three predictors on the same entries. All 600, with the entries without a template ranked last (the rule first agreed), is reported as a sensitivity analysis and never changes the outcome (decided 2026-11-27, before any score; Section 11 gives the reason). An entry with a template whose relaxations all fail is a missing prediction, ranked last, not removed.

## 4. Model and baseline

- **Main model: MatRIS-10M-MP**, with Stage 2's settings (FIRE with FrechetCellFilter, 0.05 eV/Å, at most 500 steps, CPU). From initial structures, not converging within 500 steps is not a failure; the final energy is kept and the share is reported.
- **Template-like baseline: Wrenformer.** Matbench Discovery uses an ensemble of 10 models; only one member's checkpoint is public. It is the model card's `checkpoint_url`, wandb run 2kozbp4q, ensemble member 2, trained on MP 2022-08-13 formation energies: 62,089,441 bytes, SHA-256 `20cecd15…5f36`, MIT licence. So this is **a single checkpoint, weaker than the ensemble**. The code is aviary v0.1.0, the version on the model card, imported from its source folder in a separate environment (`src/csp/init_pilot_wrenformer.py`). The input is the Wyckoff label of the initial structure (aviary v0.1.0's `get_aflow_label_from_spglib`, the method Matbench Discovery used to label WBM's initial structures), with no relaxation.
- **Check of the Wrenformer setup (done):** on 5,000 random WBM structures, the single checkpoint correlates 0.998 with the published ensemble predictions, with a median absolute difference of 19 meV/atom; its mean absolute error against DFT is 0.113 eV/atom (ensemble 0.105, as on the leaderboard).
- **Formation-energy alignment:** Wrenformer predicts formation energy with MP2020 corrections and MP elemental references. Alexandria's uncorrected energy gets pymatgen's MP2020 correction for a plain GGA calculation (the sample has no GGA+U systems), minus, for each element, the lowest-energy MP 2023 GGA entry (`src/csp/init_pilot_eform.py`). Predicted hull distance = DFT hull distance + (Wrenformer formation energy − converted DFT formation energy). **Check (done, passed):** on 1,819 Alexandria entries outside the pilot whose formula, space group and number of sites match exactly one MP 2023 GGA entry, the median absolute formation-energy difference is 2.6 meV/atom (threshold 10 meV/atom); 79% are below 10 meV/atom.

## 5. Metrics

- **Somers' D** (as in Stage 2): the probability that a model ranks a random stable structure above a random unstable one, minus the reverse; random scores 0, perfect 1.
- **p** (cost of the starting point) = D(MatRIS, initial structures) / D(MatRIS, DFT structures), paired on the same 557 entries.
- **d** (advantage over the template) = D(MatRIS, initial structures) − D(Wrenformer).
- **Intervals:** cluster bootstrap by framework, 1,000 resamples, seed 11; both paired D values are computed on the same resample each time.

## 6. Decision rules (checked in order, double cell)

| Order | Outcome | Condition | D10 |
|---|---|---|---|
| 1 | Fails | Upper bound of the 95% interval of D(initial) < 0.2 (close to random); or upper bound of d < 0 (no better than the template) | Back to defer |
| 2 | Holds | Lower bound of p ≥ 0.8, lower bound of D(initial) > 0.2, and lower bound of d > 0 | Approve (limited scope, for MatRIS-type models only) |
| 3 | Partial | Anything else | Stays a candidate investment |

- These conditions map directly onto Memo v4's continue and stop conditions: "close to random" uses the D > 0.2 bar, "fails as badly as the template" uses d > 0. The 0.10 margin of Stage 1 was set on R-precision and is not carried over to D.
- No "too small" check is needed: the main analysis uses the 557 of Stage 2's 600 entries that have a template (280 stable, the stable ones in 75 frameworks; all 600 have 300 stable in 88 frameworks).
- **Source strata (as in Stage 2):** decide again without the m3gnet and orbital sources (73 stable, 27 frameworks; all 43 entries without a template come from these two sources, so this analysis is the same under either choice above). If one holds and the other fails, the outcome is partial; otherwise the main analysis stands.
- **Sensitivity, never decisive:** all 600 entries, the 43 without a template ranked last by both initial-structure predictors; D, p, d and the outcome the rules would give are reported.
- **Descriptive, never decisive:** d with unstable structures extended to 0.1–0.3 eV/atom above the hull (needs extra entries from Stage 2's pool; cost reported separately); the share of model relaxations ending in a structure different from the DFT one; cells re-assigned by the framework key of the input rather than of the DFT structure; energy errors; the share not converged; entries with tied assignments compared separately.

## 7. Compute and spending

- Everything runs on the Mac CPU at no cost; spending cap zero.
- In Stage 2, MatRIS actually took about 1 s per step (median 7 steps, median 5.9 s per structure). From a prototype, an estimated 100–300 steps, so about 17–50 hours for 600 structures; entries with tied assignments multiply by the number of assignments.
- **Timing gate:** time 20 double-cell structures first (with tied assignments in their real proportion) and report the projected total. Above 48 hours, stop and ask; do not switch to a paid GPU or shrink the sample unasked.
- **Timing result (done):** the first 20 entries in the fixed seed-11 order (18 with a template, 27 relaxations) all finished, with 0 failures and 1 relaxation reaching 500 steps without converging. From initial structures, time per step grows roughly as the number of sites to the power 1.6, with wide spread at a given size (one 56-site, hydrogen-rich structure took about 15 s per step).
- **Parallel runs:** a single MatRIS process uses only about 1.5 of the 12 cores. Three splits were compared on one 32-site structure: 3 processes × 4 threads gave 0.88 steps per second in total, 4 × 3 gave 0.77 and 6 × 2 gave 0.66, so 3 × 4 is used. Entries are dealt in the fixed order to whichever process has the least expected work so far (sites^1.6 summed over an entry's assignments; no DFT result; `balance()` in `init_pilot_relax.py`). This changes only the order of work; every structure is relaxed the same way.
- **Projection:** the 905 relaxations need about 88 process-hours, about 30 hours of wall time with 3 processes; the 95% interval from a bootstrap over entries is 14–54 hours, with about a 7% chance of exceeding 48. Wrenformer takes minutes.
- **Stop rule during the run:** if the main run has not finished after 48 hours, stop and ask; the finished part is not scored.

## 8. Why no new sample and no interpolation run

- A new sample's only advantage is being unseen, but the truth is fixed and every output here is a new model result; pairing with Stage 2's existing results halves the compute and ties directly to Stage 2.
- How models do in interpolation from initial structures is answered by Stage 1 (WBM's standard task); double versus interpolation is answered by Stage 2. The new information here is the cost of the starting point, so only the double cell is run.

## 9. Known limits

- The rebuilt initial structures are not necessarily the ones Alexandria used; they come from generic templates, coarser than WBM's "real structure plus element substitution".
- For about half the double-cell entries, the "unfamiliar framework" appears only after DFT relaxation (the template's own framework is in MP); results with cells re-assigned by the input are reported as descriptive.
- One main model, one baseline, 557 entries; Wrenformer is the single public checkpoint, not the ensemble; the truth is still DFT.
- The main analysis has no templates newer than September 2024 (the 43 orbital and m3gnet entries), so its conclusion does not cover those newest sources.
- Most stable structures in the double cell come from ML pre-screened sources; frameworks are concentrated: in the full double cell, the largest framework holds about a fifth of the stable structures.
- GGA+U systems are excluded (oxides and fluorides of Co, Cr, Fe, Mn, Mo, Ni, V and W).

## 10. What changed after review

Problems raised by an independent review (2026-11-27) and how they were handled:

| Problem | Handling |
|---|---|
| Filtering the sample by a match to the DFT structure removes more, and harder, entries from the double cell, so the result leans optimistic | The filter is dropped; entries that cannot be rebuilt are missing predictions, not removed |
| The original "holds" used double versus interpolation, which Stage 2 already answered and which was nearly out of reach | It now uses the paired p (cost of the starting point); no interpolation run |
| Stage 2's source strata had been dropped | Restored |
| Choosing tied assignments with the DFT answer would leak it | All assignments are listed and the model's own lowest energy decides |
| Wrenformer is a 10-model ensemble and a single checkpoint is weaker; formation-energy corrections differ; the 0.10 margin came from R-precision | Use the ensemble if possible, otherwise say so; check the formation-energy conversion first; use d > 0 |
| The time estimate came from the timing sample; Stage 2 actually took about 1 s per step | Re-estimated by steps, with a timing gate |
| "WBM's method" was inaccurate | Now "WBM-like" |

## 11. Decisions made (2026-11-27)

1. **Prototype library:** downloaded; licence and coverage in Section 3.
2. **Wrenformer:** only one member's checkpoint is public, and it is used (Section 4); aviary v0.1.0 installed, so d stays part of the decision.
3. **When counts tie, every assignment is listed** (Section 3).
4. **The decision rules of Section 6 and their mapping to D10** are adopted as written.
5. **A 48-hour cap on local compute** (Section 7).
6. **The 43 entries without a template:** the main analysis uses the 557 entries with a template; all 600, with those without a template ranked last, is the sensitivity analysis. Reason: a missing template depends only on the library's date (September 2024), not on any model output, and this was settled before any score. Ranking them last, as first agreed, would lower only the two initial-structure predictors and not the DFT-start one, so p would come out roughly 0.1 lower; that comes from the library's date, not from the cost of starting from initial structures. This changes the handling in Section 10's table ("entries that cannot be rebuilt are missing predictions, not removed"): that row was about filtering the sample by a match to the DFT structure, whereas this exclusion uses no DFT result.

## 12. What was done and seen before pre-registration

- The prototype library, the Wrenformer checkpoint and the aviary v0.1.0 source were downloaded; all initial structures were rebuilt (`initial_structures.json.gz`).
- **The pilot entries' DFT volumes were looked at:** after the rebuild, the volume per atom of each of the 557 entries' first assignment was compared once with the DFT structure. The initial/DFT ratio had a median of 1.05, with 5th and 95th percentiles of 0.42 and 2.04. The volume method was not changed because of this. Template volume and DLS were then compared on the 2,000 validation entries (not in the pilot). The template volume was closer to DFT there, but those entries' templates were probably made from the same MP structures, so they say little about unfamiliar entries, and DLS stays.
- **Wrenformer was run once:** to test the pipeline, Wrenformer predicted all 905 initial structures; no score was computed, the file was deleted, and it is re-run after pre-registration (the result is deterministic).
- **Timing:** 20 entries (the first 20 in the fixed seed-11 order, 2 of them without a template) were relaxed from initial structures. The results are in `results/csp_init_pilot_timing/`; only steps, seconds and convergence were looked at, to estimate time, and nothing was scored; the main run starts again from scratch. Separately, one structure was run for 30 steps to compare process and thread splits (speed only).
- No Somers' D, p or d has been computed.

## 13. Files and scripts

In run order (all run from the repository root; data in the gitignored `data/raw/alexandria/pilot/`):

| Script | Environment | What it does |
|---|---|---|
| `src/csp/init_pilot_collect.py` | `.venv` | Pulls the 600 pilot entries and 2,000 validation entries; records template coverage |
| `src/csp/init_pilot_build.py` | `.venv` | Rebuilds initial structures from the prototype library; lists tied assignments; scales volume with DLS |
| `src/csp/init_pilot_eform.py` | `.venv` | Formation-energy conversion and its check |
| `src/csp/init_pilot_wrenformer.py` | `data/raw/aviary_venv` | Checks the Wrenformer setup; predicts formation energies of the initial structures |
| `src/csp/init_pilot_relax.py` | `data/raw/mlip_venv` | Relaxes the initial structures with MatRIS, optionally in several processes |
| `src/csp/init_pilot_decide.py` | `.venv` | Scores and applies the Section 6 rules; writes `decision.json` |
| `src/csp/init_pilot_describe.py` | `.venv` | Descriptive numbers; writes `descriptive.json`; never changes the decision |
| `tests/check_init_pilot.py` | `.venv` | Checks template paths, assignments, the rules and the 557 selection on made-up inputs only |
