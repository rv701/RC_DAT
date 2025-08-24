import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import *
from tkinter.ttk import *

import sys
import os
import re
import time
import glob
from datetime import datetime, timedelta

def get_time(line) :
	line = re.sub(' +',' ',line) # Remove multiple spaces
	#print("get_time:", line)
	items = line.split(" ")
	#print ('Number of items:', len(items), 'arguments.')
	#print("Time:", items[2])
	
	# Check if we have enough items
	if len(items) < 3:
		print(f"Warning: Not enough items in time line '{line}', using default time")
		return "00:00:00"
	
	# Check if the third item looks like a time (HH:MM:SS format)
	time_candidate = items[2]
	if re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_candidate):
		return time_candidate
	else:
		# If it's not a time format, look for a time pattern in the line
		time_match = re.search(r'\d{1,2}:\d{2}:\d{2}', line)
		if time_match:
			return time_match.group()
		else:
			print(f"Warning: No valid time found in line '{line}', using default time")
			return "00:00:00"

def parse_time_with_extended_hours(time_str):
	"""
	Parse time string that may have hours > 24
	Example: "24:09:01" becomes a datetime object representing 24 hours 9 minutes 1 second
	"""
	try:
		# Try standard parsing first
		return datetime.strptime(time_str, '%H:%M:%S')
	except ValueError:
		# If that fails, handle extended hours
		parts = time_str.split(':')
		if len(parts) == 3:
			hours = int(parts[0])
			minutes = int(parts[1])
			seconds = int(parts[2])
			
			# Create a timedelta for the extended time
			extended_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
			
			# Convert to a datetime by adding to a base time (midnight)
			base_time = datetime.strptime("00:00:00", '%H:%M:%S')
			return base_time + extended_time
		else:
			raise ValueError(f"Invalid time format: {time_str}")
	
def get_speed(line) :
	line = re.sub(' +',' ',line) # Remove multiple spaces
	#print("get_speed:", line)
	items = line.split(" ")
	#print ('Number of items:', len(items), 'arguments.')
	#print("Speed:", items[2].replace("Min",""))
	
	# Check if we have enough items and if the third item is a number
	if len(items) >= 3:
		try:
			# Try to convert to integer, removing "Min" if present
			speed_value = items[2].replace("Min","")
			return int(speed_value)
		except ValueError:
			# If conversion fails, return 0 (no penalty)
			print(f"Warning: Could not parse speed penalty from '{items[2]}', using 0")
			return 0
	else:
		# Not enough items, return 0
		print(f"Warning: Not enough items in speed line '{line}', using 0")
		return 0

def format_timedelta(td):
	"""
	Format timedelta to show hours beyond 24 as HH:MM:SS
	Example: 1 day, 1:24:14 becomes 25:24:14
	"""
	total_seconds = int(td.total_seconds())
	hours = total_seconds // 3600
	minutes = (total_seconds % 3600) // 60
	seconds = total_seconds % 60
	return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def select_directory():
	directory_path = filedialog.askdirectory(title="Select Directory to Process")
	if directory_path:
		directory_var.set(directory_path)
		update_status(f"Selected directory: {directory_path}")

def open_single_file():
	file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("Text files", "*.DAT"), ("All files", "*.*")])
	if file_path:
		selected_file_label.config(text=f"Selected: {os.path.basename(file_path)}")
		process_file(file_path, batch_mode=False)

def process_batch():
	directory = directory_var.get()
	filename_pattern = filename_pattern_var.get()
	
	if not directory:
		messagebox.showerror("Error", "Please select a directory first.")
		return
	
	if not filename_pattern:
		messagebox.showerror("Error", "Please enter a filename pattern (e.g., *.DAT).")
		return
	
	# Clear previous results
	file_text.delete('1.0', tk.END)
	update_status("Starting batch processing...")
	
	# Find all matching files recursively
	search_pattern = os.path.join(directory, "**", filename_pattern)
	files = glob.glob(search_pattern, recursive=True)
	
	if not files:
		update_status(f"No files found matching pattern: {filename_pattern}")
		return
	
	update_status(f"Found {len(files)} files to process")
	
	processed_count = 0
	error_count = 0
	
	for i, file_path in enumerate(files):
		try:
			update_status(f"Processing {i+1}/{len(files)}: {os.path.basename(file_path)}")
			process_file(file_path, batch_mode=True)
			processed_count += 1
			root.update()  # Update GUI to show progress
		except Exception as e:
			error_count += 1
			error_msg = f"Error processing {os.path.basename(file_path)}: {str(e)}"
			file_text.insert(tk.END, error_msg + "\n")
			print(error_msg)
	
	update_status(f"Batch processing complete. Processed: {processed_count}, Errors: {error_count}")

