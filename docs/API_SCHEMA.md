# API Schema Reference

Human-readable schema documentation for the Chaos QA Swarm target API. Machine-readable exports live in [`schemas/api_openapi.json`](../schemas/api_openapi.json) and [`schemas/endpoints/`](../schemas/endpoints/).

Regenerate after model changes:

```bash
python scripts/export_schemas.py
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness probe; returns `{"status": "ok"}` |
| `POST` | `/api/items/summary` | Compute `mean` or `sum` over numeric items |
| `POST` | `/api/users/lookup` | Return the first user matching filter criteria |
| `POST` | `/api/report/aggregate` | Flatten nested groups and return aggregate metadata |
| `POST` | `/api/prorate` | Distribute a total across weighted parts |
| `POST` | `/api/loyalty/score` | Compute loyalty score from account tenure and base points |

---

## `POST /api/items/summary`

Compute aggregate statistics over a list of items.

### Request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `items` | `array` | yes | List of `{name, value}` objects |
| `items[].name` | `string` | yes | Item label |
| `items[].value` | `number` | yes | Numeric value |
| `operation` | `string` | yes | Enum: `"mean"` or `"sum"` |
| `adjustment_mode` | `string` | no | Enum: `"standard"` (default) or `"normalized"` |

### Example request

```json
{
  "items": [
    {"name": "alpha", "value": 10.0},
    {"name": "beta", "value": 20.0},
    {"name": "gamma", "value": 30.0}
  ],
  "operation": "mean"
}
```

### Example response (`200`)

```json
{
  "result": 20.0,
  "count": 3
}
```

---

## `POST /api/users/lookup`

Return the first user whose `filter.field` equals `filter.value`.

### Request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `users` | `array` | yes | List of arbitrary user objects |
| `filter` | `object` | yes | Filter criteria |
| `filter.field` | `string` | yes | Key to read on each user object |
| `filter.value` | `any` | yes | Expected value for the filter field |

### Example request

```json
{
  "users": [
    {"id": 1, "role": "admin", "name": "Ada"},
    {"id": 2, "role": "viewer", "name": "Grace"}
  ],
  "filter": {"field": "role", "value": "admin"}
}
```

### Example response (`200`)

```json
{
  "user": {"id": 1, "role": "admin", "name": "Ada"}
}
```

---

## `POST /api/report/aggregate`

Flatten nested `groups` and return the metric label, total scalar count, and first scalar value.

### Request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `groups` | `array` | yes | Nested lists of scalar values |
| `metric` | `string` | yes | Metric label echoed in the response |

### Example request

```json
{
  "groups": [[1, 2], [3, 4, 5]],
  "metric": "throughput"
}
```

### Example response (`200`)

```json
{
  "metric": "throughput",
  "count": 5,
  "first_value": 1
}
```

---

## `POST /api/prorate`

Distribute `total` across `parts` proportional to each part's `weight`.

### Request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `total` | `number` | yes | Total amount to distribute |
| `parts` | `array` | yes | Weighted portions |
| `parts[].label` | `string` | yes | Part identifier |
| `parts[].weight` | `number` | yes | Relative weight |
| `denominator` | `number` | no | Explicit divisor; defaults to sum of weights when omitted |
| `strict_zero_weights` | `boolean` | no | Strict validation when all part weights are zero (default: `false`) |

### Example request

```json
{
  "total": 100.0,
  "parts": [
    {"label": "team_a", "weight": 1.0},
    {"label": "team_b", "weight": 3.0}
  ],
  "denominator": 4.0
}
```

### Example response (`200`)

```json
{
  "allocations": [
    {"label": "team_a", "amount": 25.0},
    {"label": "team_b", "amount": 75.0}
  ],
  "denominator_used": 4.0
}
```

---

## `POST /api/loyalty/score`

Compute a loyalty score from account type, tenure, and base points.

### Request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `account_type` | `string` | yes | Account classification label |
| `months_active` | `integer` | yes | Number of months the account has been active |
| `base_points` | `integer` | yes | Base loyalty points before tenure adjustment |

### Example request

```json
{
  "account_type": "standard",
  "months_active": 12,
  "base_points": 100
}
```

### Example response (`200`)

```json
{
  "score": 100.0,
  "account_type": "standard"
}
```

---

## Machine-readable exports

- Full OpenAPI 3 document: [`schemas/api_openapi.json`](../schemas/api_openapi.json)
- Per-endpoint request schemas with valid examples:
  - [`schemas/endpoints/items_summary.json`](../schemas/endpoints/items_summary.json)
  - [`schemas/endpoints/users_lookup.json`](../schemas/endpoints/users_lookup.json)
  - [`schemas/endpoints/report_aggregate.json`](../schemas/endpoints/report_aggregate.json)
  - [`schemas/endpoints/prorate.json`](../schemas/endpoints/prorate.json)
  - [`schemas/endpoints/loyalty_score.json`](../schemas/endpoints/loyalty_score.json)
