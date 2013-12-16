#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

"""This module defines the models used to persist the ngEO Browse Server 
configuration, mainly Browse Layers and Browses.

.. moduleauthor:: Stephan Meissl <stephan.meissl@eox.at>
"""

import re

from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from eoxserver.resources.coverages.models import NCNameValidator

ReferenceSystemIdentifierValidator = RegexValidator( 
    re.compile(r'^EPSG:[0-9]+$|^RAW$'),
    message="Reference system identifier must be 'RAW' or follow the pattern 'EPSG:<code>."
)
NameValidator = RegexValidator(
    re.compile(r'^[a-zA-Z_:][a-zA-Z0-9.\-_:]*$'),
    message="This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops."
)
FileNameValidator = RegexValidator(
    re.compile('^[a-zA-Z0-9-_:/.]+$'),
    message="Filenames must only contain letters, digits, hyphens, underscores, colons, slashes, or full stops."
)


class BrowseLayer(models.Model):
    """The Browse Layers are available as WMS and WMTS layers and are mapped 
    to DatasetSeries in EOxServer.
    
    Browse Layers have a unique Browse Type which is used in Browse Reports 
    to associate Browses with Browse Layers.
    
    """
    id = models.CharField("Browse Layer ID", max_length=1024, primary_key=True, validators=[NameValidator])
    browse_type = models.CharField("Browse Type", max_length=1024, unique=True, validators=[NameValidator])
    title = models.CharField(max_length=1024)
    description = models.CharField(max_length=1024, blank=True)
    browse_access_policy = models.CharField(max_length=10, default="OPEN", 
        choices = (
            ("OPEN", "Open"),
            ("RESTRICTED", "Restricted"),
            ("PRIVATE", "Private"),
        )
    )
    contains_vertical_curtains = models.BooleanField(default=False) # TODO: Fixed to False as vertical curtains are not supported for now.
    r_band = models.IntegerField(null=True, blank=True, default=None)
    g_band = models.IntegerField(null=True, blank=True, default=None)
    b_band = models.IntegerField(null=True, blank=True, default=None)
    radiometric_interval_min = models.IntegerField(null=True, blank=True, default=None)
    radiometric_interval_max = models.IntegerField(null=True, blank=True, default=None)
    grid = models.CharField(max_length=45, default="urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad", 
        choices = (
            ("urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible", "GoogleMapsCompatible using EPSG:3857"),
            ("urn:ogc:def:wkss:OGC:1.0:GoogleCRS84Quad", "GoogleCRS84Quad using EPSG:4326")
        )
    )
    highest_map_level = models.IntegerField(null=True, blank=True, default=None)
    lowest_map_level = models.IntegerField(null=True, blank=True, default=None)

    # ingestion strategy
    strategy = models.CharField(max_length=8, default="inherit",
        choices=(
            ("replace", "replace"), 
            ("merge", "merge"), 
            ("inherit", "inherit")
        )
    )

    # for mapache timedimension default
    timedimension_default = models.CharField(max_length=64)

    # for mapcache lookup query limit
    tile_query_limit = models.PositiveIntegerField()
    
    def __unicode__(self):
        return "Browse Layer '%s' with Browse Type '%s'" % (
            self.id, self.browse_type
        )
    
    class Meta:
        verbose_name = "Browse Layer"
        verbose_name_plural = "Browse Layers"
        
    def clean(self):
        # custom model validation
        if self.highest_map_level < self.lowest_map_level:
            raise ValidationError("Highest map level number must be greater "
                                  "than lowest map level number.")
        # TODO: more checks


class RelatedDataset(models.Model):
    """The Browse Layer configuration contains Related Datasets.
    
    Note that this information is no needed by the Browse Server but stored 
    for completeness.
    
    """
    dataset_id = models.CharField(max_length=1024, unique=True, validators=[NameValidator])
    browse_layer = models.ForeignKey(BrowseLayer, related_name="related_datasets", verbose_name="Browse Layer")
    
    class Meta:
        verbose_name = "Related Dataset"
        verbose_name_plural = "Related Datasets"


