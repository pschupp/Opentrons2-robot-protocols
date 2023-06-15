import datetime
import inspect
import json
import math
import os
import sys
import time

print(os.system("pwd"))
from opentrons import types

metadata = {
    "protocolName": "Lexogen Quant-seq Library kit",
    "author": "Daniel Brody <daniel.brody@ucsf.edu>",
    "source": "Oldham Lab",
    "apiLevel": "2.8",
}


def lineno():
    # returns current line number
    return inspect.currentframe().f_back.f_lineno


def unique(list1):
    unique_list = []
    for x in list1:
        if x not in unique_list:
            unique_list.append(x)
    for x in unique_list:
        print(x)


def volume_calc(volume, reservoir, numberColumns, overageFactor):
    out = {}
    out["reservoir.type"] = reservoir
    out["reservoir.volume"] = 0
    out["vol.to.add"] = volume
    if volume > 2000:
        sys.exit("volume for one of the reagents is greater than 2200!")
    out["total.volume"] = round(volume * numberColumns * 8 * overageFactor, 2)
    if out["reservoir.type"] == "96well100":
        maxWellVolume = 180
    if out["reservoir.type"] == "96well2000":
        maxWellVolume = 2200
    out["reservoir.number"] = math.ceil(out["total.volume"] / 8 / maxWellVolume)
    if out["reservoir.number"] == 1:
        out["well.uses"] = [math.floor((out["total.volume"] / 8) / out["vol.to.add"])]
        if out["well.uses"][0] > numberColumns:
            out["well.uses"] = [numberColumns]
        out["reservoir.volume"] = round(
            out["total.volume"] / (numberColumns * 8) * out["well.uses"][0], 2
        )
    else:
        uses = 0
        useTrack = []
        remainder = numberColumns
        use = math.floor(maxWellVolume / (out["vol.to.add"] * overageFactor))
        out["reservoir.volume"] = out["vol.to.add"] * overageFactor * use
        out["well.uses"] = [use]
        useTrack.append(use)
        uses = uses + use
        remainder = remainder - uses
        while remainder > use:
            out["well.uses"].append(use)
            remainder = remainder - uses
            useTrack.append(use)
        out["well.uses"].append(remainder)
        useTrack.append(remainder)
        out["reservoir.volume"] = [
            round(out["vol.to.add"] * overageFactor * useMult, 2)
            for useMult in useTrack
        ]
        out["reservoir.number"] = len(out["reservoir.volume"])
    print(out)
    return out


def reagent_assign(reagentVolume, reagentPlate, reagentCounter):
    temp = list(
        zip(
            range(reagentCounter, reagentCounter + reagentVolume["reservoir.number"]),
            reagentVolume["well.uses"],
        )
    )
    out = [reagentPlate["A" + str(i[0])] for i in temp for _ in range(i[1])]
    reagentCounter = reagentCounter + reagentVolume["reservoir.number"]
    return out, reagentCounter


# TODO replace high_mix "bool", with xdir is (not) None for this and p300_mix
def p20_mix(reps, vol, loc, pip, xdir=None, high_mix="F", bead_mix="F"):
    if high_mix == "T":
        # if xdir is None:
        loc1 = loc.bottom(1)
        loc2 = loc.bottom(4)
        loc3 = loc.bottom(3)
    else:
        loc1 = loc.bottom().move(types.Point(x=0, y=0, z=1))
        loc2 = loc.bottom().move(types.Point(x=1.5 * xdir, y=0, z=6))
        loc3 = loc.bottom().move(types.Point(x=0, y=0, z=5))
    pip.aspirate(1, loc1)
    mvol = vol - 1.5
    pip.aspirate(10, loc1)
    pip.dispense(10, loc3)
    pip.aspirate(9, loc1)
    pip.dispense(10, loc3)
    for _ in range(reps - 1):
        pip.aspirate(mvol, loc1)
        pip.dispense(mvol, loc2)
    if high_mix == "F":
        # if xdir is not None:
        pip.dispense(20, loc3)
        pip.aspirate(10, loc2)
        pip.dispense(20, loc3)
        pip.aspirate(10, loc2)
        pip.dispense(20, loc3)
    pip.flow_rate.aspirate = 10
    pip.flow_rate.dispense = 10
    pip.aspirate(mvol - 3, loc1)
    pip.dispense(mvol, loc2)
    pip.flow_rate.dispense = 30

