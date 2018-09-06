#!/usr/bin/env python3 

from urllib.request import Request, urlopen
import re

index_url = 'http://www.linux-usb.org/usb.ids'

ignored_line_pattern = re.compile('(^#.*\n)|(^[ \t\r]*\n)') #comments or empty lines
endoflist_str = "# List of known device classes, subclasses and protocols\n"
ignored = 0
endoflist = 1

patterns = [
    re.compile('^(?P<id>[0-9a-fA-F]{4})  (?P<name>.+)'), #vendor
    re.compile('^\t(?P<id>[0-9a-fA-F]{4})  (?P<name>.+)'), #device
    re.compile('^\t\t(?P<id>[0-9a-fA-F]{4})  (?P<name>.+)') #interface
]

file_prologue = r"""/* This file was auto-generated by the usbids_to_cstruct.py script. Don't edit! */
#include <stdlib.h>
#include "usbids.h"

UsbDevStruct UsbList[] = {
"""

file_epilogue = r"""}};
/*
 * Total vendors: {}
 * Total devices: {}
 */

size_t UsbListLength = sizeof UsbList / sizeof UsbList[0];

static int cmp(const void *vp, const void *vq)
{{
	const UsbDevStruct *p = vp;
	const UsbDevStruct *q = vq;

	if (p->VendorID != q->VendorID)
		return p->VendorID - q->VendorID;

    return p->DeviceID - q->DeviceID;
}}

UsbDevStruct *UsbFind(long vendor, long device)
{{
	UsbDevStruct key;

	key.VendorID = vendor;
	key.DeviceID = device;
	return bsearch(&key, UsbList, UsbListLength, sizeof *UsbList, cmp);
}}

int UsbListIsSorted(void)
{{
	size_t i;

	for (i = 1; i < UsbListLength; i++)
		if (cmp(&UsbList[i - 1], &UsbList[i]) > 0)
			return 0;
	return 1;
}}
"""


def skip_comments(page):
    for line in page:
        line = line.decode('utf-8')
        match = ignored_line_pattern.search(line)
        if match is None:
            return line
    return None

def parse(line):
    for i, pattern in enumerate(patterns):
        #order of searches is important here!
        match = pattern.search(line)

        if match is not None:
            return i, match.group('id'), match.group('name')

        if line == endoflist_str:
            return endoflist

        if ignored_line_pattern.search(line) is not None:
            return ignored

    return None


with urlopen(Request(index_url)) as page:
    first_line = skip_comments(page)
    data = parse(first_line)
    total_vendors = 0
    total_devices = 0

    with open('usbids.c', 'w') as usbids_src:

        usbids_src.write(file_prologue)

        if data is not ignored and data[0] == 0:
            curr_vendor = data
            usbids_src.write('\t{{ 0x{}, 0x0000, "{}", NULL }},\n'.format(
                                data[1], data[2].replace('\\', '\\\\').replace(r'"', r'\"'),
                             ))
            total_vendors += 1

        for line in page:
            line = line.decode('utf-8')
            data = parse(line)
            if data is None:
                raise RuntimeError('Failed parsing line "{}"'.format(line.strip('\n')))

            if data is ignored:
                continue

            if data is endoflist:
                break

            if data[0] == 0:
                curr_vendor = data
                usbids_src.write('\t{{ 0x{}, 0x0000, "{}", NULL }},\n'.format(
                                    data[1], data[2].replace('\\', '\\\\').replace(r'"', r'\"'),
                                 ))
                total_vendors += 1
            elif data[0] == 1:
                usbids_src.write('\t{{ 0x{}, 0x{}, "{}", "{}" }},\n'.format(
                                    curr_vendor[1], data[1],
                                    curr_vendor[2].replace('\\', '\\\\').replace(r'"', r'\"'),
                                    data[2].replace('\\', '\\\\').replace(r'"', r'\"'),
                                 ))
                total_devices += 1
            #ignore interfaces
            #elif data[0] == 2:

        usbids_src.write(file_epilogue.format(total_vendors, total_devices))
