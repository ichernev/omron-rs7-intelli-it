# Capture 2024.01.14 15.03.43
--- read firmware ver (1176)
--- read software ver
--- read device name

- req notify:
  - svc: ecbe3980c9a211e1b1bd0002a5d5c51b
  - char: 49123040aee811e1a74d0002a5d5c51b
  - ccc: 0x2902

- req notify:
  - svc: ecbe--
  - char: b305b680aee711e1a7300002a5d5c51b
  - ccc: 0x2902
- write:
  - svc: ecbe--
  - char: b305b680aee711e1a7300002a5d5c51b
  - value: 0200000000000000000000000000000000
- inc notif:
  - svc: ecbe--
  - char: b305b680aee711e1a7300002a5d5c51b
  - value: 8200000000000000000000000000000000
- write:
  - svc: ecbe--
  - char: b305b680aee711e1a7300002a5d5c51b
  - value: 009d76d1f8de8619bf86854417c348b974
- dis notify:
  - svc: ecbe--
  - char: b305b680aee711e1a7300002a5d5c51b
  - ccc: 0x2902

- req notify:
  - svc: ecbe--
  - char: [Characteristic UUID: 4d0bf320aee811e1a0d90002a5d5c51b]
- req notify:
  - scv: ecbe--
  - char: [Characteristic UUID: 5128ce60aee811e1b84b0002a5d5c51b]
- req notify:
  - scv: ecbe--
  - char: [Characteristic UUID: 560f1420aee811e181840002a5d5c51b]

