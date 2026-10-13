pipeline {
    agent any
    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        APP_NAME     = 'aceest-fitness-app'
        APP_VERSION  = 'V1' 
        DEV_URL      = "http://localhost:5001"
        TEST_URL     = "http://localhost:5002"
        STAGE_URL    = "http://localhost:5003"
        PROD_URL     = "http://localhost:5004"

        CURRENT_PORT = "${env.BRANCH_NAME == 'Develop' ? '5001' : env.BRANCH_NAME == 'Test' ? '5002' : env.BRANCH_NAME == 'Stage' ? '5003' : '5004'}"
    }

    stages {
        stage('Initialize') {
            steps {
                echo "Starting the automation pipeline for: ${env.APP_NAME} v${env.APP_VERSION}"
            }
        }

        stage('Repository Synchronization') {
            steps {
                echo 'Pulling application code parameters cleanly from GitHub tracking layers...'
                checkout scm
            }
        }

        stage('Docker Compression Assembly') {
            steps {
                echo 'Assembling cached container virtualization blocks on Rocky Linux Docker Engine...'
                sh 'docker build -t ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} .'
            }
        }

        stage('Static Lint Analysis') {
            steps {
                echo 'Validating Python syntax compilation structure inside the Docker Container...'
                sh 'docker run --rm ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} python -m py_compile app.py'
            }
        }

        stage('Automated Pytest Execution') {
            steps {
                echo 'Invoking component assertion tests inside clean container context...'
                sh 'docker run --rm ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} pytest test_app.py'
            }
        }

        stage('Deploy to Dev') {
            when { branch 'Develop' }
            steps {
                echo "Deploying to DEV environment at ${env.DEV_URL}..."
                sh '''
                    docker ps -q --filter "publish=${CURRENT_PORT}" | xargs -r docker stop
                    docker run -d -p ${CURRENT_PORT}:${CURRENT_PORT} --name ${APP_NAME}-dev-${BUILD_NUMBER} ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} python app.py --port=${CURRENT_PORT}
                '''
            }
        }

        stage('Deploy to Test') {
            when { branch 'Test' }
            steps {
                echo "Deploying to TEST environment at ${env.TEST_URL}..."
                sh '''
                    docker ps -q --filter "publish=${CURRENT_PORT}" | xargs -r docker stop
                    docker run -d -p ${CURRENT_PORT}:${CURRENT_PORT} --name ${APP_NAME}-test-${BUILD_NUMBER} ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} python app.py --port=${CURRENT_PORT}
                '''
            }
        }

        stage('Deploy to Stage') {
            when { branch 'Stage' }
            steps {
                echo "Deploying to STAGING environment at ${env.STAGE_URL}..."
                sh '''
                    docker ps -q --filter "publish=${CURRENT_PORT}" | xargs -r docker stop
                    docker run -d -p ${CURRENT_PORT}:${CURRENT_PORT} --name ${APP_NAME}-stage-${BUILD_NUMBER} ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} python app.py --port=${CURRENT_PORT}
                '''
            }
        }

        stage('Deploy to Prod') {
            when { branch 'main' } // Change this to 'Master' if that is your production branch name
            steps {
                echo "Deploying to PRODUCTION environment at ${env.PROD_URL}..."
                sh '''
                    docker ps -q --filter "publish=${CURRENT_PORT}" | xargs -r docker stop
                    docker run -d -p ${CURRENT_PORT}:${CURRENT_PORT} --name ${APP_NAME}-prod-${BUILD_NUMBER} ${APP_NAME}:${APP_VERSION}-${BUILD_NUMBER} python app.py --port=${CURRENT_PORT}
                '''
            }
        }
    }

    post {
        always {
            echo 'Cleaning the Jenkins workspace.'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
            script {
                try {
                    if (env.NOTIFICATION_EMAIL) {
                        mail to: "${env.NOTIFICATION_EMAIL}",
                             subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                             body: "Something is wrong with ${env.BUILD_URL}"
                    } else {
                        echo "No NOTIFICATION_EMAIL environment variable set. Skipping email dispatch."
                    }
                } catch (Exception mailError) {
                    echo "Unable to dispatch SMTP alert notification: ${mailError.getMessage()}"
                }
            }
        }
        changed {
            echo 'Things were different before...'
        }
    }
}