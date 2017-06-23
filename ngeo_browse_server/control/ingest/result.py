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


class IngestBrowseReportResult(object):
    """ Result object for ingestion operations. """

    def __init__(self):
        self._results = []

    def add(self, result):
        """ Adds a single browse ingestion result, where the status is either
        success or failure.
        """

        self._results.append(result)

    def __iter__(self):
        "Helper for easy iteration of browse ingest results."

        return iter(self._results)

    @property
    def status(self):
        """Returns 'partial' if any failure results where registered, else
        'success'.
        """
        if self.failures > 0:
            return "partial"
        else:
            return "success"

    @property
    def to_be_replaced(self):
        return len(self._results)

    @property
    def actually_inserted(self):
        return len(filter(lambda r: r.success and
                   not (r.replaced or r.skipped), self._results))

    @property
    def actually_replaced(self):
        return len(filter(lambda r: r.success and r.replaced, self._results))

    @property
    def failures(self):
        return len(filter(lambda r: not r.success, self._results))


class IngestBrowseResult(object):
    def __init__(self, identifier, extent, time_interval):
        self.success = True
        self.replaced = False
        self.skipped = False
        self.identifier = identifier
        self.extent = extent
        self.time_interval = time_interval

    status = property(lambda self: "success" if self.success else "failure")


class IngestBrowseReplaceResult(IngestBrowseResult):
    def __init__(self, identifier, extent, time_interval,
                 replaced_extent, replaced_time_interval):
        super(IngestBrowseReplaceResult, self).__init__(identifier, extent,
                                                        time_interval)
        self.replaced = True
        self.replaced_extent = replaced_extent
        self.replaced_time_interval = replaced_time_interval


class IngestBrowseSkipResult(IngestBrowseResult):
    def __init__(self, identifier):
        super(IngestBrowseSkipResult, self).__init__(identifier, (0, 0, 0, 0),
                                                     (0, 0))
        self.skipped = True


class IngestBrowseFailureResult(IngestBrowseResult):
    def __init__(self, identifier, code, message):
        super(IngestBrowseFailureResult, self).__init__(identifier, None, None)
        self.success = False
        self.code = code
        self.message = message
