pipeline {
    agent any
    
    stages {
        stage('Run Python Script') {
            steps {
                script {
                    sh "echo '${message}' | /usr/bin/python3 smiley.py"
                }
            }
        }
    }
}
