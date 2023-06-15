import datetime
import json
import math
import os
import sys
import time
import inspect
print(os.system("pwd"))
from opentrons import types
metadata={"protocolName": "Swift RNAseq Library kit",	"author": "Daniel Brody <daniel.brody@ucsf.edu>","source": "Oldham Lab","apiLevel": "2.8",}
def lineno():
	#returns current line number
	return inspect.currentframe().f_back.f_lineno
def unique(list1):
	unique_list=[]
	for x in list1:
		if x not in unique_list:
			unique_list.append(x)
	for x in unique_list:
		print(x)
def volume_calc(volume,reservoir,numberColumns,overageFactor):
	out={}
	out["reservoir.type"]=reservoir
	out["reservoir.volume"]=0
	out["vol.to.add"]=volume
	if volume>2000:
		sys.exit("volume for one of the reagents is greater than 2200!")
	out["total.volume"]=round(volume*numberColumns*8*overageFactor,2)
	if out["reservoir.type"]=="96well100":
		maxWellVolume=180
	if out["reservoir.type"]=="96well2000":
		maxWellVolume=2200
	out["reservoir.number"]=math.ceil(out["total.volume"]/8/maxWellVolume)
	if out["reservoir.number"]==1:
		out["well.uses"]=[math.floor((out["total.volume"]/8)/out["vol.to.add"])]
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
		out["reservoir.number"]=len(out["reservoir.volume"])
	print(out)
	return out
def reagent_assign(reagentVolume,reagentPlate,reagentCounter):
	temp=list(zip(range(reagentCounter,reagentCounter+reagentVolume["reservoir.number"]),reagentVolume["well.uses"],))
	out=[reagentPlate["A"+str(i[0])] for i in temp for _ in range(i[1])]
	reagentCounter=reagentCounter+reagentVolume["reservoir.number"]
	return out,reagentCounter
def p20_mix(reps,vol,loc,pip, high_mix="F"): 
	if high_mix=="T":
		loc1 = loc.bottom(.7) 
		loc2 = loc.bottom(6)
		loc3 = loc.bottom(4)
	else:
		loc1 = loc.bottom().move(types.Point(x=0,y=0,z=1)) 
		loc2 = loc.bottom().move(types.Point(x=1.5*xdir,y=0,z=6))
		loc3 = loc.bottom().move(types.Point(x=0,y=0,z=3))
	pip.aspirate(1,loc1) 
	mvol = vol-1.5 
	pip.aspirate(10,loc1)
	pip.dispense(10,loc3)
	pip.aspirate(10,loc1)
	pip.dispense(10,loc3)
	for _ in range(reps-1): 
		pip.aspirate(mvol,loc1) 
		pip.dispense(mvol,loc2)
	if high_mix=="F":
		pip.dispense(20,loc3)
		pip.aspirate(10,loc2)
		pip.dispense(20,loc3)
		pip.aspirate(10,loc2)
		pip.dispense(20,loc3) 
	pip.flow_rate.aspirate=10
	pip.flow_rate.dispense=10
	pip.aspirate(mvol,loc1) 
	pip.dispense(mvol,loc2) 
	pip.flow_rate.dispense=30
def p300_mix(reps,vol,loc,pip, high_mix="F"): 
	if high_mix=="T":	
		loc1 = loc.bottom(3) 
		loc2 = loc.bottom(16)
	else:
		loc1 = loc.bottom().move(types.Point(x=0,y=0,z=2))
		loc2 = loc.bottom().move(types.Point(x=1.2*xdir,y=0,z=5))
	pip.aspirate(5,loc1) 
	mvol = vol-10 
	for _ in range(reps-1): 
		pip.aspirate(mvol,loc1) 
		pip.dispense(mvol,loc2) 
	pip.flow_rate.aspirate=70
	pip.flow_rate.dispense=50
	pip.aspirate(mvol,loc1) 
	pip.dispense(mvol,loc2)
	pip.dispense(300,loc2)  
