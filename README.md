# MLOps Practice

MLOps와 CI/CD 관련 기술을 직접 실습하고,
각 도구가 어떤 역할을 하고 서로 어떻게 연결되는지 이해하기 위한 학습용 저장소입니다.

완성된 서비스를 만드는 것보다는 Jenkins, Kubernetes, Nexus, SonarQube,
Trivy, Airflow, MLflow 등을 직접 구성하고 연결해보는 것을 목표로 합니다.

## 실습 흐름

```text
GitHub
  ↓
Jenkins
  ↓
Kubernetes Agent
  ↓
Nexus
  ↓
SonarQube / Trivy
  ↓
Airflow / MLflow
```

현재 GitHub의 코드를 Jenkins가 가져오고,
Kubernetes에 임시 Agent Pod를 생성하여 Pipeline 작업을 실행하도록 구성하고 있습니다.

## 각 도구의 역할

| 도구 | 역할 |
|---|---|
| GitHub | 실습 코드와 설정 파일 저장 |
| Jenkins | 빌드와 테스트 작업 실행 |
| Kubernetes | Jenkins와 작업용 Agent Pod 실행 |
| Nexus | Python 라이브러리 등 의존성 관리 |
| SonarQube | 코드 품질 분석 |
| Trivy | 이미지 및 라이브러리 취약점 검사 |
| Airflow | 작업 스케줄링 및 워크플로우 관리 |
| MLflow | 머신러닝 실험 및 모델 관리 |

## 현재 진행 상황

- [x] Jenkins Kubernetes 배포
- [x] Jenkins JCasC 설정
- [x] Jenkins Plugin 코드 관리
- [x] Kubernetes Dynamic Agent 구성
- [x] GitHub 연동
- [x] Nexus PyPI Proxy / Group 구성
- [x] Jenkins용 Nexus 읽기 계정 구성
- [x] Jenkins에서 Nexus를 통한 Python 패키지 설치 검증
- [x] SonarQube 연동
- [x] Trivy 연동
- [x] Airflow 연동
- [ ] MLflow 연동
- [ ] 전체 Pipeline 연결 및 검증

## 학습 목표

각 도구를 단순히 설치하는 것에서 끝내지 않고,
직접 설정하고 연결하면서 CI/CD와 MLOps의 전체 흐름을 이해하는 것이 목표입니다.

실습이 진행될 때마다 내용을 추가할 예정입니다.
