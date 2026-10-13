# -*- coding: utf-8 -*-
"""Прогноз БУДУЩЕГО action (t+k) ассоциативными правилами + аугментация редких классов.

Постановка: по ситуации в цикле t предсказать action в цикле t+k (k по времени,
а не по номеру строки: в `time` бывают разрывы). `searching` остаётся в истории
как входной признак, но не как цель (строки с целью searching исключены).

Протокол:
  * holdout = последние 25% циклов каждого матча, в обучении и CV не участвует;
  * CV = leave-one-match-out на оставшихся 75%;
  * аугментация применяется ТОЛЬКО к обучающей части; тест и holdout реальные;
  * оценка на равном числе строк на класс (многократный undersampling);
  * метод аугментации и конфигурация правил выбираются по CV на dev;
    holdout считается один раз для выбранного метода и для baseline без аугментации.
"""

from __future__ import annotations

import argparse
import time as time_module

import numpy as np
import pandas as pd

from augment_classes import balance_classes, median_class_size
from for_predict_strategy import (
    ACTION_PREFIX,
    ALL_MATCHES,
    EXCLUDED_ACTIONS,
    HOLDOUT_FRACTION,
    MIN_SUPPORT,
    calc_stats,
    load_groundtruth,
    mine_action_rules,
    row_to_items,
    transactions_to_onehot,
)

TARGET_LABELS = ["dribbling", "fight", "kickingG", "passing"]
MAJORITY_LABEL = "dribbling"
VARIANT_DESC = {
    "A": "кадр t",
    "B": "кадр t + cur",
    "C": "кадр t + cur + dur + prev + изменения",
}
CHANGE_WINDOW = 3
MINING_MAX_LEN = 5
MINING_MIN_CONF = 0.02
MIN_RULE_COUNT = 8  # абсолютный минимум строк под правило, если выборка мала
CONF_GRID = [0.75, 0.3, 0.1, 0.03]
STRATEGIES = ["specific", "lift"]
N_BALANCE_REPEATS = 100
SEED = 42
POOL_DELTAS = (-2, -1, 1, 2)

# pool    — добавлять реальные пары (кадр, цель) с соседними горизонтами k+δ для редких целей;
# balance — как выравнивать классы в обучении (None = не трогать);
#           для oversample / mutate мажоритарный класс урезается до медианного размера.
METHODS = {
    "none": {"pool": False, "balance": None},
    "horizon": {"pool": True, "balance": None},
    "oversample": {"pool": False, "balance": "oversample"},
    "mutate": {"pool": False, "balance": "mutate"},
    "horizon+mutate": {"pool": True, "balance": "mutate"},
}


def log(message: str) -> None:
    print(message, flush=True)


# --------------------------------------------------------------------------- #
# Признаки
# --------------------------------------------------------------------------- #

def _dur_bin(duration: int) -> str:
    if duration == 1:
        return "dur=1"
    if duration <= 3:
        return "dur=2-3"
    if duration <= 10:
        return "dur=4-10"
    return "dur=11+"


def _sign(delta: int) -> str:
    if delta > 0:
        return "up"
    if delta < 0:
        return "down"
    return "same"


def build_match_frame(match_df: pd.DataFrame) -> dict:
    """Признаки каждого цикла матча для вариантов A / B / C."""
    g = match_df.sort_values("time").reset_index(drop=True)
    n = len(g)
    times = g["time"].to_numpy(dtype=int)
    actions = g["action"].astype(str).tolist()
    near = g["lenOfNearest"].fillna(0).to_numpy(dtype=float).astype(int)
    mid = g["lenOfMiddleDist"].fillna(0).to_numpy(dtype=float).astype(int)
    has_ball = (g["sideWithBall"].fillna("").astype(str).str.strip() != "").to_numpy()
    idx_by_time = {int(t): i for i, t in enumerate(times)}

    # ball= дублирует side=none/L/R, поэтому в правилах он не нужен.
    base = [
        [it for it in row_to_items(row) if not it.startswith((ACTION_PREFIX, "ball="))]
        for _, row in g.iterrows()
    ]

    dur = [1] * n
    prev_episode = ["none"] * n
    for i in range(1, n):
        if times[i] == times[i - 1] + 1:
            if actions[i] == actions[i - 1]:
                dur[i] = dur[i - 1] + 1
                prev_episode[i] = prev_episode[i - 1]
            else:
                prev_episode[i] = actions[i - 1]

    items = {"A": [], "B": [], "C": []}
    for i in range(n):
        a_items = list(base[i])
        b_items = a_items + [f"cur={actions[i]}"]
        c_items = b_items + [_dur_bin(dur[i]), f"prev={prev_episode[i]}"]
        j = idx_by_time.get(int(times[i]) - CHANGE_WINDOW)
        if j is not None:
            if has_ball[i] and not has_ball[j]:
                ball_chg = "gained"
            elif has_ball[j] and not has_ball[i]:
                ball_chg = "lost"
            else:
                ball_chg = "same"
            c_items += [
                f"near_chg={_sign(int(near[i] - near[j]))}",
                f"mid_chg={_sign(int(mid[i] - mid[j]))}",
                f"ball_chg={ball_chg}",
            ]
        items["A"].append(a_items)
        items["B"].append(b_items)
        items["C"].append(c_items)

    return {
        "n": n,
        "times": times,
        "actions": actions,
        "idx_by_time": idx_by_time,
        "items": items,
    }


