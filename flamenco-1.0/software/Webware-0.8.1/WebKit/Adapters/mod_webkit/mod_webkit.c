/********************************************************************
mod_webkit.c							   
Apache module for the WebKit Python Application Server	       
author: Jay Love (jsliv@jslove.org)				

  
********************************************************************/



#include "mod_webkit.h"




/*
 * Configuration record.  Used for both per-directory and per-server
 * configuration data.
 *
 * It's perfectly reasonable to have two different structures for the two
 * different environments.  The same command handlers will be called for
 * both, though, so the handlers need to be able to tell them apart.  One
 * possibility is for both structures to start with an int which is zero for
 * one and 1 for the other.
 *
 * Note that while the per-directory and per-server configuration records are
 * available to most of the module handlers, they should be treated as
 * READ-ONLY by all except the command and merge handlers.  Sometimes handlers
 * are handed a record that applies to the current location by implication or
 * inheritance, and modifying it will change the rules for other locations.
 */
typedef struct wkcfg {
    int cmode;			/* Environment to which record applies (directory,
				 * server, or combination).
				 */
#define CONFIG_MODE_SERVER 1
#define CONFIG_MODE_DIRECTORY 2
#define CONFIG_MODE_COMBO 3	/* Shouldn't ever happen. */
    int port;			/* Which port is the Appserver listening on? */
    char *host; 		/* Which host is the AppServer running on? */
    unsigned long addr; 	/* resolved host address */
    int retrydelay;   
    int retryattempts;
} wkcfg;


/*A quick logging macro */
#define log_error(message,server) ap_log_error(APLOG_MARK, APLOG_ERR, server, message)


/*
 * Declare ourselves so the configuration routines can find and know us.
 * We'll fill it in at the end of the module.
 */

module MODULE_VAR_EXPORT webkit_module;




/* A quick logging function */
int log_message(char* msg, request_rec* r) {
    ap_log_error(APLOG_MARK, APLOG_ERR, r->server, msg);
    return 0;
}




/* ========================================================================= */
/* Returns a unsigned long representing the ip address of a string */
/* ========================================================================= */
unsigned long resolve_host(char *value) {
    int x;
    
    /* Check if we only have digits in the string */
    for (x=0; value[x]!='\0'; x++) {
	if (!isdigit(value[x]) && value[x] != '.') {
	    break;
	}
    }
    
    if (value[x] != '\0') {
	/* If we found also characters we use gethostbyname()*/
	struct hostent *host;
	
	host=gethostbyname(value);
	if (host==NULL) return 0;
	return ((struct in_addr *)host->h_addr_list[0])->s_addr;
    } else {
	/* If we found only digits we use inet_addr() */
	return inet_addr(value);
    }
    return 0;
}




/* ================================================================== */
/*
 *  Command handler for the WKServer command.
 *  Takes 2 arguments, the host and the port of the AppServer to use.
 */
/* ================================================================= */
static const char *handle_wkserver(cmd_parms *cmd, void *mconfig,
				   char *word1, char *word2)
{
    wkcfg* cfg;
    int port;
    
    cfg = (wkcfg *) mconfig;
    
    if (word1 != NULL) cfg->host = word1;
    if (word2 != NULL) cfg->port = atoi(word2);
    cfg->addr = resolve_host(cfg->host); /*Should check for an error here */
    if (cfg->addr == 0) log_error("Couldn't resolve hostname for WebKit Server", cmd->server);
    return NULL;
}


/* ================================================================== */
/*
 *  Command handler for the WKServer command.
 *  Takes 1 argument, the number of attempts to make to connect to the appserver.
 */
/* ================================================================= */
static const char *handle_maxconnectattempts(cmd_parms *cmd, void *mconfig, char *word1)
{
    wkcfg* cfg;
    int attempts;
    
    cfg = (wkcfg *) mconfig;
    
    if (word1 != NULL) cfg->retryattempts = atoi(word1);
    return NULL;
}

/* ================================================================== */
/*
 *  Command handler for the WKServer command.
 *  Takes 1 argument, the delay to wait after a failed connection attempt before retrying.
 */
