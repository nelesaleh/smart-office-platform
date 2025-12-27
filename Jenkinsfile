pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "nelerayan/smart-office-backend"
        DOCKER_TAG = "latest"

        // Directory containing Kubernetes YAML manifests
        K8S_DIR = "smart-office-devops-k8s"

        DOCKER_CREDS = credentials('docker-hub-credentials')
        K8S_CRED_ID = 'k8s-config'
        DOCKER_BUILDKIT = '0'
    }

    stages {
        // Note: Jenkins automatically checks out the source code at the start of the pipeline.

        stage('Lint Code') {
            steps {
                echo '🔍 Linting Code...'
                sh 'pip install pylint flask || true'

                // Lint the main application file
                sh 'pylint --disable=R,C smart-office-app/run.py || true'
            }
        }

        stage('Build & Push Docker') {
            steps {
                script {
                    echo "🐳 Logging into Docker Hub..."
                    sh 'echo $DOCKER_CREDS_PSW | docker login -u $DOCKER_CREDS_USR --password-stdin'

                    echo "🔨 Building Image..."
                    // Build Docker image from the current root directory
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."

                    echo "🚀 Pushing Image..."
                    sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    echo "☸️ Deploying to Kubernetes..."

                    withKubeConfig([credentialsId: K8S_CRED_ID]) {

                        // Apply Kubernetes configurations from the K8s directory
                        sh "kubectl apply -f ${K8S_DIR}/ --validate=false"

                        // Force restart the deployment to pull the latest image
                        sh "kubectl rollout restart deployment smart-office-backend"

                        // Verify deployment status
                        sleep 10
                        sh "kubectl get pods"
                        sh "kubectl get svc smart-office-service"
                    }

                    echo "✅ Deploy Finished!"
                }
            }
        }
    }
}