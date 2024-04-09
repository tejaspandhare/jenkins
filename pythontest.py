pipeline {
  agent { label 'linux' }
  environment {
   ANSIBLE_PRIVATE_KEY=credentials('automation-key') 
  }
  stages {
    stage('Hello') {
      steps {
        sh """python3   'hello.py' '{"message":"${message}"}' """
      }
    }
  }
}
