all: nobel.txt
	./makefacets

nobel.txt:
	./getnobel

clean:
	rm -f items.tsv text.tsv
	for facet in gender country affiliation prize year; do \
		rm -f $${facet}_terms.tsv $${facet}_map.tsv; \
	done
