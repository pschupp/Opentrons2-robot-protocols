import datetime
import math

import numpy
from opentrons import types


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
    if out["reservoir.type"] == "96well":
        maxWellVolume = 2000
    if out["reservoir.type"] == "seperate_96well":
        maxWellVolume = 2000
    out["reservoir.number"] = math.ceil(out["total.volume"] / 8 / maxWellVolume)
    if out["reservoir.number"] == 1:
        out["well.uses"] = [math.floor(maxWellVolume / out["vol.to.add"])]
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
    print('Debug start:')
    print(reagentVolume)
    print(reagentPlate)
    print(reagentCounter)
    out = [reagentPlate["A" + str(i[0])] for i in temp for _ in range(i[1])]
    reagentCounter = reagentCounter + reagentVolume["reservoir.number"]
    return out, reagentCounter


def well_mix(reps, loc, vol, pip):
    loc1 = loc.bottom().move(types.Point(x=0.7, y=0, z=1.3))
    loc2 = loc.bottom().move(types.Point(x=-0.9, y=0, z=7))
    pip.aspirate(20, loc1)
    mvol = vol - 20
    for _ in range(reps - 1):
        pip.aspirate(mvol, loc1)
        pip.dispense(mvol, loc2)
    pip.dispense(280, loc2)


def elute_mix(reps, loc, vol, pip, xdir):
    loc1 = loc.bottom().move(types.Point(x=-0.8 * xdir, y=-0.8, z=0.8))
    loc2 = loc.bottom().move(types.Point(x=-0.8 * xdir, y=1, z=0.8))
    loc3 = loc.bottom(2)
    pip.flow_rate.dispense = 200
    for _ in range(reps):
        pip.aspirate(vol, loc1)
        pip.dispense(vol, loc1)
        pip.aspirate(vol, loc2)
        pip.dispense(vol, loc2)
    pip.dispense(100, loc3)
    pip.blow_out()
    pip.flow_rate.dispense = 150


def knock_off(reps, loc, vol, pip, xdir, high_mix="F"):
    if high_mix == "T":
        z_height = 18
    else:
        z_height = 14
    loc1 = loc.bottom().move(types.Point(x=-1 * xdir, y=0, z=4))
    loc2 = loc.bottom().move(types.Point(x=-1 * xdir, y=0, z=z_height))
    loc3 = loc.bottom().move(types.Point(x=-0.8 * xdir, y=1, z=z_height))
    loc4 = loc.bottom().move(types.Point(x=-0.8 * xdir, y=1, z=10))
    loc5 = loc.bottom().move(types.Point(x=1.2 * xdir, y=1, z=z_height))
    loc6 = loc.bottom().move(types.Point(x=1.2 * xdir, y=1, z=10))
    pip.flow_rate.dispense = 90
    for _ in range(reps):
        pip.aspirate(vol, loc1)
        pip.dispense(vol, loc2)
        pip.aspirate(vol, loc3)
        pip.dispense(vol, loc4)
        pip.aspirate(vol, loc5)
        pip.dispense(vol, loc6)
        pip.aspirate(vol, loc1)
        pip.dispense(vol, loc2)
        pip.aspirate(vol, loc1)
        pip.dispense(vol, loc2)
    pip.blow_out()
    pip.flow_rate.dispense = 150


def init_well_mix(reps, loc, vol, pip, xdir, wellVol=499):
    if wellVol > 500:
        zheight = 15
    else:
        zheight = 4
    loc1 = loc.bottom().move(types.Point(x=-1.2 * xdir, y=1, z=0.3))
    loc2 = loc.bottom().move(types.Point(x=-1.2 * xdir, y=1, z=0.3))
    loc3 = loc.bottom().move(types.Point(x=-1.3 * xdir, y=-0.8, z=0.3))
    loc4 = loc.bottom().move(types.Point(x=-1.2 * xdir, y=-0.8, z=0.3))
    loc5 = loc.bottom().move(types.Point(x=0, y=0.4, z=0.1))
    loc6 = loc.bottom().move(types.Point(x=0, y=0.4, z=zheight))
    loc7 = loc.bottom().move(types.Point(x=0, y=0.4, z=zheight - 2))
    loc8 = loc.bottom().move(types.Point(x=1 * xdir, y=0, z=5))
    pip.flow_rate.aspirate = 160
    pip.flow_rate.dispense = 300
    for _ in range(reps):
        pip.aspirate(vol, loc1)
        pip.dispense(vol, loc2)
        pip.aspirate(vol, loc3)
        pip.dispense(vol, loc4)
        pip.aspirate(vol, loc5)
        pip.dispense(vol, loc6)
        pip.aspirate(vol, loc7)
        pip.dispense(vol, loc8)
    pip.dispense(280, loc6)


