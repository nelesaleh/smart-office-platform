pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "nelerayan/smart-office-backend"
        DOCKER_TAG = "latest"

        // ✅ Updated: Pointing to the local folder containing YAML files in your Monorepo
        K8S_DIR = "smart-office-devops-k8s"

        DOCKER_CREDS = credentials('docker-hub-credentials')
        K8S_CRED_ID = 'k8s-config'
    }

    stages {
        // Note: We removed the separate 'Checkout' stage because in a Monorepo, 
        // Jenkins automatically checks out all files (App + DevOps) at the start.

        stage('Lint Code') {
            steps {
                echo '🔍 Linting Code...'
                sh 'pip install pylint flask || true'

                // ✅ Updated: Pointing to the Python file inside the 'smart-office-app' folder
                sh 'pylint --disable=R,C smart-office-app/run.py || true'
            }
        }

        stage('Run Unit Tests') {
            steps {
                echo '🧪 Running Unit Tests...'
                sh 'pip install -r requirements.txt'
                sh 'python -m unittest discover tests'
            }
        }

        stage('Build & Push Docker') {
            steps {
                script {
                    echo "🐳 Logging into Docker Hub..."
                    sh 'echo $DOCKER_CREDS_PSW | docker login -u $DOCKER_CREDS_USR --password-stdin'

                    echo "🔨 Building Image..."
                    // ✅ Updated: The Dockerfile is now in the Root, so we build from current directory (.)
                    sh "docker build --network=host -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    echo "🚀 Pushing Image..."
                    sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    echo "☸️ Deploying to Kubernetes..."

                    // Ensure you have the 'k8s-config' credential in Jenkins
                    withKubeConfig([credentialsId: K8S_CRED_ID]) {

                        // ✅ Updated: Apply YAML files from the local folder directly
                        sh "kubectl apply -f ${K8S_DIR}/ --validate=false"

                        // Restart the deployment to ensure it pulls the new image
                        sh "kubectl rollout restart deployment smart-office-backend"

                        // Wait a few seconds for pods to restart
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