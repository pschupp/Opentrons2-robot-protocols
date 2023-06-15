import datetime
import json
import math
import os
import sys
import time
print(os.system("pwd"))
from opentrons import types
def volume_calc(volume, reservoir, numberColumns, overageFactor):
	out={}
	out["reservoir.type"]=reservoir
	out["reservoir.volume"]=0
	out["vol.to.add"]=(volume)
	if volume>2200: sys.exit('volume for one of the reagents is greater than 2200!')
	out["total.volume"]=round(volume*numberColumns*8*overageFactor,2)
	if out["reservoir.type"]=="96well":
		maxWellVolume=2200
	if out["reservoir.type"]=="96wellEth":
		maxWellVolume=1700
	out["reservoir.number"]=(math.ceil(out["total.volume"]/8/maxWellVolume))
	if out["reservoir.number"]==1:
		out["well.uses"]=[math.floor(maxWellVolume/out["vol.to.add"])]
		if out["well.uses"][0]>numberColumns:
			out["well.uses"]=[numberColumns]
		out["reservoir.volume"]=round(out["total.volume"]/(numberColumns*8)*out["well.uses"][0],2)
	else:
		uses=0
		useTrack=[]
		remainder=numberColumns
		use=math.floor(maxWellVolume/(out["vol.to.add"]*overageFactor))
		out["reservoir.volume"]=out["vol.to.add"]*overageFactor*use
		out["well.uses"]=[use]
		useTrack.append(use)
		uses=uses+use
		remainder=remainder-uses
		while remainder>use:
			out["well.uses"].append(use)
			remainder=remainder-uses
			useTrack.append(use)
		out["well.uses"].append(remainder)
		useTrack.append(remainder)
		out["reservoir.volume"]=[round(out["vol.to.add"]*overageFactor*useMult,2) for useMult in useTrack]
	print(out)
	return out
def reagent_assign(reagentVolume, reagentPlate, reagentCounter):
	temp=list(zip(range(reagentCounter,reagentCounter+reagentVolume["reservoir.number"]),reagentVolume["well.uses"]))
	out=[reagentPlate['A'+str(i[0])] for i in temp for _ in range(i[1])]
	reagentCounter=reagentCounter+reagentVolume["reservoir.number"]
	return out, reagentCounter
def well_mix(reps, loc, vol,pip): # mixing on one side of the well
	loc1 = loc.bottom().move(types.Point(x=0.7, y=0, z=1.3)) # TODO optimize position units
	loc2 = loc.bottom().move(types.Point(x=-0.9, y=0, z=7)) # TODO optimize position units
	pip.aspirate(20, loc1) # aspirate 20 ul from loc1 (above)
	mvol = vol-20 # volume left after first aspirate
	for _ in range(reps-1): # number of reps, need to do -1 because count starts at 0
		pip.aspirate(mvol, loc1) # take up remaining volume
		pip.dispense(mvol, loc2) # dispensing from higher up (by 4.9 mm)
	pip.dispense(280, loc2)  # dispense of final 20 ul
def elute_mix(reps, loc, vol,pip, xdir): #usually run at least 2 rpes
	loc1 = loc.bottom().move(types.Point(x=-0.8*xdir, y=-.8, z=.8)) 
	loc2 = loc.bottom().move(types.Point(x=-0.8*xdir, y=1, z=.8))
	loc3 = loc.bottom(2)
	pip.flow_rate.dispense = 200 #increase dispense flow rate
	for _ in range(reps):
		pip.aspirate(vol, loc1) 
		pip.dispense(vol, loc1)
		pip.aspirate(vol, loc2)
		pip.dispense(vol, loc2)
	pip.dispense(100, loc3)
	pip.blow_out()
	pip.flow_rate.dispense = 150 #set flow rate back