def update_status(message):
	status_label.config(text=message)
	root.update()

def process_file(file_path, batch_mode=False):
	# Implement your file processing logic here
	# For demonstration, let's just display the contents of the selected file

	try:
		lines = [line.rstrip('\n').rstrip('\r') for line in open(file_path)]
	except Exception as e:
		if not batch_mode:
			messagebox.showerror("Error", f"Could not open file: {str(e)}")
		raise e
	
	# print ("File length: ", len(lines))
	
	# Initialize loop tracking variables
	loop_counter = 0
	current_loop_rider = ""
	current_loop_stage = ""
	
	# Initialize arrays to store data for each loop
	all_loops_data = []
	
	# Variables for current loop processing
	clear = 0
	show = 0
	skip = 0
	total = 0 

	penalty_speed = 0
	penalty_wp = 0
	penalty_fn = 0
	chk_index = 0
	
	last_wp = ""
	
	rider = ""
	stage = ""
	
	# Time Strings
	dss_tod = ""
	
	# Initialize time variables
	time_start = None
	time_end = None
	dss_found = False  # Flag to track if DSS was found
	
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
		
		# Check for new loop start (lines starting with #)
		if re.search("^#", lines[index]):
			# If we have data from the previous loop, save it
			if dss_found and (rider != "" or stage != ""):
				loop_data = {
					'loop_counter': loop_counter,
					'rider': rider,
					'stage': stage,
					'clear': clear,
					'show': show,
					'skip': skip,
					'total': total,
					'penalty_speed': penalty_speed,
					'penalty_wp': penalty_wp,
					'penalty_fn': penalty_fn,
					'dss_tod': dss_tod,
					'chk_tod': chk_tod.copy(),
					'chk_time': chk_time.copy(),
					'chk_adj': chk_adj.copy(),
					'chk_note': chk_note.copy(),
					'fss_tod': fss_tod,
					'fss_time': fss_time,
					'fss_adj': fss_adj,
					'fss_note': fss_note,
					'eos_tod': eos_tod,
					'eos_time': eos_time,
					'eos_adj': eos_adj,
					'eos_note': eos_note
				}
				all_loops_data.append(loop_data)
			
			# Start new loop
			loop_counter += 1
			print(f"Starting loop {loop_counter}")
			
			# Reset all counters and variables for new loop
			clear = 0
			show = 0
			skip = 0
			total = 0 
			penalty_speed = 0
			penalty_wp = 0
			penalty_fn = 0
			chk_index = 0
			last_wp = ""
			dss_tod = ""
			time_start = None
			time_end = None
			dss_found = False
			dss_set = False
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
			
			# Parse rider and stage from the # line
			words = re.split('\s+', lines[index])
			if len(words) >= 2:
				rider = words[0].replace('#','')
				stage = words[1].replace('Stage:','')
				current_loop_rider = rider
				current_loop_stage = stage
		
		# Check for DSS reset
		if re.search("Reset by DSS", lines[index]):
			print(f"Loop {loop_counter}: DSS Reset detected")
			# Output all current values before reset
			if dss_found:
				print(f"Loop {loop_counter} - Current values before DSS reset:")
				print(f"  WP Open: {show}, WP Skipped: {skip}, WP Clear: {clear}, WP Total: {total}")
				print(f"  Penalties - WP: {penalty_wp}Min, FN: {penalty_fn}Min, Speed: {penalty_speed}Min")
				print(f"  DSS Time: {dss_tod}")
			
			# Reset all stage times and penalties
			clear = 0
			show = 0
			skip = 0
			total = 0 
			penalty_speed = 0
			penalty_wp = 0
			penalty_fn = 0
			chk_index = 0
			last_wp = ""
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
			dss_set = False
		
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
		if re.search("^FN", lines[index]) and re.search("Min", lines[index]):
			#print(lines[index])
			try:
				# Handle different FN formats
				line = lines[index].strip()
				
				# Format 1: FN=6Min (equals sign format)
				if "=" in line:
					# Extract number between = and Min
					match = re.search(r'FN=(\d+)Min', line)
					if match:
						penalty_fn += int(match.group(1))
					else:
						print(f"Warning: Could not parse FN penalty from line '{line}', skipping")
				
				# Format 2: FN61 LatePenalty 0 Min 12:19:14 (space-separated format)
				else:
					temp = line.split(" ")
					if len(temp) >= 3:
						# Look for the numeric value in the line
						for i, item in enumerate(temp):
							if item.replace("Min","").isdigit():
								penalty_fn += int(item.replace("Min",""))
								break
						else:
							# If no numeric value found, try position 2 as fallback
							if len(temp) > 2:
								fn_value = temp[2].replace("Min","")
								penalty_fn += int(fn_value)
					else:
						print(f"Warning: Not enough items in FN line '{line}', skipping")
						
			except (ValueError, IndexError):
				# If conversion fails or index doesn't exist, skip this penalty
				print(f"Warning: Could not parse FN penalty from line '{lines[index]}', skipping")
			
		# Look for time points
		# Note: Removed break on "End:" since multi-loop files have "End:" at the end of each loop
		# if re.search("^End:", lines[index]) :
		# 	print("End Stage Found.")
		# 	break
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
			dss_set = False
		# Old logic for # lines - REMOVED - now handled in the new loop detection logic above
		if re.search("^Start", lines[index]):
			temp = lines[index].split(" ")
			print(lines[index])
			if len(temp) >= 2 and dss_set == False:
				print(temp[2])
				#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
				#time_start = get_time (lines[index])
				time_start = parse_time_with_extended_hours(temp[2])
				dss_tod = str(temp[2])
				dss_found = True
		if re.search("^Reset", lines[index]):
			temp = lines[index].split(" ")
			print (lines[index])
			#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
			#time_start = get_time (lines[index])
			#time_start = datetime.strptime(get_time (lines[index]), '%H:%M:%S')
			#dss_tod = str(get_time(lines[index]))
			
			if len(temp) >= 4:
				print(temp[3])
				#output_text += "DSS:\t" + get_time(lines[index]) + "\n"
				#time_start = get_time (lines[index])
				time_start = parse_time_with_extended_hours(temp[3])
				dss_tod = str(temp[3])
				dss_set = True
				dss_found = True
		if re.search("^CKP", lines[index]):
			print (lines[index])
			time_checkpoint = parse_time_with_extended_hours(get_time (lines[index]))
			
			# Ensure time_start is valid before calculation
			if time_start is None:
				time_start = datetime.strptime("00:00:00", '%H:%M:%S')  # Default start time
			
			time_delta = time_checkpoint - time_start
			time_change = timedelta(minutes=(penalty_fn + penalty_wp + penalty_speed)) 
			time_adjust = (time_checkpoint - time_start) + time_change
			#output_text +=  "CKP:\t" + get_time(lines[index]) + "\t\t" + format_timedelta(time_delta) + "\t\t" + format_timedelta(time_adjust) + "\n"
			
			chk_tod.append(str(get_time(lines[index])))
			
			tmp_str = format_timedelta(time_delta)
			chk_time.append(tmp_str)
			
			tmp_str = format_timedelta(time_adjust)
			chk_adj.append(tmp_str)
			
			chk_note.append("FN:" + str(penalty_fn) + " WP:" + str(penalty_wp) + " SZ:" + str(penalty_speed))
			
		if re.search("^FSS", lines[index]):
			print (lines[index])
			time_end = parse_time_with_extended_hours(get_time (lines[index]))
			
			# Ensure time_start is valid before calculation
			if time_start is None:
				time_start = datetime.strptime("00:00:00", '%H:%M:%S')  # Default start time
			
			time_delta = time_end - time_start
			time_change = timedelta(minutes=(penalty_fn + penalty_wp + penalty_speed)) 
			time_adjust = (time_end - time_start) + time_change
			#print("FSS:\t" + get_time(lines[index]) + "\t\t" +  format_timedelta(time_delta) + "\t\t" +  format_timedelta(time_adjust) + "\n")
			#print( "Time Start: " + str(time_start))
			#print( "Time End: " + str(time_end))
			#print( "Time Adjust: " + format_timedelta(time_adjust))
			
			fss_tod = str(get_time(lines[index]))
			fss_time = format_timedelta(time_delta)
			fss_adj = format_timedelta(time_adjust)
			fss_note = "FN:" + str(penalty_fn) + " WP:" + str(penalty_wp) + " SZ:" + str(penalty_speed)
			

	
	# Add the last loop data if it exists
	if dss_found and (rider != "" or stage != ""):
		loop_data = {
			'loop_counter': loop_counter,
			'rider': rider,
			'stage': stage,
			'clear': clear,
			'show': show,
			'skip': skip,
			'total': total,
			'penalty_speed': penalty_speed,
			'penalty_wp': penalty_wp,
			'penalty_fn': penalty_fn,
			'dss_tod': dss_tod,
			'chk_tod': chk_tod.copy(),
			'chk_time': chk_time.copy(),
			'chk_adj': chk_adj.copy(),
			'chk_note': chk_note.copy(),
			'fss_tod': fss_tod,
			'fss_time': fss_time,
			'fss_adj': fss_adj,
			'fss_note': fss_note,
			'eos_tod': eos_tod,
			'eos_time': eos_time,
			'eos_adj': eos_adj,
			'eos_note': eos_note
		}
		all_loops_data.append(loop_data)
	
	# Process all loops and generate output
	for loop_data in all_loops_data:
		output_text += f"=== LOOP {loop_data['loop_counter']} ===\n"
		output_text += "WP Open: " + str(loop_data['show']) + "\n"
		output_text += "WP Skipped: " + str(loop_data['skip']) + "\n"
		output_text += "WP Clear: " + str(loop_data['clear']) + "\n"
		output_text += "WP Total: " + str(loop_data['total']) + "\n"
		output_text += "WP Penalty: " + str(loop_data['penalty_wp']) + "Min" + "\n"
		output_text += "FN Penalty: " + str(loop_data['penalty_fn']) + "Min" + "\n"
		output_text += "Speed Penalty: " + str(loop_data['penalty_speed']) + "Min" + "\n"
		output_text += "\nTotal Penalty: " + str(loop_data['penalty_fn'] + loop_data['penalty_wp'] + loop_data['penalty_speed']) + "Min" + "\n\n"
		
		# Calculate EOS time for this loop
		time_change = timedelta(minutes=(loop_data['penalty_fn'] + loop_data['penalty_wp'] + loop_data['penalty_speed'])) 
		
		# Ensure both time_start and time_end are valid datetime objects
		if loop_data['dss_tod']:
			time_start = parse_time_with_extended_hours(loop_data['dss_tod'])
		else:
			time_start = datetime.strptime("00:00:00", '%H:%M:%S')  # Default start time
		
		if loop_data['fss_tod']:
			time_end = parse_time_with_extended_hours(loop_data['fss_tod'])
		else:
			time_end = time_start  # Fallback to start time if no FSS found
		
		time_adjust = (time_end - time_start) + time_change
		
		loop_data['eos_tod'] = loop_data['fss_tod']
		loop_data['eos_time'] = loop_data['fss_time']
		loop_data['eos_adj'] = format_timedelta(time_adjust)
		loop_data['eos_note'] = "FN:" + str(loop_data['penalty_fn']) + " WP:" + str(loop_data['penalty_wp']) + " SZ:" + str(loop_data['penalty_speed'])
	
	# Use the last loop data for GUI display (or first if only one loop)
	display_loop = all_loops_data[-1] if all_loops_data else {
		'loop_counter': 0,
		'rider': '',
		'stage': '',
		'dss_tod': '',
		'chk_tod': [],
		'chk_time': [],
		'chk_adj': [],
		'chk_note': [],
		'fss_tod': '',
		'fss_time': '',
		'fss_adj': '',
		'fss_note': '',
		'eos_tod': '',
		'eos_time': '',
		'eos_adj': '',
		'eos_note': ''
	}
	
	if not batch_mode:
		ent_rider.set( display_loop['rider'] )
		ent_stage.set( display_loop['stage'] )
		
		r1_tod.set( display_loop['dss_tod'] )
		r1_loop.set( str(display_loop['loop_counter']) )
		
		# Clear CKP rows
		r2_tod.set( "")
		r2_note.set( "" )
		r2_loop.set( "" )
		r2_time.set( "" )
		r2_adj.set( "" )
		r3_tod.set( "")
		r3_note.set( "" )
		r3_loop.set( "" )
		r3_time.set( "" )
		r3_adj.set( "" )
		r4_tod.set( "")
		r4_note.set( "" )
		r4_loop.set( "" )
		r4_time.set( "" )
		r4_adj.set( "" )
		r5_tod.set( "")
		r5_note.set( "" )
		r5_loop.set( "" )
		r5_time.set( "" )
		r5_adj.set( "" )
		r6_tod.set( "")
		r6_note.set( "" )
		r6_loop.set( "" )
		r6_time.set( "" )
		r6_adj.set( "" )
				
				
		for index in range(1, len(display_loop['chk_tod'])):
			#output_text += chk_tod[index] + "\tCKP" + str(index) + ", " + chk_note[index] + "\t" + chk_time[index] + "\t" + chk_adj[index] + "\n"
			if(index == 1):
				r2_tod.set( display_loop['chk_tod'][index] )
				r2_note.set( "CKP" + str(index) + ", " + display_loop['chk_note'][index] )
				r2_loop.set( str(display_loop['loop_counter']) )
				r2_time.set( display_loop['chk_time'][index] )
				r2_adj.set( display_loop['chk_adj'][index] )
			if(index == 2):
				r3_tod.set( display_loop['chk_tod'][index] )
				r3_note.set( "CKP" + str(index) + ", " + display_loop['chk_note'][index] )
				r3_loop.set( str(display_loop['loop_counter']) )
				r3_time.set( display_loop['chk_time'][index] )
				r3_adj.set( display_loop['chk_adj'][index] )
			if(index == 3):
				r4_tod.set( display_loop['chk_tod'][index] )
				r4_note.set( "CKP" + str(index) + ", " + display_loop['chk_note'][index] )
				r4_loop.set( str(display_loop['loop_counter']) )
				r4_time.set( display_loop['chk_time'][index] )
				r4_adj.set( display_loop['chk_adj'][index] )
			if(index == 4):
				r5_tod.set( display_loop['chk_tod'][index] )
				r5_note.set( "CKP" + str(index) + ", " + display_loop['chk_note'][index] )
				r5_loop.set( str(display_loop['loop_counter']) )
				r5_time.set( display_loop['chk_time'][index] )
				r5_adj.set( display_loop['chk_adj'][index] )
			if(index == 5):
				r6_tod.set( display_loop['chk_tod'][index] )
				r6_note.set( "CKP" + str(index) + ", " + display_loop['chk_note'][index] )
				r6_loop.set( str(display_loop['loop_counter']) )
				r6_time.set( display_loop['chk_time'][index] )
				r6_adj.set( display_loop['chk_adj'][index] )
		r7_tod.set( display_loop['fss_tod'] )
		r7_note.set( "FSS, " + display_loop['fss_note'] )
		r7_loop.set( str(display_loop['loop_counter']) )
		r7_time.set( display_loop['fss_time'] )
		r7_adj.set( display_loop['fss_adj'] )
		
		r8_tod.set( display_loop['eos_tod'] )
		r8_note.set( "EOS, " + display_loop['eos_note'] )
		r8_loop.set( str(display_loop['loop_counter']) )
		r8_time.set( display_loop['eos_time'] )
		r8_adj.set( display_loop['eos_adj'] )
			
	#output_text += fss_tod + "\tFSS, " + fss_note + "\t" + fss_time + "\t" + fss_adj + "\n"
	#output_text += eos_tod + "\tEOS, " + eos_note + "\t" + eos_time + "\t" + eos_adj + "\n"
	
	# Log to CSV for each loop
	for loop_data in all_loops_data:
		if loop_data['dss_tod']:  # Only log if DSS was found
			log_note = loop_data['eos_note'].replace(",","_")
			log_note = log_note.replace(" ","")
			log_note = "EOS_" + log_note
			
			log_text = "" 
			if (os.path.isfile("DAT_Log.csv") == False): # Add header for new files only
				log_text += "File_Path,Racer,Stage,Loop,Note,CKP1,CKP2,CKP3,CKP4,CKP5,FSS,EOS\n"
				
			log_text += file_path + "," + loop_data['rider'] + "," + loop_data['stage'] + "," + str(loop_data['loop_counter']) + "," + log_note + ","
			if(len(loop_data['chk_tod']) >= 1):
				log_text += loop_data['chk_adj'][0]
			log_text += ","
			if(len(loop_data['chk_tod']) >= 2):
				log_text += loop_data['chk_adj'][1]
			log_text += ","
			if(len(loop_data['chk_tod']) >= 3):
				log_text += loop_data['chk_adj'][2]
			log_text += ","
			if(len(loop_data['chk_tod']) >= 4):
				log_text += loop_data['chk_adj'][3]
			log_text += ","
			if(len(loop_data['chk_tod']) >= 5):
				log_text += loop_data['chk_adj'][4]
			log_text += ","
			log_text += loop_data['fss_adj'] + "," + loop_data['eos_adj'] + "\n"
			
			f = open("DAT_Log.csv", "a")
			f.write(log_text)
			f.close()
			
			# Generate detailed CSV log with one row per section
			details_log_text = ""
			if (os.path.isfile("DAT_Details_Log.csv") == False): # Add header for new files only
				details_log_text += "File_Path,Racer,Stage,Loop,Section,TOD,NOTE,TIME,ADJUSTED\n"
			
			# DSS Section
			details_log_text += f"{file_path},{loop_data['rider']},{loop_data['stage']},{loop_data['loop_counter']},DSS,{loop_data['dss_tod']},Start Time,00:00:00,00:00:00\n"
			
			# CKP Sections
			for index in range(1, len(loop_data['chk_tod'])):
				section_name = f"CKP{index}"
				details_log_text += f"{file_path},{loop_data['rider']},{loop_data['stage']},{loop_data['loop_counter']},{section_name},{loop_data['chk_tod'][index]},{loop_data['chk_note'][index]},{loop_data['chk_time'][index]},{loop_data['chk_adj'][index]}\n"
			
			# FSS Section
			details_log_text += f"{file_path},{loop_data['rider']},{loop_data['stage']},{loop_data['loop_counter']},FSS,{loop_data['fss_tod']},{loop_data['fss_note']},{loop_data['fss_time']},{loop_data['fss_adj']}\n"
			
			# EOS Section
			details_log_text += f"{file_path},{loop_data['rider']},{loop_data['stage']},{loop_data['loop_counter']},EOS,{loop_data['eos_tod']},{loop_data['eos_note']},{loop_data['eos_time']},{loop_data['eos_adj']}\n"
			
			f = open("DAT_Details_Log.csv", "a")
			f.write(details_log_text)
			f.close()
	
	if batch_mode:
		# Add to batch output
		loop_count = len(all_loops_data)
		file_text.insert(tk.END, f"Processed: {os.path.basename(file_path)} - {loop_count} loop(s) found\n")
		for loop_data in all_loops_data:
			file_text.insert(tk.END, f"  Loop {loop_data['loop_counter']}: Rider: {loop_data['rider']}, Stage: {loop_data['stage']}\n")
		file_text.see(tk.END)  # Auto-scroll to bottom
	else:
		file_text.delete('1.0', tk.END)
		file_text.insert(tk.END, output_text)
			    


