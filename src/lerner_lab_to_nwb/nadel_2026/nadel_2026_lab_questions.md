# aCUS intrinsic ephys: questions for the lab

Questions about the data in `aCUS_ephys_raw_for_NWB`, collected while reading Jacob's README (9/28/26), the tables in `tables/`, the preprint (Nadel et al., bioRxiv 2026.07.29.741478), and the data files. Most are for Jacob. Decisions about the scope and design of the conversion are in `nadel_2026_curator_questions.md`.

The conversion covers the 198 cells in the preprint's figures, listed in `nadel_2026_paper_cells.csv`. Open questions say what the code does now under "Current behavior". Closed questions record the answer, its source, and the date. Numbers stay with a question when it moves from open to closed.

Items from the README's "don't have" list that the preprint methods already answer are at the bottom so they can be confirmed in one pass.

## Open

### Cells and runs

18\. Which cells are in each Figure 2 panel? The conversion uses `used cells.csv` plus 38 cells the figures appear to include, but the lab's own analysis table points to a different list.

- Figs. 2D, 2E, and 2F (P70 BNST, PAG, and SNL): `baseline Firing Rate.csv` in the Zenodo bundle (`ALL_INTRINSIC_EPHYS/analysis`), grouped by projection and stress, reproduces the figures' source data exactly, means and SEMs, at every current we checked (for example BNST unstressed at 100 pA is 18.6667 ± 3.7791 Hz in the table and 18.667 ± 3.779 Hz in the figure). Its cells differ from `used cells.csv`: it includes the 3 cells of 2006-151 (m410), `m108 s1c3` (BNST naive), and `m011 s2c1 +` (SNL naive), and leaves out `m105 s1c1` (BNST stressed) and `m114 s2c2` (SNL naive). Is that table the record of the cells in these panels? We have not checked the TS panels.
- Fig. 2N (P40): 2 mice and 16 unstressed and 19 stressed cells. The four P40 timecourse mice have exactly that many cells once ES's four cells in `855-L` are left out (16 from 853-L and 855-L, 19 from 854-L and 862-L). The P40 cells are not in the Zenodo tables, so this rests on the counts only. Which cells are in this panel?
- `m011 s2c1 +`: `baseline Firing Rate.csv` lists sweeps 297-307 as its F-I sweeps, but those sweeps are in its rheobase runs (`m011_0277-0297.h5` and `m011_0298-0338.h5`), not its F-I runs (`m011_0232-0242.h5` to `m011_0254-0264.h5`). Are the paper's values for this cell from the right sweeps? The cell also has no log entry, so if it is in the paper we need to know which of its runs were held at -60 mV. `firing rate from -60.csv` uses `m011_0351-0361.h5`, which is in the repeat set that starts with the second spontaneous run, `m011_0339.h5`.

The P40 and m410 parts were asked by email on Oct 21 and have not been answered.

Current behavior: until this is confirmed, the 160 cells in `used cells.csv`, the 3 cells of m410, and the 35 P40 cells Jacob recorded.

1\. The Sept 2023 runs held near -60 mV: the README says to exclude them, but the Zenodo bundle has `firing rate from -60.csv` and `rheobase from -60.csv`, which suggests they were analyzed. The preprint reports no analysis at -60 mV. Should they still be left out of the NWB files? Nothing in the .h5 files marks them, so we identified them from the sweep ranges in the log. Are those ranges reliable for this?

Current behavior: excluded, following the README. The excluded runs are listed in `nadel_2026_excluded_runs.csv` (86 files from 10 cells). For `m009 s1c1`, the log says the third F-I run and the third rheobase run were done with +80 pA holding (to -60 mV), so we excluded `m009_1027-1037.h5` and `m009_1112-1152.h5`. Is that the right reading?

2\. Misfiled `m009_` files in `607-009/m009 s3c1 - (mz_s2c1)`: `m009_0001-0003.h5` and `m009_0004.h5` exist only in the MZ folder, and per the README they are the start test pulse and spontaneous run of `m009 s1c1`. Is that right?

Current behavior: written as runs of `m009 s1c1`.

3\. Sweep numbers repeat in `20250310 758-L/m114 s2c2`, which the README does not mention: `m114_0422-0432.h5` (F-I) and `m114_0432-0434.h5` (test pulse) both hold sweep 432, and `m114_0433-0435.h5` overlaps both. The run start times put the files in the order F-I, `0433-0435`, `0432-0434`, `0435-0437`. Was the counter reset by hand?

Current behavior: every file is converted, and series names include the file name so they stay unique.

### Holding and recording settings

