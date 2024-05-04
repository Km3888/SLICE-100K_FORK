from tqdm import tqdm
import json
import pdb
import os
import sys
import argparse

from preprocess_utils import debug, get_layers, make_json, \
                             get_data, \
                             convert_strings_to_table
                             
from extrusion import  relative_extrusion, absolute_extrusion, test_extrusion
from chunking import aligned_chunks
from contour_flipping import flip_on_contours

access_token = "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"

def main(args):
    """
    Main function for aligning and processing G-code files.

    Saves G-code chunks in a JSON file to be used for training the model.

    Args:
        args: Command-line arguments passed to the script.

    Returns:
        None
    """
    
    data = get_data(args.data_path,args.n_files)
    # Re-arrange Marlin G-code so that the ordering of the contours 
    # is the same as in the Sailfish version
    aligned_gcode = []
    total_successes = 0
    total_failures = 0
    print('Performing contour flipping on %s files' % args.n_files)
    for i in tqdm(range(len(data))):
        gcode_a, gcode_b = data[i]
        flipped_a,flipped_b,successes,failures = flip_on_contours(gcode_a,gcode_b)
        aligned_gcode.append((flipped_a,flipped_b))
        total_successes+=successes
        total_failures+=failures
    print('finished contour flipping!')
    print(f'{total_successes}/{total_successes+total_failures} layers successfully aligned')

    # Split up Marlin and Sailfish into corresponding chunks that are small enough
    # to fit in context window of transformer-based model
    layers_to_chunk = get_layers(aligned_gcode)
    chunk_list = []
    successes = 0
    failures = 0
    print('Creating chunks from %s layers' % len(layers_to_chunk))
    for i in tqdm(range(len(layers_to_chunk))):
        aligned_a,aligned_b = layers_to_chunk[i]
        # chunks = aligned_chunks(aligned_a,aligned_b,args.chunk_size)  
        try:
            chunks = aligned_chunks(aligned_a,aligned_b,args.chunk_size)
            chunk_list.extend(chunks)
            successes +=1
        except:
            failures+=1
    print(f'{successes}/{successes+failures} layers successfully chunked')
    print('Total number of chunks: %s' % len(chunk_list))
    make_json(chunk_list)
    print('Made json file')
    print('Signing off...')


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_files", type=int, default=50)
    parser.add_argument("--chunk_size", type=int, default=20)
    parser.add_argument("--data_path", type=str, default="/vast/km3888/paired_gcode")
    parser.add_argument("--output_path", type=str, default="/vast/km3888/paired_gcode/chunked_data")
    args = parser.parse_args()

    # main(args)
    test_extrusion(args)