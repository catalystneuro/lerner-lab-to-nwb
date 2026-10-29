# aCUS intrinsic ephys: decisions for the data curator

Decisions about the scope and design of the conversion of `/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB`. These are for the CatalystNeuro curator to make. Questions about the data itself, which the lab can answer, are in `nadel_2026_lab_questions.md`.

Open decisions say what the code does now under "Current behavior". Closed decisions record the decision, who made it, and when. Numbers stay with a decision when it moves from open to closed.

## Open

4\. The per-cell slice images (`pics/*.tif`, 4.8 GB) were left out of the hand-off. Should we ask Jacob for them and include them? They would go in each NWB file as images of the recorded cell.

Current behavior: not included.

5\. The rest of the preprint (RI60 photometry, avoidance, Kir2.1, NpHR) is in the Zenodo bundle but not in this hand-off. Is it out of scope for this conversion?

Current behavior: not converted.

6\. Jacob suggested one NWB file per mouse/day with one electrode per cell. That puts up to 12 cells in one file. The alternative is one file per cell, which makes per-cell download and analysis simpler.

Current behavior: one file per mouse/day, one electrode per cell.

7\. How should the stimulus be represented? Jacob suggested building it from the stimulus library in each file header and keeping the recorded command loopback as an extra trace where it is valid (May 2024 onward, excluding the two test pulses run in CC).

Current behavior: the stimulus is built from the library for every sweep, and the loopback is not written. Compared over all files, the loopback matches the library stimulus within ADC noise wherever it is valid, so it would duplicate the stimulus.

9\. The log sheets have per-cell pipette resistance, access resistance, holding current, resting potential, and free-text notes, but the fields are sparse and inconsistently formatted. Should any of them go in the files? The most useful would be pipette resistance and initial access resistance, which NWB has fields for. Converting them would mean cleaning the scraped values, possibly with Jacob's help.

Current behavior: not converted.

## Closed

1\. Is this dataset going to be published on DANDI?

Decision (Paul, 2026-10-28): no. The conversion is a local reference dataset for the slice ephys pipeline (Aim 3 of the scope of work), not uploaded to the DANDI sandbox or archive.

2\. Which cells should be converted?

Decision (Paul, 2026-10-29): only the cells in the preprint's figures, taken from the figures and not from `used cells.csv`, since that list does not match them. That is the 160 cells in `used cells.csv`, the 3 cells of the June 2026 PAG mouse (Fig. 2E and 2H), and the 35 P40 cells Jacob recorded (Fig. 2N), 198 cells listed with the evidence for each in `nadel_2026_paper_cells.csv`. Left out: 610-005, the bead-negative 2023 cells, the cells dropped in QC, the P220 cohort, ES's four P40 cells, `bad/`, and `pics/`. Whether this list matches the figures is lab question 18; the list stays as is until Jacob confirms.

8\. The stray `AJ_Ch1_VC_test pulse.cfg` file in `855-L/m402 s1c1ES`: include it or drop it?

Closed (2026-10-29): no longer needed. It belongs to one of ES's cells, which are not in the paper (decision 2).

3\. Should the analysis outputs go in the NWB files? Candidates are the per-cell features, clustering outputs, and spike waveforms in the Zenodo bundle (`aCUS_zenodo_bundle/ALL_INTRINSIC_EPHYS/analysis`).

Decision (Paul, 2026-10-29): no. They are not part of the raw data hand-off, and this conversion is a reference for the slice ephys pipeline, not the final conversion of this dataset. The SNL cluster label from `metadata/clusters.csv`, which is part of the hand-off, stays as a per-cell column, and the Zenodo record stays in `related_publications`.
