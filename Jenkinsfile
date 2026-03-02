pipeline {
    agent any

    stages {
        stage('Build Test Image') {
            steps {
                sh 'docker build --target test -t vertex-block-test:${BUILD_NUMBER} .'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'docker run --rm vertex-block-test:${BUILD_NUMBER} uv run pytest tests/ -v'
            }
        }

        stage('Build Prod Image') {
            when { buildingTag() }
            steps {
                sh 'docker build --target prod -t shadowlands:5000/vertex-block:${TAG_NAME} .'
            }
        }

        stage('Push to Registry') {
            when { buildingTag() }
            steps {
                sh 'docker push shadowlands:5000/vertex-block:${TAG_NAME}'
            }
        }
    }

    post {
        always {
            sh 'docker rmi vertex-block-test:${BUILD_NUMBER} || true'
        }
        success {
            script {
                if (env.TAG_NAME) {
                    sh "docker rmi shadowlands:5000/vertex-block:${TAG_NAME} || true"
                }
            }
        }
    }
}
