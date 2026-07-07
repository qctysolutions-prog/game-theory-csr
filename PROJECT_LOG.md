# PROJECT_LOG.md

This file is the durable project checkpoint for Codex sessions. Update it before ending substantial work so the project can be continued without searching task history.

## Current Objective

Organize EV battery CSR and game theory/modeling literature, maintain the literature matrices, and continue developing the LaTeX manuscript.

## Last Completed

- Created project-level Codex memory setup with `AGENTS.md` and `PROJECT_LOG.md`.
- Confirmed this project root is already trusted in the Codex configuration.
- Confirmed Codex memories are enabled globally, but project continuity should rely on this file.
- Confirmed on 2026-06-07 that `latex_code_active/` is the active manuscript line and `latex_code_v2_inactive/` is inactive/archive material.
- Confirmed on 2026-06-09 that `literatures_all/literature_list_v6.9.26.csv` is the primary literature synthesis list and coverage matrix.
- Completed a read-only reconciliation checkpoint on 2026-06-23 between `literatures_all/literature_list_v6.9.26.csv`, `latex_code_active/Bib.bib`, and active LaTeX citations; details are in `literatures_all/literature_bib_reconciliation_2026-06-23.md`.
- Revised Chapter 3 v1.3 on 2026-06-23 to center the model narrative on CSR governance between the manufacturer and retailer, while preserving the existing closed-form formulas and proposition labels.
- Merged the 2026-06-23 Chapter 3 CSR-governance rewrite into the professor-reviewed Chapter 3 file and preserved the professor's generalized product-channel wording where it improved the model framing.
- Revised the root-level professor-reviewed Chapter 3 file on 2026-06-23 so it now treats the analytical model as a general CSR Manufacturer--Retailer coordination model, with EV battery recycling retained as a late-stage use case.
- Created `weekly_meeting_notes/2026-06-23_professor_meeting_update.html` as the HTML weekly update report for the June 23 professor meeting.
- Revised the active Chapter 3 v1.3 organization sentence on 2026-06-26 so the early model setup avoids explicit EV battery/recycling language before the late applied use-case subsection.
- Revised Chapter 4 v1.2 on 2026-07-05 as a CSR-first multi-retailer reverse-logistics study with EV battery recycling as the U.S. case application; added coalition-dependent MILP, Shapley cost allocation, participation/core checks, and U.S. EPA support citations.
- Revised the Chapter 4 v1.3 literature-gap section on 2026-07-05 to foreground CSR design, distributed responsibility, and cost-sharing governance; updated `main.tex` to include the existing Chapter 4 v1.3 file.
- Revised the dissertation title in `latex_code_active/main.tex` on 2026-07-05 to make CSR-driven supply-chain governance the primary subject and EV battery recycling the applied context.

## Next Actions

1. Use `literatures_all/literature_list_v6.9.26.csv` as the primary literature synthesis source. It currently has 44 records and represents all 41 local PDFs in `literatures_all/`.
2. Use `literatures_all/literature_bib_reconciliation_2026-06-23.md` to clean up the bibliography/matrix alignment: add or verify BibTeX entries for CSV rows that lack strong BibTeX matches, normalize shortened BibTeX titles, and decide whether cited support sources should be added to the matrix.
3. Review the updated Chapter 3 v1.3 CSR-governance framing and decide whether a later formula-level redesign is needed; no contradiction requiring new parameters was found in the 2026-06-23 rewrite pass.
4. Continue manuscript work in `latex_code_active/`, especially Chapter 2 literature synthesis and any summary tables that connect CSR, EV battery recycling, game theory, reverse logistics, EPR, and Shapley/cost-sharing themes.
5. Before relying on a full manuscript build, fix the existing Chapter 2 LaTeX issue where a literal path with underscores in `chp2_literature_review_v1.2.tex` causes `Missing $ inserted` before Chapter 3 is reached.
6. Decide which Chapter 3 file should become the active `main.tex` include after reviewing the merged professor-reviewed version: `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3.tex` or `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3_professsor_reviewed.tex`.
7. Decide whether to move or copy the root-level professor-reviewed Chapter 3 file into `latex_code_active/` and update `main.tex`; the current edited target is `chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3_professsor_reviewed.tex` in the project root because that is the file currently present/opened.
8. Review Chapter 4 v1.3 for professor-facing fit: the current numerical U.S. case is internally consistent and illustrative, but a later pass should decide whether to back it with a reproducible solver appendix or calibrated data.

