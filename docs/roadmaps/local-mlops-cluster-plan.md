# Local MLOps Cluster — Ansible · Kubernetes · Kubeflow 통합 구축 계획

> **상태: PLAN ONLY / NOT STARTED**
> 최종 수정 기준일: 2026-10-21
> 대상 GitHub 저장소: `Shinsangseok/mlops-demo`
> 계획서 권장 위치: `docs/roadmaps/local-mlops-cluster-plan.md`

## 0. 이번 프로젝트의 목적과 경계

**목적:** 새 VM 3대에 Ansible로 Kubernetes 클러스터를 재현 가능하게 구축한 뒤, 기존 `mlops-demo`의 Kubeflow Iris v3 파이프라인과 `observability/feature-quality`를 새 클러스터에서 실행하고 Prometheus/Grafana로 관측한다.

**별도 프로젝트:** AWS `datacenter-project`의 K3s/GKE 이전 작업과 혼합하지 않는다. 이 문서는 로컬 학습용 `mlops-demo`만 다룬다.

**이번 프로젝트에서 제외:** GitHub Actions, Argo CD, 기존 클러스터 재설치, 운영환경 대체, 전면적인 Full Kubeflow 선설치. Jenkins 연동은 선택적 후속 확장이다.

### 절대 변경 금지 대상

- **기존 로컬 클러스터:** Rocky Linux 9.8 / Kubernetes v1.37.0 / `172.16.0.101`(Control Plane), `.102`(node01), `.103`(node02). Prometheus, Grafana, Feast 등 기존 실습 자산 보존.
- **AWS `datacenter-project`:** EC2 K3s, RDS, PROD/DEV 워크로드와 설정은 본 실습에서 변경하지 않는다.
- 기존 환경에 `kubeadm init`, `kubeadm reset`, 재설치, Calico 교체, 정리 명령을 실행하지 않는다.

### 신규 클러스터 원칙

- 새로운 VM 3대 및 **기존과 충돌하지 않는 별도 네트워크/IP**를 사용한다. 이전에 언급한 `172.16.10.101~103`은 **예시일 뿐 미확정**이다.
- Control Plane 2 vCPU/4 GiB, Worker 2대 각 4 vCPU/8 GiB는 **초기 검토 사양**이다. 전체 Kubeflow는 리소스 추가가 필요할 수 있다.
- 목표 Kubernetes는 **v1.36.x**. 정확한 패치 버전, Calico, containerd, Kubeflow Pipelines, 설치 매니페스트 버전은 **호환성 검증 후 변수로 고정**한다.
- Kubeflow는 우선 **Pipelines Standalone**부터 검토한다. Istio, 인증, 스토리지 요구사항 및 기존 구성과의 중복 설치 가능성은 배포 전 검증한다.
- Ansible이 신규 VM 외 호스트에 설치 작업을 수행하지 않도록 inventory allowlist, 실행 대상 확인 및 preflight 실패 시 중단 장치를 마련한다.

## 1. 기존 코드 활용 지점

| 기존 자산 | 이 프로젝트에서의 역할 |
|---|---|
| `kubeflow/ansible/` (기존 `feat/kubeflow-ansible-lab` 작업) | Inventory/Preflight/Pod-network 검증 스크립트 재사용·확장 |
| `kubeflow/iris-validated-pipeline.yaml` | 새 KFP에서 Iris v3 ML Pipeline 재현·품질 게이트 검증 |
| `observability/feature-quality/scripts/` | 데이터 생성, 품질 검사, PSI 드리프트 탐지 재사용 |
| `observability/feature-quality/k8s/` | 신규 환경용 Exporter/ServiceMonitor 설정 분리 및 일반화 |
| `observability/feature-quality/grafana/` | Grafana 대시보드 재배포·패널 검증 |
| Jenkins/Airflow/MLflow | 기존 학습 자산으로 유지. 모두 동시에 설치하지 않음; 확장은 별도 결정 |

**주의:** 브랜치에만 존재하는 파일은 `main`에 있다고 가정하지 않는다. 작업 시작 시 PR 및 브랜치 상태를 조회한 뒤 실제 파일 존재 여부를 확인한다. 현재 클러스터 전용 IP가 하드코딩된 EndpointSlice/YAML은 그대로 신규 클러스터에 적용하지 않는다.

