# -*- coding: utf-8 -*-
"""Прогноз action[t+k]: рекуррентная сеть, unsupervised-модели и Q-обучение.

Модели (тот же протокол, что в predict_future.py: dev/holdout по времени,
leave-one-match-out на dev, равные классы в оценке, конфигурация выбирается по CV):

  gru            GRU по окну из последних L кадров (supervised);
  gru+horizon    то же + реальные пары с соседними горизонтами для редких целей;
  ae-kmeans      автоэнкодер по окнам (без меток) -> k-means -> P(цель | кластер);
  hmm            дискретный HMM по последовательности кадров (без меток цели):
                 фильтрация состояния в t, распространение на k шагов, P(cur в t+k);
  q-greedy       табличное офлайн-Q-обучение (Fitted Q Iteration), k=1:
                 предсказываем действие с максимальным Q(s, a).

Награда для Q-обучения в данных отсутствует и задана вручную (см. reward_for).
Поэтому q-greedy проверяет гипотезу «агенты ведут себя жадно по этой награде»,
а не извлекает истинную награду.
"""

from __future__ import annotations

import argparse
import time as time_module

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neural_network import MLPRegressor

from predict_future import (
    ALL_MATCHES,
    EXCLUDED_ACTIONS,
    HOLDOUT_FRACTION,
    SEED,
    TARGET_LABELS,
    balanced_metrics,
    build_horizon_dataset,
    build_match_frame,
    calc_stats,
    fit_markov,
    load_groundtruth,
    log,
    predict_markov,
    split_point,
)

# torch в этой среде не загружается (Windows блокирует DLL политикой Application Control),
# поэтому GRU реализован на numpy (ручной BPTT + Adam), автоэнкодер — на sklearn MLPRegressor.

# --------------------------------------------------------------------------- #
# Кодирование кадров
# --------------------------------------------------------------------------- #

FEATURE_VALUES = [
    ["side=none", "side=L", "side=R"],
    ["near=0", "near=1", "near=2", "near=3+"],
    ["mid=0", "mid=1-3", "mid=4+"],
    ["pass=no", "pass=yes"],
    ["goal=no", "goal=yes"],
    ["cur=dribbling", "cur=fight", "cur=kickingG", "cur=passing", "cur=searching"],
]
F_SIDE, F_NEAR, F_MID, F_PASS, F_GOAL, F_CUR = range(6)
CARDS = [len(v) for v in FEATURE_VALUES]
FEAT_OFFSETS = np.concatenate([[0], np.cumsum(CARDS)[:-1]])
D_IN = int(sum(CARDS))
ITEM_LOOKUP = {item: (f, v) for f, vals in enumerate(FEATURE_VALUES) for v, item in enumerate(vals)}
# pass=yes <=> cur=passing, поэтому для HMM и Q признак pass не нужен
STATE_FEATURES = [F_SIDE, F_NEAR, F_MID, F_GOAL, F_CUR]
STATE_CARDS = [CARDS[f] for f in STATE_FEATURES]
N_ACTIONS = 5  # 4 цели + searching (индекс 4)

WINDOW = 12
ALPHAS = [0.0, 0.5, 1.0, 1.5]  # logp - alpha * log(prior): alpha=1 даёт argmax lift
AE_CLUSTERS = [8, 16, 32, 64]
HMM_STATES = [4, 8, 16]
Q_MIN_COUNTS = [1, 5, 20]
GRU_EPOCHS = 10
GRU_HIDDEN = 32


