#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

import sys
from os.path import basename, dirname, join, exists, isdir, relpath, splitext
import csv
import argparse
from urlparse import urlparse
import urllib
from datetime import datetime
from itertools import izip
import threading
import Queue
import numpy
import math

from lxml import etree
from osgeo import gdal

gdal.UseExceptions()


def main(args):
    parser = argparse.ArgumentParser(add_help=True, fromfile_prefix_chars='@',
                                     argument_default=argparse.SUPPRESS)

    parser.add_argument("--browse-report", dest="browse_report", default=None)
    parser.add_argument("--num-concurrent", dest="num_concurrent", default=4)
    parser.add_argument("--skip-existing", dest="skip_existing",
                        action="store_true", default=False)
    parser.add_argument("--browse-type", dest="browse_type", default=None)
    parser.add_argument("--pretty-print", dest="pretty_print",
                        action="store_true", default=False)
    parser.add_argument("--browses-per-report", dest="browses_per_report",
                        type=int, default=0)
    parser.add_argument("--rel-path", dest="rel_path",
                        action="store_true", default=False)
    parser.add_argument("input_filename", metavar="infile", nargs=1)
    parser.add_argument("output_directory", metavar="outdir", nargs=1)

    args = parser.parse_args(args)
    
    browse_report = args.browse_report
    input_filename = args.input_filename[0]
    output_dir = args.output_directory[0]
    browses_per_report = args.browses_per_report

    if not exists(input_filename):
        exit("Input file does not exist.")

    if not exists(output_dir):
        exit("Output directory does not exist.")

    if not isdir(output_dir):
        exit("Output path is not a directory.")

    datasets = parse_browse_csv(input_filename)

    urls_and_path_list = [(url, join(output_dir, filename))
                          for _, _, _, url, filename, _ in datasets]
    download_urls(urls_and_path_list, args.num_concurrent, args.skip_existing)

    if browse_report is not None:
        report_datas = [(start, stop, footprint, join(output_dir, filename), pass_dir)
                       for start, stop, footprint, _, filename, pass_dir in datasets]
        num_datas = len(report_datas)
        if browses_per_report <= 0:
            browses_per_report = len(report_datas)
        report_datas = chunks(report_datas, browses_per_report)
        num_reports = int(math.ceil(float(num_datas)/browses_per_report))
        order = int(math.ceil(math.log10(num_reports)))
        for i, report_data in enumerate(report_datas, start=1):
            filename, ext = splitext(browse_report)
            filename = filename + "_" + str(i).rjust(order, "0") + ext
            write_browse_report(filename, report_data, args.browse_type,
                                args.pretty_print, args.rel_path)


