# Notes concerning the seiler_2024 conversion split by interface

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

In FP Experiments/Behavior/PS/139.298,
- one of the sessions (ex. 09/20/19) is actually from subject 144.306
- 144.306 is a ghost -- it doesn't show up in any of the behavior folders and not in the mosue demographics google sheet

In FP Experiments/Behavior/PS/140.306,
- one of the sessions (ex. 09/06/19) has a bunch of garbage to the right of the 'A' variable

In FP Experiments/Behavior/MEDPCRawFilesbyDate/2018-11-09,
- All the sessions have the same start_date and start_time and no subject info --> need to make medpc reader support
more generic filter conditions (ex. box number)

### Opto Behavior
- Opto Behavior files are disorganized esp. DLS Excitatory with a mix of folders, medpc files, and csv files
- File structure also contains important metadata for optogenetic interface ex. ChR2 vs EYFP
- Plan: Swing back around to opto behavior when constructing optogenetic interface

## Fiber Photometry
- 6 data streams:
    - Dv1A = array of photometry response dms 465nm
    - Dv2A = array of photometry response dms 405nm
    - Dv3B = array of photometry response dls 465nm
    - Dv4B = array of photometry response dls 405nm
    - Fi1d = 4xN array of demodulated commanded voltages: dms 465nm, dms 405nm, dls 465nm, dls 405nm
    - Fi1r = 2xN array of modulated commanded voltages: dms and dls
- Questions for Lerner Lab:
    - The TTL for 'unrewarded right nose pokes' (RNnR), corresponds to the nose pokes variable in medpc, which supposedly
    records *all* nosepokes. Which is correct?

## Optogenetics
TODO
