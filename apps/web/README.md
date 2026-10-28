# apps/web

Implemented React/TypeScript kiosk: registration, code confirmation, profile view,
and name/age correction. Built with Vite and served by Member Service at
`http://localhost:8105/kiosk/` after `docker compose up --build`.

For UI development, use the pinned pnpm version from package.json:
`pnpm install --frozen-lockfile`, then `pnpm dev`. The Vite proxy forwards `/api`
to the running Member Service on port 8105. Run `pnpm build` for type checking
and a production bundle. There are no external fonts or analytics requests.

Live session display, trainer workspace, staff dashboard and leaderboard remain
planned. See [API and scope](../../docs/member-registration.md).
