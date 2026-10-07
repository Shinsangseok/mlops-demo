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

    - name: sonar
      image: sonarsource/sonar-scanner-cli:5.0
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
                              -r summarizer/requirements.txt

                            rm -f ~/.netrc

                            python -c "import requests; print('requests version:', requests.__version__)"
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar') {
                    withCredentials([
                        string(
                            credentialsId: 'sonar-token',
                            variable: 'SONAR_TOKEN'
                        )
                    ]) {
                        sh '''
                            sonar-scanner \
                              -Dproject.settings=ci/sonar-project.properties \
                              -Dsonar.host.url=http://172.16.0.200:9000 \
                              -Dsonar.login=${SONAR_TOKEN}
                        '''
                    }
                }
            }
        }
    }
}
