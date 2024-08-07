# Notes concerning the seiler_2024 conversion split by interface

# Gdrive Data Changes -- these edits have been made to the GDrive Data directly
- PS/332.393 was missing the 07/28/2020 session but Lerner Lab provided a backup --> I copy/pasted the backup from the provided .txt file into the medpc file at the end

 ## Behavior
 For all medpc files,
 - MSN refers to the name of the code file used to produce this session

### FP Behavior
 In FP Experiments/Behavior,
- G represents portEntryTs (Port Entry Times)
- E represents DurationOfPE (Duration of Port Entry)
- A represents LeftNoseTs (Left Nose Poke Times)
- C represents RightNoseTs (Right Nose Poke Times)
- D represents RightRewardTs (Reward Delivered after Active Nose Poke)
- B represents LeftRewardTs (Interleaved per animal -- probably)
- H represents Footshock times

In FP Experiments/Behavior/PS,
- some of the animals have csvs, but are missing the raw MEDPC Files (ex. 75.214)
- In MEDPC_RawFilesbyDate, many of the sessions are missing Subject info (ex. 10/08/18 16:37:19)
- Some of the sessions missing Subject info are .csv sessions (ex. 75.214 11/09/18)
- For the animals missing raw med PC files, the plan is:
    - Iterate through all of the MEDPC_RawFilesbyDate, grabbing all of the session start times, dates, subject IDs, and MSNs
    - For subject IDs that match convert those sessions
    - Will need to refactor the read_medpc_file function to be able to _optionally_ handle different subject IDs in the same session
    - Sessions with missing subject info will just have to be skipped -- but will need to iterate through .csv sessions and match them to their corresponding medpc session

In FP Experiments/Behavior/PR/028.392,
- some of the sessions (ex. 7/09/20) have ALL NaN values for Duration of Port Entry

In FP Experiments/Behavior/DPR/272.396,
- some of the days (ex. 7/06/20) have two sessions per day

In FP Experiments/Behavior/DPR/334.394,
- some of the sessions (ex. 6/17/20) have both left and right rewards (MSN: FOOD_FR1 HT TTL (Both))

In FP Experiments/Behavior/PR/141.308,
- medpc file is filled with whitespace characters like \t

In FP Experiments/Behavior/MEDPCRawFilesbyDate/2018-11-09,
- All the sessions have the same start_date and start_time and no subject info --> need to make medpc reader support
more generic filter conditions (ex. box number)

In FP Experiments/Behavior/PS/140.306,
- one of the sessions (ex. 09/06/19) has a bunch of garbage to the right of the 'A' variable
- Solution: Handled by reader

### Active Questions
None

### Resolved Questions
In FP Experiments/Behavior/PS/139.298,
- one of the sessions (ex. 09/20/19) is actually from subject 144.306
- 144.306 is a ghost -- it doesn't show up in any of the behavior folders and not in the mosue demographics google sheet
- Answer: Yes it looks like I must have accidentally saved those in the wrong file. You should trust that the subject number is correct and disregard the sessions in question.
- Solution: Trust subject field of medpc file in these cases.

What experimental stage (FR1, footshock probe, omission probe, etc.) does "Probe Test Habit Training TTL" correspond to?
- Answer: Probe tests always occur immediately following a Footshock degradation program. They were not used in the paper however.
- Solution: training stage = ProbeTest

Many MSNs (ex. 'FOOD_FR1 TTL Left', 'FOOD_FR1 TTL Right', and 'FOOD_RI 30 LEFT') list both E and U as corresponding to duration of port entry.
- Answer: As far as I can tell, U should just be ignored. It looks like a carry over from older versions of this code and nothing is actually being stored in U.
- Solution: Ignore U

In FP Experiments/Behavior/RR20/95.259/95.259, some of the sessions (ex. 04/09/19) have non-ascending reward port intervals
ex. reward port entry = 985.750, reward port exit = 985.850 (duration = 0.1), next reward port entry = 985.800 (before previous exit)
how is this possible?
    - Answer: MedPC system has limited temporal resolution for durations (probably 0.1 is the smallest interval possible).
    - Solution: Ignore non-ascending timestamp errors.