def wash_mix(reps, loc, vol, pip):
    loc1 = loc.bottom().move(types.Point(x=0.7, y=0, z=1))
    loc2 = loc.bottom().move(types.Point(x=-0.9, y=0, z=1))
    mvol = vol - 20
    for _ in range(reps):
        pip.aspirate(mvol, loc2)
        pip.dispense(mvol, loc1)
    pip.dispense(mvol + 30, loc2)


def fetch_beads(vol, src, sample, dest, pip, tips, usedtips):
    for srcWell, well, tip, tret, destWell in zip(src, sample, tips, usedtips, dest):
        pip.pick_up_tip(tip)
        pip.aspirate(vol, srcWell.bottom(2))
        pip.dispense(vol, well.top())
        init_well_mix(1, well, vol, pip, xdir=xdir, wellVol=vol)
        pip.blow_out()
        pip.flow_rate.aspirate = 130
        pip.aspirate(vol + 20, well.bottom().move(types.Point(x=0, y=0, z=-0.6)))
        pip.dispense(vol + 30, destWell.top())
        pip.blow_out()
        pip.drop_tip(tret)
    pip.flow_rate.aspirate = 60


def supernatant_removal(vol, src, dest, pip, xdir, bead_transfer="F", is_waste="F"):
    if bead_transfer == "T":
        pip.flow_rate.aspirate = 130
    else:
        pip.flow_rate.aspirate = 20
    tvol = vol
    asp_ctr = 0
    while tvol > 250:
        pip.aspirate(250, src.bottom().move(types.Point(x=-1.3 * xdir, y=0, z=0.8)))
        pip.aspirate(10, src.top())
        pip.dispense(250, dest)
        pip.blow_out()
        if is_waste == "T":
            pip.aspirate(5, dest)
        else:
            dest
            pip.aspirate(5, dest.top())
        tvol = tvol - 250
        asp_ctr = asp_ctr + 1
    if bead_transfer == "T":
        pip.aspirate(tvol, src.bottom().move(types.Point(x=0, y=0, z=0.2)))
    else:
        pip.aspirate(tvol, src.bottom().move(types.Point(x=-1.3 * xdir, y=0, z=0.8)))
    dvol = 30 * asp_ctr + tvol
    pip.dispense(dvol, dest)
    pip.blow_out()
    pip.flow_rate.aspirate = 60


def supernatant_removal_mini(vol, src, dest, pip, xdir):
    pip.pick_up_tip()
    pip.aspirate(15, src.bottom().move(types.Point(x=-0.3 * xdir, y=0, z=0.4)))
    pip.dispense(20, dest)
    pip.blow_out()


def wash_step(sample, src, vol, mtimes, tips, usedtips, pip, zheight, xdir):
    for well, tip, tret, srcWell in zip(sample, tips, usedtips, src):
        pip.pick_up_tip(tip)
        tvol = vol
        asp_ctr = 0
        while tvol > 250:
            pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
            pip.aspirate(10, srcWell.top())
            pip.dispense(280, well.top().move(types.Point(x=1.2 * xdir, y=0, z=-10)))
            pip.aspirate(5, well.top())
            tvol = tvol - 250
            asp_ctr = asp_ctr + 1
        pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
        dvol = 20 * asp_ctr + 250
        if dvol > 250:
            dvol = 250
        pip.dispense(dvol, well.top())
        init_well_mix(mtimes, well, 200, pip, xdir=xdir, wellVol=vol)
        pip.blow_out()
        pip.drop_tip(tret)


