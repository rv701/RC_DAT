import tkinter as tk
from tkinter import filedialog

from tkinter import *
from tkinter.ttk import *

import sys
import os
import re
import time
from datetime import datetime, timedelta

def get_time(line) :
	line = re.sub(' +',' ',line) # Remove multiple spaces
	#print("get_time:", line)
	items = line.split(" ")
	#print ('Number of items:', len(items), 'arguments.')
	#print("Time:", items[2])
	return items[2]
	
def get_speed(line) :
	line = re.sub(' +',' ',line) # Remove multiple spaces
	#print("get_speed:", line)
	items = line.split(" ")
	#print ('Number of items:', len(items), 'arguments.')
	#print("Speed:", items[2].replace("Min",""))
	return int(items[2].replace("Min","")) # Remove Min string and return number

def open_file_dialog():
	file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("Text files", "*.DAT"), ("All files", "*.*")])
	if file_path:
		#selected_file_label.config(text=f"Selected File: {file_path}")
		temp = f"Selected File: {file_path}"
		temp2 = temp.split("/")
		temp = temp2[-1]
		selected_file_label.config(text=temp)
		process_file(file_path)

def process_file(file_path):
	# Implement your file processing logic here
	# For demonstration, let's just display the contents of the selected file



	lines = [line.rstrip('\n').rstrip('\r') for line in open(file_path)]
	# print ("File length: ", len(lines))
	
	clear = 0
	show = 0
	skip = 0
	total = 0 

	penalty_speed = 0
	penalty_wp = 0
	chk_index = 0
	
	last_wp = ""
	
	rider = ""
	stage = ""
	
	# Time Strings
	dss_tod = ""
	
	chk_tod = []
	chk_time = []
	chk_adj = []
	chk_note = []
	
	fss_tod = ""
	fss_time = ""
	fss_adj = ""
	fss_note = ""
	
	eos_tod = ""
	eos_time = ""
	eos_adj = ""
	eos_note = ""
	
	tmp_str = ""
	
	output_text = ""
	#output_text = "DES\tTOD      \t\tTIME    \t\tADJ\n"
	
	dss_set = False
	
	for index in range(1, len(lines)):
		#print(index, ":", lines[index])
		
		if re.search("Show", lines[index]) and re.search("^[a-zA-Z]", lines[index]): # Line contains "Skip" and starts with letter
			print(lines[index])
			print("Opened WP")
			
			temp = lines[index].split(" ")
			last_wp = re.sub("^[a-zA-Z]+", "", temp[0]) # Strip leading chars and return number
			print("LastWP: " + last_wp) # Set last WP for Show/Skip test
			
			show+=1
			total+=1
			penalty_wp+=10
		if re.search("Skip", lines[index]) and not re.search("No Skip", lines[index]) :
			print(lines[index])
			print("Skipped WP")
			
			temp = lines[index].split(" ")
			current_wp = re.sub("^[a-zA-Z]+", "", temp[0]) # Strip leading chars and return number
			
			if last_wp == current_wp :
				show-=1
				total-=1
				penalty_wp-=10
				print("CurrentWP: " + last_wp)
				print("Show WP Credit " + last_wp)
			skip+=1
			total+=1
			penalty_wp+=20
			last_wp="" # Clear last wp until next WP Opening
		if re.search("Clear", lines[index]) :
			#print(lines[index])
			#print("Cleared WP")
			clear+=1
			total+=1
			last_wp="" # Clear last wp until next WP Opening
		if re.search("^SSZ", lines[index]) and re.search("Min$", lines[index]):
			#print(lines[index])
			#print("Speeding Penalty")
			penalty_speed += get_speed(lines[index])
			
		# Look for time points
		if re.search("^End:", lines[index]) :
			print("End Stage Found.")
			break
		if re.search("^Rally", lines[index]) and re.search("Cancelled", lines[index]) :
			print(lines[index])
			print("Stage Cancelled")
			
			# Reset Penalty Counters
			clear = 0
			show = 0
			skip = 0
			total = 0 
			penalty_speed = 0
			penalty_wp = 0
			chk_index = 0
		if re.search("^#", lines[index]) :
			print(lines[index])
			#output_text += (lines[index]) + "\n"
			words = re.split('\s+', lines[index])
			#output_text += "Rider: " + words[0].replace('#','') + "\n"
			#output_text += "Stage: " + words[1].replace('Stage:','') + "\n"
			rider = words[0].replace('#','')
			stage = words[1].replace('Stage:','')
		if re.search("^Start", lines[index]):
			temp = lines[index].split(" ")
			print(lines[index])
			if len(temp) >= 2:
				print(temp[2])
				#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
				#time_start = get_time (lines[index])
				time_start = datetime.strptime(temp[2], '%H:%M:%S')
				dss_tod = str(temp[2])
		if re.search("^Reset", lines[index]):
			temp = lines[index].split(" ")
			print (lines[index])
			#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
			#time_start = get_time (lines[index])
			#time_start = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			#dss_tod = str(get_time(lines[index]))
			#dss_set = True
			if len(temp) >= 4:
				print(temp[3])
				#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
				#time_start = get_time (lines[index])
				time_start = datetime.strptime(temp[3], '%H:%M:%S')
				dss_tod = str(temp[3])
		if re.search("^CKP", lines[index]):
			print (lines[index])
			time_checkpoint = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			time_delta = time_checkpoint - time_start
			time_change = timedelta(minutes=(penalty_wp + penalty_speed)) 
			time_adjust = (time_checkpoint - time_start) + time_change
			#output_text +=  "CKP:\t" + get_time(lines[index]) + "\t\t" + str(time_delta) + "\t\t" + str(time_adjust) + "\n"
			
			chk_tod.append(str(get_time(lines[index])))
			
			tmp_str = str(time_delta)
			if ( len(tmp_str) == 7):
				tmp_str = "0" + tmp_str
			chk_time.append(tmp_str)
			
			tmp_str = str(time_adjust)
			if ( len(tmp_str) == 7):
				tmp_str = "0" + tmp_str
			chk_adj.append(tmp_str)
			
			chk_note.append("WPPenalty:" + str(penalty_wp) + ", SZPenalty:" + str(penalty_speed))
			
		if re.search("^FSS", lines[index]):
			print (lines[index])
			time_end = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			time_delta = time_end - time_start
			time_change = timedelta(minutes=(penalty_wp + penalty_speed)) 
			time_adjust = (time_end - time_start) + time_change
			#output_text +=  "FSS:\t" + get_time(lines[index]) + "\t\t" +  str(time_delta) + "\t\t" +  str(time_adjust) + "\n"
			
			fss_tod = str(get_time(lines[index]))
			fss_time = str(time_delta)
			if ( len(fss_time) == 7):
				fss_time = "0" + fss_time
			fss_adj = str(time_adjust)
			if ( len(fss_adj) == 7):
				fss_adj = "0" + fss_adj
			fss_note = "WPPenalty:" + str(penalty_wp) + ", SZPenalty:" + str(penalty_speed)
			

	
	output_text += "WP Open: " + str(show) + "\n"
	output_text += "WP Skipped: " + str(skip) + "\n"
	output_text += "WP Clear: " + str(clear) + "\n"
	output_text += "WP Total: " + str(total) + "\n"
	output_text += "WP Penalty: " + str(penalty_wp) + "Min" + "\n"
	output_text += "\nSpeed Penalty: " + str(penalty_speed) + "Min" + "\n"
	output_text += "Total Penalty: " + str(penalty_wp + penalty_speed) + "Min" + "\n"
	
	#output_text += "\nNote: EOS, WPPenalty:" + str(penalty_wp) + ", SZPenalty:" + str(penalty_speed) + "\n"
	
	time_change = timedelta(minutes=(penalty_wp + penalty_speed)) 
	time_adjust = (time_end - time_start) + time_change
	
	eos_tod = fss_tod
	eos_time = fss_time
	eos_adj = str(time_adjust)
	if ( len(eos_adj) == 7):
		eos_adj = "0" + eos_adj
	eos_note = "WPPenalty:" + str(penalty_wp) + ", SZPenalty:" + str(penalty_speed)
	
	#output_text += "\n\n"
	#output_text += dss_tod + "\tDSS\n"
	
	ent_rider.set( rider )
	ent_stage.set( stage )
	
	r1_tod.set( dss_tod )
	
	# Clear CKP rows
	r2_tod.set( "")
	r2_note.set( "" )
	r2_time.set( "" )
	r2_adj.set( "" )
	r3_tod.set( "")
	r3_note.set( "" )
	r3_time.set( "" )
	r3_adj.set( "" )
	r4_tod.set( "")
	r4_note.set( "" )
	r4_time.set( "" )
	r4_adj.set( "" )
	r5_tod.set( "")
	r5_note.set( "" )
	r5_time.set( "" )
	r5_adj.set( "" )
	r6_tod.set( "")
	r6_note.set( "" )
	r6_time.set( "" )
	r6_adj.set( "" )
			
			
	for index in range(1, len(chk_tod)):
		#output_text += chk_tod[index] + "\tCKP" + str(index) + ", " + chk_note[index] + "\t" + chk_time[index] + "\t" + chk_adj[index] + "\n"
		if(index == 1):
			r2_tod.set( chk_tod[index] )
			r2_note.set( "CKP" + str(index) + ", " + chk_note[index] )
			r2_time.set( chk_time[index] )
			r2_adj.set( chk_adj[index] )
		if(index == 2):
			r3_tod.set( chk_tod[index] )
			r3_note.set( "CKP" + str(index) + ", " + chk_note[index] )
			r3_time.set( chk_time[index] )
			r3_adj.set( chk_adj[index] )
		if(index == 3):
			r4_tod.set( chk_tod[index] )
			r4_note.set( "CKP" + str(index) + ", " + chk_note[index] )
			r4_time.set( chk_time[index] )
			r4_adj.set( chk_adj[index] )
		if(index == 4):
			r5_tod.set( chk_tod[index] )
			r5_note.set( "CKP" + str(index) + ", " + chk_note[index] )
			r5_time.set( chk_time[index] )
			r5_adj.set( chk_adj[index] )
		if(index == 5):
			r6_tod.set( chk_tod[index] )
			r6_note.set( "CKP" + str(index) + ", " + chk_note[index] )
			r6_time.set( chk_time[index] )
			r6_adj.set( chk_adj[index] )
	r7_tod.set( fss_tod )
	r7_note.set( "FSS, " + fss_note )
	r7_time.set( fss_time )
	r7_adj.set( fss_adj )
	
	r8_tod.set( eos_tod )
	r8_note.set( "EOS, " + eos_note )
	r8_time.set( eos_time )
	r8_adj.set( eos_adj )
			
	#output_text += fss_tod + "\tFSS, " + fss_note + "\t" + fss_time + "\t" + fss_adj + "\n"
	#output_text += eos_tod + "\tEOS, " + eos_note + "\t" + eos_time + "\t" + eos_adj + "\n"
	
	log_note = eos_note.replace(",","_")
	log_note = log_note.replace(" ","")
	log_note = "EOS_" + log_note
	
	log_text = "" 
	if (os.path.isfile("DAT_Log.csv") == False): # Add header for new files only
		log_text += "Racer,Stage,Note,CKP1,CKP2,CKP3,CKP4,CKP5,FSS,EOS\n"
		
	log_text += rider + "," + stage + "," + log_note + ","
	if(len(chk_tod) >= 1):
		log_text += chk_adj[0]
	log_text += ","
	if(len(chk_tod) >= 2):
		log_text += chk_adj[1]
	log_text += ","
	if(len(chk_tod) >= 3):
		log_text += chk_adj[2]
	log_text += ","
	if(len(chk_tod) >= 4):
		log_text += chk_adj[3]
	log_text += ","
	if(len(chk_tod) >= 5):
		log_text += chk_adj[4]
	log_text += ","
	log_text += fss_adj + "," + eos_adj + "\n"
	
	f = open("DAT_Log.csv", "a")
	f.write(log_text)
	f.close()
		

	
	file_text.delete('1.0', tk.END)
	file_text.insert(tk.END, output_text)
			    