class BrowseReport(models.Model):
    """Browse Reports contain the metadata of some Browses, i.e. browse 
    images, and are received from the ngEO Feed.
    
    Note that Browse Reports contain a Browse Type which is unique among 
    Browse Layers. Thus we directly use Browse Layer as foreign key.
    
    """
    browse_layer = models.ForeignKey(BrowseLayer, verbose_name="Browse Layer")
    responsible_org_name = models.CharField(max_length=1024, blank=True)
    date_time = models.DateTimeField()
    
    def __unicode__(self):
        return "Browse Report for '%s' from '%s' and '%s'" % (
            self.browse_layer, self.date_time, self.responsible_org_name
        )
    
    class Meta:
        verbose_name = "Browse Report"
        verbose_name_plural = "Browse Reports"


class Browse(models.Model):
    """This is the NOT abstract base class for Browses which have one of the 
    defined five types that inherit from this class.
    
    """
    coverage_id = models.CharField("Coverage ID", max_length=256, primary_key=True, validators=[NCNameValidator])
    browse_report = models.ForeignKey(BrowseReport, related_name="browses", verbose_name="Browse Report")
    browse_layer = models.ForeignKey(BrowseLayer, related_name="browses", verbose_name="Browse Layer")
    file_name = models.CharField(max_length=1024, validators=[FileNameValidator])
    image_type = models.CharField(max_length=8, default="GeoTIFF", 
        choices = (
            ("Jpeg", "Jpeg"),
            ("Jpeg2000", "Jpeg2000"),
            ("TIFF", "TIFF"),
            ("GeoTIFF", "GeoTIFF"),
            ("PNG", "PNG"),
            ("BMP", "BMP"),
        )
    )
    reference_system_identifier = models.CharField(max_length=10, validators=[ReferenceSystemIdentifierValidator])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    def __unicode__(self):
        return "Browse image '%s' with internal ID '%s'" % (
            self.file_name, self.coverage_id
        )
    
    class Meta:
        verbose_name = "Browse image"
        verbose_name_plural = "Browse images"
        unique_together = (("start_time", "end_time", "browse_layer"),)
    
    def clean(self):
        # custom model validation
        if self.start_time > self.end_time:
            raise ValidationError("Start time may not be more recent than end "
                                  "time.")
        


class BrowseIdentifier(models.Model):
    """A Product Facility may define an identifier for a Browse which may be 
    used later to update the browse data.
    
    """
    value = models.CharField("Browse Identifier", max_length=1024, validators=[NameValidator])
    browse = models.OneToOneField(Browse, related_name="browse_identifier")
    browse_layer = models.ForeignKey(BrowseLayer, verbose_name="Browse Layer")
    
    def __unicode__(self):
        return "Browse identifier '%s'" % self.id
    
    class Meta:
        verbose_name = "Browse identifier"
        verbose_name_plural = "Browse identifiers"
        unique_together = (("value", "browse_layer"),)


class RectifiedBrowse(Browse):
    """Rectified Browses with given corner coordinates.
    
    """
    coord_list = models.CharField(max_length=2048)
    

class FootprintBrowse(Browse):
    """Non-rectified Browses with given polygon delimiting boundary or 
    footprint.
    
    """
    node_number = models.IntegerField()
    col_row_list = models.CharField(max_length=2048) # We just store this information, no need for a usable representation.
    coord_list = models.CharField(max_length=2048) # We just store this information, no need for a usable representation.

class RegularGridBrowse(Browse):
    """Non-rectified Browses with given grid of tie-points.
    
    """
    col_node_number = models.IntegerField()
    row_node_number = models.IntegerField()
    col_step = models.FloatField()
    row_step = models.FloatField()

class RegularGridCoordList(models.Model):
    """Coordinate Lists used in RegularGridBrowses.
    
    """
    regular_grid_browse = models.ForeignKey(RegularGridBrowse, related_name="coord_lists", verbose_name="RegularGrid Browse", on_delete=models.CASCADE)
    coord_list = models.CharField(max_length=2048) # We just store this information, no need for a usable representation.

# TODO: Vertical curtains are not supported for now.
class VerticalCurtainBrowse(Browse):
    """Vertical curtain Browses with given suitable footprint object.
    
    Note: Vertical curtains are not supported for now.
    
    """
    pass

class ModelInGeotiffBrowse(Browse):
    """Rectified Browses given as GeoTIFFs.
    
    """
    pass
