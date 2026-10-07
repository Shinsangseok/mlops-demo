from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

with DAG(
    dag_id="mlops_mlflow_tracking",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mlops", "mlflow", "kubernetes"],
) as dag:

    log_mlflow_run = KubernetesPodOperator(
        task_id="log_mlflow_run",
        name="mlops-mlflow-run",
        namespace="default",
        image="ghcr.io/mlflow/mlflow:v3.16.1-full",

        cmds=["python", "-c"],

        arguments=[
            """

import os
import socket
import mlflow

tracking_uri = os.environ["MLFLOW_TRACKING_URI"]

mlflow.set_tracking_uri(tracking_uri)
mlflow.set_experiment("mlops-demo")

with mlflow.start_run(run_name="airflow-kubernetes-integration"):

    mlflow.log_param("orchestrator", "airflow")
    mlflow.log_param("runtime", "kubernetes")

    mlflow.log_metric("integration_score", 1.0)

    mlflow.set_tag(
        "pod_hostname",
        socket.gethostname()
    )

    print("Airflow -> Kubernetes -> MLflow SUCCESS")
"""

        ],

        env_vars={
            "MLFLOW_TRACKING_URI": "http://172.16.0.200:5000",
            "GIT_PYTHON_REFRESH": "quiet",
        },

        in_cluster=False,
        config_file="/home/airflow/.kube/config",

        get_logs=True,
        on_finish_action="delete_pod",
        startup_timeout_seconds=120,
    )