## Open Questions

- No active open literature-source questions as of 2026-06-09. The previous questions were answered: the retired `literature_list.csv` is no longer active, `literature_list_v6.9.26.csv` is the primary synthesis source, and local verification found no newer local PDF or note files outside that matrix.

## Important Decisions

- Use `AGENTS.md` for stable Codex project instructions.
- Use `PROJECT_LOG.md` for session-to-session continuity.
- Do not rely on Codex task history as the primary project memory.
- Treat Codex memories as supplemental recall only.
- Use `latex_code_active/` as the active manuscript line unless the user gives a newer instruction.
- Use `literatures_all/literature_list_v6.9.26.csv` as the primary literature synthesis source. Do not use `literatures_all/removed/literature_list.csv` except for historical comparison.
- Use HTML format for weekly professor update summaries in `weekly_meeting_notes/`; `PROJECT_LOG.md` remains the durable project checkpoint.

## Session Notes

### 2026-07-07

- Read project instructions and continued on the active LaTeX line in `latex_code_active/`.
- Implemented the Chapter 4 v1.3 modeling expansion requested by the user, keeping CSR governance as the theoretical focus and EV battery recycling as the U.S. application setting.
- Expanded Phase I, `Coalition-Dependent CSR Network Optimization`, with a coalition CSR capability vector `G(S)=(\tau(S),\eta(S),\kappa(S))`, traceability/leakage constraints, due-diligence processor eligibility, coalition-dependent processing/recovery/governance terms, CSR performance measures, sensitivity logic, and propositions with proofs for feasibility, governance value, processor thresholds, conditional subadditivity, and average-cost behavior.
- Expanded Phase II, `Cooperative CSR Cost Sharing`, with explicit cost-game and savings-game formulations, Shapley savings interpretation, marginal-contribution decomposition, core slack and stability margin, hybrid CSR responsibility allocation, constrained Shapley projection, least-core relaxation, and Manufacturer support/subsidy formulation.
- Replaced the compact analytical-properties section with deeper propositions and interpretations covering Shapley efficiency, non-automatic individual rationality, core-stability dependence on the Phase I cost function, hybrid-rule efficiency, and nonlinear allocation responses to governance thresholds.
- Added model-supporting visuals and tables in Chapter 4: CSR governance parameter-effect diagram, governance parameter table, technology/governance logic table, analytical findings table, allocation-rule comparison table, expanded sensitivity table, and pgfplots charts for traceability/due-diligence sensitivity, recovery-value/CSR-pressure sensitivity, and allocation-rule stability slack.
- Updated the Chapter 4 case-study discussion and conclusion to use net CSR stewardship cost, traceability, due diligence, collaboration, processor eligibility, stability slack, constrained allocation, and Manufacturer support language.
- Verification: static Chapter 4 checks found no duplicate labels, no missing Chapter 4 citation keys in `Bib.bib`, and no unresolved `\ref`/`\eqref` targets against active LaTeX labels.
- Verification: focused `pdflatex` with `\includeonly{chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.3}` reached `Output written on main.pdf` after fixing a TikZ style-name conflict; the command still returned nonzero because MiKTeX cannot write its user log under `AppData`.
- Verification note: `bibtex main` could not refresh the bibliography in the include-only build state because `main.aux` references missing `chp5_conclusion_v1.2.aux` and `appendix_chapter3_detailed_proofs_v1.2.aux`; full build remains subject to the previously known Chapter 2 underscore-path blocker unless that source issue is fixed.

### 2026-07-05

