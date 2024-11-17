-- changeset author:add-player-table
CREATE TABLE player_cards (
    discord_id VARCHAR NOT NULL,
    card_name VARCHAR NOT NULL,
    card_image_url VARCHAR NOT NULL,
    count INTEGER,
    PRIMARY KEY (discord_id, card_name)
);
