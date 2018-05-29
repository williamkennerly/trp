"""
Single-Point_Energy_Analyzer_2.9

This python script creates a text file containing the energy values for a Gaussian single-point energy calculation that
can be read in Excel. The script reads all of the .out or .log files in a directory at once.

OUTPUT (in order)

Method
Basis set
Root number
Number of Basis Functions
Job CPU time
Ground-state energy in Hartrees
Ground-state energy in eV
Excitation energies in eV for n states
Absolute Excitation energies in eV for n states
Oscillator Strength for n states

My email: jgerard@skidmore.edu

I adapted much of this script from Kristine Vorwerk's TDDFT_Results_Analyzer_2.0 and Scan_Output_Analyzer_1.0.

Updates:

3.0 fixes all issues 2.9 had since changing to the new computers.

Justin Gerard
September 26 2016
"""

# -----IMPORT-----#

import re
import glob

# -----REGULAR EXPRESSIONS-----#

# gets the ground state energies from the output file in A.U. (hartrees)
ground_stateRegex = re.compile(r'''
    SCF\sDone:      #beginning of the SCF Done: line
    \s*             #whitespace before the method name
    \S*             #E followed by the method in parentheses
    \s*             #whitespace after the method name
    =               #equal between the method an the energy
    \s*             #whitespace before the energy
    (-*\d*\.\d*)    #GROUP 1: ground state energy in A.U. (Hartrees)
    ''', re.VERBOSE)

# gets the excited state energies in eV and corresponding oscilator strengths in nm from the output file
excited_stateRegex = re.compile(r'''
    Excited\sState  #excited state line
    \s*             #whitespace
    (\d*)           #GROUP 1: excited state number
    :               #colon after the number
    \s*             #whitespace
    \S*             #type of state, usually singlet-A
    \s*             #whitespace
    (\d*\.*\d*)     #GROUP 2: energy in electron-volts
    \s*             #whitespace
    eV              #units
    \s*             #whitespace
    (\d*\.*\d*)     #GROUP 3: energy in nanometers
    \s*             #whitespace
    nm              #units
    \s*             #whitespace
    f=              #beginning of the oscialtor strength
    (\d*\.*\d*)     #GROUP 4: oscilator strength
''', re.VERBOSE)

# gets the job time from the output file
timeRegex = re.compile(r'''
    Job\scpu\stime: #job time line
    \s*             #whitespace
    (\d*)           #GROUP 1: number of days
    \s*             #whitespace
    \S*             #word (days)
    \s*             #whitespace
    (\d*)           #GROUP 2: number of hours
    \s*             #whitespace
    \S*             #word (hours)
    \s*             #whitespace
    (\d*)           #GROUP 3: number of minutes
    \s*             #whitespace
    \S*             #word (minutes)
    \s*             #whitespace
    (\d*\.*\d*)     #GROUP 4: number of seconds
''', re.VERBOSE)

# gets the nstates from a route line
nstatesRegex = re.compile(r'''
    nstates=        #beginning of excited states
    (\d*)           #GROUP 1: nstates value
''', re.VERBOSE)

# gets the number of basis sets from the output file
nbasisRegex = re.compile(r'''
    NBasis=         #beginning of NBasis line
    \s*             #whitespace
    (\d*)           #GROUP 1: number of basis sets
''', re.VERBOSE)
    

#*********************************DEFINITIONS******************************

#finds the parameter line
#the parameter line is the first that begins with " #", so it searches for that line
def find_parameters(file_handle):
    file_handle.seek(0)
    for l in file_handle:
        if l.startswith(" #"):
            return l.rstrip()

#gets the folder location from the user
def get_folder_location():
    specify_folder = raw_input("Enter c to analyze the current folder, or s to specify a different folder: ")

    if specify_folder.lower()=="c":
        return ""
    elif specify_folder.lower()=="s":
        return raw_input("Enter the full folder path, including the trailing \: ")
    else:
        print "Invalid Input"
        get_folder_location()

def convertToeV(value_in_hartrees):
    """
    This function takes a value in hartrees and converts it to electron volts using the conversion factor from NIST.gov.
    Requires: "value_in_hartrees" -- float of the value to be converted to eV
    Returns: the eV value of the input
    """
    return value_in_hartrees*27.21138602
    

#**********************************BEGIN CODE******************************

#get a folder to search through
folder_location = get_folder_location()

#gets filepaths for everything in the specified folder ending with .LOG or .out
search_str_log = folder_location + "*.LOG"
search_str_out = folder_location + "*.out"

file_paths_log = glob.glob(search_str_log)
file_paths_out = glob.glob(search_str_out)

file_paths = file_paths_log + file_paths_out

#makes a new file for the results
results_location = folder_location + 'results.txt'
results = open(results_location, 'w')

#creates the list that will contain all the data in order
master_results = []

largest_nstates = 0

#loop through the files to get largest number of states
for file_name in file_paths:

    #open file to use in python
    current_file = open(file_name)
    #reads the file as a list of its lines of text
    content = current_file.readlines()

    #get the route line
    parameters=str(find_parameters(current_file))

    #find the number of states and set nstates var equal to it
    mo_nstates = nstatesRegex.search(parameters)
    if mo_nstates!=None:
        
        nstates=int(mo_nstates.group(1))

        #sets largest_nstates equal to nstates of the current file if it is larger than that of the previous file
        if nstates>largest_nstates:
            
            largest_nstates = nstates
        
    else:
        
        print "nstates not found in " + file_name   #gives name of file which did not have a number of states

    #close the file
    current_file.close()