def error(message, exit=True):
    print "Error: ", message
    if exit:
        sys.exit(1)


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def parse_browse_csv(input_filename):
    """ returns a list of tuples in the form (collection, start, stop,
    footprint, url, filename) """
    
    result = []
    with open(input_filename, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        first = True
        dt_frmt = "%Y-%m-%d %H:%M:%S.%f"
        
        for line in reader:
            # skip first line, as it is only a header
            if first:
                first = False
                continue

            footprint = pairwise(map(lambda c: float(c), line[16].split(" ")))
            
            if line[18] is not None and line[18] != "":
                result.append((datetime.strptime(line[6], dt_frmt),     # start
                               datetime.strptime(line[7], dt_frmt),     # stop
                               footprint,                               # footprint
                               line[18],                                # url
                               "_" + basename(urlparse(line[18]).path), # filename
                               line[14]                                 #pass direction 
                              ))
            else:
                print "Browse image with result ID '%s' not added because of an empty URL." % line[0]
    return result


def download_urls(url_and_path_list, num_concurrent, skip_existing):
    # prepare the queue
    queue = Queue.Queue()
    for url_and_path in url_and_path_list:
        queue.put(url_and_path)

    # start the requested number of download threads to download the files
    threads = []
    for _ in range(num_concurrent):
        t = DownloadThread(queue, skip_existing)
        t.daemon = True
        t.start()
        #threads.append(t)

    queue.join()

    # TODO: this version is safer, but currently blocks on finished
    #for thread in threads:
    #    print("Joining thread")
    #    thread.join()


class DownloadThread(threading.Thread):
    def __init__(self, queue, skip_existing):
        super(DownloadThread, self).__init__()
        self.queue = queue
        self.skip_existing = skip_existing
          
    def run(self):
        while True:
            #grabs url from queue
            url, path = self.queue.get()

            if self.skip_existing and exists(path):
                # skip if requested
                self.queue.task_done()
                continue
            
            try:
                urllib.urlretrieve(url, path)
            except IOError:
                print "Error downloading url '%s'." % url
        
            #signals to queue job is done
            self.queue.task_done()



def write_browse_report(browse_filename, datasets, browse_type, pretty_print, 
                        rel_path):
    """"""
    ext_to_image_type = {
        ".jpg": "Jpeg",
        ".jpeg": "Jpeg",
        ".jp2": "Jpeg2000",
        ".tif": "TIFF",
        ".tiff": "TIFF",
        ".png": "PNG",
        ".bmp": "BMP"
    }
    
    def ns_rep(tag):
        return "{http://ngeo.eo.esa.int/schema/browseReport}" + tag
    nsmap = {"rep": "http://ngeo.eo.esa.int/schema/browseReport"}
    
    root = etree.Element(ns_rep("browseReport"), nsmap=nsmap)
    root.attrib["version"] = "1.1"
    etree.SubElement(root, ns_rep("responsibleOrgName")).text = "EOX"
    etree.SubElement(root, ns_rep("dateTime")).text = datetime.now().isoformat()
    if browse_type:
        etree.SubElement(root, ns_rep("browseType")).text = browse_type
    
    for start, stop, footprint, filename, pass_dir in datasets:
        # open the browse image and retrieve width and height
        try:
            ds = gdal.Open(filename)
            sizex, sizey = ds.RasterXSize, ds.RasterYSize
            ds = None
        except RuntimeError:
            # skip files which cannot be opened
            print "Browse image '%s' not added in browse report '%s' because of a RuntimeError." % (filename, browse_filename)
            continue

        # calculate the pixel values to the according latlon coordinates
        footprint = list(footprint)
        length = len(footprint) - 1
        right = footprint[1:length / 2 + 1]
        left = footprint[length / 2 + 1:]

        assert(len(right) == len(left))

        
        if pass_dir == "A":
            pixel_coords = [sizex, sizey]

            ll_start = left[0]
            ll_end = left[-1]

            for point in left:
                pixel_coords.extend(
                    calc_pixel_coords(ll_start, ll_end, point, (0, 0), (0, sizey))
                )
            
            ll_start = right[0]
            ll_end = right[-1]

            for point in right:
                pixel_coords.extend(
                    calc_pixel_coords(ll_start, ll_end, point, (sizex, sizex), (0, sizey))
                )
            

        elif pass_dir == "D":
            pixel_coords = [0, 0]

            ll_start = right[0]
            ll_end = right[-1]

            
            for point in right:
                pixel_coords.extend(
                    calc_pixel_coords(ll_start, ll_end, point, (sizex, sizex), (sizey, 0))
                )

            ll_start = left[0]
            ll_end = left[-1]

            for point in left:
                pixel_coords.extend(
                    calc_pixel_coords(ll_start, ll_end, point, (0, 0), (sizey, 0))
                )
        
        ll_coords = [coord for pair in right for coord in pair] + \
                    [coord for pair in left for coord in pair]
        ll_coords.insert(0, ll_coords[-2])
        ll_coords.insert(1, ll_coords[-1])

        # convert to string
        pixel_coords = map(str, map(int, pixel_coords))
        ll_coords = map(str, ll_coords)
        
        if rel_path:
            filename = relpath(filename, dirname(browse_filename))
        else:
            filename = basename(filename)
        
        base, ext = splitext(filename)
        base = basename(base)
        
        browse = etree.SubElement(root, ns_rep("browse"))
        etree.SubElement(browse, ns_rep("browseIdentifier")).text = base
        etree.SubElement(browse, ns_rep("fileName")).text = filename
        etree.SubElement(browse, ns_rep("imageType")).text = ext_to_image_type[ext]
        etree.SubElement(browse, ns_rep("referenceSystemIdentifier")).text = "EPSG:4326"
        footprint = etree.SubElement(browse, ns_rep("footprint"))
        footprint.attrib["nodeNumber"] = str(len(ll_coords) / 2)
        etree.SubElement(footprint, ns_rep("colRowList")).text = " ".join(pixel_coords)
        etree.SubElement(footprint, ns_rep("coordList")).text = " ".join(ll_coords)
        
        etree.SubElement(browse, ns_rep("startTime")).text = start.isoformat()
        etree.SubElement(browse, ns_rep("endTime")).text = stop.isoformat()
    

    with open(browse_filename, "wb") as f:
        f.write(etree.tostring(root, pretty_print=pretty_print))


def calc_pixel_coords(ll_start, ll_end, ll_point, x_range, y_range, swap_axes=True):
    xidx = 1 if swap_axes else 0
    yidx = 0 if swap_axes else 1
    
    minx = min(ll_start[xidx], ll_end[xidx])
    miny = min(ll_start[yidx], ll_end[yidx])
    maxx = max(ll_start[xidx], ll_end[xidx])
    maxy = max(ll_start[yidx], ll_end[yidx])
    
    if (maxx == minx):
        lerp_x = 0
    else:
        lerp_x = (ll_point[xidx] - minx) / (maxx - minx)
    if (maxy == miny):
        lerp_y = 0
    else:
        lerp_y = (ll_point[yidx] - miny) / (maxy - miny)
    
    return (
        x_range[0] + (x_range[1] - x_range[0]) * lerp_x,
        y_range[0] + (y_range[1] - y_range[0]) * lerp_y
    )


if __name__ == "__main__":
    main(sys.argv[1:])
