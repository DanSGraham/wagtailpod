
from django.db import models
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed, Atom1Feed
from django.urls import reverse
from wagtailpod.models import PodIndexPage, PodcastPage

from podcast.utils import EscapeFriendlyXMLGenerator

#A shitty work around, but a workaround nonetheless.
def replace_apostrophe(str_to_replace):
    return str_to_replace.replace("""&#x27;""", """'""")

class iTunesFeed(Rss201rev2Feed):

    def write(self, outfile, encoding):
        try:
            handler = EscapeFriendlyXMLGenerator(outfile, encoding, short_empty_elements=True)
        except TypeError:
            handler = EscapeFriendlyXMLGenerator(outfile, encoding)

        handler.startDocument()
        handler.startElement('rss', self.rss_attributes())
        handler.startElement('channel', self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        self.endChannelElement(handler)
        handler.endElement('rss')
   
    def rss_attributes(self):
        return {
            "version": self._version,
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:itunes":u'http://www.itunes.com/dtds/podcast-1.0.dtd',
            "xmlns:content":u'http://purl.org/rss/1.0/modules/content/',
        }

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        handler.addQuickElement('copyright', self.feed['copyright'])
        handler.addQuickElement('itunes:subtitle', self.feed['subtitle'])
        handler.addQuickElement('itunes:author', self.feed['author_name'])
        handler.addQuickElement('itunes:summary', self.feed['description'], escape=False, cdata=True)

        for cat in self.feed['itunes_categories']:
            if ":" in cat:
                group = cat.split(":")[0]
                cat = cat.split(":")[1]
                handler.startElement('itunes:category', {'text':group})
                handler.addQuickElement('itunes:category', '',
                                        {'text': cat})
                handler.endElement('itunes:category')
            else:
                handler.addQuickElement('itunes:category', '',
                                        {'text': cat})
        handler.addQuickElement('itunes:explicit',
                                self.feed['itunes_explicit'])
        handler.startElement("itunes:owner", {})
        handler.addQuickElement('itunes:name', self.feed['itunes_name'])
        handler.addQuickElement('itunes:email', self.feed['itunes_email'])
        handler.endElement("itunes:owner")
        handler.addQuickElement('itunes:image', '', {'href': self.feed['itunes_image']})

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        handler.addQuickElement(u'itunes:summary', item['summary'])
        handler.addQuickElement(u'content:encoded', item['en_content'], escape=False, cdata=True)
        handler.addQuickElement(u'itunes:duration', item['duration'])
        handler.addQuickElement('itunes:author', self.feed['author_name'])
        handler.addQuickElement(u'itunes:explicit', item['itunes_explicit'])
        handler.addQuickElement(u'itunes:image', '', {'href': item['itunes_image']})


class PodcastFeed(Feed):

    try:
        podcast_feed_home = PodIndexPage.objects.live()[0]
        title = podcast_feed_home.title
        subtitle = podcast_feed_home.subtitle
        link = "https://dontcallitabookclub.com/"
        description = podcast_feed_home.description
        author_name = podcast_feed_home.author
        author_email = podcast_feed_home.author_email
        #categories = PodIndexPage.objects.live()[0].categories
        itunes_categories = ['Comedy', 'Arts:Literature']
        rel_image_url = podcast_feed_home.image.file.url
        image_url = 'http://dontcallitabookclub.com' + rel_image_url
        copyright = "Don't call it a book club. 2018"
    except:
        print ("NO PODINDEXPAGES YET")
        title = None
        subtitle = None
        link = None
        description = None
        author_name = None
        author_email = None
        itunes_categories = None
        rel_image_url = None
        image_url = None
        copyright = None

    def items(self):
        try:
            return PodcastPage.objects.live().order_by('-date')
        except:
            return None

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_author_name(self, item):
        return self.author_name

    def item_pubdate(self, item):
        return item.date

class PodcastAtomFeed(PodcastFeed):
    feed_type = Atom1Feed
    subtitle = PodcastFeed.description

class ItunesFeed(PodcastAtomFeed):
    itunes_explicit = 'yes'
    itunes_name = "DCBC"
    podcast_type = "episodic"
    feed_type = iTunesFeed 

    def feed_extra_kwargs(self, obj):
        return {
            'copyright': self.copyright,
            'itunes_name': self.itunes_name,
            'itunes_email': self.author_email,
            #'podcast_type': self.podcast_type,
            'itunes_image': self.image_url,
            'itunes_explicit': self.itunes_explicit,
            'itunes_categories': self.itunes_categories,
        }

    def item_extra_kwargs(self, item):
        if (item.audio.thumbnail):
            imageurl = "http://dontcallitabookclub.com" + item.audio.thumbnail.url
        else:
            imageurl = self.image_url
        return {
            'summary': item.description,
            'en_content': replace_apostrophe(item.description),
            'duration': str(item.audio.duration),
            'itunes_explicit': self.itunes_explicit,
            'itunes_image': imageurl,
           # 'content_encoded':item.description,
        }

    def item_enclosure_url(self, item):
        #need to get enclosure url.
        return 'http://dontcallitabookclub.com' + item.audio.url

    def item_enclosure_length(self, item):
        return str(item.audio.file.size)

    def item_enclosure_mime_type(self, item):
        return 'audio/mpeg'
