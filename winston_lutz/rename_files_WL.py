import os, shutil
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory

main_path = askdirectory(title='Select folder') #user select the directory of the images

#positions of gantry, col and couch ordered as the irradiation of the images
gantry = [0, 90, 180, 270, 0, 0, 0, 0] 
colimator = [0, 0, 0, 0, 90, 270, 0, 0]
couch =  [0, 0, 0, 0, 0, 0, 90, 270]

n = 0
for folderName, subfolders, filenames in os.walk(main_path):
	#print('The current folder is ' + folderName)

	for subfolder in subfolders:
		#print('SUBFOLDER OF ' + folderName + ': ' + subfolder)
		x = 0 #empty code
		
	for filename in filenames:
		#print('FILE INSIDE ' + folderName + ': '+ filename)
		if filename != "DICOMDIR":

			file_path = folderName + '/' + filename

			#move the file to the main path	
			shutil.move(file_path, main_path + "/" + "gantry" + str(gantry[n]) + "coll" + str(colimator[n]) + "couch" + str(couch[n]) + ".dcm")

			n = n + 1