def split_point(n: int, holdout_fraction: float = HOLDOUT_FRACTION) -> int:
    """Индекс первого кадра holdout в матче из n кадров."""
    n_holdout = min(max(1, int(round(n * holdout_fraction))), n - 1)
    return n - n_holdout


def build_horizon_dataset(
    frames: dict[str, dict],
    horizon: int,
    variants: list[str],
    holdout_fraction: float = HOLDOUT_FRACTION,
    pool_deltas: tuple[int, ...] = POOL_DELTAS,
) -> tuple[pd.DataFrame, dict[str, list[list[str]]]]:
    """Пары (ситуация в t, action в t+k) с разбиением dev / holdout по времени.

    Кроме реальных строк (aug=False) добавляются строки aug=True: для редких
    целей — реальные пары с соседними горизонтами k+δ. Они только из dev и
    используются только в обучении.
    """
    records = []
    variant_items: dict[str, list[list[str]]] = {v: [] for v in variants}

    def add(match: str, part: str, frame: dict, i: int, target: str, aug: bool) -> None:
        records.append((match, part, frame["actions"][i], target, aug, i))
        for v in variants:
            variant_items[v].append(frame["items"][v][i])

    for match, frame in frames.items():
        n = frame["n"]
        split_at = split_point(n, holdout_fraction)
        times, actions = frame["times"], frame["actions"]

        for i in range(n):
            j = frame["idx_by_time"].get(int(times[i]) + horizon)
            if j is None:
                continue
            target = actions[j]
            if target in EXCLUDED_ACTIONS:
                continue
            if i < split_at:
                if j >= split_at:  # цель из holdout не должна попадать в dev
                    continue
                add(match, "dev", frame, i, target, aug=False)
            else:
                add(match, "holdout", frame, i, target, aug=False)

        for j in range(split_at):
            target = actions[j]
            if target in EXCLUDED_ACTIONS or target == MAJORITY_LABEL:
                continue
            for delta in pool_deltas:
                shifted = horizon + delta
                if shifted < 1:
                    continue
                i = frame["idx_by_time"].get(int(times[j]) - shifted)
                if i is None or i >= split_at:
                    continue
                add(match, "dev", frame, i, target, aug=True)

    ds = pd.DataFrame(records, columns=["match", "part", "cur", "target", "aug", "frame"])
    return ds, variant_items


def build_vocab(variant_items: list[list[str]]) -> dict[str, int]:
    vocab = sorted({item for items in variant_items for item in items})
    if len(vocab) > 63:
        raise ValueError(f"Слишком много item'ов для uint64-маски: {len(vocab)}")
    return {item: bit for bit, item in enumerate(vocab)}


def items_to_mask(items: list[str] | frozenset[str], vocab: dict[str, int]) -> int:
    mask = 0
    for item in items:
        bit = vocab.get(item)
        if bit is not None:
            mask |= 1 << bit
    return mask


# --------------------------------------------------------------------------- #
# Правила и предсказание
# --------------------------------------------------------------------------- #

def mine_rules(items: list[list[str]], targets) -> pd.DataFrame:
    transactions = [it + [f"{ACTION_PREFIX}{t}"] for it, t in zip(items, targets)]
    min_support = max(MIN_SUPPORT, MIN_RULE_COUNT / max(1, len(transactions)))
    return mine_action_rules(
        transactions_to_onehot(transactions),
        min_support=min_support,
        min_confidence=MINING_MIN_CONF,
        max_len=MINING_MAX_LEN,
    )