def knock_off(reps, loc, vol, pip, xdir): #knocks beads off side of wall towards magnet	
	loc1 = loc.bottom().move(types.Point(x=-1*xdir, y=0, z=4))
	loc2 = loc.bottom().move(types.Point(x=-1*xdir, y=0, z=14))
	loc3 = loc.bottom().move(types.Point(x=-0.8*xdir, y=1, z=12))
	loc4 = loc.bottom().move(types.Point(x=-0.8*xdir, y=1, z=10))
	loc5 = loc.bottom().move(types.Point(x=1.2*xdir, y=1, z=12))
	loc6 = loc.bottom().move(types.Point(x=1.2*xdir, y=1, z=10))
	pip.flow_rate.dispense = 90 #set low to not disrupt beads on mag, can be increased
	for _ in range(reps):       #probably only need 1 rep
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
def init_well_mix(reps, loc, vol,pip, xdir): # mixing on both sides of the well, not used while magnet is engaged!
	if vol > 500:
		zheight=15
	else:
		zheight=4
	loc1 = loc.bottom().move(types.Point(x=-1.2*xdir, y=1, z=0.3)) 
	loc2 = loc.bottom().move(types.Point(x=-1.2*xdir, y=1, z=0.3))
	loc3 = loc.bottom().move(types.Point(x=-1*xdir, y=-.8, z=0.3))  
	loc4 = loc.bottom().move(types.Point(x=-1*xdir, y=-.8, z=0.3))
	loc5 = loc.bottom().move(types.Point(x=0, y=.4, z=.1)) 
	loc6 = loc.bottom().move(types.Point(x=0, y=.4, z= zheight))
	loc7 = loc.bottom().move(types.Point(x=0, y=.4, z= zheight-2)) 
	loc8 = loc.bottom().move(types.Point(x=1*xdir, y=0, z= .3))
	# pip.aspirate(5, loc.top())
	pip.flow_rate.aspirate = 120
	pip.flow_rate.dispense = 300
	mvol = vol-20 # volume left after first aspirate
	for _ in range(reps):
		pip.aspirate(mvol, loc1) 
		pip.dispense(mvol, loc2)
		pip.aspirate(mvol, loc3)
		pip.dispense(mvol, loc4)
		pip.aspirate(mvol, loc5)
		pip.dispense(mvol, loc6)
		pip.aspirate(mvol, loc7)
		pip.dispense(mvol, loc8) 
	pip.dispense(280, loc6)
	pip.flow_rate.aspirate = 60
def wash_mix(reps, loc, vol, pip): # repeat wash where aspirate from left and dispense from right side
	loc1 = loc.bottom().move(types.Point(x=0.7, y=0, z=1.3))
	loc2 = loc.bottom().move(types.Point(x=-0.9, y=0, z=7))
	pip.flow_rate.aspirate = 80
	pip.flow_rate.dispense = 200
	pip.aspirate(20, loc1)
	mvol = vol-20
	for _ in range(reps-1):
		pip.aspirate(mvol, loc1)
		pip.dispense(mvol, loc2)
	pip.dispense(280, loc2)
	pip.flow_rate.aspirate = 60 #set flow rate back 
	pip.flow_rate.dispense = 150#set flow rate back 

def fetch_beads(vol,src, sample, dest, pip, tips, usedtips):
	for srcWell, well, tip, tret,destWell in zip(src,sample, tips, usedtips, dest): 
		pip.pick_up_tip(tip)
		pip.aspirate(vol, srcWell.bottom(2))
		pip.dispense(vol, well.top())
		init_well_mix(1, well, vol, pip, xdir=xdir)
		pip.blow_out()
		pip.flow_rate.aspirate = 130 
		pip.aspirate(vol+20, well.bottom().move(types.Point(x=0, y=0, z=-0.1))) 
		pip.dispense(vol+30, destWell.top()) 
		pip.blow_out()
		pip.drop_tip(tret) 
	pip.flow_rate.aspirate = 60

def supernatant_removal(vol,src,dest, pip, xdir, bead_transfer='F', is_waste='F'): # magnet is engaged, need to change x depending on odds or evens
	if bead_transfer=='T':
		pip.flow_rate.aspirate = 120 # higher flow rate durring transfer of beads to not leave any behind
	else:
		pip.flow_rate.aspirate = 20 # reduces further from 50 to 20, from earlier 94
	tvol = vol # counts volume that has been aspirated
	asp_ctr = 0 # number of aspirations, important to take into account volume left over in pipette
	while tvol > 250:
		pip.aspirate(250, src.bottom().move(types.Point( x=-1*xdir, y=0, z=.8))) # aspirating away from the side with the magnests
		pip.aspirate(10, src.top())
		pip.dispense(250, dest)
		pip.blow_out()
		if is_waste=='T':
			pip.aspirate(5, dest) # presumably aspirating 10 ul to get rid of any drops that are still on the pipette
		else:
			dest
			pip.aspirate(5, dest.top())
		tvol=tvol-250
		asp_ctr=asp_ctr+1
	if bead_transfer=='T':
		pip.aspirate(tvol, src.bottom().move(types.Point(x=0, y=0, z=-0.1))) # aspirate remaining volume	
	else:	
		pip.aspirate(tvol, src.bottom().move(types.Point(x=-1*xdir, y=0, z=1))) # aspirate remaining volume 
	dvol = 30*asp_ctr + tvol # calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
	pip.dispense(dvol, dest) 
	pip.blow_out()
	pip.flow_rate.aspirate = 50# set rate back to the rate from before
