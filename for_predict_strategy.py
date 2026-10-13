# -*- coding: utf-8 -*-
"""Прогноз action по groundtruth-данным симулятора RoboCup (ассоциативные правила)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.preprocessing import TransactionEncoder
from sklearn.metrics import accuracy_score, f1_score

ACTION_LABELS = ["dribbling", "fight", "kickingG", "passing"]
EXCLUDED_ACTIONS = {"searching"}

DATA_DIR = Path(__file__).resolve().parent / "data_processed" / "data_processed"

ALL_MATCHES = [
    ("Gliders2016", "HELIOS2016"),
    ("Oxsy", "HfutEngine2017"),
    ("Oxsy", "HELIOS2016"),
    ("HfutEngine2017", "Gliders2016"),
    ("HfutEngine2017", "HELIOS2017"),
    ("Oxsy", "Gliders2016"),
    ("Gliders2016", "HELIOS2017"),
    ("HELIOS2016", "HELIOS2017"),
]

ACTION_PREFIX = "action="
MIN_SUPPORT = 0.003
MIN_CONFIDENCE = 0.75
HOLDOUT_FRACTION = 0.25
BALANCE_RANDOM_STATE = 42


def calc_stats(df: pd.DataFrame, field: str) -> dict[str, int]:
    return df[field].value_counts().to_dict()


def match_filename(team_a: str, team_b: str) -> str:
    return f"{team_a}-{team_b}-action-groundtruth-v3.csv"


def load_groundtruth(matches: list[tuple[str, str]]) -> pd.DataFrame:
    frames = []
    for team_a, team_b in matches:
        path = DATA_DIR / match_filename(team_a, team_b)
        if not path.exists():
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        df["match"] = f"{team_a}-{team_b}"
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def drop_excluded_actions(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["action"].isin(EXCLUDED_ACTIONS)].reset_index(drop=True)


def split_dev_holdout(df: pd.DataFrame, holdout_fraction: float = HOLDOUT_FRACTION) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Последние holdout_fraction строк каждого матча — только финальный тест.

    Обучение и кросс-валидация идут по оставшимся 75%. Порог Apriori
    после просмотра holdout не меняется.
    """
    dev_parts = []
    holdout_parts = []
    for match_name, match_df in df.groupby("match", sort=False):
        match_df = match_df.sort_values("time").reset_index(drop=True)
        n_holdout = max(1, int(round(len(match_df) * holdout_fraction)))
        n_holdout = min(n_holdout, len(match_df) - 1)
        split_at = len(match_df) - n_holdout
        dev_parts.append(match_df.iloc[:split_at])
        holdout_parts.append(match_df.iloc[split_at:])
        print(
            f"  {match_name}: dev={split_at}  holdout={n_holdout}",
            flush=True,
        )
    return (
        pd.concat(dev_parts, ignore_index=True),
        pd.concat(holdout_parts, ignore_index=True),
    )


def balance_classes(
    df: pd.DataFrame,
    random_state: int = BALANCE_RANDOM_STATE,
) -> pd.DataFrame:
    """Undersample до одинакового числа строк на каждый класс.

    Строки не меняются, новые не создаются. Берётся n = min(count по классам).
    """
    counts = df["action"].value_counts()
    n_per_class = int(counts.min())
    parts = [
        class_df.sample(n=n_per_class, random_state=random_state)
        for _, class_df in df.groupby("action", sort=False)
    ]
    balanced = pd.concat(parts, ignore_index=True)
    balanced = balanced.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return balanced


def _safe_int(value) -> int:
    if pd.isna(value):
        return 0
    return int(float(value))


def _bin_near(value) -> str:
    near = _safe_int(value)
    if near == 0:
        return "near=0"
    if near == 1:
        return "near=1"
    if near == 2:
        return "near=2"
    return "near=3+"


def _bin_mid(value) -> str:
    mid = _safe_int(value)
    if mid == 0:
        return "mid=0"
    if mid <= 3:
        return "mid=1-3"
    return "mid=4+"


