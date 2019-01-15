
#include "httpd.h"





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
  char *str; 
  char *ptr;
  char *end;
  apr_pool_t  *appool;
  request_rec* r; //just for debugging
} WFILE;

void w_byte(int c, WFILE* p);
void w_long(long x, WFILE *p);
void write_string(const char* s, long len, WFILE* p);
void insert_data(WFILE* dest, WFILE* src);
void write_integer(int number, WFILE* wf);
int log_message(char* msg, request_rec* r);
