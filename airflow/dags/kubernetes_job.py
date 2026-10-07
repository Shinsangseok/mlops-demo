from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator


with DAG(
    dag_id="mlops_kubernetes_test",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mlops", "kubernetes"],
) as dag:

    run_kubernetes_job = KubernetesPodOperator(
        task_id="run_kubernetes_job",
        name="mlops-airflow-test",
        namespace="default",
        image="python:3.12-slim",
        cmds=["python", "-c"],
        arguments=[
            """
import socket
print("=== Airflow KubernetesPodOperator Test ===")
print("Pod hostname:", socket.gethostname())
print("Airflow -> Kubernetes integration SUCCESS")
"""
        ],
        in_cluster=False,
        config_file="/home/airflow/.kube/config",
        get_logs=True,
        on_finish_action="delete_pod",
        startup_timeout_seconds=120,
    )
