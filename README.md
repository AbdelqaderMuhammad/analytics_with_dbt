Practice dataset: use a generic, well-known sample schema (e.g. the dbt community "Jaffle Shop" dataset, or any synthetic retail/orders schema) loaded into Snowflake. It is dataset-agnostic on purpose — the point is to run every task against one coherent set of business entities (customers, orders, payments, products) so marts and exposures have a real reason to exist, without tying the project to any specific employer's domain.

## 1. Beginner: Foundational Concepts and Setup

- **1.1 Understand dbt Core Concepts** — models, sources, seeds, tests, docs; ELT and where dbt sits in the Transform layer.
- **1.2 Set up dbt with Snowflake, including environment separation from day one**
    - Install dbt Core, configure `profiles.yml` (account, user, password, database, warehouse, schema).
    - Configure `dev` and `prod` targets.
    - **Create separate least-privilege Snowflake roles for dev and prod dbt users now** (moved up from the advanced section — cheap to set up early, expensive to retrofit).
- **1.3 Create and Run Basic dbt Models** — staging models, materializations (view vs. table), `dbt run`.
- **1.4 Define Sources and Seeds** — declare raw tables as sources (freshness checks, lineage); load static lookup tables via seeds.
- **1.5 Implement Basic Tests and Documentation**
    - Schema tests (`not_null`, `unique`, `accepted_values`, `relationships`), `dbt test`.
    - **Unit tests** — mock inputs and assert transformation logic on at least one non-trivial model (distinct from schema tests: this validates _logic_, not just output shape).
    - `schema.yml` docs; `dbt docs generate` / `dbt docs serve`.

## 2. Intermediate: Project Structure, Reusability, Advanced Features

- **2.1 Optimize Project Structure** — staging/intermediate/marts folders, `dbt_project.yml` config, shared staging database.
- **2.2 Master Jinja Templating** — variables, control structures, macros, effective use of `ref()`/`source()`.
- **2.3 Explore Advanced Materializations** — incremental models, ephemeral models, trade-offs.
- **2.4 Utilize dbt Packages**
    - `dbt-utils`, `dbt-date`, `dbt-snowflake-utils` (e.g. zero-copy clones for dev environments).
    - **`dbt-utils` `audit_helper`** — use it to diff a refactored model against its previous version whenever you change transformation logic, as a regression-safety habit for the rest of the project.
- **2.5 Advanced Testing and Data Quality**
    - Custom singular tests, source freshness checks.
- **2.6 Implement Snapshots** — SCD Type 2 tracking on at least one dimension.

## 3. Advanced: Performance, Governance, Orchestration

- **3.1 Performance Optimization** — warehouse sizing, clustering keys, query profile analysis, tags/hooks for resource management.
- **3.2 Data Governance and Security**
    - Dynamic data masking for sensitive columns.
    - **Model contracts** — enforce column names/types on the interface of at least one mart model.
    - **Model versioning** — practice deprecating and versioning a model's interface without breaking downstream consumers.
    - Permissions-as-code (e.g. Permifrost).
- **3.3 Custom Materializations and Advanced Hooks** — pre/post-hooks for grants, external tables.
- **3.4 Orchestration and CI/CD**
    - Integrate with Airflow/Dagster/Prefect for scheduling.
    - **Slim CI as its own task**: run `dbt build --select state:modified+` against a deferred prod manifest in a PR pipeline — this is the single most interview-relevant CI skill here, not a footnote under general CI/CD.
- **3.5 Monitoring, Alerting, Cost Management** — dbt artifacts (run_results, manifest) for logging; alert on test failures/long-running queries; track cost per credit/query.
- **3.6 Exposures and Semantic Layer**
    - **Exposures** — link at least one mart to a downstream consumer (a dashboard, report, or notebook) so it has a stated reason to exist, not just a table sitting unused.
    - dbt Semantic Layer / MetricFlow — define at least 2-3 metrics on top of your marts.
    - (Optional) dbt Mesh concepts for multi-project setups.

## What changed from the original draft

- Added: unit tests (1.5), `audit_helper` (2.4), model contracts + versioning (3.2), Slim CI as its own task (3.4), exposures (3.6).
- Moved: dev/prod role separation from advanced governance (3.2) up to initial setup (1.2).