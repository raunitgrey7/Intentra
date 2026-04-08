import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const userIcon = L.divIcon({
	html: '<div style="width:12px;height:12px;background:#126e52;border:2px solid #fff;border-radius:50%"></div>',
	className: "",
	iconSize: [12, 12],
});

const placeIcon = L.divIcon({
	html: '<div style="width:11px;height:11px;background:#f0a03b;border:2px solid #fff;border-radius:50%"></div>',
	className: "",
	iconSize: [11, 11],
});

function MapView({ center, places }) {
	return (
		<MapContainer center={center} zoom={13} scrollWheelZoom className="map">
			<TileLayer
				attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
				url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
			/>

			<Marker position={center} icon={userIcon}>
				<Popup>Your location</Popup>
			</Marker>

			{places.map((place) => (
				<Marker key={`${place.name}-${place.lat}-${place.lng}`} position={[place.lat, place.lng]} icon={placeIcon}>
					<Popup>
						<strong>{place.name}</strong>
						<br />
						{place.why}
					</Popup>
				</Marker>
			))}
		</MapContainer>
	);
}

export default MapView;
