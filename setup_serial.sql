-- Set location_id to start after test restaurants
SELECT MAX(location_id) + 1 FROM restaurant;
CREATE SEQUENCE location_id_seq MINVALUE 1587366;
ALTER TABLE restaurant ALTER location_id SET DEFAULT nextval('location_id_seq');
ALTER SEQUENCE location_id_seq OWNED BY restaurant.location_id;

-- Set user_id to start after test users
SELECT MAX(user_id) + 1 FROM users;
CREATE SEQUENCE user_id_seq MINVALUE 51;
ALTER TABLE users ALTER user_id SET DEFAULT nextval('user_id_seq');
ALTER SEQUENCE user_id_seq OWNED BY users.user_id;
