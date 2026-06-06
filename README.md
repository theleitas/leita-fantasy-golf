# Leita Fantasy Golf

Separate Streamlit codebase for the golf fantasy draft app.

This project was created from the existing PGA Championship draft app as a separated Streamlit project.

## What Was Reused

- Streamlit single-file app structure.
- Draft board, snake draft logic, roster cards, standings cards, tournament leaderboard, admin controls, tournament selector, and visual styling concepts.
- Existing golf logo and thumbnail assets.

## What Was Separated

- The app lives in its own folder: `leita-fantasy-golf`.
- The main app is its own file: `app.py`.
- The visible header is customizable from Admin and defaults to `Leita Fantasy Golf`.
- The GitHub repo target is now `leita-fantasy-golf`, not the old app repo.
- If no GitHub token is configured, state loads from and saves to this folder's local `draft_state.json`.
- Text alert features were removed.
- The app is built for nine coaches and a 90-pick, 10-round snake draft.

## Run

```bash
streamlit run app.py
```

## Files

- `app.py`: Streamlit app.
- `draft_state.json`: local state fallback and initial nine-coach state.
- `requirements.txt`: Python dependencies.
- `pga-tour.png`, `thumb.png`: visual assets.
- Coach photos are expected as `CoachName.jpeg`, for example `McClure.jpeg`.