- Read `AGENTS.md` and `PROJECT_LOG.md` at session start and followed the active-line rule for `latex_code_active/`.
- Reviewed the archived Chapter 3 v1.3 file linked by the user and the active Chapter 4 v1.2 file to design the Chapter 3-to-Chapter 4 transition.
- Revised `latex_code_active/chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.2.tex` as a CSR-first Chapter 4 study: CSR governance is now the theoretical focus, while EV battery recycling is the U.S. case application.
- Added an explicit transition from Chapter 3's bilateral Manufacturer--Retailer CSR maturity game to Chapter 4's multi-retailer shared CSR reverse-logistics infrastructure.
- Added a literature-gap section connecting MILP/reverse-logistics studies with cooperative-game/Shapley cost-sharing studies.
- Rebuilt the Chapter 4 methodology around a coalition-dependent MILP that defines net CSR compliance cost `c(S)` and feeds the cooperative cost game.
- Corrected the cooperative-game claims: Shapley efficiency is proven, subadditivity is conditional, and individual rationality/core stability are stated as checks rather than universal guarantees.
- Replaced the prior Guangdong case with a stylized U.S. EV battery recycling case using five retailer regions: California/West Coast, Texas/South Central, Michigan/Midwest, Georgia/Southeast, and New York--New Jersey/Northeast.
- Added internally consistent illustrative Shapley, stand-alone savings, and selected core-stability tables; arithmetic checks confirmed Shapley allocations sum to `c(N)=4,093` and the selected core slacks are positive.
- Added EPA web-source BibTeX entries `EPA2026UsedLithiumIon` and `EPA2026UniversalWaste` to `latex_code_active/Bib.bib` to support the U.S. case motivation.
- Updated `latex_code_active/main.tex` to load `natbib` in numeric mode (`\usepackage[numbers]{natbib}`), matching the existing `ieeetr` bibliography style and avoiding the author-year/numeric style conflict.
- Verification: static citation check found no missing Chapter 4 citation keys; static reference check found no missing Chapter 4 labels after removing a dependency on the Chapter 2 chapter label; duplicate-label scan found no duplicates in Chapter 4.
- Verification: focused `pdflatex` with `\includeonly{chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.2}` reached `Output written on main.pdf`; the command still returned nonzero because MiKTeX could not write its user log under `AppData`.
- Verification: full `pdflatex main.tex` still stops before Chapter 4 at the known Chapter 2 issue: a literal underscored path in `chp2_literature_review_v1.2.tex` causes `Missing $ inserted`.
- Later on 2026-07-05, found that the active Chapter 4 source present in `latex_code_active/` is `chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.3.tex`; `main.tex` still referenced missing v1.2 and was updated to include v1.3.
- Rewrote Chapter 4 v1.3 `\section{Literature-Based Research Gap}` so it begins with CSR as strategic supply-chain governance and operational responsibility, then moves to CSR network design, cooperative cost sharing, and finally EV battery recycling as the applied setting.
- The revised literature-gap section now uses CSR/governance citations first (`Buccella2024`, `FantiBuccella2017`, `Ferrara2017`, `Khosroshahi2019`, `Mahdiraji2023`, `ZhangLiang2023`, `ZhengB2022`), cooperative allocation citations second, and EV battery/reverse-logistics citations only as applied support.
- Verification: static Chapter 4 v1.3 citation-key check found no missing keys; `main.tex` points to Chapter 4 v1.3; duplicate-label scan found no duplicates in Chapter 4 v1.3.
- Verification: focused `pdflatex` with `\includeonly{chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.3}` reached `Output written on main.pdf`; the command still returned nonzero because MiKTeX could not write its user log under `AppData`. Include-only bibliography warnings remain until BibTeX/full build state is refreshed, and full build remains blocked by the Chapter 2 underscore-path issue.
- Updated the dissertation title from `Eclectic-Vehicle Battery Recycling Supply Chains: Strategic Coordination, Power Dynamics, and Cooperative Cost Sharing` to `CSR-Driven Supply Chain Governance for EV Battery Recycling: Strategic Coordination, Network Design, and Cooperative Cost Sharing`. Static search found no old-title residue in active LaTeX files.

### 2026-06-26

