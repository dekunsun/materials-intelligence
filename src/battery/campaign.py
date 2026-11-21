"""Five ways to choose the next "experiment" from a pool of candidate electrolytes.

The pool is an offline lab: running an experiment on a composition means
reading its measured conductivity from OBELiX. Every policy sees the same
composition features. The question is how many experiments each policy needs
before it finds materials above a conductivity threshold.

Policies
--------
random          pick uniformly at random. The baseline every lab already has.
bo_gp           Bayesian optimization with a Gaussian process, no prior data:
                5 random starts, then expected improvement. Learns only from
                this campaign's own experiments.
screen_rf       a computational screen: a random forest trained once on the
                prior (training-split) measurements ranks the pool, and the lab
                works down the list. Never updates.
bo_rf_prior     prior data + learning in the loop: a random forest trained on
                prior data plus this campaign's experiments, refit after every
                experiment, choosing by an upper confidence bound.
rl_reinforce    a reinforcement-learning policy (REINFORCE, linear softmax)
                trained on many simulated campaigns drawn from the training
                split, then run on the held-out pool. Its state includes what
                the campaign has found so far.

Policies that use prior data (screen_rf, bo_rf_prior, rl_reinforce) only ever
see the training split; campaigns run on the held-out pool.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

warnings.filterwarnings("ignore", category=ConvergenceWarning)


@dataclass
class Context:
    X: np.ndarray          # standardized pool features
    y: np.ndarray          # measured log10 conductivity (hidden until queried)
    threshold: float       # log10 S/cm
    budget: int
    X_prior: np.ndarray | None = None
    y_prior: np.ndarray | None = None
    fam: np.ndarray | None = None        # chemistry family per pool composition
    fam_prior: np.ndarray | None = None  # chemistry family per prior composition


# ---------------------------------------------------------------- baselines

def run_random(ctx: Context, rng: np.random.Generator) -> list[int]:
    return list(rng.permutation(len(ctx.y))[: ctx.budget])


def run_screen_rf(ctx: Context, rng: np.random.Generator) -> list[int]:
    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                               random_state=int(rng.integers(1 << 31)), n_jobs=-1)
    rf.fit(ctx.X_prior, ctx.y_prior)
    order = np.argsort(-rf.predict(ctx.X), kind="stable")
    return list(order[: ctx.budget])


def run_family_rule(ctx: Context, rng: np.random.Generator) -> list[int]:
    """A chemist's rule of thumb, no machine learning: test the chemistry family
    with the highest hit rate in the prior data first, random order within a family.
    A family absent from the prior data gets the overall prior hit rate."""
    hit_prior = ctx.y_prior >= ctx.threshold
    overall = hit_prior.mean()
    rate = {f: (hit_prior[ctx.fam_prior == f].mean() if (ctx.fam_prior == f).any() else overall)
            for f in set(ctx.fam)}
    jitter = rng.random(len(ctx.y))
    order = sorted(range(len(ctx.y)), key=lambda i: (-rate[ctx.fam[i]], jitter[i]))
    return order[: ctx.budget]


# ------------------------------------------------- Bayesian optimization (GP)

def run_bo_gp(ctx: Context, rng: np.random.Generator, n_init: int = 5) -> list[int]:
    n = len(ctx.y)
    chosen = list(rng.choice(n, size=n_init, replace=False))
    kernel = ConstantKernel(1.0) * Matern(length_scale=np.sqrt(ctx.X.shape[1]), nu=2.5) + WhiteKernel(0.1)
    while len(chosen) < ctx.budget:
        gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=0,
                                      random_state=int(rng.integers(1 << 31)))
        gp.fit(ctx.X[chosen], ctx.y[chosen])
        rest = np.setdiff1d(np.arange(n), chosen)
        mu, sd = gp.predict(ctx.X[rest], return_std=True)
        best = ctx.y[chosen].max()
        z = (mu - best) / np.maximum(sd, 1e-9)
        ei = (mu - best) * norm.cdf(z) + sd * norm.pdf(z)
        chosen.append(int(rest[np.argmax(ei)]))
    return chosen


# ------------------------------------- prior data + learning in the loop (RF)

def run_bo_rf_prior(ctx: Context, rng: np.random.Generator, beta: float = 1.0) -> list[int]:
    n = len(ctx.y)
    chosen: list[int] = []
    seed = int(rng.integers(1 << 31))
    while len(chosen) < ctx.budget:
        Xt = np.vstack([ctx.X_prior, ctx.X[chosen]]) if chosen else ctx.X_prior
        yt = np.concatenate([ctx.y_prior, ctx.y[chosen]]) if chosen else ctx.y_prior
        rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=seed, n_jobs=-1)
        rf.fit(Xt, yt)
        rest = np.setdiff1d(np.arange(n), chosen)
        per_tree = np.stack([t.predict(ctx.X[rest]) for t in rf.estimators_])
        ucb = per_tree.mean(0) + beta * per_tree.std(0)
        chosen.append(int(rest[np.argmax(ucb)]))
    return chosen


# --------------------------------------------------- reinforcement learning

def _state_features(X: np.ndarray, rest: np.ndarray, chosen: list[int], hits: list[bool],
                    y_obs: np.ndarray, step: int, budget: int, ls: float) -> np.ndarray:
    """phi(s, a) for every remaining candidate a.

    Candidate features plus what the campaign has learned so far: how similar
    the candidate is to the hits and misses already found, the conductivity of
    the most similar tested material, and how much budget is used.
    """
    Xr = X[rest]
    if chosen:
        d2 = ((Xr[:, None, :] - X[chosen][None, :, :]) ** 2).sum(-1)
        sim = np.exp(-d2 / (2 * ls * ls))
        h = np.array(hits)
        sim_hit = sim[:, h].max(1) if h.any() else np.zeros(len(rest))
        sim_miss = sim[:, ~h].max(1) if (~h).any() else np.zeros(len(rest))
        nn_y = y_obs[np.argmax(sim, 1)]
    else:
        sim_hit = sim_miss = np.zeros(len(rest))
        nn_y = np.zeros(len(rest))
    t = np.full(len(rest), step / budget)
    return np.hstack([Xr, sim_hit[:, None], sim_miss[:, None], nn_y[:, None], t[:, None], np.ones((len(rest), 1))])


class ReinforcePolicy:
    def __init__(self, n_features: int, seed: int):
        self.theta = np.zeros(n_features + 5)
        self.rng = np.random.default_rng(seed)

    def _probs(self, phi: np.ndarray) -> np.ndarray:
        logits = phi @ self.theta
        logits -= logits.max()
        p = np.exp(logits)
        return p / p.sum()

    def rollout(self, X, y, threshold, budget, rng, learn=False):
        n = len(y)
        chosen, hits, grads, rewards = [], [], [], []
        y_mean = 0.0
        ls = np.sqrt(X.shape[1])
        for step in range(min(budget, n)):
            rest = np.setdiff1d(np.arange(n), chosen)
            y_obs = (y[chosen] - y_mean) if chosen else np.zeros(0)
            phi = _state_features(X, rest, chosen, hits, y_obs, step, budget, ls)
            p = self._probs(phi)
            k = int(rng.choice(len(rest), p=p))
            a = int(rest[k])
            if learn:
                grads.append(phi[k] - p @ phi)   # gradient of log pi(a|s) for a linear softmax
            chosen.append(a)
            hit = bool(y[a] >= threshold)
            hits.append(hit)
            rewards.append(1.0 if hit else 0.0)
        return chosen, grads, rewards

    def train(self, X, y, threshold, budget, episodes=1500, pool_size=110,
              lr=0.02, gamma=0.97) -> list[float]:
        """REINFORCE with a per-step running baseline and Adam, on random sub-pools of the training split."""
        m = np.zeros_like(self.theta); v = np.zeros_like(self.theta)
        baseline = np.zeros(budget); curve = []
        for ep in range(episodes):
            idx = self.rng.choice(len(y), size=min(pool_size, len(y)), replace=False)
            _, grads, rewards = self.rollout(X[idx], y[idx], threshold, budget, self.rng, learn=True)
            G = np.zeros(len(rewards)); acc = 0.0
            for t in reversed(range(len(rewards))):
                acc = rewards[t] + gamma * acc; G[t] = acc
            baseline[: len(G)] = 0.95 * baseline[: len(G)] + 0.05 * G
            g = sum((G[t] - baseline[t]) * grads[t] for t in range(len(G))) / len(G)
            m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g
            mh = m / (1 - 0.9 ** (ep + 1)); vh = v / (1 - 0.999 ** (ep + 1))
            self.theta += lr * mh / (np.sqrt(vh) + 1e-8)   # gradient ascent on expected return
            curve.append(sum(rewards))
        return curve


def run_rl(ctx: Context, rng: np.random.Generator, policy: ReinforcePolicy) -> list[int]:
    chosen, _, _ = policy.rollout(ctx.X, ctx.y, ctx.threshold, ctx.budget, rng)
    return chosen


# ------------------------------------------------------------------ metrics

def score(seq: list[int], y: np.ndarray, threshold: float, budget: int,
          checkpoints=(10, 20, 40)) -> dict[str, float]:
    hit = y[seq] >= threshold
    first = int(np.argmax(hit)) + 1 if hit.any() else budget + 1   # censored at budget+1
    cum = np.cumsum(hit)
    to5 = int(np.argmax(cum >= 5)) + 1 if cum[-1] >= 5 else budget + 1   # censored at budget+1
    out = {"first_hit": float(first), "to_5_hits": float(to5)}
    for c in checkpoints:
        out[f"hits@{c}"] = float(hit[:c].sum())
    return out
