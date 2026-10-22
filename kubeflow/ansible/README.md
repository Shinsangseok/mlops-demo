# Ansible Kubernetes Infrastructure Lab

## 1. 프로젝트 개요

Ansible을 활용한 Kubernetes 인프라 구성 관리 및
클러스터 상태 자동 검증 실습입니다.

Kubernetes, Calico, Istio의 상태를 확인하고
Worker Node 간 네트워크 통신을 검증합니다.

## 2. 실습 환경

| 항목 | 환경 |
|---|---|
| OS | Rocky Linux 9.8 |
| Kubernetes | v1.37.0 |
| Control Plane | 1대 |
| Worker Node | 2대 |
| CNI | Calico |
| 자동화 | Ansible, Bash |
| 신규 구축 목표 | Kubernetes v1.36.x |

## 3. 프로젝트 구조

- ansible.cfg: Ansible 기본 설정
- inventory/: 관리 대상 노드 정의
- group_vars/: Kubernetes 및 Calico 버전 변수
- playbooks/: Ansible 사전 검증
- scripts/verify_cluster.sh: 클러스터 상태 점검
- scripts/verify_pod_network.sh: 네트워크 통신 검증
- k8s/network-smoke.yaml: 네트워크 테스트용 리소스

## 4. Ansible Preflight

```bash
ansible-playbook \
  -i inventory/hosts.ini.example \
  playbooks/preflight.yaml
```

검증 결과: PASS, changed=0

## 5. Kubernetes 상태 검증

```bash
./scripts/verify_cluster.sh
```

확인 항목:
- Node Ready
- Calico DaemonSet
- Istio Namespace
- Kubeflow Namespace

## 6. Cross-Node 네트워크 테스트

테스트 전용 namespace 생성:

```bash
kubectl create namespace mlops-netcheck
kubectl label namespace mlops-netcheck istio-injection=disabled
```

테스트 리소스 배포:

```bash
kubectl apply -f k8s/network-smoke.yaml
kubectl wait -n mlops-netcheck \
  --for=condition=Ready pod --all --timeout=120s
```

자동 검증:

```bash
./scripts/verify_pod_network.sh
```

검증 완료 후 테스트 리소스 정리:

```bash
kubectl delete namespace mlops-netcheck
```

## 7. 실제 검증 결과

| 검증 항목 | 결과 |
|---|---|
| Ansible Preflight | PASS |
| Kubernetes Node Ready | 3/3 |
| Calico DaemonSet | 3/3 |
| Cross-Node Pod HTTP | PASS |
| Kubernetes Service DNS | PASS |
| ClusterIP HTTP | PASS |
| Kubeflow | 현재 클러스터 미설치 |

## 8. 향후 개선 계획

- Kubernetes 신규 설치 Playbook 구현
- Calico 설치 자동화
- Kubeflow 설치 및 Pipeline 검증
- Jenkins CI 연동
- 테스트 결과 자동 리포트 생성

## 주의사항

현재 v1.37.0 클러스터는 기존 실습 환경입니다.
v1.36.x 설치 목표와 구분하여 관리합니다.

Ansible Preflight는 조회 및 설정 검증 용도이며,
실제 클러스터 설치를 수행하지 않습니다.
