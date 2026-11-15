# EARTHTRACE — Every Change Leaves a Clue

A responsive Next.js/React Earth-science investigation app with Firebase Google Authentication, a rotating interactive satellite Earth, Sri Lankan climate investigations, evidence questions, yearly charts, Mann–Kendall testing and district comparisons. AI is intentionally not connected.

## මුලින් run කරන විදිහ (Windows / VS Code)

1. ZIP එක extract කරලා project folder එක VS Code එකෙන් open කරන්න.
2. Node.js 22+ සහ Python 3.10+ install කරලා terminal එක open කරන්න.
3. Run:

```bash
npm ci
npm run dev
```

4. Open http://localhost:3000 . `Take a look around — Demo mode` මගින් real datasets එක්ක flow එක පරීක්ෂා කරන්න.
5. `npm run build` production static export එක `out/` folder එකට හදනවා.

## Google sign-in සක්‍රිය කිරීම

Google sign-in is implemented but requires your Firebase project. It does not pretend the demo is a Google login.

1. In Firebase Console, create/open your project and register a **Web app**.
2. Authentication → Sign-in method → enable **Google**; choose your support email.
3. Authentication → Settings → Authorized domains → add `localhost` and your deployed hostname. For this preview: `earthtrace-detective-lk.rompingisle2.chatgpt.site` (hostname only).
4. Copy `.env.example` to `.env.local`. Fill the four `NEXT_PUBLIC_FIREBASE_*` values using your Web app configuration.
5. Restart `npm run dev`, or rebuild and redeploy for production. These `NEXT_PUBLIC_*` values are embedded at build time. Updating runtime values alone will not change a static export.
6. Click **Continue with Google**. Successful Firebase authentication opens the home screen. The avatar signs out.

The public Firebase Web configuration is not a service-account private key. Never paste a service-account JSON key into frontend code or a NEXT_PUBLIC variable.

Official setup: https://firebase.google.com/docs/auth/web/google-signin

## What works now

- Google OAuth implementation, auth-state observation and sign-out; requires the configuration above.
- Clearly labeled demo entry using sessionStorage; demo is not authentication.
- Rotating satellite-textured, software-rendered sphere with drag, country hit-testing and pause control. It does not require WebGL. Country geometry and texture are bundled locally.
- Four mystery cards. Three selectable; Ocean is unavailable because no ocean dataset was supplied. Missing Green analyzes supporting climate clues only, not vegetation loss.
- Sri Lanka and all 25 districts; selection through successive country/district/variable/date steps.
- Rainfall, near-surface air temperature and soil moisture checkbox selection.
- Real cleaned records from all three supplied CSV files; no synthetic climate observations.
- Animated student detective, orbiting loading sequence, reduced-motion support.
- Three evidence questions (unselected variables are explicitly skipped), manual answers, automatic transition to analysis.
- Annual time-series charts, OLS slope, Sen slope, original Mann–Kendall test, p-values, descriptive rainfall–soil correlation.
- Interactive two-district comparison with independent date and variable filters; gaps and insufficient coverage are explicit.
- JSON evidence export; field guide; source download; responsive layouts.
- Detective Assistant placeholder prepared for a later AI integration, with no fabricated chat replies.

## Python FastAPI service (optional deployment)

The hosted static preview calculates statistics in the browser. `backend/analysis.py` implements equivalent calculations in Python. The UI can call the real authenticated Python endpoint when configured. Comparison filters always recalculate locally for responsiveness.

From the project root:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Set backend environment variables using your host or terminal:

- `ALLOWED_ORIGINS=http://localhost:3000` (comma-separated exact origins for production).
- `GOOGLE_APPLICATION_CREDENTIALS` pointing to your backend-only Firebase service-account file, or use application-default credentials on your host.

Set `NEXT_PUBLIC_ANALYSIS_API_URL=http://localhost:8000` in `.env.local`, restart Next.js, and **sign in with Google**. The client sends a Firebase ID token to `POST /analyze`. The API verifies it with Firebase Admin and rejects missing/invalid tokens. Demo continues using local analysis.

`GET /health` is public. `POST /analyze` accepts:

```json
{"region":"Anuradhapura","variables":["rainfall","temperature","soil"],"start":"2004-01-01","end":"2024-12-31"}
```

