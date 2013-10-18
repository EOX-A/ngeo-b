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

"""This module defines the models used by MapCache to properly handle time 
dimensions.

The corresponding SQLite database will be used in a dimension entry in the 
tileset configuration of MapCache:
<dimension type="time" name="TIME">/path/to/sqlitefile</dimension>

.. moduleauthor:: Stephan Meissl <stephan.meissl@eox.at>
"""

import re

from django.db import models
from django.core.validators import RegexValidator

NameValidator = RegexValidator(
    re.compile(r'^[a-zA-z_:][a-zA-Z0-9.-_:]*$'),
    message="This field must contain a valid Name i.e. beginning with a letter, an underscore, or a colon, and continuing with letters, digits, hyphens, underscores, colons, or full stops."
)

class Source(models.Model):
    """Corresponds to sources used in the same MapCache tileset.
    
    """
    name = models.CharField(max_length=1024, primary_key=True, validators=[NameValidator])
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        db_table = "source"

class Time(models.Model):
    """A time-stamp or -interval where data is available for the given source.
    
    """
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True)
    source = models.ForeignKey(Source)
    
    minx = models.FloatField()
    miny = models.FloatField()
    maxx = models.FloatField()
    maxy = models.FloatField()
    
    def __unicode__(self):
        return ("Start time: %s" % self.start_time)
    
    class Meta:
        db_table = "time"
