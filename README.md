# git-pork
This is the official data and analytics repo of Pork Rub Fantasy Football. The original software is written in Python 3 and uses the ESPN api to pull data. The API can be found here:
[espn-api](https://github.com/cwendt94/espn-api).
Functions that allow for pulling tons or raw data for any league can be found here. Here is a brief listing of functions and what they can do (located in main.py):  

<b>pull_all_data(league_index, username, password, draft)</b>

This function pulls data using your league ID (league_index arg). username and password can also be used if it's a private league. draft is a boolean where 0 does not pull draft data (strictly seasonal data) and 1 pulls strictly draft data.

The seasonal data is pulled and saved into a pandas dataframe which is then saved as a csv file that can be further analyzed/plotted with matplotlib or excel.

Example of dataframe saving data from 2020 season:
![alt text](https://i.imgur.com/cfPEVCQ.png)

The draft data contains all data possible to pull from the api. It dumps data into a pandas dataframe which is also saved to a csv.

Example of dataframe containing data from a draft:
![alt text](https://i.imgur.com/fwA2qlI.png)

## Modern app

The new deployable app lives in `apps/`.

- `apps/api`: FastAPI backend, normalized database models, local CSV/media import, ESPN adapter, live polling worker.
- `apps/web`: Vite + React frontend with Swiper/Recharts-ready dashboard components.
- `deploy/digitalocean-app.yaml`: DigitalOcean App Platform template.

Deployment setup, database migration, secrets, and launch checks are in
[the DigitalOcean guide](docs/digitalocean.md).

Local backend setup:

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e .
prffs-import
uvicorn prffs_api.main:app --reload --port 8000
```

Fetch ESPN seasons directly into the configured database:

```bash
prffs-fetch-season 2024 2025
```

Fetch ESPN regular season plus available playoff weeks without touching draft data:

```bash
prffs-fetch-season 2019 2020 2021 2022 2023 2024 2025 --include-playoffs --season-only
```

Import historical draft CSVs from the repo alongside local season/media data:

```bash
prffs-import
```

Draft data is available through `/api/draft/summary` and `/api/draft/picks`. All-time league history is available through `/api/history/summary`.

Local frontend setup:

```bash
cd apps/web
npm install
npm run dev
```

Secrets should use `ESPN_S2` and `ESPN_SWID`. Legacy `.env` keys `espn` and `password` are supported locally as fallbacks.

Set `ADMIN_TOKEN` in the root `.env` to enable Admin Studio, then sign in with
that password in the browser. Unconfigured admin access is disabled. See
[.env.example](.env.example) for the available settings; preserve existing
secrets when editing your `.env`.

`prffs-import` replaces the seasons present in local CSV files. It no longer
clears every season by default; that requires `--reset`. To deploy your existing
database with all history and admin content, use `prffs-migrate-db` as described
in the deployment guide instead.
