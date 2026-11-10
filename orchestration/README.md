# Pipeline Orchestration

Week 4 workstream. Add Apache Airflow DAGs after individual pipeline steps are executable.

Planned task sequence:
1. Generate or ingest synthetic/raw pings.
2. Load raw data into Snowflake.
3. Run spatial processing.
4. Execute dbt transformations and tests.
5. Refresh dashboard-ready aggregate outputs.

Make tasks idempotent, parameterized and observable. Configure retries and failure notifications. Keep Airflow connections and secrets out of DAG source code.
