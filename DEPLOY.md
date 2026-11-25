# Public deployment (Streamlit Community Cloud, free)

The app needs no secrets and no database, so it can run on Streamlit Community Cloud.

1. Make sure this repository is **public** (GitHub → Settings → General → Danger Zone → Change visibility).
2. Open https://share.streamlit.io and sign in with the GitHub account `eerier79`.
3. Click **Create app** → **Deploy a public app from GitHub**.
4. Repository: `eerier79/evacuation-ai-assistant`, branch: `main`, main file: `app.py`.
5. Optional: choose a short app URL, for example `kitty-escape`.
6. Click **Deploy**. The first start installs `requirements.txt` and takes a few minutes.

After that, every push to `main` updates the app. Put the public link at the top of `README.md`.

Notes
- The Evaluation page simulates thousands of fires; the first visit takes about 10 seconds, later visits use the cache.
- The Q-learning tab trains only when you press **Train Q-learning**.
