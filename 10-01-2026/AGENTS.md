# AGENTS.md

## Project Context

This project is for EV battery CSR research, literature review, game theory/modeling work, and LaTeX manuscript development.

The project root is:

`c:\Users\u279014\OneDrive - Oshkosh Corporation-oskgovus\Documents\IIT\EV_Papers\CSR`

Important folders and files:

- `latex_code_active/`: active LaTeX manuscript line. Use this folder for manuscript inspection and edits unless the user explicitly redirects work.
- `latex_code_v2_inactive/`: inactive or archived LaTeX manuscript line. Use only for comparison unless the user explicitly reactivates it.
- `literatures_all/`: collected literature materials, including PDF files and `literature_list_v6.9.26.csv`.
- `literatures_all/literature_list_v6.9.26.csv`: primary literature synthesis list and coverage matrix.
- `weekly_meeting_notes/`: professor meeting update reports. Moving forward, weekly update summaries should be prepared in HTML format.
- `Game_Theory_in_CSR_Nathan.pdf`: core reference PDF for game theory in CSR.

Previously referenced Excel matrices are not currently visible in the project root. The retired `literature_list.csv` has been moved under `literatures_all/removed/` and should not be treated as the active synthesis source.

## Required Startup Routine

At the start of every session in this project:

1. Read `AGENTS.md`.
2. Read `PROJECT_LOG.md`.
3. Summarize the current project status.
4. Continue from the `Next Actions` section unless the user gives a newer instruction.

Recommended user prompt:

```text
Read AGENTS.md and PROJECT_LOG.md first. Summarize the current project status, then continue from Next Actions.
```

## Working Rules

- Do not delete, overwrite, rename, or reorganize PDFs, spreadsheets, or LaTeX source files unless explicitly asked.
- Before modifying any LaTeX manuscript, inspect `PROJECT_LOG.md` and use `latex_code_active/` as the active line unless a newer log entry or user instruction says otherwise.
- Preserve citation metadata, filenames, and source-paper traceability when editing literature notes or spreadsheets.
- Keep manuscript edits focused and explain any structural changes to the paper.
- Treat Codex memories as supplemental recall only. Important project status must be recorded in `PROJECT_LOG.md`.
- Before ending a substantial work session, update `PROJECT_LOG.md` with completed work, decisions, open questions, and next actions.

Recommended end-of-session user prompt:

```text
Update PROJECT_LOG.md with what changed, decisions made, open questions, and next actions.
```
