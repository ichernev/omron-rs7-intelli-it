# .PHONY: parse
# parse:
# 	i=0; \
# 	for f in dumps/*.json; do \
# 		ii=$$(printf %02d $$i); \
# 		python human.py $$f > parsed/$$ii.txt;  \
# 		i=$$((i+1)); \
# 	done
#
# .PHONY: parse_hex
# parse_hex:
# 	i=0; \
# 	for f in dumps/*.json; do \
# 		ii=$$(printf %02d $$i); \
# 		python human.py --hex $$f > parsed_hex/$$ii.txt;  \
# 		i=$$((i+1)); \
# 	done
#
PKT_DUMPS := $(wildcard dumps_id/*.json)
PARSED_S0 := $(patsubst dumps_id/%.json,parsed/%.txt,$(PKT_DUMPS))
PARSED_S1 := $(patsubst %.txt,%.json,$(PARSED_S0))
PARSED_S2 := $(patsubst parsed/%,parsed2/%,$(PARSED_S1))

.PHONY: all
all: parse_s0 parse_s1 parse_s2

.PHONY: parse_s0
parse_s0: $(PARSED_S0)

.PHONY: parse_s1
parse_s1: $(PARSED_S1)

.PHONY: parse_s2
parse_s2: $(PARSED_S2)


.PHONY: dump_enum
dump_enum:
	i=0; \
	for f in dumps/*.json; do \
		ii=$$(printf %02d $$i); \
		pushd dumps_id 2>&1 >/dev/null && ln -s ../$$f $$ii.json && popd 2>&1 >/dev/null; \
		i=$$((i+1)); \
	done

parsed/%.txt: dumps_id/%.json
	python human.py $^ > $@

parsed/%.json: parsed/%.txt
	python human.py $^ > $@

parsed2/%.json: parsed/%.json
	python msg_parser.py $^ > $@
