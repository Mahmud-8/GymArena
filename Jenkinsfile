// GymArena PM2 - same pipeline as .github/workflows/domain-ci.yml, implemented for Jenkins.
// Requires plugins: Pipeline, Git, JUnit, Coverage, SonarQube Scanner.
// Global tools: JDK "jdk21" and Maven "maven3"; SonarQube server named "SonarQube".
pipeline {
    agent any

    tools {
        jdk 'jdk21'
        maven 'maven3'
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and unit test') {
            steps {
                dir('domain-java') {
                    sh 'mvn -B -ntp clean verify'
                }
            }
            post {
                always {
                    junit testResults: 'domain-java/target/surefire-reports/*.xml', allowEmptyResults: false
                    recordCoverage tools: [[parser: 'JACOCO', pattern: 'domain-java/target/site/jacoco/jacoco.xml']],
                                   sourceDirectories: [[path: 'domain-java/src/main/java']],
                                   qualityGates: [
                                       [threshold: 80.0, metric: 'LINE', baseline: 'PROJECT', criticality: 'FAILURE'],
                                       [threshold: 80.0, metric: 'BRANCH', baseline: 'PROJECT', criticality: 'FAILURE']
                                   ]
                }
            }
        }

        stage('SonarQube analysis') {
            steps {
                dir('domain-java') {
                    withSonarQubeEnv('SonarQube') {
                        sh 'mvn -B -ntp sonar:sonar'
                    }
                }
            }
        }

        stage('Quality gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'domain-java/target/site/jacoco/**', allowEmptyArchive: true
        }
        success {
            echo 'Unit tests, coverage gate and SonarQube quality gate passed.'
        }
        failure {
            echo 'Pipeline failed: check the test report, coverage or quality gate.'
        }
    }
}
