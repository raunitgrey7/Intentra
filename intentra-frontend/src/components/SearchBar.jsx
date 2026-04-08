import { useState } from "react";

function SearchBar({ onSearch, loading }) {
	const [query, setQuery] = useState("");

	const submit = (event) => {
		event.preventDefault();
		if (!query.trim() || loading) {
			return;
		}
		onSearch(query.trim());
	};

	return (
		<form className="search-row" onSubmit={submit}>
			<input
				type="text"
				value={query}
				onChange={(event) => setQuery(event.target.value)}
				placeholder="Try: quiet cafe to work for 2 hours"
				minLength={5}
				required
			/>
			<button type="submit" disabled={loading}>
				{loading ? "Finding places..." : "Get recommendations"}
			</button>
		</form>
	);
}

export default SearchBar;
