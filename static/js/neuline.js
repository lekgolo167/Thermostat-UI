class NeuLine extends Chart.LineController {
    draw() {
        let ctx = this.chart.ctx;
        let _stroke = ctx.stroke;

        ctx.stroke = function() {
            ctx.save();
            ctx.shadowColor = '#919191';
            ctx.shadowBlur = 15;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 5;
            _stroke.apply(this, arguments)
            ctx.restore();
        }
        super.draw(arguments);

    }
}

NeuLine.id = 'neuline';
NeuLine.defaults = Chart.LineController.defaults;

Chart.register(NeuLine);