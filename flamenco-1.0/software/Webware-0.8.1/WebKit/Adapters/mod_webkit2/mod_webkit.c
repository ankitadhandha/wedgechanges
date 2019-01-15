/********************************************************************
mod_webkit.c							   
Apache module for the WebKit Python Application Server	       
author: Jay Love (jsliv@jslove.org)				

This is the Apache 2.x version  
********************************************************************/



#include "mod_webkit.h"
#include "http_config.h"
#include "http_core.h"
#include "http_log.h"
#include "http_main.h"
#include "http_protocol.h"
#include "http_request.h"
#include "util_script.h"
#include "apr_buckets.h"
#include "apr_lib.h"
#include "apr_strings.h"




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
  apr_port_t port;			/* Which port is the Appserver listening on? */
  char *host; 		/* Which host is the AppServer running on? */
  unsigned long addr; 	/* resolved host address */
  apr_sockaddr_t* apraddr; /*apache2 sockaddr*/
  int retrydelay;   
  int retryattempts;
} wkcfg;


/*Use to log errors */
#define log_error(message,server) ap_log_error(APLOG_MARK, APLOG_ERR, 0, server, message)


/*
 * Declare ourselves so the configuration routines can find and know us.
 * We'll fill it in at the end of the module.
 */
module AP_MODULE_DECLARE_DATA webkit_module;




/* A quick debug logging function, only prints if LogLevel=debug */
int log_message(char* msg, request_rec* r) {
    ap_log_error(APLOG_MARK, APLOG_DEBUG, 0, r->server, msg);
    return 0;
}
//take a server_rec instead of request_rec
int log_message_s(char* msg, server_rec* s) {
    ap_log_error(APLOG_MARK, APLOG_DEBUG, 0, s, msg);
    return 0;
}





/* ================================================================== */
/*
 *  Command handler for the WKServer command.
 *  Takes 2 arguments, the host and the port of the AppServer to use.
 */
/* ================================================================= */
static const char *handle_wkserver(cmd_parms *cmd, void *mconfig,
				   const char *word1, const char *word2)
{
    wkcfg* cfg;
    apr_sockaddr_t *apraddr;
    apr_status_t err;

    cfg = (wkcfg *) mconfig;
    
    if (word1 != NULL) cfg->host = (char*)word1;
    if (word2 != NULL) cfg->port = atoi(word2);
    err = apr_sockaddr_info_get(&apraddr, (char*)apr_pstrdup(cmd->server->process->pool, cfg->host), APR_UNSPEC, cfg->port, 0, cmd->server->process->pool);
    cfg->apraddr = apraddr;
    if (err !=APR_SUCCESS) log_error("Couldn't resolve hostname for WebKit Server", cmd->server);
    return NULL;
}


/* ================================================================== */
/*
 *  Command handler for the WKServer command.
 *  Takes 1 argument, the number of attempts to make to connect to the appserver.
 */
