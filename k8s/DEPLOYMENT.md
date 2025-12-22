# GenAI User Mgmt Backend Kubernetes Deployment

This folder contains Kubernetes manifests for deploying the backend and MongoDB on a Hostinger VPS Kubernetes cluster.

## Resources

- Namespace: `namespace.yaml`
- ConfigMap: `configmap.yaml`
- Secret: `secret.yaml`
- Deployment: `deployment.yaml`
- Service: `service.yaml`
- Horizontal Pod Autoscaler: `hpa.yaml`
- MongoDB PVC, Deployment, Service: `mongo.yaml`
- ChromaDB PVC, Deployment, Service: `chromadb.yaml`

## Prerequisites

- Docker image for the backend pushed to a registry accessible from the cluster.
- `kubectl` configured to point to the Hostinger cluster.
- Storage class available for the MongoDB PVC.

## Environment And Database Configuration

Backend expects:

- `MONGODB_URL`
- `DB_NAME`
- `GROQ_API_KEY`
- `CHROMA_HOST_ADDR` and `CHROMA_HOST_PORT` for ChromaDB

The manifests provide:

- `configmap.yaml` for non‑secret values.
- `secret.yaml` for `MONGODB_URL` and `GROQ_API_KEY`.
- `mongo.yaml` for an in‑cluster MongoDB with persistent storage.
- `chromadb.yaml` for an in‑cluster ChromaDB vector store with persistent storage.

Set the image in `deployment.yaml` to your registry image name and tag.

If you use an external MongoDB, update `MONGODB_URL` in `secret.yaml` accordingly and you can skip applying `mongo.yaml`.

## Apply Manifests With Dry Run Validation

From the `k8s` directory:

```bash
kubectl apply -f namespace.yaml --dry-run=client
kubectl apply -f configmap.yaml --dry-run=client
kubectl apply -f secret.yaml --dry-run=client
kubectl apply -f mongo.yaml --dry-run=client
kubectl apply -f chromadb.yaml --dry-run=client
kubectl apply -f deployment.yaml --dry-run=client
kubectl apply -f service.yaml --dry-run=client
kubectl apply -f hpa.yaml --dry-run=client
```

If all validations pass:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f mongo.yaml
kubectl apply -f chromadb.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
```

## CI/CD Integration Points

Typical steps in a pipeline:

1. Build and push image:

```bash
docker build -t your-registry/genai-backend:${GIT_SHA} .
docker push your-registry/genai-backend:${GIT_SHA}
```

2. Update the image in `deployment.yaml` or use:

```bash
kubectl set image deployment/genai-backend-deployment \
  genai-backend=your-registry/genai-backend:${GIT_SHA} \
  -n genai-backend
```

3. Validate and apply manifests as shown above.

## Verification And Health Checks

1. Check pods:

```bash
kubectl get pods -n genai-backend
```

2. Check services:

```bash
kubectl get svc -n genai-backend
```

3. Test backend health endpoint:

```bash
kubectl port-forward svc/genai-backend-service 8000:8000 -n genai-backend
curl http://localhost:8000/health
```

4. Verify MongoDB:

```bash
kubectl get pvc -n genai-backend
kubectl get pods -l app=genai-user-mgmt,tier=database -n genai-backend
kubectl get pods -l app=genai-user-mgmt,tier=chromadb -n genai-backend
```

## RBAC Considerations

The backend does not call the Kubernetes API, so no additional RBAC objects are required beyond the default namespace permissions.
