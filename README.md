# 🏢 Smart Office Automation Platform

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Platform](https://img.shields.io/badge/platform-kubernetes-blue)
![Container](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![CI/CD](https://img.shields.io/badge/jenkins-%232C5263.svg?style=flat&logo=jenkins&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-success)

A smart automation backend designed to manage office utilities like lights, temperature, and parking spots. This project demonstrates a complete **DevOps Automation System** managed as a **Monorepo**.

The primary goal of this project is to showcase advanced **CI/CD, Containerization, and Orchestration** capabilities.

---

## 🚀 Project Overview

The **Smart Office Platform** serves as a robust backend API infrastructure. It includes a comprehensive CI/CD pipeline that ensures code quality, testing, and automated deployment to Kubernetes.

**Key DevOps Features:**

* **Automated Testing:** Unit tests run automatically inside Docker containers on every commit.
* **Mocking & Isolation:** Tests use `unittest.mock` to simulate Database connections, ensuring build isolation.
* **Containerization:** Optimized Docker images with non-root security and multi-stage builds.
* **Orchestration:** Kubernetes deployment with Self-Healing, Services, and Rolling Updates.
* **Infrastructure:** MongoDB StatefulSet for persistent data management.

### 🛠 Tech Stack

* 🐍 **App:** Python (Flask) REST API.
* 🗄️ **Database:** MongoDB (NoSQL).
* 🐳 **Container:** Docker.
* ☸️ **Orchestration:** Kubernetes (Minikube/EKS).
* 🏗️ **CI/CD:** Jenkins (Declarative Pipeline).

---

## 📂 Project Structure (Monorepo)

The project is organized as a Monorepo to keep Application code and Infrastructure code in sync.

```bash
SMART-OFFICE-PLATFORM/
├── smart-office-app/          # 🐍 Application Source Code
│   ├── App/                   # Blueprints & Application Logic
│   ├── tests/                 # 🧪 Unit Tests (Includes __init__.py & Mocks)
│   ├── run.py                 # Application Entry Point
│   └── templates/             # HTML Templates
│
├── smart-office-devops-k8s/   # ⚙️ Infrastructure as Code (Kubernetes)
│   ├── backend.yaml           # App Deployment & Service definition
│   ├── db.yaml                # MongoDB StatefulSet & Service
│   └── monitor.yaml           # Monitoring configurations
│
├── Dockerfile                 # 🐳 Docker Configuration (Build instructions)
├── Jenkinsfile                # ⛓ CI/CD Pipeline Logic (Groovy)
└── requirements.txt           # Python Dependencies

## 🔄 CI/CD Pipeline Workflow

The project uses a **Jenkins Declarative Pipeline** to automate the software delivery lifecycle:

1.  **Lint Code:** Checks Python syntax and style using `pylint`.
2.  **Build Image:** Builds the Docker image locally with caching strategies.
3.  **Run Unit Tests:** Runs `unittest` inside the isolated container environment.
    * *Note:* Uses Mocking to bypass live DB requirements during testing.
4.  **Push Image:** Pushes the verified image to Docker Hub (only if tests pass).
5.  **Deploy:** Applies Kubernetes manifests (`kubectl apply`) and triggers a zero-downtime rolling restart.

---

## 📡 System Capabilities

### Monitoring & Health

The system is designed with observability in mind:

* `/health/live`: Liveness probe for Kubernetes.
* `/health/ready`: Readiness probe (checks Database connectivity).
* `/metrics`: Exposes Prometheus-compatible metrics.

### Scalability

* **Horizontal Scaling:** The Flask backend is stateless and deployed via Kubernetes Deployments.
* **Persistence:** MongoDB uses StatefulSets and PVCs (Persistent Volume Claims) to ensure data safety.

---

## 🏃‍♂️ How to Run

### Prerequisites

* Kubernetes Cluster (Minikube / EKS)
* Jenkins with Docker & Kubernetes plugins
* Docker Hub Account

### Quick Start

1.  Clone the repository.
2.  Configure Jenkins credentials:
    * `docker-hub-credentials` (Username/Password)
    * `k8s-config` (Kubeconfig file)
3.  Run the pipeline!