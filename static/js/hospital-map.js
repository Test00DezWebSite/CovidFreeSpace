// Path variables
var API_KEY = "AIzaSyC3ABfQlr8Nj-T8xLSLcWePhYzA982e87k";
var locationName = window.dlocation;

// Constants
var cityZoomLevel = 11;

// Map object.
var map;

// Google Maps API Services and Libraries.
var geocoder;
var infowindow;
var service;

// Export this callback to google maps api.
window.initMap = () => {
    // Initialize map and libraries.
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: cityZoomLevel
    });
    geocoder = new google.maps.Geocoder();
    infowindow = new google.maps.InfoWindow();
    service = new google.maps.places.PlacesService(map);

    // Geocode location.
    geocoder.geocode({ address: locationName }, function(results, status) {
        if (status == "OK") {
            var locationLatLng = results[0].geometry.location;
            var locationBounds = results[0].geometry.bounds;
            if (locationBounds === undefined) {
                // Bounds is optional field, so as fallback, use viewport.
                locationBounds = results[0].geometry.viewport;
            }

            map.setCenter(locationLatLng);

            var nearbyHospitalRequest = {
                location: locationLatLng,
                bounds: locationBounds,
                type: ["hospital"]
            };

            service.nearbySearch(nearbyHospitalRequest, nearbyHospitalCallback);
        } else {
            console.log(
                "Geocode was not successful for the following reason: " + status
            );
        }
    });
};

function nearbyHospitalCallback(results, status) {
    if (status == google.maps.places.PlacesServiceStatus.OK) {
        for (var i = 0; i < results.length; i++) {
            createMarker(results[i]);
        }
    } else {
        console.log(
            "Geocode was not successful for the following reason: " + status
        );
    }
}

function createMarker(place) {
    var placeLoc = place.geometry.location;
    var marker = new google.maps.Marker({
        map: map,
        position: place.geometry.location
    });

    google.maps.event.addListener(marker, "click", function() {
        // Used to print the place object for development purposes.
        console.log(place);

        infowindow.setContent(createContent(place));
        infowindow.open(map, this);
    });
}

/**
 * Returns an ugly content string for infowindow,
 *
 * I couldn't find a library function to do this.
 */
function createContent(place) {
    const imgSrc = place.photos
        ? place.photos[0].getUrl({ maxWidth: 200, maxHeight: 200 })
        : "";

    return `
    <img src="${imgSrc}">
    <h3>${place.name}</h3>
    <p>Rating: ${place.rating}/5.0</p>
  `;
}
