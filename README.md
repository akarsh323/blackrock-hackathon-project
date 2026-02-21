# 🏆 Micro Savings — BlackRock Hackathon Project

A FastAPI microservice that helps users grow their spare change into retirement savings. Every transaction is rounded up
to the nearest ₹100, and the difference (the *remanent*) is invested automatically — either through NPS or an Index
Fund — with full Q/P/K period rule support.

---

## 🚀 Getting Started

### Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Run the Service

```bash
docker compose up -d micro_savings
```

### Swagger UI

```
http://localhost:5477/docs
```

---

## 📡 API Overview

All endpoints are prefixed with `/blackrock/challenge/v1`.

| Method | Endpoint                  | Description                                          |
|--------|---------------------------|------------------------------------------------------|
| `GET`  | `/health`                 | Service health check                                 |
| `GET`  | `/performance`            | Live server metrics (uptime, memory, threads)        |
| `POST` | `/transactions:parse`     | Step 1 — Enrich transactions with ceiling & remanent |
| `POST` | `/transactions:validator` | Step 2 — Remove invalid transactions                 |
| `POST` | `/transactions:filter`    | Step 3 — Apply Q/P/K period rules                    |
| `POST` | `/returns:nps`            | Calculate NPS retirement corpus                      |
| `POST` | `/returns:index`          | Calculate Index Fund retirement corpus               |

### Pipeline

```
Raw Transactions
      ↓
  [Parse]      ceil(amount/100)*100 → ceiling; ceiling - amount → remanent
      ↓
  [Validate]   remove negatives, duplicates, amounts ≥ ₹5,00,000
      ↓
  [Filter]     apply Q (override), P (bonus), K (reporting windows)
      ↓
  [Returns]    compound interest + inflation adjustment per K period
```

### Period Rules

| Rule  | Behaviour                                                                                                            |
|-------|----------------------------------------------------------------------------------------------------------------------|
| **Q** | Hard override — replaces remanent with a fixed value. When multiple Q periods overlap, the latest start date wins.   |
| **P** | Stacking bonus — all matching P periods sum their extras on top of remanent (applied after Q).                       |
| **K** | Reporting window — transactions outside all K windows are invalid; one transaction can belong to multiple K periods. |

### Return Rates

| Scheme     | Annual Rate | Tax Benefit               |
|------------|-------------|---------------------------|
| NPS        | 7.11%       | ✅ Section 80CCD deduction |
| Index Fund | 14.49%      | ❌ None                    |

Investment horizon: `max(60 - age, 5)` years

---

## 🗂 Project Structure

```
.
├── Dockerfile
├── compose.yml
├── pyproject.toml
├── poetry.lock
└── service/
    ├── __init__.py
    ├── micro_savings/
    │   ├── __init__.py
    │   └── app/
    │       ├── __init__.py
    │       ├── api/
    │       │   ├── application.py        # FastAPI app factory
    │       │   ├── lifespan.py           # Startup / shutdown hooks
    │       │   └── endpoints/
    │       │       ├── router.py         # Master router
    │       │       ├── filter/           # POST /transactions:filter
    │       │       ├── monitoring/       # GET  /health
    │       │       ├── parse/            # POST /transactions:parse
    │       │       ├── performance/      # GET  /performance
    │       │       ├── returns/          # POST /returns:nps  /returns:index
    │       │       └── validation/       # POST /transactions:validator
    │       ├── models/
    │       │   ├── filter.py             # FilterRequest / FilterResult
    │       │   ├── periods.py            # QPeriod, PPeriod, KPeriod
    │       │   ├── returns.py            # ReturnRequest / ReturnResponse
    │       │   ├── transaction.py        # Raw → Parsed → Validated → Filtered
    │       │   └── validator.py          # ValidatorRequest
    │       ├── transaction_engine/
    │       │   ├── ceiling_processor/    # Parse: ceiling + remanent logic
    │       │   ├── filter_processor/     # Q / P / K rule application
    │       │   ├── returns_processor/    # Compound interest + inflation
    │       │   ├── tax_processor/        # Indian income tax + NPS benefit
    │       │   └── validation_processor/ # Validation rules
    │       └── utils/
    │           ├── date_utils.py         # Period overlap / date helpers
    │           ├── logging.py            # Loguru setup
    │           └── settings.py           # Env-based config (rates, port, etc.)
    └── tests/
        └── micro_savings/
            ├── performance_utils.py      # Uptime / memory / thread helpers
            ├── test_filter.py            # Q / P / K rule tests
            ├── test_parse.py             # Ceiling & remanent tests
            ├── test_returns.py           # FV, inflation, NPS/Index tests
            ├── test_tax.py               # Tax slab & NPS benefit tests
            └── test_validator.py         # Validation rule tests
```

---

## ⚙️ Configuration

Settings are loaded from environment variables (with defaults):

| Variable         | Default   | Description                   |
|------------------|-----------|-------------------------------|
| `host`           | `0.0.0.0` | Bind address                  |
| `port`           | `5477`    | HTTP port                     |
| `workers`        | `1`       | Uvicorn workers               |
| `NPS_RATE`       | `0.0711`  | NPS annual return rate        |
| `INDEX_RATE`     | `0.1449`  | Index Fund annual return rate |
| `RETIREMENT_AGE` | `60`      | Target retirement age         |

---

## 🛠 Development

Run tests inside the container:

```bash
docker compose run --rm micro_savings pytest service/tests/
```

Or locally with Poetry:

```bash
poetry install --with dev,micro_savings
pytest service/tests/
```