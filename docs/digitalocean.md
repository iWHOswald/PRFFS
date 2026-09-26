# Deploy PRFFS to DigitalOcean

The deployment consists of a React static site, a FastAPI service, a schema
setup job, an optional ESPN score worker, and a managed PostgreSQL database.
The app spec is in [deploy/digitalocean-app.yaml](../deploy/digitalocean-app.yaml).

## Current deployment

- Site: <https://prffs-jgq9t.ondigitalocean.app>
- App: `prffs`, ID `1a93ef88-ae70-4d1b-a0b7-4a9ef7e51ebb`
- [DigitalOcean app dashboard](https://cloud.digitalocean.com/apps/1a93ef88-ae70-4d1b-a0b7-4a9ef7e51ebb)
- PostgreSQL: `prffs-postgres` in SFO2, database `prffs`, user `prffs_app`.
- Migration completed on 2026-09-26: all 17 tables and 28,412 rows verified
  against the local SQLite snapshot. Do not repeat the initial migration.
- Admin password: local, Git-ignored `var/deploy/admin-token.txt`. Select
  **Admin Studio** in the site's season/view menu to sign in. Save this password
  in your password manager; reloading or signing out clears the browser session.

Deploy future code changes after pushing to `master`:

```bash
doctl apps create-deployment 1a93ef88-ae70-4d1b-a0b7-4a9ef7e51ebb --wait
```

GitHub pushes do not deploy automatically. The API, schema job, and ESPN worker
share a Docker image; the frontend is a static site. The following sections
document the original setup and recovery process.

## 1. Create the database in DigitalOcean

Use **Databases → Create Database** with these starting settings:

| Setting | Value |
| --- | --- |
| Engine | PostgreSQL 16 |
| Plan | Basic, 1 GiB RAM, single node |
| Region | Existing cluster: SFO2; app spec uses `region: sfo` (SFO3) |
| Cluster name | `prffs-postgres` |
| Database | Create `prffs` in **Users & Databases** |
| Database user | Create `prffs_app` in **Users & Databases** |

A single node is adequate for an initial league deployment but has no standby
node for high availability. Keep DigitalOcean's managed backups enabled and
choose a maintenance window outside game time. You can increase capacity later.

In **Network Access / Trusted Sources**, allow the current public IP of the
machine that will perform the migration. Once the app exists, add the app as a
trusted source too. Remove the temporary IP rule after migration.

Connect as `doadmin` to the **prffs** database using DigitalOcean's connection
details, then grant the application user permission to create its tables:

```sql
GRANT CONNECT ON DATABASE prffs TO prffs_app;
GRANT USAGE, CREATE ON SCHEMA public TO prffs_app;
```

Run the migration and app as `prffs_app`, so that this user owns the tables and
sequences. Use the public connection string for local migration, select the
`prffs` database and `prffs_app` user, and retain `sslmode=require`. You can use
`sslmode=verify-full` with the downloaded CA certificate for local verification.
Do not use the default `defaultdb` or copy a connection string into Git.

References: [create a cluster](https://docs.digitalocean.com/products/databases/postgresql/how-to/create/),
[users and databases](https://docs.digitalocean.com/products/databases/postgresql/how-to/manage-users-and-databases/),
[permissions](https://docs.digitalocean.com/products/databases/postgresql/how-to/modify-user-privileges/).

## 2. Migrate the existing data before starting the hosted app

Run these commands from the repository root with Python 3.12:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r apps/api/requirements.lock
pip install --no-deps -e apps/api
```

Stop any local API, ESPN worker, or importer that writes to `var/prffs.db` before
the final copy. Keep the hosted app/worker stopped until the copy completes;
the migration intentionally refuses a destination that already contains rows.

Set the target connection string without putting the password in shell history
(these commands use Bash):

```bash
read -rsp 'PostgreSQL connection string: ' PRFFS_TARGET_DATABASE_URL
printf '\n'
export PRFFS_TARGET_DATABASE_URL
prffs-migrate-db --source var/prffs.db
```

This dry run makes a consistent backup in `var/backups`, prints row counts for
every source table, and checks that the destination is accessible and empty.
It does not create tables or copy data to PostgreSQL. Inspect the counts, then:

```bash
prffs-migrate-db --source var/prffs.db --apply
unset PRFFS_TARGET_DATABASE_URL
```

The migration preserves all source tables, including saved matchup experiences
that no longer have a Python model. It copies explicit IDs and repairs sequences
for future inserts. Every table must match by row count and content fingerprint
before the transaction commits. A failed transfer rolls back its table/data
changes; the original SQLite file and its backup remain available.

The migration is for an **empty** PostgreSQL database. Repeating it after a
successful migration is rejected. Do not delete a populated hosted database to
retry; investigate the failure or use a separate empty destination instead.

Do **not** run `prffs-import` during deployment. It replaces the seasons present
in local CSVs, which cover less history than the current SQLite database. It
requires `--allow-production` in production and `--reset` to clear all history.

## 3. Prepare the GitHub source and runtime secrets

Commit and push the modern application, deployment files, historical media,
`Constitution.pdf`, and content to `iWHOswald/PRFFS`, branch `master` (or update
all component source entries in the spec to the intended repository/branch).
The app was initially untracked locally: DigitalOcean cannot build those files
until they have been pushed. Review the staged files; `.env`, `var/`, databases,
dependencies, and private deployment specs are excluded by `.gitignore`.

The spec uses the public Git clone URL, so DigitalOcean's GitHub integration
does not need repository access. Deployments are triggered manually. Keep the
repository public while using this source configuration.

The required secrets are:

| Secret | Where it is used |
| --- | --- |
| `ESPN_S2` | API and score worker; ESPN private-league session cookie |
| `ESPN_SWID` | API and score worker; ESPN SWID cookie |
| `ADMIN_TOKEN` | API only; at least 32 characters; the admin sign-in password |

Generate an admin password locally and save it in your password manager:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Create a private deployment spec, with secrets marked `SECRET` and `RUN_TIME`:

```bash
python deploy/render_app_spec.py
```

The helper uses environment variables or the existing `.env` (including legacy
`espn`/`password` keys), and prompts with hidden input for missing values. It
does not deploy or print the secrets. The resulting `var/deploy/app.yaml` is
ignored by Git and readable only by its owner. Use `--without-worker` to omit
continuous score snapshots, or `--output var/deploy/another.yaml` for a new copy.
Check the cluster name, database/user, region, repository, and branch in this
private spec before creating resources. Keep secret values out of the template.

## 4. Create the App Platform app

Using the configured `doctl` CLI:

```bash
doctl apps spec validate var/deploy/app.yaml --schema-only > /dev/null
doctl apps create --spec var/deploy/app.yaml --format ID,DefaultIngress
```

The second command **creates billable cloud resources**. If you already created
an App Platform app for this deployment, use its Settings → App Spec editor or
`doctl apps update APP_ID --spec var/deploy/app.yaml` instead of creating another.
The spec validation command prints the supplied spec, so redirect its output
when validating the private copy.

Attach/add the app as a trusted source on `prffs-postgres` if it was not added
automatically. If the first schema job fails because the app was not yet trusted,
add the source and redeploy. The schema job is safe to rerun and does not import
or reset historical data.

The template configures these components:

| Component | Build/run settings |
| --- | --- |
| `prffs-api` | Source `/`; Dockerfile `apps/api/Dockerfile`; port 8080; health `/health` |
| `prffs-schema` | Same Dockerfile; `PRE_DEPLOY`; command `prffs-init-db` |
| `prffs-live-worker` | Same Dockerfile; command `prffs-live-worker`; optional |
| `prffs-web` | Source `apps/web`; Node 22; build `npm ci && npm run build`; output `dist` |

`DATABASE_URL` is bound to `${prffs-db.DATABASE_URL}` at runtime; `PGSSLMODE`
defaults to `require`. `APP_ENV=production` prevents accidental SQLite use, and
`INITIALIZE_DATABASE_ON_STARTUP=false` leaves schema setup to the predeploy job.
The API refuses to start without a sufficiently long admin token.

Routing preserves `/api`, `/media`, and `/health` when forwarding to the API;
`/` serves the frontend. Leave `VITE_API_BASE_URL` unset. No cross-origin setup
is needed. Add a custom domain to the whole app after the starter URL works.

The Docker build includes historical files and the constitution from the repo.
It excludes secrets, local databases, frontend dependencies, and legacy Python
scripts. New top-level asset directories must be added to `.dockerignore`'s
allowlist. Uploading media at runtime is not implemented; future uploads would
need persistent object storage such as Spaces.

References: [create apps](https://docs.digitalocean.com/products/app-platform/how-to/create-apps/),
[attach databases](https://docs.digitalocean.com/products/app-platform/how-to/manage-databases/),
[Docker builds](https://docs.digitalocean.com/products/app-platform/reference/dockerfile/).

## 5. Verify the hosted app

- `/health` returns `{"ok":true,"app":"PRFFS"}` and checks database connectivity.
- `/api/seasons` lists the migrated history, including 2013–2025 for the current snapshot.
- History, draft records, historical images, and the constitution PDF load.
- Current Season loads from ESPN. Check worker logs for successful polls if enabled.
- Admin Studio requires the admin password; saving notes works after signing in.
- Signing out or reloading the page requires another admin sign-in. The credential
  is held in browser memory only, never in a frontend build variable or local storage.
- A request to `/api/admin/context` without credentials returns 401.

Statistics, chat, and poll participation remain public. The admin password
controls private admin context, manual draft edits, and on-demand draft imports.
Rotate it by updating the API's `ADMIN_TOKEN` secret and redeploying.

After launch, remove the temporary database IP rule and retain the local backup.
After pushing future changes to `master`, deploy the latest code with:

```bash
doctl apps create-deployment APP_ID --wait
```

The schema job creates missing tables and
applies the existing additive column changes under a database lock; larger future
schema changes need explicit migrations, not a repeat of the SQLite transfer.

## Local checks

```bash
python -m unittest discover -s apps/api/tests -v
npm --prefix apps/web run build
doctl apps spec validate deploy/digitalocean-app.yaml --schema-only > /dev/null
```

PostgreSQL migration tests run when `PRFFS_TEST_DATABASE_URL` points at a test
database with schema-creation permissions; each test creates and removes its own
unique schema. Otherwise those tests are skipped. For a container build check,
run `docker build -f apps/api/Dockerfile -t prffs-api .` from the repository root.
