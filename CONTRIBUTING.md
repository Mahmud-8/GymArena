# Working on GymArena

Use your assigned service branch. Keep each pull request focused on one story or one small integration change.

```bash
git clone https://github.com/Mahmud-8/GymArena.git
cd GymArena
git fetch origin
git switch feature/exercise-tracking-service
git merge origin/develop
```

Replace the example branch with your assigned service branch. Commit using your own GitHub identity. Never put access tokens, passwords, real member data, face images or scale records in the public repository.

Before opening a pull request, check the acceptance criteria for the story, run the checks relevant to the code you changed, and describe the result honestly. Open feature pull requests against `develop`; use `main` only for a reviewed integration baseline. Request review from a teammate who did not author the change.

Only claim a test passed if it was actually run. The initial repository contains planning files; application startup commands will be added when the implementation exists.
