# Jenkins controller for the GymArena PM2 pipeline, configured as code.
FROM jenkins/jenkins:lts-jdk21

# Optional extra root certificates (e.g. a local TLS-scanning proxy): put *.crt in certs/.
USER root
COPY certs/ /usr/local/share/ca-certificates/extra/
RUN update-ca-certificates \
 && for c in /usr/local/share/ca-certificates/extra/*.crt; do \
      [ -f "$c" ] && keytool -importcert -noprompt -cacerts -storepass changeit -alias "$(basename "$c")" -file "$c" || true; \
    done
USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false" \
    CASC_JENKINS_CONFIG=/var/jenkins_casc/casc.yaml
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /var/jenkins_casc/casc.yaml
