pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE = 'aceest-fitness'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Clean Build') {
            steps {
                sh '''
                    rm -rf .venv
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                    .venv/bin/python -m py_compile app.py
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '.venv/bin/python -m pytest -q --junitxml=report.xml'
            }
            post {
                always {
                    junit 'report.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest .'
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh '''
                    docker rm -f aceest-staging || true
                    docker run -d --name aceest-staging -p 5001:5000 ${IMAGE}:${BUILD_NUMBER}
                    sleep 5
                    curl -fs http://localhost:5001/health
                '''
            }
        }

        stage('Approve Production') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    input message: 'Staging looks good. Promote to production?'
                }
            }
        }

        stage('Deploy to Production (with rollback)') {
            steps {
                sh '''
                    PREV_IMAGE=$(docker inspect --format '{{.Config.Image}}' aceest-prod 2>/dev/null || true)
                    docker rm -f aceest-prod || true
                    docker run -d --name aceest-prod -p 5002:5000 ${IMAGE}:${BUILD_NUMBER}
                    sleep 5
                    if ! curl -fs http://localhost:5002/health; then
                        echo "Health check failed - rolling back"
                        docker rm -f aceest-prod || true
                        if [ -n "$PREV_IMAGE" ]; then
                            docker run -d --name aceest-prod -p 5002:5000 "$PREV_IMAGE"
                        fi
                        exit 1
                    fi
                '''
            }
        }
    }

    post {
        success {
            echo 'CI/CD pipeline completed successfully'
        }
        failure {
            echo 'Pipeline failed - deployment was not completed'
        }
    }
}
