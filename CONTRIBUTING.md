# Working on TripGenie

## Everyday workflow

1. Pull `main` and create a branch: `git switch -c feature/your-change`.
2. Run both services using the README. Preserve existing `.env` files and local data.
3. Make the change and exercise the affected browser flow.
4. Run backend integration tests, frontend type checking and a production build.
5. Stage intentional files and run `python scripts/check_repository.py`.
6. Push and open a pull request. Review checks and the preview before merging.

Solo changes can go directly to `main`; linked production hosting follows that branch.

## Design and behavior

Keep the travel workspace calm, responsive, keyboard-accessible and usable with reduced motion. Every action needs a connected result, understandable loading and recoverable errors. Label sample plans, estimates and current weather honestly.

## Data and API changes

Check ownership on private routes. Exclude private notes, chat and expenses from public shares. Validate AI output before saving; preserve work on provider failure. Add meaningful tests for changed data boundaries.

Use reviewed versioned migrations for significant production schema changes. Back up live data before migrations. Do not commit databases or production exports.

## Secrets

Use backend `.env` locally and hosting environment settings in cloud. Never put real keys in `NEXT_PUBLIC_*`, source, screenshots or issues. Rotate any committed credential; removing its latest copy does not erase Git history.