# TODO combine p20 and p300
def p20_supernatant_removal(vol,src,dest,pip,xdir,is_waste="F"):  # magnet is engaged,need to change x depending on odds or evens
	pip.flow_rate.aspirate=10  # reduces further from 50 to 20,from earlier 94
	if is_waste=="T":
		pip.flow_rate.dispense=150
	else:
		pip.flow_rate.dispense=20
	tvol=vol  # counts volume that has been aspirated
	asp_ctr=0  # number of aspirations,important to take into account volume left over in pipette
	while tvol>18:
		pip.aspirate(18,src.bottom().move(types.Point(x=-0.5*xdir,y=0,z=0.5))) # aspirating away from the side with the magnests
		pip.aspirate(1,src.top())
		pip.dispense(20,dest)
		pip.blow_out()
		if is_waste=="T":
			pip.aspirate(3,dest)  # aspirating 3 ul to get rid of any drops that are still on the pipette
		else:
			pip.aspirate(3,dest.top())
		tvol=tvol-18
		asp_ctr=asp_ctr+1
	pip.aspirate(tvol,src.bottom().move(types.Point(x=-0.5*xdir,y=0,z=0.2)))  # aspirate remaining volume
	# TODO What is going on here with the 30*
	# Why cant I just dispense 20
	dvol=(30*asp_ctr+tvol)  # calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
	pip.dispense(dvol,dest)
	pip.blow_out()
	if not is_waste=="T":
		pip.touch_tip(v_offset=-8)
	pip.flow_rate.aspirate=50  # set rate back to the rate from before
	pip.flow_rate.dispense=90
def p300_supernatant_removal(vol,src,dest,pip,xdir,is_200ul_waste="F"):
	pip.flow_rate.aspirate=10  # reduces further from 50 to 20,from earlier 94
	if is_200ul_waste=="T":
		pip.flow_rate.dispense=150
	else:
		pip.flow_rate.dispense=40
	tvol=vol  # counts volume that has been aspirated
	asp_ctr=0  # number of aspirations,important to take into account volume left over in pipette
	if tvol>200:
		sys.exit("sorry tvol too high, this function is optimized to work on pcr plates now")	
			# I was having an issue where a negative value for tvol was being "aspirated", but think it was dispensing
	if is_200ul_waste=="T":	
		while tvol>80:
			pip.aspirate(80,src.bottom().move(types.Point(x=-1*xdir,y=0,z=6)))  # aspirating away from the side with the magnests
			pip.aspirate(80,src.bottom().move(types.Point(x=-0.4*xdir,y=0,z=.5)))
			pip.aspirate(10,src.top())
			pip.dispense(300,dest)
			pip.blow_out()
			pip.aspirate(5,dest)  # aspirating 3 ul to get rid of any drops that are still on the pipette
			tvol=tvol-160
			asp_ctr=asp_ctr+1
		pip.aspirate(80,src.bottom().move(types.Point(x=-0.4*xdir,y=0,z=.3)))  # aspirate remaining volume
		dvol=(30*asp_ctr+tvol)  # calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
		pip.dispense(dvol,dest)

	else:
		while tvol>100:
			pip.aspirate(50,src.bottom().move(types.Point(x=-1*xdir,y=0,z=6)))  # aspirating away from the side with the magnests
			pip.aspirate(50,src.bottom().move(types.Point(x=-0.4*xdir,y=0,z=.5)))
			pip.aspirate(10,src.top())
			pip.dispense(300,dest)
			pip.blow_out()
			pip.aspirate(5,dest.top())
			tvol=tvol-100
			asp_ctr=asp_ctr+1
		pip.aspirate(tvol,src.bottom().move(types.Point(x=-0.4*xdir,y=0,z=.3)))  # aspirate remaining volume
		dvol=(30*asp_ctr+tvol)  # calculate volume that was just aspirated and add to it 20 ul for every time there was pipetting
		pip.dispense(dvol,dest)
		pip.blow_out()
		pip.touch_tip(v_offset=-8)
	pip.flow_rate.aspirate=50  # set rate back to the rate from before
	pip.flow_rate.dispense=90
