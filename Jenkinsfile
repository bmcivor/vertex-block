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
    }

    post {
        always {
            sh 'docker rmi vertex-block-test:${BUILD_NUMBER} || true'
        }
    }
}
