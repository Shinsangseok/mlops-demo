#!/usr/bin/env bash
set -euo pipefail

NS="mlops-netcheck"
SERVER="netcheck-server"
CLIENT="netcheck-client"

echo "=== 1. Pod Scheduling ==="
kubectl get pods -n "$NS" -o wide

SERVER_NODE=$(kubectl get pod "$SERVER" -n "$NS" -o jsonpath='{.spec.nodeName}')
CLIENT_NODE=$(kubectl get pod "$CLIENT" -n "$NS" -o jsonpath='{.spec.nodeName}')

if [[ "$SERVER_NODE" != "node01" || "$CLIENT_NODE" != "node02" ]]; then
    echo "FAIL: Expected server=node01, client=node02"
    exit 1
fi

echo "PASS: Cross-node placement"

echo "=== 2. Pod IP Communication ==="
SERVER_IP=$(kubectl get pod "$SERVER" -n "$NS" -o jsonpath='{.status.podIP}')

RESULT=$(kubectl exec -n "$NS" "$CLIENT" -- \
    wget -qO- -T 5 "http://${SERVER_IP}:8080/")

if [[ "$RESULT" != "hello from node01" ]]; then
    echo "FAIL: Pod-to-Pod HTTP"
    exit 1
fi

echo "PASS: Pod-to-Pod HTTP"

echo "=== 3. Kubernetes Service DNS ==="
kubectl exec -n "$NS" "$CLIENT" -- \
    nslookup "${SERVER}.${NS}.svc.cluster.local"

echo "PASS: Service DNS"

echo "=== 4. ClusterIP Communication ==="
RESULT=$(kubectl exec -n "$NS" "$CLIENT" -- \
    wget -qO- -T 5 \
    "http://${SERVER}.${NS}.svc.cluster.local:8080/")

if [[ "$RESULT" != "hello from node01" ]]; then
    echo "FAIL: ClusterIP HTTP"
    exit 1
fi

echo "PASS: ClusterIP HTTP"
echo "=== ALL NETWORK CHECKS PASSED ==="