#root = tk.Tk()
root = tk.Tk(className=' rc dat reader ')
#root = tk.Tk(screenName=None,  baseName=None,  className='TEST',  useTk=1)
root.title("RC DAT Reader")
root.iconphoto(False, PhotoImage(file='RC.png'))
#root.iconbitmap(r'./RC.ico')
#root = Tk(className='Testing')

open_button = tk.Button(root, text="Open File", command=open_file_dialog)
open_button.grid(column=0, row=0, padx=5, pady=5)

selected_file_label = tk.Label(root, text="Selected File:")
selected_file_label.grid(column=0, row=1, padx=5, pady=5)

# Rider/Stage
lbl1 = Label(root, text="Rider")
lbl1.grid(column=3, row=0, padx=5, pady=5)

ent_rider = StringVar()
ent1 = Entry(root, textvariable=ent_rider, width=15)
ent1.grid(column=4, row=0, padx=5, pady=5)

lbl2 = Label(root, text="Stage")
lbl2.grid(column=3, row=1, padx=5, pady=5)

ent_stage = StringVar()
ent2 = Entry(root, textvariable=ent_stage, width=15)
ent2.grid(column=4, row=1, padx=5, pady=5)

# Space
lbl3 = Label(root, text=" ")
lbl3.grid(column=0, row=2, padx=5, pady=5)
lbl4 = Label(root, text=" ")
lbl4.grid(column=0, row=3, padx=5, pady=5)

