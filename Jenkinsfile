pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: python
      image: python:3.12-slim
      command:
        - cat
      tty: true

    - name: sonar
      image: sonarsource/sonar-scanner-cli:5.0
      command:
        - cat
      tty: true

    - name: trivy
      image: aquasec/trivy:0.74.0
      command:
        - cat
      tty: true
'''
        }
    }

    stages {
        stage('Kubernetes Agent Test') {
            steps {
                container('python') {
                    sh 'echo "=== Kubernetes Jenkins Agent ==="'
                    sh 'hostname'
                    sh 'python --version'
                }
            }
        }

        stage('Nexus Dependency Test') {
            steps {
                container('python') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'nexus-pypi',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASSWORD'
                        )
                    ]) {
                        sh '''
                            set +x

                            cat > ~/.netrc <<NETRC
machine 172.16.0.200
login ${NEXUS_USER}
password ${NEXUS_PASSWORD}
NETRC

                            chmod 600 ~/.netrc

                            python -m pip install \
                              --index-url http://172.16.0.200:8081/repository/pypi-group/simple \
                              --trusted-host 172.16.0.200 \
                              -r summarizer/requirements.txt

                            rm -f ~/.netrc

                            python -c "import requests; print('requests version:', requests.__version__)"
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar') {
                    withCredentials([
                        string(
                            credentialsId: 'sonar-token',
                            variable: 'SONAR_TOKEN'
                        )
                    ]) {
                        sh '''
                            sonar-scanner \
                              -Dproject.settings=ci/sonar-project.properties \
                              -Dsonar.host.url=http://172.16.0.200:9000 \
                              -Dsonar.login=${SONAR_TOKEN}
                        '''
                    }
                }
            }
        }

        stage('Trivy Filesystem Scan') {
            steps {
                container('trivy') {
                    sh '''
                        trivy fs \
                          --scanners vuln,secret,misconfig \
                          --severity HIGH,CRITICAL \
                          --exit-code 0 \
                          --format template \
                          --template "@/contrib/html.tpl" \
                          --output trivy-report.html \
                          .
                    '''
                }

                publishHTML([
                    reportDir: '.',
                    reportFiles: 'trivy-report.html',
                    reportName: 'Trivy Security Report',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: false
                ])
            }
        }

        stage('Airflow MLflow Integration') {
            steps {
                container('python') {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'airflow-api',
                            usernameVariable: 'AIRFLOW_USER',
                            passwordVariable: 'AIRFLOW_PASSWORD'
                        )
                    ]) {
                        sh '''
                            set +x

                            python - << 'PY'
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AIRFLOW_URL = "http://172.16.0.200:8089"
DAG_ID = "mlops_mlflow_tracking"

def request_json(url, method="GET", body=None, token=None):
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Airflow API HTTP error: {exc.code}")
        print(error_body)
        sys.exit(1)
    except Exception as exc:
        print(f"Airflow API request failed: {exc}")
        sys.exit(1)

print("=== Airflow authentication ===")

auth = request_json(
    f"{AIRFLOW_URL}/auth/token",
    method="POST",
    body={
        "username": os.environ["AIRFLOW_USER"],
        "password": os.environ["AIRFLOW_PASSWORD"],
    },
)

token = auth.get("access_token")

if not token:
    print("Failed to obtain Airflow access token")
    sys.exit(1)

print("Airflow authentication SUCCESS")

print("=== Trigger Airflow DAG ===")

dag_run = request_json(
    f"{AIRFLOW_URL}/api/v2/dags/{DAG_ID}/dagRuns",
    method="POST",
    body={
        "logical_date": None,
        "conf": {
            "triggered_by": "jenkins",
        },
    },
    token=token,
)


run_id = dag_run.get("dag_run_id")

if not run_id:
    print("Airflow did not return dag_run_id")
    sys.exit(1)

print(f"DAG triggered: {run_id}")

print("=== Wait for Airflow DAG ===")

encoded_run_id = urllib.parse.quote(run_id, safe="")

status_url = (
    f"{AIRFLOW_URL}/api/v2/dags/"
    f"{DAG_ID}/dagRuns/{encoded_run_id}"
)

timeout_seconds = 180
poll_seconds = 5
started = time.time()

while True:
    run = request_json(
        status_url,
        token=token,
    )

    state = run.get("state")
    print(f"Airflow DAG state: {state}")

    if state == "success":
        print("Airflow -> Kubernetes -> MLflow SUCCESS")
        break

    if state in {"failed", "canceled"}:
        print(f"Airflow DAG failed with state: {state}")
        sys.exit(1)

    if time.time() - started > timeout_seconds:
        print("Timed out waiting for Airflow DAG")
        sys.exit(1)

    time.sleep(poll_seconds)
PY
                        '''
                    }
                }
            }
        }


    }
}
