import re
import requests
import os.path
import datetime
import unicodedata
import TOOLS.prettytime as prettytime
import TOOLS.Config as cfg
import urlparse, urllib

def print_verbose(message):
    if cfg.VERBOSE:
        print message

class Post(object):
    def __init__(self,post,tempdir,main_window,connection,userno=None,reply=False):
        """ post        Post data
            tempdir     Directory for downloaded images
            main_window Reference to main window
            connection  server connection from connection.py
            userno      Number of user in post
            reply       Flag if this is an original post (False) or a reply (True)"""

        self.post = post
        self.id = post.get('post_id')
        self.tempdir = tempdir
        self.main_window = main_window
        self.connection = connection
        self.reply = reply

        if reply:
            print_verbose("Handling comment " + post['post_id'])
            if post['user_handle'] == "oj":
                self.by_oj = True
                self.replier = 0
            else:
                self.replier = post['replier']
        else:
            print_verbose("Handling post " + post['post_id'])

        # create color hex code
        self.color = '#' + post['color']
        if not self.color:
            self.color = None

        image_url = post.get('image_url')
        if (image_url is None):
            pass
        elif not cfg.DBG_NO_IMAGES:
            # Download the image into the temp folder (if not yet downloaded)
            image_headers = post.get('image_headers')
            path = os.path.join(self.tempdir, post['post_id'] + ".jpg")
            if not (os.path.exists(path) and os.path.isfile(path)):
                print_verbose("Downloading image https:" + image_url + "... ")
                try:
                    with open(path, 'wb') as handle:
                        if (image_headers is not None):
                            r = connection.imgsession.request('GET', 'https:' + image_url, headers=image_headers)
                        else:
                            r = connection.imgsession.request('GET', 'https:' + image_url)

                        if not r.ok:
                            print_verbose("Could not get image.")

                        for block in r.iter_content(1024):
                            handle.write(block)

                except requests.exceptions.ConnectionError as e:
                    print "failed: " + str(e)
            self.image_url = image_url

        #self.save_post()
        if cfg.DEBUG:
            print post
        self.get_data()

    def get_data(self):
        self.named_distance = named_distance(self.post['distance'])
        date = datetime.datetime.strptime(self.post['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        self.date = date.strftime('%Y-%m-%d at %H:%M:%S')
        #self.time_delta = prettytime.pretty(self.post['created_at'])

    def get_hashtags(self):
        hashtags = re.findall(r"#(\w+)", self.post['message'])
        print_verbose("Found hashtags " + str(hashtags))
        if hashtags:
            return hashtags
        else:
            return None

    def update(self, new_post):
        self.post = new_post
        return True

    def save_post(self):
        """ Saves post in CSV file """
        filename = self.tempdir + '\posts_' + self.connection.get_location_string() + '.csv'

        if os.path.isfile(filename) is not False:
            # write to file
            with open(filename, 'ab') as f:
                pickle.dump(self.post, f)
                # do this with csv files
        else:
            f = open(filename,'w+')
        try:
            for line in f:
                print line
        except:
            print "File empty!"
            print self.post

        print_verbose("Saving post " + self.post['post_id'] + " to " + filename)

    def print_post(self):
        date = datetime.datetime.strptime(self.post['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        date = date.strftime('%Y-%m-%d at %H:%M:%S')
        print ""
        print " ######## VOTES: "+str(self.post['vote_count'])+" #### DISTANCE: "+named_distance(self.post['distance'])+" #### CREATED AT: "+date+" ########"
        print unicodedata.normalize('NFKD', self.post['message']).encode('ascii', 'ignore') + "\n\n"


def named_distance(distance):
    if (distance < 2):
        return "very near"
    elif (distance < 15):
        return "near"
    else:
        return "remote"
