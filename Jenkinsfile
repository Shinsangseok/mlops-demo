pipeline {
    agent {
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
'''
        }
    }

    stages {
        stage('Kubernetes Agent Test') {
            steps {
                container('python') {
                    sh 'echo "=== Kubernetes Jenkins Agent ==="'
                    sh 'hostname'
                    sh 'python --version'
                }
            }
        }

    stage('Nexus Dependency Test') {
        steps {
            container('python') {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'nexus-pypi',
                        usernameVariable: 'NEXUS_USER',
                        passwordVariable: 'NEXUS_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x


                        cat > ~/.netrc <<NETRC
machine 172.16.0.200
login ${NEXUS_USER}
password ${NEXUS_PASSWORD}
NETRC

                        chmod 600 ~/.netrc

                        python -m pip install \
                          --index-url http://172.16.0.200:8081/repository/pypi-group/simple \
                          --trusted-host 172.16.0.200 \
                          requests

                        rm -f ~/.netrc


                        python -c "import requests; print('requests version:', requests.__version__)"
                     '''
                    }
                }
            }
        }
    }
}
