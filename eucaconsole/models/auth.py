# -*- coding: utf-8 -*-
# Copyright 2013-2014 Eucalyptus Systems, Inc.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Authentication and Authorization models

"""
import base64
import httplib
from ssl import SSLError
import socket
import urllib2
import xml

from boto import ec2
from boto import vpc
from boto.https_connection import CertValidatingHTTPSConnection
from boto.ec2.connection import EC2Connection
from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat
# uncomment to enable boto request logger. Use only for development (see ref in _euca_connection)
# from boto.requestlog import RequestLogger
import boto
import boto.ec2.autoscale
import boto.cloudformation
import boto.ec2.cloudwatch
import boto.ec2.elb
import boto.iam
from boto.handler import XmlHandler as BotoXmlHandler
from boto.regioninfo import RegionInfo
from boto.sts.credentials import Credentials
from pyramid.security import Authenticated, authenticated_userid


class User(object):
    """Authenticated/Anonymous User object for Pyramid Auth."""
    def __init__(self, user_id=None):
        self.user_id = user_id

    @classmethod
    def get_auth_user(cls, request):
        """Get an authenticated user.  Note that self.user_id = None if not authenticated.
           See: http://docs.pylonsproject.org/projects/pyramid_cookbook/en/latest/auth/user_object.html
        """
        user_id = authenticated_userid(request)
        return cls(user_id=user_id)

    def is_authenticated(self):
        """user_id will be None if the user isn't authenticated"""
        return self.user_id

    @staticmethod
    def get_account_id(ec2_conn=None, request=None):
        """Get 12-digit account ID for the currently signed-in user's account using the default security group"""
        from ..views import boto_error_handler
        account_id = ""
        if ec2_conn and request:
            with boto_error_handler(request):
                security_groups = ec2_conn.get_all_security_groups(filters={'group-name': 'default'})
                security_group = security_groups[0] if security_groups else None 
                if security_group is not None:
                    account_id = security_group.owner_id
        return account_id
                    

