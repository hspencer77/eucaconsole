/**
 * @fileOverview ELB Detail Page JS
 * @requires AngularJS
 *
 */

angular.module('ELBPage', ['EucaConsoleUtils', 'ELBListenerEditor', 'TagEditor', 'MagicSearch'])
    .controller('ELBPageCtrl', function ($scope, $timeout, eucaUnescapeJson) {
        $scope.elbForm = undefined;
        $scope.thisTab = '';
        $scope.listenerArray = [];
        $scope.securityGroups = [];
        $scope.availabilityZones = []; 
        $scope.selectedZoneList = [];
        $scope.unselectedZoneList = [];
        $scope.allZoneList = [];
        $scope.vpcNetwork = 'None';
        $scope.newVPCSubnet = 'None';
        $scope.newZone = 'None';
        $scope.vpcSubnetList = [];
        $scope.selectedVPCSubnetList = [];
        $scope.unselectedVPCSubnetList = [];
        $scope.allVPCSubnetList = [];
        $scope.allInstanceList = [];
        $scope.ELBInstanceHealthList = [];
        $scope.instanceList = [];
        $scope.isCrossZoneEnabled = '';
        $scope.classCrossZoneEnabled = 'active';
        $scope.classCrossZoneDisabled = 'inactive';
        $scope.pingProtocol = '';
        $scope.pingPort = '';
        $scope.pingPath = '';
        $scope.responseTimeout = '';
        $scope.timeBetweenPings = '';
        $scope.failuresUntilUnhealthy = '';
        $scope.passesUntilHealthy = '';
        $scope.isNotChanged = true;
        $scope.isInitComplete = false;
        $scope.unsavedChangesWarningModalLeaveCallback = null;
        $scope.initController = function (optionsJson) {
            var options = JSON.parse(eucaUnescapeJson(optionsJson));
            $scope.setInitialValues(options);
            $scope.setWatch();
            $scope.setFocus();
            // timeout is needed to indicate all Angular model initialization steps are complete
            // This is to prevent Foundation validation form raising false negative warnings
            $timeout(function(){
                $scope.isInitComplete = true;
            }, 1000);
        };
        $scope.setInitialValues = function (options) {
            if ($('#elb-view-form').length > 0) {
                $scope.elbForm = $('#elb-view-form');
            }
            // ?tab= value will be read from URL to determine which tab section to be displayed when the page first loaded
            var urlParams = $.url().param();
            if (urlParams.tab) {
                $scope.thisTab = urlParams.tab;
                $scope.toggleTab($scope.thisTab);
            }
            // current security group list for this elb
            if (options.hasOwnProperty('securitygroups')) {
                if (options.securitygroups instanceof Array && options.securitygroups.length > 0) {
                    $scope.securityGroups = options.securitygroups;
                    // Timeout is needed for chosen to react after Angular updates the options
                    $timeout(function(){
                        $('#securitygroup').trigger('chosen:updated');
                    }, 500);
                }
            }
            // code from David's initial work
            if (options.hasOwnProperty('in_use')) {
                $scope.elbInUse = options.in_use;
            }
            // code from David's initial work
            if (options.hasOwnProperty('has_image')) {
                $scope.hasImage = options.has_image;
            }
            if (!$scope.hasImage) {
                $('#image-missing-modal').foundation('reveal', 'open');
            }
            // all az zones list
            if (options.hasOwnProperty('availability_zone_choices')) {
                $scope.allZoneList = options.availability_zone_choices;
            }
            // az zone selected for this elb
            if (options.hasOwnProperty('availability_zones')) {
                $scope.availabilityZones = options.availability_zones;
                // Timeout is needed for the instance selector to be initialized 
                $timeout(function () {
                    $scope.$broadcast('eventUpdateAvailabilityZones', $scope.availabilityZones);
                }, 500);
            }
            // all vpc subnet choices
            if (options.hasOwnProperty('vpc_subnet_choices')) {
                $scope.allVPCSubnetList = options.vpc_subnet_choices;
            }
            // vpc network for this elb
            if (options.hasOwnProperty('elb_vpc_network')) {
                if (options.elb_vpc_network !== null) {
                    $scope.vpcNetwork = options.elb_vpc_network;
                    // Timeout is needed for the instance selector to be initizalized
                    $timeout(function () {
                        // signal to inform the instance selector widget
                        $scope.$broadcast('eventWizardUpdateVPCNetwork', $scope.vpcNetwork);
                    }, 500);
                }
            }
            // vpc subnets for this elb
            if (options.hasOwnProperty('elb_vpc_subnets')) {
                $scope.vpcSubnetList = options.elb_vpc_subnets;
            }
            // all instances list
            if (options.hasOwnProperty('all_instances')) {
                $scope.allInstanceList = options.all_instances;
            }
            // instance health list for this elb 
            if (options.hasOwnProperty('elb_instance_health')) {
                $scope.ELBInstanceHealthList = options.elb_instance_health;
            }
            // flag for the cross zone load balancer for this elb
            if (options.hasOwnProperty('is_cross_zone_enabled')) {
                $scope.isCrossZoneEnabled = options.is_cross_zone_enabled;
            }
            // currently selected instances for this elb
            if (options.hasOwnProperty('instances')) {
                $scope.instanceList = options.instances;
                // Timeout is needed for the instance selector to be initizalized
                $timeout(function () {
                    // signal to inform the instance selector widget on the currently selected instance list
                    $scope.$broadcast('eventInitSelectedInstances', $scope.instanceList);
                }, 2000);
            }
            // health check ping protocol for this elb 
            if (options.hasOwnProperty('health_check_ping_protocol')) {
                $scope.pingProtocol = options.health_check_ping_protocol;
            }
            // health check ping port for this elb 
            if (options.hasOwnProperty('health_check_ping_port')) {
                $scope.pingPort = parseInt(options.health_check_ping_port);
            }
            // health check ping path for this elb 
            if (options.hasOwnProperty('health_check_ping_path')) {
                $scope.pingPath = options.health_check_ping_path;
            }
            // health check interval for this elb 
            if (options.hasOwnProperty('health_check_interval')) {
                $scope.timeBetweenPings = options.health_check_interval;
            }
            // health check timeout for this elb 
            if (options.hasOwnProperty('health_check_timeout')) {
                $scope.responseTimeout = options.health_check_timeout;
            }
            // health check unhealthy threshold for this elb 
            if (options.hasOwnProperty('health_check_unhealthy_threshold')) {
                $scope.failuresUntilUnhealthy = options.health_check_unhealthy_threshold;
            }
            // health check healthy threshold for this elb 
            if (options.hasOwnProperty('health_check_healthy_threshold')) {
                $scope.passesUntilHealthy = options.health_check_healthy_threshold;
            }
            $scope.initChosenSelectors(); 
        };
        $scope.initChosenSelectors = function () {
            $('#securitygroup').chosen({'width': '70%', search_contains: true});
        };
        $scope.setWatch = function () {
            $(document).on('submit', '[data-reveal] form', function () {
                $(this).find('.dialog-submit-button').css('display', 'none');
                $(this).find('.dialog-progress-display').css('display', 'block');
            });
            $scope.$watch('securityGroups', function () {
                // wait for the intialization of the angular model to be complete
                // then monitor the update in the value to inform whether there has been update on the page
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
            }, true);
            $scope.$watch('availabilityZones', function () {
                // update the selected az list for the tile display
                $scope.updateSelectedZoneList();
                // signal to inform the instance selector
                $scope.$broadcast('eventUpdateAvailabilityZones', $scope.availabilityZones);
            }, true);
            $scope.$watch('selectedZoneList', function () {
                // when the selected az list is updated,
                // also update the unselected az list for the option list on the az select element
                $scope.updateUnselectedZoneList();
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
            }, true);
            $scope.$watch('vpcSubnetList', function () {
                // update the selected vpc subnet list for the tile display
                $scope.updateSelectedVPCSubnetList();
            }, true);
            $scope.$watch('selectedVPCSubnetList', function () {
                // update the unselected vpc subnet list for the option list on the vpc subnet selecte element
                $scope.updateUnselectedVPCSubnetList(); 
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
            }, true);
            $scope.$watch('instanceList', function () {
                // signal to inform the instance selector
                $scope.$broadcast('eventInitSelectedInstances', $scope.instanceList);
            }, true);
            $scope.$watch('isCrossZoneEnabled', function () {
                // handle the active link display for the cross zone load balancer field
                if ($scope.isCrossZoneEnabled === true) {
                    $scope.classCrossZoneEnabled = 'active';
                    $scope.classCrossZoneDisabled = 'inactive';
                } else {
                    $scope.classCrossZoneEnabled = 'inactive';
                    $scope.classCrossZoneDisabled = 'active';
                }
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
            });
            $scope.$watch('pingProtocol', function () {
                // update the ping path value when the ping protocol is updated
                $scope.updatePingPath();
            });
            $scope.$watch('isNotChanged', function () {
                // inactivate the navigation tab when there exist updates on the current page
                if ($scope.isNotChanged === false) {
                    $('#elb-view-tabs').removeAttr('data-tab');
                } else {
                    $('#elb-view-tabs').attr('data-tab', '');
                }
            });
            $scope.$on('searchUpdated', function ($event, query) {
                // Relay the query search update signal
                $scope.$broadcast('eventQuerySearch', query);
            });
            $scope.$on('textSearch', function ($event, searchVal, filterKeys) {
                // Relay the text search update signal
                $scope.$broadcast('eventTextSearch', searchVal, filterKeys);
            });
            $scope.$on('eventUpdateListenerArray', function ($event, listenerArray) {
                // accepts the signal from the elb listener edior on the listener array update
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
                $scope.listenerArray = listenerArray;
            });
            $scope.$on('tagUpdate', function($event) {
                // in case of tag update, mark the input update flag 
                $scope.isNotChanged = false;
            });
            // handle the input update detection on the general tab page
            $(document).on('input', '#general-tab input[type="text"]', function () {
                $scope.isNotChanged = false;
                $scope.$apply();
            });
            // handle the input update detection on the instance tab page
            $(document).on('click', '#instances-tab input[type="checkbox"]', function () {
                $scope.isNotChanged = false;
                $scope.$apply();
            });
            // handle the input update detection on the health checks tab page
            $(document).on('input', '#health-checks-tab input', function () {
                $scope.isNotChanged = false;
                $scope.$apply();
            });
            // handle the input update detection on the health checks tab page
            $(document).on('change', '#health-checks-tab select', function () {
                $scope.isNotChanged = false;
                $scope.$apply();
            });
            // Leave button is clicked on the warning unsaved changes modal
            $(document).on('click', '#unsaved-changes-warning-modal-stay-button', function () {
                $('#unsaved-changes-warning-modal').foundation('reveal', 'close');
            });
            // Stay button is clicked on the warning unsaved changes modal
            $(document).on('click', '#unsaved-changes-warning-modal-leave-link', function () {
                $scope.unsavedChangesWarningModalLeaveCallback();
            });
        };
        // setFocus function below is copy-and-pasted from another page. Need to be worked on.
        $scope.setFocus = function () {
            $(document).on('ready', function(){
                $('.actions-menu').find('a').get(0).focus();
            });
            $(document).on('opened.fndtn.reveal', '[data-reveal]', function () {
                var modal = $(this);
                var modalID = $(this).attr('id');
                if( modalID.match(/terminate/)  || modalID.match(/delete/) || modalID.match(/release/) ){
                    var closeMark = modal.find('.close-reveal-modal');
                    if(!!closeMark){
                        closeMark.focus();
                    }
                }else{
                    var inputElement = modal.find('input[type!=hidden]').get(0);
                    var modalButton = modal.find('button').get(0);
                    if (!!inputElement) {
                        inputElement.focus();
                    } else if (!!modalButton) {
                        modalButton.focus();
                    }
               }
            });
        };
        // for opening the unsave changes warning modal
        $scope.openModalById = function (modalID) {
            var modal = $('#' + modalID);
            modal.foundation('reveal', 'open');
            modal.find('h3').click();  // Workaround for dropdown menu not closing
        };
        $scope.clickTab = function ($event, tab){
            $event.preventDefault();
            // If there exists unsaved changes, open the warning modal instead
            if ($scope.isNotChanged === false) {
                $scope.openModalById('unsaved-changes-warning-modal');
                $scope.unsavedChangesWarningModalLeaveCallback = function() {
                    $scope.isNotChanged = true;
                    $scope.$apply();
                    $scope.toggleTab(tab);
                    $('#unsaved-changes-warning-modal').foundation('reveal', 'close');
                };
                return;
            } 
            $scope.toggleTab(tab);
        };
        $scope.toggleTab = function (tab) {
            $(".tabs").children("dd").each(function() {
                var id = $(this).find("a").attr("href").substring(1);
                var $container = $("#" + id);
                $(this).removeClass("active");
                $container.removeClass("active");
                if (id == tab || $container.find("#" + tab).length) {
                    $(this).addClass("active");
                    $container.addClass("active");
                    $scope.currentTab = id; // Update the currentTab value for the help display
                    $scope.$broadcast('updatedTab', $scope.currentTab);
                }
            });
        };
        $scope.updateSelectedZoneList = function () {
            var selected = [];
            angular.forEach($scope.availabilityZones, function (zoneID) {
                angular.forEach($scope.allZoneList, function (zone) {
                    zone.instanceCount = $scope.getInstanceCountInZone(zone);
                    zone.unhealthyInstanceCount = $scope.getUnhealthyInstanceCountInZone(zone);
                    if (zoneID === zone.id) {
                        selected.push(zone);
                    }
                });
            });
            $scope.selectedZoneList = selected;
        };
        $scope.updateUnselectedZoneList = function () {
            var allList = $scope.allZoneList;
            var unselected = [];
            var placeholder = {};
            placeholder.id = 'None';
            placeholder.name = $('#hidden_zone_selector_placeholder').text(); 
            unselected.push(placeholder);
            angular.forEach(allList, function (zone) {
                var isSelected = false;
                angular.forEach($scope.selectedZoneList, function (thisZone, $index) {
                    if (thisZone.id === zone.id) {
                       isSelected = true;
                    }
                });
                if (isSelected === false) {
                    zone.instanceCount = $scope.getInstanceCountInZone(zone);
                    zone.unhealthyInstanceCount = $scope.getUnhealthyInstanceCountInZone(zone);
                    unselected.push(zone);
                }
            });
            $scope.unselectedZoneList = unselected;
            $scope.newZone = placeholder;
        };
        $scope.updateSelectedVPCSubnetList = function () {
            var selected = [];
            angular.forEach($scope.vpcSubnetList, function (subnetID) {
                angular.forEach($scope.allVPCSubnetList, function (subnet) {
                    if (subnetID === subnet.id) {
                        subnet.instanceCount = $scope.getInstanceCountInSubnet(subnet.id);
                        subnet.unhealthyInstanceCount = $scope.getUnhealthyInstanceCountInSubnet(subnet.id);
                        selected.push(subnet);
                    }
                });
            });
            $scope.selectedVPCSubnetList = selected;
        };
        $scope.updateUnselectedVPCSubnetList = function () {
            var allList = $scope.allVPCSubnetList;
            var unselected = [];
            var placeholder = {};
            placeholder.id = 'None';
            placeholder.name = $('#hidden_subnet_selector_placeholder').text(); 
            unselected.push(placeholder);
            angular.forEach(allList, function (subnet) {
                var isSelected = false;
                angular.forEach($scope.selectedVPCSubnetList, function (thisSubnet, $index) {
                    if (thisSubnet.id === subnet.id) {
                       isSelected = true;
                    }
                });
                if (isSelected === false && subnet.vpc_id === $scope.vpcNetwork) {
                    subnet.instanceCount = $scope.getInstanceCountInSubnet(subnet.id);
                    subnet.unhealthyInstanceCount = $scope.getUnhealthyInstanceCountInSubnet(subnet.id);
                    unselected.push(subnet);
                }
            });
            $scope.unselectedVPCSubnetList = unselected;
            $scope.newVPCSubnet = placeholder;
        };
        $scope.getInstanceCountInZone = function (zone) {
            var count = 0;
            angular.forEach($scope.ELBInstanceHealthList, function (instanceHealth) {
                angular.forEach($scope.allInstanceList, function (instance) {
                    if (instanceHealth.instance_id === instance.id) {
                        if (instance.zone === zone.id) {
                            count += 1;
                        }
                    }
                });
            });
            return count;
        };
        $scope.getInstanceCountInSubnet = function (subnetID) {
            var count = 0;
            angular.forEach($scope.ELBInstanceHealthList, function (instanceHealth) {
                angular.forEach($scope.allInstanceList, function (instance) {
                    if (instanceHealth.instance_id === instance.id) {
                        if (instance.subnet_id === subnetID) {
                            count += 1;
                        }
                    }
                });
            });
            return count;
        };
        $scope.getUnhealthyInstanceCountInZone = function (zone) {
            var count = 0;
            angular.forEach($scope.ELBInstanceHealthList, function (instanceHealth) {
                if (instanceHealth.state === 'OutOfService') {
                    angular.forEach($scope.allInstanceList, function (instance) {
                        if (instanceHealth.instance_id === instance.id) {
                            if (instance.zone === zone.id) {
                                count += 1;
                            }
                        }
                    });
                }
            });
            return count;
        };
        $scope.getUnhealthyInstanceCountInSubnet = function (subnetID) {
            var count = 0;
            angular.forEach($scope.ELBInstanceHealthList, function (instanceHealth) {
                if (instanceHealth.state === 'OutOfService') {
                    angular.forEach($scope.allInstanceList, function (instance) {
                        if (instanceHealth.instance_id === instance.id) {
                            if (instance.subnet_id === subnetID) {
                                count += 1;
                            }
                        }
                    });
                }
            });
            return count;
        };
        $scope.clickEnableZone = function ($event) {
            $event.preventDefault();
            if ($scope.newZone.id === 'None') {
                return;
            }
            angular.forEach($scope.unselectedZoneList, function (zone, $index) {
                if ($scope.newZone.id === zone.id) {
                    $scope.selectedZoneList.push(zone);
                    $scope.unselectedZoneList.splice($index, 1);
                }
            });
        };
        $scope.clickEnableVPCSubnet = function ($event) {
            $event.preventDefault();
            if ($scope.newVPCSubnet.id === 'None') {
                return;
            }
            angular.forEach($scope.unselectedVPCSubnetList, function (subnet, $index) {
                if ($scope.newVPCSubnet.id === subnet.id) {
                    $scope.selectedVPCSubnetList.push(subnet);
                    $scope.unselectedVPCSubnetList.splice($index, 1);
                }
            });
        };
        $scope.clickDisableZone = function (thisZoneID) {
            angular.forEach($scope.selectedZoneList, function (zone, $index) {
                if (thisZoneID === zone.id) {
                    $scope.selectedZoneList.splice($index, 1);
                    $scope.unselectedZoneList.push(zone);
                }
            });
        };
        $scope.clickDisableVPCSubnet = function (thisSubnetID) {
            angular.forEach($scope.selectedVPCSubnetList, function (subnet, $index) {
                if (thisSubnetID === subnet.id) {
                    $scope.selectedVPCSubnetList.splice($index, 1);
                    $scope.unselectedVPCSubnetList.push(subnet);
                }
            });
        };
        $scope.clickCrossZoneLink = function (click) {
            if (click === 'enabled') {
                $scope.isCrossZoneEnabled = true;
            } else {
                $scope.isCrossZoneEnabled = false;
            }
        };
        $scope.updatePingPath = function () {
            if ($scope.pingProtocol === 'TCP' || $scope.pingProtocol === 'SSL') {
                $scope.pingPath = 'None';
            } else if ($scope.pingProtocol === 'HTTP' || $scope.pingProtocol === 'HTTPS') {
                if ($scope.pingPath === 'None') {
                    $scope.pingPath = '';
                }
            }
        };
        $scope.submitSaveChanges = function ($event, tab) {
            $event.preventDefault();
            $scope.isNotChanged = true;
            $scope.thisTab = tab;
            // timeout is needed for the tab input to be passed
            $timeout(function() {
                $scope.elbForm.submit();
            });
        };
    })
;