#root = tk.Tk()
root = tk.Tk(className=' rc dat reader ')
#root = tk.Tk(screenName=None,  baseName=None,  className='TEST',  useTk=1)
root.title("RC DAT Reader - Batch Processor")
root.iconphoto(False, PhotoImage(file='RC.png'))
#root.iconbitmap(r'./RC.ico')
#root = Tk(className='Testing')

# Batch processing controls
batch_frame = Frame(root)
batch_frame.grid(column=0, row=0, padx=5, pady=5, columnspan=5, sticky="ew")

# Directory selection
dir_label = Label(batch_frame, text="Directory:")
dir_label.grid(column=0, row=0, padx=5, pady=5, sticky="w")

directory_var = StringVar()
dir_entry = Entry(batch_frame, textvariable=directory_var, width=40)
dir_entry.grid(column=1, row=0, padx=5, pady=5, sticky="ew")

dir_button = Button(batch_frame, text="Browse", command=select_directory)
dir_button.grid(column=2, row=0, padx=5, pady=5)

# Filename pattern
pattern_label = Label(batch_frame, text="File Pattern:")
pattern_label.grid(column=0, row=1, padx=5, pady=5, sticky="w")

filename_pattern_var = StringVar(value="*.DAT")
pattern_entry = Entry(batch_frame, textvariable=filename_pattern_var, width=40)
pattern_entry.grid(column=1, row=1, padx=5, pady=5, sticky="ew")

