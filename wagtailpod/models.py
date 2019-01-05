from django.db import models
from django.shortcuts import render
from django.utils import timezone

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag

from wagtailaudio.edit_handlers import AudioChooserPanel

# Podcast Site Pages

# Tags are not consistenetly sorted. Need way to sort tags.

class PodIndexPage(Page):

    subtitle = models.CharField(max_length=250, default="changeme")
    author = models.CharField(max_length=250, default="Dan and Luke")
    itunes_name = models.CharField(max_length=250, default="DCBC")
    author_email = models.CharField(max_length=250, default="dcbc@dontcallitabookclub.com")
    description = RichTextField(blank=False)
    itunes_categories = ["test"]
    categories = ["test"]
    image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True, #I think this solves the default image problem. Otherwise an image would have to be loaded with the site.
        on_delete=models.SET_NULL, 
        related_name='+'
    )

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('author'),
        FieldPanel('itunes_name'),
        FieldPanel('author_email'),
        FieldPanel('description'),
        ImageChooserPanel('image'),
    ]

    subpage_types = ['pod.PodcastPage']

    def serve(self, request):

        #If notice slowdown, could add a limiter and create multiple pages.
        podcasts = PodcastPage.objects.child_of(self).live()
        print (podcasts)

        #Filter by tag
        tag = request.GET.get('tag')
        if tag:
            podcasts = podcasts.filter(tags__name=tag)

        podcasts = podcasts.order_by('-date')
        return render(request, self.template, {
            'page':self,
            'podcasts':podcasts,
        })

class PodcastPageTag(TaggedItemBase):
    content_object = ParentalKey('PodcastPage', on_delete=models.CASCADE, related_name='podcast_tags')


class PodcastPage(Page):
    date = models.DateTimeField("Post Date", default=timezone.now)
    description = RichTextField(blank=False)
    tags = ClusterTaggableManager(through=PodcastPageTag, blank=True)
    audio = models.ForeignKey(
        'wagtailaudio.Audio',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    sode_image = models.ForeignKey(
        'wagtailimages.Image', 
        null=True,
        blank=True,
        on_delete=models.SET_NULL, 
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('description'),
        index.SearchField('date'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        AudioChooserPanel('audio'),
        FieldPanel('tags'),
        FieldPanel('description'),
        ImageChooserPanel('sode_image'),
    ]

    #parent_page_types = ['pod.PodIndexPage'] #May need to add home page. Don't know if inherits.

    def get_absolute_url(self):
        return self.get_url() #Should add request
