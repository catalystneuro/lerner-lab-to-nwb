# aCUS intrinsic ephys: questions for the lab

Questions about the data in `aCUS_ephys_raw_for_NWB`, collected while reading Jacob's README (9/28/26), the tables in `tables/`, the preprint (Nadel et al., bioRxiv 2026.07.29.741478), and the data files. Most are for Jacob. Each entry records the status and, once answered, the answer and its source. Where the conversion had to proceed before an answer, "Current behavior" says what the code does now.

Items from the README's "don't have" list that the preprint methods already answer are at the bottom so they can be confirmed in one pass.

## Runs and files

1. The Sept 2023 runs held near -60 mV: the README says to exclude them, but the Zenodo bundle has `firing rate from -60.csv` and `rheobase from -60.csv`, which suggests they were analyzed. Should they still be left out of the NWB files? Nothing in the .h5 files marks them, so we identified them from the sweep ranges in the log. Are those ranges reliable for this?
   Status: open. Current behavior: excluded, following the README. The excluded runs are listed in `nadel_2026_excluded_runs.csv` (144 files from 16 cells). Two parts of that list are our reading of the log and need a check:
   - `m011 s1c1`: the log's sweep numbers run 4 higher than the file names from the sag protocol on (the log has rheobase at 50-70, the file is `m011_0046-0066.h5`). We matched the held runs with the same shift, so the held set is `m011_0109.h5` through `m011_0201-0221.h5`.
   - `m009 s1c1`: the log says the third F-I run and the third rheobase run were done with +80 pA holding (to -60 mV). We excluded `m009_1027-1037.h5` and `m009_1112-1152.h5`.

2. Misfiled `m009_` files in `607-009/m009 s3c1 - (mz_s2c1)`: we use the copies in `m009 s1c1 +` and skip the 12 duplicates in the MZ folder. `m009_0001-0003.h5` and `m009_0004.h5` exist only in the MZ folder, and per the README they are the start test pulse and spontaneous run of `m009 s1c1`, so they are written as runs of that cell. Is that right?
   Status: open

3. Sweep numbers repeat in two more cells than the README lists: in `20250310 758-L/m114 s2c2`, `m114_0422-0432.h5` (F-I) and `m114_0432-0434.h5` (test pulse) both hold sweep 432, and `m114_0433-0435.h5` overlaps both; in `20260401 862-R/m405 s1c1`, `m405_0001.h5` and `m405_0001-0003.h5` both hold sweep 1. Was the counter reset by hand in these cells? The run start times put the `m114` files in the order F-I, `0433-0435`, `0432-0434`, `0435-0437`.
   Status: open. Current behavior: every file is converted, and series names include the file name so they stay unique.

4. Spontaneous runs done in VC (MZ's holding-current recordings and `m405 s1c1`) and the one I=0 run (`m401 s2c3`) are stored according to the amplifier mode in the header, not the protocol name. Was the VC spontaneous run in `m405 s1c1` also deliberate?
   Status: open. Current behavior: as described.

## Holding and recording settings

5. VC holding at -70 mV is set on the amplifier and is not in the file. Is -70 mV correct for every VC run, including the test pulses and the Ih protocol, across all years?
   Status: open. Current behavior: the voltage clamp stimulus data are the steps relative to holding, with the series `offset` set to -70 mV, so `data * conversion + offset` is the absolute command.

6. Which MultiClamp settings file applies to which days? There are two snapshots (`ashley mc setup on 20230301.mcc` and `rig 2 mc setup on 2023 08 04.mcc`). We need the low-pass filter setting and whether bridge balance and pipette capacitance neutralization were on. The log has per-cell BB and P Neutr values, which suggests they were used even though the snapshot says off.
   Status: open

7. The four ES recordings in 855-L (`m402 s1c1ES` to `s1c4ES`) were made on the other rig the same day. Is anything about that rig different (amplifier, DAQ, filter settings)?
   Status: open. Current behavior: the ES cells share the MultiClamp 700B and PCIe-6323 devices with Jacob's cells.

8. Slice thickness was 250-300 µm in the preprint. Is the value per day recorded anywhere, or should we store the range?
   Status: open

9. Which internal was used each day? The log says "Kgluc for CC" for 2023 and "Mod Kgluc for CC" from 2024. Is the preprint recipe (130 K-gluconate, 15 KCl, 10 HEPES, 2 Mg-ATP, 1 EGTA, 0.3 Na-GTP) the modified one, and if so what was the 2023 recipe?
   Status: open

## Subjects

10. Dates of birth for the main-tree mice. The preprint says bead surgery was at P50-56 and the log says recordings were about 7 days later, which would put the main-tree recordings around P57-63. Are DOBs recoverable from colony records?
    Status: open. Current behavior: no age for the main-tree mice. NWB Inspector reports this as critical for the 32 main-tree files.

11. Timecourse mice: makeMice lists age 40 and 220. The preprint says P40 mice got beads at P40 and were recorded from P41. Should age at recording be P41 (and P221), or does "P40" in makeMice already mean the recording day?
    Status: open. Current behavior: P40D and P220D, from makeMice.

12. Surgery dates for each mouse, or the exact number of days between bead injection and recording.
    Status: open

13. Stress dates: is P28-P40 correct for every stressed mouse in this dataset, including the timecourse cohort?
    Status: open

14. 611-323 / m323: is the real ID 611-024? We use makeMice as the source of truth for sex and ID (README item 6). Do the seven sex discrepancies in `subject_discrepancies.csv` all resolve to makeMice?
    Status: open

15. Strain: the preprint says WT mice were C57BL/6J from The Jackson Laboratory, bred in house. Does that apply to every mouse here, and is the stock JAX 000664?
    Status: open. Current behavior: C57BL/6J for every mouse, not linked to a registry entry.

16. Bead hemisphere: injections were bilateral, and the log's L/R column is empty for every cell. Is the recorded hemisphere recoverable for any cells (for example from the slice images), or should it be left unknown?
    Status: open

## People

17. Full names for the experimenters: JN is Jacob A. Nadel; is MZ Manhua Zhu and ES Evan S. Swanson? Can we get ORCIDs for each?
    Status: open. Current behavior: these names are used, without ORCIDs.

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