- write: - char: [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 0800000000100018
- inc notif: - svc: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 188000000010000000940244ffffffff
- inc notif: - svc: - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: ffffffffffff005a0000000000000000

--- read device info

- write: - [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 08010002602c0047
- inc notif: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 34810002602c000e000200010002000e
- inc notif: - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: 0000000200000a4d000d000b00000000
- inc notif: - [UUID: 5128ce60aee811e1b84b0002a5d5c51b] - Value: 0000906fffff00000000000000000000
- inc notif: - [UUID: 560f1420aee811e181840002a5d5c51b] - Value: 01fe00b9000000000000000000000000


- write: - [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 080100028c100097
- inc notif: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 188100028c10a0c00003000000000118
- inc notif (1228) - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: 0f0e04055da200820000000000000000

- write: - [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 08010008601c007d
- inc notif: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 24810008601c595d984504d013630000
- inc notif: - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: 000121de434d984f04d01aa900000002
- inc notif: - [UUID: 5128ce60aee811e1b84b0002a5d5c51b] - Value: ef100011000000000000000000000000

- write: - [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 1801c002a410000e000200010002000e
- write: - [UUID: e0b8a060aee711e192f40002a5d5c51b] - Value: 000000020000006c

- inc notif: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 1881c002a410000e000200010002000e
- inc notif: - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: 00000002000000ec0000000000000000

- write - [UUID: db5b55e0aee711e1965e0002a5d5c51b] - Value: 2601c002c21e01000001000100000000
- write: - [UUID: e0b8a060aee711e192f40002a5d5c51b] - Value: 00000103a0c000030000000001180f0e
- write: - [UUID: 0ae12b00aee811e1a1920002a5d5c51b] - Value: 1d055dbb00bf
- inc notif: - [UUID: 49123040aee811e1a74d0002a5d5c51b] - Value: 2681c002c21e01000001000100000000
- inc notif: - [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] - Value: 00000103a0c000030000000001180f0e
- inc notif: - [UUID: 5128ce60aee811e1b84b0002a5d5c51b] - Value: 1d055dbb003f00000000000000000000

- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 080f000000000007
- inc notify: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 088f0000000000870000000000000000

# Log hci_snoop20240114175712.cfa (no new data, user 2 selected)

- req not: [Characteristic UUID: 49123040aee811e1a74d0002a5d5c51b]
- req not: [Characteristic UUID: b305b680aee711e1a7300002a5d5c51b]
- write: [UUID: b305b680aee711e1a7300002a5d5c51b] Value: 0200000000000000000000000000000000
- not: [UUID: b305b680aee711e1a7300002a5d5c51b] Value: 8200000000000000000000000000000000
- write: [UUID: b305b680aee711e1a7300002a5d5c51b] Value: 019d76d1f8de8619bf86854417c348b974
- not: [UUID: b305b680aee711e1a7300002a5d5c51b] Value: 8100000000000000000000000000000000
- dis not: [Characteristic UUID: b305b680aee711e1a7300002a5d5c51b]
- req not: [Characteristic UUID: 4d0bf320aee811e1a0d90002a5d5c51b]
- req not: [Characteristic UUID: 5128ce60aee811e1b84b0002a5d5c51b]
- req not: [Characteristic UUID: 560f1420aee811e181840002a5d5c51b]
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 0800000000100018
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 188000000010000000940244ffffffff
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: ffffffffffff005a0000000000000000
--- read device id
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 08010002602c0047
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 34810002602c800f800300028000000f
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 8000000380000a4d000d000b00000000
- not: [UUID: 5128ce60aee811e1b84b0002a5d5c51b] Value: 0000906f010000010003000000000000
- not: [UUID: 560f1420aee811e181840002a5d5c51b] Value: fa05003b000000000000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 080100028c100097
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 188100028c10a0c00003000000000118
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 110e193813ec00bc0000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 1801c002a410800f800300028000000f
- write: [UUID: e0b8a060aee711e192f40002a5d5c51b] Value: 80000003800000ed
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 1881c002a410800f800300028000000f
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 800000038000006d0000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 2601c002c21e01000001000500000000
- write: [UUID: e0b8a060aee711e192f40002a5d5c51b] Value: 0000fa07a0c00003000000000118110e
- write: [UUID: 0ae12b00aee811e1a1920002a5d5c51b] Value: 1b3813ee007a
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 2681c002c21e01000001000500000000
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 0000fa07a0c00003000000000118110e
- not: [UUID: 5128ce60aee811e1b84b0002a5d5c51b] Value: 1b3813ee00fa00000000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 080f000000000007
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 088f0000000000870000000000000000

# Log hci_snoop20240114175613.cfa (no new data, user 1 selected)

- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 08010002602c0047
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 34810002602c800f800300028000000f
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 8000000380000a4d000d000b00000000
- not: [UUID: 5128ce60aee811e1b84b0002a5d5c51b] Value: 0000906f010000010003000000000000
- not: [UUID: 560f1420aee811e181840002a5d5c51b] Value: fa05003b000000000000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 080100028c100097
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 188100028c10a0c00003000000000118
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 110e193813ec00bc0000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 1801c002a410800f800300028000000f
- write: [UUID: e0b8a060aee711e192f40002a5d5c51b] Value: 80000003800000ed
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 1881c002a410800f800300028000000f
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 800000038000006d0000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 2601c002c21e01000001000500000000
- write: [UUID: e0b8a060aee711e192f40002a5d5c51b] Value: 0000fa07a0c00003000000000118110e
- write: [UUID: 0ae12b00aee811e1a1920002a5d5c51b] Value: 1b3813ee007a
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 2681c002c21e01000001000500000000
- not: [UUID: 4d0bf320aee811e1a0d90002a5d5c51b] Value: 0000fa07a0c00003000000000118110e
- not: [UUID: 5128ce60aee811e1b84b0002a5d5c51b] Value: 1b3813ee00fa00000000000000000000
- write: [UUID: db5b55e0aee711e1965e0002a5d5c51b] Value: 080f000000000007
- not: [UUID: 49123040aee811e1a74d0002a5d5c51b] Value: 088f0000000000870000000000000000

# readings
- 00 initial? -- has 3 in history
- 01 empty
- 02 empty
- 03 "114|64|77 13:58 jan 15"
- 04 "113|83|66 00:32 jan 16"
- 05 4 empty

# Findings

- The first byte of every message is the length in bytes
- the last byte is a simple xor checksum of the reset of the message
- writes (to dev) have first byte 01
- reads (from dev) have first byte 81
- req bytes from 5-8 are echoed in response
- when writing more than one 16-byte word, all except the last write
  are confirmed (i.e write req+write resp)
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