# Process button
process_button = tk.Button(batch_frame, text="Process Batch", command=process_batch, bg="lightgreen")
process_button.grid(column=2, row=1, padx=5, pady=5)

# Status label
status_label = Label(batch_frame, text="Ready to process files")
status_label.grid(column=0, row=2, padx=5, pady=5, columnspan=3, sticky="w")

# Configure grid weights for batch_frame
batch_frame.columnconfigure(1, weight=1)

# Divider line
divider_frame = tk.Frame(root, height=2, bg="gray")
divider_frame.grid(column=0, row=1, padx=5, pady=10, columnspan=5, sticky="ew")

# Single file processing section
single_frame = Frame(root)
single_frame.grid(column=0, row=2, padx=5, pady=5, columnspan=5, sticky="ew")

# Single file processing controls
single_label = Label(single_frame, text="Single File Processing", font=("Arial", 12, "bold"))
single_label.grid(column=0, row=0, padx=5, pady=5, sticky="w")

# Single file open button (moved to right side)
open_button = tk.Button(single_frame, text="Open Single File", command=open_single_file, bg="lightblue")
open_button.grid(column=4, row=0, padx=5, pady=5, sticky="e")

selected_file_label = tk.Label(single_frame, text="No file selected")
selected_file_label.grid(column=0, row=1, padx=5, pady=5, sticky="w")

