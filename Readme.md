# About

I'm working with this [omron rs7 intelli it](https://www.manualslib.com/manual/2996174/Omron-Rs7-Intelli-It.html)

I have this blood pressure monitor, and it has BT capability to sync data with
app. Omron's app is not bad, but it requires account, syncing with cloud might
share data etc etc.

Why? Because I ... can? Lets find out!

# Setup

- I used android omron connect app
- capture bluetooth via HCI snoop support in dev options
- extract the snoops via adb bugreport (keeps last 2 traces)
- turn on BT, do something turn it off -- this ensures the trace is more
  manageable
- the app has a sync button, that is sometimes auto-activated on startup

- use wireshark to open the snoop bt traces
- merge the original log + the new log so the bt handles are resolved
- use wireshark json export feature for further processing
- human.py gets the json export and writes the data in a format easier to
  reason (in `parsed/*.txt`)
- then I use meld (gui diff) to compare the traces from one run to the other

# readings

NOTE: Even when performing an empty sync (i.e no new data), there is still some
data exchanged between the devices, which is not exactly the same, so I first
set out to figoure out what that is to set the stage for actual "measurement"
transfer.

- 00 initial (during first pair+sync)? -- has 3 in history, but not sure
  whether they came in here or later, the app was a bit buggy at first (or
  I hadn't figured it out yet)
- 01 empty -- an empty sync (i.e sync with no new data), device had toggle on
  other user
- 02 empty -- same, but the device had toggle on the right (no2) user
- 03 "114|64|77 13:58 jan 15"
- 04 "113|83|66 00:32 jan 16"
- 05 4 empty (split into a b c d)
- 06 4 measuremnts (one correspondence)
  - 118 76 76 17:03 jan 17
  - 120 77 73 17:04 jan 17 (low error)
  - 89 50 74  17:06 jan 17 (high error)
  - 111 73 79 17:07 jan 17
- 07 2 meas (in one trans): 20240120185324
  - 117 83 71 18:46 jan 20
  - 125 76 70 18:47 jan 20
  - synced at 18:53 (+5min) jan 20
- 08 empty: 20240120185628
  - synced at 18:56 (+3min) jan 20

# Findings

The communication is in the form of input message (var len) followed by output
message (var len). This is shoehorned in BTLE by using a few
write-only-characteristics for writing the input message (16 bytes at a time),
and a few read/notify-only-characteristics that host receives notifies - the
output message.

From now on I'm focusing on understanding the input/output messages themselves.

- The first byte of every message is the length in bytes
- the last byte is a simple xor checksum of the reset of the message
- writes (to dev) have first byte (after len) 01
- reads (from dev) have first byte (after len) 81
- req bytes from 5-8 are echoed in response
- when writing more than one 16-byte word, all except the last write
  are confirmed (i.e write req+write resp -- visible as Write (vs lower-cased
  write) in parsed)
- M3 is echoed back verbatim (sans 01->81 and checksum)

## M1-M3

Kind of transaction, current state (iter) is first read in M1, then
in M3 it is confirmed that the state is read, the device echos it back.

    [M1-o] 0b f2 0d --> [M3-io] 0d f2 0f
    [M1-o] 0d f0 0f --> [M3-io] 0f f0 11
    [M1-o] 0f ee 11 --> [M3-io] 11 ee 13
    [M1-o] 11 ec 13 --> [M3-io] 13 ec 15

The second part of (f20d) that is going in both directions, is probably
an inner checksum.

## M2

Only some stuff at the back is changing (before checksum)

    37:2f:0d:f2 -?
    05:30:3e:c1
    0e:30:35:ca
    17:30:2c:d3

the first byte increases with 9, last 2 bytes (u16) decrease with 2295, which
is -9 mod 256

## M0 08:01:00:02:60:2c:00:47

The answer is kinda long:

    [5d: empty]
    34:81:00:02:60:2c:80:0f:80:05:00:02:80:00:00:0f:
                              last

    80:00:00:05:80:00:0a:4d:00:0d:00:0b:00:00:00:00:


    00:00:90:6f:01:00:00:01:00:11:00:00:00:00:00:00:
                               ??

    ec:13:00:29

    [7: 4 measurements]
                               __       _____
    34:81:00:02:60:2c:80:0f:80:09:00:02:00:04:00:0f:
                              last        pend
             __
    80:00:00:09:80:00:0a:4d:00:0d:00:0b:00:00:00:00:
            last
                               __
    00:00:90:6f:01:00:00:01:00:13:00:00:00:00:00:00:
                               ??
    _____
    ea:15:00:af
     cs

    checksum inside package sums up to 255 (0xEA+0x15), but not sure how is it
    computed.

## M1 08:01:00:02:8c:10:00:97

    [5d: empty]

    18:81:00:02:8c:10:a0:c0:00:03:00:00:00:00:01:18:
                                              ?????

    00:10:17:30:2c:d3:00:b5
    ?????????????????

    [7: 4 meas]

    18:81:00:02:8c:10:a0:c0:00:03:00:00:00:00:01:18:
                                              ?????

    11:11:35:08:24:db:00:bf
    ?????????????????

Not sure what this is, but it is "written back" in M3 with minor corrections.


## Device memory read (blood pressure measurement)

The message is in response to 08:01:00:08:XX:YY:00:CS request.
Where XX is the start memory offset, and YY is the length (0e ~ 14 for one
measurement, or a multiple for more).

    Response
                start                                   pos
                |   .-len                               | cs-cs
    16:81:00:08:8a:0e:41:59:58:4d:05:ed:1e:94:00:00:00:04:18:e7:00:8f
                      -----------------------------------------    -> 14 bytes

     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19    -> position
                     dia   flags  -----------         cs1          -> decimal
                        sys   pulse    ts                cs2
    sys = b[7] + 25
    dia = b[6]
    pulse = b[9]

    b[8]: flags

    01011000 -- standard measurement
    11011000 -- device too low
    10011000 -- device too high

    b[10:14] look like timestamp, for multiple measurements in same transaction
             it seems reasonble, but across transactions it's too off

    # two byte checksum
    b[18] = 255 - b[19]
    b[19] = sum(b[6:18]) % 256


Also the second write-respond request 26:01:c0:02:c2:1e:01 is longer when there
is a measurement reported.

## M2 18:01:c0:02:a4:10

This message is echoed back from the device, I assume it's a write.
(It is actually M3 when data is read, but let's keep it M2 for now).

    [5d: empty]
                     |-
    18:01:c0:02:a4:10:80:0f:80:05:00:02:80:00:00:0f:
                              last
                    -|
    80:00:00:05:80:00:00:ed
            last

    [7: 4 meas]
                     |-        __
    18:01:c0:02:a4:10:80:0f:80:09:00:02:80:00:00:0f:
                              last
             __     -|
    80:00:00:09:80:00:00:ed
            last


## M3 18:01:c0:02:c2:XX

I guess c0:02 is write comman and the next two bytes are pos+len

    [4: 1 meas]
                     |->
    26:81:c0:02:c2:1e:01:00:00:01:00:0b:00:00:00:00:
                   len               ??
             --|--
    00:00:f4:0d:a0:c0:00:03:00:00:00:00:01:18:00:10:
           cs1
             --|
    14:22:3e:c2:00:eb

    [5d: empty]
                     |->
    16:01:c0:02:c2:0e:01:00:00:01:00:13:00:00:00:00:
                   len               ??
             <-|
    00:00:ec:15:00:f3
           cs1

    [7: 4 meas]
                     |->
    26:81:c0:02:c2:1e:01:00:00:01:00:15:00:00:00:00:
                   len               ??

             --|--
    00:00:ea:17:a0:c0:00:03:00:00:00:00:01:18:11:11:
           cs1
             <-|
    38:08:24:de:00:e1


cs1 sums up to 257
cs1[1] is iter + 2?

This is in the second part of the message, only present when data was read.

               M1                  M3 (second part)
                VV       ZZ                VV       ZZ
    01:18:11:0e:19:38:13:ec -> 01:18:11:0e:1b:38:13:ee     ->    1 VVd:2 ZZ:2
    01:18:11:0e:14:39:17:e8 -> 01:18:11:0e:15:39:17:e9     ->    2 VVd:1 ZZ:1
    01:18:0d:0f:38:3b:f4:0b -> 01:18:0d:0f:39:3b:f4:0c     ->    3 VVd:1 ZZ:1
    01:18:00:10:13:22:3e:c1 -> 01:18:00:10:14:22:3e:c2     ->    4 VVd:1 ZZ:1
    01:18:00:10:37:2f:0d:f2
    01:18:00:10:05:30:3e:c1
    01:18:00:10:0e:30:35:ca
    01:18:00:10:17:30:2c:d3
    01:18:11:11:35:08:24:db -> 01:18:11:11:38:08:24:de     ->    7 VVd:3 ZZ:3

Most of the message is the same as the one read from M1, then col 4 changes by
a different amount (related to number of read entries?), and the last one
changes by the same amount (checksum?).
