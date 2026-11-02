# aCUS intrinsic ephys: questions for the lab

Questions for Jacob about `aCUS_ephys_raw_for_NWB`. We are converting the cells in the preprint's figures. Answered questions move to Closed with the answer and date, and keep their numbers.

## Open

### Cells and runs

1\. Which cells are in Figure 2? The README says `used cells.csv` lists the 160 cells in the paper, and that the June 2026 PAG mouse (2006-151) and the timecourse mice are not in the paper. The preprint's statistics table does not match this.
- 1A. Figs. 2D-F (P70). The cell counts in `used cells.csv` differ from the preprint in three groups: BNST unstressed (14 vs 15), BNST stressed (14 vs 13), and PAG unstressed (11 cells from 2 mice vs 14 from 3). `baseline Firing Rate.csv` in the Zenodo bundle matches the preprint's counts in all six groups and all 66 F-I means and SEMs. It has 5 cells that `used cells.csv` does not: `m108 s1c3` (BNST unstressed), `m011 s2c1 +` (SNL unstressed), and the 3 cells of 2006-151 (PAG unstressed). It does not have 2 cells that `used cells.csv` has: `m105 s1c1` (BNST stressed) and `m114 s2c2` (SNL unstressed). Are the cells in `baseline Firing Rate.csv` the cells in these panels?
- 1B. Fig. 2N (P40). The preprint reports 16 unstressed and 19 stressed cells, from 2 mice per group. The README lists the timecourse mice as not in the paper, and no P40 cell is in `used cells.csv` or the Zenodo bundle. Are the Fig. 2N cells in the shared data? If so, are they your cells in 853-L and 855-L (unstressed) and 854-L and 862-L (stressed)? Those folders hold 16 and 19 cells, not counting ES's 4 in 855-L.
- 1C. `m011 s2c1 +` has no log entry. It has 6 F-I runs, 3 before and 3 after a second spontaneous run (`m011_0339.h5`), The 9 cells the log lists with held runs also have a second spontaneous run, which the log marks as held. Were its runs from `m011_0339.h5` on held at -60 mV?

The P40 and 2006-151 parts repeat our Oct 21 email.

2\. The README says to exclude the runs held at -60 mV in Sept 2023, but the `sweep` values in `baseline Firing Rate.csv` suggest they were used in Fig. 2F for the 10 SNL cells that have them (listed in `nadel_2026_excluded_runs.csv`). Were they?

3\. `m021_0116-0118.h5`, a VC test pulse, is in the `m021 s1c1 +` folder, but the log lists sweeps 116-118 as the opening test pulse of `m021 s1c2 +`. Which cell does it belong to?

### Recording settings

4\. The log has columns for bridge balance (BB) and pipette capacitance neutralization (P Neutr), but BB is empty for every cell and P Neutr has one entry (12B). The two MultiClamp snapshots are named with dates before the first recording day and have capacitance neutralization off. Were bridge balance and capacitance neutralization on during these recordings, and what was the low-pass filter setting?

5\. The preprint gives one internal recipe, a modified potassium gluconate internal, but the log's Internal field reads "Kgluc for CC" on 13 recording days and "Mod Kgluc" or "Modified Kgluc" on 16. Are these different solutions, and if so, what is the recipe of the unmodified one?

### Subjects

6\. The README says dates of birth and surgery dates are missing.
- 6A. The preprint says the P70 mice recovered about 3 weeks after surgery, but the log's "days since surgery" reads "7 ish" on 8 of their recording days. What were each mouse's date of birth and surgery date?
- 6B. The preprint says the P40 mice got beads at P40 and were recorded from P41, but the log's "days since surgery" reads "7 ish" for 853-L and 854-L. What were each mouse's date of birth and surgery date?

7\. README item 7 says the real ID of 611-323 (m323) is probably 611-024. Is it?

8\. The log's L or R column is empty for every cell. Is the recorded hemisphere known for any cell?

### Data and logs

9\. README item 1 says the command channel in your Sept 2023 files is wrong because of your user settings that month, but MZ's files from the same days use the same user settings file (`JN_20230823_intrinsic prop.usr`) and record the command correctly. In your spontaneous runs, which have no stimulus, the channel follows the membrane potential (r of 0.84 or higher in 30 of 33 runs). What was this input connected to in your recordings that month?

10\. The log notes mix experimental information with informal wording. We propose keeping the experimental content and removing the rest, and would send you the edited notes to review. Is that OK, or would you prefer them verbatim or left out?

11\. The preprint says recordings targeted bead-positive cells, but the log's Retrob+ column is blank for 79 of the 198 cells we are converting, and `m103 s3c5` is marked "y?". Were all of these cells bead-positive?

12\. Log entries we had to interpret (every case is listed in `nadel_2026_extract_log_sheets.py`):
- 12A. Some values look like typos. We read Cp fast "14/106" as 14.106 (`m022 s3c2 +`), holding current "-100\\" as -100 (`m103 s3c4`), and time "2L46" as 2:46 and access "(19,5)" as 19.5 (`m410 s2c1`). Are these right?
- 12B. Some values do not fit their column, so we left them blank: Rt 4.5 (`m323 s3c2 +`, in the pipette resistance range), Er 34.05 (`m403 s2c3`, in the pipette offset range), P Neutr -150 (`m202 s1c4`, in the holding current range), resting "60" (`m113 s4c2`), and access "(15ish?)" (`m006 s4c1 +`). What are the right values or columns?
- 12C. For 13 test pulses, the logged sweeps are in no file of the cell, so we matched them by position among the cell's test pulses (listed in `nadel_2026_log_test_pulses.csv`). Is that right?
- 12D. The log lists the first test pulse of `m203 s1c1` as sweeps 1-3, but no file in the hand-off holds those sweeps. Is there a file for it?
- 12E. The log lists the end test pulse of `m114 s2c2` as sweeps 436-438, but no file holds those sweeps. Is it `m114_0433-0435.h5` (recorded in CC) or `m114_0432-0434.h5` (VC)?
- 12F. The Date field on six log tabs differs from the folder date: "05/29/2024" on 671-0, 674-L, 675-R, and 674-0 (recorded May 30 to June 4), "2/13" on 752-0 (recorded Feb 20, 2025), and "10/1/25" on 854-L (recorded Oct 17, 2025). We use the folder dates. Are those right?

## Closed

None yet.
