# Local Kubernetes Deployment Guide

This directory contains the Helm chart and instructions for deploying the microservices application to a local Kubernetes environment.

## Prerequisites

- **Docker Desktop** (with Kubernetes enabled) OR **Kind** (Kubernetes in Docker)
- **kubectl** (Kubernetes command-line tool)
- **Helm** (Package manager for Kubernetes)

## 1. Setup Local Environment

### Start Kubernetes
Ensure your local Kubernetes cluster is running.
- **Docker Desktop**: Check the "Enable Kubernetes" box in Settings.
- **Kind**: Run `kind create cluster`.

### Install Ingress Controller
An Ingress Controller is required to route traffic from your local domains to the services.

**Using Helm (Recommended):**
```bash
kubectl delete validatingwebhookconfiguration ingress-nginx-admission; helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace
```

Wait for the ingress controller pod to be ready:
```bash
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s
```

## 2. Build Docker Images

Since we are using local images, you need to build them so they are available to your cluster.

**For Docker Desktop:**
Simply build the images using the standard docker command. Kubernetes in Docker Desktop shares the image cache.

```bash
# Navigate to the project root
cd ../..

# Build Product Service
docker build -t product-service:latest -f product-service/Dockerfile .

# Build Translation Service
docker build -t translation-service:latest -f translation-service/Dockerfile .
```


## 3. configure Local Domains

Map the local domains to your cluster's ingress IP (usually `127.0.0.1` for Docker Desktop).

Add the following lines to your `/etc/hosts` file (macOS/Linux) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
127.0.0.1 product.local
127.0.0.1 translation.local
```

## 4. Install the Helm Chart

Navigate to the `k8s` directory and install the chart.

```bash
# From the project root
cd k8s

# Install or Upgrade the release
helm upgrade --install microservices ./helm/microservices
```

## 5. Verify Deployment

Check the status of your pods:
```bash
kubectl get pods
```

Check the ingress:
```bash
kubectl get ingress
```

## 6. Access the Application

- **Product Service**: http://product.local
  - Health check: http://product.local/health
  - API Docs: http://product.local/docs
- **Translation Service**: http://translation.local
  - Health check: http://translation.local/health
  - API Docs: http://translation.local/docs

## 7. Cleanup

To uninstall the application:
```bash
helm uninstall microservices
```

To remove the Ingress Controller:
```bash
helm uninstall ingress-nginx -n ingress-nginx
kubectl delete namespace ingress-nginx
```
