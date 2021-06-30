import sys
import re
import argparse

#Regexes for step entities
def GetRegexFromFuncName(step_func):
    if step_func == 'closed_shell':
        return 'closed_shell\(.*,.*\((.*)\).*\)'
    if step_func == 'open_shell':
        return 'open_shell\(.*,.*\((.*)\).*\)'
    elif step_func == 'advanced_face':
        return 'advanced_face\(.*,.*\((.*)\).*\)'
    elif step_func == 'face_bound':
        return 'face_bound\(.*,(#\d+).*\)'
    elif step_func == 'face_outer_bound':
        return 'face_outer_bound\(.*,(#\d+).*\)'
    elif step_func == 'edge_loop':
        return 'edge_loop\(.*,.*\((.*)\).*\)'
    elif step_func == 'oriented_edge':
        return 'oriented_edge\(.*,.*,.*,(#\d+).*\)'
    elif step_func == 'edge_curve':
        return 'edge_curve\(.*,(#\d+.*,.*#\d+),.*\)'
    elif step_func == 'edge_curve_b_spline':
        return 'edge_curve\(.*,#\d+.*,.*#\d+,.*(#\d+).*,.*\)'
    elif step_func == 'vertex_point':
        return 'vertex_point\(.*,(#\d+)\)'
    elif step_func == 'cartesian_point':
        return 'cartesian_point\(.*,\((.*)\)\)'
    elif step_func == 'b_spline_curve_with_knots':
        return 'b_spline_curve_with_knots\(.*,\d+,\((.*)\),\..*\.,.*\)'

    return None

def GetListOfNextKeysFromKey(current_key, step_func, entities_dict):
    dict_entry = entities_dict.get(current_key)
    if dict_entry != None:
        regex = GetRegexFromFuncName(step_func)
        if regex != None:
            in_shell = re.match(regex, dict_entry)
            if in_shell != None:
                return in_shell.group(1).split(',')

    return None

def GetFuncFromKey(entity_value, entities_dict):
    next_entry = entities_dict.get(entity_value)
    func_name_match = re.match("([a-zA-Z_]+)\(.*\)", next_entry)
    return func_name_match.group(1)


def ExtractPoints(entity_value, entities_dict, out_points):
    cur_func = GetFuncFromKey(entity_value, entities_dict)
    nexts = GetListOfNextKeysFromKey(entity_value, cur_func, entities_dict)
    if cur_func == 'cartesian_point':
        point = [float(nexts[0]), float(nexts[1]), float(nexts[2]), 1.]
        out_points.append(point)
    else:
        if nexts != None:
            for element in nexts:
                if element != None:
                    if element == nexts[len(nexts) - 1]:
                        ExtractPoints(element, entities_dict, out_points)
                    else:
                        ExtractPoints(element, entities_dict, out_points)

#dict entry: #<line_value> : '<STEP_FUNCTION>(<content>)'
def BuildEntitiesDict(file_input, my_dict):
    f = open(file_input, 'r', encoding="utf-8")
    current_line = ''
    current_line_nb = ''
    for line in f:
        line = line.lower()
        split_new_line = line.split("=")
        if len(split_new_line) == 2:
            if len(current_line_nb) != 0 and len(current_line) != 0:
                current_line = current_line.replace('\n', '')
                my_dict[current_line_nb] = current_line
            current_line = split_new_line[1]
            current_line_nb = split_new_line[0]
        else:
            current_line += line

##360=B_SPLINE_CURVE_WITH_KNOTS('',3,(#),.UNSPECIFIED., .F.,.F.,(4,4),(0.,1.),.UNSPECIFIED.);
def GetBSplineKnots(entity_value, entities_dict):
    regex = 'b_spline_curve_with_knots\(.*,\d+,\(.*\),\..*\.,\..*\.,\..*\.,\((.*)\),\((.*)\),.*\)'
    result = re.match(regex, entities_dict.get(entity_value))
    lst = []
    lst.append(result.group(1))
    lst.append(result.group(2))
    return lst

def PrintBSplineForNurbsCalculator(entity_value, entities_dict):
    cur_func = GetFuncFromKey(entity_value, entities_dict)
    if cur_func != 'b_spline_curve_with_knots':
        print('Please give the value of a b_spline_curve_with_knots')
        return
    else:
        print('{\n\t\"discretization\": 100,\n\t\"degree\": 3,\n\t\"controlPoints\": [')
        list_of_points = []
        ExtractPoints(entity_value, entities_dict, list_of_points)
        index = 0
        for pt in list_of_points:
            str_pt = "\t\t{0:f},\n\t\t {1:f},\n\t\t {2:f},\n\t\t {3:f}".format(pt[0],  pt[1],  pt[2], pt[3])
            if index == len(list_of_points) - 1:
                str_pt += "\n"
            else:
                str_pt += ",\n"
            print(str_pt)
            index += 1
        print('\t],\n\t"knots": [')
        mult_and_knots = GetBSplineKnots(entity_value, entities_dict)
        split_mult = mult_and_knots[0].split(',')
        split_knots = mult_and_knots[1].split(',')
        index = 0
        for mult in split_mult:
            mult_to_int  = int(mult)
            for count in range(0,mult_to_int): # multiplicity of knot
                current_knot_str = "\t\t{0:f}".format(float(split_knots[index]))
                if index != (len(split_mult) - 1):
                    current_knot_str += ","
                print(current_knot_str)
            index += 1
        print('\t]\n}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step_file", help="Valid step file (no validity check is done in this script)")
    parser.add_argument("bspline_entity_id", help="Line number (format: #number)")
    args = parser.parse_args()
    my_dict = {}
    BuildEntitiesDict(args.step_file, my_dict)
    PrintBSplineForNurbsCalculator(args.bspline_entity_id, my_dict)