/* ================================================================= */
static const char *handle_connectretrydelay(cmd_parms *cmd, void *mconfig, char *word1)
{
    wkcfg* cfg;
    int attempts;
    
    cfg = (wkcfg *) mconfig;
    
    if (word1 != NULL) cfg->retrydelay = atoi(word1);
    return NULL;
}




/*
* This function gets called to create a per-directory configuration
* record.  This will be called for the "default" server environment, and for
* each directory for which the parser finds any of our directives applicable.
* If a directory doesn't have any of our directives involved (i.e., they
* aren't in the .htaccess file, or a <Location>, <Directory>, or related
* block), this routine will *not* be called - the configuration for the
* closest ancestor is used.
*
* The return value is a pointer to the created module-specific
* structure.
*/
static void *wk_create_dir_config(pool *p, char *dirspec)
{
    
    wkcfg *cfg;
    char *dname = dirspec;
    
    /*
     * Allocate the space for our record from the pool supplied.
     */
    cfg = (wkcfg *) ap_pcalloc(p, sizeof(wkcfg));
    /*
     * Now fill in the defaults.  If there are any `parent' configuration
     * records, they'll get merged as part of a separate callback.
     */
    cfg->port = 8086;
    cfg->host = "localhost";
    cfg->addr = resolve_host(cfg->host);
    cfg->retryattempts = 10;
    cfg->retrydelay = 1;
    return (void *) cfg;
}







/* ====================================================== */
/*  Initialize the WFILE structure
 *  This is used by the marshalling functions.
/* ======================================================= */
WFILE*	setup_WFILE(request_rec* r)
{
    WFILE* wf = NULL;
    wf = ap_pcalloc(r->pool, sizeof(WFILE));
    if (wf == NULL) {
	log_message("Failed to get WFILE structure\n", r);
	return wf;
    }
    wf->str = NULL; wf->ptr = NULL; wf->end = NULL;
    wf->str = ap_pcalloc(r->pool, 4096);
    
    if (wf->str == NULL) {
	log_message("Couldn't allocate memory", r);
	return NULL;
    }
    wf->end = wf->str + 4096;
    wf->ptr = wf->str;
    wf->appool = r->pool;
    wf->r = r;
    return wf;
}


/*============================================================================ */
// Copied from Apache:The definitive guide
// This reads input from the client.
// It's a quick fix.  Input from the client needs to go directly to the appserver, 
// and not be buffered here.
//
// NOTE: This isn't used anymore
/* =============================================================== */
static int util_read(request_rec* r, char **rbuf)
{
    int rc;
    
    //	    log_message("In util_read", r);
    if ((rc = ap_setup_client_block(r, REQUEST_CHUNKED_ERROR)) != OK) {
	return rc;
    }
    
    
    if (ap_should_client_block(r)) {
	char argsbuffer[HUGE_STRING_LENGTH];
	int rsize, len_read, rpos=0;
	long length = r->remaining;
	
	*rbuf = ap_pcalloc(r->pool, length+1);
	ap_hard_timeout("util_read", r);
	while ((len_read = ap_get_client_block(r, argsbuffer, sizeof(argsbuffer))) >0 ) {
	    ap_reset_timeout(r);
	    if ((rpos + len_read) > length) {
		rsize = length - rpos;
	    }
	    else {
		rsize = len_read;
	    }
	    memcpy((char*)*rbuf + rpos, argsbuffer, rsize);
	}
	ap_kill_timeout(r);
    }
    return rc;
}








