import { useMemo, useState } from "react";

import MapView from "../components/MapView";
import PlaceCard from "../components/PlaceCard";
import SearchBar from "../components/SearchBar";
import { fetchRecommendations } from "../services/api";

const DEFAULT_LOCATION = [28.6139, 77.2090];

function Home() {
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");
	const [location, setLocation] = useState(DEFAULT_LOCATION);
	const [intent, setIntent] = useState(null);
	const [recommendations, setRecommendations] = useState([]);

	const center = useMemo(() => location, [location]);

	const handleSearch = (query) => {
		setLoading(true);
		setError("");

		navigator.geolocation.getCurrentPosition(
			async (position) => {
				try {
					const latitude = position.coords.latitude;
					const longitude = position.coords.longitude;
					setLocation([latitude, longitude]);

					const data = await fetchRecommendations({
						query,
						latitude,
						longitude,
					});

					setIntent(data.intent);
					setRecommendations(data.recommendations || []);
				} catch (_err) {
					setError("Could not fetch recommendations. Check if backend is running.");
				} finally {
					setLoading(false);
				}
			},
			() => {
				setLoading(false);
				setError("Location access is required for recommendations.");
			}
		);
	};

	return (
		<div className="app-shell">
			<header className="hero">
				<h1>Intentra</h1>
				<p>Intent-aware places with explainable scoring</p>
			</header>

			<main className="layout">
				<section className="panel">
					<SearchBar onSearch={handleSearch} loading={loading} />

					{error && <p className="error">{error}</p>}

					{intent && (
						<p className="meta" style={{ marginTop: 12 }}>
							Intent: {intent.mood} | Radius: {intent.radius_km} km
						</p>
					)}

					<div className="results">
						{recommendations.map((place) => (
							<PlaceCard key={`${place.name}-${place.lat}-${place.lng}`} place={place} />
						))}
					</div>
				</section>

				<section className="map-panel">
					<MapView center={center} places={recommendations} />
				</section>
			</main>
		</div>
	);
}

export default Home;