def supernatant_removal_mini(vol,src,dest, pip, xdir):
	pip.pick_up_tip()
	pip.aspirate(15, src.bottom().move(types.Point(x=-1*xdir,y=0,z=0.5)))
	pip.dispense(20, dest)
def wash_step(sample, src, vol, mtimes, tips, usedtips, pip,zheight,xdir) :	# magnet not engaged
	for well, tip, tret, srcWell in zip(sample, tips, usedtips, src): 
		pip.pick_up_tip(tip) 
		tvol = vol # counts volume that has been aspirated
		asp_ctr = 0 # number of aspirations, important to take into account volume left over in pipette
		while tvol > 250: 
			pip.aspirate(250, srcWell.bottom(1)) # aspirating away from the side with the magnests
			pip.aspirate(10, srcWell.top())
			pip.dispense(280, well.top(-10))
			pip.aspirate(5, well.top()) # presumably aspirating 10 ul to get rid of any drops that are still on the pipette
			tvol=tvol-250
			asp_ctr=asp_ctr+1
		pip.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1))) # aspirate remaining volume 
		dvol = 20*asp_ctr + 250# calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
		if dvol>250: dvol=250
		pip.dispense(dvol, well.top()) 
		init_well_mix(mtimes, well, 200, pip, xdir=xdir) # origionally did only 180...why?
		pip.blow_out() 
		pip.drop_tip(tret) # use for next wash step, can save tips for next step
def wash_step_1_5(sample, src, vol, mtimes, tips, usedtips, pip,zheight,xdir, is_etoh='F') :	# magnet not engaged
	for well, tret in zip(sample, usedtips): 
		pip.pick_up_tip(tret) 
		if is_etoh== 'T':
			knock_off(1, well, 100, pip, xdir=xdir)
		else: 
			pip.aspirate(100, well.bottom().move(types.Point(x=-0, y=1, z=zheight))) 
			pip.dispense(100, well.bottom().move(types.Point(x=-0, y=1, z=zheight))) 
			pip.aspirate(100, well.bottom().move(types.Point(x=-0, y=-1, z=zheight))) 
			pip.dispense(100, well.bottom().move(types.Point(x=-0, y=-1, z=zheight))) 
			pip.aspirate(100, well.bottom().move(types.Point(x=-0, y=-1, z=zheight))) 
			pip.dispense(100, well.bottom().move(types.Point(x=-0, y=-1, z=zheight))) 		
			pip.aspirate(100, well.bottom().move(types.Point(x=-0, y=-1, z=zheight-4))) 
			pip.dispense(100, well.bottom().move(types.Point(x=-1*xdir, y=-1, z=zheight+4))) 
		pip.drop_tip(tret) # use for next wash step, can save tips for next step
def wash_step2(sample, src, vol, mtimes, tips, usedtips, pip, waste, xdir) : # 2a returns tips , magnet engaged
	for well, tip in zip(sample, usedtips):
		pip.pick_up_tip(tip)
		supernatant_removal(vol+20, well, waste, pip, xdir, bead_transfer= 'F', is_waste='T') 
		pip.aspirate(5, waste)  # making sure there is no liquid on the tip when returning the pipete
		pip.drop_tip()
