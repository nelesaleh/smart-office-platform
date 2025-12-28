# 🏢 Smart Office Automation Platform

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Platform](https://img.shields.io/badge/platform-kubernetes-blue)
![Container](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![CI/CD](https://img.shields.io/badge/jenkins-%232C5263.svg?style=flat&logo=jenkins&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)

A smart website designed to manage office utilities like lights and temperature. This project shows a full **DevOps Automation System**. I organized it as a **Monorepo**, meaning the App Code and the Server Settings are all in one place.

---

## 🚀 What is this Project?

The **Smart Office Platform** is a dashboard where you can control office devices (Lighting, Security, Parking).

This project proves I can use **Modern DevOps Tools** to:
1.  **Automate updates** (Jenkins).
2.  **Package software** (Docker).
3.  **Keep the app running** (Kubernetes).

### 🛠 Tools Used
* 🐍 **App:** Python (Flask) & HTML.
* 🗄️ **Database:** MongoDB.
* 🐳 **Container:** Docker (To package the app).
* ☸️ **Manager:** Kubernetes (To run and repair the app).
* 🏗️ **Automation:** Jenkins (To build and deploy automatically).

---

🔄 CI/CD Pipeline Workflow
The project uses a Jenkins Declarative Pipeline to automate the software delivery lifecycle:

Lint Code: Checks Python syntax and style using pylint.
Build Image: Builds the Docker image locally with caching strategies.
Run Unit Tests: Runs unittest inside the isolated container environment.
   Note: Uses Mocking to bypass live DB requirements during testing.
Push Image: Pushes the verified image to Docker Hub (only if tests pass).
Deploy: Applies Kubernetes manifests (kubectl apply) and triggers a zero-downtime rolling restart.

📡 System Capabilities
Monitoring & Health
The system is designed with observability in mind:

/health/live: Liveness probe for Kubernetes.

/health/ready: Readiness probe (checks Database connectivity).

/metrics: Exposes Prometheus-compatible metrics.

Scalability
Horizontal Scaling: The Flask backend is stateless and deployed via Kubernetes Deployments.

Persistence: MongoDB uses StatefulSets and PVCs (Persistent Volume Claims) to ensure data safety.

🏃‍♂️ How to Run
Prerequisites
Kubernetes Cluster (Minikube / EKS)

Jenkins with Docker & Kubernetes plugins

Docker Hub Account

Quick Start
Clone the repository.

Configure Jenkins credentials:

docker-hub-credentials (Username/Password)

k8s-config (Kubeconfig file)

Run the pipeline!

## 📂 Project Structure (Monorepo)

I put everything in one main folder so the code and infrastructure stay synced.

```bash
SMART-OFFICE-PLATFORM/
├── smart-office-app/        # 🐍 The Python App Code
│   ├── templates/           # Website Pages (HTML)
│   ├── run.py               # Main file to start the app
│   └── ...
├── smart-office-devops-k8s/ # ⚙️ The Server Settings (Kubernetes Files)
│   ├── backend.yaml         # App Deployment & LoadBalancer
│   ├── db.yaml              # Database Settings
│   └── monitor.yaml         # Monitoring Settings
├── Dockerfile               # 🐳 Instructions to build the Docker Image
├── Jenkinsfile              # ⛓ Steps for Jenkins to automate the work
└── requirements.txt         # List of Python libraries needed

