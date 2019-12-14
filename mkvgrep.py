#!/usr/bin/python3

import subprocess as sp
import sys
import re
import os
import tempfile
import pysubs2


tmpfile_name = "/tmp/sub%s.srt" % next(tempfile._get_candidate_names())
ffprobe = "/usr/bin/ffprobe"
mkvextract = "/usr/bin/mkvextract"
grep = "/usr/bin/grep"


def printhelp():
    print("mkvgrep.py [-m] [-t number] [-l lang] [mkv_file_name] [grep options]\n"
          "Simple tool to grep the subtitles of a mkv file\n"
          "\t-m\tprint mismatching file names\n"
          "\t-t num\tif more than one subtitle track are found, select which one to use (default 0)")
    sys.exit(0)


def find_track_id(lines, track_finders, track_displacement=0):
    candidates = []
    for line in lines:
        for subtype, patterns in track_finders.items():
            for track_finder in patterns:
                match = track_finder.match(line)
                if match is not None:
                    if match.group("trackid") not in candidates:
                        candidates.append((subtype, match.group("trackid")))
    if len(candidates) == 0:
        return None, None
    best = candidates[min(track_displacement, len(candidates) - 1)]
    return best[0], best[1]


def shitty_cli_semiparser():
    offset = 1

    file = sys.argv[offset]
    lang = "eng"
    print_mismatch = False
    grep_params = sys.argv[offset+1:]
    track_displacement = 0

    further_params = True
    current_cli_param = sys.argv[offset]
    while further_params:
        if current_cli_param == "-m":
            file = sys.argv[offset+1]
            print_mismatch = True
            grep_params = sys.argv[offset+2:]
            offset += 1
        elif current_cli_param == "-t":
            file = sys.argv[offset+2]
            track_displacement = int(sys.argv[offset+1])
            grep_params = sys.argv[offset+3:]
            offset += 2
        elif current_cli_param == "-l":
            file = sys.argv[offset+2]
            lang = sys.argv[offset+1]
            grep_params = sys.argv[offset+3:]
            offset += 2
        else:
            further_params = False
        current_cli_param = sys.argv[offset]

    return file, print_mismatch, grep_params, track_displacement, lang


def half_ass(filename, delete=True):
    subs = pysubs2.load(filename)
    newname = filename + ".ass"
    subs.save(newname)
    if delete and os.path.isfile(filename):
        os.remove(filename)
    return newname 


def main():
    global tmpfile_name
    if sys.argv[1].lower() == "-h" or sys.argv[1].lower() == "--help":
        printhelp()

    file, print_mismatch, grep_params, track_displacement, lang = shitty_cli_semiparser()
    
    track_finders = {
        "ass": [
            re.compile(".*Stream #0:(?P<trackid>[0-9]+)\(%s\): Subtitle: ass(| \(default\)).*" % lang),
            re.compile(".*Stream #0:(?P<trackid>[0-9]+): Subtitle: ass(| \(default\)).*")
            ],
        "srt": [
            re.compile(".*Stream #0:(?P<trackid>[0-9]+)\(%s\): Subtitle: subrip(| \(default\)).*" % lang),
            re.compile(".*Stream #0:(?P<trackid>[0-9]+): Subtitle: subrip(| \(default\)).*")
            ],
        "generic": [re.compile(".*Stream #0:(?P<trackid>[0-9]+)\(%s\): Subtitle: .*" % lang)]
    }

    raw_output_probe = sp.check_output([ffprobe, file], stderr=sp.STDOUT)
    output_probe = raw_output_probe.decode("utf-8")

    subtype, track_id_string = find_track_id(output_probe.split("\n"), track_finders, track_displacement)
    if track_id_string is None:
        print("No subtitle track found")
        return

    track_id = int(track_id_string)
    extractor = sp.Popen([mkvextract, "tracks", file, "%d:%s" % (track_id, tmpfile_name)],
                         stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    extractor.wait()
    
    tmpfile_name = half_ass(tmpfile_name)
    
    grep_cli = [grep] + grep_params + [tmpfile_name]
    try:
        raw_output_grep = sp.check_output(grep_cli)
        grep_output = raw_output_grep.decode("utf-8")

        if len(grep_output) > 0:
            print("%s:" % (file, ))
            for line in grep_output.split("\n"):
                fields = line.split(",")
                if len(fields) < 9: continue
                print("\t%s - %s : %s" % (fields[1], fields[2], ",".join(fields[9:])))
    except sp.CalledProcessError:
        if print_mismatch:
            print("%s: no match" % (file, ))
    finally:
        if os.path.isfile(tmpfile_name):
            os.remove(tmpfile_name)


main()