def mastermix_transfer(pip,tips,reagent_well,sample_well,transfer_vol):
	pip.flow_rate.aspirate=10  # set rate back to the rate from before
	pip.flow_rate.dispense=30
	pip.pick_up_tip(tips[0])
	#TODO change vol back
	p20_mix(5,10,reagent_well[0],pip, high_mix="T")
	pip.blow_out(reagent_well[0].top())
	for tip,r_well,s_well in zip(tips,reagent_well,sample_well):
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		p20_mix(3,5,r_well,pip,high_mix="T")  # TODO change volumes
		tvol=transfer_vol
		asp_ctr=0 
		while tvol >18:  
			pip.aspirate(18,r_well.bottom(1))
			pip.aspirate(1,r_well.top())
			pip.dispense(20,s_well.top(-10))
			pip.touch_tip(v_offset=-8)
			tvol=tvol-18
			asp_ctr=asp_ctr+1
		pip.aspirate(tvol,r_well.bottom(.5))
		pip.dispense(20,s_well.top(-8))
		p20_mix(10,17,s_well,pip,high_mix="T")
		pip.dispense(20,s_well.top(-8))
		pip.blow_out(s_well.top(-6))
		pip.touch_tip(v_offset=-8)
		pip.drop_tip()
	pip.flow_rate.aspirate=50  # set rate back to the rate from before
	pip.flow_rate.dispense=90
# TODO can we use xdir if samples are in adjascent wells ex. 1 & 2
def SPRI_clean_up_a(pip,tips,sample,bead_vol,te_vol,transfer_vol,transfer_loc,xdir,mag_bead):
	i=1
	for tip,beads,mag_samp in zip(tips,mag_bead,sample):
		if i==1:
			pip.flow_rate.aspirate=100
			pip.flow_rate.dispense=100
			pip.pick_up_tip(tip)
			p300_mix(10,220,beads,pip,high_mix="T")
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		p300_mix(4,100,beads,pip,high_mix="T")
		pip.flow_rate.aspirate=50
		pip.flow_rate.dispense=30
		pip.aspirate(bead_vol,beads)
		pip.default_speed=100
		pip.move_to(mag_samp.top(-2))
		pip.default_speed=400
		pip.dispense(bead_vol,mag_samp)
#		pip.blow_out()
		pip.flow_rate.aspirate=70
		pip.flow_rate.dispense=50
		p300_mix(10,80,mag_samp,pip)
		pip.blow_out(mag_samp.top(-5))
		pip.drop_tip()
		i=i+1

def SPRI_clean_up_b(pip,tips,sample,waste_dest,bead_vol,te_vol,transfer_vol,transfer_loc,xdir,mag_bead,ethanol):
	#`tips` is a 3-element list of tips used in function.; 	(ex [ TIPS_2,TIPS_3,TIPS_4],)
	pip.flow_rate.aspirate=20
	pip.flow_rate.dispense=70
	for tip,mag_samp in zip(tips[0],sample):
		pip.pick_up_tip(tip)
		p300_supernatant_removal(200,mag_samp,waste_dest,pip,xdir=xdir,is_200ul_waste="T")
		pip.drop_tip()
	pip.default_speed=200
	pip.flow_rate.aspirate=75
	pip.flow_rate.dispense=70
	# Etoh wash 1
	for tip,mag_samp,etoh in zip(tips[1],sample,ethanol):
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		pip.air_gap(10)
		pip.aspirate(180,etoh)
		pip.air_gap(5)
		pip.dispense(210,mag_samp.top(-2))
#	if numberSamples=="8": protocol.delay(seconds=20)
	for tip,mag_samp in zip(tips[1],sample):
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		p300_supernatant_removal(200,mag_samp,waste_dest,pip,xdir=xdir,is_200ul_waste="T")
		pip.drop_tip()
	# Etoh wash 2
	for tip,mag_samp,etoh in zip(tips[2],sample,ethanol):
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		pip.air_gap(10)
		pip.aspirate(180,etoh)
		pip.air_gap(5)
		pip.dispense(210,mag_samp.top(-2))
	if numberSamples=="8": protocol.delay(seconds=20)
	for tip,mag_samp in zip(tips[2],sample):
		if not pip.hw_pipette["has_tip"]:
			pip.pick_up_tip(tip)
		p300_supernatant_removal(200,mag_samp,waste_dest,pip,xdir=xdir,is_200ul_waste="T")
		pip.drop_tip()

# Remove residual ethanol
def SPRI_clean_up_bb(pip,tips,sample,waste_dest,bead_vol,te_vol,transfer_vol,transfer_loc,xdir,mag_bead,ethanol):
	for tip,mag_samp in zip(tips,sample):
		pip.pick_up_tip(tip)
		pip.aspirate(20,mag_samp.bottom().move(types.Point(x=-0.7*xdir,y=0,z=.2)))
		pip.drop_tip()


