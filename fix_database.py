from app import create_app
from db import db
from sqlalchemy import text


app = create_app()


with app.app_context():

    # ======================================================
    # FIX COMMENTS TABLE
    # ======================================================

    db.session.execute(
        text(
            """
            ALTER TABLE comments
            ADD COLUMN IF NOT EXISTS updated_at
            TIMESTAMP NOT NULL
            DEFAULT CURRENT_TIMESTAMP
            """
        )
    )

    # ======================================================
    # FIX POST_IMAGES TABLE
    # ======================================================

    db.session.execute(
        text(
            """
            ALTER TABLE post_images
            ADD COLUMN IF NOT EXISTS image_filename
            VARCHAR(255)
            """
        )
    )

    db.session.execute(
        text(
            """
            ALTER TABLE post_images
            ADD COLUMN IF NOT EXISTS created_at
            TIMESTAMP NOT NULL
            DEFAULT CURRENT_TIMESTAMP
            """
        )
    )

    # ======================================================
    # MAKE SURE image_filename IS NOT NULL
    # ======================================================

    # Existing rows, if any, are given a safe filename.
    # New rows created by the application will always have
    # the real uploaded filename.

    db.session.execute(
        text(
            """
            UPDATE post_images
            SET image_filename = 'legacy-image'
            WHERE image_filename IS NULL
            """
        )
    )

    db.session.execute(
        text(
            """
            ALTER TABLE post_images
            ALTER COLUMN image_filename SET NOT NULL
            """
        )
    )

    # ======================================================
    # COMMIT ALL DATABASE CHANGES
    # ======================================================

    db.session.commit()

    print()
    print("==============================================")
    print("DATABASE FIX COMPLETED SUCCESSFULLY")
    print("==============================================")
    print("comments.updated_at       -> OK")
    print("post_images.image_filename -> OK")
    print("post_images.created_at     -> OK")
    print("==============================================")