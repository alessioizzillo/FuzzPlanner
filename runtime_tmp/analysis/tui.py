import os
import sys
import sys
import json
import glob


fuzzing_exp = {}


def filter_by_score(data, min_score):
    res = []
    for bin in data:

        added = False
        for channel in bin['border_data_channels']:
            for resource in bin['border_data_channels'][channel]:
                score = float(bin['border_data_channels']
                              [channel][resource]['score'])
                if score >= min_score:
                    if not added or score > bin['max_score']:
                        bin['max_score'] = score

                    if not added:
                        res.append(bin)
                        added = True

    return res


def channel_kinds_and_count(bin):
    res = dict()
    for channel in bin['border_data_channels'].keys():
        if channel in ['inet6_socket', 'inet_socket']:
            c = "inet_socket"
        else:
            c = channel
        if c not in res:
            res[c] = 0
        res[c] += len(bin['border_data_channels'][channel])
    return res


def view_1A1(image, run_id, min_score):
    p = 'results/%s/dynamic_analysis/run_%d/views/phase_1A/view_1/binaries.json' % (image, run_id)
    data = json.load(open(p))
    data = filter_by_score(data, min_score)

    os.system('reset')
    print()
    print("VIEW 1A-1")
    print("MINIMUM SCORE THRESHOLD: %.2f" % min_score)
    print("NUMBER OF BINARIES: %d" % len(data))
    print()

    data = sorted(data, key=lambda x: (
        not x['is_proprietary'], -x['max_score'], x['id']))

    k = 0
    for bin in data:
        k += 1
        sys.stdout.write("%s " % ("*" if bin['id'] in fuzzing_exp else " ", ))
        sys.stdout.write("#%-2d " % k)
        sys.stdout.write("[%s] " % ("P" if bin['is_proprietary'] else " ", ))
        sys.stdout.write("[%.2f] " % (bin['max_score'], ))

        ckinds = channel_kinds_and_count(bin)
        sys.stdout.write("[%6s %6s %6s %6s %6s %6s] " % (
            "F=%d" % ckinds['file'] if 'file' in ckinds else "   ",
            "N=%d" % ckinds['inet_socket'] if 'inet_socket' in ckinds else "   ",
            "U=%d" % ckinds['unix_socket'] if 'unix_socket' in ckinds else "   ",
            "P=%d" % ckinds['pipe'] if 'pipe' in ckinds else "   ",
            "D=%d" % ckinds['device'] if 'device' in ckinds else "   ",
            "V=%d" % ckinds['virtual_file'] if 'virtual_file' in ckinds else "   ")
        )
        sys.stdout.write("%s" % bin['id'].lstrip())
        print()

    while True:
        print()
        print("Actions:")
        print("- set minimum score: s <float>")
        print("- select binary: p <id>")
        sys.stdout.write("> ")
        action = input().split(" ")
        if action[0] == 's':
            return "1A-1", float(action[1])
        elif action[0] == 'p':
            return "1A-2", data[int(action[1]) - 1]['id']


def view_1A2(image, run_id, bin, min_score):

    p = 'results/%s/dynamic_analysis/run_%d/views/phase_1A/view_2/' % (image, run_id)
    f = p + bin + '.json'

    if not os.path.exists(f):
        print("File does not exists: %s" % f)
        sys.exit(1)

    data = json.load(open(f))
    channels = filter(lambda x: float(
        x['score']) >= min_score and x['id'] != "file{path:}", data['data_channels'])
    channels = sorted(channels, key=lambda x: (
        not x['is_border'], -float(x['score']), x['kind'], x['id']))

    os.system('reset')
    print()
    print("VIEW 1A-2")
    print("ANALYZING BINARY: %s" % bin)
    print("MINIMUM SCORE THRESHOLD: %.2f" % min_score)
    print("NUMBER OF DATA CHANNELS: %d" % len(channels))
    print()

    k = 0
    for channel in channels:
        k += 1
        sys.stdout.write("%s " % (
            "*" if bin in fuzzing_exp and channel['id'] in fuzzing_exp[bin] else " ", ))
        sys.stdout.write("#%-2d [%s] %-15s  SCORE=%.2f  " % (
            k, "B" if channel['is_border'] else " ", channel['kind'], float(channel['score'])))

        sys.stdout.write("%s " % ("USED" if channel['used'] else "    ", ))

        t = "UNKNOWN"
        if channel['first_as_sink'] and channel['first_as_source']:
            t = "BOTH"
        elif channel['first_as_source']:
            t = "WRITER"
        elif channel['first_as_sink']:
            t = "READER"
        sys.stdout.write(" [%8s]" % t)

        sys.stdout.write(" [%s %s] " % (
            " %-14s" % (("AS_SINK=%2d" % channel['num_interactions_as_sink'])
                        if channel['num_interactions_as_sink'] > 0 else ""),
            "%-14s" % (("AS_SOURCE=%2d" % channel['num_interactions_as_source'])
                       if channel['num_interactions_as_source'] > 0 else "")
        ))

        sys.stdout.write(
            " %-8s" % (("BINS=%d" % (channel['num_executables'])) if channel['num_executables'] > 0 else "",))

        sys.stdout.write(" %s" % channel['id'].lstrip(
            channel['kind']).replace("path:", ""))
        print()

    while True:
        print()
        print("Actions:")
        print("- go back: b")
        print("- set minimum score: s <float>")
        print("- select binary: p <id>")
        print("- add binary/channel to fuzz queue: f <id>")
        print("- remove binary/channel to fuzz queue: f <id>")
        sys.stdout.write("> ")
        action = input().split(" ")
        if action[0] == 'b':
            return ("1A-1",)
        elif action[0] == 's':
            return "1A-2", bin, float(action[1])
        elif action[0] == 'p':
            return "1A-3", bin, channels[int(action[1]) - 1]['id']
        elif action[0] == 'f':
            if channels[int(action[1]) - 1]['is_border']:
                if bin not in fuzzing_exp:
                    fuzzing_exp[bin] = set()
                fuzzing_exp[bin].add(channels[int(action[1]) - 1]['id'])
            else:
                print("Cannot fuzz a non-border channel!")
                os.sleep(5)
            return "1A-2", bin
        elif action[0] == 'n':
            if bin in fuzzing_exp:
                if channels[int(action[1]) - 1]['id'] in fuzzing_exp[bin]:
                    fuzzing_exp[bin].remove(channels[int(action[1]) - 1]['id'])
                    if len(fuzzing_exp[bin]) == 0:
                        del fuzzing_exp[bin]
            return "1A-2", bin


