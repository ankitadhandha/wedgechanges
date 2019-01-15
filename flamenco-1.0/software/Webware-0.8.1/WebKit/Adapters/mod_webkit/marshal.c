
/* marshal.c */
/* author: Jay Love (jsliv@jslove.org) */
/* Adapted from marshal.c in the python distribution */
/* This file handles the creation of python marshal structures. */



#include <string.h>
#include "mod_webkit.h"



/*
#define w_byte(c, p) if ((p)->ptr != (p)->end) *(p)->ptr++ = (c); \
			   else w_more(c, p)
*/


WFILE* new_item()
{
		WFILE* wf;
}
		


char* expand_memory(WFILE* p, long add)
{
		char* newptr;
		long currsize;
		long newsize = 0;
		char log_msg[500];
		
		//log_message("Expanding Memory",p->r);

		currsize = p->end - p->str;
		if (add == 0) add = 4096;

		newsize = currsize + add;
		
		//sprintf(log_msg,"Expanding Memory from %i to %i", currsize, newsize);
		//log_message(log_msg, p->r);
		newptr = ap_pcalloc(p->r->pool, newsize);
		//if !newptr  //need a check here 

		memcpy( newptr, p->str, currsize);
		p->end = newptr + newsize;
		p->ptr = newptr + (p->ptr - p->str);
		p->str = newptr;

		//log_message("Memory Expanded", p->r);
		return newptr;
}




void
insert_data(WFILE* dest, WFILE* src) {

		long src_len, dest_avail, len_need;
		char logmsg[500];
		
		//log_message("inserting data", dest->r);

		src_len = src->ptr - src->str;
		dest_avail = dest->end - dest->ptr;
		len_need = src_len - dest_avail;
		if (len_need > 0) {  // potential off by one here
				expand_memory(dest, len_need+2);
		}
		memcpy(dest->ptr, src->str, src_len);
		dest->ptr = dest->ptr + src_len;
		//log_message("done inserting data", dest->r);
		
}



void
w_more(c, p)
	char c;
	WFILE *p;
{
	int size, newsize;
	char* newptr;

//	log_message("In w_more", p->r);
	if (p->str == NULL)
		return; /* An error already occurred, we're screwed */

	expand_memory(p, 0);
	*p->ptr++ = c;
}


void w_byte(char c, WFILE* p) {
if ((p)->ptr != (p)->end) 
		*(p)->ptr++ = (c);
else w_more(c, p);
}



void
w_string(s, n, p)
	char *s;
	int n;
	WFILE *p;
{
//		log_message("In w_string", p->r);
		while (--n >= 0) {
			w_byte(*s, p);
			s++;
   		}
}

void
w_short(x, p)
	int x;
	WFILE *p;
{
	w_byte( x      & 0xff, p);
	w_byte((x>> 8) & 0xff, p);
}

void
w_long(x, p)
	long x;
	WFILE *p;
{
	w_byte((int)( x      & 0xff), p);
	w_byte((int)((x>> 8) & 0xff), p);
	w_byte((int)((x>>16) & 0xff), p);
	w_byte((int)((x>>24) & 0xff), p);
}

#if SIZEOF_LONG > 4
void
w_long64(x, p)
	long x;
	WFILE *p;
{
	w_long(x, p);
	w_long(x>>32, p);
}
#endif


void
write_string( char* s, long len, WFILE* p){

		w_byte(TYPE_STRING, p);
		w_long(len, p);
		if (len > 0)
				w_string( s, len, p);
		//log_message(s,p->r);
}

void
write_integer(int number, WFILE* wf) {
		long x,y;
		x = (long)number;
#if SIZEOF_LONG > 4
		long y = x>>31;
		if (y && y != -1) {
			w_byte(TYPE_INT64, wf);
			w_long64(x, wf);
		}
		else
#endif
			{
			w_byte(TYPE_INT, wf);
			w_long(x, wf);
		}
}





