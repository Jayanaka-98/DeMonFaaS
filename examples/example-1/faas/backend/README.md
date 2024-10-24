# Backend


Repository TODO:

- Create package independent github CI workflows
    - [X] Require PRs have labels
    - [X] When a PR is merged, add PR name and link to release Draft and update next release version.
- Create app specific github CI/CD workflows
    - [ ] Compile and upload app Docker Image to GCP Artifact Repository when a release is published
    - [ ] Run unit and integration tests when a PR is created
- Set up basic app
    - [X] Create nested directory
    - [X] create pyproject.toml in directory
    - [X] install pre-commit in dev dependencies
    - [X] set up pre-commit yaml
    - [X] create empty fastapi app
- connect database to app (asyncpg)
    - [X] configure postgres URI from .env or envrionment variables
    - [X] create a postgres database via docker compose
    - [X] connect app to database (no routes yet)
    - [X] configure pre-start to ensure app connects to db before starting
- support user functionality
    - [X] create users table
    - [X] CRUD routes for users table
    - [X] create super user on startup
    - [ ] require tokens for update and delete API route


## Sources:
Lots of code from this repository was taken from many open source repositories.

- [fastapi-alembic-sqlmodel-async](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async/tree/main)
- [meilisearch-fastapi](https://github.com/sanders41/meilisearch-fastapi)
