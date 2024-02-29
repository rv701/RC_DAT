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
	print ("File length: ", len(lines))
	
	clear = 0
	show = 0
	skip = 0
	total = 0 

	penalty_speed = 0
	penalty_wp = 0
	
	output_text = "DES\tTOD      \t\tTIME    \t\tADJ\n"
	
	for index in range(1, len(lines)):
		#print(index, ":", lines[index])
		
		if re.search("Show", lines[index]) :
			show+=1
			total+=1
			penalty_wp+=10
		if re.search("Skip", lines[index]) :
			skip+=1
			total+=1
			penalty_wp+=20
		if re.search("Clear", lines[index]) :
			clear+=1
			total+=1
		if re.search("^SSZ", lines[index]) and re.search("Min$", lines[index]):
			penalty_speed += get_speed(lines[index])
			
		# Look for time points
		if re.search("^DSS", lines[index]) :
			#print (lines[index])
			output_text += "DSS:\t" + get_time(lines[index]) + "\n"
			#time_start = get_time (lines[index])
			time_start = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
		if re.search("^CKP", lines[index]) :
			#print (lines[index])
			time_checkpoint = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			time_delta = time_checkpoint - time_start
			time_change = timedelta(minutes=(penalty_wp + penalty_speed)) 
			time_adjust = (time_checkpoint - time_start) + time_change
			output_text +=  "CKP:\t" + get_time(lines[index]) + "\t\t" + str(time_delta) + "\t\t" + str(time_adjust) + "\n"
		if re.search("^FSS", lines[index]) :
			#print (lines[index])
			time_end = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			time_delta = time_end - time_start
			time_change = timedelta(minutes=(penalty_wp + penalty_speed)) 
			time_adjust = (time_end - time_start) + time_change
			output_text +=  "FSS:\t" + get_time(lines[index]) + "\t\t" +  str(time_delta) + "\t\t" +  str(time_adjust) + "\n"

	output_text += "\nWP Clear: " + str(clear) + "\n"
	output_text += "WP Open: " + str(show) + "\n"
	output_text += "WP Skipped: " + str(skip) + "\n"
	output_text += "WP Total: " + str(total) + "\n"
	output_text += "WP Penalty: " + str(penalty_wp) + "Min" + "\n"
	output_text += "\nSpeed Penalty: " + str(penalty_speed) + "Min" + "\n"
	output_text += "\nTotal Penalty: " + str(penalty_wp + penalty_speed) + "Min" + "\n"
	
	output_text += "\nNote: EOS, WPPenalty:" + str(penalty_wp) + ", SZPenalty:" + str(penalty_speed) + "\n"
	
	
	
	file_text.delete('1.0', tk.END)
	file_text.insert(tk.END, output_text)
			    


root = tk.Tk()
root.title("RC DAT Reader")
root.iconphoto(False, PhotoImage(file='RC.png'))
#root.iconbitmap(r'./RC.ico')

open_button = tk.Button(root, text="Open File", command=open_file_dialog)
open_button.pack(padx=20, pady=20)

selected_file_label = tk.Label(root, text="Selected File:")
selected_file_label.pack()

file_text = tk.Text(root, wrap=tk.WORD, height=25, width=50)
file_text.pack(padx=20, pady=20)

root.mainloop()