class ConnectionManager(object):
    """Returns connection objects, pulling from Beaker cache when available"""
    @staticmethod
    def aws_connection(region, access_key, secret_key, token, conn_type, validate_certs=False):
        """Return AWS EC2 connection object
        Pulls from Beaker cache on subsequent calls to avoid connection overhead

        :type region: string
        :param region: region name (e.g. 'us-east-1')

        :type access_key: string
        :param access_key: AWS access key

        :type secret_key: string
        :param secret_key: AWS secret key

        :type conn_type: string
        :param conn_type: Connection type ('ec2', 'autoscale', 'cloudwatch', 'cloudformation', 'elb', or 's3')

        :type validate_certs: bool
        :param validate_certs: indicates to check the ssl cert the server provides

        """

        def _aws_connection(_region, _access_key, _secret_key, _token, _conn_type):
            conn = None
            if conn_type == 'ec2':
                conn = ec2.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'autoscale':
                conn = ec2.autoscale.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'cloudwatch':
                conn = ec2.cloudwatch.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'cloudformation':
                conn = boto.cloudformation.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 's3':
                conn = boto.connect_s3(  # Don't specify region when connecting to S3
                    aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'elb':
                conn = ec2.elb.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'vpc':
                conn = vpc.connect_to_region(
                    _region, aws_access_key_id=_access_key, aws_secret_access_key=_secret_key, security_token=_token)
            elif conn_type == 'iam':
                return None
            conn.https_validate_certificates = validate_certs
            return conn

        return _aws_connection(region, access_key, secret_key, token, conn_type)

    @staticmethod
    def euca_connection(clchost, port, access_id, secret_key, token, conn_type, validate_certs=False, certs_file=None):
        """Return Eucalyptus connection object
        Pulls from Beaker cache on subsequent calls to avoid connection overhead

        :type clchost: string
        :param clchost: FQDN or IP of Eucalyptus CLC (cloud controller)

        :type port: int
        :param port: Port of Eucalyptus CLC (usually 8773)

        :type access_id: string
        :param access_id: Euca access id

        :type secret_key: string
        :param secret_key: Eucalyptus secret key

        :type conn_type: string
        :param conn_type: Connection type ('ec2', 'autoscale', 'cloudwatch', 'cloudformation', 'elb', 'iam', 'sts', or 's3')

        :type validate_certs: bool
        :param validate_certs: indicates to check the ssl cert the server provides

        :type certs_file: string
        :param certs_file: indicates the location of the certificates file, if otherthan standard

        """
        def _euca_connection(_clchost, _port, _access_id, _secret_key, _token, _conn_type):
            region = RegionInfo(name='eucalyptus', endpoint=_clchost)
            path = '/services/Eucalyptus'
            conn_class = EC2Connection
            api_version = '2012-12-01'

            # Configure based on connection type
            if conn_type == 'autoscale':
                api_version = '2011-01-01'
                conn_class = boto.ec2.autoscale.AutoScaleConnection
                path = '/services/AutoScaling'
            elif conn_type == 'cloudwatch':
                path = '/services/CloudWatch'
                conn_class = boto.ec2.cloudwatch.CloudWatchConnection
            elif conn_type == 'cloudformation':
                path = '/services/CloudFormation'
                conn_class = boto.cloudformation.CloudFormationConnection
            elif conn_type == 'elb':
                path = '/services/LoadBalancing'
                conn_class = boto.ec2.elb.ELBConnection
            elif conn_type == 'iam':
                path = '/services/Euare'
                conn_class = boto.iam.IAMConnection
            elif conn_type == 's3':
                path = '/services/objectstorage'
                conn_class = S3Connection
            elif conn_type == 'vpc':
                conn_class = boto.vpc.VPCConnection

            # IAM and S3 connections need host instead of region info
            if conn_type in ['iam', 's3']:
                conn = conn_class(
                    _access_id, _secret_key, host=_clchost, port=_port, path=path, is_secure=True, security_token=_token
                )
            else:
                conn = conn_class(
                    _access_id, _secret_key, region=region, port=_port, path=path, is_secure=True, security_token=_token
                )
            if conn_type == 's3':
                conn.calling_format=OrdinaryCallingFormat()

            # AutoScaling service needs additional auth info
            if conn_type == 'autoscale':
                conn.auth_region_name = 'Eucalyptus'

            setattr(conn, 'APIVersion', api_version)
            conn.https_validate_certificates = validate_certs
            if certs_file is not None:
                conn.ca_certificates_file = certs_file
            conn.http_connection_kwargs['timeout'] = 30
            # uncomment to enable boto request logger. Use only for development
            # conn.set_request_hook(RequestLogger())
            return conn

        return _euca_connection(clchost, port, access_id, secret_key, token, conn_type)


def groupfinder(user_id, request):
    if user_id is not None:
        return [Authenticated]
    return []


class EucaAuthenticator(object):
    """Eucalyptus cloud token authenticator"""
    TEMPLATE = '/services/Tokens?Action=GetAccessToken&DurationSeconds={dur}&Version=2011-06-15'

    def __init__(self, host, port, validate_certs=False, **validate_kwargs):
        """
        Configure connection to Eucalyptus STS service to authenticate with the CLC (cloud controller)

        :type host: string
        :param host: IP address or FQDN of CLC host

        :type port: integer
        :param port: port number to use when making the connection

        """
        self.host = host
        self.port = port
        self.validate_certs = validate_certs
        self.kwargs = validate_kwargs

    def authenticate(self, account, user, passwd, new_passwd=None, timeout=15, duration=3600):
        if user == 'admin' and duration > 3600:  # admin cannot have more than 1 hour duration
            duration = 3600
        # because of the variability, we need to keep this here, not in __init__
        auth_path = self.TEMPLATE.format(
            dur=duration,
        )
        if self.validate_certs:
            conn = CertValidatingHTTPSConnection(self.host, self.port, timeout=timeout, **self.kwargs)
        else:
            conn = httplib.HTTPSConnection(self.host, self.port, timeout=timeout)

        if new_passwd:
            auth_string = u"{user}@{account};{pw}@{new_pw}".format(
                user=base64.b64encode(user),
                account=base64.b64encode(account),
                pw=base64.b64encode(passwd),
                new_pw=new_passwd
            )
        else:
            auth_string = u"{user}@{account}:{pw}".format(
                user=base64.b64encode(user),
                account=base64.b64encode(account),
                pw=passwd
            )
        encoded_auth = base64.b64encode(auth_string)
        headers = {'Authorization': "Basic %s" % encoded_auth}
        try:
            conn.request('GET', auth_path, '', headers)
            response = conn.getresponse()
            if response.status != 200:
                raise urllib2.HTTPError(url='', code=response.status, msg=response.reason, hdrs=None, fp=None)
            body = response.read()

            # parse AccessKeyId, SecretAccessKey and SessionToken
            creds = Credentials()
            h = BotoXmlHandler(creds, None)
            xml.sax.parseString(body, h)
            return creds
        except SSLError as err:
            if err.message != '':
                raise urllib2.URLError(str(err))
            else:
                raise urllib2.URLError(err[1])
        except socket.error as err:
            raise urllib2.URLError(str(err))


class AWSAuthenticator(object):

    def __init__(self, package, validate_certs=False, **validate_kwargs):
        """
        Configure connection to AWS STS service

        :type package: string
        :param package: a pre-signed request string for the STS GetSessionToken call

        """
        self.host = 'sts.amazonaws.com'
        self.port = 443
        self.package = package
        self.validate_certs = validate_certs
        self.kwargs = validate_kwargs

    def authenticate(self, timeout=20):
        """ Make authentication request to AWS STS service
            Timeout defaults to 20 seconds"""
        if self.validate_certs:
            conn = CertValidatingHTTPSConnection(self.host, self.port, timeout=timeout, **self.kwargs)
        else:
            conn = httplib.HTTPSConnection(self.host, self.port, timeout=timeout)

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        try:
            conn.request('POST', '', self.package, headers)
            response = conn.getresponse()
            if response.status != 200:
                raise urllib2.HTTPError(url='', code=response.status, msg=response.reason, hdrs=None, fp=None)
            body = response.read()
            
            # parse AccessKeyId, SecretAccessKey and SessionToken
            creds = Credentials()
            h = BotoXmlHandler(creds, None)
            xml.sax.parseString(body, h)
            return creds
        except SSLError as err:
            if err.message != '':
                raise urllib2.URLError(err.message)
            else:
                raise urllib2.URLError(err[1])
        except socket.error as err:
            raise urllib2.URLError(err.message)

