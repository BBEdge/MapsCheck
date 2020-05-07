#!/usr/bin/env python3
import fnmatch
import re, os
import tempfile
import argparse
import zipfile
import gzip
import shutil

'''
    MAPS POLICY CHECKER 
    ARGUMENT: -i, --dinput - directory with supportsave files
    ARGUMENT: -o, --outpot - directories with result files
    EXAMPLE: mapscheck.py -i /tmp/supportsave -o /tmp/out    
'''


def extractgz(gz, fid):
    maps = []
    skip = True
    sberpolicy = False
    fid = ''.join(fid)

    with gzip.open(gz, 'rt', encoding='utf8', errors='ignore') as f:
        for line in f:
            if re.findall('Active Policy is', line):
                if re.findall('Sberbank_policy', line) and fid != 'FID128':
                    sberpolicy = True
                    maps.append(sberpolicy)
                else:
                    if re.findall('dflt_conservative_policy', line) and fid == 'FID128':
                        sberpolicy = True
                        maps.append(sberpolicy)
                    else:
                        maps.append(sberpolicy)

                maps.append(line.strip())

            if skip:
                if re.findall('MAPS Global Monitoring Configuration', line):
                    maps.append(line.strip())
                    skip = False
            else:
                maps.append(line.strip())
                if line.startswith('Decom Action Config:'):
                    skip = True

        #        print(maps)
        return maps


def writecheck(mapschkdetail, header, maps):
    with open(mapschkdetail, 'a') as ftext:
        del (maps[0])
        print(header, file=ftext)

        for mapsitem in maps:
            print(mapsitem, file=ftext)

        delimeter = '{:=>105}'.format('')
        print(delimeter, file=ftext)


def main():
    global header
#    parser = argparse.ArgumentParser(description='Process some integers.')
#    parser.add_argument('-i', '--dinput', help='directory with supportsave files', required=True)
#    parser.add_argument('-o', '--output', help='directories with result files', required=True)
#    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tempdir:
        print('The created temporary directory is %s' % tempdir)

#    dinput = args.dinput
#    output = args.output
    dinput = '/tmp/supportsave'
    output = '/tmp/out'
    try:
        os.listdir(dinput)
    except FileNotFoundError as e:
        print(e)
        exit(1)

    try:
        os.mkdir(output)
        foutput = os.path.join(output, 'MAPS_CHECK.out')
        mapschk = open(foutput, 'a')
    except Exception as e:
        print('Unable to create directory %s' %output)

    for files in os.listdir(dinput):
        if fnmatch.fnmatch(files, '*.zip'):
            zip = zipfile.ZipFile(os.path.join(dinput, files))
            f = zipfile.ZipFile.namelist(zip)
            switch = re.findall(r'(?<=\_)\w*(?=\_)', files)
            for item in f:
                fid = re.findall(r'FID\d+', item)
                if fid:
                    if re.findall(r'AMS_MAPS_LOG', item):
                        zip.extract(item, tempdir)
                        mapschkdetail = os.path.join(output, '_'.join(switch)) + '_MAPS_CHECK_DETAIL.out'
                        gz = os.path.join(tempdir, item)
                        header = (switch + fid)
                        maps = extractgz(gz, fid)

                        if maps[0]:
                            flagpass = '{:.>56}'.format('.PASS')
                            print(header, flagpass, file=mapschk)

                        else:
                            flagfail = '{:.>56}'.format('.FAIL')
                            print(header, flagfail, file=mapschk)

                        writecheck(mapschkdetail, header, maps)

    mapschk.close()

    print('See result in directory %s ' %output)

    try:
        shutil.rmtree(tempdir)
        print("Directory '%s' has been removed successfully" % tempdir)
    except OSError as e:
        print('Delete of the directory %s failed' % tempdir, e)


if __name__ == '__main__':
    main()
