from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from wagtail.core import blocks
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import StreamFieldPanel, FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.core.rich_text import get_text_for_indexing
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.contrib.settings.models import BaseSetting, register_setting

from .blocks import SocialMediaLinkBlock, SocialMediaShareButtonBlock


class HomePage(Page):
    template = 'home/section.html'

    def get_context(self, request):
        context = super().get_context(request)
        context['articles'] = self.get_descendants().type(Article)
        return context


class Section(Page):
    icon = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    icon_active = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    color = models.CharField(
        max_length=6,
        blank=True,
        null=True,
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('icon'),
        ImageChooserPanel('icon_active'),
        FieldPanel('color'),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['articles'] = self.get_children().type(Article)
        return context


class Article(Page):
    lead_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True
    )
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('list', blocks.ListBlock(blocks.CharBlock(label="Item"))),
        ('numbered_list', blocks.ListBlock(blocks.CharBlock(label="Item"))),
        ('page', blocks.PageChooserBlock()),
    ])

    def _get_child_block_values(self, block_type):
        searchable_content = []
        for block in self.body:
            if block.block_type == block_type:
                value = force_str(block.value)
                searchable_content.append(get_text_for_indexing(value))
        return searchable_content

    def get_heading_values(self):
        heading_values = self._get_child_block_values('heading')
        return '\n'.join(heading_values)

    def get_paragraph_values(self):
        paragraph_values = self._get_child_block_values('paragraph')
        return '\n'.join(paragraph_values)

    content_panels = Page.content_panels + [
        ImageChooserPanel('lead_image'),
        StreamFieldPanel('body')
    ]

    search_fields = [
        index.SearchField('get_heading_values', partial_match=True, boost=1),
        index.SearchField('get_paragraph_values', partial_match=True),
        index.SearchField('title', partial_match=True, boost=2),

        index.FilterField('live')
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context['breadcrumbs'] = [crumb for crumb in self.get_ancestors() if not crumb.is_root()]
        context['sections'] = self.get_ancestors().type(Section)
        return context

    def description(self):
        for block in self.body:
            if block.block_type == 'paragraph':
                return block
        return ''


@register_snippet
class Footer(models.Model):
    title = models.CharField(max_length=255)
    logos = StreamField([
        ('image', ImageChooserBlock(required=False))
    ], blank=True)
    navigation = StreamField([
        ('link_group', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('links', blocks.StreamBlock([
                ('page', blocks.PageChooserBlock())
            ]))
        ], required=False))
    ], blank=True)
    essential = StreamField([
        ('page', blocks.PageChooserBlock()),
    ])

    panels = [
        FieldPanel('title'),
        StreamFieldPanel('logos'),
        StreamFieldPanel('navigation'),
        StreamFieldPanel('essential'),
    ]

    def __str__(self):
        return self.title


