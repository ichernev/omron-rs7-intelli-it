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
- 09 11 meas: ...

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


## M0 08:01:00:02:60:2c:00:47

The answer is kinda long:

    [5d: empty]                __       _____
    34:81:00:02:60:2c:80:0f:80:05:00:02:80:00:00:0f:
                              last
             __
    80:00:00:05:80:00:0a:4d:00:0d:00:0b:00:00:00:00:


    00:00:90:6f:01:00:00:01:00:11:00:00:00:00:00:00:
                               it
    __ __
    ec:13:00:29
    xi it2

    [7: 4 measurements]
                               __       _____
    34:81:00:02:60:2c:80:0f:80:09:00:02:00:04:00:0f:
                              last        pend
             __
    80:00:00:09:80:00:0a:4d:00:0d:00:0b:00:00:00:00:
            last
                               __
    00:00:90:6f:01:00:00:01:00:13:00:00:00:00:00:00:
                               it
    _____
    ea:15:00:af
   csi it2


    csi+it2 == 255
    it2 = it + 2

Here are all the non-consts so far:

                f1 l1 f2 p  l2 f3 it
    02.M0.res   80 03 80 00 03 80 05
    03.M0.res   00 04 00 01 04 00 07
    04.M0.res   80 05 00 01 05 80 09
    05:a.M0.res 80 05 80 00 05 80 0b
    05:b.M0.res 80 05 80 00 05 80 0d
    05:c.M0.res 80 05 80 00 05 80 0f
    05:d.M0.res 80 05 80 00 05 80 11
    06.M0.res   80 09 00 04 09 80 13
    07.M0.res   00 0b 00 02 0b 00 15
    08.M0.res   00 0b 80 00 0b 00 17
    09.M0.res   00 16 00 0b 16 00 19

    f1 == f3 ?
    l1 == l2 -- the id of the last measurement
    p        -- number of pending (unread) measurements
    f2       -- 0x08 if p == 0 else 0x00
    it       -- incremented by 2


## M1 08:01:00:02:8c:10:00:97

    [5d: empty]
                                              ______
    18:81:00:02:8c:10:a0:c0:00:03:00:00:00:00:01:18:
                                                ts
    ___________ __ __
    00:10:17:30:2c:d3:00:b5
     ts-cont     x cs

    cs = sum(msg[6:0x14]) % 256

This is full device timestamp encoded in 6 bytes:
- month (1-12)
- year  (0-255) (+ 2000)
- hour  (0-23)
- day   (1-31)
- second (0-59)
- minute (0-59)

## Device memory read (blood pressure measurement)

The message is in response to 08:01:00:AA:XX:YY:00:CS request.
Where AA:XX is the start memory offset, and YY is the length (0e ~ 14 for one
measurement, or a multiple for more).

    Response
                start                                   pos
                |   .-len                               | cs-cs
    16:81:00:08:8a:0e:41:59:58:4d:05:ed:1e:94:00:00:00:04:18:e7:00:8f
                      -----------------------------------------    -> 14 bytes

     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19    -> position
                     dia   flags  ----------- fl2        cs1       -> decimal
                        sys   pulse    ts                   cs2
    sys = b[7] + 25
    dia = b[6]
    pulse = b[9]

    b[8]: flags

    01011000 -- standard measurement
    11011000 -- device too low
    10011000 -- device too high

    b[10:14] - month, date, hour, minute, second + flags
        bit 2:06 -- month (1-12)
        bit 6:11 -- date  (1-31)
        bit 11:16 -- hour (0-23)
        bit 20:26 -- min (0-59)
        bit 26:32 -- sec (0-59) -- pretty sure, will verify
        bit 19 -- 1 means cuff ok, 0 means not ok

    b[14] --> almost always 0x00, but 0x01 in 07/first, no idea

    # two byte checksum
    b[18] = 255 - b[19]
    b[19] = sum(b[6:18]) % 256


Also the second write-respond request 26:01:c0:02:c2:1e:01 is longer when there
is a measurement reported.

