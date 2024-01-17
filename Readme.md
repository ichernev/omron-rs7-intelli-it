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

## blood pressure

The message is in response to 08:01:00:08:XX:0e:00:XX request.

    16:81:00:08:8a:0e:41:59:58:4d:05:ed:1e:94:00:00:00:04:18:e7:00:8f

     0  1  2  3  4  5  6  7  8  9  -- position
                      65 89 88 77  -- decimal

    high = b[7] + b[8] - 63
    low = b[6]
    pulse = b[9]

Also the second write-respond request 26:01:c0:02:c2:1e:01 is longer when there
is a measurement reported.
