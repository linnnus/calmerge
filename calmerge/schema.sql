DROP TABLE IF EXISTS feed;
DROP TABLE IF EXISTS source;
DROP TABLE IF EXISTS url_to_content;

-- FIXME: Pluralize names

-- This table stores "feeds" which are calendars composed of multiple sources.
-- FIXME: Choose timezone? Manually or based on source(s)?
CREATE TABLE feed (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	created TIMESTAMP NOT NULL -- creation time as an ISO-8601 formatted UTC string
);

-- This table will store "primitive sources", i.e. stuff we can subscribe to.
-- FIXME: Multiple sources can point to the same URL, which is inefficient.
CREATE TABLE source (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL, -- Friendly name for UI.
	url TEXT NOT NULL UNIQUE,  -- URL pointing to .ical file
	update_frequency INTEGER, -- Maximum time since last update in seconds.
	feed_id INTEGER NOT NULL, -- Owning feed (1-to-many relationship)
	-- Because sources are owned by feeds, they should be removed when the feed is.
	FOREIGN KEY(feed_id) REFERENCES feed(id) ON DELETE CASCADE,
	FOREIGN KEY(url) REFERENCES url_to_content(url) ON DELETE CASCADE
);

-- Stores results of network queries.
-- FIXME: keep status code, timing, etc.?
-- (laste_updated, content) = (NULL, NULL) state before initial network request.
CREATE TABLE url_to_content (
	-- Requested url – primary key in spirit.
	url TEXT NOT NULL UNIQUE,

	last_updated TIMESTAMP,

	-- FIXME: Is limit size of TEXT too small?
	content TEXT
);