It looks like the start address is 08:60, and the upper bound is 0d:d8 (for 100
measurements). After it wraps over I'll have a better idea.

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

All non-cost fields

                   f1 l1 l2 f2   M0: f1 l1
    02.M2.req   10 80 03 03 80       80 03
    03.M2.req   10 00 04 04 00       00 04
    04.M2.req   10 80 05 05 80       80 05
    05:a.M2.req 10 80 05 05 80       80 05
    05:b.M2.req 10 80 05 05 80       80 05
    05:c.M2.req 10 80 05 05 80       80 05
    05:d.M2.req 10 80 05 05 80       80 05
    06.M2.req   10 80 09 09 80       80 09
    07.M2.req   10 00 0b 0b 00       00 0b
    08.M2.req   10 00 0b 0b 00       00 0b
    09.M2.req   10 00 16 16 00       00 16

    f1 == f2 == f1/f3 from M0
    l1 == l2 == l1/l2 from M0

Maybe it gets more interesting after the measurements wrap around in the
memory.

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
           x cs2

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
           x cs2

    cs1 sums up to 257
    cs1[1] is iter + 2?

    x -- from M1
    cs2 = sum(b[0x14:0x22]) % 256

This is in the second part of the message, only present when data was read.

                     ##       ##             ##       ##
      02 01:18:11:0e:14:39 17:e8 01:18:11:0e:15:39 17:e9   -> 1 | 21
      03 01:18:0d:0f:38:3b f4:0b 01:18:0d:0f:39:3b f4:0c   -> 1 | 57
      04 01:18:00:10:13:22 3e:c1 01:18:00:10:14:22 3e:c2   -> 1 | 20
    05:a 01:18:00:10:37:2f 0d:f2                                | 55
    05:b 01:18:00:10:05:30 3e:c1
    05:c 01:18:00:10:0e:30 35:ca
    05:d 01:18:00:10:17:30 2c:d3
      06 01:18:11:11:35:08 24:db 01:18:11:11:38:08 24:de   -> 3 | 53
      07 01:18:12:14:25:35 03:fc 01:18:12:14:23:35 03:fa   -> -2| 37
      08 01:18:12:14:26:38 ff:00 01:18:12:14:27:38 ff:01   -> 1 | 38
      09 01:18:0d:17:0f:13 3d:c2 01:18:0d:17:10:13 3d:c3   -> 1 | 16


      02 1 24 17 14 20 57 1 24 17 14 21 57
      03 1 24 13 15 56 59 1 24 13 15 57 59   -> 2024-01-15 13:59
      04 1 24  0 16 19 34 1 24  0 16 20 34   -> 2024-01-16 00:34
    05:a 1 24  0 16 55 47
    05:b 1 24  0 16  5 48
    05:c 1 24  0 16 14 48
    05:d 1 24  0 16 23 48
      06 1 24 17 17 53  8 1 24 17 17 56  8   -> 2024-01-17 17:08
      07 1 24 18 20 37 53 1 24 18 20 35 53   -> 2024-01-20 18:53
      08 1 24 18 20 38 56 1 24 18 20 39 56   ->
      09 1 24 13 23 15 19 1 24 13 23 16 19   -> 2024-01-23 13:19
         M yy hh dd ss mm M yy hh dd ss mm


Basically full date-time is read (the device time) and then written, so it can
be adjusted, if necessary.

All non-const (excluding cs)

                it ts                    it (M0)
    02.M3.req   07 01:18:11:0e:15:39     05
    03.M3.req   09 01:18:0d:0f:39:3b     07
    04.M3.req   0b 01:18:00:10:14:22     09
    05:a.M3.req 0d                       0b
    05:b.M3.req 0f                       0d
    05:c.M3.req 11                       0f
    05:d.M3.req 13                       11
    06.M3.req   15 01:18:11:11:38:08     13
    07.M3.req   17 01:18:12:14:23:35     15
    08.M3.req   19 01:18:12:14:27:38     17
    09.M3.req   1b 01:18:0d:17:10:13     19

    it == M0.it + 2
    ts == accurate timestamp (check M1 or above for field desc)