## Fiber Photometry
- 6 data streams:
    - Dv1A = array of photometry response dms 465nm
    - Dv2A = array of photometry response dms 405nm
    - Dv3B = array of photometry response dls 465nm
    - Dv4B = array of photometry response dls 405nm
    - Fi1d = 4xN array of demodulated commanded voltages: dms 465nm, dms 405nm, dls 465nm, dls 405nm
    - Fi1r = 2xN array of modulated commanded voltages: dms and dls
- Folders are named 'Photo_<subject_id>-YYMMDD-HHMMSS' --> match with same day behavior session
- some folders have subject_id with multiple session folders for each subject
- For DPR/334.394/07/02/20, no right nosepokes were made --> photometry object doesn't have a RNPS object
    - Solution: only extract ttls if the corresponding behavior array is non-empty

### Resolved Questions
- Delayed Punishment Resistant/Early/Photo_64_205-181017-094913 is duplicated at Delayed Punishment Resistant/Late/64.205/Photo_64_205-181017-094913
    - Same for Photo_81_236-190117-102128, Photo_87_239-190228-111317, Photo_88_239-190219-140027
    - --> skipping the second one
- Punishment Resistant/Early RI60/Photo_80_236-190121-093425 is duplicated at Punishment Resistant/Late RI60/80.236/Photo_80_236-190121-093425
    - --> skipping second one
- Punishment Sensitive/Early RI60/Photo_75_214-181029-124815 is duplicated at Punishment Sensitive/Late RI60/Photo_75_214-181029-124815
    - same for Photo_93_246-190222-130128
    - --> skipping second one
- The TTL for 'unrewarded right nose pokes' (RNnR), corresponds to the nose pokes variable in medpc, which supposedly
records *all* nosepokes. Which is correct?
    - Answer: Separately from that collection, MED is sending TTLs for either rewarded or unrewarded nosepokes to the TDT rig. This is happening based on the IF statement in S.S.4 of the MSN code.    These are not "stored" in an array in the MED output themselves but are in the TDT output. Does that make sense? It's a little confusing so I'm happy to explain it on a Zoom call.
        The right nosepokes (variable R) are being recorded in MEDPC, regardless of whether they are rewarded or unrewarded in DIM C. This is happening in the S.S.7 (Timestamp Collection) portion of the MSN code. DIM D contains all of the timestamps for when a right reward was delivered (which happens when they make a rewarded nosepoke so it makes sense that these are the same as the times of right rewarded nosepokes).
    - Solution: Treat 'RNnR' as right nosepoke times (Dim C) since it matches the shape. Treat 'RNRW' as right reward times (Dim D) since it matches the shape.
- PS/271.396_07/07/20 has two behavioral sessions but only 1 fp session folder
    - Answer: For 271.396 on 07/07/20, I initially ran the animal on RI60_RIGHT for 15ish minutes before realizing it was a mistake and switching it to RI60 LEFT, hence the 2 MED entries.
    - Solution: Ignore 15min RI60_Right and keep RI60_Left
- PS/332.393_07/28/20 has 2 fp sessions but no matching behavior session
    - Solution: added missing session to behavioral file and stitched them together
- The RR20 folder only has .mat files rather than tdt synapse output folders -- pls provide?
    - Solution: Lerner Lab provided RR20.
- Several sessions don't have fi1d -- see printout
    - Solution: Added option for fi1r-only in photometry interface
- Delayed Punishment Resistant/Late/Photo_334_394-200721-131257 throws an error from tdt.read_block, but loads fine if t2 <= 824
    - Solution: just load with t2<=824
    - This session also is missing RNPS TTL but has 3 nose poke times in the medpc file --> ask lab
- Punishment Sensitive/Late RI60/Photo_139_298-190912-095034 throws an error from tdt.read_block, but loads fine if t2 <= 2267
    - Solution: just load with t2<=2267
    - This session is also Fi1r-only
