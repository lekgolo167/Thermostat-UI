function httpGetAsync(theUrl, callback) {
    let xmlHttpReq = new XMLHttpRequest();
    xmlHttpReq.onreadystatechange = function() {
        if (xmlHttpReq.readyState == 4) {
            console.log(xmlHttpReq)
            callback(xmlHttpReq);
        }
    }
    xmlHttpReq.open("GET", theUrl, true); // true for asynchronous 
    xmlHttpReq.send(null);
}

function handleResponse(response, reload) {

    msg = JSON.parse(response.responseText)['message']
    if (response.status < 400) {
        console.log('success')
        if (reload) {
            Toast.showAfterReload(msg, 'success');
            console.log('toast set......reloading')
            history.go(0);
        } else {
            Toast.show(msg, 'success');
        }
    } else {
        Toast.show(msg, 'error');
    }
};

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

function simParams() {
    let form = document.getElementById('simParams');
    let button = document.getElementById('showHide');
    if (form.style.display === "none") {
        form.style.display = "block";
        button.innerHTML = "Hide Advanced";
    } else {
        form.style.display = "none";
        button.innerHTML = "Show Advanced";
    }
}

function setTemporaryTemp() {
    let degrees = document.getElementById('set-temp').value;
    httpGetAsync('/setTemporaryTemp/' + degrees, function(result) {
        console.log(result);
        handleResponse(result, false);
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
            handleResponse(result, true);
        });
    } else {
        httpGetAsync('/update/' + id + '/' + degrees + '/' + hour + '/' + min, function(result) {
            console.log(result);
            handleResponse(result, true);
        });
    }
}

function deleteCycle(id) {
    httpGetAsync('/delete/' + id, function(result) {
        console.log(result);
        handleResponse(result, true);
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