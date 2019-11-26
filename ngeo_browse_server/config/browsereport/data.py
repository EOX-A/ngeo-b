#-------------------------------------------------------------------------------
#
# Project: ngEO Browse Server <http://ngeo.eox.at>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Marko Locher <marko.locher@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 European Space Agency
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


"""\
This module contains intermediary (runtime) data for ingestion or the like.
The classes in this module are explicitly not tied to database models, but
provide means for easy data exchange.
"""


class Browse(object):
    """ Abstract base class for browse records. """

    def __init__(self, file_name, image_type, reference_system_identifier,
                 start_time, end_time, browse_identifier=None):
        self._browse_identifier = browse_identifier
        self._file_name = file_name
        self._image_type = image_type
        self._reference_system_identifier = reference_system_identifier
        self._start_time = start_time
        self._end_time = end_time

    browse_identifier = property(lambda self: self._browse_identifier)
    file_name = property(lambda self: self._file_name)
    image_type = property(lambda self: self._image_type)
    reference_system_identifier = property(lambda self: self._reference_system_identifier)
    start_time = property(lambda self: self._start_time)
    end_time = property(lambda self: self._end_time)

    @property
    def geo_type(self):
        raise NotImplementedError()

    def get_kwargs(self):
        return {
            "file_name": self.file_name,
            "image_type": self.image_type,
            "reference_system_identifier": self.reference_system_identifier,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

    # need setter for mutating times when shortening time interval in ingestion
    def set_start_time(self, x):
        self._start_time = x

    def set_end_time(self, x):
        self._end_time = x

class RectifiedBrowse(Browse):
    def __init__(self, coord_list, *args, **kwargs):
        super(RectifiedBrowse, self).__init__(*args, **kwargs)
        self._coord_list = coord_list

    coord_list = property(lambda self: self._coord_list)
    geo_type = property(lambda self: "rectifiedBrowse")

    def get_kwargs(self):
        kwargs = super(RectifiedBrowse, self).get_kwargs()
        kwargs.update({
            "coord_list": self.coord_list
        })
        return kwargs


class FootprintBrowse(Browse):
    @classmethod
    def from_model(cls, browse_model):
        return FootprintBrowse(
        )

    def __init__(self, node_number, col_row_list, coord_list, *args, **kwargs):
        super(FootprintBrowse, self).__init__(*args, **kwargs)
        self._node_number = node_number
        self._col_row_list = col_row_list
        self._coord_list = coord_list

    node_number = property(lambda self: self._node_number)
    col_row_list = property(lambda self: self._col_row_list)
    coord_list = property(lambda self: self._coord_list)

    geo_type = property(lambda self: "footprintBrowse")

    def get_kwargs(self):
        kwargs = super(FootprintBrowse, self).get_kwargs()
        kwargs.update({
            "node_number": self._node_number,
            "col_row_list": self._col_row_list,
            "coord_list": self._coord_list
        })
        return kwargs


class RegularGridBrowse(Browse):
    def __init__(self, col_node_number, row_node_number, col_step, row_step,
                 coord_lists, *args, **kwargs):
        super(RegularGridBrowse, self).__init__(*args, **kwargs)
        self._col_node_number = col_node_number
        self._row_node_number = row_node_number
        self._col_step = col_step
        self._row_step = row_step
        self._coord_lists = coord_lists

    col_node_number = property(lambda self: self._col_node_number)
    row_node_number = property(lambda self: self._row_node_number)
    col_step = property(lambda self: self._col_step)
    row_step = property(lambda self: self._row_step)
    coord_lists = property(lambda self: self._coord_lists)

    geo_type = property(lambda self: "regularGridBrowse")

    def get_kwargs(self):
        kwargs = super(RegularGridBrowse, self).get_kwargs()
        kwargs.update({
            "col_node_number": self._col_node_number,
            "row_node_number": self._row_node_number,
            "col_step": self._col_step,
            "row_step": self._row_step
        })
        return kwargs


class VerticalCurtainBrowse(Browse):
    geo_type = property(lambda self: "verticalCurtainBrowse")


class ModelInGeotiffBrowse(Browse):
    geo_type = property(lambda self: "modelInGeotiffBrowse")


def browse_from_model(browse_model):
    # import here, so that the module can be used without an instance
    from ngeo_browse_server.config import models

    kwargs = {
        "file_name": browse_model.file_name,
        "image_type": browse_model.image_type,
        "reference_system_identifier": browse_model.reference_system_identifier,
        "start_time": browse_model.start_time,
        "end_time": browse_model.end_time
    }

    try:
        kwargs["browse_identifier"] = browse_model.browse_identifier.value
    except models.BrowseIdentifier.DoesNotExist:
        pass

    try:
        return RectifiedBrowse(browse_model.rectifiedbrowse.coord_list, **kwargs)
    except models.RectifiedBrowse.DoesNotExist:
        pass
    try:
        return FootprintBrowse(
            browse_model.footprintbrowse.node_number,
            browse_model.footprintbrowse.col_row_list,
            browse_model.footprintbrowse.coord_list,
            **kwargs
        )
    except models.FootprintBrowse.DoesNotExist:
        pass
    try:
        return RegularGridBrowse(
            browse_model.regulargridbrowse.col_node_number,
            browse_model.regulargridbrowse.row_node_number,
            browse_model.regulargridbrowse.col_step,
            browse_model.regulargridbrowse.row_step,
            [coord_list.coord_list
             for coord_list in browse_model.regulargridbrowse.coord_lists.all()],
            **kwargs
        )
    except models.RegularGridBrowse.DoesNotExist:
        pass
    try:
        _ = browse_model.modelingeotiffbrowse
        return ModelInGeotiffBrowse(**kwargs)
    except models.ModelInGeotiffBrowse.DoesNotExist:
        pass


class BrowseReport(object):
    """ Browse report data model. """

    @classmethod
    def from_model(cls, browse_report_model, browses_qs=None):
        if browses_qs is None:
            browses_qs = browse_report_model.browses.all()

        return BrowseReport(
            browse_report_model.browse_layer.browse_type,
            browse_report_model.date_time,
            browse_report_model.responsible_org_name,
            browses=[browse_from_model(browse_model)
                     for browse_model in browses_qs]
        )

    def __init__(self, browse_type, date_time, responsible_org_name, browses=None):
        self._browse_type = browse_type
        self._date_time = date_time
        self._responsible_org_name = responsible_org_name
        self._browses = list(browses) if browses else []

    def __iter__(self):
        return iter(self._browses)

    def __len__(self):
        return len(self._browses)

    def append(self, browse):
        self._browses.append(browse)

    browse_type = property(lambda self: self._browse_type)
    date_time = property(lambda self: self._date_time)
    responsible_org_name = property(lambda self: self._responsible_org_name)

    def get_kwargs(self):
        return {
            "date_time": self._date_time,
            "responsible_org_name": self._responsible_org_name
        }