- Punishment Sensitive/Early RI60/Photo_140_306-190809-121107 has msn FOOD_RI 60 LEFT TTL, but epocs
PrtN, RNnR, PrtR, LNPS, RNRW -- why is this mismatched with the expected epocs?
    - Answer: Per my notes, this animal was accidentally run on the wrong TDT program.
    - Solution: Manually correct this session (essentially everything that says right is actually left, and vice versa).
    - This sesison is also Fi1r-only
- Some of the animals/days have 2 photometry sessions but only 1 behavior session
(ex. Punishment Sensitive/Late RI60/Photo_139_298-190912-095034 and Photo_139_298-190912-103544) is the photometry
for that 1 session split across the two folders?
    - Answer: Yes, occasionally the computer freezes or something and I need to restart the TDT recording while the MED program is unaffected. For my analysis I basically just stitched them together.
    - Solution: Added stitching functionality for optional second_folder_path
- For DPR/334.394/07/21/20, 3 right nosepokes were made BUT photometry object still doesn't have a RNPS object
    - Skip this session bc it is corrupted
- RR20/99.257 on 04/16/19 has a photometry session but no matching behavior session on that day -- pls provide?
    - Skip this session bc Lerner Lab can't find it

### Active Questions
- In one of those sessions, FP Experiments/Photometry/RR20/late/Photo_96_259-190506-105642, doesn't have any RNnR TTLs,
  even though it has plenty of right nose pokes in the behavioral file. Can you look into this?

## Optogenetics
### Notes
- Opto Behavior files are disorganized esp. DLS Excitatory with a mix of folders, medpc files, and csv files
- File structure also contains important metadata for optogenetic interface ex. ChR2 vs EYFP
- Optogenetic pulses are either paired directly with reward times or optogenetic_stimulus_times variable in medpc file
    for "scrambled" trials.
- timing info can be found in paper (460nm, 1 s, 20 Hz, 15 mW for excitatory and 625nm, 1 s, 15 mW for inhibitory)
- Some of the opto csv sessions have start times (ex. DLS Excitatory/ChR2/290.407/290.407_09-23-20.csv) -- added optional parsing
- Some of the sessions (ex. DLS-Excitatory/079.402/06/27/20) don't have any reward/stim times
- Some of the medpc files organized by date are redundant but others are not ex. 309.399
- A few of those animals died and were not included in the paper (416.405 and 289.408) --> skip DLS Excitatory .csvs

### Resolved Questions
- need to ask for more specific info about the device (data sheet)
    - Answer: This is the LED source https://www.prizmatix.com/Optogenetics/Optogenetics-LED-Dual.aspx and this is the pulser (its the PulserPlus option) https://www.prizmatix.com/optogenetics/Prizmatix-in-vivo-Optogenetics-Toolbox.htm#pls
- Need pulse width for excitatory optogenetics
    - Answer: The pulse width is 5ms
- DMS-Inhibitory Group 2 is missing
    - Solution: Lerner Lab provided this.
- DLS-Excitatory has a bunch of files (medpc and csv) organized by date not belonging to any optogenetic treatment group folder
    (ChR2, EYFP, Scrambled).  Which treatment did these sessions receive?
    - Solution: Metadata excel file has treatment info --> metadata["NWBFile"]["stimulus_notes"]
- RI 60 LEFT_STIM, RI 30 LEFT_STIM, and RK_C_FR1_BOTH_1hr msns show up in opto data but don't have associated files -- assumed to be the same as their right counterparts?

### Active Questions
None

### Resolved Questions
- DMS-Excitatory has some csv files w/ only session-aggregated info (total right rewards but not right reward times) ex. ChR2/121_280.CSV -- do you have individual session info for these animals?
    - Lerner Lab does not have this data --> skip these sessions
- Some csv files do not have any subject info (ex. DLS Excitatory/_08-28-20.csv) -- pls provide or we will need to skip these sessions
    - Lerner Lab does not have this metadata --> skip these sessions