def row_to_items(row: pd.Series) -> list[str]:
    """Преобразует строку groundtruth в набор категориальных item'ов."""
    side = row.get("sideWithBall")
    if pd.isna(side) or str(side).strip() == "":
        side_item = "side=none"
        ball_item = "ball=no"
    else:
        side_item = f"side={str(side).strip()}"
        ball_item = "ball=yes"

    pass_pair = row.get("passPair")
    pass_item = "pass=yes" if pd.notna(pass_pair) and str(pass_pair).strip() else "pass=no"

    goal = row.get("goalIsNearest")
    goal_item = "goal=yes" if goal is True or str(goal).lower() == "true" else "goal=no"

    action = str(row["action"])
    items = [
        ball_item,
        side_item,
        _bin_near(row.get("lenOfNearest")),
        _bin_mid(row.get("lenOfMiddleDist")),
        pass_item,
        goal_item,
        f"{ACTION_PREFIX}{action}",
    ]
    return items


def build_transactions(df: pd.DataFrame) -> tuple[list[list[str]], list[str]]:
    transactions = []
    labels = []
    for _, row in df.iterrows():
        items = row_to_items(row)
        labels.append(row["action"])
        transactions.append(items)
    return transactions, labels


def transactions_to_onehot(transactions: list[list[str]]) -> pd.DataFrame:
    encoder = TransactionEncoder()
    matrix = encoder.fit_transform(transactions)
    return pd.DataFrame(matrix, columns=encoder.columns_)


def mine_action_rules(
    onehot: pd.DataFrame,
    min_support: float = MIN_SUPPORT,
    min_confidence: float = MIN_CONFIDENCE,
    max_len: int | None = None,
) -> pd.DataFrame:
    frequent = apriori(onehot, min_support=min_support, use_colnames=True, max_len=max_len)
    if frequent.empty:
        return pd.DataFrame()

    support_by_itemset = {
        frozenset(itemset): support
        for itemset, support in zip(frequent["itemsets"], frequent["support"])
    }

    rules = []
    for itemset, support in support_by_itemset.items():
        actions = [item for item in itemset if item.startswith(ACTION_PREFIX)]
        if len(actions) != 1:
            continue

        action_item = actions[0]
        antecedents = frozenset(itemset - {action_item})
        if not antecedents:
            continue

        antecedent_support = support_by_itemset.get(antecedents)
        if antecedent_support is None or antecedent_support == 0:
            continue

        confidence = support / antecedent_support
        if confidence < min_confidence:
            continue

        consequent_support = support_by_itemset.get(frozenset({action_item}), 0.0)
        lift = confidence / consequent_support if consequent_support else 0.0
        rules.append(
            {
                "antecedents": antecedents,
                "consequents": frozenset({action_item}),
                "support": support,
                "confidence": confidence,
                "lift": lift,
            }
        )

    if not rules:
        return pd.DataFrame()

    action_rules = pd.DataFrame(rules)
    action_rules = action_rules.sort_values(
        ["confidence", "lift", "support"],
        ascending=False,
    )
    return action_rules.reset_index(drop=True)


def build_rule_list(rules: pd.DataFrame) -> list[tuple[frozenset, str, float, float, int]]:
    rule_list = []
    for _, rule in rules.iterrows():
        antecedents = rule["antecedents"]
        action = next(iter(rule["consequents"])).replace(ACTION_PREFIX, "")
        rule_list.append(
            (
                antecedents,
                action,
                float(rule["confidence"]),
                float(rule["lift"]),
                len(antecedents),
            )
        )
    rule_list.sort(key=lambda x: (x[4], x[2], x[3]), reverse=True)
    return rule_list


def predict_action(
    situation_items: list[str],
    rule_list: list[tuple[frozenset, str, float, float, int]],
    default_action: str,
) -> tuple[str, bool]:
    """CBA: первое подходящее правило с максимальной confidence."""
    situation = frozenset(
        item for item in situation_items if not item.startswith(ACTION_PREFIX)
    )

    for antecedents, action, _, _, _ in rule_list:
        if antecedents.issubset(situation):
            return action, True

    return default_action, False


