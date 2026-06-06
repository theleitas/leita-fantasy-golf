# DeskCheck Golf Challenge

Separate Streamlit codebase for the golf fantasy draft app.

This project was created from the existing PGA Championship draft app as a separated Streamlit project.

## What Was Reused

- Streamlit single-file app structure.
- Draft board, snake draft logic, roster cards, standings cards, tournament leaderboard, admin controls, tournament selector, and visual styling concepts.
- Existing golf logo and thumbnail assets.

## What Was Separated

- The app lives in its own folder: `leita-fantasy-golf`.
- The main app is its own file: `app.py`.
- The visible header is customizable from Admin and defaults to `DeskCheck Golf Challenge`.
- The GitHub repo target is now `leita-fantasy-golf`, not the old app repo.
- If no GitHub token is configured, state loads from and saves to this folder's local `draft_state.json`.
- Text alert features were removed.
- The app is built for nine coaches and a 90-pick, 10-round snake draft.

## Run

```bash
streamlit run app.py
```

## iMessage Share Link

Use this GitHub Pages URL when sharing the app in iMessage:

```text
https://theleitas.github.io/leita-fantasy-golf/
```

That page supplies the preview thumbnail and then redirects visitors to the Streamlit app.

The preview image and the top app title image both come from the root-level `titlethumb.png` file.

## Files

- `app.py`: Streamlit app.
- `draft_state.json`: local state fallback and initial nine-coach state.
- `requirements.txt`: Python dependencies.
- `index.html`: GitHub Pages share preview for iMessage.
- `titlethumb.png`: shared title image and iMessage preview image.
- `pga-tour.png`: visual asset.
- Coach photos are expected as `CoachName.jpeg`, for example `McClure.jpeg`.
