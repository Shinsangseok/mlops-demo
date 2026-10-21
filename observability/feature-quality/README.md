# Feature Quality & Drift Monitoring

## 1. 프로젝트 개요

Python으로 **데이터 품질 검사(Data Quality)** 와 **PSI(Population Stability Index) 기반 데이터 드리프트 탐지**를 구현하고, 결과를 **Prometheus / Grafana**에서 확인하는 MLOps 실습 프로젝트입니다.

이 저장소에는 데이터 생성 스크립트, 품질/드리프트 분석 코드, 메트릭 Exporter, Kubernetes 수집 설정, Grafana 대시보드 JSON을 보관합니다. **Feast 0.49.0 실습 환경과는 별도로 동작**하며, `feast monitor` 명령에 의존하지 않습니다.

## 2. 기술 스택 및 검증 환경

| 구분 | 구성 |
|---|---|
| 언어/라이브러리 | Python 3.9.25, pandas, NumPy, PyArrow |
| 데이터 저장 형식 | Parquet |
| 클러스터 | Kubernetes v1.37.0, 3노드, Calico |
| 모니터링 | Prometheus Operator, ServiceMonitor, Grafana |
| Grafana 대시보드 내보내기 | Grafana v13.2.4, Dashboard v2 JSON |
| 별도 학습 환경 | Feast 0.49.0 (본 모니터링 로직과 직접 연동하지 않음) |

> 실습 데이터는 합성 데이터입니다. 실제 운영 데이터의 특성이나 모델 정확도를 대표하지 않습니다.

## 3. 전체 흐름

```text
Baseline 데이터 (3,500행) ─┐
                         ├─> 합쳐진 Parquet 데이터 (7,000행)
Current 데이터 (3,500행) ─┘                │
                                        ├─> Python 품질 검사 ──> quality_report.json
                                        └─> Python PSI 분석 ──> drift_report.json
                                                                     │
                                      두 JSON 리포트를 읽는 Python Metrics Exporter (:9102)
                                                                     │
                                             Kubernetes Service + EndpointSlice
                                                                     │
                                             ServiceMonitor (release=monitor)
                                                                     │
                                                      Prometheus
                                                                     │
                                                 Grafana Dashboard
```

Prometheus는 Exporter의 `/metrics`를 주기적으로 읽습니다. **Exporter는 저장된 JSON 결과를 노출할 뿐, 품질 검사와 PSI 분석을 자동 재실행하지는 않습니다.**

## 4. 프로젝트 파일

```text
observability/feature-quality/
├── .gitignore
├── README.md
├── requirements.txt
├── scripts/
│   ├── generate_data.py
│   ├── run_quality_checks.py
│   ├── compare_drift.py
│   └── metrics_exporter.py
├── k8s/
│   └── metrics-monitoring.yaml
└── grafana/
    └── feature-quality-dashboard.json
```

실행 중 생성되는 `data/` 및 `reports/` 디렉터리는 `.gitignore`로 추적하지 않습니다.

## 5. 데이터 생성 및 재현

**다음 명령어는 `observability/feature-quality/` 디렉터리에서 실행합니다.**

```bash
python3 -m pip install -r requirements.txt

# 기준 데이터 3,500행 생성 후 별도 백업
python3 scripts/generate_data.py --phase baseline
cp data/customer_features.parquet data/baseline_customer_features.parquet

# 비교 데이터 3,500행을 기준 데이터에 추가
python3 scripts/generate_data.py --phase current
```

`--phase baseline`은 `data/customer_features.parquet`을 덮어쓰고, `--phase current`는 해당 파일에 데이터를 추가합니다. **`current`를 반복 실행하면 행이 누적될 수 있으므로**, 재실행할 때는 기준 데이터 백업을 복원하거나 위 순서를 처음부터 다시 실행하세요.

## 6. 데이터 품질 검사

```bash
python3 scripts/run_quality_checks.py
cat reports/quality_report.json
```

검사 항목: 결측치, `(customer_id, event_timestamp)` 중복, 음수 구매 횟수, 음수 평균 주문 금액, 음수 세션 시간, 고객 나이 범위(18~100).

| 결과 항목 | 실제 실습 결과 |
|---|---:|
| 검사 행 수 | 7,000 |
| `avg_order_value` 결측치 | 140 |
| 음수 `session_duration_sec` | 105 |
| 범위 밖 `customer_age` | 70 |
| 고객·시각 중복 | 0 |
| `passed` | `false` |

`passed=false`는 **품질 오류를 의도대로 찾아냈다는 뜻**입니다. 이 스크립트는 품질 검사에 실패하면 **종료 코드 1**을 반환합니다. 자동화 파이프라인에서는 이 종료 코드를 처리해야 합니다.

## 7. PSI 기반 데이터 드리프트 탐지

```bash
python3 scripts/compare_drift.py
cat reports/drift_report.json
```

판정 기준은 **PSI < 0.10: OK**, **0.10 ≤ PSI < 0.25: WARNING**, **PSI ≥ 0.25: DRIFT**입니다. 이는 실습용 임계값이며, 운영에서는 피처별 특성에 맞게 검증해야 합니다.

| 피처 | PSI | 상태 |
|---|---:|---|
| `purchase_count_7d` | 0.0000 | OK |
| `avg_order_value` | 3.6845 | DRIFT |
| `session_duration_sec` | 0.0071 | OK |
| `customer_age` | 0.0030 | OK |

평균 주문 금액은 약 **75.07 → 150.13**으로 증가했습니다. `has_drift=true`가 기록되며, 드리프트가 감지되면 스크립트가 **종료 코드 2**를 반환합니다.

