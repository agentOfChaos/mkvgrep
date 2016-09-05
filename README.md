# mkvgrep
Helper script to extract a subtitle track from an .mkv, grep it, and print the results.

It makes use of the actual grep program installed on your system.

# Usage

    ./mkvgrep.py [script options] [mkv file name] [grep options]
    
Possible script options are:

* `-m` to also print filenames when no match is found
* `-t number` to select a specific subtitle track, in case more than one subtitle track is
included in the .mkv (default to 0)

All the parameters following [mkv file name] are passed as cli parameters to the grep process.

## Example

    ./mkvgrep.py some_movie.mkv -i pizza
    
Looks if someone said "pizza" (ignoring case) in some_movie

# Dependancies

The script requires some external programs in order to work:

    ffprobe
    mkvextract
    grep
