#!/usr/bin/python3

# Copyright 2013 Universidade Federal de Uberlândia
# Author: Lucas Clemente Vella <lucas.vella@i9nagi.ufu.br>

# Utility to batch create conference tags from CSV data and SVG template.

import os
import io
import os.path
import sys
import csv
import re
import subprocess
import jinja2

parser = re.compile(r'Batch (?P<number>\d+):\n(?P<csv>(.*?,.*?\n)+)')

def parse_status(status_text):
    number = 0
    already_done = set()
    for match in parser.finditer(status_text):
        number = int(match.group('number'))
        csv_buf = io.StringIO(match.group('csv'))
        already_done.update(map(tuple, csv.reader(csv_buf)))

    return number, already_done

def main():
    try:
        working_dir = sys.argv[1]
        os.chdir(working_dir)
    except IndexError:
        pass # use current directory as working dir
    except FileNotFoundError as e:
        print(e, '\nUsage:\n  {} [working_directory]\nIf working directory is not provided, current directory will be used instead.'.format(sys.argv[0]))
        sys.exit(1)

    template = jinja2.Template(open('template.svg', 'r').read())
    data = set(map(tuple, csv.reader(open('data.csv', 'r'))))

    status = open('generated_status.txt', 'a+')
    status.seek(0)
    last_batch, already_done = parse_status(status.read())
    batch_num = last_batch + 1

    data -= already_done
    if not data:
        print('Nothing new to process, everything is in one of the batches.\nSee "generated_status.txt" file.')
        sys.exit(0)

    batch_path = 'batch{:03d}'.format(batch_num)
    os.mkdir(batch_path)

    processed = []
    workers = []
    for row in data:
        gen = template.render(nome=row[0], empresa=row[1])
        base_name = os.path.join(batch_path, ','.join(row))
        svg_name = base_name + '.svg'
        pdf_name = base_name + '.pdf'
        with open(svg_name, 'w') as output:
            output.write(gen)
        workers.append(subprocess.Popen(['inkscape', '-z', '-f={}'.format(svg_name), '-A={}.pdf'.format(base_name)]))
        processed.append(row)

    listing_text = '\n'.join(map(','.join, processed)) + '\n'
    print("Processed:")
    print(listing_text)

    with open(os.path.join(batch_path, 'listing.txt'), 'w') as listing:
        listing.write(listing_text)

    status.seek(0, os.SEEK_END)
    status.write('Batch {}:\n'.format(batch_num))
    status.write(listing_text)

    for w in workers:
        w.wait()

    #TODO: cluster output for printing....

    print('Done.')

if __name__ == "__main__":
    main()
