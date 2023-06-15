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
    print("Debug start:")
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
    pip.flow_rate.aspirate = 200
    pip.flow_rate.dispense = 400
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


# fetch beads adds etoh to residual beads after a transfer then asperates and transfers the left over beads
def fetch_beads(
    vol, src, l_sample, r_sample, l_dest, r_dest, l_pip, r_pip, l_tips, r_tips
):
    for srcWell, l_well, r_well, l_tip, r_tip, l_destWell, r_destWell in zip(
        src, l_sample, r_sample, l_tips, r_tips, l_dest, r_dest
    ):
        l_pip.pick_up_tip(l_tip)
        l_pip.aspirate(vol, srcWell.bottom(2))
        l_pip.dispense(vol, l_well.top())
        init_well_mix(1, l_well, vol, l_pip, xdir=xdir, wellVol=vol)
        l_pip.blow_out()
        l_pip.flow_rate.aspirate = 130
        l_pip.aspirate(vol + 20, l_well.bottom().move(types.Point(x=0, y=0, z=-0.2)))
        l_pip.dispense(vol + 30, l_destWell.top())
        l_pip.blow_out()
        l_pip.return_tip()

        r_pip.pick_up_tip(r_tip)
        r_pip.aspirate(vol, srcWell.bottom(2))
        r_pip.dispense(vol, r_well.top())
        init_well_mix(1, r_well, vol, r_pip, xdir=xdir, wellVol=vol)
        r_pip.blow_out()
        r_pip.flow_rate.aspirate = 130
        r_pip.aspirate(vol + 20, r_well.bottom().move(types.Point(x=0, y=0, z=-0.2)))
        r_pip.dispense(vol + 30, r_destWell.top())
        r_pip.blow_out()
        r_pip.return_tip()
    l_pip.flow_rate.aspirate = 60
    r_pip.flow_rate.aspirate = 60


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


# wash_step is used to add reagent to sample wells then mix to dislodge beads
def wash_step(
    lsample,
    rsample,
    src,
    vol,
    mtimes,
    ltips,
    rtips,
    l_pip,
    r_pip,
    xdir, 
    drop_tip="F"
):
    for l_well, r_well, l_tip, r_tip, srcWell in zip(
        lsample, rsample, ltips, rtips, src
    ):
        l_pip.pick_up_tip(l_tip)
        r_pip.pick_up_tip(r_tip)
        tvol = vol
        asp_ctr = 0
        while tvol > 250:
            l_pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
            l_pip.aspirate(10, srcWell.top())
            r_pip.aspirate(1, srcWell.top(10))
            r_pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
            r_pip.aspirate(10, srcWell.top())
            l_pip.dispense(
                280, l_well.top().move(types.Point(x=1.2 * xdir, y=0, z=-10))
            )
            l_pip.aspirate(5, l_well.top())
            r_pip.dispense(
                280, r_well.top().move(types.Point(x=1.2 * xdir, y=0, z=-10))
            )
            r_pip.aspirate(5, r_well.top())
            tvol = tvol - 250
            asp_ctr = asp_ctr + 1
        l_pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
        l_pip.aspirate(10, srcWell.top())
        l_pip.touch_tip(v_offset=-5)
        r_pip.aspirate(1, srcWell.top(10))
        r_pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1)))
        r_pip.aspirate(10, srcWell.top())
        r_pip.touch_tip(v_offset=-5)
        dvol = 20 * asp_ctr + 250
        if dvol > 250:
            dvol = 250
        l_pip.dispense(dvol, l_well.top())
        init_well_mix(mtimes, l_well, 200, l_pip, xdir=xdir, wellVol=vol)
        l_pip.blow_out()
        l_pip.touch_tip(v_offset=-5)
        r_pip.dispense(dvol, r_well.top())
        init_well_mix(mtimes, r_well, 200, r_pip, xdir=xdir, wellVol=vol)
        r_pip.blow_out()
        r_pip.touch_tip(v_offset=-5)
        if drop_tip == "T":
            l_pip.drop_tip()
            r_pip.drop_tip()
        else:
            l_pip.return_tip()
            r_pip.return_tip()