> **품질 오류와 드리프트는 다른 검사입니다.** 일부 세션 시간·고객 나이에 비정상값이 있어도 분포 전체의 PSI는 낮게 나올 수 있습니다. 현재 생성 코드에서는 기준/비교 단계에서 같은 난수 시드를 사용해 일부 피처 분포가 같아질 수 있습니다.

## 8. Prometheus Metrics Exporter

Exporter는 JSON 보고서 두 개를 읽어 Prometheus 텍스트 메트릭을 반환합니다.

```bash
# 로컬 개발 환경에서 실행 (기존 포트 사용 여부 확인)
METRICS_HOST=127.0.0.1 METRICS_PORT=9102 python3 scripts/metrics_exporter.py

# 다른 터미널에서 확인
curl http://127.0.0.1:9102/metrics
```

| 메트릭 | 의미 |
|---|---|
| `feature_quality_pass` | 품질 검사 통과 여부(1/0) |
| `feature_quality_null_count{feature="..."}` | 피처별 결측치 수 |
| `feature_quality_negative_session_duration` | 음수 세션 시간 개수 |
| `feature_quality_age_out_of_range` | 나이 범위 오류 개수 |
| `feature_drift_psi{feature="..."}` | 피처별 PSI |
| `feature_drift_detected` | 한 피처 이상에서 DRIFT 검출 여부(1/0) |

## 9. Kubernetes와 Prometheus 연동

실습 환경에서 Exporter는 **`172.16.0.200:9102`**로 접근 가능하도록 실행했고, Kubernetes Pod의 HTTP 요청이 성공했습니다.

`k8s/metrics-monitoring.yaml`은 `monitoring` 네임스페이스에 **Service, 수동 EndpointSlice, ServiceMonitor**를 생성합니다. ServiceMonitor에는 현재 Prometheus 선택 조건에 맞춘 **`release: monitor`** 라벨이 포함되어 있습니다.

```bash
# 실제 클러스터와 Namespace, Exporter 주소를 먼저 확인
kubectl apply --dry-run=server -f k8s/metrics-monitoring.yaml
kubectl apply -f k8s/metrics-monitoring.yaml

kubectl get svc,endpointslices,servicemonitors -n monitoring | grep feature-quality
```

`172.16.0.200`은 개인 실습망 주소이므로 다른 클러스터에 적용할 때 EndpointSlice 주소와 Exporter 바인딩 주소를 변경해야 합니다. Exporter 포트는 필요한 내부 네트워크 범위에서만 접근하도록 제한하세요.

Prometheus 확인용 PromQL:

```promql
up{job="feature-quality-exporter"}
feature_drift_detected{job="feature-quality-exporter"}
feature_drift_psi{job="feature-quality-exporter"}
```

실제로 Prometheus API에서 `instance="172.16.0.200:9102"`, `job="feature-quality-exporter"`, `feature_drift_detected=1`이 조회됐습니다. `up=1`은 수집 Target 상태를 별도로 확인하는 용도입니다.

## 10. Grafana 대시보드

대시보드 제목: **Feature Quality & Drift Monitoring**

| 패널 | 시각화 | 실습 결과 |
|---|---|---|
| Data Quality Status | Stat | FAIL |
| Data Drift Status | Stat | DRIFT |
| PSI by Feature | Bar gauge | `avg_order_value=3.6845` |
| Null Count by Feature | Bar gauge | `avg_order_value=140` |

PSI 색상 기준: **0.10 미만 녹색**, **0.10~0.25 미만 노란색**, **0.25 이상 빨간색**. 결측치 패널은 **0건 녹색**, **1건 이상 빨간색**입니다.

Grafana UI에서 내보낸 파일은 `grafana/feature-quality-dashboard.json`입니다. **Grafana v13.2.4의 Dashboard v2 형식**으로 내보냈으므로, 다른 Grafana 버전으로 가져올 때는 호환성과 Prometheus 데이터 소스 매핑을 확인하세요.

## 11. 확인된 검증 범위

| 항목 | 검증 결과 |
|---|---|
| 기준/비교 데이터 생성 | 성공 (3,500 + 3,500행) |
| 품질 오류 검출 | 성공 (`passed=false`, 의도된 결과) |
| PSI 드리프트 검출 | 성공 (`has_drift=true`, 의도된 결과) |
| Exporter HTTP `/metrics` | 성공 |
| Kubernetes Pod → Exporter | 성공 |
| Prometheus `feature_drift_detected` 조회 | 성공 |
| Grafana 4개 패널 구성 및 JSON 내보내기 | 성공 |

이는 **실습에 설정한 이상 탐지 시나리오가 실행되었음**을 뜻하며, 자동 반복 검사나 Alertmanager 알림까지 구축됐다는 뜻은 아닙니다.

## 12. 한계 및 다음 개선

- Airflow 또는 Kubernetes CronJob으로 품질 검사와 PSI 계산 주기적 실행
- CI에서 의도적인 실패 종료 코드(품질 1, 드리프트 2)를 구별하는 자동 테스트
- PrometheusRule / Alertmanager 알림 및 재검사 시각 메트릭 추가
- 기준/현재 데이터의 난수 시드와 시나리오를 분리해 테스트 범위 확대
- Grafana Dashboard 프로비저닝 및 이식성 검증
- Feast Feature Store와의 실제 피처 수집 연계(현재는 미연동)

## 13. 공개 저장소 주의사항

GitHub에 Push하기 전에 Grafana JSON에 포함된 내부 UID·작성자 메타데이터, Kubernetes YAML에 포함된 실습용 사설 IP와 기타 환경 정보를 검토하세요. 비밀번호, 인증 토큰, 개인키, kubeconfig 및 실제 운영 데이터를 커밋하지 마세요.
