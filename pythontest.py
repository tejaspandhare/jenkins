pipeline {
    agent any
    
    stages {
        stage('Run Python Script') {
            steps {
                script {
                    def message = "  " // Provide your input message here
                    sh "echo '${message}' | /usr/bin/python3 smiley.py"
                }
            }
        }
    }
}