/* ========================================================================= */
/* Open a socket to appserver host */
/* Taken from apache jserv.  
/*
/* ======================================================================== */
static int wksock_open(request_rec *r, unsigned long address, int port, wkcfg* cfg) {
    struct sockaddr_in addr;
    int sock;
    int ret;
    
    /* Check if we have a valid host address */
    if (address==0) {
	log_message("cannot connect to unspecified host", r);
	return -1;
    }
    
    /* Check if we have a valid port number. */
    if (port < 1024) {
	log_message("invalid port, must be geater than 1024",r);
	//port = 8007;
    }
    addr.sin_addr.s_addr = address;
    addr.sin_port = htons(port);
    addr.sin_family = AF_INET;
    
    /* Open the socket */
    sock=ap_psocket(r->pool, AF_INET, SOCK_STREAM, 0);
    if (sock==-1) {
	return -1;
    }
    
    /* Tries to connect to appserver (continues trying while error is EINTR) */
    do {
	ret=connect(sock,(struct sockaddr *)&addr,sizeof(struct sockaddr_in));
#ifdef WIN32
	if (ret==SOCKET_ERROR) errno=WSAGetLastError()-WSABASEERR;
#endif /* WIN32 */
    } while (ret==-1 && (errno==EINTR || errno==EAGAIN) );
    
    /* Check if we connected */
    if (ret==-1) {
	log_message("Can not connect to WebKit AppServer",r);
	return -1;
    }
#ifdef TCP_NODELAY
    {
	int set = 1;
	setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, (char *)&set, 
	    sizeof(set));
    }
#endif
    
    /* Return the socket number */
    return sock;
}


//is there data available on a socket?
//stolen from apache jserv, not used right now
static int data_available(int sock) {
    fd_set fdset;
    struct timeval tv;
    int rv;
    do {
	FD_ZERO(&fdset);
	FD_SET(sock, &fdset);
	tv.tv_sec = 0;
	tv.tv_usec = 0;
	rv = ap_select(sock+1, &fdset, NULL, NULL, &tv);
    } while( rv<0 && errno == EINTR);
    return (int) (rv == 1);
}  


/*
Handles one attempt to transact with the app server.  Returns one of the following
codes:
	0 = success
	1 = failure, but ok to try again
	2 = failure, and do not try again
*/
static int transact_with_app_server(request_rec *r, wkcfg* cfg, WFILE* whole_dict, WFILE* int_dict, long length)
{
    int sock = 0;
    BUFF* buffsocket;
    long bs;
    int ret;

    ap_hard_timeout("wk_send", r);
    
    sock = wksock_open(r, cfg->addr, cfg->port, cfg);
    if (sock <= 0) return 1;    

    // Errors after this point mean that the
    // whole request fails -- no retry is possible.
    // That's because once we've sent the request, it's possible
    // that the appserver has already started to work on the request,
    // and we don't want to accidentally submit the same request
    // twice.
    
    //	log_message("creating buffsocket",r);
    buffsocket=ap_bcreate(r->pool,B_SOCKET+B_RDWR);
    
    //	log_message("push socket into fd",r);
    ap_bpushfd(buffsocket,sock,sock); //sock);
    
    /* Now we send the request to the AppServer */
    //	log_message("writing request to buff",r);
    bs = ap_bwrite(buffsocket, int_dict->str, int_dict->ptr - int_dict->str);
    bs = ap_bwrite(buffsocket,whole_dict->str,length);
    
    // Now we pump through any client input.
    if (( ret = ap_setup_client_block(r, REQUEST_CHUNKED_ERROR)) != 0)
	return 2;
    if (ap_should_client_block(r)) {
	char * buff = ap_pcalloc(r->pool, MAX_STRING_LEN);
	int n; 
	int sent = 0;
	int retry = 0;
	
	while ((n = ap_get_client_block(r, buff, MAX_STRING_LEN)) > 0) {
	    retry=0;
	    sent=0;
	    while (retry < 10) {
		sent = sent + ap_bwrite( buffsocket, buff+sent, n-sent);
		if (sent < n) {
		    retry++;
		    sleep(1);
		    log_message("Have to retry sending input to appserver",r);
		}
		else break;
		if (retry == 10) {
		    
		    
		    // AppServer stopped reading
		    // absorb any remaining input
		    while (ap_get_client_block( r, buff, MAX_STRING_LEN) > 0)
			// Dump it
			;
		    break;
		}
	    }
	}
    }
    
    
    ap_bflush(buffsocket);
    /* Done sending */
    
    //	log_message("Sent Request to client", r);
    
    //Let the AppServer know we're done
    shutdown(sock, 1);
    ap_kill_timeout(r);
    
    
    /* Now we get the response from the AppServer */
    ap_hard_timeout("wk_read",r);
    
    
    //	log_message("scanning for headers",r);
    //pull out headers
    if ((ret=ap_scan_script_header_err_buff(r, buffsocket, NULL))) {
	if( ret>=500 || ret < 0) {
	    log_message("cannot scan servlet headers ", r);
	    return 2;
	}
	
	r->status_line = NULL;
    }
    
    ap_send_http_header(r);
    
    //now we just send the reply straight to the client
    //	log_message("Sending response", r);
    
		
    length = ap_send_fb(buffsocket, r);
    //	sprintf(msgbuf, "Sent %i bytes to the client", length);
    //	log_message(msgbuf, r);
    
    
    /* Kill timeouts, close buffer and socket and return */
    ap_kill_timeout(r);
    
    //	log_message("closing buffsocket",r);
    ap_bclose(buffsocket);
    
    
    //	log_message("Done", r);
    
    return 0;
}


