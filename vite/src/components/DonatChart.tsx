import * as echarts from 'echarts/core';
import { ECharts } from "echarts";

import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components';
import { PieChart } from 'echarts/charts';
import { LabelLayout } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';
import { onMount } from 'solid-js';

echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  CanvasRenderer,
  LabelLayout
]);

export interface DonatWrapperProps {
    plotData?: any
}

function Donat(props: DonatWrapperProps) {
    let el: HTMLDivElement = null!;
    let chart: ECharts = null!;

    const plotData = {
        title: {text: props.nama},
        series: [
            {
                name: 'Bendungan',
                type: 'pie',
                data: [
                    { value: 5, name: 'Bend A'},
                    { value: 3, name: 'Bend B'},
                    { value: 1, name: 'Bend C'}
                ]
            }
        ]
    }
    
    onMount(() => {
        console.log('onMount()');
        chart = echarts.init(el);
        chart.setOption(plotData);
    });
    
    return <div class="donat" style="width: 120px;height:80px;" ref={el}>
    </div>
}

export default Donat; 