- Read `AGENTS.md` and `PROJECT_LOG.md` at session start.
- Reviewed prior weekly professor meeting updates in `weekly_meeting_notes/`, especially the June 9 and June 16 HTML reports, to keep the new update format consistent.
- Created `weekly_meeting_notes/2026-06-23_professor_meeting_update.html` for this week's professor discussion.
- The new update summarizes the Chapter 3 CSR-governance rewrite, professor-reviewed Chapter 3 merge, EV battery use-case repositioning, bibliography/matrix reconciliation checkpoint, verification completed, professor discussion points, risks, and next actions.
- Revised `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3.tex` so the chapter organization paragraph refers only to an applied product-stewardship use case before the model setup, rather than naming EV battery take-back and recycling early.
- Verified that explicit EV, battery, electric, recycling, and take-back terminology in the active Chapter 3 v1.3 file now begins only at the late use-case subsection `sec:ch3_csr_usecase`.
- No PDFs or spreadsheets were modified in this session.

### 2026-06-23

- Read `AGENTS.md` and `PROJECT_LOG.md` at session start and continued from the logged Next Actions.
- Performed a read-only reconciliation of `literatures_all/literature_list_v6.9.26.csv`, `latex_code_active/Bib.bib`, and active citations in `latex_code_active/*.tex`.
- Confirmed the CSV still has 44 rows, `Bib.bib` has 45 entries, active LaTeX files cite 25 BibTeX keys, and there are no active LaTeX citation keys missing from `Bib.bib`.
- Created `literatures_all/literature_bib_reconciliation_2026-06-23.md` documenting likely CSV rows needing BibTeX entries, shortened BibTeX title metadata to normalize, duplicate BibTeX candidates, and BibTeX-only support/web sources.
- Identified likely duplicate BibTeX pairs: `Hao2022`/`mdpi2022reward` and `ZhengXu2023`/`zheng2023optimizing`; no BibTeX cleanup was performed in this pass.
- Identified two cited support sources not strongly matched to the CSV matrix, `tadaros2022location` and `wang2023collaborative`, for later decision on whether to add them to the literature matrix.
- Implemented the Chapter 3 CSR-centered revision in `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3.tex`.
- Reframed the chapter introduction, model primitives, VN/MS/RS/IN interpretations, sensitivity-analysis discussion, cross-regime tables, and Stage-0 meta-game around CSR governance, CSR maturity `s`, CSR pull `\beta`, cost curvature `\gamma`, retailer cost burden, manufacturer benefit, and coordination choice.
- Moved the `Use Case: CSR-Driven EV Battery Take-Back and Recycling` subsection from the model-primitives area to the end of the Stage-0 section immediately before the Chapter 3 conclusion.
- Added a new TikZ governance-use-case figure labeled `fig:ch3_csr_governance_usecase`, showing Stage-0 `C`/`L` choices mapping to IN/MS/RS/VN and then to CSR take-back outcomes.
- Preserved the existing closed-form equilibrium formulas, proposition labels, and core mathematical structure; no formula-level contradiction requiring new model parameters was found during this rewrite pass.
- Verification: label scan found no duplicate labels; `sec:ch3_csr_usecase` and `fig:ch3_csr_governance_usecase` are present once; the use-case subsection appears immediately before `\section{Conclusion}`.
- Verification: full `pdflatex main.tex` still stops before Chapter 3 at an existing Chapter 2 issue, `Missing $ inserted` from a literal underscored path in `chp2_literature_review_v1.2.tex`.
- Verification: `latexmk -pdf main.tex` could not launch because Windows/MiKTeX returned `Access is denied` for `latexmk.exe`, even with escalated execution.
- Verification: `pdflatex` with `\includeonly{chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3}` reached `Output written on main.pdf` and wrote Chapter 3 labels to the auxiliary file; the process still returned nonzero because MiKTeX could not write its own user log under `AppData`.
- Merged the same CSR-centered Chapter 3 rewrite into `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3_professsor_reviewed.tex`, while retaining the professor's useful generalized supply-chain wording: a single Manufacturer sells a product to a single Retailer, who then sells the same product to consumers.
- Revised the professor-reviewed Chapter 3 file so the model is framed as a general CSR Manufacturer--Retailer coordination problem; EV battery take-back and recycling language is retained only in the late-stage use-case subsection and the organization sentence that introduces that subsection.
- Applied the capitalization rule for the modeled firms by using `Manufacturer` and `Retailer` when they appear as the named channel actors or in modeled leadership regimes.
- Verification: duplicate-label scan found no duplicate labels in the professor-reviewed Chapter 3 file; `sec:ch3_csr_usecase` and `fig:ch3_csr_governance_usecase` appear once; the use-case subsection appears immediately before `\section{Conclusion}`.
- Verification: a lightweight command-line `pdflatex` wrapper reached the professor-reviewed Chapter 3 content without edited-source syntax errors, but MiKTeX failed at font/log generation (`tcrm1200` and AppData access). Temporary `prof_reviewed_check.*` build artifacts could not be deleted afterward because Windows returned access denied.
- Installed the OpenAI curated `jupyter-notebook` Codex skill for future economic research, model-checking, simulation, and notebook-based analysis workflows. Codex must be restarted before the new skill is automatically available.
- Revised the root-level `chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3_professsor_reviewed.tex` file as the current working target. The file now frames the chapter opening, model primitives, VN/MS/RS/IN regimes, sensitivity analysis, cross-regime comparisons, Stage-0 game, and conclusion around general CSR governance rather than EV battery recycling.
- Removed the early use-case placement from the model-primitives section and inserted `\subsection{Use Case: CSR-Driven EV Battery Take-Back and Recycling}` immediately before `\section{Conclusion}`.
- Added a TikZ governance figure labeled `fig:ch3_csr_governance_usecase`, mapping Stage-0 choices `C`/`L` to IN/MS/RS/VN and then to take-back outcomes such as CSR maturity, consumer trust, demand, price, and profit allocation.
- Strengthened reader-facing explanations around propositions, first-order conditions, sensitivity figures, and cross-regime tables so the equations are interpreted as CSR Manufacturer--Retailer governance results rather than textbook-style formula listings.
- Applied the modeled-firm capitalization rule by using `Manufacturer` and `Retailer` when referring to the single modeled channel actors; generic compound terms such as `multi-retailer` remain lowercase.
- Verification: static scan found no duplicate labels; `sec:ch3_csr_usecase` and `fig:ch3_csr_governance_usecase` each appear once; the use-case subsection appears before the conclusion; searches for `CSR-recycling`, `recycling maturity`, `recycling-cost`, and old title residue found no model-body leftovers.

