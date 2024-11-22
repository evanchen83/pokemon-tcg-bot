-- changeset author:add-player-table
CREATE TABLE player_cards (
    discord_id VARCHAR NOT NULL,
    card_id VARCHAR NOT NULL,
    count INTEGER,
    PRIMARY KEY (discord_id, card_id)
);
