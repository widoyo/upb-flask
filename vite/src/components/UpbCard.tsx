import { splitProps, Index } from 'solid-js';
import { Card } from 'solid-bootstrap';
import Bar from './BarChart';

const UpbCard = (props) => {
    const names = props.upb.map((e) => e.name);
    console.log(names);
    const vols = props.upb.map((e) => [e.volume_potensial, e.volume_real]);
    console.log(vols);
    const upb = props.upb[0].upb;
    //const bdgs = props.upb.map((e) => e.name )
    return(
        <>
        <Card>
            <Card.Title>{props.id} UPB-{upb} ({props.upb.length})</Card.Title>
            <Card.Subtitle class="mb-2 text-muted">{props.name}</Card.Subtitle>
            <Bar x={names} y={vols}></Bar>
            <Card.Text>
                <ul>
                <Index each={props.upb}>{(e) => 
                    <li>{e().name}</li>
                }</Index>
                </ul>
            </Card.Text>
        </Card>
    </>
    )
    
}


export default UpbCard;