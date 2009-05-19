# Author:	Jachym Cepicky
#        	http://les-ejk.cz
# Lince:
#
# Web Processing Service implementation
# Copyright (C) 2006 Jachym Cepicky
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# references used in the comments of this source code:
# OWS_1-1-0:
#      OGC Web Services Common Specification
#      version 1.1.0 with Corrigendum 1
#      ref.num.: OGC 06-121r3
# WPS_1-0-0:
#      OpenGIS(R) Web Processing Service
#      version 1.0.0
#      ref.num.: OGC 05-007r7

import types
from string import split
from pywps.Parser.Parser import Parser
from pywps.Process.Lang import Lang

class Get(Parser):
    """ Main Class for parsing HTTP GET request types """
    unparsedInputs =  {}    # temporary store for later validation
    requestParser = None

    GET_CAPABILITIES = "getcapabilities"
    DESCRIBE_PROCESS = "describeprocess"
    EXECUTE = "execute"

    def parse(self,queryString):
        """Parse given string with parameters given in KVP encoding

        Keyword arguments:
        queryString -- string of parameters taken from URL in KVP encoding

        """

        key = None
        value = None
        keys = []
        maxInputLength = self.wps.config.getint("server","maxinputparamlength")

        # parse query string
        # arguments are separated by "&" character
        # everything is stored into unparsedInputs structure, for latter
        # validation
        for feature in queryString.split("&"):
            feature = feature.strip()
            # omit empty KVPs, e.g. due to optional ampersand after the last
            # KVP in request string (OWS_1-1-0, p.75, sect. 11.2):
            if not feature == '':
                try:
                    key,value = split(feature,"=",maxsplit=1)
                except:
                    raise self.wps.exceptions.NoApplicableCode(\
                                                'Invalid Key-Value-Pair: "' + \
                                                str(feature) + '"')
                if value.find("[") == 0:  # if value in brackets:
                    value = value[1:-1]   #    delete brackets
                if len(value)>maxInputLength:
                        raise self.wps.exceptions.FileSizeExceeded(key)
                keys.append(key)
                self.unparsedInputs[key.lower()] = value[:maxInputLength]


        # check service name
        self.checkService()

        # check request type
        self.checkRequestType()

        # parse the request
        self.requestParser.parse(self.unparsedInputs)

    def checkRequestType(self):
        """Find requested request type and import given request parser."""

        if not "request" in self.unparsedInputs:
            raise self.wps.exceptions.MissingParameterValue("request")

        # test, if one of the mandatory WPS operation is called (via request)
        # (mandatory operations see WPS_1-0-0 p.4 sect.6.1)
        if self.unparsedInputs["request"].lower() ==\
           self.GET_CAPABILITIES:
            import GetCapabilities
            self.requestParser = GetCapabilities.Get(self.wps)
            self.wps.inputs["request"] = self.GET_CAPABILITIES
        elif self.unparsedInputs["request"].lower() ==\
           self.DESCRIBE_PROCESS:
            import DescribeProcess
            self.requestParser = DescribeProcess.Get(self.wps)
            self.wps.inputs["request"] = self.DESCRIBE_PROCESS
        elif self.unparsedInputs["request"].lower() ==\
           self.EXECUTE:
            import Execute
            self.requestParser = Execute.Get(self.wps)
            self.wps.inputs["request"] = self.EXECUTE
        else:
            raise self.wps.exceptions.InvalidParameterValue("request")


    def checkService(self):
        """ Check mandatory service name parameter.  """

        # service name is mandatory for all requests (OWS_1-1-0 p.14 tab.3 +
        # p.46 tab.26); service must be "WPS" (WPS_1-0-0 p.17 tab.13 + p.32 tab.39)
        if "service" in self.unparsedInputs:
            value=self.unparsedInputs["service"].upper()
            if value != "WPS":
                raise self.wps.exceptions.InvalidParameterValue("service")
            else:
                self.wps.inputs["service"] = "WPS"
        else:
            raise self.wps.exceptions.MissingParameterValue("service")

    def checkLanguage(self):
        """ Check optional language parameter.  """

        if "language" in self.unparsedInputs:
            value=Lang.getCode(self.unparsedInputs["language"].lower())
            if value not in self.wps.languages:
                raise self.wps.exceptions.InvalidParameterValue("language")
            else:
                self.wps.inputs["language"] = value
        else:
            self.wps.inputs["language"] = self.wps.defaultLanguage

    def checkVersion(self):
        """ Check mandatory version parameter.  """

        if "version" in self.unparsedInputs:
            value=self.unparsedInputs["version"]
            if value not in self.wps.versions:
                raise self.wps.exceptions.VersionNegotiationFailed(
                    'The requested version "' + value + \
                    '" is not supported by this server.')
            else:
                self.wps.inputs["version"] = value
        else:
            raise self.wps.exceptions.MissingParameterValue("version")