/*
    Here's what we need to send
    I'm gonna set the time = 0 for the time being
    dict = {
	'format': 'CGI',
	'time':   time.time(),
	'environ': env,
	'input':   myInput
    }
*/
//Here's the real content handler
static int content_handler(request_rec *r)
{
    
    long length;
    wkcfg *cfg;
    char** env;
    WFILE* env_dict=NULL;
    char* content;
    int i;
    int con_length;
    char msgbuf[MAX_STRING_LEN];
    int debugint;
    int conn_attempt = 0;
    int conn_attempt_delay = 1;
    int max_conn_attempt=10;
    WFILE* whole_dict=NULL;
    WFILE* int_dict = NULL;
    const char *value;
    const char *key;
    array_header *hdr_arr;
    table_entry *elts;
    
    
    cfg = NULL;
    cfg =  ap_get_module_config(r->per_dir_config, &webkit_module);
    if (cfg == NULL) {
	log_message("No cfg", r);
	cfg = (wkcfg*) wk_create_dir_config(r->pool,"/");
    }
    
    env_dict = setup_WFILE(r);
    whole_dict = setup_WFILE(r);
    int_dict = setup_WFILE(r);
    
    
    if (env_dict == NULL || whole_dict == NULL) {
	log_message("Couldn't allocate python data structures", r);
	return HTTP_INTERNAL_SERVER_ERROR;
    }
    
    
    
    
    ap_add_common_vars(r);
    ap_add_cgi_vars(r);
    
    
    //Build the environment dictionary
    
    hdr_arr = ap_table_elts(r->subprocess_env);
    elts = (table_entry *) hdr_arr->elts;
    
    
    //start dictionary
    w_byte(TYPE_DICT, env_dict);
    
    
    for (i = 0; i < hdr_arr->nelts; ++i) {
	if (!elts[i].key)
	    continue;
	key = elts[i].key;
	value = ap_table_get(r->subprocess_env, elts[i].key);
	write_string(key, (int) strlen(key), env_dict);
	if (value !=NULL) write_string(value, strlen(value), env_dict);
	else w_byte(TYPE_NONE, env_dict);
    }
    w_byte(TYPE_NULL, env_dict);
    //end dictionary
    //	log_message("Built env dictionary", r);
    
    
    //We can start building the full dictionary now
    w_byte(TYPE_DICT, whole_dict);
    write_string("format", 6, whole_dict); //key
    write_string("CGI", 3, whole_dict);  //value
    write_string("time", 4, whole_dict); //key
    w_byte(TYPE_INT, whole_dict);  //value
    //patch from Ken Lalonde to make the time entry useful, (who knew?? I didn't think this would work and didn't bother)
    w_long((long)time(0), whole_dict);//value
    
    write_string("environ", 7, whole_dict); //key
    
    //copy env_dict into whole_dict
    insert_data(whole_dict, env_dict);	    
    
    //that should be it
    //end dictionary
    w_byte(TYPE_NULL, whole_dict);
    
    length = whole_dict->ptr - whole_dict->str;
    
    write_integer((int)length, int_dict);
    
    //now we try to send it
    for( conn_attempt=1; conn_attempt<=cfg->retryattempts; conn_attempt++ ) {
	int result = transact_with_app_server(r, cfg, whole_dict, int_dict, length);
	if( result == 0 ) {
	    return OK;
	} else if( result == 2 ) {
	    log_message("error transacting with app server -- giving up.", r);
	    return HTTP_INTERNAL_SERVER_ERROR;
	}
	sprintf(msgbuf, "Couldn't connect to AppServer, attempt %i of %i", conn_attempt, cfg->retryattempts);
	log_message(msgbuf, r);
	sleep(cfg->retrydelay);
    }
    log_message("error transacting with app server -- giving up.", r);
    return HTTP_INTERNAL_SERVER_ERROR;
}



