import sys
from os.path import basename, join, exists, isdir
import csv
import argparse
from urlparse import urlparse
import urllib
from datetime import datetime
import threading
import Queue


def main(args):
    parser = argparse.ArgumentParser(add_help=True, fromfile_prefix_chars='@',
                                     argument_default=argparse.SUPPRESS)

    parser.add_argument("--browse-report", dest="browse_report", default=None)
    parser.add_argument("--num-concurrent", dest="num_concurrent", default=4)
    parser.add_argument("--skip-existing", dest="skip_existing",
                        action="store_true", default=False)
    parser.add_argument("input_filename", metavar="infile", nargs=1)
    parser.add_argument("output_directory", metavar="outdir", nargs=1)

    args = parser.parse_args(args)
    browse_report = args.browse_report
    input_filename = args.input_filename[0]
    output_dir = args.output_directory[0]

    if not exists(input_filename):
        exit("Input file does not exist.")

    if not exists(output_dir):
        exit("Output directory does not exist.")

    if not isdir(output_dir):
        exit("Output path is not a directory.")

    datasets = parse_browse_csv(input_filename)

    urls_and_path_list = [(url, join(output_dir, filename)
                          for _, _, _, _, url, filename in datasets]
    download_urls(urls_and_path_list, args.num_concurrent, args.skip_existing)

    if browse_report is not None:
        write_browse_report(browse_report)



def error(message, exit=True):
    print "Error: ", message
    if exit:
        sys.exit(1)


def parse_browse_csv(input_filename):
    """ returns a list of tuples in the form (collection, start, stop,
    footprint, url, filename) """
    result = []
    with open(input_filename, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        first = True

        dt_frmt = "%Y-%m-%d %H:%M:%S.%f"
        
        for line in reader:
            if first:
                first = False
                continue
            
            result.append((line[4],                             # collection
                           datetime.strptime(line[6], dt_frmt), # start
                           datetime.strptime(line[7], dt_frmt), # stop
                           line[16],                            # footprint
                           line[18],                            # url
                           basename(urlparse(line[18]).path)    # filename
                          ))
            

    return result


def download_urls(url_and_path_list, num_concurrent, skip_existing):
    print "num concurrent ", num_concurrent
    queue = Queue.Queue()
    
    for url_and_path in url_and_path_list:
        queue.put(url_and_path)

    print "size", queue.qsize()

    threads = []
    for _ in range(num_concurrent):
        print "Starting thread"
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

def write_browse_report(filename, datasets):
    

    


    
    pass


if __name__ == "__main__":
    main(sys.argv[1:])
