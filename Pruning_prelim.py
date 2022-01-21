# Import json Python module
import json
import numpy as np
import time
import pyhf

file = open("likelihood_32.json", 'r')
json_data = json.load(file)

for key, value in json_data.items():
    if(key == 'channels'):
    	for i in value:
    		print("i",i.get('name'))
    		for samp in i.get('samples'):
        		#skip samples which are not to be pruned
        		if ('mufakes') in samp.get('name'):
        			continue
        		
        		#Nominal yield	
        		lists_to_modify = [samp.get('data')]
        		
        		#Get all the modifiers
        		for mod in samp.get('modifiers'):
        			if(mod.get('type') == 'staterror'):
        				lists_to_modify.append(mod.get('data'))
        			if(mod.get('type') == 'histosys'):
        				lists_to_modify.append(mod.get('data').get('hi_data'))
        				lists_to_modify.append(mod.get('data').get('lo_data'))
        		
        		#Set all nominal negative yields to 0 - this is giving an assertion error
        		 
        		#Solution - Fix it to negligible yields
        		#Poisson prob mass distribution is not well defined for 0 yields in histfactory
        		#Fix Nominal, corresponding uncertainties, staterror to 1e-20. 
        		for data_index in range(len(samp.get('data'))):
        			if samp.get('data')[data_index] < 0 or samp.get('data')[data_index] == 0:
        				for list in lists_to_modify:
        					list[data_index] = 1e-20
        		
        		#Set all the uncertainties (histosys, staterror) to 0
        		for i, sys in enumerate(lists_to_modify):
        			for j, val in enumerate(sys):
        				if(val<0 or val == 0):
        					sys[j]=1e-20
        		
        		#For RELATIVE staterror data > 1, set it to 1e-20, set the corresponding nominal, uncertainties to 0
        		for index in range(len(samp.get('data'))): 
        			#no staterror for signal, hardcoded for now      			
        			if ('ttX') in samp.get('name'):
        				continue
        				
        			#Get relative error, data in staterror is absolute error        				
        			if (lists_to_modify[1][index]/samp.get('data')[index] > 1):
        				for list in lists_to_modify:
        					list[index] = 1e-20
        
channels = json_data['channels']
observe = json_data['observations']

#Remove all contributions from samples which are below 2% in all bins, in each channel
for iobs,obs in enumerate(observe):
	for ichannel, channel in enumerate(channels):
		samples = channel['samples']
		samples_to_remove = []
		for isamp, samp in enumerate(samples):
			if ('mufakes') in samp['name']:
				continue					
			if(obs['name']!= channel['name']):
				continue
			Nominal = samp['data']
			Total = obs['data']
			fract = np.divide(Nominal,Total)
			maxfract = np.max(fract)
			
			if maxfract < 0.02:
				samples_to_remove.append(isamp)
		for samp in reversed(samples_to_remove): del samples[samp]											

#HistoSys, NormSys Pruning 
for ichannel, channel in enumerate(channels):
	samples = channel['samples']
	for isamp, samp in enumerate(samples):
		if ('mufakes') in samp['name']:
			continue
		#Get Nominal Yield per sample per channel
		Nom = np.array(samp['data'])
				
		# clean this up, lots of repetitions !! Very hand wavy to make it work at the moment.
		modifiers = samp['modifiers']
		mods_to_remove = []
		for imodifier,modifier in enumerate(modifiers):
			if modifier['type'] == 'histosys':
				hi = np.array(modifier['data']['hi_data'])
				lo = np.array(modifier['data']['lo_data'])
				var = np.divide(np.maximum(np.abs(hi-Nom), np.abs(lo-Nom)), Nom, where=Nom!=0)
				maxvar = np.max(var)
				if 'SR' in channel['name'] and maxvar < 0.02:
					mods_to_remove.append(imodifier)
				elif 'TTZ' in channel['name'] and maxvar < 0.05:
					mods_to_remove.append(imodifier)
				elif 'ttbar' in channel['name'] and maxvar < 0.1:
					mods_to_remove.append(imodifier)
				elif 'AR' in channel['name'] and maxvar < 0.1:
					mods_to_remove.append(imodifier)

			if modifier['type'] == 'normsys':
				hi_ = modifier['data']['hi']
				lo_ = modifier['data']['lo']
				hi_lo_ = [np.abs(1-hi_),np.abs(1-lo_)]
				maxvar = np.max(hi_lo_)
								
				if 'SR' in channel['name'] and maxvar < 0.02:
					mods_to_remove.append(imodifier)
				elif 'TTZ' in channel['name'] and maxvar < 0.05:
					mods_to_remove.append(imodifier)
				elif 'ttbar' in channel['name'] and maxvar < 0.1:
					mods_to_remove.append(imodifier)
				elif 'AR' in channel['name'] and maxvar < 0.1:
					mods_to_remove.append(imodifier)
		for modifier in reversed(mods_to_remove): del modifiers[modifier]
				
with open("pruned_32_negligible.json",'w') as outfile:
	#issue - values are printed vertically, not horizontally, write up an encoder
	json.dump(json_data, outfile, sort_keys=True, indent=4)
file.close()	