## 2. 목표 아키텍처

```text
GitHub mlops-demo (versioned IaC / pipelines / dashboard)
    |
    +--> Ansible (NEW-VM inventory ONLY)
    |      +--> OS/users/SSH/sysctl/containerd
    |      +--> Kubernetes kubeadm v1.36.x + Calico
    |      +--> cluster / pod-network / DNS validation
    |
    +--> NEW Kubernetes cluster (3 VMs; IP/OS to be confirmed)
           |
           +--> Kubeflow Pipelines Standalone
           |      +--> existing Iris v3 train -> evaluate -> quality_gate
           |      +--> future Feature Quality pipeline
           |
           +--> Data Quality / PSI drift (Python)
           |      +--> quality_report.json / drift_report.json
           |      +--> persisted shared report access (PVC or object storage)
           |
           +--> Exporter -> ServiceMonitor -> Prometheus -> Grafana

Existing local K8s 172.16.0.101~103: read-only reference; NO CHANGES.
AWS datacenter-project: out of scope; NO CHANGES.
```

## 3. 원래 8개 미션 — 상세 실행 게이트

### Mission 1 — 새 VM 3대 준비 (Phase 0~1)

- 실행 전: 하이퍼바이저/호스트 자원(물리 RAM·CPU·디스크), 네트워크, 기존 VM 구성, IP 충돌 확인.
- 신규 VM: Control Plane 1대 / Worker 2대. Rocky Linux 9.8 우선 검토하되 실제 OS 확정 후 문서 수정.
- 고정할 값: hostname, IP, NIC, CPU/RAM, OS, 디스크, 접근 계정, SSH 키.
- **완료 기준:** 신규 3대의 접속·주소·리소스·이름 확인; 기존 `.101~.103`와 중복 없음.
- **중단:** 신규 VM 자원 부족, IP 충돌, 기존 클러스터와 구분 불가.

### Mission 2 — `mlops-user` 생성 및 sudo (Phase 2)

- 신규 노드 3대에만 `mlops-user`를 생성하고, SSH 키 및 제한된 sudo 정책 구성.
- 키·암호·토큰을 Git에 올리지 않음. 사용자/권한 설정은 Ansible Role 또는 bootstrap 문서로 재현 가능하게 작성.
- **완료 기준:** 3대 모두 SSH 키 접속 및 필요한 sudo 명령 가능.

### Mission 3 — Inventory / hosts (Phase 2)

- `inventory/new-cluster/hosts.ini`와 `inventory/existing-lab/`를 분리. 실행 전 대상 주소·노드 역할 출력.
- OS `hosts` 파일과 Ansible inventory는 구분. DNS/hosts 변경은 신규 VM에 한정.
- **완료 기준:** `ansible-inventory --graph`, 연결 확인 시 정확히 신규 VM 3대만 선택.

### Mission 4 — `ansible.cfg` (Phase 2)

- 기본 inventory, remote_user, SSH 설정, privilege escalation, 로그 위치를 명시. `host_key_checking` 무분별한 전역 해제 금지.
- 설치용 Playbook은 explicit inventory 선택·allowlist 검증 후 실행하도록 설계.
- **완료 기준:** 구성 확인 + Ansible Ping 3/3 + 기존 VM 미포함 확인.

### Mission 5 — Kubernetes v1.36.x 자동 설치 (Phase 3)

- 변수화: K8s patch version, containerd version, Pod/Service CIDR, image repository, kubeadm 설정.
- OS 전제: 커널 모듈, sysctl, swap, 시간 동기화, 방화벽/포트, cgroup driver 등을 검증.
- 절차: 신규 Control Plane `kubeadm init` → 인증서/토큰 안전 전달 → 신규 Workers join. 민감한 join token은 Git 미저장.
- cluster-admin kubeconfig는 신규 환경용으로 별도 보관. 실행 전 `kubectl config current-context`와 API Server 주소를 출력·확인.
- **완료 기준:** `kubectl get nodes -o wide` 신규 노드 3/3 Ready; 핵심 시스템 Pod 정상. 설치 재실행·오류 재시도 안전성 확인.
- **중단:** 기존 API server 주소 발견, 설치 대상 오인, 불일치 버전/네트워크 CIDR.

### Mission 6 — Calico 자동 설치 및 Pod 네트워크 검증 (Phase 4)

