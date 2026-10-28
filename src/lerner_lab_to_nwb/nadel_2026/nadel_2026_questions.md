# aCUS intrinsic ephys: open questions

Questions about the data in `/Volumes/T7/CatalystNeuro/Lerner/aCUS_ephys_raw_for_NWB`, collected while reading Jacob's README (9/28/26), the tables in `tables/`, the preprint (Nadel et al., bioRxiv 2026.07.29.741478), and the Year 3 scope of work. Each entry records the status and, once answered, the answer and its source. Where the conversion had to proceed before an answer, "Current behavior" says what the code does now.

Items from the README's "don't have" list that the preprint methods already answer are recorded at the bottom so they can be confirmed in one pass.

## Scope

1. Is this dataset going to be published on DANDI? The scope of work uses it as the reference dataset for the slice ephys pipeline (Aim 3) and the DANDI aims cover the ASAP manuscript only. If it is published, should it be its own Dandiset, and should it be embargoed until the paper is accepted?
   Status: answered (Paul, 2026-10-28). Not uploaded to DANDI. The conversion is a local reference dataset for the slice ephys pipeline.

2. Which cells should be converted?
   - all 191 good cell folders in the main tree, or only the 160 paper cells
   - the timecourse tree (P40 vs P220, 62 cells), which is not in the preprint
   - the June 2026 PAG mouse (2006-151, 3 cells)
   - 610-005 (use=False), the 12 bead-negative 2023 cells, and the 10 cells dropped in QC
   - MZ's unfiled s1c3 recording in `607-009/pics`
   - the `bad/` folders (we would leave these out unless asked)
   Our default would be every good cell folder in both trees, with columns marking paper inclusion, bead status, and QC status, and nothing from `bad/` or `pics/`.
   Status: open. Paul asked for all of the slice ephys data. Current behavior: every good cell folder in both trees (253 cells), nothing from `bad/` or `pics/`.

3. The Sept 2023 runs held near -60 mV: the README says to exclude them, but the Zenodo bundle has `firing rate from -60.csv` and `rheobase from -60.csv`, which suggests they were analyzed. Should they be excluded from the NWB files or included and labeled as held at -60 mV with the holding current from the log? Either way we would identify them from the sweep ranges in the log, since nothing in the .h5 marks them. Can you confirm those log sweep ranges are reliable for this?
   Status: open. Current behavior: excluded, following the README. The excluded runs are listed in `nadel_2026_excluded_runs.csv` (144 files from 16 cells). Two parts of that list are our reading of the log and need a check:
   - `m011 s1c1`: the log's sweep numbers run 4 higher than the file names from the sag protocol on (the log has rheobase at 50-70, the file is `m011_0046-0066.h5`). We matched the held runs with the same shift, so the held set is `m011_0109.h5` through `m011_0201-0221.h5`.
   - `m009 s1c1`: the log says the third F-I run and the third rheobase run were done with +80 pA holding (to -60 mV). We excluded `m009_1027-1037.h5` and `m009_1112-1152.h5`.

4. Should the analysis outputs go in the NWB files? Candidates are the per-cell features in the Zenodo bundle (`ALL_INTRINSIC_EPHYS/analysis`), the SNL cluster labels (`metadata/clusters.csv`), and the paper inclusion list (`metadata/used cells.csv`). Our default would be cluster label and paper inclusion as per-cell metadata, with the feature tables left on Zenodo and linked.
   Status: open. Current behavior: the default above, with the Zenodo record linked in `related_publications`.

5. The per-cell slice images (`pics/*.tif`, 4.8 GB): do you want these included? They would go in each NWB file as images of the recorded cell.
   Status: open

6. The rest of the preprint (RI60 photometry, avoidance, Kir2.1, NpHR) is in the Zenodo bundle but not in this hand-off. We are treating it as out of scope for this conversion. Is that right?
   Status: open

## File structure

7. Jacob suggested one NWB file per mouse/day with one electrode per cell. That would put up to 13 cells in one file. The alternative is one file per cell, which makes per-cell download and analysis simpler on DANDI. Is there a preference?
   Status: open. Current behavior: one file per mouse/day, one electrode per cell.

8. The four ES recordings in 855-L (`m402 s1c1ES` to `s1c4ES`) were made on the other rig the same day. Is anything about that rig different (amplifier, DAQ, filter settings) beyond the experimenter?
   Status: open. Current behavior: the ES cells share the MultiClamp 700B and PCIe-6323 devices with Jacob's cells.

## Stimulus and channels

9. Plan for the stimulus: build it for every sweep from the stimulus library in the file header, and store the recorded command loopback as a separate trace only where it is valid (May 2024 onward, excluding the four ES folders and the two test pulses run in CC). For Sept 2023 the loopback would be left out. Does that match how you want it represented?
   Status: open. Current behavior: the stimulus is built from the library for every sweep, and the loopback is not written. Compared over all files, the loopback matches the library stimulus within ADC noise wherever it is valid, so it would duplicate the stimulus.

10. VC holding at -70 mV is set on the amplifier and is not in the file. We plan to store the voltage-clamp stimulus as absolute membrane potential (the -70 mV holding plus the step) and say so in the description. Is -70 mV correct for every VC run, including the test pulses and the Ih protocol, across all years?
   Status: open. Current behavior: the voltage clamp stimulus data are the steps relative to holding, with the series `offset` set to -70 mV, so `data * conversion + offset` is the absolute command.