# Rider/Stage
lbl1 = Label(single_frame, text="Rider")
lbl1.grid(column=3, row=2, padx=5, pady=5)

ent_rider = StringVar()
ent1 = Entry(single_frame, textvariable=ent_rider, width=15)
ent1.grid(column=4, row=2, padx=5, pady=5)

lbl2 = Label(single_frame, text="Stage")
lbl2.grid(column=3, row=3, padx=5, pady=5)

ent_stage = StringVar()
ent2 = Entry(single_frame, textvariable=ent_stage, width=15)
ent2.grid(column=4, row=3, padx=5, pady=5)

# Space
lbl3 = Label(root, text=" ")
lbl3.grid(column=0, row=3, padx=5, pady=5)
lbl4 = Label(root, text=" ")
lbl4.grid(column=0, row=4, padx=5, pady=5)

# Table Header
th1 = Label(root, text="DESCRIPTION")
th1.grid(column=0, row=5, padx=5, pady=5)
th2 = Label(root, text="TOD")
th2.grid(column=1, row=5, padx=5, pady=5)
th3 = Label(root, text="NOTE")
th3.grid(column=2, row=5, padx=5, pady=5)
th4 = Label(root, text="LOOP")
th4.grid(column=3, row=5, padx=5, pady=5)
th5 = Label(root, text="TIME")
th5.grid(column=4, row=5, padx=5, pady=5)
th6 = Label(root, text="ADJUSTED")
th6.grid(column=5, row=5, padx=5, pady=5)