#loop through the files again to get all the relevant results
for file_name in file_paths:

    #open file to use in python
    current_file = open(file_name)
    #reads the file as a list of its lines of text
    content = current_file.readlines()

    #get the route line
    parameters=str(find_parameters(current_file))

    #find the number of states and set nstates var equal to it
    #only runs the rest of the code in the loop if there exists an number of states for the current_file
    mo_nstates = nstatesRegex.search(parameters)
    if mo_nstates!=None:

        #get the method and basis set of the calculation
        #(using sneaky string slicing)
        slash_pos = parameters.find("/")
        space_pos = parameters.find(" ",slash_pos)
        close_paren_pos = parameters.find(")")
        if "geom=connectivity" in parameters:
            basis = parameters[slash_pos+1:space_pos]
        else:
            basis = parameters[slash_pos+1:]

        method = parameters[close_paren_pos+2:slash_pos]

        #append the method and basis to the master_results list
        master_results.append(method)
        master_results.append(basis)

        #append nstates to master_results list
        nstates=int(mo_nstates.group(1))
        master_results.append(nstates)

        #check length of master_results list
        check_len = len(master_results)

        #loop through the lines of the file to get the number of basis sets and the job time
        #append nbasis and time to master_results list
        for line in content:

            mo_nbasis = nbasisRegex.search(line)
            if mo_nbasis!=None:

                nbasis=int(mo_nbasis.group(1))
                if nbasis!=master_results[len(master_results)-1]:
                    master_results.append(nbasis)
            
            mo_time = timeRegex.search(line)
            if mo_time!=None:

                days=float(mo_time.group(1))
                hours=float(mo_time.group(2))
                minutes=float(mo_time.group(3))
                seconds=float(mo_time.group(4))

                #converts the job time into minutes
                total_time_minutes=(days*24*60)+(hours*60)+minutes+(seconds/60)
                master_results.append(total_time_minutes)

        #if no time is found, the job time is appended as "_" to keep the order of the list
        if check_len==len(master_results):
            
            print "job time not found in " + file_name   #gives name of file which did not have a job time

        #initialize the lists to be used for the energy and osc strength values
        #(lists are initialized again as empty lists for each new file)
        EE_lst = []
        abs_EE_lst = []
        osc_lst = []

        #loop through the lines of the file to get all the energies and osc strengths for all states
        for line in content:
        
            mo_ground_state = ground_stateRegex.search(line)
            if mo_ground_state!=None:

                gs_hartrees=float(mo_ground_state.group(1))
                master_results.append(str(gs_hartrees))

                gs_eV=convertToeV(gs_hartrees)
                master_results.append(str(gs_eV))

            mo_excited_state = excited_stateRegex.search(line)
            if mo_excited_state!=None:

                excitation_energy=float(mo_excited_state.group(2))
                EE_lst.append(excitation_energy)
        
                absolute_energy=excitation_energy+gs_eV
                abs_EE_lst.append(absolute_energy)

                oscillator_strength=float(mo_excited_state.group(4))
                osc_lst.append(oscillator_strength)

        #append spaces for empty cells, if nstates of the current calculation is smaller than largest_nstates
        for x in xrange(nstates, largest_nstates):

            EE_lst.append(" ")
            abs_EE_lst.append(" ")
            osc_lst.append(" ")

        #append those values in order to the master_results
        master_results.extend(EE_lst+abs_EE_lst+osc_lst)
                        
    current_file.close()    #close the file

#initalize list that will contain the divided results
#this list will have a separate list for each set of data from each calculation (file)
divided_results = []

#sets var equal to length of the set of data for all calculations
data_set_length = 7+3*largest_nstates

#creates lists for each set of data for each calculation and appends them to divided_results
for x in xrange(0, len(master_results), 7+3*largest_nstates):
    divided_results.append(master_results[x:x+7+3*largest_nstates])

#creates a list which contains the divided_results list, sorted by method and then by basis set
sorted_mb_results = sorted(divided_results, key=lambda x: (x[0].lower(), x[1].lower()))

#write information to results file
for x in xrange(7+3*largest_nstates):
                        
    if x==0:
        results.write("Method:")
    if x==1:
        results.write("Basis Set:")
    if x==2:
        results.write("Number of States:")
    if x==3:
        results.write("Number of Basis Functions:")
    if x==4:
        results.write("Job CPU Time in Minutes:")
    if x==5:
        results.write("Ground State Energy in Hartrees:")
    if x==6:
        results.write("Ground State Energy in eV:")
    if x>6 and x<=6+largest_nstates:
        results.write("Excitation Energy for State %d:" % (x-6))
    if x>6+largest_nstates and x<=6+2*largest_nstates:
        results.write("Abs. Excitation Energy for State %d:" % (x-6-largest_nstates))
    if x>6+2*largest_nstates:
        results.write("Oscillator Strength for State %d:" % (x-6-2*largest_nstates))
    for lst in sorted_mb_results:
        results.write("\t" + str(lst[x]))
    results.write("\n")
    
#close results text output file
results.close()
