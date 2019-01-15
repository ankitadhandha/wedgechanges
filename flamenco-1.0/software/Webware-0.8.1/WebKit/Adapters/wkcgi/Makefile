
all: wkcgi

CFLAGS = -O2
COMMON = ../common

.c.o:
	$(CC) $(CFLAGS) -c $(@D)/$(<F) -o $(@D)/$(@F)


wkcgi: wkcgi.o marshal.o environ.o wkcommon.o parsecfg.o

wkcgi.o: wkcgi.c wkcgi.h

marshal.o: $(COMMON)/marshal.c $(COMMON)/marshal.h
	$(CC) $(CFLAGS) -c $(COMMON)/marshal.c

environ.o: $(COMMON)/environ.c $(COMMON)/environ.h
	$(CC) $(CFLAGS) -c $(COMMON)/environ.c

wkcommon.o: $(COMMON)/wkcommon.c $(COMMON)/wkcommon.h
	$(CC) $(CFLAGS) -c $(COMMON)/wkcommon.c

parsecfg.o: $(COMMON)/parsecfg.c
	$(CC) $(CFLAGS) -c $(COMMON)/parsecfg.c


clean:
	-rm *.o
	-rm wkcgi