@register_setting
class SiteSettings(BaseSetting):
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    show_only_translated_pages = models.BooleanField(
        default=False,
        help_text='When selecting this option, untranslated pages'
                  ' will not be visible to the front end user'
                  ' when viewing a child language of the site')
    fb_analytics_app_id = models.CharField(
        verbose_name=_('Facebook Analytics App ID'),
        max_length=25,
        null=True,
        blank=True,
        help_text=_(
            "The tracking ID to be used to view Facebook Analytics")
    )
    local_ga_tag_manager = models.CharField(
        verbose_name=_('Local GA Tag Manager'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            "Local GA Tag Manager tracking code (e.g GTM-XXX) to be used to "
            "view analytics on this site only")
    )
    global_ga_tag_manager = models.CharField(
        verbose_name=_('Global GA Tag Manager'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            "Global GA Tag Manager tracking code (e.g GTM-XXX) to be used"
            " to view analytics on more than one site globally")
    )
    local_ga_tracking_code = models.CharField(
        verbose_name=_('Local GA Tracking Code'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            "Local GA tracking code to be used to "
            "view analytics on this site only")
    )
    global_ga_tracking_code = models.CharField(
        verbose_name=_('Global GA Tracking Code'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_(
            "Global GA tracking code to be used"
            " to view analytics on more than one site globally")
    )
    content_rotation_start_date = models.DateTimeField(
        null=True, blank=True,
        help_text='The date rotation will begin')
    content_rotation_end_date = models.DateTimeField(
        null=True, blank=True,
        help_text='The date rotation will end')
    monday_rotation = models.BooleanField(default=False, verbose_name='Monday')
    tuesday_rotation = models.BooleanField(default=False, verbose_name='Tuesday')
    wednesday_rotation = models.BooleanField(default=False, verbose_name='Wednesday')
    thursday_rotation = models.BooleanField(default=False, verbose_name='Thursday')
    friday_rotation = models.BooleanField(default=False, verbose_name='Friday')
    saturday_rotation = models.BooleanField(default=False, verbose_name='Saturday')
    sunday_rotation = models.BooleanField(default=False, verbose_name='Sunday')
    time = StreamField([
        ('time', blocks.TimeBlock(required=False)),
    ], null=True, blank=True, help_text='The time/s content will be rotated')
    social_media_link = StreamField([
        ('social_media_link', SocialMediaLinkBlock()),
    ], null=True, blank=True)
    social_media_content_sharing_button = StreamField([
        ('social_media_content_sharing_button', SocialMediaShareButtonBlock()),
    ], null=True, blank=True)
    media_file_size_threshold = models.IntegerField(
        default=9437184, help_text='Show warning if uploaded media file size is greater than this.')
    allow_anonymous_comment = models.BooleanField(default=False)

    panels = [
        ImageChooserPanel('logo'),
        MultiFieldPanel(
            [
                FieldPanel('show_only_translated_pages'),
            ],
            heading="Multi Language",
        ),
        MultiFieldPanel(
            [
                FieldPanel('fb_analytics_app_id'),
            ],
            heading="Facebook Analytics Settings",
        ),
        MultiFieldPanel(
            [
                FieldPanel('local_ga_tag_manager'),
                FieldPanel('global_ga_tag_manager'),
            ],
            heading="GA Tag Manager Settings",
        ),
        MultiFieldPanel(
            [
                FieldPanel('local_ga_tracking_code'),
                FieldPanel('global_ga_tracking_code'),
            ],
            heading="GA Tracking Code Settings",
        ),
        MultiFieldPanel(
            [
                FieldPanel('content_rotation_start_date'),
                FieldPanel('content_rotation_end_date'),
                FieldRowPanel([
                    FieldPanel('monday_rotation', classname='col6'),
                    FieldPanel('tuesday_rotation', classname='col6'),
                    FieldPanel('wednesday_rotation', classname='col6'),
                    FieldPanel('thursday_rotation', classname='col6'),
                    FieldPanel('friday_rotation', classname='col6'),
                    FieldPanel('saturday_rotation', classname='col6'),
                    FieldPanel('sunday_rotation', classname='col6'),
                ]),
                StreamFieldPanel('time'),
            ],
            heading="Content Rotation Settings", ),
        MultiFieldPanel(
            [
                MultiFieldPanel(
                    [
                        StreamFieldPanel('social_media_link'),
                    ],
                    heading="Social Media Footer Page", ),
            ],
            heading="Social Media Page Links", ),
        MultiFieldPanel(
            [
                MultiFieldPanel(
                    [
                        StreamFieldPanel('social_media_content_sharing_button'),
                    ],
                    heading="Social Media Content Sharing Buttons", ),
            ],
            heading="Social Media Content Sharing Buttons", ),
        MultiFieldPanel(
            [
                FieldPanel('media_file_size_threshold'),
            ],
            heading="Media File Size Threshold",
        ),
        MultiFieldPanel(
            [
                FieldPanel('allow_anonymous_comment'),
            ],
            heading="Allow Anonymous Comment",
        ),
    ]
