cat > kubeflow/README.md <<'EOF'
# Kubeflow Pipelines - Iris ML Pipeline

## 프로젝트 개요

Kubeflow Pipelines(KFP)를 활용하여 머신러닝 모델의 학습,
평가 및 품질 검증 과정을 자동화한 MLOps 실습 프로젝트입니다.

Iris 데이터셋과 RandomForest를 사용하여
v1부터 v3까지 단계적으로 파이프라인을 개선했습니다.

## 기술 스택

- Kubernetes
- Kubeflow Pipelines 2.16.1
- Python / scikit-learn
- Jupyter Notebook
- MinIO (Artifact Storage)

## 파이프라인 구성

### v1 - 기본 학습 파이프라인
- Iris 데이터셋 로드
- RandomForest 모델 학습
- Accuracy 평가
- 단일 Component 구성

### v2 - 학습 및 평가 분리
- 학습과 평가를 독립된 Component로 분리
- Model 및 Dataset Artifact 생성
- MinIO 기반 Artifact 저장 및 전달
- Component 간 데이터 의존성 구성

### v3 - 모델 평가 및 품질 검증
- Stratified 5-Fold Cross Validation
- Accuracy, F1-score, Precision, Recall 평가
- KFP Metrics 및 Confusion Matrix 기록
- Quality Gate를 통한 모델 품질 기준 검사
- 학습, 평가, 품질 검증을 3개 Component로 구성

## 파이프라인 구조

train_model_v3
    |
    |-- RandomForest 학습
    |-- 5-Fold 교차검증
    |-- Model / Dataset Artifact 저장
    |
    v
evaluate_model_v3
    |
    |-- Accuracy / F1-score
    |-- Precision / Recall
    |-- Confusion Matrix
    |
    v
quality_gate
    |
    |-- 테스트 Accuracy 기준 검사
    |-- CV 평균 Accuracy 기준 검사
    |
    v
최종 모델 품질 검증 결과

## 파일 구성

| 파일 | 설명 |
|---|---|
| iris_training_v3.ipynb | v1~v3 전체 실습 Notebook |
| iris-training-pipeline.yaml | v1 파이프라인 |
| iris-train-evaluate-pipeline.yaml | v2 파이프라인 |
| iris-validated-pipeline.yaml | v3 파이프라인 |

## 실습 결과

- v1: 기본 학습 파이프라인 실행 성공
- v2: 학습 및 평가 분리, Artifact 전달 검증
- v3: 교차검증, 다중 평가 지표, Quality Gate 구현 및 컴파일

v3의 최종 실행 상태와 성능 수치는 KFP Run에서 별도 검증합니다.

## 향후 개선 계획

- MLflow Experiment Tracking 연동
- 모델 하이퍼파라미터 튜닝
- Model Registry 연동
- KServe를 활용한 모델 서빙 자동화
EOF
