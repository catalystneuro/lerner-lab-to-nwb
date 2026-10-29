# aCUS intrinsic ephys: decisions for the data curator

Decisions about the scope and design of the conversion of `/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB`. These are for the CatalystNeuro curator to make. Questions about the data itself, which the lab can answer, are in `nadel_2026_lab_questions.md`.

Open decisions say what the code does now under "Current behavior". Closed decisions record the decision, who made it, and when. Numbers stay with a decision when it moves from open to closed.

## Open

## Closed

1\. Is this dataset going to be published on DANDI?

Decision (Paul, 2026-10-28): no. The conversion is a local reference dataset for the slice ephys pipeline (Aim 3 of the scope of work), not uploaded to the DANDI sandbox or archive.

2\. Which cells should be converted?

Decision (Paul, 2026-10-29): only the cells in the preprint's figures, taken from the figures and not from `used cells.csv`, since that list does not match them. That is the 160 cells in `used cells.csv`, the 3 cells of the June 2026 PAG mouse (Fig. 2E and 2H), and the 35 P40 cells Jacob recorded (Fig. 2N), 198 cells listed with the evidence for each in `nadel_2026_paper_cells.csv`. Left out: 610-005, the bead-negative 2023 cells, the cells dropped in QC, the P220 cohort, ES's four P40 cells, `bad/`, and `pics/`. Whether this list matches the figures is lab question 18; the list stays as is until Jacob confirms.

8\. The stray `AJ_Ch1_VC_test pulse.cfg` file in `855-L/m402 s1c1ES`: include it or drop it?

Closed (2026-10-29): no longer needed. It belongs to one of ES's cells, which are not in the paper (decision 2).

3\. Should the analysis outputs go in the NWB files? Candidates are the per-cell features, clustering outputs, and spike waveforms in the Zenodo bundle (`aCUS_zenodo_bundle/ALL_INTRINSIC_EPHYS/analysis`).

Decision (Paul, 2026-10-29): no. They are not part of the raw data hand-off, and this conversion is a reference for the slice ephys pipeline, not the final conversion of this dataset. The SNL cluster label from `metadata/clusters.csv`, which is part of the hand-off, stays as a per-cell column, and the Zenodo record stays in `related_publications`.

4\. Should we ask Jacob for the per-cell slice images (`pics/*.tif`, 4.8 GB) and include them?

Decision (Paul, 2026-10-29): no. The conversion covers the data in the hand-off, and the images were left out of it.

5\. Should the rest of the preprint (RI60 photometry, avoidance, Kir2.1, NpHR) be converted?

Decision (Paul, 2026-10-29): no. The scope is the slice ephys data for the lab's ephys pipeline.

6\. One NWB file per mouse/day, or one file per cell?

Decision (Paul, 2026-10-29): one file per mouse/day, with one electrode per cell, which is the usual NWB organization.

7\. How should the stimulus be represented? Jacob suggested building it from the stimulus library in each file header and keeping the recorded command loopback as an extra trace where it is valid.

Decision (Paul, 2026-10-29): include both. The waveform built from the stimulus library is the stimulus template for every run, and the recorded loopback is the delivered stimulus for every run that has one. Jacob's Sept 2023 runs have no loopback, because their second analog input recorded the membrane potential instead (lab question 19), so those runs have a template only.

9\. Should the log sheet fields go in the files?

Decision (Paul, 2026-10-29): yes, for every cell and day that has them, extracted from the three Excel log sheets directly instead of Jacob's scraped CSVs, to recover more of the entries and handle the inconsistent formatting. Entries that hold two readings are kept as text, exactly as written, and ambiguous entries are left blank instead of guessed. The free-text notes wait on lab question 20.
