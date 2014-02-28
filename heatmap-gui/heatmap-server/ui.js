
var map, layer, heatmap;
var lastRequestExtent;
var selectedDataset = "ro";
var point_radius = 50;  // px
var kPOINT_RADIUS_METERS = 30.;
var kPOINT_RADIUS_DEGREE = kPOINT_RADIUS_METERS / 111694.;


// Transforms the json (lat, lon, count) by applying the maps' projection.
function transform_data(inputData) {
    var transformedHeatmapData = { max: inputData.max , data: [] };
    var data = inputData.data;
    var datalen = data.length;

    // in order to use the OpenLayers Heatmap Layer we have to transform the data into
    // { max: <max>, data: [{lonlat: <OpenLayers.LonLat>, count: <count>},...]}

    while(datalen--){
        transformedHeatmapData.data.push({
            lonlat: new OpenLayers.LonLat(data[datalen].lon, data[datalen].lat),
            count: data[datalen].count
        });
    }
    return transformedHeatmapData;
};


function data_bounds(data) {
    var minLat = 90., minLon = 180., maxLat = -90., maxLon = -180.;
    for (var i = 0; i < data.length; ++i) {
        if (data[i].lat < minLat) { minLat = data[i].lat; }
        if (data[i].lat > maxLat) { maxLat = data[i].lat; }
        if (data[i].lon < minLon) { minLon = data[i].lon; }
        if (data[i].lon > maxLon) { maxLon = data[i].lon; }
    }
    bounds = new OpenLayers.Bounds();
    bounds.extend(new OpenLayers.LonLat(minLon, minLat));
    bounds.extend(new OpenLayers.LonLat(maxLon, maxLat));
    return bounds;
};


function init(){
    map = new OpenLayers.Map('heatmapArea', {
        projection: new OpenLayers.Projection("EPSG:4326"),
        displayProjection: new OpenLayers.Projection("EPSG:4326")
    });
    permalink = new OpenLayers.Control.Permalink();
    map.addControl(permalink);

    layer = new OpenLayers.Layer.OSM();

    // create heatmap layer
    heatmap = new OpenLayers.Layer.Heatmap(
        "Heatmap Layer",
        map,
        layer,
        {
            visible: true,
            radius: point_radius
        },
        {
            isBaseLayer: false,
            opacity: 0.3,
            projection: new OpenLayers.Projection("EPSG:4326")
        }
    );
    map.addLayers([layer, heatmap]);

    map.zoomToMaxExtent();
    map.zoomIn();
    lastRequestExtent = map.getExtent();

    // Load initial data from server
    //get_heatmap_extract("");
    get_heatmap_raster("");

    //$.getJSON( "dummy.json", function( data ) {
        //update_heatmap(data);
    //});
}


function get_current_map_extent() {
    return map.getExtent().transform(layer.projection, map.projection);
}


// Avoids inconsistent updates. If set, no ajax heatmapRequest will be sent.
var allowNewHeatmapRequest = true;


// Updates the heatmap with json data (lat, lon, count)
function update_heatmap(data) {
    var transformedHeatmapData = transform_data(data);
    heatmap.setDataSet(transformedHeatmapData);
    if (data.data.length) {
        allowNewHeatmapRequest = false;
        //map.zoomToExtent(data_bounds(data.data).transform(map.projection, layer.projection));
        allowNewHeatmapRequest = true;
    }
    //set_heatmap_point_scale(kPOINT_RADIUS_DEGREE);
    set_heatmap_point_scale(data.radius);
}


// Updates the radius in pixels of heatmap points in order to match meters
function set_heatmap_point_scale(targetRadius) {
    var ext, deltaLatitudeOfMap, pixelHeightOfMap;
    ext = layer.getExtent().transform(layer.projection, map.projection);
    deltaLatitudeOfMap = Math.abs(ext.top - ext.bottom);
    console.log("deltaLat = " + deltaLatitudeOfMap)
    pixelHeightOfMap = $('#heatmapArea').height();
    point_radius = targetRadius / deltaLatitudeOfMap * pixelHeightOfMap;
    // Scale the radius to get more stable colors on distant zoom levels.
    var scaleR = 16 - map.zoom;
    if (scaleR < 0) { scaleR = 0; }
    if (scaleR > 7) { scaleR = 7; }
    if (map.zoom < 6) { scaleR = map.zoom - 1; }
    console.log("scale r = " + scaleR);
    point_radius = Math.ceil(point_radius) + scaleR
    heatmap.heatmap.set("radius", point_radius)
    //console.log("setting point scale to " + point_radius)
};


var url = "http://sambesi.informatik.uni-freiburg.de:8080/index.html";
var hostname = window.location.hostname;
var port = window.location.port;
var url = "http://" + hostname + ":" + port + "/"
var lastRequestTimeStamp = 0;
var paramOfLastRequest = "none"


function milliseconds() {
    var d = new Date();
    return d.getMinutes() * 60000 + d.getSeconds() * 1000 + d.getMilliseconds();
}


function get_heatmap_extract(bbox) {
    if (allowNewHeatmapRequest) {
        var timestamp = milliseconds();
        if (paramOfLastRequest != bbox) {
            if (Math.abs(timestamp - lastRequestTimeStamp) > 500) {
                $.ajax({
                    url: url + "?heatmapRequest=" + bbox,
                    dataType: "jsonp"
                });
                lastRequestTimeStamp = timestamp;
                paramOfLastRequest = bbox;
                lastRequestExtent = map.getExtent();
                console.log("Requesting data inside " + lastRequestExtent.transform(layer.projection,map.projection).toBBOX())
            }
        }
    }
}


