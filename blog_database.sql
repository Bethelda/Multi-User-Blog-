-- ==========================================================
-- MULTI USER BLOG DATABASE
-- PostgreSQL Database Script
-- ==========================================================

-- ==========================================================
-- USERS TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,

    full_name VARCHAR(120) NOT NULL,

    username VARCHAR(80) NOT NULL UNIQUE,

    email VARCHAR(150) NOT NULL UNIQUE,

    password_hash VARCHAR(255) NOT NULL,

    role VARCHAR(20) NOT NULL DEFAULT 'user',

    bio TEXT,

    profile_image VARCHAR(255),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================================
-- POSTS TABLE
-- ==========================================================

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,

    title VARCHAR(200) NOT NULL,

    content TEXT NOT NULL,

    image VARCHAR(255),

    published BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    user_id INTEGER NOT NULL,

    CONSTRAINT fk_posts_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- ==========================================================
-- INDEXES
-- ==========================================================

CREATE INDEX IF NOT EXISTS idx_users_username
ON users(username);


CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);


CREATE INDEX IF NOT EXISTS idx_posts_user_id
ON posts(user_id);


CREATE INDEX IF NOT EXISTS idx_posts_created_at
ON posts(created_at);


-- ==========================================================
-- CHECK ROLE VALUES
-- ==========================================================

ALTER TABLE users
DROP CONSTRAINT IF EXISTS check_user_role;


ALTER TABLE users
ADD CONSTRAINT check_user_role
CHECK (role IN ('user', 'admin'));


-- ==========================================================
-- FINISHED
-- ==========================================================