/* ================================================================= */
static const char *handle_maxconnectattempts(cmd_parms *cmd, void *mconfig, const char *word1)
{
    wkcfg* cfg;
    
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
static const char *handle_connectretrydelay(cmd_parms *cmd, void *mconfig, const char *word1)
{
    wkcfg* cfg;
    
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
static void *webkit_create_dir_config(apr_pool_t *p, char *dirspec)
{
    
    wkcfg *cfg;
    char *dname = dirspec;
    apr_sockaddr_t *apraddr;
    apr_status_t rv;

    

    /*
     * Allocate the space for our record from the pool supplied.
     */
    cfg = (wkcfg *) apr_pcalloc(p, sizeof(wkcfg));

    cfg->port = 8086;
    cfg->host = "localhost";
    cfg->apraddr=NULL;
    cfg->retryattempts = 10;
    cfg->retrydelay = 1;

    //    cfg->addr = resolve_host(cfg->host);

    rv=apr_sockaddr_info_get(&apraddr, cfg->host,APR_UNSPEC, cfg->port, 0, p);
    /*
     * Now fill in the defaults.  If there are any `parent' configuration
     * records, they'll get merged as part of a separate callback.
     */

    if (rv != APR_SUCCESS){
      log_message_s("couldn't resolve localhost",NULL);
    }

    cfg->apraddr=apraddr;
    return (void *) cfg;
}







/* ====================================================== */
/*  Initialize the WFILE structure
 *  This is used by the marshalling functions.
/* ======================================================= */
WFILE*	setup_WFILE(request_rec* r)
{
    WFILE* wf = NULL;
    wf = (WFILE*)apr_pcalloc(r->pool, sizeof(WFILE));
    if (wf == NULL) {
	log_message("Failed to get WFILE structure\n", r);
	return wf;
    }
    wf->str = NULL; wf->ptr = NULL; wf->end = NULL;
    wf->str = (char*)apr_pcalloc(r->pool, 4096);
    
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




/* ========================================================================= */
/* Open a socket to appserver host */
/* Taken from apache jserv.  
/*
/* ======================================================================== */
static apr_socket_t* wksock_open(request_rec *r, unsigned long address, int port, wkcfg* cfg) {
    apr_status_t rv;
    apr_socket_t *aprsock;

    //    log_message("In wksock_open",r);

    if (cfg->apraddr==NULL) {
      log_error("No Valid Host Configured",r->server);
      return NULL;
    }
     if ((rv = apr_socket_create(&aprsock, AF_INET,
                                    SOCK_STREAM, r->pool)) != APR_SUCCESS)

       {
	 log_error("Failure creating socket for appserver connection",r->server);
	return NULL;
       }

    
    /* Tries to connect to appserver (continues trying while error is EINTR) */
    do {
        rv = apr_connect(aprsock, cfg->apraddr);
	//	ret=connect(sock,(struct sockaddr *)&addr,sizeof(struct sockaddr_in));
#ifdef WIN32
	//	if (rv==SOCKET_ERROR) errno=WSAGetLastError()-WSABASEERR;
	if(rv !=APR_SUCCESS) errno=WSAGetLastError()-WSABASEERR;
#endif /* WIN32 */
    } //while (ret==-1 && (errno==EINTR || errno==EAGAIN) );
    while (rv !=APR_SUCCESS  && (errno==EINTR || errno==EAGAIN));

    /* Check if we connected */
    if (rv!=APR_SUCCESS){  //(ret==-1) {
	log_message("Can not open socket connection to WebKit AppServer",r);
	return NULL;
    }

#ifdef APR_TCP_NODELAY
    apr_socket_opt_set(aprsock, APR_TCP_NODELAY, 1);
#endif


    apr_socket_timeout_set(aprsock, r->server->timeout);

    /* Return the socket number */
    return aprsock;
}





static void discard_script_output(apr_bucket_brigade *bb)
{
    apr_bucket *e;
    const char *buf;
    apr_size_t len;
    apr_status_t rv;
    APR_BRIGADE_FOREACH(e, bb) {
        if (APR_BUCKET_IS_EOS(e)) {
            break;
        }
        rv = apr_bucket_read(e, &buf, &len, APR_BLOCK_READ);
        if (rv != APR_SUCCESS) {
            break;
        }
    }
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

    int ret;
    apr_socket_t* aprsock;
    apr_bucket_brigade *bb;
    apr_bucket *b;
    int seen_eos, appserver_stopped_reading;
    apr_status_t rv;
    apr_size_t aprlen;
    conn_rec *c = r->connection;
    const char *location;
    char sbuf[MAX_STRING_LEN];



    //    log_message("In transact_with_appserver",r);


    aprsock = wksock_open(r, cfg->addr, cfg->port, cfg);
    if (aprsock == NULL) return 1;    



    // Errors after this point mean that the
    // whole request fails -- no retry is possible.
    // That's because once we've sent the request, it's possible
    // that the appserver has already started to work on the request,
    // and we don't want to accidentally submit the same request
    // twice.

    aprlen = int_dict->ptr - int_dict->str;
    rv = apr_send(aprsock, int_dict->str, &aprlen);
    aprlen = length;
    rv = apr_send(aprsock,whole_dict->str,&aprlen);

    
    //This is copied from mod_cgi

    /* Transfer any put/post args, CERN style...
     * Note that we already ignore SIGPIPE in the core server.
     */
    bb = apr_brigade_create(r->pool, r->connection->bucket_alloc);
    seen_eos = 0;
    appserver_stopped_reading = 0;
    /*    if (conf->logname) {
        dbuf = apr_palloc(r->pool, conf->bufbytes + 1);
        dbpos = 0;
	}*/
    do {
        apr_bucket *bucket;

        rv = ap_get_brigade(r->input_filters, bb, AP_MODE_READBYTES,
                            APR_BLOCK_READ, HUGE_STRING_LEN);
       
        if (rv != APR_SUCCESS) {
            return rv;
        }

        APR_BRIGADE_FOREACH(bucket, bb) {
            const char *data;
            apr_size_t len;

            if (APR_BUCKET_IS_EOS(bucket)) {
                seen_eos = 1;
                break;
            }

            /* We can't do much with this. */
            if (APR_BUCKET_IS_FLUSH(bucket)) {
                continue;
            }

            /* If the appserver stopped, we still must read to EOS. */
            if (appserver_stopped_reading) {
                continue;
            } 

            /* read */
            apr_bucket_read(bucket, &data, &len, APR_BLOCK_READ);
            
	    do {
		aprlen=len;
		rv = apr_send(aprsock, data, &aprlen);
		len = len-aprlen;
	    } while (len >0 && rv==APR_SUCCESS);

	    if (rv != APR_SUCCESS) {
                /* silly server stopped reading, soak up remaining message */
                appserver_stopped_reading = 1;
            }
	    
        }
        apr_brigade_cleanup(bb);
    }
    while (!seen_eos);

    //end mod_cgi copy

    // @@ gtalvola 2002-12-03: I had to remove this call to shutdown
    // in order to get this to work on Windows.  I don't know why.
    //apr_shutdown(aprsock, APR_SHUTDOWN_WRITE);

    /* Handle script return... */
    b = apr_bucket_socket_create(aprsock, c->bucket_alloc);
    APR_BRIGADE_INSERT_TAIL(bb, b);
    b = apr_bucket_eos_create(c->bucket_alloc);
    APR_BRIGADE_INSERT_TAIL(bb, b);
    
    if ((ret = ap_scan_script_header_err_brigade(r, bb, sbuf)) != HTTP_OK) {
      //      return log_error("the Appserver provided an invalid response",r->server);
    }
    sprintf(sbuf,"Status: %i",r->status);
    log_message(sbuf,r);

    location = apr_table_get(r->headers_out, "Location");    
    if (location && location[0] == '/' && r->status == 200) {
      discard_script_output(bb);
      apr_brigade_destroy(bb);
      //      log_script_err(r, script_err);
      /* This redirect needs to be a GET no matter what the original
       * method was.
       */
      r->method = (char*)apr_pstrdup(r->pool, "GET");
      r->method_number = M_GET;
      
      /* We already read the message body (if any), so don't allow
       * the redirected request to think it has one.  We can ignore 
       * Transfer-Encoding, since we used REQUEST_CHUNKED_ERROR.
       */
      apr_table_unset(r->headers_in, "Content-Length");
      
      ap_internal_redirect_handler(location, r);
      return OK;
    }
    else if (location && r->status == 200) {
      /* XX Note that if a script wants to produce its own Redirect
       * body, it now has to explicitly *say* "Status: 302"
       */
      discard_script_output(bb);
      apr_brigade_destroy(bb);
      return HTTP_MOVED_TEMPORARILY;
    }
    
    ap_pass_brigade(r->output_filters, bb);
    
    apr_socket_close(aprsock);

    return 0;
}





//Here's the real content handler
static int webkit_handler(request_rec *r)
{
    
    long length;
    wkcfg *cfg;
    WFILE* env_dict=NULL;
    int i;
    char msgbuf[MAX_STRING_LEN];
    int conn_attempt = 0;
    int conn_attempt_delay = 1;
    int max_conn_attempt=10;
    WFILE* whole_dict=NULL;
    WFILE* int_dict = NULL;
    const char *value;
    const char *key;
    apr_table_entry_t *tentry;
    apr_array_header_t *array_header;



    if (strcmp(r->handler, "webkit-handler"))
        return DECLINED;

    log_message("In webkit_handler",r);

    
    cfg = NULL;
    cfg =  ap_get_module_config(r->per_dir_config, &webkit_module);
    if (cfg == NULL) {
	log_message("No cfg", r);
	cfg = (wkcfg*) webkit_create_dir_config(r->pool,"/");
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
    
    //hdr_arr = ap_table_elts(r->subprocess_env);
    array_header = (apr_array_header_t*)apr_table_elts(r->subprocess_env);
    //    elts = (table_entry *) hdr_arr->elts;
    tentry=(apr_table_entry_t*)array_header->elts;
    
    //start dictionary
    w_byte(TYPE_DICT, env_dict);
    
    
    for (i = 0; i < array_header->nelts; ++i) {
	if (!tentry[i].key)
	    continue;
	key = tentry[i].key;
	value = tentry[i].val;
	write_string(key, (long)strlen(key), env_dict);
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
    
    log_message("dictionaries built",r);



    //now we try to send it
    for( conn_attempt=1; conn_attempt<=cfg->retryattempts; conn_attempt++ ) {
	int result = transact_with_app_server(r, cfg, whole_dict, int_dict, length);
	if( result == 0 ) {
	    return OK;
	} else if( result == 2 ) {
	    log_error("error transacting with app server -- giving up.", r->server);
	    return HTTP_INTERNAL_SERVER_ERROR;
	}
	sprintf(msgbuf, "Couldn't connect to AppServer, attempt %i of %i, sleeping %i second(s)", conn_attempt, cfg->retryattempts, cfg->retrydelay);
	log_message(msgbuf, r);
	apr_sleep(cfg->retrydelay * APR_USEC_PER_SEC);
    }
    log_error("timed out trying to connect to appserver-- giving up.", r->server);
    return HTTP_INTERNAL_SERVER_ERROR;
}



static int psp_handler(request_rec *r) {

    if (strcmp(r->handler, "psp-handler"))
        return DECLINED;
    r->handler=(char*)apr_pstrdup(r->pool, "webkit-handler");
    apr_table_add(r->subprocess_env, "WK_ABSOLUTE","1");
    
    return webkit_handler(r);
}


//==========================================================
/* Initialize WebKit Module */
static int webkit_post_config(apr_pool_t *pconf, apr_pool_t *plog,
                          apr_pool_t *ptemp, server_rec *s)
{
  //static void webkit_init(server_rec *s, apr_pool_t *p) {
    
    /* Tell apache we're here */
    ap_add_version_component(ptemp, "mod_webkit2/0.5");
    return OK;
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
  AP_INIT_TAKE2(
	"WKServer",		 /* directive name */
	handle_wkserver,	    /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	"WKServer directive.  Arguments are Host and then Port"
	/* directive description */
    ),
  AP_INIT_TAKE1(
	"MaxConnectAttempts",		   /* directive name */
	handle_maxconnectattempts,	      /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	"MaxConnectAttempts directive.  One argument, giving the number of attempts to make to connect to the AppServer."
	/* directive description */
    ),
  AP_INIT_TAKE1(
	"ConnectRetryDelay",		  /* directive name */
	handle_connectretrydelay,	     /* config action routine */
	NULL,			/* argument to include in call */
	OR_OPTIONS,		/* where available, allow directory to overide if AllowOverride Options is specified */
	"ConnectRetryDelay directive.  One argument, an integer giving the number of seconds to wait before retrying a connect to an AppServer that didn't respond."
	/* directive description */
    ),    
    {NULL}
};




/*--------------------------------------------------------------------------*/
/*                                                                          */
/* Which functions are responsible for which hooks in the server.           */
/*                                                                          */
/*--------------------------------------------------------------------------*/
/* 
 * Each function our module provides to handle a particular hook is
 * specified here.  The functions are registered using 
 * ap_hook_foo(name, predecessors, successors, position)
 * where foo is the name of the hook.
 *
 * The args are as follows:
 * name         -> the name of the function to call.
 * predecessors -> a list of modules whose calls to this hook must be
 *                 invoked before this module.
 * successors   -> a list of modules whose calls to this hook must be
 *                 invoked after this module.
 * position     -> The relative position of this module.  One of
 *                 APR_HOOK_FIRST, APR_HOOK_MIDDLE, or APR_HOOK_LAST.
 *                 Most modules will use APR_HOOK_MIDDLE.  If multiple
 *                 modules use the same relative position, Apache will
 *                 determine which to call first.
 *                 If your module relies on another module to run first,
 *                 or another module running after yours, use the 
 *                 predecessors and/or successors.
 *
 * The number in brackets indicates the order in which the routine is called
 * during request processing.  Note that not all routines are necessarily
 * called (such as if a resource doesn't have access restrictions).
 * The actual delivery of content to the browser [9] is not handled by
 * a hook; see the handler declarations below.
 */

static void webkit_register_hooks(apr_pool_t *p)
{
  ap_hook_post_config(webkit_post_config,NULL,NULL,APR_HOOK_MIDDLE);
  ap_hook_handler(webkit_handler, NULL, NULL, APR_HOOK_MIDDLE);
  ap_hook_handler(psp_handler, NULL, NULL, APR_HOOK_MIDDLE);
}


/*--------------------------------------------------------------------------*/
/*                                                                          */
/* Finally, the list of callback routines and data structures that provide  */
/* the static hooks into our module from the other parts of the server.     */
/*                                                                          */
/*--------------------------------------------------------------------------*/
/* 
 * Module definition for configuration.  If a particular callback is not
 * needed, replace its routine name below with the word NULL.
 */
module AP_MODULE_DECLARE_DATA webkit_module =
{
    STANDARD20_MODULE_STUFF,
    webkit_create_dir_config,    /* per-directory config creator */
    NULL,     /* dir config merger */
    NULL, /* server config creator */
    NULL,  /* server config merger */
    webkit_cmds,                 /* command table */    
    webkit_register_hooks       /* set up other request processing hooks */
};













