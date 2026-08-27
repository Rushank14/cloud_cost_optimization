import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments for the DAG
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# The absolute path to the project root for local execution
PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/opt/airflow/project")
VENV_PYTHON = f"{PROJECT_ROOT}/venv/bin/python"
DBT_BIN = f"{PROJECT_ROOT}/venv/bin/dbt"

with DAG(
    'cloud_cost_optimization_pipeline',
    default_args=default_args,
    description='A daily pipeline to analyze warehouse query logs and generate cost optimization recommendations.',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['cost_optimization', 'daily'],
) as dag:

    # 1. Ingestion / Mock Data Generation
    # In a real environment, this might be a BigQueryToGCSOperator or similar.
    generate_mock_data = BashOperator(
        task_id='generate_mock_data',
        bash_command=f'cd {PROJECT_ROOT} && {VENV_PYTHON} -m src.mock_data.generator',
    )

    load_to_warehouse = BashOperator(
        task_id='load_to_warehouse',
        bash_command=f'cd {PROJECT_ROOT} && {VENV_PYTHON} -m src.ingest.loader',
    )

    # 2. Transformation (dbt)
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f'cd {PROJECT_ROOT}/dbt_project && {DBT_BIN} run --profiles-dir .',
    )
    
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=f'cd {PROJECT_ROOT}/dbt_project && {DBT_BIN} test --profiles-dir .',
    )

    # 3. Business Logic (Heuristics) & Reporting
    # We execute the report generator which runs the heuristics engine under the hood.
    run_heuristics_and_report = BashOperator(
        task_id='run_heuristics_and_report',
        bash_command=f'cd {PROJECT_ROOT} && {VENV_PYTHON} -m src.report.generator',
    )

    # Define DAG Dependencies
    generate_mock_data >> load_to_warehouse >> dbt_run >> dbt_test >> run_heuristics_and_report