### 2026-06-16

- Applied approved Chapter 3 CSR-first revision to `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.3.tex`.
- Retitled Chapter 3 around CSR-driven manufacturer--retailer coordination and rewrote the opening to frame EV battery recycling as the applied use case rather than the primary research identity.
- Rewrote Assumption 6 in prose, removed the regime-validity table, and clarified that cross-regime comparisons use the tighter common domain `2\alpha\gamma-\beta^2>0` (`0<x<2`) while RS alone remains valid under `4\alpha\gamma-\beta^2>0` (`0<x<4`).
- Added reader-oriented lead-in text before the VN, MS, RS, and IN propositions without changing mathematical formulas or citations.
- Removed unreferenced equation labels from the v1.3 Chapter 3 file while preserving labels still referenced by Chapter 3 or the active appendix.
- Updated `latex_code_active/main.tex` to include the v1.3 Chapter 3 file.
- Created `weekly_meeting_notes/2026-06-16_professor_meeting_update.html` as the HTML weekly update report for the June 16 professor meeting.
- Cleaned Chapter 3 v1.3 equation numbering by converting unreferenced `equation` and `align` environments to `equation*` and `align*`; only actively cited equation labels remain numbered.

### 2026-06-09

- Updated `AGENTS.md` and this log to make `literatures_all/literature_list_v6.9.26.csv` the active primary literature synthesis source.
- Verified local literature coverage: `literature_list_v6.9.26.csv` has 44 records; `literatures_all/` has 41 local PDFs; all 41 local PDFs are represented in the CSV; no listed PDF filename is missing locally.
- Verified there are 6 CSV-only/no-local-PDF rows in `literature_list_v6.9.26.csv`; these are reflected in the matrix but do not currently have matching local PDF files.
- Verified no local literature PDF or note file appears newer than `literature_list_v6.9.26.csv`; only manuscript/log files changed afterward.
- Counted 45 entries in `latex_code_active/Bib.bib`; next reconciliation should focus on BibTeX-only or non-paper support sources rather than missing local PDFs.
- Created `weekly_meeting_notes/2026-06-09_professor_meeting_update.md` for the Tuesday professor meeting, summarizing June 6--9 progress, discussion points, blockers, and Friday follow-up items.
- Created `weekly_meeting_notes/2026-06-09_professor_meeting_update.html` as the HTML weekly update report and recorded HTML as the preferred format for future weekly professor summaries.