def evaluate(
    transactions: list[list[str]],
    labels: list[str],
    rule_list: list[tuple[frozenset, str, float, float, int]],
    default_action: str,
) -> dict:
    predictions = []
    covered = 0

    for items, true_action in zip(transactions, labels):
        situation = [item for item in items if not item.startswith(ACTION_PREFIX)]
        pred, was_covered = predict_action(situation, rule_list, default_action)
        predictions.append(pred)
        covered += int(was_covered)

    total = len(labels)
    f1_per_class = f1_score(
        labels,
        predictions,
        labels=ACTION_LABELS,
        average=None,
        zero_division=0.0,
    )
    per_class = {}
    for cls, f1_value in zip(ACTION_LABELS, f1_per_class):
        cls_total = sum(1 for t in labels if t == cls)
        cls_correct = sum(1 for p, t in zip(predictions, labels) if t == cls and p == cls)
        cls_pred = sum(1 for p in predictions if p == cls)
        precision = cls_correct / cls_pred if cls_pred else 0.0
        recall = cls_correct / cls_total if cls_total else 0.0
        per_class[cls] = {
            "support": cls_total,
            "precision": precision,
            "recall": recall,
            "f1": float(f1_value),
        }

    recalls = [v["recall"] for v in per_class.values()]
    return {
        "accuracy": accuracy_score(labels, predictions) if total else 0.0,
        "balanced_accuracy": sum(recalls) / len(recalls) if recalls else 0.0,
        "f1_macro": f1_score(labels, predictions, labels=ACTION_LABELS, average="macro", zero_division=0.0),
        "f1_weighted": f1_score(
            labels, predictions, labels=ACTION_LABELS, average="weighted", zero_division=0.0
        ),
        "coverage": covered / total if total else 0.0,
        "per_class": per_class,
        "confusion": pd.crosstab(
            pd.Series(labels, name="true"),
            pd.Series(predictions, name="pred"),
            dropna=False,
        ),
    }


