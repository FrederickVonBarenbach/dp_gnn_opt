import os
import sys
import argparse
import json
import math
import random


def parse_axis(axis):
    if "combine" in axis:
        return combine_axes(*axis["combine"])
    elif "join" in axis:
        return join_axes(*axis["join"])
    else:
        return axis


def combine_axes(*axes):
    combination = {}
    for axis in axes:
        current_length = 1
        if combination.values():
            current_length = len(list(combination.values())[0])
        # combine axis
        added_length = len(list(axis.values())[0])
        for key in combination:
            combination[key] = combination[key]*added_length
        for key in axis:
            combination[key] = [value for value in axis[key] for i in range(current_length)]
    return combination


def join_axes(*axes):
    joined = {}
    for axis in axes:
        current_length = 0
        if joined.values():
            current_length = len(list(joined.values())[0])
        axis = parse_axis(axis)
        # join axis
        added_length = len(list(axis.values())[0])
        for key in joined:
            if key not in axis:
                joined[key] += ["N/a"]*added_length
        for key in axis:
            if key not in joined:
                joined[key] = ["N/a"]*current_length
            joined[key] += axis[key]
    return joined


def parse_args(config):
    command = ""
    for key, value in config.items():
        if value != "N/a":
            command += " --config." + key + "=" + str(value)
    return command


def get_experiment_name(json_obj, config):
    experiment_name = ""
    for key, value in config.items():
        # Add value to experiment name if it's not N/a and if the key is in "experiment_name_params" (if it exists in json_obj)
        if value != "N/a" and ("experiment_name_params" not in json_obj or key in json_obj["experiment_name_params"]):
            experiment_name += key + "=" + str(value) + ","
    if len(experiment_name) > 0:
        return experiment_name[:-1]
    return experiment_name


def parse_environment_variables(json_obj, config, iteration):
    command = " --workdir=./tmp/" + get_experiment_name(json_obj, config) + ",iter=" + str(iteration)
    for key, value in json_obj.items():
        if key == "config":
            command += " --config=" + str(value)
        elif key == "random" and value == True:
            command += " --config.rng_seed=" + str(random.randint(0, 1000000)) # Use same rng seed
        elif key != "grid" and key != "iter"  and key != "experiment_name_params":
            command += " --config." + key + "=" + str(value)
    command += " --config.experiment_name=" + get_experiment_name(json_obj, config)
    return command


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("in_path", help="input JSON (or previous runner script if recompute is set)", type=str)
    parser.add_argument("--out_path", help="path to runner script", default="../runner.sh", type=str)
    args = parser.parse_args()

    # parse JSON
    with open(args.in_path) as json_file:
        json_obj = json.load(json_file)
        grid = parse_axis(json_obj["grid"])
    
    # make runner
    n_configs = len(next(iter(grid.values())))
    iterations = 1 if "iter" not in json_obj else json_obj["iter"]

    # open files
    command_file = open(args.out_path, 'w')

    # write to files
    for i in range(n_configs):
        # get config for this experiment (i)
        config = {}
        for key, value in grid.items():
            config[key] = value[i]
        # write command
        for iteration in range(1, iterations+1):
            # parse command for runner
            command = "python main.py" + parse_environment_variables(json_obj, config, iteration) + parse_args(config)
            command_file.write(command + "\n")

    # close files
    command_file.close()