static int psp_handler(request_rec *r) {
    
    ap_table_add(r->subprocess_env, "WK_ABSOLUTE","1");
    
    return content_handler(r);
}


//==========================================================
/* Initialize WebKit Module */
static void wk_init(server_rec *s, pool *p) {
    int ret;
    
#if MODULE_MAGIC_NUMBER >= 19980527
    /* Tell apache we're here */
    ap_add_version_component( "mod_webkit/0.5");
#endif
    
}


/*--------------------------------------------------------------------------*/
/*									    */
/* All of the routines have been declared now.	Here's the list of	    */
/* directives specific to our module, and information about where they	    */
/* may appear and how the command parser should pass them to us for	    */
/* processing.	Note that care must be taken to ensure that there are NO    */
/* collisions of directive names between modules.			    */
/*									    */
/*--------------------------------------------------------------------------*/
/* 
* List of directives specific to our module.
*/
static const command_rec webkit_cmds[] =
{
    {
	"WKServer",		 /* directive name */
	handle_wkserver,	    /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	TAKE2,		      /* arguments */
	"WKServer directive.  Arguments are Host and then Port"
	/* directive description */
    },
    {
	"MaxConnectAttempts",		   /* directive name */
	handle_maxconnectattempts,	      /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	TAKE1,		      /* arguments */
	"MaxConnectAttempts directive.  One argument, giving the number of attempts to make to connect to the AppServer."
	/* directive description */
    },
    {
	"ConnectRetryDelay",		  /* directive name */
	handle_connectretrydelay,	     /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	TAKE1,		      /* arguments */
	"ConnectRetryDelay directive.  One argument, an integer giving the number of seconds to wait before retrying a connect to an AppServer that didn't respond."
	/* directive description */
    },
	    
    {NULL}
};




/*--------------------------------------------------------------------------*/
/*									    */
/* Now the list of content handlers available from this module. 	    */
/*									    */
/*--------------------------------------------------------------------------*/
/* 
 * List of content handlers our module supplies.  Each handler is defined by
 * two parts: a name by which it can be referenced (such as by
 * {Add,Set}Handler), and the actual routine name.  The list is terminated by
 * a NULL block, since it can be of variable length.
 *
 * Note that content-handlers are invoked on a most-specific to least-specific
 * basis; that is, a handler that is declared for "text/plain" will be
 * invoked before one that was declared for "text / *".  Note also that
 * if a content-handler returns anything except DECLINED, no other
 * content-handlers will be called.
 */
static const handler_rec webkit_handlers[] =
{
    {"webkit-handler", content_handler},
    {"psp-handler",psp_handler},
    {NULL}
};




module MODULE_VAR_EXPORT webkit_module = {
    STANDARD_MODULE_STUFF,
    wk_init,			    /* module initializer */
    wk_create_dir_config,	    /* per-directory config creator */
    NULL,			    /* dir config merger */
    NULL,			    /* server config creator */
    NULL,			    /* server config merger */
    webkit_cmds,		    /* command table */
    webkit_handlers,		    /* [7] list of handlers */
    NULL,			    /* [2] filename-to-URI translation */
    NULL,			    /* [5] check/validate user_id */
    NULL,			    /* [6] check user_id is valid *here* */
    NULL,			    /* [4] check access by host address */
    NULL,			    /* [7] MIME type checker/setter */
    NULL,			    /* [8] fixups */
    NULL,			    /* [10] logger */
    NULL,			    /* [3] header parser */
#if MODULE_MAGIC_NUMBER > 19970622
    NULL,			    /* apache child process initializer */
    NULL,			    /* apache child process exit/cleanup */
    NULL			    /* [1] post read_request handling */
#endif
};













