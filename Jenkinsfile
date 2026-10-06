pipeline {
    agent  {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod 
spec: 
  containers: 
    - name: python 
      image: python:3.12-slim 
      command: 
        - cat 
      tty: true 
...
        } 
    } 

    stages {
        stage('Kubernetes Agent Test') {
            steps  {
                container('python') {
                    sh 'echo "=== Kubernetes Jenkins Agent ==="'
                    sh 'hostname'
                    sh 'python --version'
                    sh 'cat /etc/os-release | head' 
                }
            }
        }
    }
}