def build_global(frames: dict[str, dict]) -> dict:
    """Склеивает кадры всех матчей в глобальные массивы."""
    names = list(frames)
    codes, cstart, local_i, times, match_id, is_dev = [], [], [], [], [], []
    offsets: dict[str, int] = {}
    total = 0
    for m, name in enumerate(names):
        fr = frames[name]
        n = fr["n"]
        offsets[name] = total
        arr = np.zeros((n, len(FEATURE_VALUES)), dtype=np.int64)
        for r, items in enumerate(fr["items"]["B"]):
            for item in items:
                hit = ITEM_LOOKUP.get(item)
                if hit is not None:
                    arr[r, hit[0]] = hit[1]
        t = fr["times"]
        cs = np.arange(n)
        for r in range(1, n):
            if t[r] == t[r - 1] + 1:
                cs[r] = cs[r - 1]
        codes.append(arr)
        cstart.append(cs + total)
        local_i.append(np.arange(n))
        times.append(t)
        match_id.append(np.full(n, m))
        is_dev.append(np.arange(n) < split_point(n, HOLDOUT_FRACTION))
        total += n

    codes_all = np.concatenate(codes)
    onehot = np.zeros((len(codes_all), D_IN), dtype=np.float32)
    for f in range(len(CARDS)):
        onehot[np.arange(len(codes_all)), FEAT_OFFSETS[f] + codes_all[:, f]] = 1.0
    return {
        "names": names,
        "offsets": offsets,
        "codes": codes_all,
        "onehot": onehot,
        "cstart": np.concatenate(cstart),
        "local_i": np.concatenate(local_i),
        "times": np.concatenate(times),
        "match_id": np.concatenate(match_id),
        "is_dev": np.concatenate(is_dev),
        "state": np.ravel_multi_index(codes_all[:, STATE_FEATURES].T, STATE_CARDS),
    }


def gather_windows(G: dict, gidx: np.ndarray, length: int = WINDOW) -> np.ndarray:
    """Окна (n, length, D_IN+1) из последних кадров; кадры до разрыва времени обнуляются."""
    pos = gidx[:, None] + np.arange(-length + 1, 1)[None, :]
    valid = pos >= G["cstart"][gidx][:, None]
    x = G["onehot"][np.clip(pos, 0, None)] * valid[..., None]
    return np.concatenate([x, valid[..., None].astype(np.float32)], axis=2).astype(np.float32)


# --------------------------------------------------------------------------- #
# GRU (numpy: прямой проход, BPTT, Adam)
# --------------------------------------------------------------------------- #

def _sigmoid(a: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-a))


