#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from lxml import etree 


class XMLDecodeError(Exception):
    pass


class XMLDecoder(object):
    """ Multi-purpose XML parser. Applies a given schema to an XML tree node. 
    """
    
    def __init__(self, schema, namespaces=None):
        """\
        Initializes the XMLDecoder.
        
        :param schema: is a dict in the form 'key': (selector, [type[, 
        multiplicity]]). *key* is the parameter name to be set on the result 
        dictionary. *selector* is either an xpath string or a callable that 
        accepts an :class:`etree.Element` and returns a list of objects 
        (Elements/strings etc). *type* is a callable that converts the decoded 
        strings/Elements to their intended type. *multiplicity* is either a 
        positive integer or one of '*', '+' or '?', defining how many items are
        expected. If *multiplicity* is 1 or '?' the resulting value is scalar, 
        otherwise a list.
        :param namespaces: is a dictionary to map namespaces prefix to the to 
        its URI to be used for XPath expressions.
        """
        
        self._schema = schema
        self.namespaces = namespaces
        
        for key, value in schema.items():
            if isinstance(value, basestring):
                schema[key] = self._init_param(value)
            else:
                schema[key] = self._init_param(*value)
    
    
    def _init_param(self, selector, *args):
        """ Initialize a single parameter. If the selector is a string, it will
        be interpreted as an XPath expression. """
        
        if isinstance(selector, basestring):
            selector = etree.XPath(selector, namespaces=self.namespaces)
            
        return (selector,) + args
        
    
    def decode(self, element, kwargs=None):
        """ Applies the schema to the element and parses all parameters.
        """
        
        if kwargs is None:
            kwargs = {}
        
        for key, args in self._schema.items():
            self.decode_arg(element, kwargs, key, *args)
        
        return kwargs
    
    __call__ = decode
    
    
    def decode_arg(self, element, kwargs, key, selector, typ=str, multiplicity=1):
        """ Decodes a single argument and adds it to the result dict. Also checks
        for the correct multiplicity of the element and applies the given type.
        """
        
        results = selector(element)
        try:
            num_results = len(results)
        except TypeError:
            num_results = 1
            results = (results,)
        
        multiple = multiplicity not in (1, "?")
        
        if isinstance(multiplicity, int) and num_results != multiplicity:
            if not num_results:
                raise XMLDecodeError("Could not find required element%s %s." % 
                                     ("s" if multiple else "",  selector))
            raise XMLDecodeError("Found unexpected number (%d) of elements %s. "
                                 "Expected %s." %
                                 (num_results, selector, multiplicity))
        
        if multiplicity == "+" and not num_results:
            raise XMLDecodeError("Could not find required element %s." % selector)
        
        if multiplicity == "?" and num_results > 1:
            raise XMLDecodeError("Expected at most one element of %s." % selector)
        
        if multiple:
            kwargs[key] = map(typ, results)
        
        elif multiplicity == 1:
            kwargs[key] = typ(results[0])
        
        elif multiplicity == "?" and num_results:
            kwargs[key] = typ(results[0])


class typelist(object):
    """ Helper for XMLDecoder schemas that expect a string that represents a list
    of a type separated by some separator.
    """
    
    def __init__(self, typ, separator=" "):
        self.typ = typ
        self.separator = separator
        
    
    def __call__(self, value):
        return map(self.typ, value.split(self.separator))

