# Contributing

Below are instructions and best practices to follow when making changes to the repository.


## 1. Create your own branch

Create a branch with a descriptive overview of what changes you will make

```bash
git checkout -b my-branch-name
```

## 2. Set up Poetry

[Install poetry](https://python-poetry.org/docs/#installation) to your system. This is the python package and dependency manager used for this project.

Once installed to your system, install the dependencies by first navigating `/backend/` which contains `pyproject.toml`. Then run:
```bash
poetry install --with dev
```

## Set up pre-config hooks

In the same directory as `pyproject.toml`, activate your terminal with the poetry environment

```bash
source $(poetry env info --path)/bin/activate
```

Then, navigate to the repository root (where `.pre-commit-config.yaml` lives) and run:

```bash
pre-commit install
```

You should see a message like this `pre-commit installed at .git/hooks/pre-commit`.

Now when you try to commit to the repo, many checks will run to ensure code consistency and quality.

## Install Just to execute helper script recipes

Just is a handy way to save and run project-specific commands.

Install it to your `$PATH` by following the [instructions here](https://just.systems/man/en/chapter_2.html#installation).

Once installed, from the project root directory, all recipes found in the `justfile` can be run by simply doing

```bash
just <recipe name>
```

## Run Tests

To run pytest, you can't really do it locally. When you want to run the pytests for the application, run the following recipe.

```bash
just pytest
```

This recipe looks at `docker-compose-dev.yaml` and builds the api into a docker image,
but downloads the dependencies specified in `dev` so that pytest can run.

## Creating Alembic Revisions

When you have made changes to the database table definitions (largely located in `/backend/app/models/`) then an alembic database revision script must be created.

To accomplish this, you need to have a poetry shell script open (or use `poetry run`) and an instance of the postgres database must be running and able to be connected to.

To achieve the latter, start the database (and the api, but we can ignore it entirely) using `just`

```bash
just start-api-dev
```
The postgres instance is accessible over localhost port 5432, so in your `.env` you must make sure that `DATABASE_HOST=localhost` is present.

Then, make sure that the table you want to generate revisions for is imported in `/backend/app/models/__init__.py` or else alembic won't grab the metadata properly.

Finally, run the alembic command:

```bash
alembic revision --autogenerate -m "your message here."
```

NOTE: You MUST manually inspect the revision and make changes. Column parameters like `unique=True` might not show up in the generated revision.
This is a very important thing to remember, because alembic is the piece that actually constructs the tables in production.