# Table Header
th1 = Label(root, text="DESCRIPTION")
th1.grid(column=0, row=4, padx=5, pady=5)
th2 = Label(root, text="TOD")
th2.grid(column=1, row=4, padx=5, pady=5)
th3 = Label(root, text="NOTE")
th3.grid(column=2, row=4, padx=5, pady=5)
th4 = Label(root, text="TIME")
th4.grid(column=3, row=4, padx=5, pady=5)
th5 = Label(root, text="ADJUSTED")
th5.grid(column=4, row=4, padx=5, pady=5)

# Row 1
r1_des = StringVar()
td11 = Entry(root, textvariable=r1_des, width=15)
r1_des.set( "DSS" )
td11.grid(column=0, row=5, padx=5, pady=5)

r1_tod = StringVar()
td12 = Entry(root, textvariable=r1_tod, width=15)
td12.grid(column=1, row=5, padx=5, pady=5)

r1_note = StringVar()
td13 = Entry(root, textvariable=r1_note, width=30)
td13.grid(column=2, row=5, padx=5, pady=5)

r1_time = StringVar()
td14 = Entry(root, textvariable=r1_time, width=15)
td14.grid(column=3, row=5, padx=5, pady=5)

r1_adj = StringVar()
td15 = Entry(root, textvariable=r1_adj, width=15)
td15.grid(column=4, row=5, padx=5, pady=5)