metadata = { # 
	'protocolName': 'Zymo Magbead DNA/RNA kit, part 1',
	'author': 'Patrick Schupp <patrick.schupp@ucsf.edu>',
	'source': 'Oldham Lab',
	'apiLevel': '2.8'
}
# begin by doing lysis yourself in DNA/RNA shield, lyse by using pipetting up and down and the tube is completely clear. 
# reservoirs will be of this variety: https://www.usascientific.com/50ml-reservoir-grad-white/p/Grad-Res-50mL
#	only issue is that they might move and that they have not been measured by opentrons, but they are 5x cheaper than:
#	https://www.usascientific.com/12-channel-automation-reservoir/p/1061-8150
# these provide much more flexiblity, especially for large volumes.
print(datetime.datetime.now())
overageFactor=1.2
numberSamples=24
startWell=1
dnaRNAShieldVolume=200
numberColumns=math.ceil(numberSamples/8)
protKIncTime=30 # minutes
delayTime = 0 if numberSamples>8 else 45
TOT_LYSMAG_INC = 30 # (30 min) total time of mixing loops for lysis buffer & mag beads
TOT_LYSMAG_WITH_45_GAP = 2.5 # (2.5 min) total time of one lysis/mag mixing loop including 45sec delay
TOT_LYSMAG_WO_45_GAP = 1.8 # (1.8 min) total time of one lysis/mag mixing loop with out 45sec delay
NUM_LYSMAG_ITER = round(TOT_LYSMAG_INC/(TOT_LYSMAG_WITH_45_GAP if numberColumns == 1 else TOT_LYSMAG_WO_45_GAP*numberColumns)) #number of loops dependent on number of columns and total time 
TOT_ELUTE_INC = 15 # (15 min) total time of mixing loops for elution
TOT_ELUTE_WITH_45_GAP = 2.5 # (2.5 min) total time of one lysis/mag mixing loop including 45sec delay
TOT_ELUTE_WO_45_GAP = 1.8 # (1.8 min) total time of one lysis/mag mixing loop with out 45sec delay
NUM_ELUTE_ITER = math.ceil(TOT_ELUTE_INC/(TOT_ELUTE_WITH_45_GAP if numberColumns == 1 else TOT_ELUTE_WO_45_GAP*numberColumns)) #number of loops dependent on number of columns and total time 
reagentCounterInit=1
ethanolCounterInit=1
start_odd_even="odd"
xdir=1 if start_odd_even=="odd" else -1
print("Processing "+str(numberSamples)+" samples using "+str(numberColumns)+" columns")
p20tipNumber=math.ceil(numberColumns*4/12)
p300tipNumber=math.ceil(numberColumns*8/12)
p20Location=['7']
p300Location=['2','5','6', '10'][:p300tipNumber]
print('Using '+str(p20tipNumber)+' racks of p20 tips in slot(s) '+str(p20Location))
print('Using '+str(p300tipNumber)+' racks of p300 tips in slot(s) '+str(p300Location))
print("'vol.to.add' refers to the volume added over the entire protocol, i.e. 500 * 2 = 1000 ul ethanol")
print("Lysis Buffer + Mag beads ")
lysisVolume=volume_calc(dnaRNAShieldVolume*2.5+30, "96well",numberColumns, overageFactor)
print("Wash 1 Buffer")
wash1Volume=volume_calc(500, "96well",numberColumns, overageFactor)
print("Wash 2 Buffer")
wash2Volume=volume_calc(500, "96well",numberColumns, overageFactor)
print("Ethanol Buffer 1")
ethanol1Volume=volume_calc(1200, "96wellEth",numberColumns, overageFactor)
print("Ethanol Buffer 2")
ethanol2Volume=volume_calc(1200, "96wellEth",numberColumns, overageFactor)
print("Water")
waterVolume=volume_calc(60, "96well",numberColumns, overageFactor)
def run(protocol):
	magdeck = protocol.load_module('magnetic module gen2', '1') 
	print('magnetic module in slot 1')
	magheight = 6.75 
	magplate = magdeck.load_labware('usascientific_96_wellplate_2.4ml_deep', 'Sample Plate') 
	print('liquid waste in slot 11')
	liqwaste = protocol.load_labware('nest_1_reservoir_195ml', '11', 'Liquid Waste') 
	waste = liqwaste['A1'].top() 
	print('96 well reagent plate in slot 3')
	reagentPlate=protocol.load_labware('usascientific_12_reservoir_22ml', '3', 'Reagent Plate') 
	print('96 well ethanol plate in slot 8')
	ethanolPlate=protocol.load_labware('usascientific_12_reservoir_22ml', '8', 'Ethanol Plate') 
	print('96 well DNA elution plate in slot 10')
	elutionPlate=protocol.load_labware('usascientific_96_wellplate_2.4ml_deep', '9', 'DNA Elution Plate') 
	print('96 well RNA elution plate in slot 4')
	nextRNAPlate=protocol.load_labware('usascientific_96_wellplate_2.4ml_deep', '4', 'RNA Elution Plate (DNA Protocol)') 
	tips200 = [protocol.load_labware('opentrons_96_tiprack_300ul', s) for s in  p300Location] 
	all_tips = [tr['A'+str(i)] for tr in tips200 for i in range(1, 13)] 
	[tips1, tips2, tips3, tips4, tips5, tips6, tips7, tips8] = [all_tips[i:i+numberColumns] for i in range(0, numberColumns*8, numberColumns) ] 
	s_tips = [protocol.load_labware('opentrons_96_tiprack_20ul', s) for s in p20Location]
	p20=protocol.load_instrument("p20_multi_gen2", "right", tip_racks=s_tips)
	print('p20 multichannel mounted on right arm')
	p300=protocol.load_instrument("p300_multi_gen2", "left", tip_racks=tips200) # gen 2 p300 on left arm
	print('p300 multichannel mounted on left arm') 
	p300.flow_rate.aspirate = 50 # reduced from 94
	p300.flow_rate.dispense = 150 # increased from from 94
	p300.flow_rate.blow_out = 300 # increased from 94
	lysis,reagentCounter=reagent_assign(lysisVolume,reagentPlate,reagentCounterInit)
