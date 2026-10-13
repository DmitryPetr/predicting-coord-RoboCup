# -*- coding: utf-8 -*-
"""Выравнивание классов для транзакций (списков категориальных item'ов).

Работает с данными вида: items = [["side=L", "near=1", ...], ...], targets = ["fight", ...].
Применять только к ОБУЧАЮЩЕЙ части: тест и holdout должны оставаться реальными.

Методы добора редких классов:
  * "oversample" — случайное дублирование строк (baseline);
  * "mutate"     — категориальный аналог SMOTE (SMOTE-N): берём строку класса,
                   находим k ближайших соседей того же класса по Хэммингу и
                   по каждой группе признаков (side, near, mid, ...) с вероятностью
                   `mix_rate` подставляем значение соседа.

Мажоритарные классы при `majority="undersample"` случайно урезаются до `target_size`.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

METHODS = ("none", "oversample", "mutate")


def item_group(item: str) -> str:
    """'near_chg=up' -> 'near_chg'; одна группа = один признак."""
    return item.split("=", 1)[0]


def median_class_size(targets) -> int:
    counts = sorted(Counter(targets).values())
    return int(np.median(counts))


def oversample_random(
    items: list[list[str]],
    n_new: int,
    rng: np.random.Generator,
) -> list[list[str]]:
    if n_new <= 0 or not items:
        return []
    picks = rng.integers(0, len(items), size=n_new)
    return [list(items[i]) for i in picks]


def mutate_samples(
    items: list[list[str]],
    n_new: int,
    rng: np.random.Generator,
    k_neighbors: int = 5,
    mix_rate: float = 0.3,
) -> list[list[str]]:
    """Синтетические строки: кроссовер по группам признаков с ближайшим соседом."""
    n = len(items)
    if n_new <= 0 or n == 0:
        return []
    if n == 1:
        return oversample_random(items, n_new, rng)

    vocab = {item: idx for idx, item in enumerate(sorted({x for row in items for x in row}))}
    matrix = np.zeros((n, len(vocab)), dtype=np.float32)
    for r, row in enumerate(items):
        for item in row:
            matrix[r, vocab[item]] = 1.0

    sizes = matrix.sum(axis=1)
    distance = sizes[:, None] + sizes[None, :] - 2.0 * (matrix @ matrix.T)  # Хэмминг
    np.fill_diagonal(distance, np.inf)
    k = min(k_neighbors, n - 1)
    neighbors = np.argpartition(distance, k - 1, axis=1)[:, :k]

    groups = [{item_group(x): x for x in row} for row in items]
    synthetic = []
    for _ in range(n_new):
        seed = int(rng.integers(0, n))
        donor = int(neighbors[seed][rng.integers(0, k)])
        seed_groups, donor_groups = groups[seed], groups[donor]
        row = []
        for group in sorted(set(seed_groups) | set(donor_groups)):
            source = donor_groups if rng.random() < mix_rate else seed_groups
            item = source.get(group)
            if item is not None:
                row.append(item)
        synthetic.append(row)
    return synthetic


def balance_classes(
    items: list[list[str]],
    targets,
    target_size: int,
    method: str = "mutate",
    rng: np.random.Generator | None = None,
    majority: str = "undersample",
    max_factor: float | None = 20.0,
    k_neighbors: int = 5,
    mix_rate: float = 0.3,
) -> tuple[list[list[str]], np.ndarray, dict[str, tuple[int, int]]]:
    """Приводит каждый класс к `target_size` строкам.

    method:   "none" | "oversample" | "mutate" — как добирать редкие классы.
    majority: "undersample" — урезать большие классы до target_size, "keep" — не трогать.
    max_factor: максимум во сколько раз класс можно увеличить синтетикой
                (защита от «выдумывания» сотен копий из пары строк).

    Возвращает (items, targets, report), report[class] = (было, стало).
    """
    if method not in METHODS:
        raise ValueError(f"method должен быть из {METHODS}")
    rng = rng if rng is not None else np.random.default_rng(0)
    targets = np.asarray(targets, dtype=object)

    out_items: list[list[str]] = []
    out_targets: list[str] = []
    report: dict[str, tuple[int, int]] = {}

    for cls in sorted(set(targets.tolist())):
        idx = np.flatnonzero(targets == cls)
        rows = [items[i] for i in idx]
        before = len(rows)

        if before > target_size and majority == "undersample":
            keep = rng.choice(before, size=target_size, replace=False)
            rows = [rows[i] for i in keep]
        elif before < target_size and method != "none":
            n_new = target_size - before
            if max_factor is not None:
                n_new = min(n_new, int((max_factor - 1) * before))
            if method == "oversample":
                rows = rows + oversample_random(rows, n_new, rng)
            else:
                rows = rows + mutate_samples(rows, n_new, rng, k_neighbors, mix_rate)

        out_items.extend(rows)
        out_targets.extend([cls] * len(rows))
        report[cls] = (before, len(rows))

    return out_items, np.asarray(out_targets, dtype=object), report


def demo() -> None:
    """Показывает выравнивание на groundtruth (задача распознавания, без searching)."""
    from for_predict_strategy import (
        ACTION_PREFIX,
        ALL_MATCHES,
        build_transactions,
        drop_excluded_actions,
        load_groundtruth,
    )

    df = drop_excluded_actions(load_groundtruth(ALL_MATCHES))
    transactions, labels = build_transactions(df)
    items = [[x for x in row if not x.startswith(ACTION_PREFIX)] for row in transactions]
    target_size = median_class_size(labels)
    rng = np.random.default_rng(42)

    print("До:", dict(Counter(labels)), f"target_size={target_size}")
    for method in ("oversample", "mutate"):
        aug_items, aug_targets, report = balance_classes(
            items, labels, target_size, method=method, rng=rng
        )
        print(f"\n{method}: {report}")
    print("\nПримеры синтетических kickingG (mutate):")
    kick = [it for it, lab in zip(items, labels) if lab == "kickingG"]
    for row in mutate_samples(kick, 3, rng):
        print("  ", sorted(row))


if __name__ == "__main__":
    demo()
