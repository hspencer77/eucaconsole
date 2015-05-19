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
Forms for Elastic Load Balancer

"""
import wtforms
from wtforms import validators

from ..i18n import _
from . import BaseSecureForm, ChoicesManager, TextEscapedField, NAME_WITHOUT_SPACES_NOTICE
from ..views import BaseView


# update ELB form for the ELB detail page
class ELBForm(BaseSecureForm):
    """Elastic Load Balancer update form"""
    idle_timeout = wtforms.TextField(
        label=_(u'Idle timeout (secs)'),
    )
    idle_timeout_help_text = _(u'Amount of time a connection to an instance can be idle \
                                 before the load balancer closes it. If keep alive is set for instances, \
                                 keep alive value should be set higher than idle timeout.')
    securitygroup_error_msg = _(u'Security groups are required')
    securitygroup = wtforms.SelectMultipleField(
        label=_(u'Security groups'),
    )
    ping_protocol_error_msg = _(u'Ping protocol is required')
    ping_protocol = wtforms.SelectField(
        label=_(u'Protocol'),
        validators=[validators.InputRequired(message=ping_protocol_error_msg)],
    )
    ping_port_error_msg = _(u'Port range value must be whole numbers between 1-65535')
    ping_port = wtforms.IntegerField(
        label=_(u'Port'),
        validators=[
            validators.InputRequired(message=ping_port_error_msg),
            validators.NumberRange(min=1, max=65535),
        ],
    )
    ping_path_error_msg = _(u'Ping path is required')
    ping_path = TextEscapedField(
        id=u'ping-path',
        label=_(u'Path'),
        default="index.html",
        validators=[validators.InputRequired(message=ping_path_error_msg)],
    )
    response_timeout_error_msg = _(u'Response timeout is required')
    response_timeout = wtforms.IntegerField(
        label=_(u'Response timeout (secs)'),
        validators=[validators.InputRequired(message=response_timeout_error_msg)],
    )
    time_between_pings_error_msg = _(u'Time between pings is required')
    time_between_pings = wtforms.SelectField(
        label=_(u'Time between pings'),
        validators=[validators.InputRequired(message=time_between_pings_error_msg)],
    )
    failures_until_unhealthy_error_msg = _(u'Failures until unhealthy is required')
    failures_until_unhealthy = wtforms.SelectField(
        label=_(u'Failures until unhealthy'),
        validators=[validators.InputRequired(message=failures_until_unhealthy_error_msg)],
    )
    passes_until_healthy_error_msg = _(u'Passes until healthy is required')
    passes_until_healthy = wtforms.SelectField(
        label=_(u'Passes until healthy'),
        validators=[validators.InputRequired(message=passes_until_healthy_error_msg)],
    )

    def __init__(self, request, conn=None, vpc_conn=None, elb=None, securitygroups=None, **kwargs):
        super(ELBForm, self).__init__(request, **kwargs)
        self.conn = conn
        self.vpc_conn = vpc_conn
        self.cloud_type = request.session.get('cloud_type', 'euca')
        self.is_vpc_supported = BaseView.is_vpc_supported(request)
        self.security_groups = securitygroups or []
        self.idle_timeout.help_text = self.idle_timeout_help_text
        self.set_error_messages()
        self.set_choices()
        if elb is not None:
            self.idle_timeout.data = elb.idle_timeout

    def set_error_messages(self):
        self.securitygroup.error_msg = self.securitygroup_error_msg
        self.ping_path.error_msg = self.ping_path_error_msg

    def set_choices(self):
        self.securitygroup.choices = self.set_security_group_choices()
        # using the static methods from CreateELBForm
        self.ping_protocol.choices = CreateELBForm.get_ping_protocol_choices()
        self.time_between_pings.choices = CreateELBForm.get_time_between_pings_choices()
        self.failures_until_unhealthy.choices = CreateELBForm.get_failures_until_unhealthy_choices()
        self.passes_until_healthy.choices = CreateELBForm.get_passes_until_healthy_choices()

    def set_security_group_choices(self):
        choices = []
        for sgroup in self.security_groups:
            sg_name = sgroup.name
            sg_name = BaseView.escape_braces(sg_name)
            choices.append((sgroup.id, sg_name))
        if not self.security_groups:
            choices.append(('default', 'default'))
        return sorted(set(choices))


class ELBDeleteForm(BaseSecureForm):
    """ELB deletion form.
       Only need to initialize as a secure form to generate CSRF token
    """
    pass


class ELBsFiltersForm(BaseSecureForm):
    """Form class for filters on landing page"""
    availability_zones = wtforms.SelectMultipleField(label=_(u'Availability zone'))
    instance_type = wtforms.SelectMultipleField(label=_(u'Instance type'))
    key_name = wtforms.SelectMultipleField(label=_(u'Key pair'))
    security_groups = wtforms.SelectMultipleField(label=_(u'Security group'))

    def __init__(self, request, cloud_type='euca', ec2_conn=None, **kwargs):
        super(ELBsFiltersForm, self).__init__(request, **kwargs)
        self.request = request
        self.cloud_type = cloud_type
        self.ec2_conn = ec2_conn
        self.ec2_choices_manager = ChoicesManager(conn=ec2_conn)
        region = request.session.get('region')
        self.availability_zones.choices = self.ec2_choices_manager.availability_zones(region, add_blank=False)
        self.instance_type.choices = self.ec2_choices_manager.instance_types(
            add_blank=False, cloud_type=self.cloud_type, add_description=False)
        self.key_name.choices = self.ec2_choices_manager.keypairs(add_blank=False, no_keypair_filter_option=True)
        self.security_groups.choices = self.ec2_choices_manager.security_groups(use_id=True, add_blank=False)
        self.facets = [
            {'name': 'instance_type', 'label': self.instance_type.label.text,
                'options': self.getOptionsFromChoices(self.instance_type.choices)},
            {'name': 'key_name', 'label': self.key_name.label.text,
                'options': self.getOptionsFromChoices(self.key_name.choices)},
            {'name': 'security_group', 'label': self.security_groups.label.text,
                'options': self.getOptionsFromChoices(self.security_groups.choices)},
        ]


# create a new ELB form for the create ELB wizard
class CreateELBForm(BaseSecureForm):
    """Create Elastic Load Balancer form"""
    name_error_msg = NAME_WITHOUT_SPACES_NOTICE
    name = wtforms.TextField(
        label=_(u'Name'),
        validators=[validators.InputRequired(message=name_error_msg)],
    )
    vpc_network_error_msg = _(u'VPC network is required')
    vpc_network = wtforms.SelectField(
        label=_(u'VPC network'),
        validators=[validators.InputRequired(message=vpc_network_error_msg)],
    )
    vpc_subnet = wtforms.SelectMultipleField(
        label=_(u'VPC subnets'),
    )
    securitygroup_error_msg = _(u'Security group is required')
    securitygroup = wtforms.SelectMultipleField(
        label=_(u'Security groups'),
        validators=[validators.InputRequired(message=securitygroup_error_msg)],
    )
    zone = wtforms.SelectMultipleField(
        label=_(u'Availability zones'),
    )
    cross_zone_enabled_help_text = _(u'Distribute traffic evenly across all instances in all availability zones')
    cross_zone_enabled = wtforms.BooleanField(label=_(u'Enable cross-zone load balancing'))
    add_availability_zones_help_text = _(u'Enable this load balancer \
        to route traffic to instances in the selected zones')
    add_vpc_subnets_help_text = _(u'Enable this load balancer to route traffic to instances in the selected subnets')
    add_instances_help_text = _(u'Balance traffic between the selected instances')
    ping_protocol_error_msg = _(u'Ping protocol is required')
    ping_protocol = wtforms.SelectField(
        label=_(u'Protocol'),
        validators=[validators.InputRequired(message=ping_protocol_error_msg)],
    )
    ping_port_error_msg = _(u'Port range value must be whole numbers between 1-65535')
    ping_port = wtforms.IntegerField(
        label=_(u'Port'),
        validators=[
            validators.InputRequired(message=ping_port_error_msg),
            validators.NumberRange(min=1, max=65535),
        ],
    )
    ping_path_error_msg = _(u'Ping path is required')
    ping_path = TextEscapedField(
        id=u'ping-path',
        label=_(u'Path'),
        default="index.html",
        validators=[validators.InputRequired(message=ping_path_error_msg)],
    )
    response_timeout_error_msg = _(u'Response timeout is required')
    response_timeout = wtforms.IntegerField(
        label=_(u'Response timeout (secs)'),
        validators=[validators.InputRequired(message=response_timeout_error_msg)],
    )
    time_between_pings_error_msg = _(u'Time between pings is required')
    time_between_pings = wtforms.SelectField(
        label=_(u'Time between pings'),
        validators=[validators.InputRequired(message=time_between_pings_error_msg)],
    )
    failures_until_unhealthy_error_msg = _(u'Failures until unhealthy is required')
    failures_until_unhealthy = wtforms.SelectField(
        label=_(u'Failures until unhealthy'),
        validators=[validators.InputRequired(message=failures_until_unhealthy_error_msg)],
    )
    passes_until_healthy_error_msg = _(u'Passes until healthy is required')
    passes_until_healthy = wtforms.SelectField(
        label=_(u'Passes until healthy'),
        validators=[validators.InputRequired(message=passes_until_healthy_error_msg)],
    )

    def __init__(self, request, conn=None, vpc_conn=None, **kwargs):
        super(CreateELBForm, self).__init__(request, **kwargs)
        self.conn = conn
        self.vpc_conn = vpc_conn
        self.cloud_type = request.session.get('cloud_type', 'euca')
        from ..views import BaseView
        self.is_vpc_supported = BaseView.is_vpc_supported(request)
        self.set_error_messages()
        self.choices_manager = ChoicesManager(conn=conn)
        self.vpc_choices_manager = ChoicesManager(conn=vpc_conn)
        self.set_choices(request)
        self.cross_zone_enabled.help_text = self.cross_zone_enabled_help_text

    def set_choices(self, request):
        if self.cloud_type == 'euca' and self.is_vpc_supported:
            self.vpc_network.choices = self.vpc_choices_manager.vpc_networks(add_blank=False)
        else:
            self.vpc_network.choices = self.vpc_choices_manager.vpc_networks()
        self.vpc_subnet.choices = self.vpc_choices_manager.vpc_subnets()
        self.securitygroup.choices = self.choices_manager.security_groups(
            securitygroups=None, use_id=True, add_blank=False)
        region = request.session.get('region')
        self.zone.choices = self.get_availability_zone_choices(region)
        # using the static methods from CreateELBForm
        self.ping_protocol.choices = CreateELBForm.get_ping_protocol_choices()
        self.time_between_pings.choices = CreateELBForm.get_time_between_pings_choices()
        self.failures_until_unhealthy.choices = CreateELBForm.get_failures_until_unhealthy_choices()
        self.passes_until_healthy.choices = CreateELBForm.get_passes_until_healthy_choices()
        self.cross_zone_enabled.data = True
        # Set default choices where applicable, defaulting to first non-blank choice
        if self.cloud_type == 'aws' and len(self.zone.choices) > 1:
            self.zone.data = self.zone.choices[0]
        # Set the defailt option to be the first choice
        if len(self.vpc_network.choices) > 1:
            self.vpc_network.data = self.vpc_network.choices[0][0]

    def set_error_messages(self):
        self.name.error_msg = self.name_error_msg

    def get_availability_zone_choices(self, region):
        return self.choices_manager.availability_zones(region, add_blank=False)

    # static method for the ping protocol select options on the health checks section
    @staticmethod
    def get_ping_protocol_choices():
        return [
            ('HTTP', 'HTTP'),
            ('HTTPS', 'HTTPS'),
            ('TCP', 'TCP'),
            ('SSL', 'SSL')
        ]

    # static method for the ping time delay select options on the health checks section
    @staticmethod
    def get_time_between_pings_choices():
        return [
            ('30', _(u'30 seconds')),
            ('60', _(u'1 minute')),
            ('300', _(u'5 minutes'))
        ]

    # static method for the ping failures until unhealthy select options on the health checks section
    @staticmethod
    def get_failures_until_unhealthy_choices():
        return [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),
        ]

    # static method for the ping passes until unhealthy select options on the health checks section
    @staticmethod
    def get_passes_until_healthy_choices():
        return [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10'),
        ]


class ELBInstancesFiltersForm(BaseSecureForm):
    """Form class for filters on create ELB wizard"""
    state = wtforms.SelectMultipleField(label=_(u'Status'))
    availability_zone = wtforms.SelectMultipleField(label=_(u'Availability zone'))
    tags = TextEscapedField(label=_(u'Tags'))
    security_group = wtforms.SelectMultipleField(label=_(u'Security group'))
    vpc_id = wtforms.SelectMultipleField(label=_(u'VPC network'))
    subnet_id = wtforms.SelectMultipleField(label=_(u'VPC subnet'))

    def __init__(self, request, ec2_conn=None, autoscale_conn=None,
                 iam_conn=None, vpc_conn=None,
                 cloud_type='euca', **kwargs):
        super(ELBInstancesFiltersForm, self).__init__(request, **kwargs)
        self.request = request
        self.cloud_type = cloud_type
        from ..views import BaseView
        self.is_vpc_supported = BaseView.is_vpc_supported(request)
        self.ec2_choices_manager = ChoicesManager(conn=ec2_conn)
        self.autoscale_choices_manager = ChoicesManager(conn=autoscale_conn)
        self.iam_choices_manager = ChoicesManager(conn=iam_conn)
        self.vpc_choices_manager = ChoicesManager(conn=vpc_conn)
        self.region = request.session.get('region')
        self.availability_zone.choices = self.get_availability_zone_choices(self.region)
        self.state.choices = self.get_status_choices()
        self.security_group.choices = self.ec2_choices_manager.security_groups(add_blank=False)
        self.vpc_id.choices = self.vpc_choices_manager.vpc_networks(add_blank=False)
        if self.cloud_type == 'aws':
            self.vpc_id.choices.append(('None', _(u'No VPC')))
        self.vpc_id.choices = sorted(self.vpc_id.choices)
        self.subnet_id.choices = self.vpc_choices_manager.vpc_subnets(add_blank=False)
        self.facets = []
        self.set_search_facets()

    def set_search_facets(self):
        if self.cloud_type == 'aws':
            self.facets = [
                {'name': 'state', 'label': self.state.label.text, 'options': self.get_status_choices()},
                {'name': 'availability_zone', 'label': self.availability_zone.label.text,
                    'options': self.get_availability_zone_choices(self.region)},
                {'name': 'subnet_id', 'label': self.subnet_id.label.text,
                    'options': self.getOptionsFromChoices(self.vpc_choices_manager.vpc_subnets(add_blank=False))},
                {'name': 'security_group', 'label': self.security_group.label.text,
                    'options': self.getOptionsFromChoices(self.ec2_choices_manager.security_groups(add_blank=False))},
            ]
            vpc_choices = self.vpc_choices_manager.vpc_networks(add_blank=False)
            vpc_choices.append(('None', _(u'No VPC')))
            self.facets.append(
                {'name': 'vpc_id', 'label': self.vpc_id.label.text,
                    'options': self.getOptionsFromChoices(vpc_choices)},
            )
        else:
            self.facets = [
                {'name': 'state', 'label': self.state.label.text, 'options': self.get_status_choices()},
                {'name': 'security_group', 'label': self.security_group.label.text,
                    'options': self.getOptionsFromChoices(self.ec2_choices_manager.security_groups(add_blank=False))},
            ]
            if self.is_vpc_supported:
                self.facets.append(
                    {'name': 'subnet_id', 'label': self.subnet_id.label.text,
                        'options': self.getOptionsFromChoices(self.vpc_choices_manager.vpc_subnets(add_blank=False))},
                )
                vpc_choices = self.vpc_choices_manager.vpc_networks(add_blank=False)
                self.facets.append(
                    {'name': 'vpc_id', 'label': self.vpc_id.label.text,
                        'options': self.getOptionsFromChoices(vpc_choices)},
                )
            else:
                self.facets.append(
                    {'name': 'availability_zone', 'label': self.availability_zone.label.text,
                        'options': self.get_availability_zone_choices(self.region)},
                )

    def get_availability_zone_choices(self, region):
        return self.getOptionsFromChoices(self.ec2_choices_manager.availability_zones(region, add_blank=False))

    @staticmethod
    def get_status_choices():
        return [
            {'key': 'running', 'label': _(u'Running')},
            {'key': 'pending', 'label': _(u'Pending')},
            {'key': 'stopping', 'label': _(u'Stopping')},
            {'key': 'stopped', 'label': _(u'Stopped')},
            {'key': 'shutting-down', 'label': _(u'Terminating')},
            {'key': 'terminated', 'label': _(u'Terminated')},
        ]


# create a new SSL certificate form for the certificate modal on the create ELB wizard
class CertificateForm(BaseSecureForm):
    """Create SSL Certificate form"""
    certificate_name_error_msg = NAME_WITHOUT_SPACES_NOTICE
    certificate_name = wtforms.TextField(
        label=_(u'Certificate name'),
        validators=[validators.InputRequired(message=certificate_name_error_msg)],
    )
    private_key_error_msg = _(u'Private key is required')
    private_key = wtforms.TextAreaField(
        label=_(u'Private key'),
        validators=[validators.InputRequired(message=private_key_error_msg)],
    )
    public_key_certificate_error_msg = _(u'Public key certificate is required')
    public_key_certificate = wtforms.TextAreaField(
        label=_(u'Public key certificate'),
        validators=[validators.InputRequired(message=public_key_certificate_error_msg)],
    )
    certificate_chain = wtforms.TextAreaField(
        label=_(u'Certificate chain'),
    )
    certificates_error_msg = _(u'Certificate is required')
    certificates = wtforms.SelectField(
        label=_(u'Certificate name'),
        validators=[validators.InputRequired(message=certificates_error_msg)],
    )

    def __init__(self, request, conn=None, iam_conn=None, elb_conn=None, **kwargs):
        super(CertificateForm, self).__init__(request, **kwargs)
        self.conn = conn
        self.iam_conn = iam_conn
        self.elb_conn = elb_conn
        self.set_error_messages()
        self.certificates.choices = self.get_all_server_certs(iam_conn=self.iam_conn)
        if len(self.certificates.choices) > 1:
            self.certificates.data = self.certificates.choices[0][0]

    def set_error_messages(self):
        self.certificate_name.error_msg = self.certificate_name_error_msg
        self.private_key.error_msg = self.private_key_error_msg
        self.public_key_certificate.error_msg = self.public_key_certificate_error_msg

    # get all uploaded server certifactes for the account
    # notice that it uses IAM connection to retrive the cert list, thus not available on AWS
    def get_all_server_certs(self,  iam_conn=None, add_blank=True):
        choices = []
        certificates = {}
        if iam_conn is not None:
            certificates = self.iam_conn.get_all_server_certs()
            for cert in certificates.list_server_certificates_result.server_certificate_metadata_list:
                choices.append((cert.arn, cert.server_certificate_name))
        if len(choices) == 0:
            choices.append(('None', _(u'')))
        return sorted(set(choices))


# create a new backend certificate form for the certificate modal on the create ELB wizard
class BackendCertificateForm(BaseSecureForm):
    """Create SSL Certificate form"""
    backend_certificate_name_error_msg = NAME_WITHOUT_SPACES_NOTICE
    backend_certificate_name = wtforms.TextField(
        label=_(u'Certificate name'),
        validators=[validators.InputRequired(message=backend_certificate_name_error_msg)],
    )
    backend_certificate_body_error_msg = _(u'Backend certificate body is required')
    backend_certificate_body = wtforms.TextAreaField(
        label=_(u'Body (pem encoded)'),
        validators=[validators.InputRequired(message=backend_certificate_body_error_msg)],
    )

    def __init__(self, request, conn=None, iam_conn=None, elb_conn=None, **kwargs):
        super(BackendCertificateForm, self).__init__(request, **kwargs)
        self.conn = conn
        self.iam_conn = iam_conn
        self.elb_conn = elb_conn
        self.set_error_messages()

    def set_error_messages(self):
        self.backend_certificate_name.error_msg = self.backend_certificate_name_error_msg
        self.backend_certificate_body.error_msg = self.backend_certificate_body_error_msg