# Row 2
r2_des = StringVar()
td21 = Entry(root, textvariable=r2_des, width=15)
r2_des.set( "CPK1" )
td21.grid(column=0, row=6, padx=5, pady=5)

r2_tod = StringVar()
td22 = Entry(root, textvariable=r2_tod, width=15)
td22.grid(column=1, row=6, padx=5, pady=5)

r2_note = StringVar()
td23 = Entry(root, textvariable=r2_note, width=30)
td23.grid(column=2, row=6, padx=5, pady=5)

r2_time = StringVar()
td24 = Entry(root, textvariable=r2_time, width=15)
td24.grid(column=3, row=6, padx=5, pady=5)

r2_adj = StringVar()
td25 = Entry(root, textvariable=r2_adj, width=15)
td25.grid(column=4, row=6, padx=5, pady=5)

# Row 3
r3_des = StringVar()
td31 = Entry(root, textvariable=r3_des, width=15)
r3_des.set( "CKP2" )
td31.grid(column=0, row=7, padx=5, pady=5)

r3_tod = StringVar()
td32 = Entry(root, textvariable=r3_tod, width=15)
td32.grid(column=1, row=7, padx=5, pady=5)

r3_note = StringVar()
td33 = Entry(root, textvariable=r3_note, width=30)
td33.grid(column=2, row=7, padx=5, pady=5)

r3_time = StringVar()
td34 = Entry(root, textvariable=r3_time, width=15)
td34.grid(column=3, row=7, padx=5, pady=5)

r3_adj = StringVar()
td35 = Entry(root, textvariable=r3_adj, width=15)
td35.grid(column=4, row=7, padx=5, pady=5)

