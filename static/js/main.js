function httpGetAsync(theUrl, callback) {
    let xmlHttpReq = new XMLHttpRequest();
    xmlHttpReq.onreadystatechange = function() {
        if (xmlHttpReq.readyState == 4 && xmlHttpReq.status == 200) {
            console.log(xmlHttpReq)
            callback(JSON.parse(xmlHttpReq.responseText));
        }
    }
    xmlHttpReq.open("GET", theUrl, true); // true for asynchronous 
    xmlHttpReq.send(null);
}

var slider = document.getElementById("temp-slider");
var output = document.getElementById("set-temp");

function temperatureSliderCallback() {
    var x = slider.value;
    var color = 'linear-gradient(90deg, #185ef0, #30cfd0 ' + x + '%, #00000000 ' + x + '%)';
    slider.style.background = color;
    var t = Math.trunc(map(x, 1, 100, min_t, max_t));
    output.innerHTML = t;
}
slider.addEventListener("touchmove", temperatureSliderCallback, false);
slider.addEventListener("mousemove", temperatureSliderCallback, false);

function map(x, in_min, in_max, out_min, out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

function setTemporaryTemp() {
    let degrees = document.getElementById('set-temp').value;
    httpGetAsync('/setTemporaryTemp/' + degrees, function(result) {
        console.log(result);
    });
}

function updateCycle(id) {
    let degrees = document.getElementById('set-temp').value;
    let min = Number(document.getElementById('minute').value);
    let hour = Number(document.getElementById('hour').value);
    let ante = document.getElementById('ante').value;
    if (ante === 'PM') {
        if (hour !== 12) {
            hour += 12;
        }
    } else if (hour === 12) {
        hour = 0;
    }
    if (id === 0) {
        httpGetAsync('/newCycle/' + degrees + '/' + hour + '/' + min, function(result) {
            console.log(result);
            location.reload()
        });
    } else {
        httpGetAsync('/update/' + id + '/' + degrees + '/' + hour + '/' + min, function(result) {
            console.log(result);
            location.reload()
        });
    }
}

function deleteCycle(id) {
    httpGetAsync('/delete/' + id, function(result) {
        console.log(result);
        location.reload()
    })
}

function setDay(day) {
    httpGetAsync('/setDay/' + day, function(result) {
        console.log(result);
        location.reload()
    })
}

window.addEventListener("load", function() {
    tp.attach({
        target: "sel_time",
        wrap: "time_picker"
    });
});