# Row 1
r1_des = StringVar()
td11 = Entry(root, textvariable=r1_des, width=15)
r1_des.set( "DSS" )
td11.grid(column=0, row=6, padx=5, pady=5)

r1_tod = StringVar()
td12 = Entry(root, textvariable=r1_tod, width=15)
td12.grid(column=1, row=6, padx=5, pady=5)

r1_note = StringVar()
td13 = Entry(root, textvariable=r1_note, width=30)
td13.grid(column=2, row=6, padx=5, pady=5)

r1_loop = StringVar()
td14 = Entry(root, textvariable=r1_loop, width=10)
td14.grid(column=3, row=6, padx=5, pady=5)

r1_time = StringVar()
td15 = Entry(root, textvariable=r1_time, width=15)
td15.grid(column=4, row=6, padx=5, pady=5)

r1_adj = StringVar()
td16 = Entry(root, textvariable=r1_adj, width=15)
td16.grid(column=5, row=6, padx=5, pady=5)

# Row 2
r2_des = StringVar()
td21 = Entry(root, textvariable=r2_des, width=15)
r2_des.set( "CPK1" )
td21.grid(column=0, row=7, padx=5, pady=5)

r2_tod = StringVar()
td22 = Entry(root, textvariable=r2_tod, width=15)
td22.grid(column=1, row=7, padx=5, pady=5)