def fit_predict_fold(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    train_transactions, _ = build_transactions(train_df)
    # Правила майнятся на исходном train; в оценке — равное число строк на класс.
    test_balanced = balance_classes(test_df)
    test_transactions, test_labels = build_transactions(test_balanced)
    rules = mine_action_rules(transactions_to_onehot(train_transactions))
    rule_list = build_rule_list(rules)
    default_action = train_df["action"].value_counts().idxmax()
    metrics = evaluate(test_transactions, test_labels, rule_list, default_action)
    metrics["n_rules"] = len(rules)
    metrics["n_test"] = len(test_balanced)
    metrics["n_test_raw"] = len(test_df)
    metrics["n_per_class"] = metrics["n_test"] // len(test_balanced["action"].unique())
    return metrics


def leave_one_match_out(df: pd.DataFrame) -> pd.DataFrame:
    """Кросс-валидация: каждый матч один раз в тесте, остальные в обучении."""
    rows = []
    matches = df["match"].unique().tolist()
    for test_match in matches:
        train_df = df[df["match"] != test_match]
        test_df = df[df["match"] == test_match]
        print(
            f"\nFold test={test_match}  train_rows={len(train_df)}  "
            f"test_raw={len(test_df)}  test_raw_stats={calc_stats(test_df, 'action')}",
            flush=True,
        )
        metrics = fit_predict_fold(train_df, test_df)
        print(
            f"  balanced test: {metrics['n_test']} rows "
            f"({metrics['n_per_class']} per class)",
            flush=True,
        )
        fold = {
            "fold": test_match,
            "n_test": metrics["n_test"],
            "n_rules": metrics["n_rules"],
            "accuracy": metrics["accuracy"],
            "f1_macro": metrics["f1_macro"],
            "f1_weighted": metrics["f1_weighted"],
        }
        for cls, stats in metrics["per_class"].items():
            fold[f"f1_{cls}"] = stats["f1"]
        rows.append(fold)
        print(
            f"  acc={metrics['accuracy']:.4f}  "
            f"f1_macro={metrics['f1_macro']:.4f}  "
            f"f1_weighted={metrics['f1_weighted']:.4f}  "
            f"rules={metrics['n_rules']}",
            flush=True,
        )
    return pd.DataFrame(rows)


def print_metrics(split_name: str, metrics: dict) -> None:
    print(f"\n{split_name} metrics:")
    print(f"  accuracy:          {metrics['accuracy']:.4f}")
    print(f"  balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  f1_macro:          {metrics['f1_macro']:.4f}")
    print(f"  f1_weighted:       {metrics['f1_weighted']:.4f}")
    print(f"  rule coverage:     {metrics['coverage']:.4f}")
    print("  per-class precision / recall / f1:")
    for cls, stats in metrics["per_class"].items():
        print(
            f"    {cls:10s}  n={stats['support']:5d}  "
            f"precision={stats['precision']:.3f}  "
            f"recall={stats['recall']:.3f}  "
            f"f1={stats['f1']:.3f}"
        )
    print("  confusion matrix:")
    print(metrics["confusion"].to_string())


def print_cv_summary(cv_df: pd.DataFrame) -> None:
    metric_cols = [col for col in cv_df.columns if col not in {"fold", "n_test", "n_rules"}]
    print("\nLeave-one-match-out summary (mean +/- std):")
    for col in metric_cols:
        values = cv_df[col].to_numpy(dtype=float)
        print(f"  {col:16s}  {values.mean():.4f} +/- {values.std(ddof=1):.4f}")
    print("\nPer-fold table:")
    print(cv_df.round(4).to_string(index=False))


def print_rules(rules: pd.DataFrame, top_n: int = 15) -> None:
    print(f"\nTop-{top_n} action rules:")
    for _, rule in rules.head(top_n).iterrows():
        ant = ", ".join(sorted(rule["antecedents"]))
        cons = ", ".join(sorted(rule["consequents"]))
        print(
            f"  {ant} -> {cons}  "
            f"(conf={rule['confidence']:.3f}, lift={rule['lift']:.2f}, sup={rule['support']:.3f})"
        )


def main() -> None:
    full_df = load_groundtruth(ALL_MATCHES)
    print("All rows:", len(full_df), "matches:", full_df["match"].unique().tolist())
    print("All action:", calc_stats(full_df, "action"))
    full_df = drop_excluded_actions(full_df)
    print("Excluded actions:", sorted(EXCLUDED_ACTIONS))
    print("Rows after drop:", len(full_df), "action:", calc_stats(full_df, "action"))

    print(f"\n=== Split: {1 - HOLDOUT_FRACTION:.0%} dev / {HOLDOUT_FRACTION:.0%} final holdout ===")
    print("Holdout = last 25% of each match by time; not used in training or CV.")
    dev_df, holdout_df = split_dev_holdout(full_df)
    print("Dev rows:", len(dev_df), "Holdout rows:", len(holdout_df))
    print("Dev action:", calc_stats(dev_df, "action"))
    print("Holdout action:", calc_stats(holdout_df, "action"))

    print("\n=== Leave-one-match-out on DEV (rules from original rows, eval balanced) ===")
    cv_df = leave_one_match_out(dev_df)
    print_cv_summary(cv_df)

    print("\n=== Final holdout (single evaluation, no retuning) ===")
    print(
        f"Hyperparameters frozen: min_support={MIN_SUPPORT}, min_confidence={MIN_CONFIDENCE}",
        flush=True,
    )
    holdout_balanced = balance_classes(holdout_df)
    print("Holdout original:", calc_stats(holdout_df, "action"))
    print("Holdout balanced:", calc_stats(holdout_balanced, "action"))

    # Майнинг на исходном DEV — тот же набор строк и та же схема правил.
    dev_transactions, _ = build_transactions(dev_df)
    holdout_transactions, holdout_labels = build_transactions(holdout_balanced)
    rules = mine_action_rules(transactions_to_onehot(dev_transactions))
    rule_list = build_rule_list(rules)
    default_action = dev_df["action"].value_counts().idxmax()
    print(f"Mined rules on full DEV: {len(rules)} (default action: {default_action})", flush=True)
    print_rules(rules)
    print_metrics(
        "Final holdout 25% (balanced classes)",
        evaluate(holdout_transactions, holdout_labels, rule_list, default_action),
    )


if __name__ == "__main__":
    main()
