DROP TABLE IF EXISTS feed;
DROP TABLE IF EXISTS source;
DROP TABLE IF EXISTS source_to_feed;

-- This table stores "feeds" which are calendars composed of multiple sources.
-- FIXME: Choose timezone? Manually or based on source(s)?
CREATE TABLE feed (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	created TIMESTAMP NOT NULL -- creation time as an ISO-8601 formatted UTC string
);

-- This table will store "primitive sources", i.e. stuff we can subscribe to.
CREATE TABLE source (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	url TEXT NOT NULL UNIQUE,

	-- When we update sources, their content are stored in this table.
	-- NULL indicates lack of data in case of failed fetch.
	last_updated TIMESTAMP,
	-- FIXME: Is limit size of TEXT too small?
	content TEXT
);


-- This table manages the many-to-many relationship between `feed` and `source`.
CREATE TABLE source_to_feed (
	source_id INTEGER NOT NULL,
	feed_id INTEGER NOT NULL,
	UNIQUE(source_id, feed_id),
	FOREIGN KEY(source_id) REFERENCES source(id),
	FOREIGN KEY(feed_id) REFERENCES feed(id) ON DELETE CASCADE
);