5\. VC holding at -70 mV is set on the amplifier and is not in the file. Is -70 mV correct for every VC run, including the test pulses and the Ih protocol, across all years?

Current behavior: the voltage clamp stimulus data are the steps relative to holding, with the series `offset` set to -70 mV, so `data * conversion + offset` is the absolute command.

6\. Which MultiClamp settings file applies to which days? There are two snapshots (`ashley mc setup on 20230301.mcc` and `rig 2 mc setup on 2023 08 04.mcc`). We need the low-pass filter setting and whether bridge balance and pipette capacitance neutralization were on. The log has per-cell BB and P Neutr values, which suggests they were used even though the snapshot says off.

8\. Slice thickness was 250-300 µm in the preprint. Is the value per day recorded anywhere, or should we store the range?

9\. Which internal was used each day? The log says "Kgluc for CC" for 2023 and "Mod Kgluc for CC" from 2024. Is the preprint recipe (130 K-gluconate, 15 KCl, 10 HEPES, 2 Mg-ATP, 1 EGTA, 0.3 Na-GTP) the modified one, and if so what was the 2023 recipe?

### Subjects

10\. Dates of birth for the P70 mice. The preprint says bead surgery was at P50-56 and the log says recordings were about 7 days later, which would put these recordings around P57-63. Are DOBs recoverable from colony records?

Current behavior: no age for these mice. NWB Inspector reports this as critical for the 30 files from the main data tree.

11\. P40 mice: makeMice lists age 40. The preprint says these mice got beads at P40 and were recorded from P41. Should age at recording be P41, or does "40" in makeMice already mean the recording day?

Current behavior: P40D, from makeMice.

12\. Surgery dates for each mouse, or the exact number of days between bead injection and recording.

13\. Stress dates: is P28-P40 correct for every stressed mouse in this dataset, including the P40 cohort?

14\. 611-323 / m323: is the real ID 611-024? We use makeMice as the source of truth for sex and ID (README item 6). Do the sex discrepancies in `subject_discrepancies.csv` all resolve to makeMice?

15\. Strain: the preprint says WT mice were C57BL/6J from The Jackson Laboratory, bred in house. Does that apply to every mouse here, and is the stock JAX 000664?

Current behavior: C57BL/6J for every mouse, not linked to a registry entry.

16\. Bead hemisphere: injections were bilateral, and the log's L/R column is empty for every cell. Is the recorded hemisphere recoverable for any cells (for example from the slice images), or should it be left unknown?

### People

17\. Full names for the experimenters: JN is Jacob A. Nadel; is MZ Manhua Zhu? Can we get ORCIDs for each?

Current behavior: these names are used, without ORCIDs.

19\. The second analog input in Jacob's Sept 2023 files. The README (item 1) describes this channel as a command loopback that doesn't track the stimulus, attributed to the user settings that month. In these files the channel instead records the membrane potential a second time: converted to volts at the DAQ, it follows the primary voltage channel with a slope of 0.92 to 1.00 and r of 0.96 to 1.00 (1.000 on the sag runs). Its "-336 pA" baseline in `m009_1005-1015.h5` is the -83 mV resting potential at the primary channel's gain. MZ's files from the same days have identical headers (same user settings file, same input terminal AI4, same scales) and record the true command. That suggests a cabling difference: AI4 connected to an amplifier voltage output on the setup Jacob used, and to the DAQ command output on MZ's. Did you and MZ record on different rigs or with different cabling that month? We suggest correcting README item 1 to say that the channel records membrane potential in your Sept 2023 files and that the delivered command was not recorded there.

Current behavior: no recorded command for those 263 runs. The stimulus template, built from the protocol library, is the only stimulus.

20\. The free-text notes in your log sheets. Many of them carry useful experimental information, for example that the holding current from the previous cell was left on during some runs, or that access resistance doubled during a recording. That information is mixed with informal wording. We'd like to include it in the NWB files, which may eventually be shared publicly. Our proposal: keep the experimental content of each note, remove expletives and purely personal remarks, and leave out notes that have no experimental content. Is that OK, or would you prefer the notes verbatim, or left out entirely? Either way, we can send you the edited notes to review before anything is shared.

Current behavior: notes are not converted.

## Closed

4\. Was the VC spontaneous run in `m405 s1c1` deliberate, like MZ's?

Closed (2026-10-29): no longer needed. `m405 s1c1` is a P220 cell, and the P220 cohort is not in the paper, so it is not converted.

7\. Was the rig ES used for the four `855-L` cells different from Jacob's?

Closed (2026-10-29): no longer needed. ES's cells are not in the paper (Fig. 2N counts match without them), so they are not converted.

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