11. Spont-firing runs done in VC (MZ's holding-current recordings, `m405 s1c1`) and the one I=0 run (`m401 s2c3`) will be stored according to the amplifier mode in the header, not the protocol name. Confirm that `m405 s1c1`'s VC spont run was also deliberate.
   Status: open. Current behavior: as described.

12. The stray `AJ_Ch1_VC_test pulse.cfg` file in `855-L/m402 s1c1ES` (20 kHz, 30 s): include it or drop it?
   Status: open. Current behavior: included as a voltage clamp response with no stimulus, since its stimulus map binds nothing to the output channel.

## Subjects

13. Dates of birth for the main-tree mice. Without them we can only give age as a range. The preprint says bead surgery was at P50-56 and the log says recordings were about 7 days later, which would put the main-tree recordings around P57-63. Are DOBs recoverable from colony records?
   Status: open. Current behavior: no age for the main-tree mice. NWB Inspector reports this as critical for the 32 main-tree files.

14. Timecourse mice: makeMice lists age 40 and 220. The preprint says P40 mice got beads at P40 and were recorded from P41. Should age at recording be P41 (and P221), or does "P40" in makeMice already mean the recording day?
   Status: open. Current behavior: P40D and P220D, from makeMice.

15. Surgery dates for each mouse, or the exact number of days between bead injection and recording.
   Status: open

16. Stress dates: is P28-P40 correct for every stressed mouse in this dataset, including the timecourse cohort?
   Status: open

17. 611-323 / m323: is the real ID 611-024? We will use makeMice as the source of truth for sex and ID unless told otherwise (README item 6). Confirm that the seven sex discrepancies in `subject_discrepancies.csv` all resolve to makeMice.
   Status: open

18. Strain: the preprint says WT mice were C57BL/6J from The Jackson Laboratory, bred in house. Does that apply to every mouse here?
   Status: open. Current behavior: C57BL/6J for every mouse. The strain is not linked to a registry entry, since the preprint does not give the JAX stock number. Is it JAX 000664?

19. Bead hemisphere: injections were bilateral, and the log's L/R column is empty for every cell. Is the recorded hemisphere recoverable for any cells (for example from the slice images), or should it be left unknown?
   Status: open

## Recording settings

20. Which MultiClamp settings file applies to which days? There are two snapshots (`ashley mc setup on 20230301.mcc` and `rig 2 mc setup on 2023 08 04.mcc`). We need the low-pass filter setting and whether bridge balance and pipette capacitance neutralization were on. The log has per-cell BB and P Neutr values, which suggests they were used despite the snapshot saying off.
   Status: open

21. Slice thickness was 250-300 µm in the preprint. Is the value per day recorded anywhere, or should we store the range?
   Status: open

22. Which internal was used each day? The log says "Kgluc for CC" for 2023 and "Mod Kgluc for CC" from 2024. Is the preprint recipe (130 K-gluconate, 15 KCl, 10 HEPES, 2 Mg-ATP, 1 EGTA, 0.3 Na-GTP) the modified one, and if so what was the 2023 recipe?
   Status: open

## People

23. Full names for the experimenters: JN is Jacob A. Nadel; is MZ Manhua Zhu and ES Evan S. Swanson? Can we get ORCIDs for each?
   Status: open. Current behavior: these names are used, without ORCIDs.

## Files

24. Misfiled `m009_` files in `607-009/m009 s3c1 - (mz_s2c1)`: we use the copies in `m009 s1c1 +` and skip the 12 duplicates in the MZ folder. `m009_0001-0003.h5` and `m009_0004.h5` exist only in the MZ folder, and per the README they are the start test pulse and spontaneous run of `m009 s1c1`, so they are written as runs of that cell. Confirm.
   Status: open

25. Sweep numbers repeat in two more cells than the README lists: in `20250310 758-L/m114 s2c2`, `m114_0422-0432.h5` (F-I) and `m114_0432-0434.h5` (test pulse) both hold sweep 432, and `m114_0433-0435.h5` overlaps both; in `20260401 862-R/m405 s1c1`, `m405_0001.h5` and `m405_0001-0003.h5` both hold sweep 1. Was the counter reset by hand in these cells? The run start times put the files in the order F-I, `0433-0435`, `0432-0434`, `0435-0437`.
   Status: open. Current behavior: every file is converted, and series names include the file name so they stay unique.

26. The log sheets have per-cell pipette resistance, access resistance, holding current, resting potential, and free-text notes, but the fields are sparse and inconsistently formatted. Do you want any of them in the files? The most useful would be pipette resistance and initial access resistance, which NWB has fields for.
   Status: open. Current behavior: not converted.

## Answered by the preprint methods (to confirm)

| Item | Value from the preprint |
|---|---|
| Amplifier | MultiClamp 700B (Molecular Devices) |
| DAQ | National Instruments PCIe-6323 with BNC-2090A breakout |
| Acquisition | WaveSurfer 0.945, 10 kHz |
| Temperature | 30-32 °C, inline heater, ~1.5 ml/min |
| Slices | coronal, 250-300 µm, Leica VT1200S, NMDG protective recovery |
| Internal | 130 K-gluconate, 15 KCl, 10 HEPES, 2 Mg-ATP, 1 EGTA, 0.3 Na-GTP (mM) |
| Bath drugs | D-AP5 50 µM, NBQX 5 µM, gabazine 10 µM |
| Pipettes | 3-7 MΩ, borosilicate (Warner G150TF-4), Narishige PC-100 |
| Beads | red Retrobeads (LumaFluor), 1:4 in saline, 250 nL |
| Strain | C57BL/6J (Jackson), bred in house |
| Time zone | America/Chicago (from `read_wavesurfer_example.py`) |