def p300_mix(reps, vol, loc, pip, xdir, high_mix="F"):
    if high_mix == "T":
        loc1 = loc.bottom(1)
        loc2 = loc.bottom(9)
    else:
        loc1 = loc.bottom().move(types.Point(x=0, y=0, z=1))
        loc2 = loc.bottom().move(types.Point(x=1.5 * xdir, y=0, z=4.5))
    pip.aspirate(5, loc1)
    mvol = vol - 10
    for _ in range(reps - 1):
        pip.aspirate(mvol, loc1)
        pip.dispense(mvol, loc2)
    pip.flow_rate.aspirate = 70
    pip.flow_rate.dispense = 50
    pip.aspirate(mvol, loc1)
    pip.dispense(mvol, loc2)
    pip.dispense(300, loc2)


print(datetime.datetime.now())
overageFactor = 1.1
numberSamples = 96
startWell = 1
SPRI_1_vol = 16
SPRI_2_vol = 35  # more for dual index kit
numberColumns = math.ceil(numberSamples / 8)
reagentCounterInit = 1
reagentRTCounterInit = 1
debug = "no"
start_odd_even = "odd"
# xdir=1 if start_odd_even=="odd" else -1

print(
    "Processing "
    + str(numberSamples)
    + " samples using "
    + str(numberColumns)
    + " columns"
)
p20tipNumber = math.ceil(numberColumns * 6 / 12)
p300tipNumber = math.ceil(numberColumns * 30 / 12)
p20Location = ["4", "5"][:p20tipNumber]
p300Location = [ "9"][:p300tipNumber]
print(
    "Using " + str(p20tipNumber) + " racks of p20 tips in slot(s) " + str(p20Location)
)
print(
    "Using "
    + str(p300tipNumber)
    + " racks of p300 tips in slot(s) "
    + str(p300Location)
)
print(
    "'vol.to.add' refers to the volume added over the entire protocol,i.e. 500*2=1000 ul ethanol"
)

print("FS1 Master Mix")
fs1_mm_volume = volume_calc(5, "96well100", numberColumns, overageFactor)
print("FS2/E1 Mix")
fs2e1_mm_volume = volume_calc(10, "96well100", numberColumns, overageFactor)
print("RS Master Mix")
rs_mm_volume = volume_calc(5, "96well100", numberColumns, overageFactor)
print("USS Master Mix")
uss_mm_volume = volume_calc(10, "96well100", numberColumns, overageFactor)
print("SS2/E2 Master Mix")
ss2e2_mm_volume = volume_calc(5, "96well100", numberColumns, overageFactor)
print("PCR/E3 Master Mix")
pcre3_mm_volume = volume_calc(8, "96well100", numberColumns, overageFactor)
print("Mag Bead 1")
mag_bead1_volume = volume_calc(
    (SPRI_1_vol),
    "96well100",
    numberColumns,
    overageFactor,
)
print("Mag Bead 2")
mag_bead2_volume = volume_calc(
    (SPRI_2_vol),
    "96well100",
    numberColumns,
    overageFactor,
)
print("Ethanol")
ethanol_volume = volume_calc(880, "96well2000", numberColumns, overageFactor)
print("Elution Buffer")
elution_buffer_volume = volume_calc(
    40 + 20 + 30 + 20, "96well2000", numberColumns, overageFactor
)
print("Purification Solution")
ps_volume = volume_calc(56 + 30, "96well2000", numberColumns, overageFactor)