### 2026-06-07

- Read `AGENTS.md` and `PROJECT_LOG.md` at session start.
- Found that the actual LaTeX folders are `latex_code_active/` and `latex_code_v2_inactive/`, not the older names `latex_code/` and `latex_code_v2/`.
- Updated `AGENTS.md` to reflect the current directory structure and active manuscript line.
- Found no `.xlsx` files under the current project root. The current visible literature synthesis file is `literatures_all/literature_list.csv`.
- Current coverage snapshot: 29 CSV literature records, 41 PDF files in `literatures_all/`, and 39 BibTeX entries in `latex_code_active/Bib.bib`.
- Chapter 2 in `latex_code_active/chp2_literature_review.tex` already has sections for EV battery recycling/CLSCs, EPR policy, reverse logistics/MILP, cooperative game theory/Shapley value, and research gaps.
- Heuristic title matching found 14 PDFs that may not be represented in `literature_list.csv`, 6 CSV rows that may not have matching local PDF filenames, 7 CSV rows that may not match BibTeX titles, and 17 BibTeX entries that may not match CSV titles.
- Next concrete work should be a literature coverage reconciliation table before making larger Chapter 2 changes.
- Implemented the literature-review update plan: rewrote Chapter 2 around two study focuses and four model blocks; reframed Chapter 3 as CSR-driven EV battery recycling while preserving the mathematical model; added a CSR-driven EV battery take-back use-case subsection; lightly aligned Chapter 1 and the abstract.
- Added BibTeX entries for newly cited CSR/game-theory papers used in Chapter 2.
- Generated an expanded literature coverage matrix at `literatures_all/literature_list.tmp.csv` with 44 rows and 26 columns. It represents all 41 PDFs and has category columns restricted to `X` or blank.
- Could not overwrite `literatures_all/literature_list.csv` because Windows reported the file is being used by another process. Close the open CSV tab/application, then replace it with `literatures_all/literature_list.tmp.csv`.
- LaTeX build was attempted with `latexmk -pdf main.tex`, but the existing template failed at `\degree` under the `report` document class before reaching the updated chapters. Citation-key validation passed separately.
- Rewrote Chapter 1 to make CSR supply-chain coordination the primary research identity and EV battery recycling the applied case study. The new Chapter 1 connects Chapter 2's study-aligned literature review, Chapter 3's CSR-driven bilateral game and stage-0 meta-game, Chapter 4's MILP/Shapley reverse-logistics model, and Chapter 5's synthesis role.
- Renamed the active included chapter/appendix LaTeX source files in `latex_code_active/` to the `_v1.2.tex` naming convention and updated `latex_code_active/main.tex` `\include{...}` references accordingly. `main.tex`, `Bib.bib`, and generated build files were not renamed.
- Revised Chapter 3 regularity-condition framing in `latex_code_active/chp3_models_manufacturer_retailer_dynamics_in_ev_battery_recycling_v1.2.tex` and its appendix. The chapter now distinguishes denominator positivity from second-order sufficiency, states VN/MS/IN on `2\alpha\gamma-\beta^2>0`, states RS on `4\alpha\gamma-\beta^2>0`, keeps cross-regime and stage-0 comparisons on `0<x<2`, and notes the standalone RS-valid range `2<x<4`.
- Re-ran `latexmk -pdf main.tex`; the build still stops before Chapter 3 at the unrelated `\degree{PhD of Management Science}` title-page command in `main.tex` under the current `report` class setup.

### 2026-06-06

- Initialized project memory setup for the `CSR` project root.
- Added startup and end-of-session routines for future Codex work.
- Next session should begin by reading `AGENTS.md` and this file, then continue from `Next Actions`.