r2_note = StringVar()
td23 = Entry(root, textvariable=r2_note, width=30)
td23.grid(column=2, row=7, padx=5, pady=5)

r2_loop = StringVar()
td24 = Entry(root, textvariable=r2_loop, width=10)
td24.grid(column=3, row=7, padx=5, pady=5)

r2_time = StringVar()
td25 = Entry(root, textvariable=r2_time, width=15)
td25.grid(column=4, row=7, padx=5, pady=5)

r2_adj = StringVar()
td26 = Entry(root, textvariable=r2_adj, width=15)
td26.grid(column=5, row=7, padx=5, pady=5)

# Row 3
r3_des = StringVar()
td31 = Entry(root, textvariable=r3_des, width=15)
r3_des.set( "CKP2" )
td31.grid(column=0, row=8, padx=5, pady=5)

r3_tod = StringVar()
td32 = Entry(root, textvariable=r3_tod, width=15)
td32.grid(column=1, row=8, padx=5, pady=5)

r3_note = StringVar()
td33 = Entry(root, textvariable=r3_note, width=30)
td33.grid(column=2, row=8, padx=5, pady=5)

r3_loop = StringVar()
td34 = Entry(root, textvariable=r3_loop, width=10)
td34.grid(column=3, row=8, padx=5, pady=5)

r3_time = StringVar()
td35 = Entry(root, textvariable=r3_time, width=15)
td35.grid(column=4, row=8, padx=5, pady=5)

r3_adj = StringVar()
td36 = Entry(root, textvariable=r3_adj, width=15)
td36.grid(column=5, row=8, padx=5, pady=5)

# Row 4
r4_des = StringVar()
td41 = Entry(root, textvariable=r4_des, width=15)
r4_des.set( "CKP3" )
td41.grid(column=0, row=9, padx=5, pady=5)

r4_tod = StringVar()
td42 = Entry(root, textvariable=r4_tod, width=15)
td42.grid(column=1, row=9, padx=5, pady=5)

r4_note = StringVar()
td43 = Entry(root, textvariable=r4_note, width=30)
td43.grid(column=2, row=9, padx=5, pady=5)