# Row 4
r4_des = StringVar()
td41 = Entry(root, textvariable=r4_des, width=15)
r4_des.set( "CKP3" )
td41.grid(column=0, row=8, padx=5, pady=5)

r4_tod = StringVar()
td42 = Entry(root, textvariable=r4_tod, width=15)
td42.grid(column=1, row=8, padx=5, pady=5)

r4_note = StringVar()
td43 = Entry(root, textvariable=r4_note, width=30)
td43.grid(column=2, row=8, padx=5, pady=5)

r4_time = StringVar()
td44 = Entry(root, textvariable=r4_time, width=15)
td44.grid(column=3, row=8, padx=5, pady=5)

r4_adj = StringVar()
td45 = Entry(root, textvariable=r4_adj, width=15)
td45.grid(column=4, row=8, padx=5, pady=5)

# Row 5
r5_des = StringVar()
td51 = Entry(root, textvariable=r5_des, width=15)
r5_des.set( "CKP4" )
td51.grid(column=0, row=9, padx=5, pady=5)

r5_tod = StringVar()
td52 = Entry(root, textvariable=r5_tod, width=15)
td52.grid(column=1, row=9, padx=5, pady=5)

r5_note = StringVar()
td53 = Entry(root, textvariable=r5_note, width=30)
td53.grid(column=2, row=9, padx=5, pady=5)

r5_time = StringVar()
td54 = Entry(root, textvariable=r5_time, width=15)
td54.grid(column=3, row=9, padx=5, pady=5)

r5_adj = StringVar()
td55 = Entry(root, textvariable=r5_adj, width=15)
td55.grid(column=4, row=9, padx=5, pady=5)

# Row 6
r6_des = StringVar()
td61 = Entry(root, textvariable=r6_des, width=15)
r6_des.set( "CKP5" )
td61.grid(column=0, row=10, padx=5, pady=5)

r6_tod = StringVar()
td62 = Entry(root, textvariable=r6_tod, width=15)
td62.grid(column=1, row=10, padx=5, pady=5)

r6_note = StringVar()
td63 = Entry(root, textvariable=r6_note, width=30)
td63.grid(column=2, row=10, padx=5, pady=5)

r6_time = StringVar()
td64 = Entry(root, textvariable=r6_time, width=15)
td64.grid(column=3, row=10, padx=5, pady=5)

r6_adj = StringVar()
td65 = Entry(root, textvariable=r6_adj, width=15)
td65.grid(column=4, row=10, padx=5, pady=5)

# Row 7
r7_des = StringVar()
td71 = Entry(root, textvariable=r7_des, width=15)
r7_des.set( "FSS" )
td71.grid(column=0, row=11, padx=5, pady=5)

r7_tod = StringVar()
td72 = Entry(root, textvariable=r7_tod, width=15)
td72.grid(column=1, row=11, padx=5, pady=5)

r7_note = StringVar()
td73 = Entry(root, textvariable=r7_note, width=30)
td73.grid(column=2, row=11, padx=5, pady=5)

r7_time = StringVar()
td74 = Entry(root, textvariable=r7_time, width=15)
td74.grid(column=3, row=11, padx=5, pady=5)

r7_adj = StringVar()
td75 = Entry(root, textvariable=r7_adj, width=15)
td75.grid(column=4, row=11, padx=5, pady=5)

# Row 8
r8_des = StringVar()
td81 = Entry(root, textvariable=r8_des, width=15)
r8_des.set( "EOS" )
td81.grid(column=0, row=12, padx=5, pady=5)

r8_tod = StringVar()
td82 = Entry(root, textvariable=r8_tod, width=15)
td82.grid(column=1, row=12, padx=5, pady=5)

r8_note = StringVar()
td83 = Entry(root, textvariable=r8_note, width=30)
td83.grid(column=2, row=12, padx=5, pady=5)

r8_time = StringVar()
td84 = Entry(root, textvariable=r8_time, width=15)
td84.grid(column=3, row=12, padx=5, pady=5)

r8_adj = StringVar()
td85 = Entry(root, textvariable=r8_adj, width=15)
td85.grid(column=4, row=12, padx=5, pady=5)


file_text = tk.Text(root, wrap=tk.WORD, height=10, width=95)
file_text.grid(column=0, row=13, padx=5, pady=5, columnspan=5)

root.mainloop()