class RuleTable:
    """Правила с масками антецедентов для быстрого CBA-предсказания."""

    def __init__(self, rules: pd.DataFrame, vocab: dict[str, int]):
        self.empty = rules.empty
        if self.empty:
            return
        self.ant_masks = np.array(
            [items_to_mask(a, vocab) for a in rules["antecedents"]], dtype=np.uint64
        )
        self.lens = np.array([len(a) for a in rules["antecedents"]], dtype=np.int64)
        self.cons = np.array(
            [next(iter(c))[len(ACTION_PREFIX):] for c in rules["consequents"]], dtype=object
        )
        self.conf = rules["confidence"].to_numpy(dtype=float)
        self.lift = rules["lift"].to_numpy(dtype=float)
        self.sup = rules["support"].to_numpy(dtype=float)

    def predict(
        self,
        uniq_masks: np.ndarray,
        strategy: str,
        min_conf: float,
        default: str,
    ) -> np.ndarray:
        if self.empty:
            return np.full(len(uniq_masks), default, dtype=object)
        keep = np.flatnonzero(self.conf >= min_conf)
        if len(keep) == 0:
            return np.full(len(uniq_masks), default, dtype=object)

        if strategy == "specific":  # как в for_predict_strategy.py
            order = np.lexsort((self.lift[keep], self.conf[keep], self.lens[keep]))[::-1]
        elif strategy == "lift":  # при равных классах в тесте argmax lift = argmax posterior
            order = np.lexsort((self.sup[keep], self.conf[keep], self.lift[keep]))[::-1]
        else:
            raise ValueError(strategy)
        keep = keep[order]
        ants = self.ant_masks[keep]
        cons = self.cons[keep]

        out = np.empty(len(uniq_masks), dtype=object)
        step = 512
        for start in range(0, len(uniq_masks), step):
            chunk = uniq_masks[start:start + step]
            matched = (chunk[:, None] & ants[None, :]) == ants[None, :]
            has = matched.any(axis=1)
            first = matched.argmax(axis=1)
            out[start:start + len(chunk)] = np.where(has, cons[first], default)
        return out


# --------------------------------------------------------------------------- #
# Baseline'ы
# --------------------------------------------------------------------------- #

def fit_markov(cur: np.ndarray, target: np.ndarray) -> tuple[dict[str, str], str]:
    table = pd.crosstab(pd.Series(cur, name="cur"), pd.Series(target, name="target"))
    mapping = table.idxmax(axis=1).to_dict()
    default = pd.Series(target).value_counts().idxmax()
    return mapping, default


def predict_markov(cur: np.ndarray, model: tuple[dict[str, str], str]) -> np.ndarray:
    mapping, default = model
    return np.array([mapping.get(c, default) for c in cur], dtype=object)


# --------------------------------------------------------------------------- #
# Метрики на равных классах
# --------------------------------------------------------------------------- #

def balanced_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    repeats: int = N_BALANCE_REPEATS,
    seed: int = SEED,
) -> dict:
    """Accuracy и macro-F1 на выборке с равным числом строк на класс.

    Undersampling повторяется `repeats` раз, метрики усредняются: на малых
    выборках (редкие классы) один случайный undersample слишком шумный.
    """
    y_true = np.asarray(y_true, dtype=object)
    y_pred = np.asarray(y_pred, dtype=object)
    by_class = {c: np.flatnonzero(y_true == c) for c in TARGET_LABELS}
    present = [c for c in TARGET_LABELS if len(by_class[c]) > 0]
    n = min(len(by_class[c]) for c in present)
    rng = np.random.default_rng(seed)

    accs, macros = [], []
    per_class = {c: [] for c in present}
    for _ in range(repeats):
        sel = np.concatenate([rng.choice(by_class[c], size=n, replace=False) for c in present])
        yt, yp = y_true[sel], y_pred[sel]
        accs.append(float((yt == yp).mean()))
        f1s = []
        for c in present:
            tp = int(((yt == c) & (yp == c)).sum())
            fp = int(((yt != c) & (yp == c)).sum())
            fn = int(((yt == c) & (yp != c)).sum())
            denom = 2 * tp + fp + fn
            f1 = 2 * tp / denom if denom else 0.0
            per_class[c].append(f1)
            f1s.append(f1)
        macros.append(float(np.mean(f1s)))

    return {
        "n_per_class": n,
        "acc": float(np.mean(accs)),
        "f1_macro": float(np.mean(macros)),
        "f1": {c: float(np.mean(v)) for c, v in per_class.items()},
        "acc_raw": float((y_true == y_pred).mean()),
    }


