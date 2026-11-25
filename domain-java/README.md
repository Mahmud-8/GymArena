# GymArena domain scenarios (PM2)

Java 21 implementation of the four PM2 design scenarios (one per team member), tested with JUnit 5 and Mockito, with JaCoCo coverage.

| Package | Scenario | Owner | Jira |
| --- | --- | --- | --- |
| `com.gymarena.membership` | Record a membership renewal | Mahmoud Emad | GYM-21 |
| `com.gymarena.session` | Pause and resume a local 1v1 attempt | Ahmed Ebrahim | GYM-40 |
| `com.gymarena.member` | Capture and confirm a scale reading | Mohamed Soliman | GYM-26 |
| `com.gymarena.challenge` | Approve and present versioned challenge rules | Mohamed Hegazy | GYM-31 |

Design rules used by the tests:

- Objects in the object diagrams are the fixtures (`*Fixtures` classes).
- Messages in the collaboration diagrams are Mockito mocks checked with `InOrder.verify`.
- Every state-diagram transition, valid or invalid, has a test (`*StateTest` classes).

```
mvn verify            # tests, JaCoCo report in target/site/jacoco, 80% line/branch gate
mvn verify sonar:sonar -Dsonar.host.url=<url> -Dsonar.token=<token> -Dsonar.qualitygate.wait=true
```

CI: `.github/workflows/domain-ci.yml` and the root `Jenkinsfile`. Diagrams: `docs/pm2/diagrams/`.
