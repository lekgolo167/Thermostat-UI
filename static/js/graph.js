window.onload = function() {

    httpGetAsync('/plot', function(result) {
        result = JSON.parse(result.responseText)

        const data = {
            datasets: [{
                    label: 'Inside',
                    borderColor: '#e74e4e',
                    //showLine: false,
                    radius: 0,
                    fill: false,
                    cubicInterpolationMode: 'monotone',
                    data: result.inside
                },
                {
                    label: 'Schedule',
                    data: result.schedule,
                    borderColor: '#18a1f0',
                    borderDash: [15, 3, 3, 3],
                    fill: false,
                    backgroundColor: 'rgba(75,192,192,0.1)',
                    stepped: true,
                }, {
                    label: 'Outside',
                    borderColor: '#5bcc1af3',
                    radius: 0,
                    fill: false,
                    cubicInterpolationMode: 'monotone',
                    data: result.outside
                }
            ]
        };
        const totalDuration = 1500;
        const delayBetweenPoints = totalDuration / result.inside.length;
        const previousY = (ctx) => ctx.index === 0 ? ctx.chart.scales.y.getPixelForValue(100) : ctx.chart.getDatasetMeta(ctx.datasetIndex).data[ctx.index - 1].getProps(['y'], true).y;
        const animation = {
            x: {
                type: 'number',
                easing: 'linear',
                duration: delayBetweenPoints,
                from: NaN, // the point is initially skipped
                delay(ctx) {
                    if (ctx.type !== 'data' || ctx.xStarted) {
                        return 0;
                    }
                    ctx.xStarted = true;
                    return ctx.index * delayBetweenPoints;
                }
            },
            y: {
                type: 'number',
                easing: 'linear',
                duration: delayBetweenPoints,
                from: previousY,
                delay(ctx) {
                    if (ctx.type !== 'data' || ctx.yStarted) {
                        return 0;
                    }
                    ctx.yStarted = true;
                    return ctx.index * delayBetweenPoints;
                }
            }
        };
        const config = {
            type: 'neuline',
            data: data,

            options: {
                animation,
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
                                hour: 'h:mm a'
                            },
                            tooltipFormat: 'h:mm a'
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