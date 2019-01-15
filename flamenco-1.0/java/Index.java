// Copyright (c) 2004-2006 The Regents of the University of California.


// Lucene indexer for Flamenco (Ka-Ping Yee <ping@zesty.ca>, 31 July 2002)
// Conforms to the Flamenco metaschema specification (see metadb.txt).
//
// Run this program with the path to an instance directory as an argument.
// The settings in the "instance.py" file in that directory will be used to
// connect to a MySQL database.  Each item in the database will be indexed
// with text fields for each facet and attribute, and with a single large
// text field named "all" containing the names of all assigned facets and
// attributes.  The index will be written to the "Lucene" subdirectory.

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.Runtime;
import java.net.URLEncoder;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.HashMap;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.IndexWriter;

public class Index {
    Connection conn;
    String path;
    String[] facets, svfacets, mvfacets, attrs;
    boolean[] multivalued;
    HashMap[] facetvalues;
    int count = 0;

    public static String unquote(String quoted) {
        int sq = quoted.indexOf('\''), dq = quoted.indexOf('"');
        if (sq < 0 && dq < 0) return "";
        int i = (sq >= 0) ? sq : dq;
        char quote = quoted.charAt(i);
        String result = "";
        for (i += 1; i < quoted.length(); i += 1) {
            if (quoted.charAt(i) == quote) break;
            if (quoted.charAt(i) == '\\') i += 1;
            result += quoted.charAt(i);
        }
        return result;
    }

    public static void usage() {
        System.err.println(
        "usage: java Index <instancedir> [<command>] [<limit>]\n" +
        "    <instancedir> is the instance directory\n" +
        "    <command> is an optional shell command that takes an item id\n" +
        "        as an argument and generates text for indexing on stdout\n" +
        "    <limit> is the maximum number of items to index (for testing)");
    }

    public static void main(String[] args)
        throws java.lang.ClassNotFoundException,
               java.io.FileNotFoundException,
               java.io.IOException,
               java.lang.IllegalAccessException,
               java.lang.InstantiationException,
               java.sql.SQLException {
        if (args.length < 1) {
            usage();
            return;
        }
        String instpath = args[0];
        String command = (args.length > 1) ? args[1] : "";
        int limit = (args.length > 2) ? Integer.parseInt(args[2]) : -1;

        // Read the instance settings from instance.py.
        String dbhost = null, dbuser = null, dbpass = null, dbname = null;
        BufferedReader reader = new BufferedReader(
            new FileReader(instpath + "/instance.py"));
        String line;
        while ((line = reader.readLine()) != null) {
             String[] parts = line.split("=", 2);
             if (parts.length < 2) continue;
             String name = parts[0].trim(), value = parts[1].trim();
             if (name.equals("DBHOST")) dbhost = unquote(value);
             if (name.equals("DBUSER")) dbuser = unquote(value);
             if (name.equals("DBPASS")) dbpass = unquote(value);
             if (name.equals("DBNAME")) dbname = unquote(value);
        }
        if (dbhost == null || dbuser == null ||
            dbpass == null || dbname == null) {
            System.err.println(
                "DBHOST, DBUSER, DBPASS, or DBNAME is missing from\n" +
                instpath + "/instance.py.");
            return;
        }

        // Establish a connection to the Flamenco database.
        System.err.println("database: mysql://" + dbhost + "/" + dbname + "\n");
        Class.forName("org.gjt.mm.mysql.Driver").newInstance();
        Connection dbconn = DriverManager.getConnection(
            "jdbc:mysql://" + dbhost +
            "/" + URLEncoder.encode(dbname, "UTF-8") +
            "?user=" + URLEncoder.encode(dbuser, "UTF-8") +
            "&password=" + URLEncoder.encode(dbpass, "UTF-8"));

        // Construct the index.
        String indexpath = instpath + "/Lucene";
        new Index(indexpath, dbconn).index(command, limit);
    }

    public Index(String path, Connection conn) {
        this.path = path;
        this.conn = conn;
    }

    public ResultSet query(String sql)
        throws java.sql.SQLException {
        java.sql.Statement stmt = conn.createStatement();
        ResultSet results = stmt.executeQuery(sql);
        results.last();
        count = results.getRow();
        results.beforeFirst();
        return results;
    }

    public String[] values(String sql, String field)
        throws java.sql.SQLException {
        ResultSet results = query(sql);
        String[] values = new String[count];
        for (int i = 0; i < count; i++) {
            results.next();
            values[i] = results.getString(field);
        }
        return values;
    }

