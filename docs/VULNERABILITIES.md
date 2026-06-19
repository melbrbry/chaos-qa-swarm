# Vulnerability Catalog

**Maintainer / evaluation ground truth only.** The White-Box Chaos Agent in Phase 3 reads `target_app/` source at runtime — not this file.

Each trap requires reading source code and reasoning about compound branches. Black-box schema fuzzing is unlikely to discover them because triggers depend on specific field combinations, not random type violations.

---

## `POST /api/loyalty/score`

| Field | Value |
| --- | --- |
| **File** | `target_app/routes/loyalty.py` |
| **Line** | Division on the `legacy` branch |
| **Bug type** | `ZeroDivisionError` (HTTP 500) |
| **Trigger** | `account_type == "legacy"` **and** `months_active == 0` |
| **Example payload** | `{"account_type": "legacy", "months_active": 0, "base_points": 100}` |
| **Why not black-box** | Must pair the exact string `"legacy"` with integer `0`. Random fuzzing almost never hits both. |

---

## `POST /api/items/summary`

| Field | Value |
| --- | --- |
| **File** | `target_app/routes/items.py` |
| **Line** | Mean calculation on empty list in normalized mode |
| **Bug type** | `ZeroDivisionError` (HTTP 500) |
| **Trigger** | `operation == "mean"` **and** `adjustment_mode == "normalized"` **and** `items == []` |
| **Example payload** | `{"items": [], "operation": "mean", "adjustment_mode": "normalized"}` |
| **Why not black-box** | Default `adjustment_mode` is `"standard"`, which handles empty mean gracefully. Fuzzer must discover the non-default enum value combined with an empty array. |

---

## `POST /api/users/lookup`

| Field | Value |
| --- | --- |
| **File** | `target_app/routes/users.py` |
| **Line** | Dynamic key access in filter loop; fallback to `users[0]` |
| **Bug type** | `KeyError` or `IndexError` (HTTP 500) |
| **Trigger (KeyError)** | `filter.field` names a key absent from user dicts, e.g. `"department"` |
| **Trigger (IndexError)** | No user matches filter **and** `users` is empty |
| **Example payloads** | `{"users": [{"id": 1, "role": "admin"}], "filter": {"field": "department", "value": "eng"}}` or `{"users": [], "filter": {"field": "role", "value": "admin"}}` |
| **Why not black-box** | Requires understanding dynamic `user[body.filter.field]` access and the no-match fallback path. Schema allows any filter field string without hinting which keys exist on user objects. |

---

## `POST /api/report/aggregate`

| Field | Value |
| --- | --- |
| **File** | `target_app/routes/report.py` |
| **Line** | `first_value = body.groups[0][0]` |
| **Bug type** | Logic error (HTTP 200, wrong data) or `IndexError` when first group is empty |
| **Trigger (logic)** | First non-empty value in flattened order differs from `groups[0][0]` when the first group is empty, e.g. `groups: [[], [7, 8]]` — correct `first_value` is `7`, code crashes on `groups[0][0]` |
| **Trigger (crash)** | `groups: [[]]` or `groups: []` — `IndexError` on `groups[0][0]` |
| **Why not black-box** | Happy-path tests pass with well-formed groups where `groups[0][0]` coincidentally equals `flat[0]`. Agent must read code to see `first_value` uses the wrong source. |

---

## `POST /api/prorate`

| Field | Value |
| --- | --- |
| **File** | `target_app/routes/prorate.py` |
| **Line** | Allocation division when denominator remains zero |
| **Bug type** | `ZeroDivisionError` (HTTP 500) |
| **Trigger** | `denominator == 0` **and** `sum(weights) == 0` **and** `strict_zero_weights == true` |
| **Example payload** | `{"total": 100.0, "parts": [{"label": "a", "weight": 0.0}], "denominator": 0.0, "strict_zero_weights": true}` |
| **Why not black-box** | Bare `denominator: 0` no longer crashes (falls back to weight sum). Fuzzer must enable the obscure `strict_zero_weights` flag with zero-weight parts. |
