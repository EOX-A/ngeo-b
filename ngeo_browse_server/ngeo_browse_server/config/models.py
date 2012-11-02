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


ReferenceSystemIdentifierValidator = RegexValidator( 
    re.compile(r'^EPSG:[0-9]+$|^RAW$'),
    message="Reference system identifier must be 'RAW' or follow the pattern 'EPSG:<code>."
)
NameValidator = RegexValidator(
    re.compile(r'^[a-zA-z_:][a-zA-Z0-9.-_:]*$'),
    message="This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops."
)


class BrowseLayer(models.Model):
    """The Browse Layers are available as WMS and WMTS layers and are mapped 
    to DatasetSeries in EOxServer.
    
    """
    id = models.CharField("Browse Layer ID", max_length=1024, primary_key=True, validators=[NameValidator])
    title = models.CharField(max_length=1024)
    description = models.CharField(max_length=1024, blank=True)
    browse_access_policy = models.CharField(max_length=10, default="OPEN", 
        choices = (
            ("OPEN", "Open"),
            ("RESTRICTED", "Restricted"),
            ("PRIVATE", "Private"),
        )
    )
    contains_vertical_curtains = models.BooleanField(default=False) # TODO: Fixed to False for now as vertical curtains are not supported.
    r_band = models.IntegerField(null=True, blank=True, default=None)
    g_band = models.IntegerField(null=True, blank=True, default=None)
    b_band = models.IntegerField(null=True, blank=True, default=None)
    radiometric_interval_min = models.IntegerField(null=True, blank=True, default=None)
    radiometric_interval_max = models.IntegerField(null=True, blank=True, default=None)
    highest_map_level = models.IntegerField(null=True, blank=True, default=None)
    lowest_map_level = models.IntegerField(null=True, blank=True, default=None)
    
    def __unicode__(self):
        return self.id
    
    class Meta:
        verbose_name = "Browse Layer"
        verbose_name_plural = "Browse Layers"


class BrowseType(models.Model):
    """The Browse Type is used to determine the Browse Layer(s) to which the 
    Browses contained in a Browse Report belong to.
    
    """
    id = models.CharField("Browse Type ID", max_length=1024, primary_key=True, validators=[NameValidator])
    browse_layer = models.OneToOneField(BrowseLayer, verbose_name="Browse Type")
    
    def __unicode__(self):
        return self.id
    
    class Meta:
        verbose_name = "Browse Type"
        verbose_name_plural = "Browse Types"


# TODO: Clarify, when and where are these needed? Do we really need to save these?
class RelatedDataset(models.Model):
    """The Browse Layer configuration contains Related Datasets.
    
    """
    dataset_id = models.CharField(max_length=1024, unique=True, validators=[NameValidator])
    browse_layer = models.ForeignKey(BrowseLayer, verbose_name="Browse Layer")
    
    class Meta:
        verbose_name = "Related Dataset"
        verbose_name_plural = "Related Datasets"


class BrowseReport(models.Model):
    """Browse Reports contain the metadata of some Browses, i.e. browse 
    images, and are received from the ngEO Feed.
    
    """
    browse_type = models.ForeignKey(BrowseType, verbose_name="Browse Type")
    responsible_org_name = models.CharField(max_length=1024, blank=True)
    date_time = models.DateTimeField()
    
    class Meta:
        verbose_name = "Browse Report"
        verbose_name_plural = "Browse Reports"


class Browse(models.Model):
    """This is the NOT abstract base class for Browses which have one of the 
    defined five types that inherit from this class.
    
    """
    browse_report = models.ForeignKey(BrowseReport, related_name="browses", verbose_name="Browse Report")
    file_name = models.CharField(max_length=1024, validators=[NameValidator])
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
    geo_type = models.CharField(max_length=24, default="modelInGeotiff", 
        choices = (
            ("rectifiedBrowse", "Browse is rectified and the corner coordinates are given"),
            ("footprint", "Browse is non-rectified and a polygon delimiting boundary is given"),
            ("regularGrid", "Browse is non-rectified and a grid of tie-points is provided"),
            ("verticalCurtainFootprint", "Browse is vertical curtain and a suitable footprint object is supplied"), # TODO: Vertical curtains are not supported for now.
            ("modelInGeotiff", "Browse is a rectified GeoTIFF"),
        )
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class BrowseIdentifier(models.Model):
    """A Product Facility may define an identifier for a Browse which may be 
    used later to update the browse data.
    
    """
    id = models.CharField("Browse Identifier", max_length=1024, primary_key=True, validators=[NameValidator])
    browse = models.OneToOneField(Browse, related_name="browse_identifier")


class RectifiedBrowse(Browse):
    """Rectified Browses with given corner coordinates.
    
    """
    minx = models.FloatField()
    miny = models.FloatField()
    maxx = models.FloatField()
    maxy = models.FloatField()

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