    public String[][] tuples(String sql, String[] fields)
        throws java.sql.SQLException {
        ResultSet results = query(sql);
        String[][] tuples = new String[count][fields.length];
        for (int i = 0; i < count; i++) {
            results.next();
            for (int j = 0; j < fields.length; j++) {
                tuples[i][j] = results.getString(fields[j]);
            }
        }
        return tuples;
    }

    public String join(String[] parts, String separator) {
        String result = "";
        for (int i = 0; i < parts.length; i++) {
            if (i > 0) result += separator;
            result += parts[i];
        }
        return result;
    }

    public void getFields() throws java.sql.SQLException {
        facets = values("select ident from facets", "ident");
        multivalued = new boolean[facets.length];
        for (int i = 0; i < facets.length; i++) {
            multivalued[i] = true;
        }

        String[] fields = values("describe items", "Field");
        for (int i = 0; i < fields.length; i++) {
            String field = fields[i];
            for (int j = 0; j < facets.length; j++) {
                if (field.equals(facets[j])) {
                    multivalued[j] = false;
                }
            }
        }

        attrs = values("select ident from attrs", "ident");

        int nsingle = 0, nmulti = 0;
        for (int i = 0; i < facets.length; i++) {
            if (multivalued[i]) nmulti++;
            else nsingle++;
        }

        svfacets = new String[nsingle];
        mvfacets = new String[nmulti];
        int si = 0, mi = 0;
        for (int i = 0; i < facets.length; i++) {
            if (multivalued[i]) mvfacets[mi++] = facets[i];
            else svfacets[si++] = facets[i];
        }

        System.err.println("single-valued facets: " + join(svfacets, ", "));
        System.err.println("multi-valued facets: " + join(mvfacets, ", "));
        System.err.println("attributes: " + join(attrs, ", "));
    }

    public void getFacets() throws java.sql.SQLException {
        facetvalues = new HashMap[facets.length];
        for (int i = 0; i < facets.length; i++) {
            facetvalues[i] = new HashMap();
            ResultSet results = query("select id, name from " + facets[i]);
            while (results.next()) {
                facetvalues[i].put(
                    results.getString("id"), results.getString("name"));
            }
            System.err.println("read facet " + facets[i]);
        }
    }

    public void index(String command, int limit)
        throws java.sql.SQLException, java.io.IOException {
        getFields();
        getFacets();

        StandardAnalyzer analyzer = new StandardAnalyzer();
        IndexWriter writer = new IndexWriter(path, analyzer, true);
        writer.mergeFactor = 20;

        System.err.println("fetching items...");
        String fields = "item";
        if (attrs.length > 0) fields += ", " + join(attrs, ", ");
        if (svfacets.length > 0) fields += ", " + join(svfacets, ", ");
        ResultSet results = query("select " + fields + " from items");

        System.err.println("processing items...");
        int done = 0, total = count;
        while (results.next()) {
            String item = results.getString("item");
            Document doc = new Document();
            doc.add(Field.Keyword("item", item));

            String all = "";
            for (int i = 0; i < attrs.length; i++) {
                String value = results.getString(attrs[i]);
                if (value == null) value = "";
                doc.add(Field.UnStored(attrs[i], value));
                all += value + " / ";
            }
            for (int i = 0; i < facets.length; i++) {
                String value = "";
                if (multivalued[i]) {
                    String[] ids = values("select id from item_" + facets[i] +
                                          " where item = '" + item + "'", "id");
                    String[] values = new String[ids.length];
                    for (int j = 0; j < ids.length; j++) {
                        values[j] = (String) facetvalues[i].get(ids[j]);
                    }
                    value = join(values, " / ");
                } else {
                    String id = results.getString(facets[i]);
                    value = (String) facetvalues[i].get(id);
                }
                if (value == null) value = "";
                doc.add(Field.UnStored(facets[i], value));
                all += value + " / ";
            }

            if (command.length() > 0) {
                Runtime runtime = Runtime.getRuntime();
                Process process = runtime.exec(new String[] {command, item});
                InputStream input = process.getInputStream();
                InputStreamReader reader = new InputStreamReader(input);
                char chunk[] = new char[8192];
                StringBuffer buffer = new StringBuffer();
                while (true) {
                    int count = reader.read(chunk);
                    if (count < 0) break;
                    buffer.append(chunk, 0, count);
                }
                String text = buffer.toString();
                doc.add(Field.UnStored("text", text));
                all += text + " / ";
            }

            doc.add(Field.UnStored("all", all));
            writer.addDocument(doc);
            done++;
            if (done % 100 == 0) {
                System.err.println(
                    "indexed " + done + " of " + total + " items");
            }
            if (limit >= 0 && done >= limit) break;
        }

        System.err.println("optimizing index...");
        writer.optimize();
        System.err.println("done!");
        writer.close();
    }
}