def view_1A3(image, run_id, bin, channel):

    p = 'results/%s/dynamic_analysis/run_%d/views/phase_1A/view_3/' % (image, run_id)
    d = p + bin

    if not os.path.exists(d):
        print("Dir does not exists: %s" % d)
        sys.exit(1)

    f = None
    for j in glob.glob("%s/*.json" % d):
        with open(j, "r") as fp:
            data = json.load(fp)
            if data['id'] == channel:
                f = j
                break

    if f is None:
        print("Cannot find channel: %s" % channel)
        sys.exit(1)

    data = json.load(open(f))

    exs = data['executables']
    exs = sorted(exs, key = lambda ex: (-ex['is_proprietary'], ex['id']))

    os.system('reset')
    print()
    print("VIEW 1A-3")
    print("ANALYZING BINARY: %s" % bin)
    print("ANALYZING DATA CHANNEL: %s" % channel)
    print("DATA CHANNEL SCORE: %s" % data['score'])
    print("NUMBER OF INTERACTING BINARIES: %d" % len(data['executables']))
    print()

    k = 0
    for ex in exs:
        k += 1

        sys.stdout.write("[%s] " % ("P" if ex['is_proprietary'] else " ", ))
        sys.stdout.write("[%8s] " % ex['type'])

        t = "UNKNOWN"
        if ex['num_interactions_as_source'] > 0 and ex['num_interactions_as_sink'] > 0:
            t = "BOTH"
        elif ex['num_interactions_as_source'] > 0:
            t = "WRITER"
        elif ex['num_interactions_as_sink'] > 0:
            t = "READER"
        sys.stdout.write(" [%8s]" % t)
        sys.stdout.write(" N_PROCS=%-5d " % ex['num_processes'])    

        sys.stdout.write(" %s" % ex['id'])
        print()

    while True:
        print()
        print("Actions:")
        print("- go back: b")
        sys.stdout.write("> ")
        action = input().split(" ")
        if action[0] == 'b':
            return "1A-2", bin


images = {
    "DAP-2330_1.01" : 1, 
    "DSL-2740R_UK_1.01" : 0
}
if len(sys.argv) != 2 or sys.argv[1] not in images.keys():
    print("Usage: %s %s" % (sys.argv[0], images.keys()))
    sys.exit(1)

image = sys.argv[1]
run_id = images[image]

views = ["1A-1", "1A-2", "1A-3"]
view = views[0]
last_args = {views[0]: (0.0, ), views[1]: (0.0, )}
args = None

while True:
    print("Loading view: %s" % view)
    if view == views[0]:
        if args is None:
            if len(sys.argv) == 3:
                args = (float(sys.argv[2]),)
            else:
                args = tuple()

        if len(args) < 1:
            min_score = float(last_args[view][0])
        else:
            min_score = float(args[0])
            last_args[view] = args
        next = view_1A1(image, run_id, min_score)

    elif view == views[1]:
        bin = args[0]
        if len(args) < 2:
            min_score = float(last_args[view][0])
        else:
            min_score = float(args[1])
            last_args[view] = args[1:]
        next = view_1A2(image, run_id, bin, min_score)

    elif view == views[2]:
        bin = args[0]
        channel = args[1]
        next = view_1A3(image, run_id, bin, channel)

    else:
        raise NotImplementedError

    view = next[0]
    args = next[1:]

else:
    raise NotImplementedError