# --------------------------------------------------------------------------- #
# Эксперимент
# --------------------------------------------------------------------------- #

def prepare_training(
    items: list[list[str]],
    targets: np.ndarray,
    is_aug: np.ndarray,
    method: str,
    rng: np.random.Generator,
) -> tuple[list[list[str]], np.ndarray, dict]:
    """Применяет pool (отбор aug-строк) и выравнивание классов к обучающей части."""
    spec = METHODS[method]
    keep = np.ones(len(items), dtype=bool) if spec["pool"] else ~is_aug
    items = [it for it, k in zip(items, keep) if k]
    targets_kept = targets[keep]
    if spec["balance"] is None:
        report = {c: (int(n), int(n)) for c, n in pd.Series(targets_kept).value_counts().items()}
        return items, targets_kept, report

    # размер класса считаем по реальным строкам, чтобы пулинг не менял цель выравнивания
    target_size = median_class_size(targets[~is_aug])
    return balance_classes(
        items, targets_kept, target_size, method=spec["balance"], rng=rng, majority="undersample"
    )


def run_horizon(
    horizon: int,
    ds: pd.DataFrame,
    variant_items: dict[str, list[list[str]]],
    methods: list[str],
    variants: list[str],
) -> tuple[list[dict], list[dict]]:
    part = ds["part"].to_numpy()
    is_aug = ds["aug"].to_numpy(dtype=bool)
    dev_real = np.flatnonzero((part == "dev") & ~is_aug)
    dev_all = np.flatnonzero(part == "dev")
    hold_idx = np.flatnonzero(part == "holdout")
    cur = ds["cur"].to_numpy(dtype=object)
    target = ds["target"].to_numpy(dtype=object)
    match = ds["match"].to_numpy(dtype=object)
    dev_matches = list(dict.fromkeys(match[dev_real]))

    log(f"\n=== Горизонт k={horizon}: dev real={len(dev_real)} (+aug {len(dev_all) - len(dev_real)}) "
        f"holdout={len(hold_idx)} ===")
    log(f"  dev target: {calc_stats(ds.iloc[dev_real], 'target')}")

    cv_rows: list[dict] = []
    hold_rows: list[dict] = []

    # ---- baseline'ы (только реальные строки) ------------------------------
    oof = {"persistence": np.empty(len(ds), dtype=object), "markov": np.empty(len(ds), dtype=object)}
    for test_match in dev_matches:
        te = dev_real[match[dev_real] == test_match]
        tr = dev_real[match[dev_real] != test_match]
        oof["markov"][te] = predict_markov(cur[te], fit_markov(cur[tr], target[tr]))
        oof["persistence"][te] = cur[te]
    final_markov = fit_markov(cur[dev_real], target[dev_real])
    hold_pred = {
        "persistence": cur[hold_idx],
        "markov": predict_markov(cur[hold_idx], final_markov),
    }
    for name in ["persistence", "markov"]:
        row = {"horizon": horizon, "variant": "-", "method": name, "config": "-"}
        cv_rows.append({**row, **balanced_metrics(target[dev_real], oof[name][dev_real])})
        hold_rows.append({**row, **balanced_metrics(target[hold_idx], hold_pred[name])})

    # ---- правила: CV по всем методам --------------------------------------
    configs = [(s, c) for s in STRATEGIES for c in CONF_GRID]
    prepared: dict[str, dict] = {}
    for variant in variants:
        items = variant_items[variant]
        vocab = build_vocab(items)
        masks = np.array([items_to_mask(it, vocab) for it in items], dtype=np.uint64)
        prepared[variant] = {"items": items, "vocab": vocab, "masks": masks, "cv": {}}

        for method in methods:
            oof_cfg = {cfg: np.empty(len(ds), dtype=object) for cfg in configs}
            started = time_module.time()
            for fold, test_match in enumerate(dev_matches):
                te = dev_real[match[dev_real] == test_match]
                tr = dev_all[match[dev_all] != test_match]
                rng = np.random.default_rng(SEED + fold)
                tr_items, tr_targets, report = prepare_training(
                    [items[i] for i in tr], target[tr], is_aug[tr], method, rng
                )
                if fold == 0:
                    log(f"  [{variant}/{method}] обучение (фолд 0): {report}")
                table = RuleTable(mine_rules(tr_items, tr_targets), vocab)
                default = pd.Series(target[tr][~is_aug[tr]]).value_counts().idxmax()
                uniq, inverse = np.unique(masks[te], return_inverse=True)
                for cfg in configs:
                    oof_cfg[cfg][te] = table.predict(uniq, cfg[0], cfg[1], default)[inverse]

            metrics = {cfg: balanced_metrics(target[dev_real], oof_cfg[cfg][dev_real]) for cfg in configs}
            best_cfg = max(configs, key=lambda c: (metrics[c]["f1_macro"], metrics[c]["acc"]))
            prepared[variant]["cv"][method] = (best_cfg, metrics[best_cfg])
            log(f"  [{variant}/{method}] CV {time_module.time() - started:.0f}с  "
                f"лучший {best_cfg}: f1_macro={metrics[best_cfg]['f1_macro']:.3f}")
            cv_rows.append({
                "horizon": horizon, "variant": variant, "method": method,
                "config": f"{best_cfg[0]}/{best_cfg[1]}", **metrics[best_cfg],
            })

    # ---- holdout: только выбранный по CV метод и baseline без аугментации ---
    for variant in variants:
        cv = prepared[variant]["cv"]
        best_method = max(methods, key=lambda m: (cv[m][1]["f1_macro"], cv[m][1]["acc"]))
        to_eval = [best_method] if best_method == "none" else [best_method, "none"]
        if "none" not in methods:
            to_eval = [best_method]
        log(f"  [{variant}] лучший метод по CV: {best_method}")
        items, vocab, masks = (prepared[variant][k] for k in ("items", "vocab", "masks"))
        uniq, inverse = np.unique(masks[hold_idx], return_inverse=True)
        for method in to_eval:
            cfg = cv[method][0]
            tr_items, tr_targets, _ = prepare_training(
                [items[i] for i in dev_all], target[dev_all], is_aug[dev_all], method,
                np.random.default_rng(SEED),
            )
            table = RuleTable(mine_rules(tr_items, tr_targets), vocab)
            default = pd.Series(target[dev_real]).value_counts().idxmax()
            pred = table.predict(uniq, cfg[0], cfg[1], default)[inverse]
            hold_rows.append({
                "horizon": horizon, "variant": variant,
                "method": method + (" (выбран по CV)" if method == best_method else " (без аугм.)"),
                "config": f"{cfg[0]}/{cfg[1]}",
                **balanced_metrics(target[hold_idx], pred),
            })
    return cv_rows, hold_rows


