/**
 * @fileOverview ELB Detail Page JS (General tab)
 * @requires AngularJS
 *
 */

angular.module('ELBPage', ['EucaConsoleUtils', 'ELBListenerEditor', 'TagEditor'])
    .controller('ELBPageCtrl', function ($scope, $timeout, eucaUnescapeJson, eucaHandleUnsavedChanges) {
        $scope.elbForm = undefined;
        $scope.listenerArray = [];
        $scope.securityGroups = [];
        $scope.vpcNetwork = 'None';
        $scope.isNotChanged = true;
        $scope.isInitComplete = false;
        $scope.unsavedChangesWarningModalLeaveCallback = null;
        $scope.initController = function (optionsJson) {
            var options = JSON.parse(eucaUnescapeJson(optionsJson));
            $scope.setInitialValues(options);
            $scope.setWatch();
            $timeout(function(){
                // Prevent Foundation validation from raising false negative warnings
                $scope.isInitComplete = true;
            }, 1000);
        };
        $scope.setInitialValues = function (options) {
            if ($('#elb-view-form').length > 0) {
                $scope.elbForm = $('#elb-view-form');
            }
            if (options.securitygroups instanceof Array && options.securitygroups.length > 0) {
                $scope.securityGroups = options.securitygroups;
                // Timeout is needed for chosen to react after Angular updates the options
                $timeout(function(){
                    $('#securitygroup').trigger('chosen:updated');
                }, 500);
            }
            if (options.elb_vpc_network !== null) {
                $scope.vpcNetwork = options.elb_vpc_network;
                // Timeout is needed for the instance selector to be initizalized
                $timeout(function () {
                    $scope.$broadcast('eventWizardUpdateVPCNetwork', $scope.vpcNetwork);
                }, 500);
            }
            $scope.initChosenSelectors();
        };
        $scope.initChosenSelectors = function () {
            $('#securitygroup').chosen({'width': '70%', search_contains: true});
        };
        $scope.setWatch = function () {
            eucaHandleUnsavedChanges($scope);
            $(document).on('submit', '[data-reveal] form', function () {
                $(this).find('.dialog-submit-button').css('display', 'none');
                $(this).find('.dialog-progress-display').css('display', 'block');
            });
            $scope.$watch('securityGroups', function () {
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
            }, true);
            $scope.$on('eventUpdateListenerArray', function ($event, listenerArray) {
                if ($scope.isInitComplete === true) {
                    $scope.isNotChanged = false;
                }
                $scope.listenerArray = listenerArray;
            });
            $scope.$on('tagUpdate', function($event) {
                $scope.isNotChanged = false;
            });
            $(document).on('input', 'input', function () {
                $scope.isNotChanged = false;
                $scope.$apply();
            });
        };
        $scope.openModalById = function (modalID) {
            var modal = $('#' + modalID);
            modal.foundation('reveal', 'open');
            modal.find('h3').click();  // Workaround for dropdown menu not closing
        };
    })
;
