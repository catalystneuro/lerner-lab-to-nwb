# aCUS intrinsic ephys: decisions for the data curator

Decisions about the scope and design of the conversion of `/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB`. These are for the CatalystNeuro curator to make. Questions about the data itself, which the lab can answer, are in `nadel_2026_lab_questions.md`.

Each entry records the status and, once decided, the decision and who made it. Where the conversion had to proceed before a decision, "Current behavior" says what the code does now.

## Scope

1. Is this dataset going to be published on DANDI? The scope of work uses it as the reference dataset for the slice ephys pipeline (Aim 3) and the DANDI aims cover the ASAP manuscript only. If it is published, should it be its own Dandiset, and should it be embargoed until the paper is accepted?
   Status: decided (Paul, 2026-10-28). Not uploaded to DANDI. The conversion is a local reference dataset for the slice ephys pipeline.

2. Which cells should be converted?
   - all 191 good cell folders in the main tree, or only the 160 paper cells
   - the timecourse tree (P40 vs P220, 62 cells), which is not in the preprint
   - the June 2026 PAG mouse (2006-151, 3 cells)
   - 610-005 (use=False), the 12 bead-negative 2023 cells, and the 10 cells dropped in QC
   - MZ's unfiled s1c3 recording in `607-009/pics`
   - the `bad/` folders
   Status: decided (Paul, 2026-10-28): convert all of the slice ephys data. Current behavior: every good cell folder in both trees (253 cells), with columns marking paper inclusion, bead status, and cluster, and nothing from `bad/` or `pics/`.

3. Should the analysis outputs go in the NWB files? Candidates are the per-cell features in the Zenodo bundle (`ALL_INTRINSIC_EPHYS/analysis`), the SNL cluster labels (`metadata/clusters.csv`), and the paper inclusion list (`metadata/used cells.csv`).
   Status: open. Current behavior: cluster label and paper inclusion are per-cell metadata, the feature tables stay on Zenodo, and the Zenodo record is linked in `related_publications`.

4. The per-cell slice images (`pics/*.tif`, 4.8 GB) were left out of the hand-off. Should we ask Jacob for them and include them? They would go in each NWB file as images of the recorded cell.
   Status: open. Current behavior: not included.

5. The rest of the preprint (RI60 photometry, avoidance, Kir2.1, NpHR) is in the Zenodo bundle but not in this hand-off. Is it out of scope for this conversion?
   Status: open. Current behavior: not converted.

## File structure

6. Jacob suggested one NWB file per mouse/day with one electrode per cell. That puts up to 13 cells in one file. The alternative is one file per cell, which makes per-cell download and analysis simpler.
   Status: open. Current behavior: one file per mouse/day, one electrode per cell.

## Stimulus and channels

7. How should the stimulus be represented? Jacob suggested building it from the stimulus library in each file header and keeping the recorded command loopback as an extra trace where it is valid (May 2024 onward, excluding the four ES folders and the two test pulses run in CC).
   Status: open. Current behavior: the stimulus is built from the library for every sweep, and the loopback is not written. Compared over all files, the loopback matches the library stimulus within ADC noise wherever it is valid, so it would duplicate the stimulus.

8. The stray `AJ_Ch1_VC_test pulse.cfg` file in `855-L/m402 s1c1ES` (20 kHz, 30 s, someone else's protocol): include it or drop it?
   Status: open. Current behavior: included as a voltage clamp response with no stimulus, since its stimulus map binds nothing to the output channel.

## Metadata

9. The log sheets have per-cell pipette resistance, access resistance, holding current, resting potential, and free-text notes, but the fields are sparse and inconsistently formatted. Should any of them go in the files? The most useful would be pipette resistance and initial access resistance, which NWB has fields for. Converting them would mean cleaning the scraped values, possibly with Jacob's help.
   Status: open. Current behavior: not converted.