The Python service is provided as runnable source, but is **not hosted by the static preview**. Deploy it on a Python-capable host and set the URL to use it remotely. Firestore storage is not added: the requested flow reads bundled datasets; investigation answers remain in memory until exported.

## Data and scientific interpretation

`data/raw/` preserves all three original CSVs. Regenerate the cleaned dataset with:

```bash
python scripts/prepare_data.py data/raw
```

The import produces `public/data/climate.json` (23,455 usable monthly observations) and `public/data/quality-report.json`.

- Rain: `GLDAS_NOAH025_M_2_1_Rainf_tavg`, original kg/m²/s → monthly mm using seconds per day × calendar days, summed for annual totals.
- Air temperature: `GLDAS_NOAH025_M_2_1_Tair_f_inst`, Kelvin → °C. This is air temperature, not land-surface temperature.
- Soil: `GLDAS_NOAH025_M_2_1_SoilMoi0_10cm_inst`, kg/m² in the upper 10 cm.
- Annual temperature/soil means are weighted by days per month.
- All 12 months must fall wholly within the chosen date interval. Partial months and partial years are excluded. No observations are interpolated.
- At least 5 complete years are required for a trend test. Five is a minimal exploratory threshold; longer records are preferable.
- District aliases are explicitly normalized, including ATale → Matale, Rathnapura → Ratnapura, and malformed Hambantota. A soil observation lacking a district is excluded, not silently assigned.
- Jaffna rainfall ends in November 2024; Colombo temperature has missing months; the UI reports the usable full-year coverage.
- The exports have one bounding-box metadata header for multiple district series. Administrative boundaries were not independently verified. Treat values as user-labeled area averages and verify regional source geometry before scientific reporting.
- Mann–Kendall uses tie-corrected variance and continuity correction, two-sided normal approximation, alpha = .05. Sen slope uses actual year intervals. Original Mann–Kendall is not adjusted for serial correlation or multiple testing. Residual lag-1 correlation is disclosed.
- Annual aggregation reduces the seasonal-cycle problem. Statistical significance is not causal proof; non-significance is not evidence of no change. Correlation is descriptive and may be affected by shared trends.
- The globe is context imagery, not historical imagery or a visualization of the selected climate values.

Source documentation: https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/README_GLDAS2.pdf

## Verification

```bash
npm test
python -m unittest backend.test_analysis -v
npm run build
```

Tests cover known monotonic series, tie handling, constant values, incomplete years, day-weighted leap-year means, and year-aligned correlation. The browser workflow was checked from demo entry through result cards and comparison filters. Firebase OAuth cannot be verified without your project configuration.

## Structure

- `app/page.tsx`: full guided experience and Firebase-aware navigation.
- `app/globals.css`: responsive blue/green design, motion and reduced-motion support.
- `components/Globe.tsx`: satellite sphere and spherical country selection.
- `components/Detective.tsx`: animated original SVG student character.
- `lib/analysis.ts`: browser statistics and annual aggregation.
- `lib/firebase.ts`: Firebase initialization and Google OAuth.
- `backend/`: authenticated FastAPI service and Python statistics/tests.
- `scripts/prepare_data.py`: reproducible CSV cleaning.
- `scripts/package_source.py`: downloadable source archive (excludes secrets and build outputs).

## Credits

Earth texture: Three.js examples planet Earth image, https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg (NASA-derived Earth imagery). Country polygons: Natural Earth via https://github.com/datasets/geo-countries, simplified for globe hit testing. Country boundaries are illustrative and not authoritative. Character artwork and interface graphics are original SVG/CSS. NASA data use does not imply NASA endorsement.

## Discovery atlas & Detective Assistant update

After completing an investigation, select **Discovered trends** on the analysis
page. All selected variables appear as individual findings, with filters for
statistical evidence and uncertain/flat results. The comparison lab includes
annual grouped bars, fitted OLS lines, district and date controls. The heat map
shows district-by-year standardized anomalies for the selected variable and period;
select a cell for its value and z-score. Colors are not significance tests.

The assistant now has a responsive chat interface, English/Sinhala prompts,
optional evidence attachment, authenticated requests, session continuity, loading
and recoverable error states. Set `NEXT_PUBLIC_AI_API_URL` and Firebase Web config,
then rebuild. The separately hosted Python service and its setup instructions are
in `ai-backend/README.md`. Until configured, the UI clearly explains that the
backend is not connected; it does not fabricate AI answers.
#   N A S A _ E A R T H T R A C E  
 