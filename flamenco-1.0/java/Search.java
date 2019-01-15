// Copyright (c) 2004-2006 The Regents of the University of California.


// Text pipe interface to Lucene (Ka-Ping Yee <ping@zesty.ca>, 31 July 2002)
//
// Run this program with a single argument giving the path to the index.
// Give queries (in Lucene format) on stdin; results will appear on stdout.
// Each result will be prefixed by a single status line starting with
// either "+" (okay) or "-" (error).  On a successful query, the status
// line gives the number of results.  All the ids of the result set are
// then printed on a single line, separated by spaces.

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.io.IOException;
import java.io.PrintStream;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.queryParser.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Searcher;
import org.apache.lucene.search.Hits;
import org.apache.lucene.search.Query;

public class Search {
    BufferedReader input;
    PrintStream output;
    String pathname;
    Searcher searcher;
    Analyzer analyzer;

    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.out.println("-ERR no index directory specified");
            return;
        }

        new Search(args[0]).run();
    }

    public Search(String pathname) {
        input = new BufferedReader(new InputStreamReader(System.in));
        output = new PrintStream(System.out, true);
        this.pathname = pathname;
    }

    public void okay() {
        output.println("+OK");
    }

    public void okay(String message) {
        output.println("+OK " + message);
    }

    public void error(Exception ex) {
        String name = ex.getClass().getName();
        String message = ex.getMessage().replace('\n', ' ');
        output.println("-ERR " + name + ": " + message);
    }

    public void run() throws IOException {
        try {
            searcher = new IndexSearcher(pathname);
            analyzer = new StandardAnalyzer();
        } catch (Exception ex) {
            error(ex);
            return;
        }

        okay();

        String line = "";
        String[] ids = null;
        int count = 0;
        while ((line = input.readLine()) != null) {
            try {
                Query query = QueryParser.parse(line, "all", analyzer);
                Hits hits = searcher.search(query);
                count = hits.length();
                ids = new String[count];
                for (int i = 0; i < count; i++) {
                    ids[i] = hits.doc(i).get("item");
                }
            } catch (Exception ex) {
                error(ex);
                continue;
            }

            okay("" + count);
            for (int i = 0; i < count; i++) {
                if (i > 0) output.print(" " + ids[i]);
                else output.print(ids[i]);
            }
            output.println();
        }
    }
}