r4_loop = StringVar()
td44 = Entry(root, textvariable=r4_loop, width=10)
td44.grid(column=3, row=9, padx=5, pady=5)

r4_time = StringVar()
td45 = Entry(root, textvariable=r4_time, width=15)
td45.grid(column=4, row=9, padx=5, pady=5)

r4_adj = StringVar()
td46 = Entry(root, textvariable=r4_adj, width=15)
td46.grid(column=5, row=9, padx=5, pady=5)

# Row 5
r5_des = StringVar()
td51 = Entry(root, textvariable=r5_des, width=15)
r5_des.set( "CKP4" )
td51.grid(column=0, row=10, padx=5, pady=5)

r5_tod = StringVar()
td52 = Entry(root, textvariable=r5_tod, width=15)
td52.grid(column=1, row=10, padx=5, pady=5)

r5_note = StringVar()
td53 = Entry(root, textvariable=r5_note, width=30)
td53.grid(column=2, row=10, padx=5, pady=5)

r5_loop = StringVar()
td54 = Entry(root, textvariable=r5_loop, width=10)
td54.grid(column=3, row=10, padx=5, pady=5)

r5_time = StringVar()
td55 = Entry(root, textvariable=r5_time, width=15)
td55.grid(column=4, row=10, padx=5, pady=5)

r5_adj = StringVar()
td56 = Entry(root, textvariable=r5_adj, width=15)
td56.grid(column=5, row=10, padx=5, pady=5)

# Row 6
r6_des = StringVar()
td61 = Entry(root, textvariable=r6_des, width=15)
r6_des.set( "CKP5" )
td61.grid(column=0, row=11, padx=5, pady=5)

r6_tod = StringVar()
td62 = Entry(root, textvariable=r6_tod, width=15)
td62.grid(column=1, row=11, padx=5, pady=5)

r6_note = StringVar()
td63 = Entry(root, textvariable=r6_note, width=30)
td63.grid(column=2, row=11, padx=5, pady=5)

r6_loop = StringVar()
td64 = Entry(root, textvariable=r6_loop, width=10)
td64.grid(column=3, row=11, padx=5, pady=5)

r6_time = StringVar()
td65 = Entry(root, textvariable=r6_time, width=15)
td65.grid(column=4, row=11, padx=5, pady=5)

r6_adj = StringVar()
td66 = Entry(root, textvariable=r6_adj, width=15)
td66.grid(column=5, row=11, padx=5, pady=5)

# Row 7
r7_des = StringVar()
td71 = Entry(root, textvariable=r7_des, width=15)
r7_des.set( "FSS" )
td71.grid(column=0, row=12, padx=5, pady=5)

r7_tod = StringVar()
td72 = Entry(root, textvariable=r7_tod, width=15)
td72.grid(column=1, row=12, padx=5, pady=5)

r7_note = StringVar()
td73 = Entry(root, textvariable=r7_note, width=30)
td73.grid(column=2, row=12, padx=5, pady=5)

r7_loop = StringVar()
td74 = Entry(root, textvariable=r7_loop, width=10)
td74.grid(column=3, row=12, padx=5, pady=5)

r7_time = StringVar()
td75 = Entry(root, textvariable=r7_time, width=15)
td75.grid(column=4, row=12, padx=5, pady=5)

r7_adj = StringVar()
td76 = Entry(root, textvariable=r7_adj, width=15)
td76.grid(column=5, row=12, padx=5, pady=5)

# Row 8
r8_des = StringVar()
td81 = Entry(root, textvariable=r8_des, width=15)
r8_des.set( "EOS" )
td81.grid(column=0, row=13, padx=5, pady=5)

r8_tod = StringVar()
td82 = Entry(root, textvariable=r8_tod, width=15)
td82.grid(column=1, row=13, padx=5, pady=5)

r8_note = StringVar()
td83 = Entry(root, textvariable=r8_note, width=30)
td83.grid(column=2, row=13, padx=5, pady=5)

r8_loop = StringVar()
td84 = Entry(root, textvariable=r8_loop, width=10)
td84.grid(column=3, row=13, padx=5, pady=5)

r8_time = StringVar()
td85 = Entry(root, textvariable=r8_time, width=15)
td85.grid(column=4, row=13, padx=5, pady=5)

r8_adj = StringVar()
td86 = Entry(root, textvariable=r8_adj, width=15)
td86.grid(column=5, row=13, padx=5, pady=5)


file_text = tk.Text(root, wrap=tk.WORD, height=10, width=95)
file_text.grid(column=0, row=14, padx=5, pady=5, columnspan=6)

root.mainloop()