class NumpyGRU:
    """GRU по окну -> линейный слой на последнем состоянии -> softmax по целям."""

    def __init__(self, d_in: int, hidden: int, n_classes: int, seed: int):
        rng = np.random.default_rng(seed)
        s_in, s_h = 1.0 / np.sqrt(d_in), 1.0 / np.sqrt(hidden)
        self.H = hidden
        self.p = {
            "W": rng.uniform(-s_in, s_in, (d_in, 3 * hidden)),      # z | r | h
            "U": rng.uniform(-s_h, s_h, (hidden, 3 * hidden)),
            "b": np.zeros(3 * hidden),
            "Wo": rng.uniform(-s_h, s_h, (hidden, n_classes)),
            "bo": np.zeros(n_classes),
        }

    def forward(self, x: np.ndarray, keep: bool = False):
        H, p = self.H, self.p
        B, T, _ = x.shape
        xw = x @ p["W"] + p["b"]
        h = np.zeros((B, H))
        cache = []
        for t in range(T):
            hz_hr = h @ p["U"][:, : 2 * H]
            z = _sigmoid(xw[:, t, :H] + hz_hr[:, :H])
            r = _sigmoid(xw[:, t, H:2 * H] + hz_hr[:, H:])
            hh = np.tanh(xw[:, t, 2 * H:] + (r * h) @ p["U"][:, 2 * H:])
            h_new = (1 - z) * h + z * hh
            if keep:
                cache.append((h, z, r, hh))
            h = h_new
        logits = h @ p["Wo"] + p["bo"]
        return (logits, h, cache) if keep else logits

    def loss_and_grads(self, x: np.ndarray, y: np.ndarray, l2: float):
        H, p = self.H, self.p
        B, T, D = x.shape
        logits, h_last, cache = self.forward(x, keep=True)
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True)
        loss = -np.log(probs[np.arange(B), y] + 1e-12).mean()
        loss += 0.5 * l2 * sum((p[k] ** 2).sum() for k in ("W", "U", "Wo"))

        dlogits = probs
        dlogits[np.arange(B), y] -= 1.0
        dlogits /= B
        g = {"Wo": h_last.T @ dlogits, "bo": dlogits.sum(0)}
        dh = dlogits @ p["Wo"].T
        dpre = np.zeros((B, T, 3 * H))
        dU = np.zeros_like(p["U"])
        for t in range(T - 1, -1, -1):
            h_prev, z, r, hh = cache[t]
            dz = dh * (hh - h_prev)
            dhh_pre = dh * z * (1 - hh ** 2)
            d_rh = dhh_pre @ p["U"][:, 2 * H:].T
            dr_pre = d_rh * h_prev * r * (1 - r)
            dz_pre = dz * z * (1 - z)
            dpre[:, t, :H], dpre[:, t, H:2 * H], dpre[:, t, 2 * H:] = dz_pre, dr_pre, dhh_pre
            dU[:, :H] += h_prev.T @ dz_pre
            dU[:, H:2 * H] += h_prev.T @ dr_pre
            dU[:, 2 * H:] += (r * h_prev).T @ dhh_pre
            dh = dh * (1 - z) + d_rh * r + dz_pre @ p["U"][:, :H].T + dr_pre @ p["U"][:, H:2 * H].T
        g["W"] = x.reshape(-1, D).T @ dpre.reshape(-1, 3 * H)
        g["U"] = dU
        g["b"] = dpre.sum((0, 1))
        for k in ("W", "U", "Wo"):
            g[k] = g[k] + l2 * p[k]
        return loss, g

    def fit(self, x: np.ndarray, y: np.ndarray, epochs: int, seed: int,
            lr: float = 5e-3, l2: float = 1e-4, batch: int = 128) -> None:
        rng = np.random.default_rng(seed)
        m = {k: np.zeros_like(v) for k, v in self.p.items()}
        v2 = {k: np.zeros_like(v) for k, v in self.p.items()}
        step = 0
        for _ in range(epochs):
            order = rng.permutation(len(y))
            for start in range(0, len(y), batch):
                idx = order[start:start + batch]
                _, g = self.loss_and_grads(x[idx], y[idx], l2)
                step += 1
                for k in self.p:
                    m[k] = 0.9 * m[k] + 0.1 * g[k]
                    v2[k] = 0.999 * v2[k] + 0.001 * g[k] ** 2
                    mh, vh = m[k] / (1 - 0.9 ** step), v2[k] / (1 - 0.999 ** step)
                    self.p[k] -= lr * mh / (np.sqrt(vh) + 1e-8)

    def log_proba(self, x: np.ndarray) -> np.ndarray:
        out = []
        for s in range(0, len(x), 4096):
            logits = self.forward(x[s:s + 4096])
            logits -= logits.max(axis=1, keepdims=True)
            out.append(logits - np.log(np.exp(logits).sum(axis=1, keepdims=True)))
        return np.concatenate(out)


def train_gru(x: np.ndarray, y: np.ndarray, seed: int) -> NumpyGRU:
    model = NumpyGRU(x.shape[2], GRU_HIDDEN, len(TARGET_LABELS), seed)
    model.fit(x, y, GRU_EPOCHS, seed)
    return model


def gradient_check() -> float:
    """Сравнение аналитических градиентов GRU с численными (макс. относительная ошибка)."""
    rng = np.random.default_rng(0)
    model = NumpyGRU(5, 4, 3, seed=1)
    x = rng.normal(size=(6, 4, 5))
    y = rng.integers(0, 3, 6)
    _, grads = model.loss_and_grads(x, y, l2=1e-3)
    worst = 0.0
    for name, arr in model.p.items():
        for _ in range(6):
            idx = tuple(rng.integers(0, s) for s in arr.shape)
            old = arr[idx]
            arr[idx] = old + 1e-5
            lp, _ = model.loss_and_grads(x, y, l2=1e-3)
            arr[idx] = old - 1e-5
            lm, _ = model.loss_and_grads(x, y, l2=1e-3)
            arr[idx] = old
            num, ana = (lp - lm) / 2e-5, grads[name][idx]
            worst = max(worst, abs(num - ana) / max(1e-8, abs(num) + abs(ana)))
    return worst