def wash_step_1_5(sample, src, vol, mtimes, tips, usedtips, pip, zheight, is_etoh="F"):
    for sampleWell, tret in zip(sample, usedtips):
        pip.pick_up_tip(tret)
        if is_etoh == "T":
            knock_off(1, sampleWell, 100, pip, xdir=xdir)
        else:
            pip.aspirate(
                100, sampleWell.bottom().move(types.Point(x=-0, y=1, z=zheight))
            )
            pip.dispense(
                100, sampleWell.bottom().move(types.Point(x=-0, y=1, z=zheight))
            )
            pip.aspirate(
                100, sampleWell.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            pip.dispense(
                100, sampleWell.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            pip.aspirate(
                100, sampleWell.bottom().move(types.Point(x=-0, y=1, z=zheight))
            )
            pip.dispense(
                100, sampleWell.bottom().move(types.Point(x=-0, y=1, z=zheight))
            )
            pip.aspirate(
                100, sampleWell.bottom().move(types.Point(x=-0, y=-1, z=zheight - 4))
            )
            pip.dispense(
                100, sampleWell.bottom().move(types.Point(x=-0, y=-1, z=zheight + 4))
            )
        pip.drop_tip(tret)


def wash_step2(
    sample, src, vol, mtimes, tips, usedtips, pip, waste, xdir, return_tips="F"
):
    for well, tip, utip in zip(sample, tips, usedtips):
        pip.pick_up_tip(tip)
        supernatant_removal(vol, well, waste, pip, xdir, is_waste="T")
        pip.aspirate(5, waste)
        if return_tips == "T":
            pip.return_tip()
        else:
            pip.drop_tip()


metadata = {
    "protocolName": "Zymo Magbead DNA/RNA kit,part 2",
    "author": "Patrick Schupp <patrick.schupp@ucsf.edu>",
    "source": "Oldham Lab",
    "apiLevel": "2.8",
}
print(datetime.datetime.now())
overageFactor = 1.1
numberSamples = 24
startWell = 1
inputVolume = 700
numberColumns = math.ceil(numberSamples / 8)
reagentCounterInit = 1
reagentCounterInit2 = 1
ethanolCounterInit = 1
debug = "no"
start_odd_even = "odd"
xdir = 1 if start_odd_even == "odd" else -1
print(
    "Processing "
    + str(numberSamples)
    + " samples using "
    + str(numberColumns)
    + " columns"
)
p20tipNumber = math.ceil(numberColumns * 2 / 12)
p300tipNumber = math.ceil(numberColumns * 13 / 12)
# p20Location=['7'][:p20tipNumber]
p300Location = [ "5", "6", "7", "8","9"][:p300tipNumber]
# print('Using '+str(p20tipNumber)+' racks of p20 tips in slot(s) '+str(p20Location))
print(
    "Using "
    + str(p300tipNumber)
    + " racks of p300 tips in slot(s) "
    + str(p300Location)
)
print(
    "'vol.to.add' refers to the volume added over the entire protocol,i.e. 500 * 2 = 1000 ul ethanol"
)
print("lysis+beads")
lysMagVolume = volume_calc(730, "96well", numberColumns, overageFactor)
print("lysis+Sheild")
lysisSheildVolume = volume_calc(500, "96well", numberColumns, overageFactor)
print("Magbinding Beads")
magBeadVolume = volume_calc(30, "96well", numberColumns, overageFactor)
print("Wash 1 Buffer")
wash1Volume = volume_calc(500, "96well", numberColumns, overageFactor)
print("Wash 2 Buffer")
wash2Volume = volume_calc(500, "96well", numberColumns, overageFactor)
print("Ethanol Buffer 0")
ethanol0Volume = volume_calc(700, "seperate_96well", numberColumns, overageFactor)
print("Ethanol Buffer 1")
ethanol1Volume = volume_calc(1000, "seperate_96well", numberColumns, overageFactor)
print("Ethanol Buffer 2")
ethanol2Volume = volume_calc(1000, "seperate_96well", numberColumns, overageFactor)
print("Ethanol Buffer 3")
ethanol3Volume = volume_calc(600, "seperate_96well", numberColumns, overageFactor)
print("Ethanol Buffer 4")
ethanol4Volume = volume_calc(1000, "seperate_96well", numberColumns, overageFactor)
print("DNAse I Reaction Mix")
dnaseIReactionMixVolume = volume_calc(50, "96well", numberColumns, overageFactor)
print("DNA/RNA Prep Buffer")
dnaRNAPrepBufferVolume = volume_calc(500, "96well", numberColumns, overageFactor)
print("Water")
waterVolume = volume_calc(60, "96well", numberColumns, overageFactor)


def run(protocol):
    magdeck = protocol.load_module("magnetic module gen2", "1")
    print("magnetic module in slot 8")
    magheight = 6.75
    magplate = magdeck.load_labware(
        "usascientific_96_wellplate_2.4ml_deep", "Sample Plate"
    )
    liqwaste = protocol.load_labware("nest_1_reservoir_195ml", "11", "Liquid Waste")
    print("liquid waste in slot 11")
    waste = liqwaste["A1"].top()
    reagentPlate = protocol.load_labware(
        "nest_96_wellplate_2ml_deep", "2", "Reagent Plate"
    )
    ethanolPlate = protocol.load_labware(
        "usascientific_12_reservoir_22ml", "3", "Ethanol Plate"
    )
    reagentPlate2 = protocol.load_labware(
        "nest_96_wellplate_2ml_deep", "4", "Reagent Plate 2"
    )
    print("reagent 96-well plate in slot 3")
    elutionPlate = protocol.load_labware(
        "usascientific_96_wellplate_2.4ml_deep", "10", "Elution Plate"
    )
    print("elution (DNA) 96-well plate in slot 10")
    tips200 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", s) for s in p300Location
    ]


    #ADD REAL 	ELUTION PLATE HERE PCR PLATE LIKE DNA PROTOCOL, BUT DONT SKIP COLUMNS 


    all_tips = [tr["A" + str(i)] for tr in tips200 for i in range(1, 13)]
    [tips1, tips2, tips3, tips4, tips5, tips6, tips7, tips8, tips9, tips10] = [
        all_tips[i : i + numberColumns]
        for i in range(0, numberColumns * 10, numberColumns)
    ]
    # s_tips = [protocol.load_labware('opentrons_96_tiprack_20ul',s) for s in p20Location]
    # p20=protocol.load_instrument("p20_multi_gen2","right",tip_racks=s_tips)
    # print('p20 multichannel mounted on right arm')
    p300 = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=tips200)
    print("p300 multichannel mounted on left arm")
    p300.flow_rate.aspirate = 50
    p300.flow_rate.dispense = 150
    p300.flow_rate.blow_out = 300

    lysMag, reagentCounter = reagent_assign(
        lysMagVolume, reagentPlate, reagentCounterInit
    )
    lysisSheild, reagentCounter = reagent_assign(
        lysisSheildVolume, reagentPlate, reagentCounter
    )
    magBead, reagentCounter = reagent_assign(
        magBeadVolume, reagentPlate, reagentCounter
    )
    wash1, reagentCounter = reagent_assign(wash1Volume, reagentPlate, reagentCounter)
    wash2, reagentCounter = reagent_assign(wash2Volume, reagentPlate, reagentCounter)
    ethanol1, ethanolCounter = reagent_assign(
        ethanol1Volume, ethanolPlate, ethanolCounterInit
    )
    ethanol2, ethanolCounter = reagent_assign(
        ethanol2Volume, ethanolPlate, ethanolCounter
    )
    ethanol0, ethanolCounter = reagent_assign(
        ethanol0Volume, ethanolPlate, ethanolCounterInit
    )
    ethanol3, ethanolCounter = reagent_assign(
        ethanol3Volume, ethanolPlate, ethanolCounter
    )
    ethanol4, ethanolCounter = reagent_assign(
        ethanol4Volume, ethanolPlate, ethanolCounter
    )
    dnaseIReactionMix, reagentCounter2 = reagent_assign(
        dnaseIReactionMixVolume, reagentPlate2, reagentCounterInit2
    )
    dnaRNAPrepBuffer, reagentCounter2 = reagent_assign(
        dnaRNAPrepBufferVolume, reagentPlate2, reagentCounter2
    )
    water, reagentCounter2 = reagent_assign(waterVolume, reagentPlate2, reagentCounter2)
    sample = [
        magplate["A" + str(i)]
        for i in range(startWell, startWell + numberColumns * 2, 2)
    ]
    print(sample)
    sampleTransfer1 = [
        magplate["A" + str(i)]
        for i in range(startWell + 1, startWell + numberColumns * 2 + 1, 2)
    ]
    print(sampleTransfer1)
    sampleTransfer2 = [
        elutionPlate["A" + str(i)]
        for i in range(startWell + 1, startWell + numberColumns * 2 + 1, 2)
    ]
    print(sampleTransfer2)
    sampleRNA = [
        elutionPlate["A" + str(i)]
        for i in range(startWell, startWell + numberColumns * 2, 2)
    ]
    print(sampleRNA)
    print("\n")
    print("lysis + Mag bead here:")
    print(lysMagVolume["reservoir.volume"])
    print(unique(lysMag))
    print("\n")
    print("lysis + sheild here:")
    print(lysisSheildVolume["reservoir.volume"])
    print(unique(lysisSheild))
    print("\n")
    print("Mag bead here:")
    print(magBeadVolume["reservoir.volume"])
    print(unique(magBead))
    print("\n")
    print("Wash 1 here:")
    print(wash1Volume["reservoir.volume"])
    print(unique(wash1))
    print("\n")
    print("Wash 2 here:")
    print(wash2Volume["reservoir.volume"])
    print(unique(wash2))
    print("\n")
    print("DNAse I reaction mix here:")
    print(dnaseIReactionMixVolume["reservoir.volume"])
    print(unique(dnaseIReactionMix))
    print("\n")
    print("DNA/RNA Prep buffer here:")
    print(dnaRNAPrepBufferVolume["reservoir.volume"])
    print(unique(dnaRNAPrepBuffer))
    print("\n")
    print("Water here:")
    print(waterVolume["reservoir.volume"])
    print(unique(water))
    print("\n")
    print("Ethanol here:")
    print(ethanol0Volume["reservoir.volume"])
    print(unique(ethanol0))
    print(ethanol1Volume["reservoir.volume"])
    print(unique(ethanol1))
    print(ethanol2Volume["reservoir.volume"])
    print(unique(ethanol2))
    print(ethanol3Volume["reservoir.volume"])
    print(unique(ethanol3))
    print(ethanol4Volume["reservoir.volume"])
    print(unique(ethanol4))
    print("\n")
    
    magdeck.disengage()
    i = 1
    """
    for well, reagent, tip in zip(sample, lysMag, tips1):  # TODO measure time
        pipetteSteps = math.ceil(730 / 250)
        pipetteAspirate = 730 / pipetteSteps
        p300.pick_up_tip(tip)
        if i in range(
            1, len(lysMag) + 1, math.ceil(len(lysMag) / len(set(list(lysMag))))
        ):
            init_well_mix(2, reagent, 220, p300, xdir=xdir, wellVol=510)
        for _ in range(pipetteSteps - 1):  # mix in resevoir 4 times.
            init_well_mix(1, reagent, 220, p300, xdir=xdir, wellVol=510)
            p300.aspirate(
                pipetteAspirate, reagent
            )  # pick up 160 ul from reagent 4+1 times, 800 ul.
            p300.aspirate(10, reagent.top())
            p300.dispense(
                pipetteAspirate + 40, well.top(-5)
            )  # drop 160 ul 5mm below top of magwell
            p300.aspirate(10, well.top())  # aspirate 10 ul at current position
        p300.aspirate(pipetteAspirate, reagent)  # final mix
        p300.dispense(
            pipetteAspirate + 40, well.top(-15)
        )  # dispense 160 +40 ul extra picked up from previous run, probably mostly air
        init_well_mix(1, well, 200, p300, xdir=xdir)
        p300.aspirate(
            10, well.top()
        )  # this must again be to remove any droplets hanging on
        p300.drop_tip()
        i = i + 1
    
    protocol.pause("Mix off deck for 30 min")
    # 	protocol.delay(minutes=30) # only use delay if you are mixing off deck                                                                                                                      ) #this is for protocols mixing off deck
    protocol.comment("move sample plate to mixer")

    magdeck.engage(height=magheight)
    protocol.comment("Incubating on magdeck for 4 minutes")
    protocol.delay(minutes=4)  # TODO how much time does it really take!
    for well, tip, tret in zip(sample, tips2, tips2):  # TODO measure time
        p300.pick_up_tip(tip)
        init_well_mix(1, well, 200, p300, xdir=xdir)
        p300.return_tip()
    protocol.delay(minutes=3)
    for well, tip, tret in zip(sample, tips2, tips2):  # TODO measure time
        p300.pick_up_tip(tip)
        knock_off(1, well, 100, p300, xdir=xdir)
        p300.drop_tip()
    protocol.delay(minutes=5)
    protocol.comment("Removing supernatant:")
    protocol.max_speeds["Z"] = 200  # limit x axis to 200 mm/s
    
    for well, tip, sampleRNAWell in zip(
        sample, tips3, sampleRNA
    ):  # TODO in example protocol, this is repeated again with different tips
        p300.pick_up_tip(tip)
        supernatant_removal(900, well, sampleRNAWell, p300, xdir)
        p300.drop_tip()
    
    magdeck.disengage()
    '''
    wash_step(sample, lysisSheild, 500, 4, tips4, tips4, p300, zheight=10, xdir=xdir)
    '''
    protocol.pause("RNA has transfered, swap with DNA")

    for well, reagent, tip in zip(sample, ethanol0, tips5):
        pipetteSteps = math.ceil(inputVolume / 250)
        pipetteAspirate = inputVolume / pipetteSteps
        p300.pick_up_tip(tip)
        for _ in range(pipetteSteps - 1):
            p300.aspirate(pipetteAspirate, reagent)
            p300.dispense(pipetteAspirate, well.top())
            p300.aspirate(10, well.top())
        p300.aspirate(pipetteAspirate, reagent)
        p300.dispense(pipetteAspirate + 40, well.top())
        init_well_mix(2, well, 250, p300, xdir, 1400)
        p300.blow_out()
        p300.aspirate(10, well.top(-2))
        p300.drop_tip()
    i = 1
    volumeMix = 30 * numberColumns
    if volumeMix > 280:
        volumeMix = 280
    for well, reagent, tip in zip(sample, magBead, tips6):
        p300.pick_up_tip(tip)
        if i == 1:
            init_well_mix(2, reagent, volumeMix, p300, xdir)
        init_well_mix(1, reagent, volumeMix, p300, xdir=xdir)
        p300.aspirate(30, reagent.bottom())
        p300.dispense(40, well.top(-10))
        init_well_mix(1, well, 200, p300, xdir)
        p300.aspirate(10, well.top())
        p300.return_tip()
        i = i + 1
    protocol.pause("Shake for 30 min")
    # 	protocol.delay(minutes=31)
    """
    protocol.comment("move sample plate to mixer")
    magdeck.engage(height=magheight)
    protocol.comment("Incubating on magdeck for 10 minutes with mixes")
    protocol.delay(minutes=3)
    for well, tip, tret in zip(sample, tips6, tips6):
        p300.pick_up_tip(tip)
        init_well_mix(1, well, 120, p300, xdir=xdir)
        p300.return_tip()
    protocol.delay(minutes=2)
    for well, tip, tret in zip(sample, tips6, tips6):
        p300.pick_up_tip(tip)
        knock_off(1, well, 120, p300, xdir=xdir, high_mix="T")
        p300.drop_tip()
    protocol.delay(minutes=5)
    protocol.comment("Removing supernatant:")
    step5Volume = inputVolume * 2 + 30 + 100
    for well, tip, tret in zip(sample, tips7, tips7):
        p300.pick_up_tip(tip)
        supernatant_removal(step5Volume - 500, well, waste, p300, xdir, is_waste="T")
        p300.return_tip()
    for well, tip, tret in zip(sample, tips7, tips7):
        p300.pick_up_tip(tip)
        supernatant_removal(500, well, waste, p300, xdir, is_waste="T")
        p300.drop_tip()
    protocol.max_speeds["Z"] = 300
    magdeck.disengage()
    protocol.comment("Washing!")
    wash_step(sample, wash1, 500, 4, tips8, tips8, p300, zheight=10, xdir=xdir)
    magdeck.engage(height=magheight)
    protocol.delay(minutes=3)
    wash_step_1_5(sample, wash1, 500, 5, tips8, tips8, p300, zheight=7)
    protocol.delay(minutes=4)
    wash_step2(sample, wash1, 500, 5, tips8, tips8, p300, waste, xdir)
    magdeck.disengage()
    wash_step(sample, wash2, 500, 4, tips9, tips9, p300, zheight=10, xdir=xdir)
    magdeck.engage(height=magheight)
    protocol.delay(minutes=3)
    wash_step_1_5(sample, wash2, 500, 5, tips9, tips9, p300, zheight=7)
    protocol.delay(minutes=4)
    wash_step2(sample, wash2, 500, 5, tips9, tips9, p300, waste, xdir)
    
    magdeck.disengage()
    wash_step(sample, ethanol1, 1000, 4, tips10, tips10, p300, zheight=15, xdir=xdir)
    magdeck.engage(height=magheight)
    protocol.delay(minutes=2)
    wash_step_1_5(
        sample, ethanol1, 1000, 5, tips10, tips10, p300, zheight=15, is_etoh="T"
    )
    protocol.delay(minutes=4)
    wash_step2(
        sample,
        ethanol1,
        500,
        5,
        tips10,
        tips10,
        p300,
        waste,
        xdir=xdir,
        return_tips="T",
    )
    wash_step_1_5(
        sample, ethanol1, 500, 5, tips10, tips10, p300, zheight=15, is_etoh="T"
    )
    wash_step2(sample, ethanol1, 500, 5, tips10, tips10, p300, waste, xdir=xdir)
    magdeck.disengage()
    for well, tip, tret, srcWell, dest in zip(
        sample, tips1, tips1, ethanol2, sampleTransfer1
    ):
        p300.pick_up_tip(tip)
        tvol = 600
        asp_ctr = 0
        while tvol > 250:
            p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
            p300.aspirate(10, srcWell.top())
            p300.dispense(280, well.top(-10))
            p300.aspirate(5, well.top())
            tvol = tvol - 250
            asp_ctr = asp_ctr + 1
        p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
        dvol = 20 * asp_ctr + 250
        if dvol > 250:
            dvol = 250
        p300.dispense(dvol, well.top())
        init_well_mix(3, well, 200, p300, xdir=xdir)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        p300.aspirate(5, dest.top())
        p300.blow_out()
        p300.drop_tip()
    fetch_beads(200, ethanol2, sample, sampleTransfer1, p300, tips2, tips2)
    
    sample = sampleTransfer1
    
    magdeck.engage(height=magheight)
    protocol.delay(minutes=2)
    wash_step_1_5(sample, ethanol2, 600, 5, tips2, tips2, p300, zheight=15, is_etoh="T")
    protocol.delay(minutes=4)
    wash_step2(sample, ethanol2, 850, 5, tips2, tips2, p300, waste, xdir=xdir * -1)
    magdeck.disengage()




    for well, reagent, tip, tret in zip(sample, dnaseIReactionMix, tips3, tips3):
        p300.pick_up_tip(tip)
        p300.aspirate(50, reagent)
        p300.dispense(80, well.top(-20))
        elute_mix(2, well, 45, p300, xdir=xdir * -1)
        p300.drop_tip(tret)
    for _ in range(2):
        for well, tip, tret in zip(sample, tips3, tips3):
            p300.pick_up_tip(tip)
            elute_mix(2, well, 45, p300, xdir=xdir * -1)
            p300.drop_tip(tret)
   
 
    wash_step(
        sample, dnaRNAPrepBuffer, 500, 2, tips4, tips4, p300, zheight=10, xdir=xdir * -1
    )
    # 	protocol.delay(minutes=11)
    protocol.comment("move sample plate to mixer")
    protocol.pause("Shake for 10 min")

    magdeck.engage(height=magheight)
    protocol.delay(minutes=2)

    wash_step_1_5(sample, dnaRNAPrepBuffer, 500, 5, tips4, tips4, p300, zheight=7)
    protocol.delay(minutes=4)
    wash_step2(
        sample, dnaRNAPrepBuffer, 600, 5, tips4, tips4, p300, waste, xdir=xdir * -1
    )
    magdeck.disengage()
    protocol.comment("Transfering")
    for well, tip, tret, srcWell, dest in zip(
        sample, tips5, tips5, ethanol3, sampleTransfer2
    ):
        p300.pick_up_tip(tip)
        tvol = 600
        asp_ctr = 0
        while tvol > 250:
            p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
            p300.aspirate(10, srcWell.top())
            p300.dispense(280, well.top(-10))
            p300.aspirate(5, well.top())
            tvol = tvol - 250
            asp_ctr = asp_ctr + 1
        p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
        dvol = 20 * asp_ctr + 250
        if dvol > 250:
            dvol = 250
        p300.dispense(dvol, well.top())
        init_well_mix(3, well, 200, p300, xdir=xdir)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        wash_mix(3, well, 200, p300)
        supernatant_removal(200, well, dest, p300, xdir=xdir, bead_transfer="T")
        p300.aspirate(5, dest.top())
        p300.blow_out()
        p300.drop_tip()

    fetch_beads(200, ethanol2, sample, sampleTransfer2, p300, tips6, tips6)
    magdeck.engage(height=magheight)
    protocol.pause("do you want to switch to the pcr plate switch script?")
    protocol.pause("Move sample to magnet!")
    protocol.delay(minutes=2)
    wash_step_1_5(sample, ethanol3, 600, 5, tips6, tips6, p300, zheight=7, is_etoh="T")
    protocol.delay(minutes=3)
    wash_step2(sample, ethanol3, 850, 5, tips6, tips6, p300, waste, xdir=xdir * -1)
    magdeck.disengage()
    protocol.comment("!!!!!!!!REPLACE TIPS 1,2,AND 3!!!!!!")
    wash_step(sample, ethanol4, 1000, 3, tips7, tips7, p300, zheight=15, xdir=xdir * -1)
    magdeck.engage(height=magheight)
    protocol.delay(minutes=2)
    wash_step_1_5(
        sample, ethanol4, 1000, 5, tips7, tips7, p300, zheight=15, is_etoh="T"
    )
    protocol.delay(minutes=3)

    wash_step2(
        sample,
        ethanol4,
        700,
        5,
        tips7,
        tips7,
        p300,
        waste,
        xdir=xdir * -1,
        return_tips="T",
    )
    wash_step_1_5(sample, ethanol4, 700, 5, tips7, tips7, p300, zheight=15, is_etoh="T")
    wash_step2(
        sample,
        ethanol4,
        500,
        5,
        tips7,
        tips7,
        p300,
        waste,
        xdir=xdir * -1,
        return_tips="T",
    )
    protocol.comment("Allowing beads to air dry for 5 minutes.")
    protocol.delay(minutes=4)
    for src, tip in zip(sample, tips7):
        p300.pick_up_tip(tip)
        p300.aspirate(65, src.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300.dispense(100, waste)
        p300.drop_tip()
    protocol.delay(minutes=3)
    magdeck.disengage()
    protocol.comment("Adding NF-Water to wells for elution:")
    for well, tip, tret, waterWell in zip(sample, tips8, tips8, water):
        p300.pick_up_tip(tip)
        p300.aspirate(70, waterWell)
        p300.dispense(80, well)
        elute_mix(2, well, 60, p300, xdir=xdir)
        p300.blow_out()
        p300.drop_tip(tret)
    # 	protocol.delay(minutes=11)
    protocol.comment("move sample plate to mixer")
    protocol.pause("Shake for 10 min")
    magdeck.engage(height=magheight)
    protocol.comment("Incubating on MagDeck for 1.5 minutes.")
    protocol.delay(minutes=1.5)
    for well, tip, tret in zip(sample, tips8, tips8):
        p300.pick_up_tip(tip)
        elute_mix(2, well, 30, p300, xdir=xdir)
        p300.blow_out()
        p300.drop_tip()
    protocol.comment("Incubating on MagDeck for 4 minutes.")
    protocol.delay(minutes=4)
    protocol.comment("Transferring elution to final plate:")
    p300.flow_rate.aspirate = 10
    for src, dest, tip in zip(sample, sampleRNA, tips9):
        p300.pick_up_tip(tip)
        p300.aspirate(60, src.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300.dispense(100, dest)
        p300.drop_tip()
    # 	magdeck.disengage()
    protocol.comment("Congratulations!")
