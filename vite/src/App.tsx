import type { Component } from 'solid-js';
import { Index } from 'solid-js';
import data from './contoh_volume.json';
import { Container, Row, Col } from 'solid-bootstrap';
import UpbCard from './components/UpbCard';


const App: Component = () => {
	const total_potensial = data.reduce((vol_potensial, obj) => {
		return vol_potensial + obj.volume_potensial;
	}, 0);
	const total_real = data.reduce((acc, obj) => {
		return acc + obj.volume_real;}, 0);
	const persen_vol = (total_real / total_potensial) * 100;
	const list_upb = Object.values(data.reduce((row, obj) => {
		row[obj.upb] = row[obj.upb] || [];
		row[obj.upb].push(obj);
		return row;
	}, Object.create(null)));
	
	const rows = [{nama: 'UPB 1', kepala: 'Adhi Wibowo'},
	{nama: 'UPB 2', kepala: 'Diar Wibowo'}]
	return (
	<Container class="mt-5">
		<Row>
			<Col class="border">
				<div class="">
				</div>
			
			</Col>
			<Col class="border">Sebanyak {data.length} bendungan, {persen_vol.toFixed(1)}%, total Potensi Volume: {total_potensial.toFixed(2)} Juta M<sup>3</sup>, total Realisasi Volume: {total_real.toFixed(2)} Juta M<sup>3</sup>
			</Col>
		</Row>
			
		<Row>
		<Col><UpbCard upb={list_upb[0]} /></Col>
		<Col><UpbCard upb={list_upb[1]}/></Col>
		<Col><UpbCard upb={list_upb[2]} /></Col>
		<Col><UpbCard upb={list_upb[3]} /></Col>
		</Row>
		<Row>
		<Col><UpbCard upb={list_upb[4]} /></Col>
		<Col><UpbCard upb={list_upb[5]} /></Col>
		<Col><UpbCard upb={list_upb[6]} /></Col>
		<Col><UpbCard upb={list_upb[7]} /></Col>
		</Row>
	</Container>
	)
};

export default App