- Kubernetes/Calico 호환 버전 확인 후 고정. Pod CIDR, iptables/nftables, MTU, NetworkPolicy 고려.
- Calico 상태, CoreDNS, Pod-to-Pod cross-node HTTP, DNS, ClusterIP, 외부 이미지 Pull 검증.
- 격리 테스트 namespace에서만 테스트 리소스 생성 후 정리.
- **완료 기준:** 노드 3/3 Ready, CNI 정상, DNS 및 Pod/Service 통신 PASS, 삭제 후 원상복귀.

### Mission 7 — Kubeflow 커널·호환성 사전 설정 (Phase 5)

- sysctl/모듈/containerd/cgroup, 디스크/스토리지 및 PV 동작, DNS/Ingress/TLS, CPU·RAM 여유 검증.
- Full Kubeflow가 아니라 Pipelines Standalone 요구사항을 먼저 판정. Istio/인증 중복 구성 위험 검토.
- **완료 기준:** 요구사항 체크리스트 PASS, 도입 방식 및 필요한 리소스 확정.
- **중단:** 가용 자원 부족, KFP/K8s 버전 미지원, Persistent Storage 부재.

### Mission 8 — Git 기반 Kubeflow 설치 소스 준비 (Phase 5)

- 공식 소스 및 설치 설명서 확인 후 **release tag/commit SHA** 고정; 무검증 `main` HEAD 설치 지양.
- 설치 매니페스트 구성·namespace·ServiceAccount·스토리지 의존성을 Git으로 검토. 실제 설치는 다음 Gate 이후 수행.
- **완료 기준:** 설치 소스 무결성, 선언형 설정, 롤백 계획 및 배포 승인 준비 완료.

## 4. 프로젝트 통합 확장 (8개 미션 이후)

### Phase 6 — KFP Standalone 설치 및 Iris v3 이식

- 설치 전: 컴포넌트별 메모리/CPU/PVC 요구사항 및 호환성 재점검.
- 기존 `kubeflow/iris-validated-pipeline.yaml` 실행: 학습 → 평가 → quality gate.
- Accuracy/F1/Precision/Recall, 모델·데이터 Artifact, Run 상태를 실제 실행 결과로 확인.
- **완료 기준:** KFP Pipeline 성공 실행, Artifact 접근, quality gate 결과 기록, 재실행 PASS.

### Phase 7 — Feature Quality & PSI 파이프라인화

- 기존 고객 feature 데이터는 Iris 모델 데이터와 **별도 워크플로**로 유지. 학습 레이블 없는 데이터이므로 무리하게 모델 학습과 연결하지 않음.
- Baseline/current 생성 → 품질 검사/PSI → 결과 Artifact 저장 → Exporter 노출.
- 현재 스크립트에서 품질 FAIL 시 exit 1, Drift 감지 시 exit 2 등 **탐지 결과와 파이프라인 장애를 구분**할 규칙 설계.
- exporter는 정적 JSON 읽기 방식이므로 새 리포트 갱신/공유·지속 저장(PVC/Object Storage), 메트릭 stale 처리, Job 주기 실행 여부를 명시.
- **완료 기준:** 정상/의도적 이상 시나리오 각각 재현; PSI `avg_order_value` DRIFT, 결측 140 등 기준 테스트 결과 확인.

### Phase 8 — Prometheus / Grafana 통합

- 새 클러스터 전용 Scrape 설정: ServiceMonitor/EndpointSlice 등 구성의 IP 하드코딩 제거 또는 환경 변수화.
- 새 환경에 맞는 Grafana 데이터 소스 설정과 Dashboard JSON Import 검증.
- 주요 패널: Data Quality Status, Data Drift Status, PSI by Feature, Null Count by Feature.
- **완료 기준:** 새 Exporter에서 Prometheus 수집 PASS 및 Grafana 4개 패널 표시 PASS.

### Phase 9 — 재현성 검증·문서화·PR

- Ansible Playbook lint/syntax/dry-run, idempotency, inventory 안전장치 검증.
- 테스트 증적: 노드, Calico, DNS/통신, KFP Run, 결과 Artifact, Prometheus, Grafana.
- Secret/토큰/개인정보/내부 kubeconfig가 Git에 올라가지 않는지 점검.
- 실행 가이드, 롤백·정리 절차, VM 비용·자원 사용량, 장애 사례를 README에 기록.
- 별도 작업 브랜치 PR 검토 후 사용자 판단에 따라 `main` 병합.