#	magBead,reagentCounter=reagent_assign(magBeadVolume,reagentPlate,reagentCounter)
	wash1,reagentCounter=reagent_assign(wash1Volume,reagentPlate,reagentCounter)
	wash2,reagentCounter=reagent_assign(wash2Volume,reagentPlate,reagentCounter)
	ethanol1,ethanolCounter=reagent_assign(ethanol1Volume,ethanolPlate, ethanolCounterInit)
	ethanol2,ethanolCounter=reagent_assign(ethanol2Volume,ethanolPlate, ethanolCounter)
	print(ethanol1)
	print(ethanol2)
	print(ethanol1Volume)
	print(ethanolPlate)
	water,reagentCounter=reagent_assign(waterVolume,reagentPlate,reagentCounter)
	sample=[magplate['A'+str(i)] for i in range(startWell,startWell+numberColumns*2,2)]
	sampleTransfer=[magplate['A'+str(i)] for i in range(startWell+1, startWell+numberColumns*2+1,2)]
	sampleDNA=[elutionPlate['A'+str(i)] for i in range(1,2*numberColumns+1,2)]
	sampleRNA=[nextRNAPlate['A'+str(i)] for i in range(1,2*numberColumns+1,2)]
	magdeck.disengage()
	protocol.comment('Adding lysis buffer + beads to samples:')
	step5Volume=lysisVolume["vol.to.add"]+30 #+magBeadVolume["vol.to.add"]
	i=1

	#Start commenting out from here for finishing DNA after RNA run

	for well, reagent, tip in zip(sample, lysis, tips1): # TODO measure time
		pipetteSteps=math.ceil(step5Volume/250)
		pipetteAspirate=step5Volume/pipetteSteps
		p300.pick_up_tip(tip)
		if(i in range(1, len(lysis)+1, math.ceil(len(lysis)/len(set(list(lysis)))))):
			init_well_mix(2,reagent,220, p300,xdir=xdir) 
		for _ in range(pipetteSteps-1): # mix in resevoir 4 times.
			p300.aspirate(pipetteAspirate, reagent) # pick up 160 ul from reagent 4+1 times, 800 ul. 
			p300.aspirate(10, reagent.top())
			p300.dispense(pipetteAspirate+40, well.top(-5)) # drop 160 ul 5mm below top of magwell
			p300.aspirate(10, well.top()) # aspirate 10 ul at current position
		p300.aspirate(pipetteAspirate, reagent) # final mix
		p300.dispense(pipetteAspirate+40, well.top(-15))# dispense 160 +40 ul extra picked up from previous run, probably mostly air
		init_well_mix(1, well, 200, p300,xdir=xdir) 
		p300.aspirate(10, well.top()) # this must again be to remove any droplets hanging on
		p300.drop_tip()
		i=i+1

	protocol.pause("Mix off deck for 30 min")
