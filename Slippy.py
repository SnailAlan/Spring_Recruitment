## Slippy Program
#!/usr/bin/env python3
import sys, re
import os.path

##################################################
## pre-processing
##################################################
length = len(sys.argv)

if length == 1:
    print("usage: slippy [-i] [-n] [-f <script-file> | <sed-command>] [<files>...]", file = sys.stderr)
    sys.exit(1)

## a bunch of initialized variables to read the command line inputs
Line_box = []; input_files = []
command_file_name = None; slippy_option = None
_f_command = None; _i_command = None
command_list = None
##### -----     -----   -----   -----   -----   ----- #####

## read the command line inputs
if length >= 2:
    for _input in sys.argv[1:]:
        if os.path.exists(_input):
            if '.txt' in _input:
                input_files.append(_input)
            else:
                command_file_name = _input
        elif _input == '-n':
            slippy_option = _input
        elif _input == '-f':
            _f_command = _input
        elif _input == '-i':
            _i_command = _input
        else:
            command_list = _input

## concatenate all inputs from files
if input_files:
    for File in input_files:
        file = open(File, 'r')
        file_lines = file.readlines()
        file.close()
        Line_box += file_lines

## read append, insert and change command
special_command = None; special_content = None
if command_list:
    if re.match(r'.+a ', command_list):
        special_command = 'append'
        special_content = re.sub(r'.+a ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'a .+', '', command_list, count = 1)
        command_list = command_list + '@'
    elif re.match(r'a .+', command_list):
        special_command = 'append'
        special_content = re.sub(r'a ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'a .+', '', command_list, count = 1)
        command_list = command_list + '@'
    elif re.match(r'.+i ', command_list):
        special_command = 'insert'
        special_content = re.sub(r'.+i ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'i .+', '', command_list, count = 1)
        command_list = command_list + '@'
    elif re.match(r'i .+', command_list):
        special_command = 'insert'
        special_content = re.sub(r'i ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'i .+', '', command_list, count = 1)
        command_list = command_list + '@'
    elif re.match(r'.+c ', command_list):
        special_command = 'change'
        special_content = re.sub(r'.+c ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'c .+', '', command_list, count = 1)
        command_list = command_list + '@'
    elif re.match(r'c .+', command_list):
        special_command = 'change'
        special_content = re.sub(r'c ', '', command_list, count = 1)
        special_content = special_content + '\n'
        command_list = re.sub(r'c .+', '', command_list, count = 1)
        command_list = command_list + '@'
##### -----     -----   -----   -----   ----- #####

## -f command line option
if _f_command == '-f':
    if command_file_name == None:
        print("usage: slippy [-i] [-n] [-f <script-file> | <sed-command>] [<files>...]", file = sys.stderr)
        sys.exit(1)

    file = open(command_file_name, 'r')
    command_list = file.readlines()
    i = 0
    while i < len(command_list):
        command_list[i] = re.sub(r'\n', '', command_list[i])
        command_list[i] = re.sub(r' ', '', command_list[i])
        command_list[i] = re.sub(r'#.*', '', command_list[i])
        i += 1

    command_argcs = []
    j = 0
    while j < len(command_list):
        if re.search(r';', command_list[j]):
            sub_command_list = re.split(r';', command_list[j])
            for command in sub_command_list:
                command_argcs.append(command)
        else:
            command_argcs.append(command_list[j])
        j += 1
    file.close()
    output = [[] for i in range(len(command_argcs))]

## command from sys.argv
else:
    command_line = re.sub(r' ', '', command_list)
    command_line = re.sub(r'#.*', '', command_line)
    command_line = re.sub(r'\n', ';', command_line)

    ## store all commands into the 'command_argcs' list
    if re.search(r';', command_line):
        command_line.strip()
        command_argcs = re.split(r';', command_line)
        output = [[] for i in range(len(command_argcs))]
    else:
        command_argcs = [command_line]
        output = [[]]

##################################################
## self-defined functions
##################################################
## read the line address in digital_numbers (eg: 3 in '3q')
def read_line_address(command_argcs = None, th_command = 0):
    line_address = 0
    if re.match(r'-?[0-9]+[qpds@]', command_argcs[th_command]):
        line_address = int(re.sub(r'[qpds@].*', '' , command_argcs[th_command]))
        if line_address == 0:
            print("slippy: command line: invalid command", file = sys.stderr)
            sys.exit(1)
        elif line_address < 0:
            print("usage: slippy [-i] [-n] [-f <script-file> | <sed-command>] [<files>...]", file = sys.stderr)
            sys.exit(1)

    ## read '$' as the last line
    if re.match(r'\$[qpds@]', command_argcs[th_command]): line_address = -1
    return line_address

## read the line address in regex pattern (eg: .1 in '/.1/q')
def read_regex_pattern(command_argcs = None, th_command = 0):
    pattern = re.match(r'\/[^\/]+\/', command_argcs[th_command])
    if pattern:
        pattern = re.sub(r'\/', '', pattern.group())
    else:
        pattern = None
    return pattern

## read the line address in "start, end" pattern (eg: [1,2] in '1,2p')
def read_start_end(command_argcs = None, th_command = 0, delimit_char = '\/'):
    ## index 0: start, index 1: end
    start_end = [None, None]

    command = command_argcs[th_command][-1]
    if command in ['p', 'd', 'q', '@']:
        _line_address = command_argcs[th_command][0: -1]
        _line_address.strip()
        _line_address = re.split(r'\,', _line_address)
        if len(_line_address) == 2:
            start_end[0] = _line_address[0]
            start_end[1] = _line_address[1]

    elif re.match(r'.*s' + f'{delimit_char}', command_argcs[th_command]):
        _line_address = re.sub(r's' + f'{delimit_char}' + r'.+', '', command_argcs[th_command])
        _line_address = re.split(r'\,', _line_address)
        if len(_line_address) == 2:
            start_end[0] = _line_address[0]
            start_end[1] = _line_address[1]
    return start_end

## read the special delimit char for substitute command (eg: 'X' in 'sXaXbX')
def read_delimiter(command_argcs = None, th_command = 0):
    delimit_char = '\/'

    if command_argcs[th_command][-1] == 'g':
        if command_argcs[th_command][-2] == '?': delimit_char = "\\" + command_argcs[th_command][-2]
        else: delimit_char = command_argcs[th_command][-2]
    else:
        if command_argcs[th_command][-1] == '?': delimit_char = "\\" + command_argcs[th_command][-1]
        else: delimit_char = command_argcs[th_command][-1]
    return delimit_char

## execute q command
def slippy_quit(line_address = 0, pattern = None, line = None, th_line = 0, output = None, option = None):
    if option == '-n': sys.exit()

    ## single q-command
    if line_address == 0 and pattern is None:
        output.append(line)
        status = 'exit'
        return status

    ## line_address in regex pattern
    if pattern:
        output.append(line)
        if re.search(f'{pattern}', line):
            status = 'exit'
            return status

    ## line_address in digital numbers
    elif not pattern and line_address > 0:
        if line_address >= th_line:
            output.append(line)
        else:
            status = 'exit'
            return status

    ## '$' quit the last line
    if line_address == -1: output.append(line)
    if line_address == -1 and line == '':
        status = 'exit'
        return status

## execute p command
def slippy_print(line_address_list = None, pattern = None, line = None, th_line = 0, output = None, option = None):
    if option != '-n' and -1 not in line_address_list : output.append(line)

    ## line_address in regex pattern
    if pattern:
        if re.search(f'{pattern}', line): output.append(line)
    ## single p-command
    elif 0 in line_address_list and pattern is None: output.append(line)
    ## line_address in digital numbers
    else:
        if th_line in line_address_list: output.append(line)

    ## '$' print the last line
    if -1 in line_address_list:
        if option == '-n' and option and line != '':
            signal[0] = line
        elif option != '-n':
            output.append(line)

        if line == '' and option == '-n':
            output.append(signal[0])
        elif line == '' and option != '-n':
            output.append(output[-2])

## execute d command
def slippy_delete(line_address_list = None, pattern = None, line = None, th_line = 0, output = None, option = None):
    if option == '-n': 
        status = 'exit'
        return status

    ## single d-command
    if 0 in line_address_list and pattern is None:
        status = 'exit'
        return status

    ## line_address in regex pattern
    if pattern:
        if not re.search(f'{pattern}', line): output.append(line)
    ## line_address in digital numbers
    else:
        if th_line not in line_address_list: output.append(line)

    ## '$' delete the last line
    if -1 in line_address_list and line == '':
        output.remove(output[-1])
        output.remove(output[-1])

        status = 'exit'
        return status

## execute s command
def slippy_substitute(line_address_list = None, pattern = None, line = None, th_line = 0, output = None, option = None, regex_pattern = None, replace_str = None, occurrence = 0):
    if option == '-n':
        status = 'exit'
        return status

    ## '$' substitue the last line
    if -1 in line_address_list:
        output.append(line)
        if line == '':
            last_line = output[-2]
            output.remove(last_line)
            slippy_substitute_assist(regex_pattern, replace_str, last_line, occurrence, output)
            status = 'exit'
            return status

    ## line_address in digital numbers
    if th_line in line_address_list:
        slippy_substitute_assist(regex_pattern, replace_str, line, occurrence, output)
    ## line_address in regex pattern
    elif re.search(f'{pattern}', line):
        slippy_substitute_assist(regex_pattern, replace_str, line, occurrence, output)
    ## without line_address
    elif pattern is None and 0 in line_address_list:
        slippy_substitute_assist(regex_pattern, replace_str, line, occurrence, output)
    ## substitute to all lines with the given pattern
    elif -1 not in line_address_list:
        output.append(line)
    
## assist function is used for substituting the requested_pattern with replaced_string
def slippy_substitute_assist(regex_pattern = None, replace_str = None, line = None, occurrence = 0, output = None):
    if occurrence == 0: ## without g suffix
        line = re.sub(f'{regex_pattern}', f'{replace_str}', line, count = 1)
    elif occurrence == 1: ## with g suffix
        line = re.sub(f'{regex_pattern}', f'{replace_str}', line)
    output.append(line)

## advanced function is used for executing line_address in range pattern (ie. from start to end)
def slippy_range(start_end = None, Assist_Line_box = None, line = None, Range = None, pattern = None, slippy_option = None, command = None, output = None, regex_pattern = None, replace_str = None, occurrence = 0, special_content = None):
    ## start and end are both digital numbers (eg. '1,2d')
    if not re.match(r'\/', start_end[0]) and not re.match(r'\/', start_end[1]):
        Assist_Line_box.append(line)

        if int(start_end[0]) > int(start_end[1]): Range.add(int(start_end[0]))
        ## start_end[0] indicates the start_number
        ## start_end[1] indicates the end_number
        start = int(start_end[0])
        while start <= int(start_end[1]):
            Range.add(start)
            start += 1

        status = slippy_range_assist(Range, line, Assist_Line_box, pattern, slippy_option, command, regex_pattern, replace_str, occurrence, output, special_content)
        if status == 'exit':
            return status

    ## start with digital numbers and end with regex pattern (eg, '3,/1/d')
    elif not re.match(r'\/', start_end[0]) and re.match(r'\/', start_end[1]):
        end_regex = re.sub(r'\/', '', start_end[1])
        Assist_Line_box.append(line)

        ## return_list[0] indicates the start_number
        ## return_list[1] indicates the end_number
        if re.search(end_regex, line) and th_line > int(start_end[0]) and signal[0] == 0:
            signal[0] = 1
            start = int(start_end[0])
            end = int(th_line)
            while start <= end:
                Range.add(start)
                start += 1

        status = slippy_range_assist(Range, line, Assist_Line_box, pattern, slippy_option, command, regex_pattern, replace_str, occurrence, output, special_content)
        if status == 'exit':
            return status
    
    ## start with regex pattern and end with digital numbers (eg. '/1/,3d')
    elif re.match(r'\/', start_end[0]) and not re.match(r'\/', start_end[1]):
        start_regex = re.sub(r'\/', '', start_end[0])
        Assist_Line_box.append(line)
        
        if re.search(start_regex, line):
            Range.add(th_line)
            if signal[0] == 0:
                signal[0] = th_line

        elif int(start_end[1]) == th_line:
            start = signal[0]
            Range.add(th_line)
            while start <= int(start_end[1]):
                Range.add(start)
                start += 1

        status = slippy_range_assist(Range, line, Assist_Line_box, pattern, slippy_option, command, regex_pattern, replace_str, occurrence, output, special_content)
        if status == 'exit':
            return status

    ## start with regex pattern and also end with regex pattern (eg. '/1$/,/^2/d')
    elif re.match(r'\/', start_end[0]) and re.match(r'\/', start_end[1]):
        start_regex = re.sub(r'\/', '', start_end[0])
        end_regex = re.sub(r'\/', '', start_end[1])
        Assist_Line_box.append(line)

        ########################################
        if re.search(start_regex, line):
            start_matched.append(th_line)
        if re.search(end_regex, line):
            end_matched.append(th_line)
        ########################################
        if line == '':
            num = 0; tag = 0

            regexstart_to_regexend(num, tag, start_matched, end_matched, Range)
            status = slippy_range_assist(Range, line, Assist_Line_box, pattern, slippy_option, command, 
            regex_pattern, replace_str, occurrence, output, special_content)
            if status == 'exit':
                return status

## assist function is used for executing the command with corresponding line_address
def slippy_range_assist(Range = None, line = None, Assist_Line_box = None, pattern = None, slippy_option = None, command = None, regex_pattern = None, replace_str = None, occurrence = 0, output = None, special_content = None):
    if len(Range) != 0 and line == '':
        th_line = 1
        for l in Assist_Line_box:
            if command == 'delete':
                status = slippy_delete(Range, pattern, l, th_line, output, slippy_option)
                if status == 'exit':
                    return status
            elif command == 'print':
                slippy_print(Range, pattern, l, th_line, output, slippy_option)
            elif command == 'substitute':
                status = slippy_substitute(Range, pattern, l, th_line, output, slippy_option, regex_pattern, replace_str, occurrence)
                if status == 'exit':
                    return status
            elif command == 'append':
                slippy_append(Range, l, th_line, pattern, output, special_content)
            elif command == 'insert':
                slippy_insert(Range, l, th_line, pattern, output, special_content)
            elif command == 'change':
                slippy_change(Range, l, th_line, pattern, output, special_content)
            th_line += 1

## a special recursion function is used to store all line_address from start to end in regex pattern (eg: '/1/,/4/p')
def regexstart_to_regexend(num = 0, tag = 0, start_matched = None, end_matched = None, Range = None):
    while num < len(start_matched):
        if len(end_matched) > tag:
            if start_matched[num] < end_matched[tag]:
                _start = int(start_matched[num])
                while _start <= int(end_matched[tag]):
                    Range.add(_start)
                    _start += 1
            elif start_matched[num] >= end_matched[tag]:
                if len(end_matched) > tag + 1:
                    tag = tag + 1
                    regexstart_to_regexend(num, tag, start_matched, end_matched, Range)
                else:
                    Range.add(int(start_matched[num]))
                    num += 1
            num += 1
            tag += 1
        else:
            Range.add(int(start_matched[num]))
            num += 1

## execute append command
def slippy_append(line_address_list = None, line = None, th_line = 0, pattern = None, output = None, content = None):
    output.append(line)
    if -2 in line_address_list and pattern is None and line != '':
        output.append(content)
    if pattern:
        if re.search(f'{pattern}', line): 
            output.append(content)
    elif th_line in line_address_list:
        output.append(content)

    ## handle $ last line address
    if -1 in line_address_list and line == '':
        output.append(content)

## execute insert command
def slippy_insert(line_address_list = None, line = None, th_line = 0, pattern = None, output = None, content = None):
    if -2 in line_address_list and pattern is None and line != '':
        output.append(content)
    if pattern:
        if re.search(f'{pattern}', line):
            output.append(content)
            output.append(line)
        else:
            output.append(line)
    elif th_line not in line_address_list and line != '':
        output.append(line)
    elif th_line in line_address_list and line != '':
        output.append(content)
        output.append(line)

    ## handle $ last line address
    if -1 in line_address_list and line != '':
        signal[0] = line
    if -1 in line_address_list and line == '':
        output.remove(signal[0])
        output.append(content)
        output.append(signal[0])

## execute change command
def slippy_change(line_address_list = None, line = None, th_line = 0, pattern = None, output = None, content = None):
    if -2 in line_address_list and pattern is None and line != '':
        output.append(content)
    elif pattern:
        if re.search(f'{pattern}', line):
            output.append(content)
        else:
            output.append(line)
    elif th_line not in line_address_list and line != '' and -1 not in line_address_list:
        output.append(line)
    elif th_line in line_address_list and line != '':
        output.append(content)

    ## handle $ last line address
    if -1 in line_address_list and line != '':
        output.append(line)
    if -1 in line_address_list and line == '':
        output.remove(output[-1])
        output.append(content)

##################################################
## main part
##################################################
##-----a bunch of help variables are used for store "temp" lines or 'results'-----
Assist_Line_box = [] ## a help list is used in in slippy_range function to store all lines from stdin
Range = set() ## a list is used to store all addresses in 'start,end' pattern (only used in slippy_range function)
signal = [0] ## a help list is used to tell the program to stop or continue
start_matched = []; end_matched = []
##-----     -----   -----   -----   -----   -----   -----

th_command = 0
while th_command < len(command_argcs):
    ##-----a bunch of variables are used for identifying the line address-----
    line_address = read_line_address(command_argcs, th_command)
    pattern = read_regex_pattern(command_argcs, th_command)
    delimit_char = read_delimiter(command_argcs, th_command)
    start_end = read_start_end(command_argcs, th_command, delimit_char)
    if start_end[0] != None and start_end[1] != None:
        pattern = None
    ##-----     -----       -----       -----       -----       -----       -----

    ## execute the first command
    if Line_box == []:
        th_line = 0
        while True:
            line = sys.stdin.readline()
            Line_box.append(line)
            th_line += 1

            ## quit command --
            if command_argcs[th_command][-1] == 'q':
                if start_end[0] == None and start_end[1] == None:
                    status = slippy_quit(line_address, pattern, line, th_line, output[th_command], slippy_option)
                    if status == 'exit': break
                else:
                    print("slippy: command line: invalid command", file = sys.stderr)
                    sys.exit(1)

            ## print command --
            elif command_argcs[th_command][-1] == 'p':
                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address
                    slippy_print(line_address_list, pattern, line, th_line, output[th_command], slippy_option)
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'print', output[th_command])
                    if status == 'exit': break

            ## delete command --
            elif command_argcs[th_command][-1] == 'd':
                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address
                    status = slippy_delete(line_address_list, pattern, line, th_line, output[th_command], slippy_option)
                    if status == 'exit': break
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'delete', output[th_command])
                    if status == 'exit': break

            ## substitute command --
            elif re.match(r'.*s' + f'{delimit_char}', command_argcs[th_command]):
                occurrence = 0
                ## replacing all occurrences
                if command_argcs[th_command][-1] == 'g': occurrence = 1

                command = re.sub(r'.*s/', '', command_argcs[th_command], count = 1)
                command = 's/' + command
                command = re.split(f'{delimit_char}', command)
                replace_str = command[2]
                replace_str = re.sub(r'\\', '', replace_str)
                regex_pattern = command[1]

                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address

                    status = slippy_substitute(line_address_list, pattern, line, th_line, output[th_command], slippy_option, regex_pattern, replace_str, occurrence)
                    if status == 'exit': break
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'substitute', output[th_command], regex_pattern, replace_str, occurrence)
                    if status == 'exit': break

            ## special command --
            elif command_argcs[th_command][-1] == '@':
                if special_command == 'append':
                    if start_end[0] == None and start_end[1] == None:
                        line_address_list = [0]
                        line_address_list[0] = line_address
                        if line_address_list[0] == 0 and pattern is None:
                            line_address_list[0] = -2
                        slippy_append(line_address_list, line, th_line, pattern, output[th_command], special_content)
                    else:
                        regex_pattern = None; replace_str = None; occurrence = 0
                        status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'append', output[th_command], regex_pattern, replace_str, occurrence, special_content)
                        if status == 'exit': break
                elif special_command == 'insert':
                    if start_end[0] == None and start_end[1] == None:
                        line_address_list = [0]
                        line_address_list[0] = line_address
                        if line_address_list[0] == 0 and pattern is None:
                            line_address_list[0] = -2
                        slippy_insert(line_address_list, line, th_line, pattern, output[th_command], special_content)
                    else:
                        regex_pattern = None; replace_str = None; occurrence = 0
                        status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'insert', output[th_command], regex_pattern, replace_str, occurrence, special_content)
                        if status == 'exit': break
                elif special_command == 'change':
                    if start_end[0] == None and start_end[1] == None:
                        line_address_list = [0]
                        line_address_list[0] = line_address
                        if line_address_list[0] == 0 and pattern is None:
                            line_address_list[0] = -2
                        slippy_change(line_address_list, line, th_line, pattern, output[th_command], special_content)
                    else:
                        regex_pattern = None; replace_str = None; occurrence = 0
                        status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'change', output[th_command], regex_pattern, replace_str, occurrence, special_content)
                        if status == 'exit': break

            if line == '': break
    ## execute the rest of commands
    else:
        Line_box.append("")
        th_line = 1
        for line in Line_box:
            ## quit command --
            if command_argcs[th_command][-1] == 'q':
                if start_end[0] == None and start_end[1] == None:
                    status = slippy_quit(line_address, pattern, line, th_line, output[th_command], slippy_option)
                    if status == 'exit': break
                else:
                    print("slippy: command line: invalid command", file = sys.stderr)
                    sys.exit(1)

            ## print command --
            elif command_argcs[th_command][-1] == 'p':
                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address

                    slippy_print(line_address_list, pattern, line, th_line, output[th_command], slippy_option)
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'print', output[th_command])
                    if status == 'exit': break

            ## delete command --
            elif command_argcs[th_command][-1] == 'd':
                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address

                    status = slippy_delete(line_address_list, pattern, line, th_line, output[th_command], slippy_option)

                    if status == 'exit': break
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'delete', output[th_command])
                    if status == 'exit': break

            ## substitute command --
            elif re.match(r'.*s' + f'{delimit_char}', command_argcs[th_command]):
                occurrence = 0
                ## replacing all occurrences
                if command_argcs[th_command][-1] == 'g': occurrence = 1

                command = re.sub(r'.*s/', '', command_argcs[th_command], count = 1)
                command = 's/' + command
                command = re.split(f'{delimit_char}', command)
                replace_str = command[2]
                replace_str = re.sub(r'\\', '', replace_str)
                regex_pattern = command[1]

                if start_end[0] == None and start_end[1] == None:
                    line_address_list = [0]
                    line_address_list[0] = line_address

                    status = slippy_substitute(line_address_list, pattern, line, th_line, output[th_command], slippy_option, regex_pattern, replace_str, occurrence)
                    if status == 'exit': break
                else:
                    status = slippy_range(start_end, Assist_Line_box, line, Range, pattern, slippy_option, 'substitute', output[th_command], regex_pattern, replace_str, occurrence)
                    if status == 'exit': break
            th_line += 1
    th_command += 1

##################################################
## generate the output
##################################################
## print to stdout
if _i_command is None:
    ## single command
    if len(command_argcs) == 1:
        for l in output[0]:
            print(l, end = '')
    ## multiple commands
    else:
        result = []
        i = 0
        while i < len(command_argcs) - 1:
            j = 0
            while j < len(output[i + 1]):
                if output[i + 1][j] in output[0] and output[i + 1][j] != '':
                    if output[i + 1][j] not in result:
                        result.append(output[i + 1][j])
                j += 1
            i += 1
        for l in sorted(result, key=int):
            print(l, end = '')
## overwrite to the input file
elif _i_command == '-i':
    file = open(input_files[0], 'w')
    ## single command
    if len(command_argcs) == 1:
        for l in output[0]:
            file.write(l)
    ## multiple commands
    else:
        result = []
        i = 0
        while i < len(command_argcs) - 1:
            j = 0
            while j < len(output[i + 1]):
                if output[i + 1][j] in output[0] and output[i + 1][j] != '':
                    if output[i + 1][j] not in result:
                        result.append(output[i + 1][j])
                j += 1
            i += 1
        for l in sorted(result, key=int):
            file.write(l)
    file.close()


