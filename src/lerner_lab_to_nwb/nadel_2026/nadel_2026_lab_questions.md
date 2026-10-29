# aCUS intrinsic ephys: questions for the lab

Questions about the data in `aCUS_ephys_raw_for_NWB`, collected while reading Jacob's README (9/28/26), the tables in `tables/`, the preprint (Nadel et al., bioRxiv 2026.07.29.741478), and the data files. Most are for Jacob. Decisions about the scope and design of the conversion are in `nadel_2026_curator_questions.md`.

The conversion covers the 198 cells in the preprint's figures, listed in `nadel_2026_paper_cells.csv`. Open questions say what the code does now under "Current behavior". Closed questions record the answer, its source, and the date. Numbers stay with a question when it moves from open to closed.

## Open

### Cells and runs

1\. Which cells are in each Figure 2 panel? The conversion uses `used cells.csv` plus 38 cells the figures appear to include, but the lab's own analysis table points to a different list.

- Figs. 2D, 2E, and 2F (P70 BNST, PAG, and SNL): `baseline Firing Rate.csv` in the Zenodo bundle (`ALL_INTRINSIC_EPHYS/analysis`), grouped by projection and stress, reproduces the figures' source data exactly, means and SEMs, at every current we checked (for example BNST unstressed at 100 pA is 18.6667 ± 3.7791 Hz in the table and 18.667 ± 3.779 Hz in the figure). Its cells differ from `used cells.csv`: it includes the 3 cells of 2006-151 (m410), `m108 s1c3` (BNST naive), and `m011 s2c1 +` (SNL naive), and leaves out `m105 s1c1` (BNST stressed) and `m114 s2c2` (SNL naive). Is that table the record of the cells in these panels? We have not checked the TS panels.
- Fig. 2N (P40): 2 mice and 16 unstressed and 19 stressed cells. The four P40 timecourse mice have exactly that many cells once ES's four cells in `855-L` are left out (16 from 853-L and 855-L, 19 from 854-L and 862-L). The P40 cells are not in the Zenodo tables, so this rests on the counts only. Which cells are in this panel?
- `m011 s2c1 +`: `baseline Firing Rate.csv` lists sweeps 297-307 as its F-I sweeps, but those sweeps are in its rheobase runs (`m011_0277-0297.h5` and `m011_0298-0338.h5`), not its F-I runs (`m011_0232-0242.h5` to `m011_0254-0264.h5`). Are the paper's values for this cell from the right sweeps? The cell also has no log entry, so if it is in the paper we need to know which of its runs were held at -60 mV. `firing rate from -60.csv` uses `m011_0351-0361.h5`, which is in the repeat set that starts with the second spontaneous run, `m011_0339.h5`.

The P40 and m410 parts were asked by email on Oct 21 and have not been answered.

Current behavior: until this is confirmed, the 160 cells in `used cells.csv`, the 3 cells of m410, and the 35 P40 cells Jacob recorded.

2\. The Sept 2023 runs held near -60 mV: the README says to exclude them, but the Zenodo bundle has `firing rate from -60.csv` and `rheobase from -60.csv`, which suggests they were analyzed. The preprint reports no analysis at -60 mV. Should they still be left out of the NWB files? Nothing in the .h5 files marks them, so we identified them from the sweep ranges in the log. Are those ranges reliable for this?

Current behavior: excluded, following the README. The excluded runs are listed in `nadel_2026_excluded_runs.csv` (86 files from 10 cells). For `m009 s1c1`, the log says the third F-I run and the third rheobase run were done with +80 pA holding (to -60 mV), so we excluded `m009_1027-1037.h5` and `m009_1112-1152.h5`. Is that the right reading?

3\. Misfiled `m009_` files in `607-009/m009 s3c1 - (mz_s2c1)`: `m009_0001-0003.h5` and `m009_0004.h5` exist only in the MZ folder, and per the README they are the start test pulse and spontaneous run of `m009 s1c1`. Is that right?

Current behavior: written as runs of `m009 s1c1`.

4\. Sweep numbers repeat in `20250310 758-L/m114 s2c2`, which the README does not mention: `m114_0422-0432.h5` (F-I) and `m114_0432-0434.h5` (test pulse) both hold sweep 432, and `m114_0433-0435.h5` overlaps both. The run start times put the files in the order F-I, `0433-0435`, `0432-0434`, `0435-0437`. Was the counter reset by hand?

Current behavior: every file is converted, and series names include the file name so they stay unique.

### Holding and recording settings

5\. VC holding at -70 mV is set on the amplifier and is not in the file. Is -70 mV correct for every VC run, including the test pulses and the Ih protocol, across all years?

Current behavior: the voltage clamp stimulus data are the steps relative to holding, with the series `offset` set to -70 mV, so `data * conversion + offset` is the absolute command.

6\. Which MultiClamp settings file applies to which days? There are two snapshots (`ashley mc setup on 20230301.mcc` and `rig 2 mc setup on 2023 08 04.mcc`). We need the low-pass filter setting and whether bridge balance and pipette capacitance neutralization were on. The log has per-cell BB and P Neutr values, which suggests they were used even though the snapshot says off.

7\. Slice thickness was 250-300 µm in the preprint. Is the value per day recorded anywhere, or should we store the range?

8\. Which internal was used each day? The log says "Kgluc for CC" for 2023 and "Mod Kgluc for CC" from 2024. Is the preprint recipe (130 K-gluconate, 15 KCl, 10 HEPES, 2 Mg-ATP, 1 EGTA, 0.3 Na-GTP) the modified one, and if so what was the 2023 recipe?