def run(protocol):
    def mastermix_transfer(
        pip, tips, reagent_well, sample_well, transfer_vol, mix_type="norm_mix"
    ):
        pip.flow_rate.aspirate = 10  # set rate back to the rate from before
        pip.flow_rate.dispense = 30
        pip.pick_up_tip(tips[0])
        # TODO change vol back
        p20_mix(2, 10, reagent_well[0], pip, high_mix="T")
        # pip.blow_out(reagent_well[0].top())
        for tip, r_well, s_well in zip(tips, reagent_well, sample_well):
            if not pip.hw_pipette["has_tip"]:
                pip.pick_up_tip(tip)
            p20_mix(1, 5, r_well, pip, high_mix="T")  # TODO change volumes
            tvol = transfer_vol
            asp_ctr = 0
            while tvol > 18:
                pip.aspirate(18, r_well.bottom(1))
                pip.aspirate(1, r_well.top())
                pip.dispense(20, s_well.top(-10))
                # pip.touch_tip(v_offset=-8)
                tvol = tvol - 18
                asp_ctr = asp_ctr + 1
            pip.flow_rate.aspirate = 2
            if mix_type == "thick_mix":
                pip.aspirate(tvol - 2, r_well.bottom(0.5))
                pip.aspirate(2, r_well.bottom(0.4))
                protocol.delay(seconds=5)
                pip.touch_tip(v_offset=-8)
            elif mix_type == "bead_mix":
                pip.aspirate(tvol - 2, r_well.bottom(0.5))
                pip.aspirate(2, r_well.bottom(0.35))
                pip.aspirate(0.02, r_well.bottom(0.4))
                protocol.delay(seconds=6)
            else:
                pip.aspirate(tvol, r_well.bottom(0.3))
                protocol.delay(seconds=3)
            pip.dispense(20, s_well.top(-8))
            pip.flow_rate.aspirate = 10
            if mix_type == "bead_mix":
                p20_bead_mix(8, 17, s_well, pip)
            else:
                p20_mix(8, 17, s_well, pip, high_mix="T")
            pip.dispense(20, s_well.top(-8))
            pip.blow_out(s_well.top(-6))
            pip.touch_tip(v_offset=-8)
            pip.drop_tip()
        pip.flow_rate.aspirate = 50  # set rate back to the rate from before
        pip.flow_rate.dispense = 90

    mag_max, warm_max = 3, 4

    startWell = 1
    # numberColumns = 2

    # numberColumns = 2

    #load Labware/Modules
    magdeck = protocol.load_module("magnetic module gen2", "1")
    print("magnetic module in slot 1")
    magheight = 7.5  # TODO figure out ????
    magplate = magdeck.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", "Mag_Sample_Plate"
    )
    liqwaste = protocol.load_labware("nest_1_reservoir_195ml", "11", "Liquid Waste")
    print(
        "liquid waste in slot 11"
    )  # TODO We probably want to put waste in RT reagent plate
    waste = liqwaste["A1"].top()
    
    thermocycler = protocol.load_module("thermocycler")
    print("thermocycler in slot 7,8,10,11")
    thermo_plate = thermocycler.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    
    tempdeck = protocol.load_module("temperature module gen2", "6")
    print("thermal module in slot 6")
    warm_plate = tempdeck.load_labware(
        "opentrons_96_aluminumblock_nest_wellplate_100ul", "Warm_Sample_Plate"
    )
    
    rt_reagents = protocol.load_labware("nest_96_wellplate_2ml_deep", "2")
    print("rt_reagents 96-well plate in slot 3")
    mm_plate = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "3")
    print("cold 96-well plate in slot 2")
    
    tips20 = [
        protocol.load_labware("opentrons_96_tiprack_20ul", s) for s in p20Location
    ]
    p20_tips = [tr["A" + str(i)] for tr in tips20 for i in range(1, 13)]
    [tips_1, tips_2, tips_3, tips_4, tips_5, tips_6] = [
        p20_tips[i : i + numberColumns]
        for i in range(0, numberColumns * 6, numberColumns)
    ]
    tips300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", s) for s in p300Location
    ]
    p300_tips = [tr["A" + str(i)] for tr in tips300 for i in range(1, 13)]
    [
        TIPS_1,
        TIPS_2,
        TIPS_3,
        TIPS_4,
        TIPS_5,
        TIPS_6,
        TIPS_7,
        TIPS_8,
        TIPS_9,
        TIPS_10,
        TIPS_11,
        TIPS_12,
        TIPS_13,
        TIPS_14,
        TIPS_15,
        TIPS_16,
        TIPS_17,
        TIPS_18,
        TIPS_19,
        TIPS_20,
    ] = [
        p300_tips[i : i + numberColumns]
        for i in range(0, numberColumns * 20, numberColumns)
    ]
    print(TIPS_1)
    print(TIPS_2)
    p20 = protocol.load_instrument("p20_multi_gen2", "right", tip_racks=tips20)
    print("p20 multichannel mounted on right arm")
    p300 = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=tips300)
    print("p300 multichannel mounted on left arm")
    p300.flow_rate.aspirate = 50  # reduced from 94
    p300.flow_rate.dispense = 150  # increased from from 94
    p300.flow_rate.blow_out = 300  # increased from 94
    p20.flow_rate.aspirate = 60
    p20.flow_rate.dispense = 150
    p20.flow_rate.blow_out = 300
    fs1_mm, reagentCounter = reagent_assign(fs1_mm_volume, mm_plate, reagentCounterInit)
    fs2e1_mm, reagentCounter = reagent_assign(fs2e1_mm_volume, mm_plate, reagentCounter)
    rs_mm, reagentCounter = reagent_assign(rs_mm_volume, mm_plate, reagentCounter)
    uss_mm, reagentCounter = reagent_assign(uss_mm_volume, mm_plate, reagentCounter)
    ss2e2_mm, reagentCounter = reagent_assign(ss2e2_mm_volume, mm_plate, reagentCounter)
    pcre3_mm, reagentCounter = reagent_assign(pcre3_mm_volume, mm_plate, reagentCounter)
    mag_bead1, reagentCounter = reagent_assign(
        mag_bead1_volume, mm_plate, reagentCounter
    )
    mag_bead2, reagentCounter = reagent_assign(
        mag_bead2_volume, mm_plate, reagentCounter
    )
    ethanol, reagentRTCounter = reagent_assign(
        ethanol_volume, rt_reagents, reagentRTCounterInit
    )
    elution_buffer, reagentRTCounter = reagent_assign(
        elution_buffer_volume, rt_reagents, reagentRTCounter
    )
    ps, reagentRTCounter = reagent_assign(ps_volume, rt_reagents, reagentRTCounter)

    """
    # TODO finish this
    mag_samps, warm_samps, col_numss, xdirss = [], [], [], []
    for ns in range(max(mag_max, warm_max)):
        col_nums = list(
            range(startWell + numberColumns * ns, startWell + (ns + 1) * numberColumns)
        )
        # col_nums = list(
        #     range(startWell + numberColumns * ns, startWell + ns * numberColumns + numberColumns)
        # )


        col_numss.append(col_nums)
        xdirss.append([1 if col_num % 2 else -1 for col_num in col_nums])

        if ns <= warm_max:
            warm_samps.append([warm_plate["A" + str(i)] for i in col_nums])
        if ns <= mag_max:
            mag_samps.append([magplate["A" + str(i)] for i in col_nums])
    
    """
    col_nums = list(range(startWell, startWell + numberColumns, 1))
    xdirss = [1 if col_num % 2 else -1 for col_num in col_nums]

    mag_sample = [
        magplate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    ]
    warm_sample = [
        warm_plate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    ]

    # mag_sample_1=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
    # mag_sample_2=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
    # mag_sample_3=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
    # cold_sample_1 = [
    #     cold_plate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    # ]
    # cold_sample_2 = [
    #     cold_plate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    # ]
    # cold_sample_3 = [
    #     cold_plate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    # ]
    # cold_sample_4 = [
    #     cold_plate["A" + str(i)] for i in range(startWell, startWell + numberColumns, 1)
    # ]
    # TODO Figure out next sample well situation
    # Only using 'cold_plate' for samples not in magplate,so I need to figure out the flow of plates and columns; Fragmentation; PolyA selection (Last elution with 15ul Fragmentation Master Mix); Run Thermocycler off deck; return sample to magdeck when program has competed

    print("\n")
    print("FS1 mastermix here:")
    print(fs1_mm_volume["reservoir.volume"])
    print(unique(fs1_mm))
    print("\n")
    print("FS2/E1 master mix here:")
    print(fs2e1_mm_volume["reservoir.volume"])
    print(unique(fs2e1_mm))
    print("\n")
    print("RS mm here:")
    print(rs_mm_volume["reservoir.volume"])
    print(unique(rs_mm))
    print("\n")
    print("USS mm here:")
    print(uss_mm_volume["reservoir.volume"])
    print(unique(uss_mm))
    print("\n")
    print("SS2/E2 here:")
    print(ss2e2_mm_volume["reservoir.volume"])
    print(unique(ss2e2_mm))
    print("\n")
    print("PCR/E3 here:")
    print(pcre3_mm_volume["reservoir.volume"])
    print(unique(pcre3_mm))
    print("\n")
    print("mag bead 1 here:")
    print(mag_bead1_volume["reservoir.volume"])
    print(unique(mag_bead1))
    print("\n")
    print("mag bead 2 here:")
    print(mag_bead2_volume["reservoir.volume"])
    print(unique(mag_bead2))
    print("\n")
    
    print("ethanol here:")
    print(ethanol_volume["reservoir.volume"])
    print(unique(ethanol))
    print("\n")
    print("elution buffer here:")
    print(elution_buffer_volume["reservoir.volume"])
    print(unique(elution_buffer))
    print("\n")
    print("purification solution here:")
    print(ps_volume["reservoir.volume"])
    print(unique(ps))
    print("\n")

    print("Guess what line it is...", lineno())
    
    ##############################################################################################################################
    """
    thermocycler.set_block_temperature(4, hold_time_seconds=15, hold_time_minutes=45, block_max_volume=50)
    thermocycler.set_block_temperature(4, hold_time_seconds=60, ramp_rate=0.5) #°C/sec
    
    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    thermocycler.set_lid_temperature(108)

    profile = [
        {'temperature': 98, 'hold_time_minutes': 2},
        {'temperature': 98, 'hold_time_seconds': 20},
        {'temperature': 60, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_seconds': 30},
        {'temperature': 72, 'hold_time_minutes': 1},
    ]
    thermocycler.close_lid()
    thermocycler.execute_profile(steps=profile[:1],
                                 repetitions=1,
                                 block_max_volume=50)
    thermocycler.execute_profile(steps=profile[1:4],
                                 repetitions=tc_num_reps,
                                 block_max_volume=50)
    thermocycler.execute_profile(steps=profile[4:],
                                 repetitions=1,
                                 block_max_volume=50)
    thermocycler.set_block_temperature(4, block_max_volume=20.5)
    thermocycler.open_lid()


    """
    ###################################################################################################################################
    #tempdeck.set_temperature(42)
    thermocycler.open_lid()
    if thermocycler.lid_position != 'open':
        thermocycler.open_lid()
    thermocycler.set_lid_temperature(108)

    # Transfer FS1
    print(mag_sample)
    mastermix_transfer(p20, tips_1, fs1_mm, mag_sample, 5.5)
    
    #Incubate sample on thermocycler for 3min at 85C, then cool down to 42C"
    thermocycler.close_lid()
    thermocycler.set_block_temperature(85, hold_time_minutes=3, block_max_volume=12)
    thermocycler.set_block_temperature(42, block_max_volume=12)
    thermocycler.open_lid()
    protocol.comment("Line 515")

    # FS2/E1
    protocol.comment("pre-warm MasterMix 3min at 42C")
    protocol.comment("spin down samples")

    # Transfer FS2/E1
    mastermix_transfer(p20, tips_2, fs2e1_mm, warm_sample, 10.5)
    #tempdeck.deactivate()
    
    #Incubate sample on thermocycler for 15min at 42C
    thermocycler.close_lid()
    thermocycler.set_block_temperature(42, hold_time_minutes=15, block_max_volume=25)
    thermocycler.set_block_temperature(20, block_max_volume=25)
    thermocycler.open_lid()
    protocol.comment("Line 530")
    protocol.comment("spin down samples")

    # temp_mod.deactivate()
    # tempdeck.deactivate()

    # Transfer RS
    mastermix_transfer(p20, tips_3, rs_mm, mag_sample, 5.5)
    #tempdeck.set_temperature(37)

    #Incubate sample on thermocycler for 10min at 95C
    thermocycler.close_lid()
    thermocycler.set_block_temperature(95, hold_time_minutes=10, block_max_volume=30)
    thermocycler.set_block_temperature(25, block_max_volume=25)
    thermocycler.open_lid()
    #tempdeck.deactivate()
    protocol.comment("Line 546")

    # Transfer USS (UMI second strand mix)
    protocol.comment("Thaw USS at 37C")
    mastermix_transfer(p20, tips_4, uss_mm, mag_sample, 10.5, mix_type="thick_mix")

    #Incubate sample on thermocycler for 1min at 98C, slowly cool down to 25 °C at a reduced ramp speed of 0.5 °C/second. Then 30min at 25C
    thermocycler.close_lid()
    thermocycler.set_block_temperature(98, hold_time_minutes=1, block_max_volume=42)
    thermocycler.set_block_temperature(25, hold_time_minutes=30, ramp_rate=0.5, block_max_volume=42)
    thermocycler.open_lid()
    protocol.comment("spin down samples")
    protocol.comment("Line 558")
    print("You made it to line...", lineno())

    # Transfer SS2/E2
    protocol.comment("Keep mastermix at RT")
    mastermix_transfer(p20, tips_5, ss2e2_mm, mag_sample, 5.5)

    #Incubate sample on thermocycler for 15min at 25C
    thermocycler.close_lid()
    thermocycler.set_block_temperature(25, hold_time_minutes=15, block_max_volume=50)
    thermocycler.open_lid()
    
    protocol.comment("Spin down samples")
    protocol.comment("Safe Stopping point, store at -20")
    protocol.comment("Line 572")

    protocol.comment("Part 1 complete!")
    
