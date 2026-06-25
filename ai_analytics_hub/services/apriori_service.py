

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ai_analytics_hub.core.exceptions import DependencyNotInstalledError
from ai_analytics_hub.domain.models import Upload
from ai_analytics_hub.services.dataset_service import load_dataframe

if TYPE_CHECKING:
    import pandas as pd


def run_apriori_analysis(
    *,
    upload: Upload,
    min_support: float,
    min_confidence: float,
    min_lift: float,
    max_len: int,
) -> dict:
    """
    Run Apriori association rule mining on a previously uploaded CSV dataset.

    Args:
        upload:         The Upload record pointing to the stored CSV file.
        min_support:    Minimum support threshold (0.0 – 1.0).
        min_confidence: Minimum confidence threshold for association rules.
        min_lift:       Minimum lift value for association rules.
        max_len:        Maximum itemset length to consider.

    Returns:
        A dict containing:
          - transaction_count: number of valid rows parsed
          - frequent_itemsets: list of {itemsets, support} dicts
          - association_rules:  list of {antecedents, consequents, support,
                                         confidence, lift} dicts

    Raises:
        DependencyNotInstalledError: if pandas or mlxtend are not installed.
        ValueError: if the dataset contains no valid transactions.
    """
    try:
        import pandas as pd
        from mlxtend.frequent_patterns import apriori, association_rules
        from mlxtend.preprocessing import TransactionEncoder
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Apriori dependencies are not installed. Run 'pip install -e .[analytics]'."
        ) from error

    dataframe = load_dataframe(upload)
    transactions = _extract_transactions(dataframe)
    if not transactions:
        raise ValueError("The uploaded CSV does not contain any non-empty transactions.")

    encoder = TransactionEncoder()
    matrix = encoder.fit(transactions).transform(transactions)
    transaction_frame = pd.DataFrame(matrix, columns=encoder.columns_)

    frequent_itemsets = apriori(
        transaction_frame,
        min_support=min_support,
        use_colnames=True,
        max_len=max_len,
    )

    # Return early when no itemsets meet the minimum support threshold.
    if frequent_itemsets.empty:
        return {
            "transaction_count": len(transactions),
            "frequent_itemsets": [],
            "association_rules": [],
        }

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )
    if not rules.empty:
        rules = rules[rules["lift"] >= min_lift]

    # Sort itemsets for deterministic, human-readable output.
    frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(
        lambda values: sorted(values)
    )
    itemsets_payload = frequent_itemsets.sort_values("support", ascending=False).to_dict(
        "records"
    )

    rules_payload = _build_rules_payload(rules)

    return {
        "transaction_count": len(transactions),
        "frequent_itemsets": [
            {
                "itemsets": record["itemsets"],
                "support": round(float(record["support"]), 4),
            }
            for record in itemsets_payload
        ],
        "association_rules": rules_payload,
    }


def _build_rules_payload(rules: "pd.DataFrame") -> list[dict]:
    """
    Convert the association rules DataFrame into a list of serializable dicts.

    Args:
        rules: The filtered DataFrame returned by mlxtend's association_rules().

    Returns:
        A list of rule dicts sorted by lift (descending) then confidence (descending).
    """
    if rules.empty:
        return []

    rules = rules.sort_values(["lift", "confidence"], ascending=False)
    payload = []
    for record in rules.to_dict("records"):
        payload.append(
            {
                "antecedents": sorted(record["antecedents"]),
                "consequents": sorted(record["consequents"]),
                "support": round(float(record["support"]), 4),
                "confidence": round(float(record["confidence"]), 4),
                "lift": round(float(record["lift"]), 4),
            }
        )
    return payload


def _extract_transactions(dataframe: "pd.DataFrame") -> list[list[str]]:
    """
    Convert each row of a DataFrame into a list of string items.

    Single-column CSVs are treated as delimited item lists (comma, semicolon, or pipe).
    Multi-column CSVs treat each non-null cell value as an individual item.

    Args:
        dataframe: The raw DataFrame loaded from the uploaded CSV.

    Returns:
        A list of non-empty transactions (each transaction is a list of strings).
    """
    if dataframe.empty:
        return []

    transactions: list[list[str]] = []
    is_single_column = len(dataframe.columns) == 1

    for row in dataframe.itertuples(index=False):
        items = _normalize_row(list(row), is_single_column)
        if items:
            transactions.append(items)

    return transactions


def _normalize_row(values: Iterable[object], single_column: bool) -> list[str]:
    """
    Clean and normalize raw row values into a deduplicated list of item strings.

    Args:
        values:        Iterable of cell values from a single DataFrame row.
        single_column: True when the dataset has exactly one column, meaning
                       cell values may be delimited strings rather than atoms.

    Returns:
        A deduplicated list of non-empty string items (order-preserving).
    """
    try:
        import pandas as pd
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Apriori dependencies are not installed. Run 'pip install -e .[analytics]'."
        ) from error

    cleaned: list[str] = []
    for value in values:
        # Skip null / NaN values safely.
        try:
            if pd.isna(value):
                continue
        except (TypeError, ValueError):
            pass

        raw = str(value).strip()
        if not raw:
            continue

        if single_column and any(sep in raw for sep in (",", ";", "|")):
            cleaned.extend(_split_delimited_tokens(raw))
        else:
            cleaned.append(raw)

    # Use dict.fromkeys to deduplicate while preserving insertion order.
    return list(dict.fromkeys(cleaned))


def _split_delimited_tokens(value: str) -> list[str]:
    """
    Split a single cell value by comma, semicolon, or pipe delimiters.

    Args:
        value: A raw cell string that may contain multiple delimiters.

    Returns:
        A list of stripped, non-empty token strings.
    """
    for separator in (";", "|"):
        value = value.replace(separator, ",")
    return [token.strip() for token in value.split(",") if token.strip()]