# --------------------------------------------------------------------------- #
# Автоэнкодер (MLP по плоскому окну) + k-means
# --------------------------------------------------------------------------- #

def fit_ae_clusters(G: dict, train_frames: np.ndarray, seed: int) -> dict[int, np.ndarray]:
    """Без меток: автоэнкодер по окнам кадров train-матчей, затем k-means по латентному коду."""
    x_train = gather_windows(G, train_frames).reshape(len(train_frames), -1)
    ae = MLPRegressor(
        hidden_layer_sizes=(64, 12, 64), activation="tanh", max_iter=40,
        learning_rate_init=3e-3, random_state=seed,
    )
    ae.fit(x_train, x_train)

    def encode(x: np.ndarray) -> np.ndarray:
        a = np.tanh(x @ ae.coefs_[0] + ae.intercepts_[0])
        return np.tanh(a @ ae.coefs_[1] + ae.intercepts_[1])

    all_idx = np.arange(len(G["codes"]))
    z_all = np.concatenate([
        encode(gather_windows(G, all_idx[s:s + 4096]).reshape(len(all_idx[s:s + 4096]), -1))
        for s in range(0, len(all_idx), 4096)
    ])
    clusters = {}
    for c in AE_CLUSTERS:
        km = KMeans(n_clusters=c, n_init=3, random_state=seed).fit(z_all[train_frames])
        clusters[c] = km.predict(z_all)
    return clusters


# --------------------------------------------------------------------------- #
# HMM с факторизованными категориальными эмиссиями (numpy)
# --------------------------------------------------------------------------- #

class CategoricalHMM:
    def __init__(self, n_states: int, cards: list[int], seed: int):
        rng = np.random.default_rng(seed)
        self.n = n_states
        self.A = 0.7 * np.eye(n_states) + 0.3 * rng.dirichlet(np.ones(n_states), size=n_states)
        self.pi = np.full(n_states, 1.0 / n_states)
        self.B = [rng.dirichlet(np.ones(c) * 2.0, size=n_states) for c in cards]

    def _emission(self, obs: np.ndarray) -> np.ndarray:
        E = np.ones(obs.shape[:2] + (self.n,))
        for f, Bf in enumerate(self.B):
            E *= Bf[:, obs[:, :, f]].transpose(1, 2, 0)
        return E

    def _forward(self, E: np.ndarray, mask: np.ndarray):
        S, T, N = E.shape
        alpha = np.zeros((S, T, N))
        scale = np.ones((S, T))
        a = self.pi[None, :] * E[:, 0, :]
        c0 = np.maximum(a.sum(1), 1e-300)
        alpha[:, 0], scale[:, 0] = a / c0[:, None], c0
        for t in range(1, T):
            a = (alpha[:, t - 1] @ self.A) * E[:, t, :]
            m = mask[:, t]
            ct = np.where(m, np.maximum(a.sum(1), 1e-300), 1.0)
            alpha[:, t] = np.where(m[:, None], a / ct[:, None], alpha[:, t - 1])
            scale[:, t] = ct
        return alpha, scale

    def fit(self, seqs: list[np.ndarray], n_iter: int = 25) -> None:
        obs, mask = pad_sequences(seqs)
        S, T, F = obs.shape
        for _ in range(n_iter):
            E = self._emission(obs)
            alpha, scale = self._forward(E, mask)
            beta = np.ones_like(alpha)
            for t in range(T - 2, -1, -1):
                w = E[:, t + 1, :] * beta[:, t + 1, :] / scale[:, t + 1, None]
                beta[:, t, :] = np.where(mask[:, t + 1][:, None], w @ self.A.T, 1.0)
            gamma = alpha * beta
            gamma /= np.maximum(gamma.sum(2, keepdims=True), 1e-300)
            gamma *= mask[..., None]
            w_next = E[:, 1:, :] * beta[:, 1:, :] / scale[:, 1:, None] * mask[:, 1:, None]
            xi = self.A * np.einsum("sti,stj->ij", alpha[:, :-1, :], w_next)
            self.A = (xi + 1e-3) / (xi + 1e-3).sum(1, keepdims=True)
            self.pi = gamma[:, 0, :].sum(0) + 1e-3
            self.pi /= self.pi.sum()
            for f in range(F):
                counts = np.stack(
                    [(gamma * (obs[:, :, f] == v)[..., None]).sum((0, 1)) for v in range(self.B[f].shape[1])],
                    axis=1,
                ) + 1e-3
                self.B[f] = counts / counts.sum(1, keepdims=True)

    def filter(self, seqs: list[np.ndarray]) -> list[np.ndarray]:
        obs, mask = pad_sequences(seqs)
        alpha, _ = self._forward(self._emission(obs), mask)
        return [alpha[s, : len(seq)] for s, seq in enumerate(seqs)]


