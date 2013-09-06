/*
    Copyright (C) 2010  Jens Neuhalfen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/init.h>
#include <linux/kernel.h>       /* printk() */

#include <linux/mm.h>


void my_dump_page(struct page* page, char* msg){
  if (!msg)
    msg="";

   if (page)
     printk(KERN_DEBUG "%s page #%lu: flags: %lx Count: %i, Mapcount: %i, Mapping/private/first_page/... %p. Index: %lu. lru.next: %p / prev: %p\n", msg,page_to_pfn(page), page->flags, page_count(page), page_mapcount(page), page->mapping, page->index, page->lru.next, page->lru.prev);
   else
     printk(KERN_DEBUG "%s page NULL\n", msg);

}
