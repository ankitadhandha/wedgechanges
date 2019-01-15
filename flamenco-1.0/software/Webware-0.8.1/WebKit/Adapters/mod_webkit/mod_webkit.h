
#include "httpd.h"
#include "http_config.h"
#include "http_core.h"
#include "http_log.h"
#include "http_main.h"
#include "http_protocol.h"
#include "http_request.h"
#include "util_script.h"






#define HUGE_STRING_LENGTH  4096 
#define TYPE_NULL	'0'
#define TYPE_NONE	'N'
#define TYPE_ELLIPSIS   '.'
#define TYPE_INT	'i'
#define TYPE_INT64	'I'
#define TYPE_FLOAT	'f'
#define TYPE_COMPLEX	'x'
#define TYPE_LONG	'l'
#define TYPE_STRING	's'
#define TYPE_TUPLE	'('
#define TYPE_LIST	'['
#define TYPE_DICT	'{'
#define TYPE_CODE	'c'
#define TYPE_UNICODE	'u'
#define TYPE_UNKNOWN	'?'

typedef struct {
/*
/*	FILE *fp;
/*	int error;
/*	int depth;
/*	/* If fp == NULL, the following are valid: */
/*	PyObject *str;
*/

	char *str; 
	char *ptr;
	char *end;
	pool  *appool;
	request_rec* r; //just for debugging
} WFILE;


int log_message(char* msg, request_rec* r);
