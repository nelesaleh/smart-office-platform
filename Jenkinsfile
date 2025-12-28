pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "nelerayan/smart-office-backend"
        DOCKER_TAG = "latest"
        K8S_DIR = "smart-office-devops-k8s"
        DOCKER_CREDS = credentials('docker-hub-credentials')
        K8S_CRED_ID = 'k8s-config'
    }

    stages {
        stage('Lint Code') {
            steps {
                echo '🔍 Linting Code...'
                // Trying to install pip, but adding || true so it doesn't fail the build if pip is missing
                sh 'pip install pylint flask || true'
                sh 'pylint --disable=R,C smart-office-app/run.py || true'
            }
        }

        // 1. BUILD FIRST (So the image exists and has the new test files)
        stage('Build Docker Image') {
            steps {
                script {
                    echo "🔨 Building Image (No Cache)..."
                    // --no-cache ensures it picks up the moved 'tests' folder
                    sh "docker build --no-cache --network=host -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                }
            }
        }

        // 2. TEST SECOND (Run the image we just built)
        stage('Run Unit Tests') {
            steps {
                echo '🧪 Running Unit Tests inside Container...'
                // Now this will work because the image is built and fresh
                sh "docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -m unittest discover tests"
            }
        }

        // 3. PUSH THIRD (Only if tests passed)
        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "🐳 Logging into Docker Hub..."
                    sh 'echo $DOCKER_CREDS_PSW | docker login -u $DOCKER_CREDS_USR --password-stdin'

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
                        sh "kubectl apply -f ${K8S_DIR}/ --validate=false"
                        
                        // Restart to pull the new image
                        sh "kubectl rollout restart deployment smart-office-backend"
                        
                        // Wait for update
                        sleep 10
                        sh "kubectl get pods"
                    }
                    echo "✅ Deploy Finished!"
                }
            }
        }
    }
}