#	protocol.delay(minutes=30) # only use delay if you are mixing off deck                                                                                                                      ) #this is for protocols mixing off deck
	protocol.comment("move sample plate to mixer")
	
	# end comment out here for finishing DNA after RNA run

	'''	
	beadIncubationStartTime=time.time()
	protocol.delay(seconds=delayTime)			
	protocol.comment('Mixing samples+buffer+beads:')
	for i in range(NUM_LYSMAG_ITER): # can't do while loop as it won't test properly, calculates how many loops to run
		for well, tip, tret in zip(sample, tips2, tips2): # TODO measure time
			p300.pick_up_tip(tip) # pickup itp from slot6
			init_well_mix(4, well, 240, p300,xdir=xdir) # side to side mixing, 8 times 
			p300.blow_out()
			p300.drop_tip(tret) 
		protocol.delay(seconds=delayTime)
		protocol.comment('Finished mixing loop '+str(i+1))
	'''
	magdeck.engage(height=magheight) 
	protocol.comment('Incubating on magdeck for 4 minutes')
	protocol.delay(minutes=4) # TODO how much time does it really take!
	for well, tip, tret in zip(sample, tips2, tips2): # TODO measure time
		p300.pick_up_tip(tip)
		init_well_mix(1, well, 200, p300, xdir=xdir)
		p300.return_tip()
	protocol.delay(minutes=3)
	for well, tip, tret in zip(sample, tips2, tips2): # TODO measure time
		p300.pick_up_tip(tip)
		knock_off(1, well, 100, p300, xdir=xdir)
		p300.drop_tip()
	protocol.delay(minutes=5) 
	protocol.comment('Removing supernatant:')
	protocol.max_speeds['Z'] = 200 # limit x axis to 200 mm/s
	for well,tip,sampleRNAWell in zip(sample, tips3, sampleRNA): # TODO in example protocol, this is repeated again with different tips
		p300.pick_up_tip(tip)
		supernatant_removal(step5Volume+300, well, sampleRNAWell, p300, xdir)
		p300.drop_tip()

	protocol.pause("RNA has transfered, Continue with DNA?")
	
	'''
	magdeck.disengage()
	del protocol.max_speeds['Z']  # reset x axis limit
	protocol.comment('Washing!')
	wash_step(sample, wash1, 500, 4, tips4, tips4, p300, zheight=10, xdir=xdir)
	magdeck.engage(height=magheight)
	protocol.delay(minutes=2)
	wash_step_1_5(sample, wash1, 500, 5, tips4, tips4, p300, zheight=7, xdir=xdir)
	protocol.delay(minutes=4)
	wash_step2(sample, wash1, 500, 5, tips4, tips4, p300, waste, xdir) 
	magdeck.disengage()
	wash_step(sample, wash2, 500, 3  , tips5, tips5, p300,zheight=10,xdir=xdir)
	magdeck.engage(height=magheight)
	protocol.delay(minutes=2)
	wash_step_1_5(sample, wash2, 500, 5, tips5, tips5, p300,zheight=7, xdir=xdir)
	protocol.delay(minutes=4)
	wash_step2(sample, wash2, 500, 5, tips5, tips5, p300, waste, xdir)
	magdeck.disengage()
	for well, tip, tret, srcWell, dest in zip(sample, tips6, tips6, ethanol1, sampleTransfer): 
		p300.pick_up_tip(tip) 
		tvol = 600 # counts volume that has been aspirated
		asp_ctr = 0 # number of aspirations, important to take into account volume left over in pipette
		while tvol > 250: 
			p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1))) # aspirating away from the side with the magnests
			p300.aspirate(10, srcWell.top())
			p300.dispense(280, well.top(-10))
			p300.aspirate(5, well.top()) # presumably aspirating 10 ul to get rid of any drops that are still on the pipette
			tvol=tvol-250
			asp_ctr=asp_ctr+1
		p300.aspirate(250, srcWell.bottom().move(types.Point(x=-0, y=0, z=1))) # aspirate remaining volume 
		dvol = 20*asp_ctr + 250# calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
		if dvol>250: dvol=250
		p300.dispense(dvol, well.top()) 
		init_well_mix(3, well, 200, p300, xdir=xdir) # origionally did only 180...why?
		supernatant_removal(200, well,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, well, 200, p300)
		supernatant_removal(200,well,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, well, 200, p300)
		supernatant_removal(200,well,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, well, 200, p300) #added this because there was some left after transfer
		supernatant_removal(200,well,dest, p300, xdir=xdir, bead_transfer= 'T') #added this because there was some left after transfer
		p300.aspirate(5, dest.top())  
		p300.blow_out() 
		p300.drop_tip()
	fetch_beads(200, ethanol1, sample, sampleTransfer, p300, tips7, tips7)

	""" 		this is commented out beacuse I want the transfer to happen immediatly after the etoh is added	
	for src, dest, tip in zip(sample, sampleTransfer, tips7):
		p300.pick_up_tip(tip) 
		supernatant_removal(200,src,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, src, 200, p300)
		supernatant_removal(200,src,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, src, 200, p300)
		supernatant_removal(200,src,dest, p300, xdir=xdir, bead_transfer= 'T')
		wash_mix(3, src, 200, p300) #added this because there was some left after transfer
		supernatant_removal(200,src,dest, p300, xdir=xdir, bead_transfer= 'T') #added this because there was some left after transfer
		p300.aspirate(5, dest.top())  
		p300.return_tip() """
	sample=sampleTransfer
	magdeck.engage(height=magheight)
	protocol.delay(minutes=2)
	wash_step_1_5(sample, ethanol1, 600, 5, tips7, tips7, p300, zheight=7, xdir=xdir, is_etoh='T')
	protocol.delay(minutes=4)
	wash_step2(sample, ethanol1, 850, 5, tips7, tips7, p300, waste, xdir=xdir*-1) 
	magdeck.disengage()
	wash_step(sample, ethanol2, 1200, 3, tips8, tips8, p300,zheight=15,xdir=xdir*-1)
	magdeck.engage(height=magheight)
	protocol.delay(minutes=2)
	wash_step_1_5(sample, ethanol2, 1200, 5, tips8, tips8, p300,zheight=15, xdir=xdir, is_etoh='T')
	protocol.delay(minutes=4)
	wash_step2(sample, ethanol2, 1200, 5, tips8, tips8, p300, waste, xdir=xdir*-1)
	protocol.comment('Allowing beads to air dry for 2 minutes.')
	protocol.delay(minutes=2)
	"""
	protocol.comment('Removing any excess ethanol from wells:') # over drying....?
	for well in sample:
		p20.transfer(18, well.bottom().move(types.Point(x=-0.3*xdir*-1, y=0, z=1.5)), waste, new_tip='once', trash='true') # TODO is 250 ul too much?
	"""	
	protocol.comment('Allowing beads to air dry for 15 minutes.')
	protocol.delay(minutes=15)
	magdeck.disengage()
	protocol.comment('Adding NF-Water to wells for elution:')
	for well, tip, tret,waterWell in zip(sample, tips1, tips1, water): 
		p300.pick_up_tip(tip)
#		p300.aspirate(20, waterWell.top()) 
		p300.aspirate(70, waterWell)
		p300.dispense(80, well)  
		elute_mix(8, well, 60, p300, xdir=xdir)
		p300.blow_out()
		p300.drop_tip() 
	
	protocol.delay(minutes=11) #this is for protocols mixing off deck
	protocol.comment("move sample plate to mixer")
	"""
		protocol.delay(seconds=delayTime)
	for i in range(NUM_ELUTE_ITER): # can't do while loop as it won't test properly, calculates how many loops to run
		for well, tip, tret in zip(sample, tips1, tips1): # TODO measure time
			p300.pick_up_tip(tip) 
			elute_mix(4, well, 60, p300,xdir=xdir) # side to side mixing
			p300.blow_out()
			p300.drop_tip(tret) 
		protocol.delay(seconds=delayTime)
		protocol.comment('Finished mixing loop '+str(i+1))
	"""
	#protocol.comment('Incubating at room temp for 10 minutes.')
	#protocol.delay(minutes=10) # TODO beads setteling out of solution! Check, maybe they don't at this stage
	magdeck.engage(height=magheight) # Transfer elutes to clean plate

	protocol.comment('Incubating on MagDeck for 1.5 minutes.')
	protocol.delay(minutes=1.5)	
	for well,tip,tret in zip(sample,tips1,tips1): 
		p300.pick_up_tip(tip) 
		elute_mix(2,well,30,p300,xdir=xdir)
		p300.blow_out()
		p300.drop_tip() 
	
	protocol.comment('Incubating on MagDeck for 4 minutes.')
	protocol.delay(minutes=4)
	protocol.comment('Transferring elution to final plate:')
	p300.flow_rate.aspirate = 10
	for src, dest, tip, tret in zip(sample, sampleDNA, tips2, tips2):
		p300.pick_up_tip(tip)
		p300.aspirate(60, src.bottom().move(types.Point(x=-1*xdir*-1, y=0, z=.5))) 
		p300.dispense(100, dest)
		p300.drop_tip(tret)  # drop in trash
	magdeck.disengage()
	protocol.comment('Congratulations!')
	'''
