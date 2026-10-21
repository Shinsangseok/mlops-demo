#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. Kubernetes Context ==="
kubectl config current-context

echo
echo "=== 2. Kubernetes Nodes ==="
kubectl get nodes -o wide 

echo 
echo "=== 3. Node Ready Check ==="
kubectl wait \
  --for=condition=Ready \
  nodes --all \
  --timeout=30s

echo
echo "=== 4. CNI Network Check ==="
kubectl get daemonsets -A | \
  grep -Ei 'calico|cilium|flannel|weave' || \
  echo "No matching CNI DaemonSet found"

echo
echo "=== 5. Kubeflow Namespace Check ==="
kubectl get namespaces | \
  grep -Ei 'kubeflow|istio' || \
  echo "No matching Kubeflow/Istio namespace found"

echo 
echo "=== 6. Kubeflow Pod Status ==="
if kubectl get namespace kubeflow > /dev/null 2>&1; then 
  kubectl get pods -n kubeflow
else
  echo "Kubeflow namespace not found"
fi

echo 
echo "=== Verification Script Finished ==="