def SPRI_clean_up_c(pip,tips,sample,bead_vol,te_vol,transfer_vol,transfer_loc,xdir,mag_bead,low_edta_te):
	#`tips` is a 1-element list of tips used in function.(ex [TIPS_5],)
	for tip,te,mag_samp in zip(tips,low_edta_te,sample):
		pip.pick_up_tip(tip)
		pip.aspirate(te_vol,te)
		pip.dispense(te_vol,mag_samp.top().move(types.Point(x=0.7*xdir,y=0,z=-6)))
		pip.blow_out(mag_samp.top())
		pip.flow_rate.aspirate=100
		pip.flow_rate.dispense=200
		if pip=="p300":
			p300_mix(10,te_vol,mag_samp,pip)  
		else:
			p20_mix(10,te_vol,mag_samp,pip)
		pip.blow_out(mag_samp.top())
		if te_vol>30:
			pip.touch_tip(v_offset=-6)
		else:
			pip.touch_tip(v_offset=-10)
		pip.flow_rate.aspirate=20
		pip.flow_rate.dispense=50
		pip.drop_tip()
def SPRI_clean_up_d(pip,tips,sample,bead_vol,te_vol,transfer_vol,transfer_loc,xdir,mag_bead):
	#`tips` is a 1-element list of tips used in function.(ex [TIPS_6],)
	for tip,mag_samp,trans_loc in zip(tips,sample,transfer_loc):
		pip.pick_up_tip(tip)
		p300_supernatant_removal(transfer_vol,mag_samp,trans_loc,pip,xdir=xdir)
#		pip.aspirate(transfer_vol,mag_samp)
#		pip.dispense(transfer_vol,trans_loc)
#		pip.blow_out(trans_loc.top())
#		pip.touch_tip(v_offset=-8)
		pip.drop_tip()