## 5. 세션별 진행 순서와 예상 시간

| 세션 | 수행 내용 | 예상 |
|---|---|---|
| 0 | Git/PR 상태, 기존 클러스터 분리, VM 플랫폼·리소스·주소 설계 (READ-ONLY) | 1~2h |
| 1 | 신규 VM 3대 생성 및 네트워크 검증 | 1~3h |
| 2 | mlops-user, SSH/sudo, Inventory, ansible.cfg | 1~2h |
| 3 | 신규 클러스터 Kubernetes v1.36.x 구성 | 2~4h |
| 4 | Calico + cross-node/DNS/Service 테스트 | 1~2h |
| 5 | Kubeflow 사전 요구사항 + Git 배포 소스 고정 | 1~2h |
| 6 | KFP Standalone + Iris v3 파이프라인 검증 | 2~4h |
| 7 | Feature Quality/PSI 실행·결과 저장·메트릭 연계 | 3~5h |
| 8 | 검증 리포트, 문서화, PR | 1~3h |

시간은 추정치이며 새 VM 이미지 다운로드, 자원 제약, Kubeflow 호환성에 따라 달라진다.

## 6. Phase 0 — 착수 준비 및 안전 점검 체크리스트

### 사전 확인 항목 (READ-ONLY)

1. `Shinsangseok/mlops-demo`의 최신 `main`, PR/브랜치 상태 및 `kubeflow/ansible`, `observability/feature-quality` 존재 여부. PR이 `main`에 병합됐다는 전제 금지.
2. 신규 VM을 생성할 가상화 플랫폼(VirtualBox/VMware/기타), 실제 호스트의 CPU·RAM·여유 디스크와 OS ISO.
3. 기존 VM의 네트워크 대역/NIC 구조, 새 가상 네트워크 후보, DHCP/IP 충돌 여부.
4. 신규 VM 3대의 후보 IP/hostname/리소스. 확정 전 inventory에 주소를 하드코딩하지 않음.
5. 기존 K8s `.101~.103`와 AWS K3s가 **작업 대상에서 제외**됐는지 확인.
6. `Kubernetes 1.36.x + containerd + Calico + KFP`의 설치/호환 버전 확정 필요 목록 작성.

### 첫 번째 세션 완료 기준

- 신규 VM에 손대기 전 **기존 클러스터 보호 체크 PASS**.
- VM 플랫폼, 리소스, 네트워크, 설치 대상·미대상 식별표 확정.
- 단계별 수행 명령과 rollback/stop gate 준비.
- 안전 점검 결과와 중단 조건을 문서화하고, Phase 1 진입 가능 여부를 판정.

## 7. 프로젝트 진행 기록 템플릿

업데이트할 때 아래 표의 상태를 `TODO / IN PROGRESS / PASS / HOLD` 중 하나로 변경하고 근거를 기록한다.

| 단계 | 현재 상태 | 근거/산출물 | 다음 작업 |
|---|---|---|---|
| 0. Read-only 설계 | TODO | — | 하이퍼바이저/용량/PR·네트워크 점검 |
| 1. 신규 VM 3대 | TODO | — | 생성·접속 검증 |
| 2. Ansible 준비 | TODO | — | mlops-user·SSH·Inventory |
| 3. Kubernetes 설치 | TODO | — | 버전 호환성·kubeadm 자동화 |
| 4. Calico 네트워크 | TODO | — | CNI·cross-node 검증 |
| 5. Kubeflow 준비 | TODO | — | 사전 요구사항·Git 버전 고정 |
| 6. Iris v3 Pipeline | TODO | — | KFP Run·Artifact 검증 |
| 7. Feature Quality | TODO | — | KFP·리포트 지속성 확보 |
| 8. Metrics/Grafana | TODO | — | ServiceMonitor·패널 검증 |
| 9. 최종 검증/PR | TODO | — | 증적·README·보안 점검 |

**문서 작성 시점 상태:** 설계 단계. 신규 VM 구축과 Kubernetes/Kubeflow 배포는 미착수이며, 각 단계의 진행 결과는 실제 검증 후 이 표에 갱신한다.
