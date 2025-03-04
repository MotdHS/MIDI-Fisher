import time
import random
import sys
tkinter_available = True
try:
    from tkinter import filedialog
except ImportError:
    print("Tkinter failed to load! Please install Tkinter if you want to use the GUI file picker.")
    tkinter_available = False

MThd = [77,84,104,100]
MTrk = [77,84,114,107]

print("\nMIDI Fisher v0.3.1\n")

# other ideas:
# Change all notes to the same octave
# Change all notes to the same key
# Change all notes to be a chord
# Swap note and velocity values

mode = 69420

print("""
Select from the following modes:
1. Change all notes to be an E
2. Randomize the key order
3. Flip the MIDI notes
4. Randomize the note key values
5. Randomize the note velocity values
6. Change all note velocities to 127
7. Invert the note velocity values

0. Exit
""")


while mode not in range(8):
    mode = int(input("Select a mode: "))
    if mode == 0:
        print("Exiting...")
        sys.exit()
    if mode not in range(8):
        print("Please select a number in the list!")


if tkinter_available:
    # ask for .mid, .midi, or .kar file
    print("Select a MIDI file...")
    path = filedialog.askopenfilename(title="Select a MIDI file", filetypes=[("MIDI files", "*.mid *.midi *.kar")])
    # save as .mid file
    print("Save as...")
    outpath = filedialog.asksaveasfilename(title="Save as", filetypes=[("MIDI files", "*.mid")], defaultextension=".mid")
else:
    path = input("Enter the path to the MIDI file: ")
    outpath = input("Enter the name of the output file: ")

# debug = input("Debug mode? (y/N): ")
# if debug.lower() == "y":
#     debug = True
# else:
#     debug = False

debug = False

def decode_vlq_single(a):
    return [a >> 7, a & 0b0111_1111]

def decode_vlq(a):
    result = []
    last = False
    value = 0
    for i in a:
        vlq = decode_vlq_single(i)
        result.append(vlq[1])
        if not vlq[0]:
            break
    for i in result:
        value <<= 7
        value += i
    return [value, len(result)]

outdata = []
starttime = time.perf_counter()
startime = time.perf_counter()


keys = list(range(128))
if mode == 2:
    random.shuffle(keys)
if mode == 3:
    keys = keys[::-1]


with open(path, "rb") as f:
    outdata.extend(f.read(14))
    if bytes(outdata[0:4]) != bytes(MThd):
        print("This doesn't look like a MIDI file... exiting")
        exit()
    
    tracks = int.from_bytes(outdata[10:12], "big")

    print(f"Found {tracks} tracks")
    # exit()
    for i in range(tracks):
        trackout = list(f.read(8))
        tracklen = int.from_bytes(trackout[4:8], "big")
        print(f"Track {i+1} is {tracklen} bytes long")
        track_data = f.read(tracklen)
        cpos = 0 # current position in bytes
        # print(trackout)

        active_notes = {}

        while True:
            eot = False
            towrite = []
            asdf = decode_vlq(track_data[cpos:cpos+4])
            towrite.extend(track_data[cpos:cpos+asdf[1]])
            cpos += asdf[1] # skip delta time
            event = [track_data[cpos]]
            if event[-1] > 0x7f:
                et = event[-1]
                cpos += 1
            else:
                et = pet
            # towrite += bytes(etype)

            if et == 0xff: # meta event
                if track_data[cpos] == 0x2f: # end of track
                    eot = True
                cpos += 1 # skip meta event type
                # skip by meta event length
                dt = decode_vlq(track_data[cpos:cpos+4])
                if debug: print(dt) # DEBUG OUTPUT
                event.extend(track_data[cpos-1:cpos+dt[1]])
                cpos += dt[1]
                if dt[0] != 0:
                    event.extend(track_data[cpos:cpos+dt[0]])
                    cpos += dt[0]
            if et in [0xf0, 0xf7]: # sysex event
                dt = decode_vlq(track_data[cpos:cpos+4])
                if debug: print(dt) # DEBUG OUTPUT
                event.extend(track_data[cpos:cpos+dt[1]])
                cpos += dt[1]
                if dt[0] != 0:
                    event.extend(track_data[cpos:cpos+dt[0]])
                    cpos += dt[0]

            if et >> 4 in [8, 9, 10]: # here's the fun part :D (note on/off, polyphonic aftertouch)
                if mode == 1:
                    note = int(track_data[cpos]/12) * 12 + 4 # makes every note an E
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1
                if mode in [2, 3]:
                    note = keys[track_data[cpos]] # use the note number in the keys list
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1
                if mode == 4:
                    channel = et & 0b1111
                    og_note = track_data[cpos]
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1

                    if et >> 4 == 9 and velocity != 0: # Note On
                        note = random.randint(0, 127)
                        # Store multiple Note On instances in a stack (list)
                        if (channel, og_note) not in active_notes:
                            active_notes[(channel, og_note)] = []
                        active_notes[(channel, og_note)].append(note)

                    if et >> 4 == 8 or velocity == 0: # Note Off
                        if (channel, og_note) in active_notes and active_notes[(channel, og_note)]:
                            note = active_notes[(channel, og_note)].pop(0)

                            # If stack is empty, remove entry to free memory
                            if not active_notes[(channel, og_note)]:
                                del active_notes[(channel, og_note)]
                        else:
                            note = og_note
                    
                    if et >> 4 == 10: # Polyphonic Aftertouch
                        note = random.randint(0, 127)

                if mode == 5:
                    note = track_data[cpos]
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1
                    if et >> 4 in [8, 9] and velocity != 0: # note on/off
                        velocity = random.randint(0, 127)
                if mode == 6:
                    note = track_data[cpos]
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1
                    if et >> 4 in [8, 9] and velocity != 0: # note on/off
                        velocity = 127
                if mode == 7:
                    note = track_data[cpos]
                    cpos += 1
                    velocity = track_data[cpos]
                    cpos += 1
                    if et >> 4 in [8, 9] and velocity != 0: # note on/off
                        velocity = 0 - velocity + 128

                event.extend([note, velocity])
                # print(note, velocity)
                # exit()
            
            if et >> 4 in [11, 14]: # controller, pitch bend
                event.extend(track_data[cpos:cpos+2])
                cpos += 2
            if et >> 4 in [12, 13]: # program change, channel pressure
                event.append(track_data[cpos])
                cpos += 1

            towrite.extend(event)
            if debug: print(bytes(towrite)) # DEBUG OUTPUT
            trackout.extend(towrite)
            if eot:
                break
            pet = et

            # if i == 1 and cpos > 100:
            #     exit()
            if time.perf_counter() - startime > 1:
                print(f"Track {i+1}/{tracks} | {time.perf_counter() - starttime:.3f} seconds elapsed | {cpos}/{tracklen} bytes processed ({cpos/tracklen*100:.3f}%)")
                startime = time.perf_counter()

        if debug: print(bytes(trackout)) # DEBUG OUTPUT
        print(len(trackout) - 8)
        outdata.extend(trackout)

if debug: print(bytes(outdata)) # DEBUG OUTPUT
with open(outpath, "wb") as f:
    f.write(bytes(outdata))
