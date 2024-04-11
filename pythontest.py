pipeline {
  agent any
  stages {
    stage('Get Message from Terminal') {
      steps {
        sh """python3   'hello.py' ${params.message} """
      }
    }
  }
}