- Some of the sessions in the DLS Excitatory medpc files organized by date don't have subject info -- pls provide or we will need to skip these sessions
    Full List:
        start_date ='08/28/20' start_time ='14:02:02'
        start_date ='08/28/20' start_time ='15:19:38'
        start_date ='08/28/20' start_time ='15:53:16'
        start_date ='08/28/20' start_time ='16:02:33'
        start_date ='08/28/20' start_time ='16:33:16'
        start_date ='08/28/20' start_time ='16:38:51'
        start_date ='09/03/20' start_time ='12:39:34'
        start_date ='09/03/20' start_time ='12:39:34'
        start_date ='09/03/20' start_time ='12:39:34'
        start_date ='09/03/20' start_time ='12:39:34'
        start_date ='08/31/20' start_time ='13:02:03'
        start_date ='08/31/20' start_time ='13:02:03'
        start_date ='08/31/20' start_time ='13:02:03'
        start_date ='08/31/20' start_time ='13:02:03'
        start_date ='08/31/20' start_time ='14:53:03'
        start_date ='08/31/20' start_time ='14:53:03'
        start_date ='08/31/20' start_time ='14:53:03'
        start_date ='08/31/20' start_time ='15:34:14'
        start_date ='09/22/20' start_time ='12:43:27'
        start_date ='09/22/20' start_time ='12:43:27'
        start_date ='09/22/20' start_time ='12:43:27'
    - Lerner Lab does not have this metadata --> skip these sessions

## Western Blot
### Notes
- Excel file has subject_ids for Female DLS Actin, Female DLS DAT, Female DMS Actin, Female DMS DAT and their
    and their corresponding data (area, mean, min, max, white-sample, corrected sample-blank) BUT no male data.
- Tif files have western blot images for male and female all conditions BUT only 1 subject/condition (Fig S3A has ~7animals/condition)
- Tif files are combined WT on the left DAT on the right --> will need to split.
- How to deal with this data? Western Blot extension? Skip? Just include the images?

## Metadata
### Notes
- Some medpc filenames/sessions have incomplete or missing subject names (ex. 75 instead of 75.214) -- need to do some matching operation
- Punishment Group has a typo for PR ('Punishment Resitant' instead of 'Punishment Resistant') -- I'll fix on my end

### Resolved Questions
- Some of the subject_ids are not present in the metadata excel file -- pls provide
- Some animals are missing the "Hemisphere with DMS" field -- pls provide
- Some of the mouse ids have typos (leading and trailing zeros) as well as some that appear incorrect (RR20 section)
    So, I made the following corrections to metadata excel sheet:
    Mouse ID corrections:
        79.402 --> 079.402
        344.4 --> 344.400
        432.42 --> 432.420
        48.392 --> 048.392
        98.259 --> 98.257
        101.259 --> 101.260
        97.259 --> 97.257
        99.259 --> 99.257
        100.259 --> 100.258
        359.43 --> 359.430
        28.392 --> 028.392
        227.43 --> 227.430
        262.478 --> 262.259
        354.43 --> 354.430
        430.42 --> 430.420
        342.483 --> 342.400
    After these corrections the following mouse_ids are still missing from the excel sheet:
    subjects_to_skip = {
        "289.407",
        "244.464",
        "264.477",
        "102.260",
        "262.478",
        "289.408",
        "264.475",
        "129.425",
        "250.427",
        "95.259",
        "309.399",
        "433.421",
        "416.405",
        "364.426",
    }

### Active Questions
None

# Final Notes
## Double Checks and Lingering Questions
These checks/questions should be directed to the Lerner Lab in their final review:
- Double-check skipped MSNs
- Double-check skipped subject_ids
- Double-check session descriptions
- In one session, FP Experiments/Photometry/RR20/late/Photo_96_259-190506-105642, doesn't have any RNnR TTLs, even though it has plenty of right nose pokes in the behavioral file. Can you look into this?