### Subjects

9\. Dates of birth for the P70 mice. The preprint says bead surgery was at P50-56 and the log says recordings were about 7 days later, which would put these recordings around P57-63. Are DOBs recoverable from colony records?

Current behavior: no age for these mice. NWB Inspector reports this as critical for the 30 files from the main data tree.

10\. P40 mice: makeMice lists age 40. The preprint says these mice got beads at P40 and were recorded from P41. Should age at recording be P41, or does "40" in makeMice already mean the recording day?

Current behavior: P40D, from makeMice.

11\. Surgery dates for each mouse, or the exact number of days between bead injection and recording.

12\. Stress dates: is P28-P40 correct for every stressed mouse in this dataset, including the P40 cohort?

13\. 611-323 / m323: is the real ID 611-024? We use makeMice as the source of truth for sex and ID (README item 6). Do the sex discrepancies in `subject_discrepancies.csv` all resolve to makeMice?

14\. Strain: the preprint says WT mice were C57BL/6J from The Jackson Laboratory, bred in house. Does that apply to every mouse here, and is the stock JAX 000664?

Current behavior: C57BL/6J for every mouse, not linked to a registry entry.

15\. Bead hemisphere: injections were bilateral, and the log's L/R column is empty for every cell. Is the recorded hemisphere recoverable for any cells (for example from the slice images), or should it be left unknown?

### People

16\. Full names for the experimenters: JN is Jacob A. Nadel; is MZ Manhua Zhu? Can we get ORCIDs for each?

Current behavior: these names are used, without ORCIDs.

17\. The second analog input in Jacob's Sept 2023 files. The README (item 1) describes this channel as a command loopback that doesn't track the stimulus, attributed to the user settings that month. In these files the channel instead records the membrane potential a second time: converted to volts at the DAQ, it follows the primary voltage channel with a slope of 0.92 to 1.00 and r of 0.96 to 1.00 (1.000 on the sag runs). Its "-336 pA" baseline in `m009_1005-1015.h5` is the -83 mV resting potential at the primary channel's gain. MZ's files from the same days have identical headers (same user settings file, same input terminal AI4, same scales) and record the true command. That suggests a cabling difference: AI4 connected to an amplifier voltage output on the setup Jacob used, and to the DAQ command output on MZ's. Did you and MZ record on different rigs or with different cabling that month? We suggest correcting README item 1 to say that the channel records membrane potential in your Sept 2023 files and that the delivered command was not recorded there.

Current behavior: no recorded command for those 263 runs. The stimulus template, built from the protocol library, is the only stimulus.

18\. The free-text notes in your log sheets. Many of them carry useful experimental information, for example that the holding current from the previous cell was left on during some runs, or that access resistance doubled during a recording. That information is mixed with informal wording. We'd like to include it in the NWB files, which may eventually be shared publicly. Our proposal: keep the experimental content of each note, remove expletives and purely personal remarks, and leave out notes that have no experimental content. Is that OK, or would you prefer the notes verbatim, or left out entirely? Either way, we can send you the edited notes to review before anything is shared.

Current behavior: notes are not converted.

19\. Retrobead status: we describe every converted cell as retrobead-positive, based on the preprint's statement that bead-positive cells were targeted and on no paper cell being marked bead-negative. The folder names mark bead status only in 2023, and the log sheets' "Retrob+" column is blank for 79 of the 198 cells in his scraped table. One cell is logged as "y?": `m103 s3c5` (20240529 675-L). Were all analyzed cells bead-positive, including that one?

Current behavior: every cell is described as retrobead-positive.

20\. Log sheet entries we had to interpret. We read the three log sheets directly to put the per-cell values in the files (`nadel_2026_extract_log_sheets.py` lists every case). Can you check these?
- Read as typos: Cp fast "14/106" as 14.106 (`m022 s3c2`), holding current "-100\\" as -100 (`m103 s3c4`), time "2L46" as 2:46 and test-pulse access "(19,5)" as 19.5 (`m410 s2c1`), "35!!" as 35, and four access values with an unclosed parenthesis.
- Left blank: Rt 4.5 in MZ's sheet for `m323 s3c2`, which looks like a pipette resistance in the wrong column (the Rt column is otherwise empty for every paper cell); Er 34.05 for `m403 s2c3`, which is in the range of pipette offsets; P Neutr -150 for `m202 s1c4`, which is in the range of holding currents; resting "60" for `m113 s4c2` (sign unclear); access "(15ish?)" for MZ's s2c1.
- Test pulses logged with sweep numbers no file holds: 12 were matched to the cell's one overlapping test-pulse file (for example "577-579" to `m011_0576-0578.h5`) and 13 by order. Three are not matched: `m021 s1c2`'s first test pulse is `m021_0116-0118.h5`, which sits in the `m021 s1c1` folder; `m203 s1c1`'s "1-3" has no file in the hand-off; `m114 s2c2` has three candidate files.
- Day fields: the Internal field for m021 reads "021", and the Surgery field for m106 reads "s", so both are left blank. The Date fields on the m104 to m107 tabs (05/29/2024), m204 (2/13), and m403 (10/1/25) do not match the recording days.

Current behavior: as described; the values are in `nadel_2026_log_cells.csv`, `nadel_2026_log_test_pulses.csv`, and `nadel_2026_log_sessions.csv`.

## Closed

None yet.