// Computes the GCD in meters.
// According to: http://en.wikipedia.org/wiki/Great-circle_distance
function great_circle_distance(latlon0, latlon1) {
    var lat0 = latlon0[0],
    lon0 = latlon0[1],
    lat1 = latlon1[0],
    lon1 = latlon1[1];

    var to_rad = Math.pi / 180.
    var r = 6371000.785
    var dLat = (lat1 - lat0) * to_rad
    var dLon = (lon1 - lon0) * to_rad
    var a = Math.sin(dLat / 2.) * Math.sin(dLat / 2.)
    a += (Math.cos(lat0 * to_rad) * Math.cos(lat1 * to_rad) *
          Math.sin(dLon / 2) * Math.sin(dLon / 2));
    return 2 * r * math.asin(Math.sqrt(a));
}


function get_heatmap_raster(bbox) {
    var timestamp = milliseconds();
    if (Math.abs(timestamp - lastRequestTimeStamp) > 500) {
        $.ajax({
            url: url + "?heatmapRasterRequest=" + bbox + "&dataset=" + selectedDataset,
            dataType: "jsonp"
        });
        lastRequestTimeStamp = timestamp;
        paramOfLastRequest = bbox;
        lastRequestExtent = map.getExtent();
        console.log("Requesting raster data inside " + lastRequestExtent.transform(layer.projection,map.projection).toBBOX())
        console.log("Dataset is " + selectedDataset);
    }
}


// Parses the JSON data which come in the following format:
// json = {
//    datacount : int,
//    max       : float,
//    radius    : float (latitude degrees),
//    data      : [lat0,lon0,count0,lat1,lon1,count1,...]
// }
function parse_datastring(json) {
    var length = json.datacount;
    var result = { max: 0 , data: [] };
    var maxi = 0;
    for (var i = 0; i < length; i++) {
        var heat = parseFloat(json.datapoints[3*i+2]);
        maxi = Math.max(maxi, heat);
        result.data.push({
            lat :   parseFloat(json.datapoints[3*i]),
            lon :   parseFloat(json.datapoints[3*i+1]),
            count : heat
        });
    }
    // Scale the maximum to get more stable colors when zooming.
    //result.max = maxi;
    var factor = (map.zoom - 11);
    if (!factor || factor < 1) { factor = 1; }
    factor = Math.sqrt(factor);
    result.max = json.max * factor;

    result.radius = json.radius;
    return result;
}

var allowCentering = true
function heatmap_request_callback(json) {
    console.log("Received JSONP with " + json.datacount + " elements.")
    console.log(json)
    if (json.datacount > 1) {
        var data = parse_datastring(json);
        update_heatmap(data);
        if (allowCentering) {
            //console.log("Allow initial centering.")
            allowCentering = false;
            map.zoomToExtent(
                data_bounds(data.data).transform(map.projection,
                                                 layer.projection)
            );
        }
    }
}


function select_dataset(shortName) {
  selectedDataset = shortName;
  allowCentering = true;  // Allow centering for this request.
  get_heatmap_raster("");
}

window.onload = function() {
    init();
    set_heatmap_point_scale(kPOINT_RADIUS_DEGREE);

    // register event handlers
    map.events.register("zoomend", map, function(){
        if (!lastRequestExtent.containsBounds(get_current_map_extent())) {
            //get_heatmap_extract(get_current_map_extent().toBBOX());

        }
        get_heatmap_raster(get_current_map_extent().toBBOX());
        set_heatmap_point_scale(kPOINT_RADIUS_DEGREE);
        console.log("Zoom level " + map.zoom);
    });

    map.events.register("moveend", map, function(){
        if (!lastRequestExtent.containsBounds(get_current_map_extent())) {
            //get_heatmap_extract(get_current_map_extent().toBBOX());
        }
        get_heatmap_raster(get_current_map_extent().toBBOX());
        set_heatmap_point_scale(kPOINT_RADIUS_DEGREE);
    });


    $('#data-toggle-de').click(function() {
      select_dataset("de");
    });
    $('#data-toggle-at').click(function() {
      select_dataset("at");
    });
    $('#data-toggle-ch').click(function() {
      select_dataset("ch");
    });
    $('#data-toggle-ro').click(function() {
      select_dataset("ro");
    });
};


// Loading animation
$(document).on({
  ajaxStart: function() {
    $("body").addClass("loading");
  },
  ajaxStop: function() {
    $("body").removeClass("loading");
  }
});


$(document).ready(function(){
    allowCentering = true
    lastRequestTimeStamp = 0;
    paramOfLastRequest = "none"

    // Show only home.
    $('#about').hide();

    // Add actions to nav buttons.
    $('#nav-home').click(function(){
        var hash = window.location.hash;
        $('#home').show();
        $('#nav-home').addClass('active');
        $('#about').hide();
        $('#nav-about').removeClass('active');
    });
    $('#nav-about').click(function(){
        var hash = window.location.hash;
        $('#about').show();
        $('#nav-about').addClass('active');
        $('#home').hide();
        $('#nav-home').removeClass('active');
    });
    //$('img.simzoom').addpowerzoom(); //add zoom effect to images with CSS class "simzoom"
});
