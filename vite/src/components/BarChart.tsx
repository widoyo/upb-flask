import { onMount } from 'solid-js';
import * as echarts from 'echarts/core';
import {
  ToolboxComponent,
  ToolboxComponentOption,
  TooltipComponent,
  TooltipComponentOption,
  GridComponent,
  GridComponentOption,
  LegendComponent,
  LegendComponentOption
} from 'echarts/components';
import { BarChart, BarSeriesOption } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  ToolboxComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  BarChart,
  CanvasRenderer
]);

type EChartsOption = echarts.ComposeOption<
  | ToolboxComponentOption
  | TooltipComponentOption
  | GridComponentOption
  | LegendComponentOption
  | BarSeriesOption
>;

let app: any = {};
const posList = [
    'left',
    'right',
    'top',
    'bottom',
    'inside',
    'insideTop',
    'insideLeft',
    'insideRight',
    'insideBottom',
    'insideTopLeft',
    'insideTopRight',
    'insideBottomLeft',
    'insideBottomRight'
  ] as const;
  
app.configParameters = {
    rotate: {
      min: -90,
      max: 90
    },
    align: {
      options: {
        left: 'left',
        center: 'center',
        right: 'right'
      }
    },
    verticalAlign: {
      options: {
        top: 'top',
        middle: 'middle',
        bottom: 'bottom'
      }
    },
    position: {
      options: posList.reduce(function (map, pos) {
        map[pos] = pos;
        return map;
      }, {} as Record<string, string>)
    },
    distance: {
      min: 0,
      max: 100
    }
  };
  
  app.config = {
    rotate: 90,
    align: 'left',
    verticalAlign: 'middle',
    position: 'insideBottom',
    distance: 15,
    onChange: function () {
      const labelOption: BarLabelOption = {
        rotate: app.config.rotate as BarLabelOption['rotate'],
        align: app.config.align as BarLabelOption['align'],
        verticalAlign: app.config
          .verticalAlign as BarLabelOption['verticalAlign'],
        position: app.config.position as BarLabelOption['position'],
        distance: app.config.distance as BarLabelOption['distance']
      };
      chart.setOption<EChartsOption>({
        series: [
          {
            label: labelOption
          },
          {
            label: labelOption
          },
          {
            label: labelOption
          },
          {
            label: labelOption
          }
        ]
      });
    }
  };
  
type BarLabelOption = NonNullable<BarSeriesOption['label']>;

const labelOption: BarLabelOption = {
  show: true,
  position: app.config.position as BarLabelOption['position'],
  distance: app.config.distance as BarLabelOption['distance'],
  align: app.config.align as BarLabelOption['align'],
  verticalAlign: app.config.verticalAlign as BarLabelOption['verticalAlign'],
  rotate: app.config.rotate as BarLabelOption['rotate'],
  formatter: '{c}  {name|{a}}',
  fontSize: 16,
  rich: {
    name: {}
  }
};
var option: EChartsOption;
option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    yAxis: {}
  };
const Bar = (props) => {
    let el: HTMLDivElement = null!;
    option.xAxis = {type: 'category', data: props.x};
    const out = {type: 'bar', name: 'Kap', data: props.y};
    option.series = [];
    option.series.push(out);
    console.log(option);
    let chart;

    onMount(() => {
        console.log('onMount()');
        chart = echarts.init(el);
        chart.setOption(option);
    });
    
    return <div class="bar" style="width: 220px;height:80px;" ref={el}>
    </div>
 
}

export default Bar;