print(datetime.datetime.now())
overageFactor=1.2
numberSamples=16
startWell=3
numberColumns=math.ceil(numberSamples/8)
reagentCounterInit=1
reagentRTCounterInit=1
SPRI_1_vol=50  # 50 for(300-350bp)or 70 for (250-300bp) or 90 for (200-250bp) depending on insert size
SPRI_2a_vol=52.2
SPRI_2b_vol=60
SPRI_3_vol=30
SPRI_4_vol=42.5
debug="no"
start_odd_even="odd"
xdir=1 if start_odd_even=="odd" else -1
print("Processing "+str(numberSamples)+" samples using "+str(numberColumns)+" columns")
p20tipNumber=math.ceil(numberColumns*6/12)
p300tipNumber=math.ceil(numberColumns*30/12)
p20Location=["4","7"][:p20tipNumber]
p300Location=["5","8","9","10"][:p300tipNumber]
print("Using "+str(p20tipNumber)+" racks of p20 tips in slot(s) "+str(p20Location))
print("Using "+str(p300tipNumber)+" racks of p300 tips in slot(s) "+str(p300Location))
print("'vol.to.add' refers to the volume added over the entire protocol,i.e. 500*2=1000 ul ethanol")
print("Fragmentation Master Mix")
fragmentation_mm_volume=volume_calc(15,"96well100",numberColumns,overageFactor)
print("Reverse Transcription Master Mix")
reverse_transcription_mm_volume=volume_calc(6.5,"96well100",numberColumns,overageFactor)
print("Adaptase Master Mix")
adaptase_mm_volume=volume_calc(11,"96well100",numberColumns,overageFactor)
print("Extension Master Mix")
extension_mm_volume=volume_calc(23.5,"96well100",numberColumns,overageFactor)
print("Ligation Master Mix")
ligation_mm_volume=volume_calc(15.5,"96well100",numberColumns,overageFactor)
print("PCR Master Mix")
pcr_mm_volume=volume_calc(25.5,"96well100",numberColumns,overageFactor)
print("Mag Beads")
mag_bead_volume=volume_calc((SPRI_1_vol+SPRI_2a_vol+SPRI_2b_vol+SPRI_3_vol+SPRI_4_vol),"96well2000",numberColumns,overageFactor,)
print("Ethanol")
ethanol_volume=volume_calc(1800,"96well2000",numberColumns,overageFactor)
print("Low EDTA TE")
low_edta_te_volume=volume_calc(30+12+52+17+22+22,"96well2000",numberColumns,overageFactor)
def run(protocol):
	magdeck=protocol.load_module("magnetic module gen2","1")
	print("magnetic module in slot 1")
	magheight=9  # TODO figure out ????
	magplate=magdeck.load_labware("nest_96_wellplate_100ul_pcr_full_skirt","Mag_Sample_Plate")
	liqwaste=protocol.load_labware("nest_1_reservoir_195ml","11","Liquid Waste")
	print("liquid waste in slot 11")  # TODO We probably want to put waste in RT reagent plate
	waste=liqwaste["A1"].top()
	tempdeck=protocol.load_module("temperature module gen2","6")
	#TODO reset this back to 4	
	tempdeck.set_temperature(32)
	print("thermal module in slot 6")
	cool_reagents=tempdeck.load_labware(
		"opentrons_96_aluminumblock_nest_wellplate_100ul","Cool_Reagent_Plate")
	rt_reagents=protocol.load_labware("usascientific_12_reservoir_22ml","3")
	print("rt_reagents 96-well plate in slot 3")
	cold_plate=protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt","2")
	print("cold 96-well plate in slot 2")
	tips20=[protocol.load_labware("opentrons_96_tiprack_20ul",s) for s in p20Location]
	p20_tips=[tr["A"+str(i)] for tr in tips20 for i in range(1,13)]
	[tips_1,tips_2,tips_3,tips_4,tips_5,tips_6]=[p20_tips[i : i+numberColumns] for i in range(0,numberColumns*6,numberColumns)]
	tips300=[protocol.load_labware("opentrons_96_tiprack_300ul",s) for s in p300Location]
	p300_tips=[tr["A"+str(i)] for tr in tips300 for i in range(1,12)]
	[TIPS_1,TIPS_2, TIPS_3,TIPS_4,TIPS_5,TIPS_6,TIPS_7,TIPS_8,TIPS_9,TIPS_10,TIPS_11,TIPS_12,TIPS_13,TIPS_14,TIPS_15,TIPS_16,TIPS_17,TIPS_18,TIPS_19,TIPS_20,TIPS_21,TIPS_22,TIPS_23,TIPS_24,TIPS_25,TIPS_26,TIPS_27,TIPS_28,TIPS_29,TIPS_30,]=[p300_tips[i : i+numberColumns] for i in range(0,numberColumns*30,numberColumns)]
	print(TIPS_1)
	print(TIPS_2)
	print(TIPS_30)
	p20=protocol.load_instrument("p20_multi_gen2","right",tip_racks=tips20)
	print("p20 multichannel mounted on right arm")
	p300=protocol.load_instrument("p300_multi_gen2","left",tip_racks=tips300)
	print("p300 multichannel mounted on left arm")
	p300.flow_rate.aspirate=50  # reduced from 94
	p300.flow_rate.dispense=150  # increased from from 94
	p300.flow_rate.blow_out=300  # increased from 94
	p20.flow_rate.aspirate=60
	p20.flow_rate.dispense=150
	p20.flow_rate.blow_out=300
	fragmentation_mm,reagentCounter=reagent_assign(fragmentation_mm_volume,cool_reagents,reagentCounterInit)
	reverse_transcription_mm,reagentCounter=reagent_assign(reverse_transcription_mm_volume,cool_reagents,reagentCounter)
	adaptase_mm,reagentCounter=reagent_assign(
		adaptase_mm_volume,cool_reagents,reagentCounter)
	extension_mm,reagentCounter=reagent_assign(extension_mm_volume,cool_reagents,reagentCounter)
	ligation_mm,reagentCounter=reagent_assign(ligation_mm_volume,cool_reagents,reagentCounter)
	pcr_mm,reagentCounter=reagent_assign(pcr_mm_volume,cool_reagents,reagentCounter)
	mag_bead,reagentRTCounter=reagent_assign(mag_bead_volume,rt_reagents,reagentRTCounterInit)
	ethanol,reagentRTCounter=reagent_assign(ethanol_volume,rt_reagents,reagentRTCounter)
	low_edta_te,reagentRTCounter=reagent_assign(low_edta_te_volume,rt_reagents,reagentRTCounter)
	# TODO finish this
	mag_sample_1=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	mag_sample_2=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	mag_sample_3=[magplate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	cold_sample_1=[cold_plate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	cold_sample_2=[cold_plate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	cold_sample_3=[cold_plate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	cold_sample_4=[cold_plate["A"+str(i)] for i in range(startWell,startWell+numberColumns,1)]
	# TODO Figure out next sample well situation
	# Only using 'cold_plate' for samples not in magplate,so I need to figure out the flow of plates and columns; Fragmentation; PolyA selection (Last elution with 15ul Fragmentation Master Mix); Run Thermocycler off deck; return sample to magdeck when program has competed
	
	
	print('\n')
	print('Revers transcription mastermix here:')
	print(reverse_transcription_mm_volume['reservoir.volume'])
	print(unique(reverse_transcription_mm))
	print('\n')
	print('Adaptase master mix here:')
	print(adaptase_mm_volume['reservoir.volume'])
	print(unique(adaptase_mm))
	print('\n')
	print('Extension mm here:')
	print(extension_mm_volume['reservoir.volume'])
	print(unique(extension_mm))
	print('\n')
	print('Ligation mm here:')
	print(ligation_mm_volume['reservoir.volume'])
	print(unique(ligation_mm))
	print('\n')
	print('PCR here:')
	print(pcr_mm_volume['reservoir.volume'])
	print(unique(pcr_mm))
	print('\n')
	print('mag bead here:')
	print(mag_bead_volume['reservoir.volume'])
	print(unique(mag_bead))
	print('\n')
	
	print("Guess what line it is...", lineno())

	magdeck.engage(height=magheight)
	protocol.comment("Engaging Magnetic Module and incubate for 6 minutes.")
	protocol.delay(minutes=.6)
	# Transfer supernatant
	protocol.comment("Transfer Supernatent from Magnet plate to Cold plate")
	for cold_well,mag_well,tip in zip(cold_sample_1,mag_sample_1,tips_1):
		p20.pick_up_tip(tip)
		p20_supernatant_removal(14.5,mag_well,cold_well,p20,xdir=xdir)
		p20.drop_tip()
	magdeck.disengage()
	protocol.comment("lin4 404")
	# Incubate for 2 min
	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	# Reverse Transcription
	mastermix_transfer(p20,tips_2,reverse_transcription_mm,cold_sample_1,6.5)
	protocol.pause("Run Thermocycler off deck")
	protocol.comment("Line 414")
	# SPRI clean-up 1 (see ratio table)
	# spri cleanup vol: 50ul beads for 300-350bp; 70ul beads for 250-300bp; 90ul beads for 200-250bp
	p300.pick_up_tip(TIPS_5[0])
	for mag_samp,te in zip(mag_sample_1,low_edta_te):
		p300.aspirate(31,te)
		p300.dispense(31,mag_samp.top(-5))
		p300.blow_out(mag_samp.top())
		p300.touch_tip(v_offset=-6)
	p300.return_tip() 
	protocol.comment("Line 462")

	print("You made it to line...", lineno())	

	SPRI_clean_up_a(p300,TIPS_1,mag_sample_1,SPRI_1_vol,12.5,10.5,cold_sample_2,xdir,mag_bead)
	# Incubate -> Engage -> Incubate

	print("You made it to line...", lineno())		

	protocol.delay(minutes=.5)
	magdeck.engage(magheight)
	protocol.delay(minutes=.6)
		
	print("You made it to line...", lineno())
	SPRI_clean_up_b(p300,[TIPS_2,TIPS_3,TIPS_4],mag_sample_1,waste,SPRI_1_vol,12.5,10.5,cold_sample_2,xdir,mag_bead,ethanol)
#	SPRI_clean_up_bb(p20,tips_3,mag_sample_1,waste,SPRI_1_vol,12,10,cold_sample_2,xdir,mag_bead,ethanol)

	protocol.comment("Line 479")
	protocol.comment("Letting beads dry for 30 seconds.")
	protocol.delay(seconds=30)
	magdeck.disengage()
	SPRI_clean_up_c(p20,tips_4,mag_sample_1,SPRI_1_vol,12.5,10.5,cold_sample_2,xdir,mag_bead,low_edta_te)
	protocol.comment("Line 484")
	# Incubate -> Engage -> Incubate

	print("Guess what line it is...", lineno())

	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
	magdeck.engage()
	protocol.delay(minutes=.6)
	SPRI_clean_up_d(p20,tips_5,mag_sample_1,SPRI_1_vol,12.5,10.5,cold_sample_2,xdir,mag_bead)
	magdeck.disengage()
	protocol.pause("Run Thermocycler off deck: 95c denaturation for 2 min")
	protocol.comment("Line 445")
	# Adaptase; Preheat thermocycler to 95C; Denature 10ul eluate @95C w/lid temp on for 2 minutes; Move samples to cold block
	# Incubate for 2 min on cold block
	protocol.comment("Incubating on cold block for 2 minutes.")
	protocol.delay(minutes=.2)
	# Transfer Adaptase master mix to sample
	mastermix_transfer(p20,tips_6,adaptase_mm,cold_sample_2,11)
	protocol.pause("Run Thermocycler off deck")
	protocol.comment("Line 453")
	protocol.comment("Return plate to cold block")
	# Extension
	mastermix_transfer(p20,tips_1,extension_mm,cold_sample_2,23.5)
	protocol.pause("Run Thermocycler off deck")
	protocol.comment("Line 458")
	protocol.comment("Return plate to magnetic module")
	
	print("You made it to line...", lineno())	

	# SPRI clean-up 2a   
	SPRI_clean_up_a(p300,TIPS_5,mag_sample_2,SPRI_2a_vol,52.5,50.5,cold_sample_2,xdir,mag_bead)
	# Incubate -> Engage -> Incubate
	protocol.delay(minutes=.5)
	
	print("You made it to line...", lineno())	


	magdeck.engage(magheight)
	protocol.delay(minutes=.6)

	print("You made it to line...", lineno())	

	SPRI_clean_up_b(p300,[TIPS_6,TIPS_7,TIPS_8],mag_sample_2,waste,SPRI_2a_vol,52.5,50.5,cold_sample_2,xdir,mag_bead,ethanol)
#	SPRI_clean_up_bb(p20,tips_2,mag_sample_2,waste,SPRI_2a_vol,52,50,cold_sample_2,xdir,mag_bead,ethanol)	
	print("You made it to line...", lineno())	

	protocol.comment("Letting beads dry for 30 seconds.")
	protocol.delay(seconds=30)

	print("You made it to line...", lineno())	

	magdeck.disengage()
	SPRI_clean_up_c(p300,TIPS_9,mag_sample_2,SPRI_2a_vol,52.5,50.5,cold_sample_2,xdir,mag_bead,low_edta_te)
	# Incubate -> Engage -> Incubate
	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	protocol.comment("Line 477")
	protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
	magdeck.engage()
	protocol.delay(minutes=.6)
	SPRI_clean_up_d(p300,TIPS_10,mag_sample_2,SPRI_2a_vol,52.5,50.5,cold_sample_2,xdir,mag_bead)
	magdeck.disengage()
	protocol.pause("Place cold plate on magnetic module")
	protocol.comment("Line 484")

	print("You made it to line...", lineno())	

	# SPRI clean-up 2b
	SPRI_clean_up_a(p300,TIPS_11,mag_sample_2,SPRI_2b_vol,17.5,15.5,cold_sample_3,xdir,mag_bead)
	# Incubate -> Engage -> Incubate
	protocol.delay(minutes=.5)
	protocol.comment("Line 490")
	magdeck.engage(magheight)
	protocol.delay(minutes=.6)
	SPRI_clean_up_b(p300,[TIPS_12,TIPS_13,TIPS_14],mag_sample_2,waste,SPRI_2b_vol,17.5,15.5,cold_sample_3,xdir,mag_bead,ethanol)
#	SPRI_clean_up_bb(p20,tips_3,mag_sample_2,waste,SPRI_2b_vol,17,15,cold_sample_3,xdir,mag_bead,ethanol)
	protocol.comment("Letting beads dry for 30 seconds.")
	protocol.delay(seconds=30)
	protocol.comment("Line 496")
	magdeck.disengage()
	SPRI_clean_up_c(p20,tips_4,mag_sample_2,SPRI_2b_vol,17.5,15.5,cold_sample_3,xdir,mag_bead,low_edta_te)
	# Incubate -> Engage -> Incubate
	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	protocol.comment("Line 502")
	protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
	magdeck.engage()
	protocol.delay(minutes=.6)
	SPRI_clean_up_d(p20,tips_5,mag_sample_2,SPRI_2b_vol,17.5,15.5,cold_sample_3,xdir,mag_bead)
	magdeck.disengage()
	protocol.comment("Line 450")
	# Ligation
	mastermix_transfer(p20,tips_6,ligation_mm,cold_sample_3,15.5)
	protocol.pause("Run Thermocycler off deck")
	protocol.comment("Line 564")
	print("You made it to line...", lineno())	

	'''
	protocol.comment("Return plate to magnetic module")
	protocol.comment("Place 'Indexing Plate' on cold pack")
	# SPRI clean-up 3 (1x *1)
	SPRI_clean_up_a(p300,TIPS_15,mag_sample_3,SPRI_3_vol,22.5,20.5,cold_sample_3,xdir,mag_bead)
	# Incubate -> Engage -> Incubate
	protocol.delay(minutes=.5)
	protocol.comment("Line 521")
	magdeck.engage(magheight)
	protocol.delay(minutes=.6)
	SPRI_clean_up_b(p300,[TIPS_16,TIPS_17,TIPS_18],mag_sample_3,waste,SPRI_3_vol,22.5,20.5,cold_sample_3,xdir,mag_bead,ethanol)
#	SPRI_clean_up_bb(p20,tips_1,mag_sample_3,waste,SPRI_3_vol,22.5,20.5,cold_sample_3,xdir,mag_bead,ethanol)
	protocol.comment("Letting beads dry for 30 seconds.")
	protocol.delay(seconds=30)
	protocol.comment("Line 527")
	magdeck.disengage()
	SPRI_clean_up_c(p20,tips_2,mag_sample_3,SPRI_3_vol,22.5,20.5,cold_sample_3,xdir,mag_bead,low_edta_te)
	# Incubate -> Engage -> Incubate
	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	protocol.comment("Line 533")
	protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
	magdeck.engage()
	protocol.delay(minutes=.6)
	SPRI_clean_up_d(p20,tips_3,mag_sample_3,SPRI_3_vol,22.5,20.5,cold_sample_3,xdir,mag_bead)
	magdeck.disengage()
	protocol.comment("Line 539")
	# Transfer PCR master mix to sample
	mastermix_transfer(p20,tips_4,pcr_mm,cold_sample_3,25.5)
	protocol.pause("Run Thermocycler off deck")
	protocol.comment("Line 543")
	protocol.comment("Return plate to magnetic module")
	# SPRI Clean-up 4 (0.85x *1)
	SPRI_clean_up_a(p300,TIPS_19,mag_sample_3,SPRI_4_vol,22.5,20.5,cold_sample_4,xdir,mag_bead)
	# Incubate -> Engage -> Incubate
	protocol.delay(minutes=.5)
	protocol.comment("Line 549")
	magdeck.engage(magheight)
	protocol.delay(minutes=.6)
	SPRI_clean_up_b(p300,[TIPS_20,TIPS_21,TIPS_22],mag_sample_3,waste,SPRI_4_vol,22.5,20.5,cold_sample_4,xdir,mag_bead,ethanol)
#	SPRI_clean_up_bb(p20,tips_5,mag_sample_3,waste,SPRI_4_vol,22.5,20.5,cold_sample_4,xdir,mag_bead,ethanol)
	protocol.comment("Letting beads dry for 30 seconds.")
	protocol.delay(seconds=30)
	protocol.comment("Line 555")
	magdeck.disengage()
	SPRI_clean_up_c(p20,tips_6,mag_sample_3,SPRI_4_vol,22.5,20.5,cold_sample_4,xdir,mag_bead,low_edta_te)
	# Incubate -> Engage -> Incubate
	protocol.comment("Incubating for 2 minutes.")
	protocol.delay(minutes=.2)
	protocol.comment("Line 501")
	protocol.comment("Engaging Magnetic Module and incubating for 6 minutes.")
	magdeck.engage()
	protocol.delay(minutes=.6)
	SPRI_clean_up_d(p20,tips_1,mag_sample_3,SPRI_4_vol,22.5,20.5,cold_sample_4,xdir,mag_bead)
	magdeck.disengage()
	'''
