pipeline {
  agent any
  stages {
    stage('Hello') {
      steps {
        sh """python3   'hello.py' ${params.message} """
      }
    }
  }
}
