 # Which of the favors of your Lord will you deny?

import sys
from collections import defaultdict

# Utility Functions
def lower(s):
    return s.lower()

def remove_whitespace(s):
    return "".join(s.split())

def tokenize(s, delim):
    return s.split(delim)

def dec_to_hex(d_s):
    return format(int(d_s), 'x')

def dec_to_hex_pad_trim(d_s):
    t = dec_to_hex(d_s)
    if len(t) == 1:
        return "0" + t
    elif len(t) > 2:
        return t[-2:]
    return t

def string_hex_to_dec(s):
    return int(s, 16)

# Main Function
def main():
    # File handling
    input_file = "assembly_text.txt"
    output_file = "instruction.hex"

    try:
        with open(input_file, "r") as infile:
            lines = infile.readlines()
    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)

    instructions = ["add", "sub", "and", "or", "sll", "srl", "nor", "addi", "subi", "andi", "ori", "sw", "lw", "beq", "bneq", "j"]
    instructions_r = ["add", "sub", "and", "or", "sll", "srl", "nor"]
    instructions_i = ["addi", "subi", "andi", "ori", "sw", "lw", "beq", "bneq"]

    map_reg_add = {
        "$zero": "0", "$t0": "1", "$t1": "2", "$t2": "3",
        "$t3": "4", "$t4": "5", "$sp": "6"
    }

    map_ins_opc = {
        # "add": "4", "sub": "c", "and": "d", "or": "9",
        # "sll": "f", "srl": "6", "nor": "a",
        # "addi": "e", "subi": "0", "andi": "0", "ori": "5",
        # "sw": "2", "lw": "7", "beq": "3", "bneq": "1", "j": "8"
        "andi": "0", "addi":"1","or":"2","sll":"3", "subi":"4",
        "nor":"5", "lw":"6", "add" : "7", "bneq" : "8", "sw":"9",
        "sub" : "a", "ori":"b", "j":"c","and":"d", "beq":"e", "srl":"f"
     }

    map_label_add = {}
    map_instruction_counter = {}
    machine_code = []
    line_label = []

    counter = 0

    for line in lines:
        tokens = line.strip().split()
        if not tokens:
            continue

        ins = lower(tokens[0])
        og = tokens[0]
        counter = len(machine_code)

        if ins in instructions_r:  # R-type
            info = remove_whitespace("".join(tokens[1:]))
            res = tokenize(info, ',')

            dest_reg, src_reg_1, src_reg_2 = res[:3]
            sh_amt = "0"

            if ins in ["sll", "srl"]:
                sh_amt = int(sh_amt) 
                if sh_amt < 0 : 
                    sh_amt += 256
                sh_amt = dec_to_hex(src_reg_2)
                output = f"{map_ins_opc[ins]}{map_reg_add[src_reg_1]}0{map_reg_add[dest_reg]}{sh_amt}"
            else:
                output = f"{map_ins_opc[ins]}{map_reg_add[src_reg_1]}{map_reg_add[src_reg_2]}{map_reg_add[dest_reg]}{sh_amt}"
            machine_code.append(output)

        elif ins in instructions_i:  # I-type
            info = remove_whitespace("".join(tokens[1:]))
            res = tokenize(info, ',')

            dest_reg, src_reg = res[:2]
            opcode = map_ins_opc[ins]

            if ins in ["addi", "subi", "andi", "ori"]:
                add_imm = int(res[2])
                if add_imm < 0 : 
                    add_imm += 256 
                t = dec_to_hex_pad_trim(add_imm)
                output = f"{opcode}{map_reg_add[src_reg]}{map_reg_add[dest_reg]}{t}"
            elif ins in ["sw", "lw"]:
                if '(' in src_reg:
                    temp = tokenize(src_reg, '(')
                    offset_d, left = temp[0], temp[1]
                    offset_d = int(offset_d)
                    if offset_d < 0 : 
                        offset_d += 256 
                    other = tokenize(left, ')')[0]
                    t = dec_to_hex_pad_trim(offset_d)
                    output = f"{opcode}{map_reg_add[other]}{map_reg_add[dest_reg]}{t}"
                else:
                    output = f"{opcode}{map_reg_add[src_reg]}{map_reg_add[dest_reg]}00"
            elif ins in ["beq", "bneq"]:
                label = res[2]
                print(res)
                print(label)
                if label not in map_label_add:
                    output = f"{opcode}{map_reg_add[dest_reg]}{map_reg_add[src_reg]}"
                    line_label.append((counter, label))
                    map_instruction_counter[output] = counter
                else:
                    offset_count = string_hex_to_dec(map_label_add[label]) - counter - 1
                    if offset_count < 0:
                        offset_count = 256 + offset_count
                    print(offset_count)
                    offset_count_str = dec_to_hex_pad_trim(str(offset_count))
                    output = f"{opcode}{map_reg_add[dest_reg]}{map_reg_add[src_reg]}{offset_count_str}"
            machine_code.append(output)

        elif ins == "j":  # J-type
            target = tokens[1]
            if target not in map_label_add:
                output = f"{map_ins_opc[ins]}"
                line_label.append((counter, target))
            else:
                output = f"{map_ins_opc[ins]}{map_label_add[target]}00"
            machine_code.append(output)

        else:  # Label
            label = tokenize(og, ':')[0]
            addr = dec_to_hex_pad_trim(str(counter))
            map_label_add[label] = addr

    # Resolve labels
    for code_idx, label_name in line_label:
        if machine_code[code_idx] == map_ins_opc["j"]:
            machine_code[code_idx] += f"{map_label_add[label_name]}00"
        else:
            offset_count = string_hex_to_dec(map_label_add[label_name]) - map_instruction_counter[machine_code[code_idx]] - 1
            offset_count_str = dec_to_hex_pad_trim(str(offset_count))
            machine_code[code_idx] += offset_count_str

    # Write output
    with open(output_file, "w") as outfile:
        outfile.write("v2.0 raw\n")
        outfile.write("\n".join(machine_code) + "\n")
        # outfile.write("\n")

if __name__ == "__main__":
    main()
