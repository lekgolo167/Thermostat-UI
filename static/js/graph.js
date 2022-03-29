function httpGetAsync(theUrl, callback) {
    let xmlHttpReq = new XMLHttpRequest();
    xmlHttpReq.onreadystatechange = function() {
        if (xmlHttpReq.readyState == 4 && xmlHttpReq.status == 200)
            callback(JSON.parse(xmlHttpReq.responseText));
    }
    xmlHttpReq.open("GET", theUrl, true); // true for asynchronous 
    xmlHttpReq.send(null);
}
window.onload = function() {
    let draw = Chart.controllers.line.prototype.draw;
    Chart.controllers.line = Object.assign(Chart.controllers.line, {
        draw: function() {
            draw.apply(this, arguments);
            let ctx = this.chart.chart.ctx;
            let _stroke = ctx.stroke;
            ctx.stroke = function() {
                ctx.save();
                ctx.shadowColor = '#E56590';
                ctx.shadowBlur = 10;
                ctx.shadowOffsetX = 0;
                ctx.shadowOffsetY = 4;
                _stroke.apply(this, arguments)
                ctx.restore();
            }
        }
    });
    httpGetAsync('/plot', function(result) {

        console.log(result.schedule);
        console.log(result.outside);
        console.log(result.inside);

        const data = {
            datasets: [{
                label: 'Schedule',
                data: result.schedule,
                borderColor: 'blue',
                fill: true,
                backgroundColor: 'rgba(75,192,192,0.1)',
                stepped: true,
            }, {
                label: 'Outside',
                borderColor: 'green',
                fill: false,
                cubicInterpolationMode: 'monotone',
                data: result.outside
            }, {
                label: 'inside',
                borderColor: 'red',
                //showLine: false,
                radius: 0,
                fill: false,
                cubicInterpolationMode: 'monotone',
                data: result.inside
            }]
        };
        const config = {
            type: 'line',
            data: data,

            options: {
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            major: {
                                enabled: true
                            }
                        },
                        min: '00:00',
                        max: '23:59',
                        type: 'time',
                        time: {
                            parser: 'HH:mm',
                            unit: 'hour',
                            displayFormats: {
                                hour: 'h:mm'
                            }
                        }
                    },

                    y: {
                        grid: {
                            display: false
                        }
                    }
                },
                responsive: true,
                interaction: {
                    intersect: false,
                    axis: 'x'
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Interpolation',
                    }
                }
            }
        };
        let ctx = document.getElementById("scheduleGraph").getContext('2d');

        let scheduleGraph = new Chart(ctx, config)
    });
}