CLASSPATH=.:../software/lucene-1.2.jar:../software/mm.mysql-2.0.14-bin.jar
JAVAC=javac -classpath $(CLASSPATH)

all: Index.class Search.class

clean:
	rm *.class

Index.class: Index.java
	$(JAVAC) Index.java

Search.class: Search.java
	$(JAVAC) Search.java