# wash_step_1_5 is meant to push beads closer to the magnet
def wash_step_1_5(l_sample, r_sample, ltips, rtips, l_pip, r_pip, zheight, is_etoh="F"):
    for l_well, r_well, l_tip, r_tip in zip(l_sample, r_sample, ltips, rtips):
        l_pip.pick_up_tip(l_tip)
        r_pip.pick_up_tip(r_tip)

        if is_etoh == "T":
            knock_off(1, l_well, 100, l_pip, xdir=xdir)
            knock_off(1, r_well, 100, r_pip, xdir=xdir)
        else:
            l_pip.aspirate(100, l_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            l_pip.dispense(100, l_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            l_pip.aspirate(
                100, l_well.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            l_pip.dispense(
                100, l_well.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            l_pip.aspirate(100, l_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            l_pip.dispense(100, l_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            l_pip.aspirate(
                100, l_well.bottom().move(types.Point(x=-0, y=-1, z=zheight - 4))
            )
            l_pip.dispense(
                100, l_well.bottom().move(types.Point(x=-0, y=-1, z=zheight + 4))
            )
            l_pip.blow_out(l_well.top())
            r_pip.aspirate(100, r_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            r_pip.dispense(100, r_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            r_pip.aspirate(
                100, r_well.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            r_pip.dispense(
                100, r_well.bottom().move(types.Point(x=-0, y=-1, z=zheight))
            )
            r_pip.aspirate(100, r_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            r_pip.dispense(100, r_well.bottom().move(types.Point(x=-0, y=1, z=zheight)))
            r_pip.aspirate(
                100, r_well.bottom().move(types.Point(x=-0, y=-1, z=zheight - 4))
            )
            r_pip.dispense(
                100, r_well.bottom().move(types.Point(x=-0, y=-1, z=zheight + 4))
            )
            r_pip.blow_out(r_well.top())
        l_pip.return_tip()
        r_pip.return_tip()


def wash_step2(
    l_sample, r_sample, vol, ltips, rtips, l_pip, r_pip, waste, xdir, return_tips="F"
):
    for l_well, r_well, l_tip, r_tip in zip(l_sample, r_sample, ltips, rtips):
        l_pip.pick_up_tip(l_tip)
        r_pip.pick_up_tip(r_tip)
        supernatant_removal(vol, l_well, waste, l_pip, xdir, is_waste="T")
        l_pip.aspirate(5, waste)
        supernatant_removal(vol, r_well, waste, r_pip, xdir, is_waste="T")
        r_pip.aspirate(5, waste)
        if return_tips == "T":
            l_pip.return_tip()
            r_pip.return_tip()
        else:
            l_pip.drop_tip()
            r_pip.drop_tip()

metadata = {
    "protocolName": "Zymo Magbead DNA/RNA kit,part 2",
    "author": "Patrick Schupp <patrick.schupp@ucsf.edu>",
    "source": "Oldham Lab",
    "apiLevel": "2.8",
}
print(datetime.datetime.now())
overageFactor = 1.1
numberSamples = 48
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
# p20tipNumber = math.ceil(numberColumns * 2 / 12)
p300tipNumber = math.ceil(numberColumns * 13 / 12)
# p20Location=['7'][:p20tipNumber]
p300Location = ["5", "6", "7", "8", "9"][:p300tipNumber]
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
lysMagVolume = volume_calc(530, "96well", numberColumns, overageFactor)
print("lysis+Sheild")
lysisSheild_or_WB1Volume = volume_calc(500, "96well", numberColumns, overageFactor)
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
        "nest_96_wellplate_100ul_pcr_full_skirt", "10", "Elution Plate"
    )
    print("elution (RNA) 96-well plate in slot 10")

    tips300 = [
        protocol.load_labware("opentrons_96_tiprack_300ul", s) for s in p300Location
    ]

    # ADD REAL 	ELUTION PLATE HERE PCR PLATE LIKE DNA PROTOCOL, BUT DONT SKIP COLUMNS

    """
    all_tips = [tr["A" + str(i)] for tr in tips300 for i in range(1, 13)]
    [tips1, tips2, tips3, tips4, tips5, tips6, tips7, tips8, tips9, tips10] = [
        all_tips[i : i + numberColumns]
        for i in range(0, numberColumns * 10, numberColumns)
    ]
    """

    l_tips = [tr["A" + str(i)] for tr in tips300 for i in range(1, 13, 2)]
    [
        tips1_L,
        tips2_L,
        tips3_L,
        tips4_L,
        tips5_L,
        tips6_L,
        tips7_L,
        tips8_L,
        tips9_L,
        tips10_L,
    ] = [
        l_tips[i : i + int(numberColumns / 2)]
        for i in range(0, int(numberColumns / 2) * 10, int(numberColumns / 2))
    ]

    r_tips = [tr["A" + str(i)] for tr in tips300 for i in range(2, 13, 2)]
    [
        tips1_R,
        tips2_R,
        tips3_R,
        tips4_R,
        tips5_R,
        tips6_R,
        tips7_R,
        tips8_R,
        tips9_R,
        tips10_R,
    ] = [
        r_tips[i : i + int(numberColumns / 2)]
        for i in range(0, int(numberColumns / 2) * 10, int(numberColumns / 2))
    ]

    # s_tips = [protocol.load_labware('opentrons_96_tiprack_20ul',s) for s in p20Location]
    # p20=protocol.load_instrument("p20_multi_gen2","right",tip_racks=s_tips)
    # print('p20 multichannel mounted on right arm')
    # p300 = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=tips300)
    p300R = protocol.load_instrument("p300_multi_gen2", "right", tip_racks=tips300)
    p300L = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=tips300)
    print("p300R multichannel mounted on right arm")
    print("p300L multichannel mounted on left arm")
    p300R.flow_rate.aspirate = 50
    p300R.flow_rate.dispense = 150
    p300R.flow_rate.blow_out = 300
    p300L.flow_rate.aspirate = 50
    p300L.flow_rate.dispense = 150
    p300L.flow_rate.blow_out = 300

    lysMag, reagentCounter = reagent_assign(
        lysMagVolume, reagentPlate, reagentCounterInit
    )
    lysisSheild_or_WB1, reagentCounter = reagent_assign(
        lysisSheild_or_WB1Volume, reagentPlate, reagentCounter
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
    """
    sample = [
        magplate["A" + str(i)]
        for i in range(startWell, startWell + numberColumns * 2, 2)
    ]
    print(sample)
    """
    l_sample = [
        magplate["A" + str(i)]
        for i in range(startWell, startWell + numberColumns * 2, 4)
    ]
    r_sample = [
        magplate["A" + str(i)]
        for i in range(startWell + 2, startWell + numberColumns * 2, 4)
    ]
    print("\n")
    print("L_sample here")
    print(l_sample)
    print("R_sample here")
    print(r_sample)
    # TODO do the same to the sample transfers
    l_sampleTransfer1 = [
        magplate["A" + str(i)]
        for i in range(startWell + 1, startWell + numberColumns * 2 + 1, 4)
    ]
    r_sampleTransfer1 = [
        magplate["A" + str(i)]
        for i in range(startWell + 3, startWell + numberColumns * 2 + 3, 4)
    ]
    print("\n")
    print("L_sampleTransfer here")
    print(l_sampleTransfer1)
    print("R_sampleTransfer here")
    print(r_sampleTransfer1)
    print("\n")

    l_sampleTransfer2 = [
        elutionPlate["A" + str(i)]
        for i in range(startWell + 1, startWell + numberColumns * 2 + 1, 4)
    ]
    r_sampleTransfer2 = [
        elutionPlate["A" + str(i)]
        for i in range(startWell + 3, startWell + numberColumns * 2 + 3, 4)
    ]
    print("L_sampleTransfer2 here")
    print(l_sampleTransfer2)
    print("R_sampleTransfer2 here")
    print(r_sampleTransfer2)
    print("\n")
    l_sampleRNA = [
        elutionPlate["A" + str(i)]
        for i in range(startWell, startWell + numberColumns * 2, 4)
    ]
    r_sampleRNA = [
        elutionPlate["A" + str(i)]
        for i in range(startWell + 2, startWell + numberColumns * 2, 4)
    ]
    print("L_sampleRNA here")
    print(l_sampleRNA)
    print("R_sampleRNA here")
    print(r_sampleRNA)
    print("\n")
    print("lysis + Mag bead here:")
    print(lysMagVolume["reservoir.volume"])
    print(unique(lysMag))
    print("\n")
    print("lysis + sheild here:")
    print(lysisSheild_or_WB1Volume["reservoir.volume"])
    print(unique(lysisSheild_or_WB1))
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
    print(tips1_L)
    print("\n")
    print(tips1_R)
    """
    print(tips2_R)
    print(tips3_R)
    print(tips3_R)
    print(tips1_L)
    print(tips2_L)
    print(tips3_L)
    print(tips3_L)
    """
    print("\n")
    ##########################################################################
    """
    Remember to switch the elution start well
    """
    ###############################################################################
    
    l_sample = l_sampleTransfer1
    r_sample = r_sampleTransfer1
    
    #Swap can start any time after second transfer!
    magdeck.engage(height=magheight)
    protocol.pause("Move sample to magnet!")
    protocol.pause("Did you change the elution start well number to either 1 or 7??")
    protocol.delay(minutes=2)

    wash_step_1_5(l_sample, r_sample, tips6_L, tips6_R, p300L, p300R, zheight=7)
    protocol.delay(minutes=3)
    wash_step2(
        l_sample, r_sample, 850, tips6_L, tips6_R, p300L, p300R, waste, xdir=xdir * -1
    )
    magdeck.disengage()
    protocol.comment("!!!!!!!!REPLACE TIPS 1,2,AND 3!!!!!!")
    wash_step(
        l_sample,
        r_sample,
        ethanol4,
        1000,
        3,
        tips7_L,
        tips7_R,
        p300L,
        p300R,
        xdir=xdir * -1,
    )

    magdeck.engage(height=magheight)
    protocol.delay(minutes=2)
    wash_step_1_5(l_sample, r_sample, tips7_L, tips7_R, p300L, p300R, zheight=15)
    protocol.delay(minutes=3)
    wash_step2(
        l_sample,
        r_sample,
        700,
        tips7_L,
        tips7_R,
        p300L,
        p300R,
        waste,
        xdir=xdir * -1,
        return_tips="T",
    )
    wash_step_1_5(
        l_sample, r_sample, tips7_L, tips7_R, p300L, p300R, zheight=15, is_etoh="T"
    )

    wash_step2(
        l_sample,
        r_sample,
        500,
        tips7_L,
        tips7_R,
        p300L,
        p300R,
        waste,
        xdir=xdir * -1,
        return_tips="T",
    )

    protocol.comment("Allowing beads to air dry for 5 minutes.")
    protocol.delay(minutes=4)
    for l_well, r_well, l_tip, r_tip in zip(l_sample, r_sample, tips7_L, tips7_R):
        p300L.pick_up_tip(l_tip)
        p300R.pick_up_tip(r_tip)
        p300L.aspirate(65, l_well.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300R.aspirate(65, r_well.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300L.drop_tip()
        p300R.drop_tip()
    protocol.delay(minutes=3)
    magdeck.disengage()
    protocol.comment("Adding NF-Water to wells for elution:")
    for l_well, r_well, l_tip, r_tip, waterWell in zip(
        l_sample, r_sample, tips8_L, tips8_R, water
    ):
        p300L.pick_up_tip(l_tip)
        p300R.pick_up_tip(r_tip)
        p300L.aspirate(57, waterWell)
        p300R.aspirate(1, waterWell.top(10))
        p300R.aspirate(57, waterWell)
        p300L.dispense(80, l_well)
        elute_mix(2, l_well, 50, p300L, xdir=xdir)
        p300L.blow_out()
        p300R.dispense(80, r_well)
        elute_mix(2, r_well, 50, p300R, xdir=xdir)
        p300R.blow_out()
        p300L.return_tip()
        p300R.return_tip()
    # 	protocol.delay(minutes=11)

    protocol.comment("move sample plate to mixer")
    protocol.pause("Shake for 10 min")
    magdeck.engage(height=magheight)
    protocol.comment("Incubating on MagDeck for 1.5 minutes.")
    protocol.delay(minutes=1.5)
    for l_well, r_well, l_tip, r_tip in zip(l_sample, r_sample, tips8_L, tips8_R):
        p300L.pick_up_tip(l_tip)
        p300R.pick_up_tip(r_tip)
        elute_mix(2, l_well, 30, p300L, xdir=xdir)
        p300L.blow_out()
        elute_mix(2, r_well, 30, p300R, xdir=xdir)
        p300R.blow_out()
        p300L.drop_tip()
        p300R.drop_tip()
    protocol.comment("Incubating on MagDeck for 4 minutes.")
    protocol.delay(minutes=4)
    protocol.comment("Transferring elution to final plate:")
    p300L.flow_rate.aspirate = 10
    p300R.flow_rate.aspirate = 10
    for l_src, r_src, l_dest, r_dest, l_tip, r_tip in zip(
        l_sample, r_sample, l_sampleTransfer2, r_sampleTransfer2, tips9_L, tips9_R
    ):
        p300L.pick_up_tip(l_tip)
        p300R.pick_up_tip(r_tip)
        p300L.aspirate(51, l_src.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300R.aspirate(51, r_src.bottom().move(types.Point(x=1, y=0, z=0.5)))
        p300L.dispense(100, l_dest)
        p300R.dispense(100, r_dest)
        p300L.return_tip()
        p300R.return_tip()
    # 	magdeck.disengage()
    protocol.comment("Congratulations!")