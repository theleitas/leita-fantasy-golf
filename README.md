# Leita Fantasy Golf

Separate Streamlit codebase for the golf fantasy draft app.

This project was created from the existing PGA Championship draft app as a separated copy, with the title changed to `Leita Fantasy Golf`.

## What Was Reused

- Streamlit single-file app structure.
- Existing draft board, snake draft logic, roster cards, standings cards, tournament leaderboard, admin controls, tournament selector, visual styling, and Twilio text update flow.
- Existing static team assets and copied `draft_state.json`.

## What Was Separated

- The app lives in its own folder: `leita-fantasy-golf`.
- The main app is its own file: `app.py`.
- The page title and visible header are now `Leita Fantasy Golf`.
- The GitHub repo target is now `leita-fantasy-golf`, not the old app repo.
- If no GitHub token is configured, state loads from and saves to this folder's local `draft_state.json`.

## Run

```bash
streamlit run app.py
```

## Files

- `app.py`: Streamlit app.
- `draft_state.json`: local state fallback and initial copied state.
- `requirements.txt`: Python dependencies.
- `jayme-pic.png`, `spencer-pic.png`, `peter-pic.png`, `pga-tour.png`, `thumb.png`: copied visual assets.