def pad_sequences(seqs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    t_max = max(len(s) for s in seqs)
    obs = np.zeros((len(seqs), t_max, seqs[0].shape[1]), dtype=np.int64)
    mask = np.zeros((len(seqs), t_max), dtype=bool)
    for i, s in enumerate(seqs):
        obs[i, : len(s)] = s
        mask[i, : len(s)] = True
    return obs, mask


def segments(G: dict, frame_mask: np.ndarray) -> list[np.ndarray]:
    """Непрерывные по времени отрезки кадров (глобальные индексы), ограниченные frame_mask."""
    out, cur = [], []
    for g in np.flatnonzero(frame_mask):
        if cur and not (g == cur[-1] + 1 and G["cstart"][g] == G["cstart"][cur[-1]]):
            out.append(np.array(cur))
            cur = []
        cur.append(g)
    if cur:
        out.append(np.array(cur))
    return out


def fit_hmm_filtered(G: dict, train_frames: np.ndarray, n_states: int, seed: int):
    """Обучает HMM на train-кадрах без меток цели; возвращает модель и фильтр для всех кадров."""
    obs_codes = G["codes"][:, STATE_FEATURES]
    train_mask = np.zeros(len(obs_codes), dtype=bool)
    train_mask[train_frames] = True
    hmm = CategoricalHMM(n_states, STATE_CARDS, seed)
    hmm.fit([obs_codes[s] for s in segments(G, train_mask)])
    alpha_all = np.zeros((len(obs_codes), n_states))
    all_segments = segments(G, np.ones(len(obs_codes), dtype=bool))
    for seg, alpha in zip(all_segments, hmm.filter([obs_codes[s] for s in all_segments])):
        alpha_all[seg] = alpha
    return hmm, alpha_all


def hmm_logp(hmm: CategoricalHMM, alpha_all: np.ndarray, gidx: np.ndarray, horizon: int) -> np.ndarray:
    cur_emission = hmm.B[len(STATE_FEATURES) - 1][:, : len(TARGET_LABELS)]  # P(cur=a | state), a в целях
    state_k = alpha_all[gidx] @ np.linalg.matrix_power(hmm.A, horizon)
    probs = state_k @ cur_emission
    probs /= np.maximum(probs.sum(1, keepdims=True), 1e-300)
    return np.log(np.maximum(probs, 1e-12))


# --------------------------------------------------------------------------- #
# Q-обучение (офлайн, табличное)
# --------------------------------------------------------------------------- #

REWARD_PASS_LOOKAHEAD = 8


def reward_for(G: dict, g: int, frame_mask: np.ndarray) -> float:
    """Награда за действие в кадре g+1 (ручная, см. docstring модуля).

    kickingG +3; passing +1 / -1 / 0 (мяч дошёл до своих / перехвачен / не ясно за 8 кадров);
    dribbling +0.1 (сохранили мяч) / -0.3 (мяч свободен) / -1 (перехват); fight, searching 0.
    """
    codes, cstart = G["codes"], G["cstart"]
    a, side = codes[g + 1, F_CUR], codes[g + 1, F_SIDE]
    if a == 2:
        return 3.0
    if a == 3:
        for f in range(g + 2, g + 2 + REWARD_PASS_LOOKAHEAD):
            if f >= len(codes) or not frame_mask[f] or cstart[f] != cstart[g + 1]:
                break
            if codes[f, F_SIDE] != 0:
                return 1.0 if codes[f, F_SIDE] == side else -1.0
        return 0.0
    if a == 0:
        f = g + 2
        if f < len(codes) and frame_mask[f] and cstart[f] == cstart[g + 1]:
            nxt = codes[f, F_SIDE]
            if nxt == side:
                return 0.1
            return -0.3 if nxt == 0 else -1.0
    return 0.0


def fit_q(G: dict, train_frames: np.ndarray, gamma: float = 0.9, iters: int = 30):
    """Fitted Q Iteration: Q(s,a) = среднее [r + gamma * max_{a' в поддержке} Q(s',a')]."""
    mask = np.zeros(len(G["codes"]), dtype=bool)
    mask[train_frames] = True
    g = np.flatnonzero(mask[:-1] & mask[1:] & (G["cstart"][1:] == G["cstart"][:-1]))
    s, s2 = G["state"][g], G["state"][g + 1]
    a = G["codes"][g + 1, F_CUR]
    r = np.array([reward_for(G, int(i), mask) for i in g])

    n_states = int(np.prod(STATE_CARDS))
    n = np.zeros((n_states, N_ACTIONS))
    np.add.at(n, (s, a), 1)
    support = n > 0
    Q = np.zeros((n_states, N_ACTIONS))
    for _ in range(iters):
        V = np.where(support, Q, -np.inf).max(axis=1)
        V[~support.any(axis=1)] = 0.0
        sums = np.zeros_like(Q)
        np.add.at(sums, (s, a), r + gamma * V[s2])
        Q = np.divide(sums, n, out=np.zeros_like(sums), where=n > 0)
    return Q, n


def q_scores(Q: np.ndarray, n: np.ndarray, states: np.ndarray, min_count: int) -> np.ndarray:
    scores = np.where(n[states, : len(TARGET_LABELS)] >= min_count, Q[states, : len(TARGET_LABELS)], -1e9)
    return scores


# --------------------------------------------------------------------------- #
# Протокол
# --------------------------------------------------------------------------- #

class HorizonData:
    def __init__(self, horizon: int, ds: pd.DataFrame, G: dict):
        self.k = horizon
        self.ds = ds
        self.part = ds["part"].to_numpy()
        self.aug = ds["aug"].to_numpy(dtype=bool)
        self.match = ds["match"].to_numpy(dtype=object)
        self.cur = ds["cur"].to_numpy(dtype=object)
        self.target = ds["target"].to_numpy(dtype=object)
        self.y = np.array([TARGET_LABELS.index(t) for t in self.target])
        self.gidx = np.array(
            [G["offsets"][m] + i for m, i in zip(self.match, ds["frame"].to_numpy())], dtype=np.int64
        )
        self.dev_real = np.flatnonzero((self.part == "dev") & ~self.aug)
        self.hold = np.flatnonzero(self.part == "holdout")
        n = len(ds)
        self.store: dict[tuple[str, object], dict[str, np.ndarray]] = {}
        self._n = n

    def slot(self, model: str, config) -> dict[str, np.ndarray]:
        key = (model, config)
        if key not in self.store:
            self.store[key] = {
                "logp": np.zeros((self._n, len(TARGET_LABELS))),
                "logprior": np.zeros((self._n, len(TARGET_LABELS))),
            }
        return self.store[key]


def log_prior(y: np.ndarray) -> np.ndarray:
    counts = np.bincount(y, minlength=len(TARGET_LABELS)) + 1.0
    return np.log(counts / counts.sum())


def run_fold(
    fold_name: str,
    train_matches: list[str],
    G: dict,
    data: dict[int, HorizonData],
    models: list[str],
    seed: int,
) -> None:
    train_match_ids = np.array([G["names"].index(m) for m in train_matches])
    train_frames = np.flatnonzero(G["is_dev"] & np.isin(G["match_id"], train_match_ids))
    is_final = fold_name == "final"

    started = time_module.time()
    clusters, hmms, q_model = {}, {}, None
    if "ae-kmeans" in models:
        clusters = fit_ae_clusters(G, train_frames, seed)
    if "hmm" in models:
        for n_states in HMM_STATES:
            hmms[n_states] = fit_hmm_filtered(G, train_frames, n_states, seed)
    if "q-greedy" in models:
        q_model = fit_q(G, train_frames)
    log(f"  [{fold_name}] unsupervised/Q готовы за {time_module.time() - started:.0f}с")

    for k, hd in data.items():
        in_train = np.isin(hd.match, train_matches)
        train_real = np.flatnonzero((hd.part == "dev") & ~hd.aug & in_train)
        train_pool = np.flatnonzero((hd.part == "dev") & in_train)
        test = hd.hold if is_final else hd.dev_real[hd.match[hd.dev_real] == fold_name]
        prior_real = log_prior(hd.y[train_real])

        def put(model: str, config, logp: np.ndarray, logprior: np.ndarray) -> None:
            slot = hd.slot(model, config)
            slot["logp"][test] = logp
            slot["logprior"][test] = logprior[None, :] if logprior.ndim == 1 else logprior

        for model, rows in (("gru", train_real), ("gru+horizon", train_pool)):
            if model not in models:
                continue
            tr_model = train_gru(gather_windows(G, hd.gidx[rows]), hd.y[rows], seed)
            logp = tr_model.log_proba(gather_windows(G, hd.gidx[test]))
            put(model, "gru", logp, log_prior(hd.y[rows]))

        if "ae-kmeans" in models:
            for c, cluster_ids in clusters.items():
                counts = np.ones((c, len(TARGET_LABELS)))
                np.add.at(counts, (cluster_ids[hd.gidx[train_real]], hd.y[train_real]), 1)
                table = np.log(counts / counts.sum(1, keepdims=True))
                put("ae-kmeans", c, table[cluster_ids[hd.gidx[test]]], prior_real)

        if "hmm" in models:
            for n_states, (hmm, alpha_all) in hmms.items():
                put("hmm", n_states, hmm_logp(hmm, alpha_all, hd.gidx[test], k), prior_real)

        if "q-greedy" in models and k == 1:
            Q, n = q_model
            for min_count in Q_MIN_COUNTS:
                scores = q_scores(Q, n, G["state"][hd.gidx[test]], min_count)
                put("q-greedy", min_count, scores, np.zeros(len(TARGET_LABELS)))


def predictions(slot: dict[str, np.ndarray], rows: np.ndarray, alpha: float) -> np.ndarray:
    scores = slot["logp"][rows] - alpha * slot["logprior"][rows]
    return np.array(TARGET_LABELS, dtype=object)[scores.argmax(axis=1)]


def select_and_report(data: dict[int, HorizonData], models: list[str]) -> tuple[list[dict], list[dict]]:
    cv_rows, hold_rows = [], []
    for k, hd in data.items():
        # baseline'ы
        oof = {"persistence": np.empty(len(hd.ds), dtype=object), "markov": np.empty(len(hd.ds), dtype=object)}
        for test_match in dict.fromkeys(hd.match[hd.dev_real]):
            te = hd.dev_real[hd.match[hd.dev_real] == test_match]
            tr = hd.dev_real[hd.match[hd.dev_real] != test_match]
            oof["markov"][te] = predict_markov(hd.cur[te], fit_markov(hd.cur[tr], hd.target[tr]))
            oof["persistence"][te] = hd.cur[te]
        hold_pred = {
            "persistence": hd.cur[hd.hold],
            "markov": predict_markov(hd.cur[hd.hold], fit_markov(hd.cur[hd.dev_real], hd.target[hd.dev_real])),
        }
        for name in ["persistence", "markov"]:
            base = {"horizon": k, "model": name, "config": "-"}
            cv_rows.append({**base, **balanced_metrics(hd.target[hd.dev_real], oof[name][hd.dev_real])})
            hold_rows.append({**base, **balanced_metrics(hd.target[hd.hold], hold_pred[name])})

        # модели: конфигурация и alpha выбираются по CV
        for model in ["gru", "gru+horizon", "ae-kmeans", "hmm", "q-greedy"]:
            if model not in models:
                continue
            configs = [key[1] for key in hd.store if key[0] == model]
            if not configs:
                continue
            alphas = [0.0] if model == "q-greedy" else ALPHAS
            best = None
            for config in configs:
                for alpha in alphas:
                    m = balanced_metrics(
                        hd.target[hd.dev_real], predictions(hd.slot(model, config), hd.dev_real, alpha)
                    )
                    if best is None or (m["f1_macro"], m["acc"]) > (best[2]["f1_macro"], best[2]["acc"]):
                        best = (config, alpha, m)
            config, alpha, m = best
            base = {"horizon": k, "model": model, "config": f"{config}/a={alpha}"}
            cv_rows.append({**base, **m})
            hold_rows.append({
                **base,
                **balanced_metrics(hd.target[hd.hold], predictions(hd.slot(model, config), hd.hold, alpha)),
            })

            if model == "q-greedy":
                preds = predictions(hd.slot(model, config), hd.dev_real, alpha)
                agree = pd.Series(preds == hd.target[hd.dev_real]).groupby(hd.match[hd.dev_real]).mean()
                log(f"\n  Q-greedy (k=1): доля совпадений с реальным действием по матчам (реальное распределение):")
                log("    " + agree.round(3).to_string().replace("\n", "\n    "))
    return cv_rows, hold_rows


def format_table(rows: list[dict], title: str) -> None:
    log(f"\n##### {title}; равные классы #####")
    table = []
    for r in rows:
        table.append({
            "k": r["horizon"], "model": r["model"], "config": r["config"], "n/class": r["n_per_class"],
            "acc": round(r["acc"], 3), "f1_macro": round(r["f1_macro"], 3),
            **{f"f1_{c}": round(r["f1"].get(c, float("nan")), 3) for c in TARGET_LABELS},
            "acc_raw": round(r["acc_raw"], 3),
        })
    log(pd.DataFrame(table).to_string(index=False))


ALL_MODELS = ["gru", "gru+horizon", "ae-kmeans", "hmm", "q-greedy"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument("--models", nargs="+", default=ALL_MODELS, choices=ALL_MODELS)
    parser.add_argument("--check-only", action="store_true", help="только градиентная проверка GRU")
    parser.add_argument("--smoke", action="store_true", help="быстрый прогон на 3 матчах для проверки кода")
    args = parser.parse_args()

    parser_smoke = args.smoke
    log(f"Градиентная проверка GRU: макс. относительная ошибка = {gradient_check():.2e}")
    if args.check_only:
        return

    global GRU_EPOCHS, HMM_STATES, AE_CLUSTERS
    if parser_smoke:  # быстрый прогон для проверки кода, метрики не осмысленны
        GRU_EPOCHS, HMM_STATES, AE_CLUSTERS = 1, [4], [8]
    full_df = load_groundtruth(ALL_MATCHES[:3] if parser_smoke else ALL_MATCHES)
    log(f"All rows: {len(full_df)}  action: {calc_stats(full_df, 'action')}")
    log(f"Цель без {sorted(EXCLUDED_ACTIONS)}; горизонты {args.horizons}; модели {args.models}")

    frames = {name: build_match_frame(df) for name, df in full_df.groupby("match", sort=False)}
    G = build_global(frames)
    data = {}
    for k in args.horizons:
        ds, _ = build_horizon_dataset(frames, k, ["A"])
        data[k] = HorizonData(k, ds, G)
        log(f"k={k}: dev real={len(data[k].dev_real)} holdout={len(data[k].hold)} "
            f"target dev: {calc_stats(ds.iloc[data[k].dev_real], 'target')}")

    dev_matches = list(G["names"])
    for fold, test_match in enumerate(dev_matches + ["final"]):
        train_matches = dev_matches if test_match == "final" else [m for m in dev_matches if m != test_match]
        log(f"\n--- фолд {fold + 1}/{len(dev_matches) + 1}: тест={test_match} ---")
        run_fold(test_match, train_matches, G, data, args.models, SEED + fold)

    cv_rows, hold_rows = select_and_report(data, args.models)
    format_table(cv_rows, "CV на dev (pooled out-of-fold)")
    format_table(hold_rows, "Holdout 25% (один прогон, конфигурация выбрана по CV)")


if __name__ == "__main__":
    main()
