#!/usr/bin/python3

import os
import pinboard
from urllib.parse import urlparse
from datetime import datetime
from dateutil import tz

# Added to avoid
# urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1056)>
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
#

pb = pinboard.Pinboard(os.environ['PINBOARD_API'])
index = {}

def make_post(p, timestamp):

    url_parts = urlparse(p.url)

    # Use the Pinboard tags to identiy the type of link
    if '_brief' in p.tags or len(p.extended) == 0:
        link_type = 'BriefLink'
    elif '_feature' in p.tags:
        link_type = 'FeatureLink'
    elif '_local' in p.tags:
        link_type = 'LocalLink'
    else:
        link_type = 'NormalLink'

    # Some links have archives of the original article attached in the body.
    # We will attempt to ignore those where we can.
    if (len(p.extended) > 1024) and (link_type == "NormalLink") and (timestamp.year < 2017):
        my_body = ''
        print("WARNING: Ignoring long body, %d characters long." % len(p.extended))
        link_type = "BriefLink"
    else:
        my_body = p.extended.replace('{', '&#123;').replace('}', '&#125;')

    reverse_site=url_parts.netloc.split('.')
    reverse_site.reverse()
    reverse_name="/".join(reverse_site)

    # Put the data into our object
    data = {
        "title": p.description,
        "date": timestamp.strftime('%Y-%m-%d %H:%M:%S %z'),
        "type": link_type,
        "external-url": p.url,
        "hash": p.hash,
        "year": timestamp.strftime('%Y'),
        "month": timestamp.strftime('%m'),
        "day": timestamp.strftime('%d'),
        "host": url_parts.netloc,
        "host_index": reverse_name,
        "body": my_body
    }

    permalink = "/{year}/{month}/{day}/{hash}".format(**data)

    if url_parts.netloc not in index:
        # create new host
        index[url_parts.netloc] = []
    index[url_parts.netloc].append({"title": p.description, "link": permalink})

    return """Title: {title}
Date: {date}
Permalink: /{year}/{month}/{day}/{hash}
ExternalURL: {external-url}
Host: {host}
HostIndex: {host_index}

{body}
""".format(**data)


def make_index(site, links):
    retval = "Title: Index for {}\n".format(site)
    retval += "Menu: No\n"
    retval += "\n"

    for l in links:
        retval += "- [{}]({})\n".format(l["title"],l["link"])

    return retval


def write_file(p, timestamp):

    # Make directories
    dname = "{}".format(timestamp.strftime('Posts/%Y/%m/%d'))
    if not os.path.exists(dname):
        print("Creating %s directory" % dname)
        os.makedirs(dname)

    fname = "{}/{}.md".format(
        dname,
        p.hash)

    print("Writing %s" % fname)
    file = open(fname,"w") 
    file.write(make_post(p, timestamp))      
    file.close() 


def main():
    if 'PINBOARD_API' not in os.environ:
        print("Please set PINBOARD_API environment variable.")
        exit(1)

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Chicago')

    #pins = pb.posts.recent()['posts']
    pins = pb.posts.all()

    print("Writing Posts...")

    for p in pins:
        if p.shared and not p.toread and len(p.extended) > 0:
            # Convert date from UTC to CDT
            utc = p.time.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)

            write_file(p, central)

    print("Writing Index...")

    for site in index.keys():
        reverse_site=site.split('.')
        reverse_site.reverse()
        reverse_name="/".join(reverse_site)
        fname = "Pages/Index/{}.md".format(reverse_name)
        print("Writing %s" % fname)
        if not os.path.exists(os.path.dirname(fname)):
            os.makedirs(os.path.dirname(fname))
        file = open(fname,"w") 
        file.write(make_index(site,index[site]))
        file.close() 

    file = open("Pages/Index.md","w")
    file.write("Title: Index\n")
    file.write("Menu: Yes\n")
    file.write("\n")

    for site in index.keys():
        reverse_site=site.split('.')
        reverse_site.reverse()
        reverse_name="/".join(reverse_site)
        file.write("- [{}](/index/{})\n".format(site, reverse_name))

    file.close()


main()

