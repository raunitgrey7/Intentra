function PlaceCard({ place }) {
	return (
		<article className="card">
			<h3>{place.name}</h3>
			<div className="meta">
				{place.distance_km} km away | score {place.score} | rating {place.rating}
			</div>
			<p className="why">{place.why}</p>
		</article>
	);
}

export default PlaceCard;