def format_table(rows: list[dict], title: str) -> None:
    log(f"\n##### {title}; равные классы #####")
    table = []
    for r in rows:
        table.append({
            "k": r["horizon"], "var": r["variant"], "method": r["method"], "config": r["config"],
            "n/class": r["n_per_class"],
            "acc": round(r["acc"], 3), "f1_macro": round(r["f1_macro"], 3),
            **{f"f1_{c}": round(r["f1"].get(c, float("nan")), 3) for c in TARGET_LABELS},
            "acc_raw": round(r["acc_raw"], 3),
        })
    log(pd.DataFrame(table).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument("--variants", nargs="+", default=["A", "C"], choices=list(VARIANT_DESC))
    parser.add_argument("--methods", nargs="+", default=list(METHODS), choices=list(METHODS))
    args = parser.parse_args()

    full_df = load_groundtruth(ALL_MATCHES)
    log(f"All rows: {len(full_df)}  action: {calc_stats(full_df, 'action')}")
    log(f"Цель без {sorted(EXCLUDED_ACTIONS)}; searching остаётся в истории (cur/prev).")
    log(f"Горизонты {args.horizons}, варианты {args.variants}, методы {args.methods}")

    started = time_module.time()
    frames = {
        match_name: build_match_frame(match_df)
        for match_name, match_df in full_df.groupby("match", sort=False)
    }
    log(f"Признаки построены за {time_module.time() - started:.1f}с")

    all_cv: list[dict] = []
    all_hold: list[dict] = []
    for horizon in args.horizons:
        ds, variant_items = build_horizon_dataset(frames, horizon, args.variants)
        cv_rows, hold_rows = run_horizon(horizon, ds, variant_items, args.methods, args.variants)
        all_cv.extend(cv_rows)
        all_hold.extend(hold_rows)

    format_table(all_cv, "CV на dev (pooled out-of-fold, реальные тест-строки)")
    format_table(all_hold, "Holdout 25% (один прогон: выбранный по CV метод и без аугментации)")


if __name__ == "__main__":
    main()
