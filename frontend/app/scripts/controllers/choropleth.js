'use strict';

angular.module('frontendApp')
  .controller('ChoroplethCtrl', ['$scope', 'Mappings', function ($scope, Mappings) {
    // Generate some dummy data
    $scope.newData = function() {
      $scope.districtData = _.map(Mappings.getAllDistricts(), function(district) {
        return {code: district, value: Math.random() * 100};
      });

      $scope.areaData = _.map(Mappings.getAllAreas(), function(area){
        return {code: area, value: Math.random() * 100};
      });
    };
    $scope.newData();

    $scope.indicators = [
      {name: 'foo', identifier: 'bar'},
      {name: 'bar', identifier: 'baz'}
    ];

    $scope.groups = [
      {name: 'Both sexes', identifier: 'both'},
      {name: 'Male', identifier: 'male'},
      {name: 'Female', identifier: 'female'},
    ];

    $scope.mapLevel = 'ca';
    $scope.theData = $scope.areaData;
  }]);